import json
import os
import re

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def analyze_timeline():
    print("Analisando linha do tempo do Mines...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    
    current_session = []
    
    for b in blocks:
        # Extrair timestamp e JSON
        ts_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3})', b)
        if not ts_match: continue
        ts = ts_match.group(1)
        
        json_start = b.find('{')
        json_end = b.rfind('}') + 1
        if json_start == -1: continue
        
        try:
            data = json.loads(b[json_start:json_end])
            if "message" in data:
                msg = data["message"]
                raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)]) if isinstance(msg, dict) else bytes(msg)
                text = "".join([chr(x) if 32 <= x <= 126 else "." for x in raw]).lower()
                
                event_type = "OUTRO"
                if "bet" in text or "balance" in text:
                    event_type = "BET/START"
                if "opencell" in text:
                    event_type = "CLIQUE"
                if "mines" in text or "cellnumber" in text:
                    event_type = "BOMBAS_DETEC"
                if "winamount" in text:
                    event_type = "WIN/CASH"
                
                print(f"[{ts}] Type: {event_type} | Size: {len(raw)} bytes")
                if event_type == "BOMBAS_DETEC":
                    # Tentar extrair os valores
                    bombs = []
                    for m in re.finditer(b"cellNumber", raw):
                        v_offset = m.end() + 4
                        if v_offset < len(raw):
                            bombs.append(int(raw[v_offset]))
                    print(f"   >>> BOMBAS: {bombs}")
        except: continue

if __name__ == "__main__":
    analyze_timeline()
