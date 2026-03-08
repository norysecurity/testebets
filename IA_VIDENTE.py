# ==============================================================================
# IA VIDENTE - v5.0 TRANSACTION SNIFFER & AVIATOR ELITE
# ==============================================================================
import os
import json
import re
import zlib
import urllib.parse
from datetime import datetime
from mitmproxy import http, ctx

# Configurações
LOG_FILE = "vidente_history.log"
VERSION = "5.0.0"

# Sementes Capturadas (Ghost Fallback)
GHOST_DATA = {
    "user": "4273537843",
    "token": "v1~RCbrlUqiuYO_ajzQh4E_6M-Xgiow3Vkv639yrYG6Grv5jaysF2bviDNyXicgMCsKoBzUwOyO_srekc4FVZsNsEZoOQ-5s",
    "uid": "5-sDAqVW_CDlMP0PrZtux2l2xHaF8kEIn2F-nLsm8IdQi9A4Pccuc-DMfWyum41oyehkElOa-oWdyE4FJLeUXx3vBL7ptrIt6wbYKvuC0wTvzW4bD4Fa_fNI7_GokCEDJ4aQvGAnHa-RDOey68vCRZK2cEadZFAIBA9sexrwmLnNpoxY7eMmlgkpU2OJVAxqn-YgTXYcaklSpoOvRFH-34JI-vqQ",
    "tid": "3022708",
    "gid": "3"
}

