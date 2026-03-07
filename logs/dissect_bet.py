import json
import os

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def dissect_bet():
    print("Dissecando BetResponse (176 bytes)...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    blocks = content.split('\n[')
    for b in blocks:
        if '{' in b:
            try:
                data = json.loads(b[b.find('{'):b.rfind('}')+1])
                msg = data.get("message")
                if msg:
                    raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)]) if isinstance(msg, dict) else bytes(msg)
                    if len(raw) == 176:
                        print(f"\n--- BetResponse 176b ---")
                        # Imprimir os bytes em grupos de 10 para ver as tags
                        for i in range(0, min(100, len(raw)), 10):
                            chunk = raw[i:i+10]
                            hex_c = " ".join([f"{x:02x}" for x in chunk])
                            val_c = "  ".join([f"{x:2d}" for x in chunk])
                            print(f"{i:03d} | {hex_c}")
                            print(f"    | {val_c}")
            except: pass

if __name__ == "__main__":
    dissect_bet()
