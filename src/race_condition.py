#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo: race_condition.py
Testa vulnerabilidades de Race Condition (TOCTOU) em endpoints de transação.
Dispara N requisições simultâneas usando asyncio + aiohttp.
"""

import asyncio
import json
import time
from typing import Any

import aiohttp


# ─────────────────────────────────────────────────────────────────────────────
#  HELPER INTERNO
# ─────────────────────────────────────────────────────────────────────────────

async def _disparar_requisicao(
    session: aiohttp.ClientSession,
    url: str,
    payload: dict,
    headers: dict,
    indice: int,
) -> dict[str, Any]:
    """Executa uma requisição POST assíncrona e retorna métricas."""
    inicio = time.monotonic()
    try:
        async with session.post(url, json=payload, headers=headers, ssl=False) as resp:
            duracao = round((time.monotonic() - inicio) * 1000, 2)
            corpo = await resp.text()
            return {
                "indice": indice,
                "status": resp.status,
                "duracao_ms": duracao,
                "tamanho_bytes": len(corpo),
                "resposta_curta": corpo[:120].replace("\n", " "),
            }
    except Exception as exc:
        duracao = round((time.monotonic() - inicio) * 1000, 2)
        return {
            "indice": indice,
            "status": "ERRO",
            "duracao_ms": duracao,
            "tamanho_bytes": 0,
            "resposta_curta": str(exc)[:120],
        }


# ─────────────────────────────────────────────────────────────────────────────
#  FUNÇÃO PRINCIPAL DO MÓDULO
# ─────────────────────────────────────────────────────────────────────────────

async def race_condition_test(
    url: str,
    payload_str: str,
    headers_str: str,
    num_conexoes: int = 50,
) -> list[dict[str, Any]]:
    """
    Dispara `num_conexoes` requisições simultâneas contra `url` e exibe
    uma tabela de resultados. Retorna a lista de dicionários com os resultados.

    Parâmetros
    ----------
    url           : endpoint alvo (POST)
    payload_str   : JSON em string com o corpo da requisição
    headers_str   : JSON em string com os cabeçalhos HTTP
    num_conexoes  : quantidade de requisições paralelas (padrão: 50)
    """
    print(f"\n{'═'*62}")
    print("  MÓDULO 1 — RACE CONDITION (TOCTOU)")
    print(f"{'═'*62}")
    print(f"  URL        : {url}")
    print(f"  Conexões   : {num_conexoes}")
    print(f"{'─'*62}\n")

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"[ERRO] Payload JSON inválido: {e}") from e

    try:
        headers = json.loads(headers_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"[ERRO] Headers JSON inválidos: {e}") from e

    connector = aiohttp.TCPConnector(limit=num_conexoes, ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)

    print(f"[*] Disparando {num_conexoes} requisições simultâneas...\n")

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tarefas = [
            _disparar_requisicao(session, url, payload, headers, i + 1)
            for i in range(num_conexoes)
        ]
        resultados: list[dict[str, Any]] = await asyncio.gather(*tarefas)

    # ── Tabela de resultados ─────────────────────────────────────────────────
    print(
        f"  {'#':<5} {'Status':<8} {'ms':>8} {'Bytes':>8}  "
        f"{'Resposta (120 chars)'}"
    )
    print(f"  {'─'*5} {'─'*8} {'─'*8} {'─'*8}  {'─'*42}")

    contagem_status: dict[Any, int] = {}
    for r in sorted(resultados, key=lambda x: x["indice"]):
        st = r["status"]
        contagem_status[st] = contagem_status.get(st, 0) + 1
        print(
            f"  {r['indice']:<5} {str(st):<8} {r['duracao_ms']:>8} "
            f"{r['tamanho_bytes']:>8}  {r['resposta_curta']}"
        )

    # ── Resumo ───────────────────────────────────────────────────────────────
    print(f"\n{'─'*62}")
    print("  RESUMO DE STATUS:")
    for st, cnt in contagem_status.items():
        flag = ""
        if cnt > 1 and str(st).startswith("2"):
            flag = "  ⚠  POSSÍVEL EXPLORAÇÃO! (múltiplos 2xx simultâneos)"
        print(f"    HTTP {st}: {cnt} resposta(s){flag}")

    print("\n[✓] Teste de Race Condition concluído.\n")
    return resultados