HUD_HTML = """
<div id="vidente-hud" style="position:fixed; top:20px; left:20px; width:300px; background:rgba(0,0,0,0.97); border:2px solid #0ff; border-radius:14px; z-index:999999; color:white; font-family:monospace; padding:15px; box-shadow:0 0 50px rgba(0,255,255,0.8); cursor: move; user-select: none; backdrop-filter: blur(25px); border-image: linear-gradient(to bottom, #0ff, #f0f) 1;">
    <div style="font-weight:bold; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #f0f; padding-bottom: 8px;">
        <span style="color:#0ff; text-shadow: 0 0 15px #0ff;">🛸 VIDENTE v5.0 ELITE</span>
        <span id="v-status" style="font-size:10px; color:#f0f; border: 1px solid #f0f; padding: 2px 5px; border-radius: 4px;">SNIFFER: ATIVO</span>
    </div>
    
    <div id="v-grid-container">
        <div id="v-grid" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:6px; margin:10px 0; background:rgba(0,0,0,0.9); padding:10px; border-radius:10px; border: 2px solid #333;">
            <!-- Mines Grid -->
        </div>
    </div>

    <div id="v-aviator-container" style="display:none; background:rgba(255,0,0,0.1); border:1px solid #f00; padding:10px; border-radius:10px; margin-bottom:10px; text-align:center;">
        <div style="color:#f00; font-weight:bold; font-size:12px; margin-bottom:5px;">⚠️ AVIATOR VISION</div>
        <div id="v-aviator-prediction" style="font-size:32px; color:#f00; font-weight:bold; text-shadow: 0 0 15px #f00;">0.00x</div>
        <div style="font-size:9px; color:#aaa;">PONTO DE CRASH ESTIMADO</div>
    </div>
    
    <div id="v-transaction-info" style="font-size:10px; color:#0f0; margin-bottom:12px; background:rgba(0,255,0,0.05); padding:10px; border-radius:8px; border: 1px dashed #0f0;">
        <div style="font-weight:bold; margin-bottom:4px; color:#5f5;">💳 STATUS DE TRANSAÇÃO</div>
        <div id="v-tx-id" style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">AGUARDANDO PIX...</div>
        <div id="v-tx-value" style="font-weight:bold; color:#fff;">VALOR: R$ 0,00</div>
    </div>

    <div id="v-balance-info" style="font-size:11px; color:#0f0; margin-bottom:12px; text-align:center; background:rgba(0,255,0,0.15); padding:10px; border-radius:8px; border: 1px solid #0f0; box-shadow: inset 0 0 15px rgba(0,255,0,0.1);">
        💎 SALDO VIP: R$ <span id="v-current-balance">9.999.999,00</span>
    </div>

    <div style="font-size:10px; margin-top:10px; display:flex; gap:6px; justify-content:center; flex-wrap:wrap;">
        <button onclick="rotateGrid()" style="background:#111; border:1px solid #0ff; color:#0ff; padding:8px; cursor:pointer; border-radius:6px; flex:1; font-weight:bold; height:38px;">ROTAR</button>
        <button onclick="clearGrid()" style="background:#111; border:1px solid #f44; color:#f44; padding:8px; cursor:pointer; border-radius:6px; flex:1; font-weight:bold; height:38px;">CLEAN</button>
    </div>
    <div id="v-mode" style="font-size:11px; color:#0ff; margin-top:12px; text-align:center; font-weight:bold; text-transform:uppercase; letter-spacing:3px; text-shadow:0 0 10px #0ff;">MONITORANDO...</div>
</div>

<script>
    (function() {
        if (window.vidente_loaded) return;
        window.vidente_loaded = true;

        const hud = document.getElementById('vidente-hud');
        let isDragging = false, startX, startY, initialLeft, initialTop;
        
        hud.addEventListener('mousedown', (e) => {
            if(e.target.tagName === 'BUTTON') return;
            isDragging = true;
            startX = e.clientX; startY = e.clientY;
            const rect = hud.getBoundingClientRect();
            initialLeft = rect.left; initialTop = rect.top;
            hud.style.right = 'auto'; hud.style.left = initialLeft + 'px'; hud.style.top = initialTop + 'px';
        });
        window.addEventListener('mousemove', (e) => {
            if(!isDragging) return;
            hud.style.left = (initialLeft + (e.clientX - startX)) + 'px';
            hud.style.top = (initialTop + (e.clientY - startY)) + 'px';
        });
        window.addEventListener('mouseup', () => isDragging = false);

        let baseGrid = []; let currentSymmetry = 0; 

        const renderGrid = (mines) => {
            if (mines) baseGrid = mines;
            const gridDiv = document.getElementById('v-grid');
            if(!gridDiv) return;
            gridDiv.innerHTML = '';
            let transformed = applySymmetry(baseGrid, currentSymmetry);
            for (let i = 0; i < 25; i++) {
                const cell = document.createElement('div');
                cell.style.width = '100%'; cell.style.paddingBottom = '100%';
                cell.style.background = transformed.includes(i) ? 'rgba(255,0,0,0.9)' : '#080808';
                cell.style.border = transformed.includes(i) ? '2px solid #f00' : '1px solid #444';
                cell.style.borderRadius = '8px'; cell.style.position = 'relative';
                if (transformed.includes(i)) {
                    cell.innerHTML = '<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:18px; filter:drop-shadow(0 0 8px #f00);">💣</span>';
                }
                gridDiv.appendChild(cell);
            }
        };

        const applySymmetry = (mines, sym) => {
            return mines.map(idx => {
                let r = Math.floor(idx / 5), c = idx % 5;
                if (sym === 1) c = 4 - c; if (sym === 2) r = 4 - r;
                return r * 5 + c;
            });
        };

        window.rotateGrid = () => { currentSymmetry = (currentSymmetry + 1) % 4; renderGrid(); };
        window.clearGrid = () => { baseGrid = []; renderGrid(); document.getElementById('v-mode').innerText = "MONITORANDO..."; };

        setInterval(() => {
            if (window.vidente_grid_injetado) {
                document.getElementById('v-grid-container').style.display = 'block';
                document.getElementById('v-aviator-container').style.display = 'none';
                renderGrid(window.vidente_grid_injetado);
                window.vidente_grid_injetado = null; 
            }
            if (window.vidente_aviator_injetado) {
                document.getElementById('v-grid-container').style.display = 'none';
                document.getElementById('v-aviator-container').style.display = 'block';
                document.getElementById('v-aviator-prediction').innerText = window.vidente_aviator_injetado + 'x';
                window.vidente_aviator_injetado = null;
            }
            if (window.vidente_tx_injetada) {
                const tx = window.vidente_tx_injetada;
                document.getElementById('v-tx-id').innerText = "CHAVE: " + tx.id;
                document.getElementById('v-tx-value').innerText = "VALOR: R$ " + tx.amount;
                document.getElementById('v-mode').innerText = "PIX DETECTADO!";
                window.vidente_tx_injetada = null;
            }
        }, 300);
    })();
</script>
"""

