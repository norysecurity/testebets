import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def scan_large_packets():
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
                    bytes_list = [msg[k] for k in sorted(msg.keys(), key=lambda x: int(x))] if isinstance(msg, dict) else list(msg)
                    
                    if len(bytes_list) > 1000:
                        msg_str = "".join([chr(b) if 32 <= b <= 126 else "." for b in bytes_list])
                        print(f"\n--- LARGE PACKET (Size {len(bytes_list)}) ---")
                        # Procurar por 'mines'
                        mines_pos = msg_str.find("mines")
                        if mines_pos != -1:
                            print(f"[!] ENCONTRADO 'mines' na posição {mines_pos}")
                            # Procurar cellNumber após mines
                            sub = msg_str[mines_pos:]
                            cells = []
                            for m in re.finditer(r"cellNumber", sub):
                                pos = mines_pos + m.end()
                                # No Spribe, o valor vem alguns bytes após a string
                                # Vamos pegar um range de bytes
                                b_val = bytes_list[pos+4] # Chute baseado no dump anterior
                                cells.append(b_val)
                            print(f"Bombas detectadas: {cells}")
                        else:
                            print("Palavra 'mines' não encontrada.")
            except: pass

if __name__ == "__main__":
    scan_large_packets()
