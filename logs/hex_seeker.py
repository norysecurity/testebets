import json
import os

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def seek_hex_patterns(target_cells):
    print(f"Buscando padrões hex para {target_cells}")
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
                    
                    # Converter lista de bytes para representação hex string
                    hex_stream = "".join([f"{b:02x}" for b in bytes_list])
                    
                    # Padrão Protobuf: Tag 10 (0x0A) + Valor (1 byte se < 127)
                    # cellNumber em Spribe costuma ser Tag 10
                    # Vamos ver se encontramos a sequência de bombas
                    # mas elas costumam estar espalhadas em objetos repetidos
                    
                    # Se encontrarmos pelo menos os valores das bombas próximos uns dos outros
                    # num pacote sent no INÍCIO do jogo
                    found_vals = 0
                    for val in target_cells:
                        if f"{val:02x}" in hex_stream:
                            found_vals += 1
                    
                    if found_vals >= 3:
                        msg_str = "".join([chr(b) if 32 <= b <= 126 else "." for b in bytes_list])
                        # Se não contém 'win' ou 'lose' ou 'cashout', é promissor!
                        if not any(x in msg_str.lower() for x in ["win", "lose", "cashout", "opencellresponse"]):
                            print(f"\n[!!!] PACOTE PRÉ-JOGO SUSPEITO ({len(bytes_list)} bytes)")
                            print(f"Texto: {msg_str[:150]}...")
                            print(f"Bomba bytes: {[f'{v:02x}' for v in target_cells]}")
                            print(f"Hex: {hex_stream[:200]}...")
            except: pass

if __name__ == "__main__":
    # Bombas reais: [9, 10, 11, 19]
    seek_hex_patterns([9, 10, 11, 19])
