import os
import re

# Caminho do log massivo
LOG_PATH = r"f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\game_responses.log"

def find_deposits():
    print("=== BUSCADOR DE DEPSITOS (v1.0) ===")
    if not os.path.exists(LOG_PATH):
        print(f"Log no encontrado em: {LOG_PATH}")
        return

    patterns = [
        r"recharge", r"deposit", r"deposito", r"pix", r"wallet", r"payment"
    ]
    
    found_count = 0
    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if any(re.search(p, line, re.IGNORECASE) for p in patterns):
                # Filtra apenas linhas que parecem conter URLs ou JSONs relevantes
                if "trpc" in line or "api" in line or "\"amount\"" in line:
                    print(f"[ACHADO] {line.strip()[:150]}...")
                    found_count += 1
            if found_count > 50:
                print("... limite de 50 resultados atingido.")
                break

    if found_count == 0:
        print("Nenhum registro de depsito óbvio encontrado no log.")
    else:
        print(f"\nTotal de {found_count} possveis registros encontrados.")

if __name__ == "__main__":
    find_deposits()
