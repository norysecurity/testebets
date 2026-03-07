#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo: client_trust_scan.py

Detecta "Client-Side Trust" — vulnerabilidades onde lógica crítica de segurança
(aleatório, resultado de jogos, tempo restante, validação de vitória) é
processada no front-end em vez de no servidor.

Inspirado nos vídeos CTF:
  - Double: seed gerada no front-end (timestamp), resultado calculado no browser
  - Aviator: tempo até o crash criptografado em AES e enviado ao cliente
  - Mines: resultado da seleção decidido no cliente com float bypass
  - Refunds: token JWT em cookie sem flag 'secure' + 'httpOnly'

O módulo faz duas verificações:
  1. Análise de requisições HTTP — procura parâmetros suspeitos no payload
     enviado pelo cliente para o servidor (seed, is_winner, time_left, result, etc.)
  2. Análise estática de JS — busca padrões de código inseguro no JS da página
     (random no front, descriptografia AES, cálculo de resultado)
"""

import re
import json
from typing import Any
from urllib.parse import urlparse

import requests


# ─────────────────────────────────────────────────────────────────────────────
#  PADRÕES SUSPEITOS
# ─────────────────────────────────────────────────────────────────────────────

# Parâmetros que NÃO deveriam ser enviados pelo cliente
PARAMS_SUSPEITOS = [
    # Sementes / aleatório
    "seed", "random_seed", "game_seed", "client_seed", "nonce",
    # Resultado / vitória
    "is_winner", "winner", "result", "outcome", "win", "lose",
    "ganhou", "perdeu", "resultado",
    # Tempo restante (Aviator)
    "time_left", "crash_time", "time_ms", "gms", "ms",
    # Controle de jogo no cliente
    "multiplier_server", "bomb_positions", "board",
    # Flags de liberação (Mines float)
    "deliverable", "release_it", "rule",
    # Roles passados pelo cliente
    "role", "is_admin", "admin", "slug",
]

# Padrões de código JS suspeito
PADROES_JS = [
    # Geração de aleatório no front
    (r"Math\.random\(\)", "Math.random() no client — resultado pode ser previsível"),
    (r"Date\.now\(\)|new Date\(\)\.getTime\(\)|performance\.now\(\)",
     "Timestamp como seed — previsível e repetível"),
    # Criptografia no cliente (Aviator pattern)
    (r"AES\.decrypt|CryptoJS\.AES|aesDecrypt|decryptAES",
     "Descriptografia AES no front — dado sensível pode ser extraído"),
    (r"AES\.encrypt|CryptoJS\.AES\.encrypt",
     "Criptografia AES no front — chave pode estar exposta no bundle"),
    # Cálculo de resultado no cliente
    (r"is_winner\s*=|isWinner\s*=|winner\s*=\s*true|resultado\s*=",
     "Variável de vitória calculada no front-end"),
    (r"seed\s*=\s*Date|seed\s*:\s*Date|\"seed\"\s*:\s*Date",
     "Seed baseada em Date (timestamp) — não use no front"),
    # localStorage com dados sensíveis
    (r"localStorage\.setItem\(['\"].*[Tt]oken",
     "Token armazenado em localStorage — vulnerável a XSS"),
    (r"localStorage\.setItem\(['\"].*[Aa]dmin",
     "Flag de admin em localStorage — bypassável via JS"),
    # Cookie sem flags
    (r"document\.cookie\s*=(?!.*[Hh]ttp[Oo]nly)(?!.*[Ss]ecure)",
     "Cookie definido sem HttpOnly/Secure — bypassável via XSS"),
    # Rotas admin expostas no bundle
    (r"['\"/]admin['\"/]|['\"/]zadmin['\"/]|['\"/]backoffice['\"/]",
     "Rota admin referenciada no JS do front-end — expõe superfície oculta"),
    # eval / Function para código dinâmico
    (r"\beval\s*\(|new\s+Function\s*\(",
     "eval/Function — possível XSS ou bypass de filtros"),
    # Roles/permissões comparadas no cliente
    (r"role\s*===?\s*['\"]admin|role\s*===?\s*['\"]student|userRole\s*===?\s*",
     "Role comparado no front-end — trivialmente bypassável"),
]

# Parâmetros suspeitos em cookies (sem flags de segurança)
COOKIE_FLAGS = {"httponly", "secure", "samesite"}


# ─────────────────────────────────────────────────────────────────────────────
#  ANÁLISE 1 — Payload de requisição HTTP
# ─────────────────────────────────────────────────────────────────────────────

def analisar_payload(payload_str: str) -> list[dict[str, Any]]:
    """
    Verifica se o payload enviado pelo cliente contém parâmetros
    que deveriam ser gerados/validados exclusivamente pelo servidor.
    """
    achados: list[dict[str, Any]] = []

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        return [{"tipo": "PARSE_ERROR", "detalhe": "Payload não é JSON válido"}]

    chaves_lower = {k.lower(): k for k in payload.keys()}

    for param_suspeito in PARAMS_SUSPEITOS:
        if param_suspeito in chaves_lower:
            chave_original = chaves_lower[param_suspeito]
            valor = payload[chave_original]
            achados.append({
                "tipo": "PARAM_CLIENT_SIDE",
                "parametro": chave_original,
                "valor": str(valor)[:80],
                "risco": "ALTO",
                "descricao": (
                    f"Parâmetro '{chave_original}' enviado pelo cliente. "
                    "Este valor deveria ser calculado/validado exclusivamente no servidor."
                ),
            })

    return achados


# ─────────────────────────────────────────────────────────────────────────────
#  ANÁLISE 2 — Código JavaScript estático da página
# ─────────────────────────────────────────────────────────────────────────────

def analisar_javascript(url: str, headers_str: str | None = None) -> list[dict[str, Any]]:
    """
    Baixa a página `url` e todos os scripts (<script src=...>) referenciados,
    em seguida aplica os padrões de código suspeito.
    """
    achados: list[dict[str, Any]] = []

    headers = {}
    if headers_str:
        try:
            headers = json.loads(headers_str)
        except json.JSONDecodeError:
            pass

    # Garantir User-Agent razoável
    if "User-Agent" not in headers:
        headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    # Baixar HTML da página
    try:
        resp_html = requests.get(url, headers=headers, timeout=15, verify=False)
        html = resp_html.text
    except Exception as exc:
        return [{"tipo": "FETCH_ERROR", "detalhe": str(exc)}]

    # Verificar cookies da resposta
    for cookie in resp_html.cookies:
        flags_presentes = set()
        if cookie.has_nonstandard_attr("httponly") or getattr(cookie, "_rest", {}).get("HttpOnly"):
            flags_presentes.add("httponly")
        if cookie.secure:
            flags_presentes.add("secure")
        if cookie.has_nonstandard_attr("samesite"):
            flags_presentes.add("samesite")

        flags_faltando = COOKIE_FLAGS - flags_presentes
        if flags_faltando:
            achados.append({
                "tipo": "COOKIE_INSEGURO",
                "cookie": cookie.name,
                "risco": "MÉDIO-ALTO" if "httponly" in flags_faltando else "MÉDIO",
                "descricao": (
                    f"Cookie '{cookie.name}' sem flags: {', '.join(flags_faltando).upper()}. "
                    "Se contiver token de sessão, pode ser roubado via XSS."
                ),
            })

    # Extrair URLs de scripts
    base_parsed = urlparse(url)
    base_origin = f"{base_parsed.scheme}://{base_parsed.netloc}"

    script_urls: list[str] = []
    src_pattern = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    for match in src_pattern.finditer(html):
        src = match.group(1)
        if src.startswith("http"):
            script_urls.append(src)
        elif src.startswith("//"):
            script_urls.append(f"{base_parsed.scheme}:{src}")
        elif src.startswith("/"):
            script_urls.append(f"{base_origin}{src}")

    # Incluir JS inline
    inline_pattern = re.compile(r'<script(?![^>]+src)[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)
    blocos_js = [m.group(1) for m in inline_pattern.finditer(html)]

    # Baixar scripts externos
    for script_url in script_urls:
        try:
            r = requests.get(script_url, headers=headers, timeout=10, verify=False)
            if "javascript" in r.headers.get("Content-Type", "") or r.url.endswith(".js"):
                blocos_js.append(r.text)
        except Exception:
            continue

    # Aplicar padrões
    todo_js = "\n".join(blocos_js)
    total_chars = len(todo_js)

    for padrao, descricao in PADROES_JS:
        matches = list(re.finditer(padrao, todo_js))
        if matches:
            # Pegar contexto ao redor da primeira ocorrência
            m = matches[0]
            start = max(0, m.start() - 60)
            end = min(len(todo_js), m.end() + 60)
            contexto = todo_js[start:end].replace("\n", " ").strip()

            achados.append({
                "tipo": "JS_CLIENT_SIDE_LOGIC",
                "padrao": padrao,
                "ocorrencias": len(matches),
                "risco": "ALTO",
                "descricao": descricao,
                "contexto": f"...{contexto}...",
            })

    return achados, total_chars


# ─────────────────────────────────────────────────────────────────────────────
#  FUNÇÃO PRINCIPAL DO MÓDULO
# ─────────────────────────────────────────────────────────────────────────────

def client_trust_scan(
    url: str | None = None,
    payload_str: str | None = None,
    headers_str: str | None = None,
    apenas_payload: bool = False,
    apenas_js: bool = False,
) -> list[dict[str, Any]]:
    """
    Escaneia por vulnerabilidades de Client-Side Trust.

    Modos:
      - payload_str fornecido → analisa parâmetros suspeitos no payload
      - url fornecida         → baixa e analisa o JS da página
      - ambos                 → executa os dois

    Parâmetros
    ----------
    url            : URL da plataforma a escanear (para análise JS)
    payload_str    : JSON do payload capturado (para análise de parâmetros)
    headers_str    : JSON dos headers (para autenticação no download do JS)
    apenas_payload : analisa só o payload (ignora JS)
    apenas_js      : analisa só o JS (ignora payload)
    """
    todos_achados: list[dict[str, Any]] = []

    print(f"\n{'═'*68}")
    print("  MÓDULO 6 — CLIENT-SIDE TRUST SCAN")
    print(f"{'═'*68}\n")

    # ── Análise 1: Payload ────────────────────────────────────────────────────
    if payload_str and not apenas_js:
        print("[*] Analisando payload da requisição...")
        achados_payload = analisar_payload(payload_str)
        todos_achados.extend(achados_payload)

        if achados_payload:
            print(f"\n  ⚠  {len(achados_payload)} parâmetro(s) suspeito(s) encontrado(s) no payload:\n")
            for a in achados_payload:
                print(f"    🔴 [{a['risco']}] {a.get('parametro', a['tipo'])}")
                print(f"       {a['descricao']}")
                if "valor" in a:
                    print(f"       Valor: {a['valor']}")
                print()
        else:
            print("   Nenhum parâmetro suspeito encontrado no payload.\n")

    # ── Análise 2: JavaScript ─────────────────────────────────────────────────
    if url and not apenas_payload:
        print(f"[*] Baixando e analisando JavaScript de: {url}")
        import warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        resultado_js = analisar_javascript(url, headers_str)
        if isinstance(resultado_js, tuple):
            achados_js, total_chars = resultado_js
        else:
            achados_js = resultado_js
            total_chars = 0

        todos_achados.extend(achados_js)

        if total_chars:
            print(f"   Total de JS analisado: {total_chars:,} caracteres\n")

        achados_codigo = [a for a in achados_js if a["tipo"] == "JS_CLIENT_SIDE_LOGIC"]
        achados_cookie = [a for a in achados_js if a["tipo"] == "COOKIE_INSEGURO"]
        achados_erro   = [a for a in achados_js if a["tipo"] in ("FETCH_ERROR", "PARSE_ERROR")]

        if achados_erro:
            for e in achados_erro:
                print(f"  [ERRO] {e.get('detalhe', e)}\n")

        if achados_cookie:
            print(f"  🍪 COOKIES INSEGUROS ({len(achados_cookie)}):\n")
            for a in achados_cookie:
                print(f"    🔴 [{a['risco']}] Cookie: {a['cookie']}")
                print(f"       {a['descricao']}\n")

        if achados_codigo:
            print(f"  🧩 LÓGICA CRÍTICA NO FRONT-END ({len(achados_codigo)} padrão(ões)):\n")
            for a in achados_codigo:
                print(f"    🔴 [{a['risco']}] {a['descricao']}")
                print(f"       Ocorrências : {a['ocorrencias']}")
                print(f"       Contexto    : {a['contexto'][:120]}")
                print()

        if not achados_js:
            print("   Nenhum padrão suspeito encontrado no JavaScript.\n")

    # ── Resumo final ──────────────────────────────────────────────────────────
    print(f"{'─'*68}")
    print(f"  RESUMO — {len(todos_achados)} vulnerabilidade(s) de Client-Side Trust encontrada(s)")

    if not todos_achados:
        print("    Nenhuma vulnerabilidade detectada nesta varredura.")
    else:
        tipos = {}
        for a in todos_achados:
            tipos[a["tipo"]] = tipos.get(a["tipo"], 0) + 1
        for tipo, cnt in tipos.items():
            print(f"    {tipo}: {cnt}")

    print("\n[✓] Client Trust Scan concluído.\n")
    return todos_achados
