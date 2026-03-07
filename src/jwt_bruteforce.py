#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo: jwt_bruteforce.py
1. Decodifica e exibe header + payload de um JWT sem verificar assinatura.
2. Tenta descobrir o secret (HMAC) via brute-force com uma wordlist.
"""

import json

import jwt as pyjwt


# ─────────────────────────────────────────────────────────────────────────────
#  FUNÇÃO PRINCIPAL DO MÓDULO
# ─────────────────────────────────────────────────────────────────────────────

def jwt_analisar_e_bruteforce(token: str, wordlist_path: str) -> dict:
    """
    Analisa um token JWT e tenta descobrir o secret por força bruta.

    Retorna um dicionário com:
        header       : dict com o header decodificado
        payload      : dict com o payload decodificado
        secret       : str com o secret encontrado (ou None)
        tentativas   : int com o número de tentativas realizadas

    Parâmetros
    ----------
    token         : token JWT completo (header.payload.signature)
    wordlist_path : caminho para arquivo .txt de wordlist (uma palavra por linha)
    """
    resultado = {
        "header": {},
        "payload": {},
        "secret": None,
        "tentativas": 0,
    }

    print(f"\n{'═'*62}")
    print("  MÓDULO 2 — ANÁLISE E BRUTE FORCE JWT")
    print(f"{'═'*62}\n")

    # ── 1. Decodificação sem verificação de assinatura ───────────────────────
    try:
        header = pyjwt.get_unverified_header(token)
        payload = pyjwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=[
                "HS256", "HS384", "HS512",
                "RS256", "RS384", "RS512",
                "ES256", "ES384", "ES512",
            ],
        )
    except pyjwt.exceptions.DecodeError as e:
        print(f"[ERRO] Token JWT inválido ou malformado: {e}\n")
        return resultado

    resultado["header"] = header
    resultado["payload"] = payload

    algoritmo: str = header.get("alg", "desconhecido")

    print("[HEADER DECODIFICADO]")
    print(json.dumps(header, indent=4, ensure_ascii=False))

    print("\n[PAYLOAD DECODIFICADO]")
    print(json.dumps(payload, indent=4, ensure_ascii=False, default=str))
    print()

    # ── 2. Verificar se algoritmo é HMAC (brute-force aplicável) ─────────────
    if not algoritmo.startswith("HS"):
        print(
            f"[INFO] Algoritmo '{algoritmo}' usa criptografia assimétrica.\n"
            "       Brute-force de secret HMAC não se aplica.\n"
            "       Para RSA/EC, você precisa da chave privada.\n"
        )
        return resultado

    print(f"[*] Algoritmo detectado: {algoritmo}")
    print(f"[*] Iniciando brute-force com wordlist: {wordlist_path}\n")

    # ── 3. Carregar wordlist ─────────────────────────────────────────────────
    try:
        with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as wl:
            linhas = wl.read().splitlines()
    except FileNotFoundError:
        print(f"[ERRO] Wordlist não encontrada: {wordlist_path}\n")
        return resultado

    total = len(linhas)
    print(f"[*] Total de palavras na wordlist: {total:,}\n")

    # ── 4. Brute-force ───────────────────────────────────────────────────────
    encontrado = False
    i = 0
    for candidato_raw in linhas:
        candidato = candidato_raw.strip()
        if not candidato:
            continue

        i += 1
        resultado["tentativas"] = i

        if i % 10_000 == 0:
            pct = (i / total) * 100
            print(f"    [progresso] {i:,}/{total:,} ({pct:.1f}%)", end="\r", flush=True)

        try:
            pyjwt.decode(token, candidato, algorithms=[algoritmo])
            print(f"\n\n  🎯  SECRET ENCONTRADO  →  '{candidato}'")
            print(f"      Tentativa nº {i:,} de {total:,}\n")
            resultado["secret"] = candidato
            encontrado = True
            break
        except pyjwt.exceptions.InvalidSignatureError:
            continue
        except pyjwt.exceptions.DecodeError:
            continue
        except Exception:
            continue

    if not encontrado:
        print(f"\n[─] Secret não encontrado após {i:,} tentativas.")
        print(
            "    Sugestões:\n"
            "      • Use uma wordlist maior (ex: rockyou.txt — ~14M palavras)\n"
            "      • Verifique se o algoritmo está correto no header\n"
            "      • O secret pode ser forte demais para força bruta simples\n"
        )

    print("[✓] Análise JWT concluída.\n")
    return resultado
