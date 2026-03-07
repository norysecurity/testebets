import json
import os

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def session_diff():
    print("Comparando binários de sessões 'Bingo'...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    
    # Encontrar sessões 176b
    bingos = []
    current_bet = None
    for b in blocks:
        if '{' not in b: continue
        try:
            data = json.loads(b[b.find('{'):b.rfind('}')+1])
            msg = data["message"]
            raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)]) if isinstance(msg, dict) else bytes(msg)
            text = "".join([chr(x) if 32 <= x <= 126 else "." for x in raw]).lower()
            
            if len(raw) == 176: current_bet = raw
            if "mines" in text and current_bet:
                bombs = []
                for m in __import__('re').finditer(b"cellNumber", raw):
                    bombs.append(int(raw[m.end()+4]))
                if bombs:
                    bingos.append({"bombs": bombs, "bet": current_bet})
                current_bet = None
        except: continue

    if len(bingos) < 2: return
    
    # Comparar os primeiros 10
    for i in range(min(5, len(bingos))):
        s = bingos[i]
        bet = s["bet"]
        print(f"\nSessão {i} | Bombas: {s['bombs']}")
        # Mostrar apenas os bytes que costumam mudar (depois do multiplier)
        # Multiplier acaba em ~100. Vamos ver 100-176.
        chunk = bet[100:]
        print(f"Bytes 100-176: {chunk.hex()}")
        # Tentar achar os números das bombas em qualquer lugar
        for b in s["bombs"]:
            if b in list(bet):
                print(f"Bomba {b} está no índice {list(bet).index(b)}")

if __name__ == "__main__":
    session_diff()
