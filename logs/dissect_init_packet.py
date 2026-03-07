import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def dissect():
    print("Dissecando pacote de inicialização (20k)...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    for b in blocks:
        if len(b) > 15000:
            print(f"\n--- BLOCO DE {len(b)} CHARS ---")
            
            # 1. Tentar decodificar TUDO que parece JSON
            jsons = re.findall(r'\{.*\}', b, re.DOTALL)
            for j in jsons:
                try:
                    data = json.loads(j)
                    # Caminhar recursivamente por todo o JSON buscando arrays de ints
                    def find_grids(obj):
                        if isinstance(obj, list):
                            if len(obj) == 25 and all(isinstance(x, int) and 0 <= x <= 1 for x in obj):
                                print(f"[!!!] POSSÍVEL GRID 5x5 ACHADO: {obj}")
                            if 3 <= len(obj) <= 24 and all(isinstance(x, int) and 0 <= x <= 24 for x in obj):
                                print(f"[!!!] POSSÍVEL LISTA DE BOMBAS ACHADA: {obj}")
                            for item in obj: find_grids(item)
                        elif isinstance(obj, dict):
                            for v in obj.values(): find_grids(v)
                    
                    find_grids(data)
                except: pass

            # 2. Se for o formato Spribe (message: [ {byte_dict} ]), decodificar e buscar binário
            try:
                # Pegar o primeiro { }
                json_start = b.find('{')
                json_end = b.rfind('}') + 1
                data = json.loads(b[json_start:json_end])
                if "message" in data:
                    msgs = data["message"]
                    if isinstance(msgs, list):
                        for m_idx, m_dict in enumerate(msgs):
                            raw = bytes([m_dict[k] for k in sorted(m_dict.keys(), key=int)])
                            # Buscar por padrões de grid (0/1)
                            for i in range(len(raw) - 25):
                                chunk = raw[i:i+25]
                                if all(x in [0, 1] for x in chunk) and 1 <= sum(chunk) <= 24:
                                    print(f"[!!!] GRID 5x5 em sub-msg {m_idx}, offset {i}: {[idx for idx,v in enumerate(chunk) if v==1]}")
                            # Buscar por sequências de cellNumber (hex)
                            # hex: 63656c6c4e756d626572
                            if b"cellNumber" in raw:
                                print(f"[INFO] 'cellNumber' encontrado em sub-msg {m_idx}")
                
            except: pass

if __name__ == "__main__":
    dissect()
