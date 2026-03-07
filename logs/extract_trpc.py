import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def extract_trpc():
    print("Extraindo chamadas tRPC...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    for b in blocks:
        if 'trpc' in b.lower() and '{' in b:
            print(f"\n[TRPC] Bloco size: {len(b)}")
            try:
                # Extrair o JSON limpando "Extra data"
                # tRPC costuma vir no formato {"result":{"data":{"json":...}}}
                json_match = re.search(r'\{.*\}', b, re.DOTALL)
                if json_match:
                    candidate = json_match.group(0)
                    # Tentar achar o fim real do JSON equilibrando chaves
                    stack = 0
                    real_end = 0
                    for idx, char in enumerate(candidate):
                        if char == '{': stack += 1
                        elif char == '}': 
                            stack -= 1
                            if stack == 0:
                                real_end = idx + 1
                                break
                    if real_end > 0:
                        data = json.loads(candidate[:real_end])
                        js_str = json.dumps(data, indent=2)
                        
                        # Procurar por minas ou estados de jogo
                        if 'mines' in js_str.lower() or 'grid' in js_str.lower():
                            print("!!! ACHADO GRID NO TRPC !!!")
                            print(js_str[:1000]) # Mostrar o início
            except: pass

if __name__ == "__main__":
    extract_trpc()
