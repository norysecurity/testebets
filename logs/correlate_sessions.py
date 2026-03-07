import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def correlate():
    print("Correlacionando BetResponse com GameOver...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    
    sessions = []
    current_bet_packet = None
    
    for b in blocks:
        if '{' not in b: continue
        try:
            json_start = b.find('{')
            json_end = b.rfind('}') + 1
            data = json.loads(b[json_start:json_end])
            if "message" not in data: continue
            
            msg = data["message"]
            raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)]) if isinstance(msg, dict) else bytes(msg)
            text = "".join([chr(x) if 32 <= x <= 126 else "." for x in raw]).lower()
            
            if len(raw) == 176 and "bet" in text:
                current_bet_packet = raw
                
            if "mines" in text and current_bet_packet:
                # Extrair as bombas (GameOver)
                bombs = []
                for m in re.finditer(b"cellNumber", raw):
                    v_offset = m.end() + 4
                    if v_offset < len(raw):
                        bombs.append(int(raw[v_offset]))
                
                if bombs:
                    print(f"\n[SESSION] Bombas finais: {bombs}")
                    # Verificar se esses números estavam no BetResponse
                    found_in_bet = [b for b in bombs if b in list(current_bet_packet)]
                    print(f"Encontrados no BetResponse: {found_in_bet}")
                    if len(found_in_bet) == len(bombs):
                        print("!!! BINGO !!! As bombas estão no BetResponse!")
                        # Onde?
                        indices = [list(current_bet_packet).index(b) for b in bombs]
                        print(f"Indices no BetResponse: {indices}")
                    
                    current_bet_packet = None # Reset
        except: continue

if __name__ == "__main__":
    correlate()
