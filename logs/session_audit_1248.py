import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def session_audit():
    print("Auditando a sessão do balanço 12.48...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    
    found_balance = False
    for i, b in enumerate(blocks):
        if '12.48' in b or '1248' in b:
            print(f"\n[!!!] ENCONTRADO 12.48 no Bloco {i} (size {len(b)})")
            print(f"Timestamp: {b[:15]}")
            # Ver o que veio ANTES desse bloco (os últimos 10 blocos)
            print("--- Fluxo Anterior ---")
            for j in range(max(0, i-10), i):
                prev = blocks[j]
                print(f"B{j} | {prev[:15]} | Size: {len(prev)} | {prev[prev.find('https'):prev.find(' ', prev.find('https'))]}")
            
            # Se for um pacote Spribe, ver se tem bombas
            if 'spribe' in b.lower() and 'message' in b:
                try:
                    data = json.loads(b[b.find('{'):b.rfind('}')+1])
                    msg = data["message"]
                    raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)]) if isinstance(msg, dict) else bytes(msg)
                    if b"mines" in raw.lower():
                        bombs = [int(raw[m.end()+4]) for m in re.finditer(b"cellNumber", raw)]
                        print(f"BOMBAS DESTA SESSÃO: {bombs}")
                except: pass

if __name__ == "__main__":
    session_audit()
