import json
import os

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def find_pre_game_bombs(target_bombs):
    print(f"Buscando bombas {target_bombs} em pacotes pré-jogo...")
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
                    
                    # Se o pacote é de tamanho médio (400-800 bytes) e NÃO contém 'mines'
                    # ou contém 'bet' no texto
                    msg_str = "".join([chr(b) if 32 <= b <= 126 else "." for b in bytes_list])
                    if "bet" in msg_str.lower() or "mines" in msg_str.lower():
                        # Verificar se as bombas [9, 10, 11, 19] aparecem escondidas
                        # Talvez como char(9), char(10), etc?
                        found = [b for b in target_bombs if b in bytes_list]
                        if len(found) >= 2:
                            print(f"\n[SUSPEITO] Encontrado {len(found)} das bombas num pacote de {len(bytes_list)} bytes")
                            print(f"Texto: {msg_str[:100]}...")
                            # Listar posições dos bytes
                            for b in target_bombs:
                                if b in bytes_list:
                                    print(f"Bomba {b} no índice {bytes_list.index(b)}")
            except: pass

if __name__ == "__main__":
    # Bombas da imagem 3: [9, 10, 11, 19]
    find_pre_game_bombs([9, 10, 11, 19])
