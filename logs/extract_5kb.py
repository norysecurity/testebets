import json
import os
import re
import zlib

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def find_5kb_packet():
    print("Buscando pacotes de ~5kb nos logs...")
    if not os.path.exists(log_file): return

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Dividir por blocos de timestamp ou URL
    blocks = content.split('\n[')
    
    for b in blocks:
        # Procurar por spribe/api/send
        if 'spribe/api/send' in b:
            # Tentar extrair o JSON
            try:
                json_start = b.find('{')
                json_end = b.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    data = json.loads(b[json_start:json_end])
                    msg = data.get("message")
                    if msg:
                        # Reconstruir binário
                        if isinstance(msg, list):
                            raw = bytearray()
                            for m in msg: raw.extend([m[k] for k in sorted(m.keys(), key=int)])
                        else:
                            raw = bytes([msg[k] for k in sorted(msg.keys(), key=int)])
                        
                        size = len(raw)
                        if size > 1500: # ~5kb em base64/chars vira menos em binário comprimido
                            print(f"\n[!!!] PACOTE GRANDE ENCONTRADO ({size} bytes binários)")
                            
                            # Tentar descomprimir
                            decoded = raw
                            try: decoded = zlib.decompress(raw, -zlib.MAX_WBITS)
                            except: 
                                try: decoded = zlib.decompress(raw)
                                except: pass
                            
                            print(f"Tamanho descompactado: {len(decoded)} bytes")
                            
                            # Ver se tem texto
                            text = "".join([chr(x) if 32 <= x <= 126 else "." for x in decoded])
                            print(f"Preview Texto: {text[:500]}...")
                            
                            # Procurar por padrões de semente ou tabelas
                            if b"mines" in decoded.lower():
                                print("Contém 'mines'!")
                            
                            # Dump completo para arquivo de debug
                            with open('debug_5kb_raw.bin', 'wb') as df:
                                df.write(decoded)
                            print("Arquivo 'debug_5kb_raw.bin' salvo para inspeção profunda.")
            except: pass

if __name__ == "__main__":
    find_5kb_packet()
