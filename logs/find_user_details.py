import json
import os

log_file = r'f:\ia\Nova pasta\bet_auditor\BetAuditor\logs\vidente_history.log'

def find_user_details():
    if not os.path.exists(log_file): return
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # trpc calls are often logged as strings in JSON format
    # {"result":{"data":{"json":{"id":"4273537843","username":"...", "role":"user"}}}}
    matches = re.finditer(r'user\.details.*(\{.*\})', content)
    for m in matches:
        try:
            d = json.loads(m.group(1))
            print(f"ENCONTRADO USER DETAILS: {json.dumps(d, indent=2)}")
        except: pass

if __name__ == "__main__":
    import re
    find_user_details()
