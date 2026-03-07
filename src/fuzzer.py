#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo: fuzzer.py
Fuzzing Lógico (Type/Logic Flaws): injeta anomalias de tipo em parâmetros
numéricos de um payload JSON e exibe uma tabela comparativa de respostas HTTP.
"""

import json
from typing import Any

import requests


# ─────────────────────────────────────────────────────────────────────────────
#  ANOMALIAS INJETADAS EM CADA PARÂMETRO NUMÉRICO
# ─────────────────────────────────────────────────────────────────────────────

ANOMALIAS: list[tuple[str, Any]] = [
    ("negativo",          -1),
    ("zero",              0),
    ("fracionado_baixo",  0.5),
    ("fracionado_alto",   9.99),
    ("muito_grande",      9_999_999_999),
    ("overflow_float",    1.7976931348623157e+308),
    ("string_vazia",      ""),
    ("string_numero",     "1337a"),
    ("null",              None),
    ("booleano_true",     True),
    ("booleano_false",    False),
    ("array_vazio",       []),
    ("objeto_vazio",      {}),
]


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _clonar_payload_com_valor(base: dict, chave: str, valor: Any) -> dict:
    """Retorna cópia do payload com `chave` substituída por `valor`."""
    copia = json.loads(json.dumps(base, default=str))
    copia[chave] = valor
    return copia


def _fazer_requisicao(
    url: str,
    metodo: str,
    payload: dict,
    headers: dict,
    timeout: int = 15,
) -> tuple[int | str, int]:
    """
    Executa a requisição e retorna (status_code, tamanho_resposta_bytes).
    Em caso de falha de conexão, retorna ("ERR", 0).
    """
    try:
        r = requests.request(
            metodo.upper(), url, json=payload, headers=headers, timeout=timeout
        )
        return r.status_code, len(r.content)
    except requests.exceptions.Timeout:
        return "TIMEOUT", 0
    except requests.exceptions.ConnectionError:
        return "CONN_ERR", 0
    except Exception as exc:
        return f"ERR:{str(exc)[:30]}", 0


def _classificar_alerta(
    status: int | str,
    tamanho: int,
    status_base: int,
    tamanho_base: int,
    valor_anomalia: Any,
) -> str:
    """Retorna uma string de alerta com base nos desvios detectados."""
    if status == 500:
        return "🔴 SERVER ERROR (500) — possível exception não tratada"
    if str(status).startswith("2") and valor_anomalia in (-1, None, "", False, [], {}):
        return "⚠  2xx com valor inválido/nulo — lógica não validada"
    if status != status_base and str(status).startswith("2"):
        return "⚠  2xx com status diferente da baseline"
    if status == status_base and tamanho != tamanho_base and abs(tamanho - tamanho_base) > 20:
        return "⚠  Tamanho de resposta diferente — comportamento anômalo"
    if isinstance(valor_anomalia, float) and str(status).startswith("2"):
        return "⚠  2xx com float — validação de inteiro ausente?"
    return ""


# ─────────────────────────────────────────────────────────────────────────────
#  FUNÇÃO PRINCIPAL DO MÓDULO
# ─────────────────────────────────────────────────────────────────────────────

def fuzzing_logico(
    url: str,
    payload_str: str,
    headers_str: str,
    metodo: str = "POST",
    timeout: int = 15,
) -> list[dict[str, Any]]:
    """
    Itera sobre parâmetros numéricos do payload, injeta anomalias e registra
    o comportamento do servidor em uma tabela comparada à resposta baseline.

    Retorna lista de dicionários com todos os alertas encontrados.

    Parâmetros
    ----------
    url         : endpoint alvo
    payload_str : JSON em string com o payload base
    headers_str : JSON em string com os cabeçalhos HTTP
    metodo      : método HTTP (GET, POST, PUT, PATCH) — padrão: POST
    timeout     : timeout em segundos por requisição (padrão: 15)
    """
    print(f"\n{'═'*70}")
    print("  MÓDULO 3 — FUZZING LÓGICO (TYPE/LOGIC FLAWS)")
    print(f"{'═'*70}")
    print(f"  URL    : {url}")
    print(f"  Método : {metodo.upper()}")
    print(f"{'─'*70}\n")

    # ── Parse de inputs ──────────────────────────────────────────────────────
    try:
        payload_base = json.loads(payload_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"[ERRO] Payload JSON inválido: {e}") from e

    try:
        headers = json.loads(headers_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"[ERRO] Headers JSON inválidos: {e}") from e

    # ── Identificar parâmetros alvo ──────────────────────────────────────────
    chaves_numericas = [
        k for k, v in payload_base.items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    ]
    if not chaves_numericas:
        print(
            "[AVISO] Nenhum parâmetro numérico no payload raiz.\n"
            "         Aplicando fuzzing em TODOS os parâmetros.\n"
        )
        chaves_numericas = list(payload_base.keys())

    total_testes = len(chaves_numericas) * len(ANOMALIAS)
    print(f"  Parâmetros alvo  : {chaves_numericas}")
    print(f"  Anomalias/param  : {len(ANOMALIAS)}")
    print(f"  Total de testes  : {total_testes}\n")

    # ── Baseline (requisição com payload original) ───────────────────────────
    status_base, tamanho_base = _fazer_requisicao(
        url, metodo, payload_base, headers, timeout
    )
    print(f"  [BASELINE] Status={status_base}  Bytes={tamanho_base}\n")

    # ── Cabeçalho da tabela ──────────────────────────────────────────────────
    print(
        f"  {'Parâmetro':<20} {'Anomalia':<22} {'Valor Injetado':<20} "
        f"{'Status':<9} {'Bytes':<8} Alerta"
    )
    print(f"  {'─'*20} {'─'*22} {'─'*20} {'─'*9} {'─'*8} {'─'*38}")

    alertas: list[dict[str, Any]] = []

    for chave in chaves_numericas:
        for nome_anomalia, valor_anomalia in ANOMALIAS:
            payload_mod = _clonar_payload_com_valor(payload_base, chave, valor_anomalia)
            status, tamanho = _fazer_requisicao(url, metodo, payload_mod, headers, timeout)

            alerta = _classificar_alerta(
                status, tamanho, status_base, tamanho_base, valor_anomalia
            )

            valor_str = "null" if valor_anomalia is None else str(valor_anomalia)
            if len(valor_str) > 18:
                valor_str = valor_str[:15] + "..."

            print(
                f"  {chave:<20} {nome_anomalia:<22} {valor_str:<20} "
                f"{str(status):<9} {tamanho:<8} {alerta}"
            )

            if alerta:
                alertas.append({
                    "parametro": chave,
                    "anomalia": nome_anomalia,
                    "valor": valor_anomalia,
                    "status": status,
                    "tamanho": tamanho,
                    "alerta": alerta,
                })

    # ── Resumo final ─────────────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  RESUMO — {len(alertas)} alerta(s) encontrado(s) de {total_testes} teste(s):")
    if alertas:
        for a in alertas:
            print(
                f"    → {a['alerta']}\n"
                f"       param='{a['parametro']}'  anomalia='{a['anomalia']}'  "
                f"valor={a['valor']}  HTTP {a['status']}"
            )
    else:
        print("    Nenhuma anomalia crítica detectada — servidor valida bem os tipos.")

    print("\n[✓] Fuzzing lógico concluído.\n")
    return alertas
