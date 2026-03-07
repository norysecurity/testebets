import json
import os

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def dump_packets(target_cells):
    print(f"Dumping packets for: {target_cells}")
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
                    
                    found_count = sum(1 for c in target_cells if c in bytes_list)
                    if found_count >= 3:
                        msg_str = "".join([chr(b) if 32 <= b <= 126 else "." for b in bytes_list])
                        print(f"\n--- MATCH {found_count}/4 (Size {len(bytes_list)}) ---")
                        print(f"Texto: {msg_str}")
                        print(f"Bytes: {bytes_list}")
            except: pass

if __name__ == "__main__":
    dump_packets([9, 10, 11, 19])
