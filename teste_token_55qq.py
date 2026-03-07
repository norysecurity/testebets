#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
teste_token_55qq.py  v2
Carrega os tokens salvos pelo capturador e testa endpoints autenticados.
"""

import json
import os
import requests
import warnings
warnings.filterwarnings("ignore")

BASE = "https://api5.a-b-c-8.com"
LOG  = os.path.join(os.path.dirname(__file__), "logs", "tokens_capturados.json")

ENDPOINTS = [
    ("GET",  "/api/frontend/trpc/user.details?input=%7B%22json%22%3A%7B%7D%7D"),
    ("GET",  "/api/frontend/trpc/user.assets?input=%7B%22json%22%3A%7B%7D%7D"),
    ("GET",  "/api/frontend/trpc/wallet.balance?input=%7B%22json%22%3A%7B%7D%7D"),
    ("GET",  "/api/frontend/trpc/mail.noRead?input=%7B%22json%22%3A%7B%7D%7D"),
    ("GET",  "/api/frontend/trpc/activity.list?input=%7B%22json%22%3A%7B%7D%7D"),
    ("POST", "/api/frontend/trpc/auth.token"),
]


def testar(auth_value, label):
    print(f"\n{'='*55}")
    print(f"  [{label}]")
    print(f"  Auth: {auth_value[:60]}...")
    print(f"{'='*55}")
    hdrs = {
        "Authorization": auth_value if auth_value.startswith("Bearer") else f"Bearer {auth_value}",
        "Content-Type": "application/json",
        "Origin": "https://55qq2.com",
        "Referer": "https://55qq2.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0) Chrome/145",
        "Accept": "application/json",
    }
    for method, path in ENDPOINTS:
        url = BASE + path
        ep  = path.split("/trpc/")[-1].split("?")[0]
        try:
            if method == "POST":
                r = requests.post(url, headers=hdrs, json={"json": {}}, timeout=8, verify=False)
            else:
                r = requests.get(url, headers=hdrs, timeout=8, verify=False)
            ok  = "OK " if r.status_code == 200 else "---"
            print(f"  [{ok}] {r.status_code}  {ep}")
            if r.status_code == 200:
                d = r.json()
                print(f"         {json.dumps(d, ensure_ascii=False)[:180]}")
        except Exception as e:
            print(f"  [ERR] {ep}: {e}")


if __name__ == "__main__":
    if not os.path.exists(LOG):
        print(f"[ERRO] Arquivo nao encontrado: {LOG}")
        print("       Execute o INICIAR_CAPTURA.bat primeiro e faca login.")
        exit(1)

    with open(LOG, encoding="utf-8") as f:
        sessao = json.load(f)

    session_token = sessao.get("session_token")
    token_data    = sessao.get("token_data")
    auth_tag      = sessao.get("auth_tag")
    user_id       = sessao.get("user_id")

    print("="*55)
    print("  BetAuditor - Teste de Tokens 55QQ")
    print("="*55)
    print(f"  user_id       : {user_id}")
    print(f"  session_token : {str(session_token)[:40]}...")
    print(f"  token_data    : {str(token_data)[:40]}..." if token_data else "  token_data    : Nao capturado ainda")
    print(f"  auth_tag      : {str(auth_tag)[:40]}..." if auth_tag else "  auth_tag      : Nao capturado")

    if not session_token:
        print("\n[ERRO] Nenhum token capturado. Faca login primeiro!")
        exit(1)

    # Testa com session token
    testar(session_token, "SESSION TOKEN")

    # Testa com tokenData (se disponivel)
    if token_data:
        testar(token_data, "TOKEN DATA (JWT longo)")

    # Testa com authTag
    if auth_tag:
        testar(auth_tag, "AUTH TAG")

    print("\n[CONCLUIDO]")
