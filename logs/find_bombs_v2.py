import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def find_bombs_in_history(target_bombs):
    print(f"Buscando bombas {target_bombs} (e variantes) em todo o histórico...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('\n[')
    for block in blocks:
        if '{' in block and '}' in block:
            try:
                json_start = block.find('{')
                json_end = block.rfind('}') + 1
                data = json.loads(block[json_start:json_end])
                
                if "message" in data:
                    msg = data["message"]
                    bytes_list = [msg[k] for k in sorted(msg.keys(), key=int)] if isinstance(msg, dict) else list(msg)
                    
                    # 1. Busca por bytes isolados das bombas
                    found = [b for b in target_bombs if b in bytes_list]
                    if len(found) >= 3:
                        print(f"\n[MATCH {len(found)}/4] Tamanho: {len(bytes_list)} bytes")
                        # Onde estão os bytes?
                        indices = [i for i, x in enumerate(bytes_list) if x in target_bombs]
                        print(f"Indices: {indices}")
                        # Ver se estão perto de strings
                        msg_str = "".join([chr(b) if 32 <= b <= 126 else "." for b in bytes_list])
                        print(f"Texto: {msg_str[:150]}...")

                    # 2. Busca por bitmask (9, 10, 11, 19)
                    # 527872 em Little Endian: [0, 14, 8, 0] ou similar
                    # Vamos buscar por sequências de bits
                    # Ou representação hexadecimal
            except: pass

if __name__ == "__main__":
    # Bombas reais da imagem 3: [9, 10, 11, 19]
    find_bombs_in_history([9, 10, 11, 19])
    # Tentar também o inverso (24-x): [15, 14, 13, 5]
    print("\n--- BUSCANDO INVERSO ---")
    find_bombs_in_history([15, 14, 13, 5])