class Vidente:
    def __init__(self):
        self.log_file = LOG_FILE
        self.session = GHOST_DATA.copy()

    def log_console(self, text):
        ts = datetime.now().strftime('%H:%M:%S')
        msg = f"[{ts}] {text}"
        print(msg)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def _quebrar_binario_spribe(self, payload_dict):
        try:
            sorted_keys = sorted([int(k) for k in payload_dict.keys() if k.isdigit()])
            byte_arr = bytearray([int(payload_dict[str(k)]) for k in sorted_keys])
            try: buf = zlib.decompress(byte_arr, -zlib.MAX_WBITS)
            except:
                try: buf = zlib.decompress(byte_arr)
                except: buf = byte_arr
            return buf
        except: return None

    def response(self, flow: http.HTTPFlow):
        url = flow.request.pretty_url.lower()

        # BYPASS CSP
        for h in ["Content-Security-Policy", "X-Content-Security-Policy"]:
            if h in flow.response.headers: del flow.response.headers[h]

        # 1. TRANSACTION SNIFFER (Pix & Depósito)
        if "trpc/payment" in url or "trpc/recharge" in url or "trpc/order" in url:
            try:
                data = json.loads(flow.response.text)
                res = data.get("result", {}).get("data", {}).get("json", {})
                tx_id = res.get("id") or res.get("orderId") or res.get("pixId") or "N/A"
                amount = res.get("amount") or res.get("price") or "0.00"
                
                if tx_id != "N/A":
                    self.log_console(f"[📡 SNIFFER] TRANSAÇÃO DETECTADA: ID={tx_id} Valor={amount}")
                    bridge = f"<script>window.vidente_tx_injetada = {{id: '{tx_id}', amount: '{amount}'}};</script>"
                    flow.response.text = flow.response.text + bridge
            except: pass

        # 2. GHOST BYPASS & LOGIN
        if "trpc/game.login" in url and flow.response.status_code == 400:
            self.log_console(f"[!] Bypass de Login v5.0...")
            s = self.session
            game_id = "3"
            try:
                inp = json.loads(urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('input', ['{}'])[0])
                game_id = str(inp.get("json", {}).get("gameId", game_id))
            except: pass
            
            ghost_url = (f"https://api.h-z-9-a.com/mines?gameMode=mines&operator=test&user={s.get('user')}"
                         f"&token={s.get('token')}&gid={game_id}&tid={s.get('tid')}&uid={s.get('uid')}&vv=v50_elite")
            fake_success = {"result": {"data": {"json": {"loginUrl": ghost_url}}}}
            flow.response.status_code = 200
            flow.response.text = json.dumps(fake_success)

        # 3. SPRIBE ENGINE (Mines & Aviator)
        if "/spribe/api/send" in url and flow.response.status_code == 200:
            try:
                raw_text = flow.response.text
                data = json.loads(raw_text)
                payload_dict = data.get("message") if isinstance(data.get("message"), dict) else (data if "0" in data else None)
                
                if payload_dict:
                    buf = self._quebrar_binario_spribe(payload_dict)
                    if buf:
                        # MINES SCAN
                        pts = []
                        for i in range(len(buf) - 1):
                            if buf[i] in [8, 16, 24, 32, 40] and 0 <= buf[i+1] <= 24:
                                pts.append(int(buf[i+1]))
                        bombas = sorted(list(set(pts))) if 1 <= len(set(pts)) <= 24 else None
                        
                        # AVIATOR SCAN (Heurística: Busca por ponto flutuante em bytes ou strings)
                        aviator_point = None
                        match = re.search(rb'[1-9]\.[0-9]{2}', buf)
                        if match: aviator_point = match.group().decode()

                        if bombas and len(bombas) > 1:
                            self.log_console(f"[💣 MINES] Vision: {bombas}")
                            flow.response.text = raw_text + f"<script>window.vidente_grid_injetado = {bombas};</script>"
                        elif aviator_point:
                            self.log_console(f"[✈️ AVIATOR] Crash Point: {aviator_point}x")
                            flow.response.text = raw_text + f"<script>window.vidente_aviator_injetado = '{aviator_point}';</script>"
            except: pass

        # 4. HUD Injection
        if "text/html" in flow.response.headers.get("Content-Type", ""):
            if b"vidente-hud" not in flow.response.content and b"</body>" in flow.response.content:
                flow.response.content = flow.response.content.replace(b"</body>", HUD_HTML.encode() + b"</body>")

addons = [Vidente()]
