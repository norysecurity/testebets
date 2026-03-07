import json
import os

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def find_patterns(target_cells):
    print(f"Buscando padrões para células: {target_cells}")
    if not os.path.exists(log_file):
        print("Arquivo de log não encontrado.")
        return

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Dividir por blocos de HTTP/WS
    blocks = content.split('\n[')
    for block in blocks:
        if '{' in block and '}' in block:
            try:
                # Extrair JSON do bloco
                json_start = block.find('{')
                json_end = block.rfind('}') + 1
                data = json.loads(block[json_start:json_end])
                
                if "message" in data:
                    msg = data["message"]
                    if isinstance(msg, dict):
                        bytes_list = [msg[k] for k in sorted(msg.keys(), key=lambda x: int(x))]
                    else:
                        bytes_list = list(msg)
                    
                    # Verificar se as células alvo aparecem no pacote
                    found_count = 0
                    for c in target_cells:
                        if c in bytes_list:
                            found_count += 1
                    
                    if found_count >= 3: # Se encontrar pelo menos 3 das 4 bombas
                        indices = [i for i, x in enumerate(bytes_list) if x in target_cells]
                        print(f"\n[!] POSSÍVEL MATCH ENCONTRADO ({found_count}/4):")
                        print(f"Tamanho: {len(bytes_list)} bytes")
                        print(f"Valores encontrados nos índices: {indices}")
                        # Mostrar os bytes ao redor do primeiro match
                        first_idx = indices[0]
                        start = max(0, first_idx - 10)
                        end = min(len(bytes_list), first_idx + 30)
                        print(f"Contexto: {bytes_list[start:end]}")
            except Exception as e:
                pass

if __name__ == "__main__":
    # Posições identificadas na imagem 3: 9, 10, 11, 19
    find_patterns([9, 10, 11, 19])
