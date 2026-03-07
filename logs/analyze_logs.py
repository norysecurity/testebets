import json
import os
import re

def decode_spribe_bin(bytes_list):
    """ Tenta decodificar o formato binário proprietário da Spribe. """
    i = 0
    results = {}
    while i < len(bytes_list):
        # Procura por strings (nomes de campos)
        if 32 <= bytes_list[i] <= 126:
            start = i
            while i < len(bytes_list) and 32 <= bytes_list[i] <= 126:
                i += 1
            name = "".join([chr(b) for b in bytes_list[start:i]])
            if len(name) > 1:
                # O valor costuma vir depois de alguns bytes (tipo + tamanho)
                # Ex: "cellNumber" [4 bytes] [valor]
                # Vamos pular 4 bytes e ver se o próximo é um valor útil
                if i + 5 < len(bytes_list):
                    val = bytes_list[i+4]
                    results[name] = val
                    i += 1
        else:
            i += 1
    return results

log_path = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    matches = re.finditer(r'\{.*?\}', content, re.DOTALL)
    for m in matches:
        block = m.group(0)
        if 1300 < len(block) < 1600:
            try:
                data = json.loads(block)
                if 'message' in data:
                    vals = data['message']
                    if isinstance(vals, dict):
                        bytes_list = [vals[k] for k in sorted(vals.keys(), key=int)]
                    else: bytes_list = vals
                    
                    decoded = decode_spribe_bin(bytes_list)
                    if decoded:
                        print(f"Packet Len {len(block)} -> Decoded: {decoded}")
            except: pass
else:
    print("Log not found")
