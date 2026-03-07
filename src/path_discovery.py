#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo: path_discovery.py

Descoberta de rotas/subpaths ocultos em aplicações web — estilo GoBuster.

Inspirado no vídeo CTF:
  - Uso de GoBuster para descobrir subdomínios como community.ruyter.com e refunds.ruyter.com
  - Wordlist de paths para encontrar /zadmin (rota admin escondida)
  - "Security by obscurity não é segurança."

Funcionalidades:
  - Descoberta de paths (ex: /admin, /api/v1, /dashboard)
  - Filtragem por status HTTP aceitos (padrão: todos exceto 404)
  - Controle de concorrência via asyncio
  - Suporte a wordlist customizada ou lista de paths comuns embutida
"""

import asyncio
import time
from typing import Any

import aiohttp


# ─────────────────────────────────────────────────────────────────────────────
#  WORDLIST EMBUTIDA — paths comuns em plataformas de cursos/bets/SaaS
# ─────────────────────────────────────────────────────────────────────────────

PATHS_COMUNS = [
    # Admin
    "admin", "admin/", "admin/login", "admin/dashboard", "admin/panel",
    "administrator", "administrator/login", "adm", "adm/login",
    "zadmin", "zadmin/", "zadmin/login",
    "manage", "management", "manager", "superadmin",
    "backend", "backoffice", "controlpanel", "cp",
    # APIs
    "api", "api/v1", "api/v2", "api/v3",
    "api/admin", "api/users", "api/config",
    "api/refund", "api/refunds", "api/affiliate", "api/affiliates",
    # Auth
    "login", "logout", "register", "signup", "signin",
    "auth", "auth/login", "oauth", "oauth/callback",
    "forgot-password", "reset-password",
    # Dados / Export
    "export", "export/db", "export/users", "download",
    "backup", "backup.sql", "backup.zip", "db.sql",
    "database", "dump", ".env", "config.json",
    # Docs / Dev
    "docs", "swagger", "swagger-ui", "swagger.json", "openapi.json",
    "api-docs", "graphql", "graphiql",
    "debug", "debug/pprof", "test", "staging",
    # Plataformas comuns de cursos
    "community", "members", "courses", "lessons",
    "affiliate", "affiliates", "refund", "refunds",
    "checkout", "payment", "payments", "pix",
    # Misc
    "health", "status", "ping",
    ".git", ".git/config", ".gitignore",
    "robots.txt", "sitemap.xml", "wp-login.php",
    "phpmyadmin", "pma", "phpinfo.php",
]


# ─────────────────────────────────────────────────────────────────────────────
#  WORKER ASSÍNCRONO
# ─────────────────────────────────────────────────────────────────────────────

async def _testar_path(
    session: aiohttp.ClientSession,
    url_base: str,
    path: str,
    semaforo: asyncio.Semaphore,
    status_ignorados: set[int],
) -> dict[str, Any] | None:
    """Faz GET para url_base/path e retorna resultado (ou None se ignorado)."""
    url = f"{url_base.rstrip('/')}/{path.lstrip('/')}"
    async with semaforo:
        inicio = time.monotonic()
        try:
            async with session.get(url, ssl=False, allow_redirects=False) as resp:
                duracao = round((time.monotonic() - inicio) * 1000, 1)
                status = resp.status
                tamanho = int(resp.headers.get("Content-Length", 0))
                location = resp.headers.get("Location", "")
                if status in status_ignorados:
                    return None
                return {
                    "path": path,
                    "url": url,
                    "status": status,
                    "tamanho": tamanho,
                    "duracao_ms": duracao,
                    "location": location,
                }
        except Exception:
            return None


# ─────────────────────────────────────────────────────────────────────────────
#  FUNÇÃO PRINCIPAL DO MÓDULO
# ─────────────────────────────────────────────────────────────────────────────

async def path_discovery(
    url_base: str,
    wordlist_path: str | None = None,
    concorrencia: int = 50,
    status_ignorados: list[int] | None = None,
    timeout_seg: int = 10,
    extensoes: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Descobre paths/rotas ocultas em uma aplicação web.

    Parâmetros
    ----------
    url_base        : URL base do alvo (ex: https://refunds.ruyter.com)
    wordlist_path   : caminho para .txt com um path por linha. Se None, usa lista embutida.
    concorrencia    : máximo de requisições simultâneas (padrão: 50)
    status_ignorados: lista de status HTTP para ignorar (padrão: [404, 410])
    timeout_seg     : timeout por requisição (padrão: 10s)
    extensoes       : extensões extras a concatenar (ex: [".php", ".asp"])
    """
    if status_ignorados is None:
        status_ignorados = [404, 410]
    status_ignorados_set = set(status_ignorados)

    # Carregar wordlist
    if wordlist_path:
        try:
            with open(wordlist_path, encoding="utf-8", errors="ignore") as f:
                paths = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        except FileNotFoundError:
            raise ValueError(f"[ERRO] Wordlist não encontrada: {wordlist_path}")
    else:
        paths = PATHS_COMUNS.copy()

    # Adicionar variantes com extensões
    if extensoes:
        base_paths = paths.copy()
        for p in base_paths:
            for ext in extensoes:
                paths.append(f"{p}{ext}")

    total = len(paths)

    print(f"\n{'═'*64}")
    print("  MÓDULO 5 — PATH DISCOVERY (GoBuster-style)")
    print(f"{'═'*64}")
    print(f"  Alvo         : {url_base}")
    print(f"  Total paths  : {total:,}")
    print(f"  Concorrência : {concorrencia}")
    print(f"  Ignorando    : HTTP {status_ignorados}")
    if extensoes:
        print(f"  Extensões    : {extensoes}")
    print(f"{'─'*64}\n")
    print(
        f"  {'Status':<8} {'Tamanho':>8} {'ms':>7}  Path"
    )
    print(f"  {'─'*8} {'─'*8} {'─'*7}  {'─'*45}")

    semaforo = asyncio.Semaphore(concorrencia)
    timeout = aiohttp.ClientTimeout(total=timeout_seg)
    connector = aiohttp.TCPConnector(limit=concorrencia, ssl=False)

    encontrados: list[dict[str, Any]] = []
    testados = 0
    inicio_geral = time.monotonic()

    lote_size = concorrencia * 3

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i in range(0, total, lote_size):
            lote = paths[i : i + lote_size]
            tarefas = [
                _testar_path(session, url_base, p, semaforo, status_ignorados_set)
                for p in lote
            ]
            resultados = await asyncio.gather(*tarefas)
            testados += len(lote)

            for r in resultados:
                if r is None:
                    continue
                encontrados.append(r)

                # Emoji por status
                if r["status"] == 200:
                    icone = "🟢"
                elif r["status"] in (301, 302, 307, 308):
                    icone = "🔵"
                elif r["status"] in (401, 403):
                    icone = "🔴"
                else:
                    icone = "🟡"

                loc = f"  → {r['location']}" if r["location"] else ""
                print(
                    f"  {icone} {r['status']:<6} {r['tamanho']:>8} {r['duracao_ms']:>7}  "
                    f"{r['path']}{loc}"
                )

    duracao_total = round(time.monotonic() - inicio_geral, 1)

    print(f"\n{'─'*64}")
    print(
        f"  RESUMO — {duracao_total}s | {testados:,} paths testados | "
        f"{len(encontrados)} encontrado(s)"
    )

    if encontrados:
        print("\n  Paths encontrados (por status):")
        for r in sorted(encontrados, key=lambda x: x["status"]):
            print(f"    [{r['status']}] {r['url']}")
    else:
        print("    Nenhum path encontrado além dos ignorados.")

    print("\n[✓] Path Discovery concluído.\n")
    return encontrados
