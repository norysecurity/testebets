import json
import os
import zlib

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'
output_dir = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\large_packets'
os.makedirs(output_dir, exist_ok=True)

def extract_large_packets():
    print(f"Extraindo pacotes grandes de {log_file}...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('\n[')
    count = 0
    for block in blocks:
        if '{' in block and '}' in block:
            try:
                json_start = block.find('{')
                json_end = block.rfind('}') + 1
                data = json.loads(block[json_start:json_end])
                
                if "message" in data:
                    msg = data["message"]
                    # Converter dict de keys string para lista de bytes
                    if isinstance(msg, dict):
                        raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)])
                    else:
                        raw = bytes(msg)
                    
                    if len(raw) > 3000:
                        count += 1
                        filename = os.path.join(output_dir, f"packet_{count}_{len(raw)}.bin")
                        with open(filename, "wb") as bf:
                            bf.write(raw)
                        
                        # Tentar descompressão
                        try:
                            decomp = zlib.decompress(raw, -zlib.MAX_WBITS)
                            with open(filename.replace(".bin", "_decomp.bin"), "wb") as df:
                                df.write(decomp)
                        except: pass
                        
                        print(f"Salvou pacote {count}: {len(raw)} bytes")
            except: pass

if __name__ == "__main__":
    extract_large_packets()
