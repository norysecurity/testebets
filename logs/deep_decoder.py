import json
import os

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def deep_decode():
    print("Iniciando decodificação profunda de sub-mensagens...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    for block in blocks:
        if '{' in block and '}' in block:
            try:
                json_start = block.find('{')
                json_end = block.rfind('}') + 1
                data = json.loads(block[json_start:json_end])
                
                if "message" in data:
                    msgs = data["message"]
                    # Se for uma lista de mensagens (Big Packet)
                    if isinstance(msgs, list):
                        for j, msg_dict in enumerate(msgs):
                            raw = bytes([msg_dict[k] for k in sorted(msg_dict.keys(), key=int)])
                            text = "".join([chr(b) if 32 <= b <= 126 else "." for b in raw])
                            
                            # Procurar por padrões de grid
                            for i in range(len(raw) - 25):
                                chunk = raw[i:i+25]
                                if all(x in [0, 1] for x in chunk):
                                    n = sum(chunk)
                                    if 1 <= n <= 24:
                                        print(f"\n[!!!] GRID ENCONTRADO em sub-mensagem {j}!")
                                        print(f"BOMBAS: {[idx for idx,v in enumerate(chunk) if v==1]}")
                                        print(f"Texto ao redor: {text[max(0, i-20):min(len(text), i+45)]}")
                    
                    # Se for uma mensagem direta (Single Packet)
                    elif isinstance(msgs, dict):
                        raw = bytes([msgs[k] for k in sorted(msgs.keys(), key=int)])
                        # (Opcional) Adicionar busca aqui também
            except: pass

if __name__ == "__main__":
    deep_decode()
