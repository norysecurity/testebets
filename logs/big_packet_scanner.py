import json
import os

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def scan_big_packet():
    print("Escaneando Big Packets (20k)...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    for b in blocks:
        if len(b) > 20000:
            print(f"\n--- Big Packet ({len(b)} bytes) ---")
            try:
                data = json.loads(b[b.find('{'):b.rfind('}')+1])
                msg = data["message"]
                if isinstance(msg, list):
                    # Concatenar todos os fragmentos da mensagem
                    raw = bytearray()
                    for sub in msg:
                        raw.extend([sub[k] for k in sorted(sub.keys(), key=int)])
                    
                    print(f"Tamanho binário total: {len(raw)} bytes")
                    
                    # 1. Procurar por 25 bytes seguidos (0 ou 1)
                    for i in range(len(raw) - 25):
                        chunk = raw[i:i+25]
                        if all(x in [0, 1] for x in chunk):
                            n_bombs = sum(chunk)
                            if 1 <= n_bombs <= 24:
                                print(f"GRID 5x5 ACHADO! Offset: {i}, Bombas: {n_bombs}")
                                board = [idx for idx,v in enumerate(chunk) if v==1]
                                print(f"Board: {board}")
                    
                    # 2. Procurar por strings de texto interessantes
                    text = "".join([chr(x) if 32 <= x <= 126 else "." for x in raw])
                    suspects = ['seed', 'hash', 'board', 'mines', 'gameid']
                    for s in suspects:
                        if s in text.lower():
                            print(f"Texto suspeito achado: {s}")
                            # Mostrar contexto
                            idx = text.lower().find(s)
                            print(f"Contexto: {text[max(0, idx-30):min(len(text), idx+100)]}")

            except: pass

if __name__ == "__main__":
    scan_big_packet()
