#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
capturador_55qq.py  v7 - "O AUDITOR"
Foco: Capturar rodadas reais (Spin/Bet) e analisar RNG.
  - Interceptação de WebSockets (PG Soft usa muito WS)
  - Filtro inteligente (não ignora domínios de API disfarçados)
  - Log de domínios únicos para descobrir o motor de jogo
"""

import json
import os
import urllib.parse
from datetime import datetime
from mitmproxy import http, ctx

log_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_dir, exist_ok=True)

sess = {"session_token": "", "token_data": "", "auth_tag": "", "user_id": ""}
dominios_vistos = set()

def _ts() -> str:
    now = datetime.now()
    s = now.strftime("%H:%M:%S.%f")
    return str(s)[:-3]

def _salvar_sessao():
    p = os.path.join(log_dir, "tokens_capturados.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(sess, f, indent=2, ensure_ascii=False)

def _log_game(prefix, path, body):
    with open(os.path.join(log_dir, "game_responses.log"), "a", encoding="utf-8") as f:
        f.write(f"\n[{_ts()}] {prefix} {path}\n{body}\n")

def _e_lixo(url: str) -> bool:
    # Ignorar apenas lixo real (estáticos pesados)
    lixo = [".png", ".jpg", ".jpeg", ".gif", ".woff2", ".css", ".svg", "fonts.googleapis", "gstatic"]
    url_l = url.lower()
    return any(x in url_l for x in lixo)

def request(flow: http.HTTPFlow) -> None:
    url = flow.request.pretty_url
    dominio = flow.request.host
    if dominio not in dominios_vistos:
        dominios_vistos.add(dominio)
        with open(os.path.join(log_dir, "dominios_descobertos.txt"), "a") as f:
            f.write(f"{_ts()} | {dominio}\n")

    if _e_lixo(url): return
    
    auth = flow.request.headers.get("Authorization", "")
    if "Bearer" in auth:
        ctx.log.info(f"  [REQ] {dominio}{flow.request.path[:30]} | Auth detectado")

def response(flow: http.HTTPFlow) -> None:
    url = flow.request.pretty_url
    if _e_lixo(url): return

    status = flow.response.status_code
    path = flow.request.path
    
    # Capturar tokens
    if any(x in path for x in ["auth.token", "auth.login"]):
        try:
            body = flow.response.get_text()
            dados = json.loads(body)
            d = dados.get("result", {}).get("data", {}).get("json", {})
            if not d: d = dados.get("result", {}).get("data", {}).get("data", {})
            
            if isinstance(d, dict):
                if d.get("token"): sess["session_token"] = str(d.get("token") or "")
                if d.get("tokenData"): sess["token_data"] = str(d.get("tokenData") or "")
                if d.get("authTag"): sess["auth_tag"] = str(d.get("authTag") or "")
                if d.get("userId"): sess["user_id"] = str(d.get("userId") or "")
                _salvar_sessao()
                ctx.log.alert(f"  [TOKEN] Atualizado!")
        except: pass

    # Capturar Jogo (Tiger, Mines, etc)
    # Procurar por padrões de aposta: spin, bet, play, rpc, crash
    patterns = ["spin", "bet", "play", "rpc", "crash", "mines", "game.", "settle"]
    if any(p in path.lower() for p in patterns) or any(p in url.lower() for p in patterns):
        ctx.log.alert(f"  [GAME-DATA] {path} | {status}")
        try:
            body = flow.response.get_text()
            _log_game("HTTP", path, body)
            if "is_winner" in body or "result" in body or "ge" in body:
                ctx.log.info("  [RESULTADO] Identificado no pacote HTTP!")
        except: pass

def websocket_message(flow: http.HTTPFlow):
    url = flow.request.pretty_url
    message = flow.websocket.messages[-1]
    
    # Logar mensagens de WebSocket em busca de RNG
    direcao = ">>" if message.from_client else "<<"
    conteudo = message.content.decode("utf-8", errors="ignore")
    
    # Filtrar pings/pongs para não poluir
    if len(conteudo) > 10:
        _log_game(f"WS-{direcao}", url, conteudo)
        if any(x in conteudo.lower() for x in ["result", "win", "seed", "ge", "spin"]):
             ctx.log.warn(f"  [WS-ANALYSIS] Dado suspeito de RNG detectado!")

def done():
    _salvar_sessao()
    print("Auditor Finalizado.")

