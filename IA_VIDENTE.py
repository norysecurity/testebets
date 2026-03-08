# ==============================================================================
# IA VIDENTE - v4.3 DEEP CORTEX (Money Hook & Login Bypass)
# ==============================================================================
import os
import json
import re
import zlib
from datetime import datetime
from mitmproxy import http, ctx

# Configurações
LOG_FILE = "vidente_history.log"
VERSION = "4.3.0"

# HUD Injetado (Draggable, v4.3 Pro Design)
HUD_HTML = """
<div id="vidente-hud" style="position:fixed; top:20px; left:20px; width:280px; background:rgba(10,10,10,0.95); border:2px solid #0ff; border-radius:12px; z-index:999999; color:white; font-family:monospace; padding:15px; box-shadow:0 0 30px rgba(0,255,255,0.5); cursor: move; user-select: none; backdrop-filter: blur(15px);">
    <div style="font-weight:bold; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #0ff; padding-bottom: 5px;">
        <span style="color:#0ff; text-shadow: 0 0 10px #0ff;">🔮 VIDENTE v4.3 ALPHA</span>
        <span id="v-status" style="font-size:10px; color:#0f0;">BYPASS: ON</span>
    </div>
    
    <div id="v-grid" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:6px; margin:10px 0; background:rgba(0,0,0,0.8); padding:10px; border-radius:8px; border: 1px solid #333;">
        <!-- Grid cells -->
    </div>
    
    <div id="v-balance-info" style="font-size:11px; color:#0f0; margin-bottom:8px; text-align:center; background:rgba(0,255,0,0.1); padding:5px; border-radius:4px; border: 1px solid #0f0;">
        💰 SALDO INJETADO: R$ <span id="v-current-balance">9.999.999,00</span>
    </div>

    <div style="font-size:10px; margin-top:10px; display:flex; gap:4px; justify-content:center; flex-wrap:wrap;">
        <button onclick="rotateGrid()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:8px; cursor:pointer; border-radius:4px; flex:1; font-weight:bold;">ROTAR</button>
        <button onclick="toggleMirror()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:8px; cursor:pointer; border-radius:4px; flex:1; font-weight:bold;">ESPELHAR</button>
        <button onclick="clearGrid()" style="background:#222; border:1px solid #f33; color:#f33; padding:8px; cursor:pointer; border-radius:4px; flex:1; font-weight:bold;">CLEAN</button>
    </div>
    <div id="v-mode" style="font-size:11px; color:#ff0; margin-top:10px; text-align:center; font-weight:bold; letter-spacing:1px; text-shadow:0 0 5px #ff0;">AGUARDANDO APOSTA...</div>
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

        let baseGrid = []; let currentSymmetry = 0; let revealedCells = {}; 

        const renderGrid = (mines) => {
            if (mines) baseGrid = mines;
            const gridDiv = document.getElementById('v-grid');
            gridDiv.innerHTML = '';
            let transformed = applySymmetry(baseGrid, currentSymmetry);
            for (let i = 0; i < 25; i++) {
                const cell = document.createElement('div');
                cell.style.width = '100%'; cell.style.paddingBottom = '100%';
                cell.style.background = transformed.includes(i) ? 'rgba(255,0,0,0.8)' : '#111';
                cell.style.border = transformed.includes(i) ? '2px solid #f00' : '1px solid #444';
                cell.style.borderRadius = '5px'; cell.style.position = 'relative';
                
                if (revealedCells[i]) {
                    cell.style.background = revealedCells[i] === 'mine' ? '#411' : '#141';
                    cell.innerHTML = `<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:18px;">${revealedCells[i] === 'mine' ? '💥' : '💎'}</span>`;
                } else if (transformed.includes(i)) {
                    cell.innerHTML = '<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:14px;">💣</span>';
                }
                gridDiv.appendChild(cell);
            }
        };

        const applySymmetry = (mines, sym) => {
            return mines.map(idx => {
                let r = Math.floor(idx / 5), c = idx % 5;
                if (sym === 1) c = 4 - c; if (sym === 2) r = 4 - r;
                if (sym === 3) { let t = r; r = c; c = 4 - t; }
                if (sym === 4) { r = 4 - r; c = 4 - c; }
                if (sym === 5) { let t = r; r = 4 - c; c = t; }
                if (sym === 6) { let t = r; r = c; c = t; }
                if (sym === 7) { let t = r; r = 4 - c; c = 4 - r; }
                return r * 5 + c;
            });
        };

        const handleData = (data) => {
            if (!data) return;
            if (data.vidente_grid) { 
                baseGrid = data.vidente_grid; 
                document.getElementById('v-mode').innerText = "VULNERABILIDADE ATIVA!"; 
                document.getElementById('v-mode').style.color = "#0f0";
                renderGrid(); 
            }
            if (data.vidente_balance) {
                document.getElementById('v-current-balance').innerText = data.vidente_balance;
            }
            
            const scan = (obj) => {
                if (!obj || typeof obj !== 'object') return;
                Object.values(obj).forEach(val => { if(typeof val === 'object') scan(val); });
            };
            scan(data);
        };

        window.rotateGrid = () => { currentSymmetry = (currentSymmetry + 1) % 8; renderGrid(); };
        window.toggleMirror = () => { currentSymmetry = (currentSymmetry === 1 ? 0 : 1); renderGrid(); };
        window.clearGrid = () => { baseGrid = []; revealedCells = {}; renderGrid(); document.getElementById('v-mode').innerText = "AGUARDANDO..."; document.getElementById('v-mode').style.color = "#ff0"; };

        // Bypass de Balanço Global
        window.balance = 9999999;
        window.totalBalance = 9999999;
    })();
</script>
"""

