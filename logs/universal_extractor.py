import json
import os
import zlib

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'
output_dir = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\extracted'
os.makedirs(output_dir, exist_ok=True)

def extract_all_binary():
    print("Extraindo todos os pacotes binários suspeitos...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    for i, block in enumerate(blocks):
        if '{' in block and '}' in block:
            try:
                json_start = block.find('{')
                json_end = block.rfind('}') + 1
                data = json.loads(block[json_start:json_end])
                
                if "message" in data:
                    msg = data["message"]
                    if isinstance(msg, dict):
                        raw = bytes([msg[k] for k in sorted(msg.keys(), key=lambda x: int(x))])
                    else:
                        raw = bytes(msg)
                    
                    # Filtramos por tamanho ou palavras chave
                    text = "".join([chr(b) if 32 <= b <= 126 else "." for b in raw])
                    
                    # Salvar todos os pacotes > 150 bytes (BetResponse, State, GameOver)
                    if len(raw) > 150:
                        ts = block[:15].replace(":", "").replace(".", "")
                        fn = os.path.join(output_dir, f"P_{ts}_{len(raw)}.bin")
                        with open(fn, "wb") as bf:
                            bf.write(raw)
                        
                        # Se tiver 'mines', marcar como GAME_OVER
                        if 'mines' in text.lower():
                            with open(fn + ".tag", "w") as tf: tf.write("GAME_OVER")
                        elif 'bet' in text.lower() or 'balance' in text.lower():
                            with open(fn + ".tag", "w") as tf: tf.write("BET_INIT")
            except Exception as e: pass

if __name__ == "__main__":
    extract_all_binary()
