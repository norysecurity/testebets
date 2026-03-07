import json
import os
import zlib

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'
output_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\big_packet_dump.txt'

def analyze_big_packet():
    print("Analisando o 'Big Packet' de 7k...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('\n[')
    with open(output_file, 'w', encoding='utf-8') as out:
        for block in blocks:
            if '{' in block and '}' in block:
                try:
                    json_start = block.find('{')
                    json_end = block.rfind('}') + 1
                    data = json.loads(block[json_start:json_end])
                    
                    if "message" in data:
                        msg = data["message"]
                        raw_bytes = bytes([msg[k] for k in sorted(msg.keys(), key=int)]) if isinstance(msg, dict) else bytes(msg)
                        
                        if len(raw_bytes) > 5000:
                            out.write(f"\n\n=== BIG PACKET ({len(raw_bytes)} bytes) ===\n")
                            # Tentar descompressão
                            try:
                                decoded = zlib.decompress(raw_bytes, -zlib.MAX_WBITS)
                                out.write("[ZLIB DECODED]\n")
                            except:
                                try:
                                    decoded = zlib.decompress(raw_bytes)
                                    out.write("[ZLIB DECODED]\n")
                                except:
                                    decoded = raw_bytes
                                    out.write("[RAW BINARY]\n")
                            
                            # Dump as hex and text
                            hex_str = decoded.hex()
                            text_str = "".join([chr(b) if 32 <= b <= 126 else "." for b in decoded])
                            out.write(f"TEXT: {text_str}\n")
                            
                            # Buscar por padrões de bombas em 25 bytes
                            for i in range(len(decoded) - 25):
                                chunk = decoded[i:i+25]
                                if all(x in [0, 1] for x in chunk):
                                    n = sum(chunk)
                                    if 1 <= n <= 24:
                                        out.write(f"\n[!!!] POSSÍVEL GRID 5x5 no offset {i}: {[idx for idx,v in enumerate(chunk) if v==1]}\n")
                except: pass
    print(f"Análise concluída. Verifique {output_file}")

if __name__ == "__main__":
    analyze_big_packet()
