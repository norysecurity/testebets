import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def brute_force_scan():
    print("Iniciando scan de força bruta...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Encontrar todos os JSONs { ... }
    # Usando regex simples para encontrar o início e o fim
    matches = re.finditer(r'\{', content)
    found_count = 0
    
    for m in matches:
        start = m.start()
        # Tentar fechar o JSON sucessivamente
        for end in range(start + 2, min(start + 50000, len(content))):
            if content[end] == '}':
                candidate = content[start:end+1]
                try:
                    data = json.loads(candidate)
                    if "message" in data:
                        msg = data["message"]
                        # Ver se é um pacote binário do Spribe
                        if isinstance(msg, dict) or isinstance(msg, list):
                            raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)]) if isinstance(msg, dict) else bytes(msg)
                            text = "".join([chr(b) if 32 <= b <= 126 else "." for b in raw])
                            
                            # Filtro: Contém 'balance' ou 'bet' mas NÃO 'mines' nem 'cellNumber'
                            # (Isso isola o pacote de INÍCIO do jogo)
                            tl = text.lower()
                            if ('balance' in tl or 'bet' in tl) and 'mines' not in tl and 'cellnumber' not in tl:
                                print(f"\n[!!!] ACHADO PACOTE DE INÍCIO ({len(raw)} bytes)")
                                print(f"Texto: {text[:150]}...")
                                print(f"Hex: {raw.hex()[:64]}...")
                                found_count += 1
                    break # Se achou um JSON válido, para de expandir
                except: continue
    print(f"\nScan concluído. {found_count} pacotes suspeitos encontrados.")

if __name__ == "__main__":
    brute_force_scan()
