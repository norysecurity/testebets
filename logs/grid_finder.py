import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def find_hidden_grid():
    print("Buscando Grid oculto nos pacotes de 20k...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    for b in blocks:
        if len(b) > 5000:
            try:
                json_start = b.find('{')
                json_end = b.rfind('}') + 1
                data = json.loads(b[json_start:json_end])
                if "message" in data:
                    msg = data["message"]
                    raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)]) if isinstance(msg, dict) else bytes(msg)
                    
                    # 1. Tentar encontrar 25 bytes seguidos que contenham apenas 0 e 1
                    # (Um tabuleiro Mines 5x5 costuma ser enviado assim em algumas versões)
                    for i in range(len(raw) - 25):
                        chunk = raw[i:i+25]
                        if all(x in [0, 1] for x in chunk):
                            bomb_count = sum(chunk)
                            if 1 <= bomb_count <= 24:
                                print(f"\n[!!!] GRID 5x5 DETECTADO no pacote de {len(raw)} bytes!")
                                print(f"Offset: {i}")
                                print(f"Bombas: {[idx for idx, v in enumerate(chunk) if v == 1]}")
                                # Ver o texto ao redor
                                context = "".join([chr(x) if 32 <= x <= 126 else "." for x in raw[max(0, i-20):min(len(raw), i+45)]])
                                print(f"Contexto: {context}")

                    # 2. Tentar encontrar a string 'serverHash' ou 'seed'
                    text = "".join([chr(x) if 32 <= x <= 126 else "." for x in raw])
                    if 'hash' in text.lower() or 'seed' in text.lower():
                        print(f"\n[INFO] Hash/Seed encontrado no pacote de {len(raw)} bytes")
                        print(f"Texto: {text[:200]}...")
            except: pass

if __name__ == "__main__":
    find_hidden_grid()
