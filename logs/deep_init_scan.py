import os

def deep_scan_init():
    file_path = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\debug_5kb_raw.bin'
    if not os.path.exists(file_path): return
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"Analisando Init Packet ({len(data)} bytes)...")
    
    # 1. Procurar por sequências de 25 bytes (minas: 1, diamantes: 0)
    found_grids = []
    for i in range(len(data) - 25):
        chunk = data[i:i+25]
        if all(x in [0, 1] for x in chunk):
            n = sum(chunk)
            if 1 <= n <= 24:
                found_grids.append((i, list(chunk), n))
    
    if found_grids:
        for offset, grid, bombs in found_grids:
            print(f"GRID 5x5 ACHADO! Offset: {offset}, Bombas: {bombs}")
            print(f"Indices: {[idx for idx,v in enumerate(grid) if v==1]}")
    else:
        print("Nenhum grid 5x5 (0/1) literal encontrado.")

    # 2. Procurar por sequências de N números únicos entre 0 e 24
    # (Ex: [11, 12, 22, 15] que vimos antes)
    potential_lists = []
    for seq_len in range(3, 16):
        for i in range(len(data) - seq_len):
            chunk = data[i:i+seq_len]
            if all(0 <= x <= 24 for x in chunk) and len(set(chunk)) == seq_len:
                # Verificar se os bytes vizinhos são tags de Protobuf (0x08, 0x10, etc)
                potential_lists.append((i, list(chunk)))
    
    if potential_lists:
        # Filtrar as mais longas ou que aparecem depois de 'mines'
        print(f"Encontradas {len(potential_lists)} sequências numéricas candidatas.")
        for offset, lst in potential_lists[-10:]: # Mostrar as últimas (final do pacote)
             print(f"Offset {offset}: {lst}")

if __name__ == "__main__":
    deep_scan_init()
