import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def inspect_large_site_packet():
    print("Inspecionando pacotes massivos do site (55qq2.com)...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Vamos buscar por blocos que contenham 'game/action'
    blocks = content.split('\n[')
    for b in blocks:
        if '/game/action' in b and len(b) > 5000:
            print(f"\n[!!!] PACOTE GIGANTE ENCONTRADO ({len(b)} chars)")
            # Extrair o JSON limpando "Extra data"
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
                    try:
                        data = json.loads(candidate[:real_end])
                        # Salvar para inspeção manual
                        with open(r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\site_packet_debug.json', 'w') as out:
                            json.dump(data, out, indent=2)
                        print("Sucesso! Salvo em site_packet_debug.json")
                        
                        # Procurar por chaves suspeitas
                        suspects = ['mines', 'grid', 'board', 'cells', 'bombs', 'game_state', 'history']
                        for s in suspects:
                            if s in str(data).lower():
                                print(f"ACHADO campo suspeito: {s}")
                    except Exception as e: print(f"Erro ao ler JSON: {e}")

if __name__ == "__main__":
    inspect_large_site_packet()
