import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def analyze_flow():
    print("Analisando fluxo de apostas...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Dividir por blocos de log
    blocks = content.split('\n[')
    
    for i, block in enumerate(blocks):
        # Procurar por pacotes que não tenham 'cellNumber' mas tenham 'bet' ou 'start'
        if 'api/send' in block:
            try:
                json_start = block.find('{')
                json_end = block.rfind('}') + 1
                data = json.loads(block[json_start:json_end])
                
                if "message" in data:
                    msg = data["message"]
                    raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)]) if isinstance(msg, dict) else bytes(msg)
                    text = "".join([chr(b) if 32 <= b <= 126 else "." for b in raw])
                    
                    # Se este pacote for um BetResponse (tamanho ~500-2000 bytes)
                    if 300 < len(raw) < 3000:
                        # Se NÃO tem a palavra 'mines' (que aparece no GameOver), mas tem 'bet' ou 'balance'
                        if 'mines' not in text.lower() and ('bet' in text.lower() or 'balance' in text.lower()):
                            print(f"\n[POTENCIAL BET RESPONSE] {len(raw)} bytes")
                            print(f"Timestamp: {block[:20]}")
                            print(f"Texto: {text[:200]}...")
                            # Salvar o hex desse bloco para análise de bitmask
                            print(f"Hex: {raw.hex()[:100]}...")
            except: pass

if __name__ == "__main__":
    analyze_flow()