class Vidente:
    def __init__(self):
        self.log_file = LOG_FILE

    def log_console(self, text):
        ts = datetime.now().strftime('%H:%M:%S')
        msg = f"[{ts}] {text}"
        print(msg)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def _quebrar_binario_spribe(self, payload_dict):
        try:
            chaves = list(payload_dict.keys())
            if not any(k.isdigit() for k in chaves[:5]): return None
            chaves_int = sorted([int(k) for k in chaves if k.isdigit()])
            byte_array = bytearray([int(payload_dict[str(k)]) for k in chaves_int])
            try: buf = zlib.decompress(byte_array, -zlib.MAX_WBITS)
            except:
                try: buf = zlib.decompress(byte_array)
                except: buf = byte_array
            bombs = []
            pts = []
            for i in range(len(buf) - 1):
                if buf[i] in [8, 16, 24, 32, 40] and 0 <= buf[i+1] <= 24:
                    pts.append(int(buf[i+1]))
            if 1 <= len(set(pts)) <= 24: bombs = sorted(list(set(pts)))
            return bombs
        except: return None

    def response(self, flow: http.HTTPFlow):
        url = flow.request.pretty_url.lower()

        # BYPASS CSP
        for h in ["Content-Security-Policy", "X-Content-Security-Policy"]:
            if h in flow.response.headers: del flow.response.headers[h]

        # 1. BYPASS DE LOGIN (ERRO 400 -> 200)
        if "trpc/game.login" in url:
            if flow.response.status_code == 400:
                self.log_console(f"[BYPASS] Detectado bloqueio de Login (Erro 400). Forando Sada 200...")
                flow.response.status_code = 200
                fake_success = {
                    "result": {
                        "data": {
                            "json": {
                                "gameUrl": "https://api.h-z-9-a.com/mines?operator=test&jurisdiction=CW&lang=pt",
                                "token": "vidente_bypass_token_" + datetime.now().strftime("%Y%m%d%H%M"),
                                "status": "PLAYABLE"
                            }
                        }
                    }
                }
                flow.response.text = json.dumps(fake_success)

        # 2. MONEY HOOK (Injeo de Saldo no tRPC)
        if "trpc/user.details" in url:
            try:
                data = json.loads(flow.response.text)
                if "result" in data:
                    node = data["result"]["data"]["json"]
                    node.update({
                        "role": "admin",
                        "isAdmin": True,
                        "balance": 9999999,
                        "totalBalance": 9999999,
                        "rechargeAmount": 1000,
                        "vipLevel": 10
                    })
                    flow.response.text = json.dumps(data)
                    self.log_console(f"[$] MONEY HOOK ATIVO: Saldo Fantasma Injetado (R$ 9.999.999,00)")
            except: pass

        # 3. HUD v4.3 injeo
        if "mines" in url and "text/html" in flow.response.headers.get("Content-Type", ""):
            if b"vidente-hud" not in flow.response.content and b"</body>" in flow.response.content:
                flow.response.content = flow.response.content.replace(b"</body>", HUD_HTML.encode() + b"</body>")
                self.log_console(f"[HUD v4.3] Deep Cortex & Bypass Ativado.")

        # 4. Motor de Busca de Bombas (Deep Cortex)
        if "/spribe/api/send" in url and flow.request.method == "POST":
            if flow.response.status_code == 200:
                try:
                    data = json.loads(flow.response.text)
                    payload_bin = None
                    if "message" in data and isinstance(data["message"], dict): payload_bin = data["message"]
                    elif isinstance(data, dict) and "0" in data: payload_bin = data

                    bombas = self._quebrar_binario_spribe(payload_bin) if payload_bin else None
                    if bombas and isinstance(bombas, list):
                        self.log_console(f"    [!!!] BOMBAS DETECTADAS: {bombas}")
                        bridge = f"<script>window.vidente_grid_injetado = {bombas};</script>"
                        flow.response.text = flow.response.text + bridge
                except: pass

addons = [Vidente()]
