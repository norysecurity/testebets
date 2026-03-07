# ==============================================================================
# IA VIDENTE - v3.1 DEBUG & REPAIR (Cortex & WS Edition)
# ==============================================================================
import os
import json
import re
import zlib
from datetime import datetime
from mitmproxy import http, ctx

# Configurações
LOG_FILE = "vidente_history.log"
VERSION = "3.1.0"

# HUD Injetado (Draggable, Transparente, WS Hook + Admin)
HUD_HTML = """
<div id="vidente-hud" style="position:fixed; top:20px; right:20px; width:280px; background:rgba(10,10,10,0.90); border:1px solid #0ff; border-radius:12px; z-index:999999; color:white; font-family:monospace; padding:15px; box-shadow:0 0 20px rgba(0, 255, 255, 0.4); backdrop-filter: blur(8px); cursor: move; user-select: none;">
    <div style="font-weight:bold; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #333; padding-bottom: 5px;">
        <span style="color:#0ff; text-shadow: 0 0 5px #0ff;">🔮 VIDENTE v3.1</span>
        <span id="v-status" style="font-size:10px; color:#0f0;">WS: ATIVO</span>
    </div>
    
    <div id="v-grid" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:4px; margin:10px 0; background:rgba(0,0,0,0.6); padding:8px; border-radius:8px; border: 1px solid #222;">
        <!-- Grid cells generated here -->
    </div>
    
    <div id="v-seeds" style="font-size:9px; color:#666; margin-bottom:10px; text-align:left; background:rgba(0,0,0,0.3); padding:5px; border-radius:4px; display:none;">
        <b>SEEDS:</b> <span id="v-server-seed">---</span>
    </div>

    <div style="font-size:10px; margin-top:10px; display:flex; gap:4px; justify-content:center;">
        <button onclick="rotateGrid()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px; cursor:pointer; border-radius:4px; flex:1;">ROTAR</button>
        <button onclick="toggleMirror()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px; cursor:pointer; border-radius:4px; flex:1;">ESPELHAR</button>
        <button onclick="clearGrid()" style="background:#222; border:1px solid #f33; color:#f33; padding:5px; cursor:pointer; border-radius:4px; flex:1;">CLEAN</button>
    </div>
    <div id="v-mode" style="font-size:10px; color:#aaa; margin-top:8px; text-align:center; font-weight:bold;">AGUARDANDO...</div>
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

        let baseGrid = [];
        let currentSymmetry = 0;
        let revealedCells = {}; 

        const renderGrid = (mines) => {
            if (mines) baseGrid = mines;
            const gridDiv = document.getElementById('v-grid');
            gridDiv.innerHTML = '';
            let transformed = applySymmetry(baseGrid, currentSymmetry);
            for (let i = 0; i < 25; i++) {
                const cell = document.createElement('div');
                cell.style.width = '100%'; cell.style.paddingBottom = '100%';
                cell.style.background = transformed.includes(i) ? 'rgba(255,0,0,0.5)' : '#111';
                cell.style.border = '1px solid #333'; cell.style.borderRadius = '3px';
                cell.style.position = 'relative';
                if (revealedCells[i]) {
                    cell.style.background = revealedCells[i] === 'mine' ? '#411' : '#141';
                    cell.innerHTML = `<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);">${revealedCells[i] === 'mine' ? '💥' : '💎'}</span>`;
                } else if (transformed.includes(i)) {
                    cell.innerHTML = '<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); opacity:0.8;">💣</span>';
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
            if (data.vidente_grid) { baseGrid = data.vidente_grid; renderGrid(); document.getElementById('v-mode').innerText = "PREDICÇÃO REAL!"; document.getElementById('v-mode').style.color = "#0f0"; }
            if (data.vidente_seeds) { document.getElementById('v-seeds').style.display = 'block'; document.getElementById('v-server-seed').innerText = data.vidente_seeds.server.substring(0,10)+"..."; }
            
            // Suporte para Spribe data
            if (data.action && (data.action === "bet" || data.action === "state")) {
                let d = data.data || {};
                if (d.mines) { baseGrid = d.mines; renderGrid(); }
            }
            if (data.dt && data.dt.cellNumber !== undefined) {
                revealedCells[data.dt.cellNumber] = data.dt.win > 0 ? 'gem' : 'mine';
                renderGrid();
            }
            
            const scan = (obj) => {
                if (!obj || typeof obj !== 'object') return;
                if (Array.isArray(obj) && obj.length === 25) {
                    const b = obj.map((v, i) => (v === 1 || v === true || v === 'bomb') ? i : -1).filter(x => x !== -1);
                    if (b.length > 0 && b.length < 25) { baseGrid = b; renderGrid(); }
                }
                Object.values(obj).forEach(val => { if(typeof val === 'object') scan(val); });
            };
            scan(data);
        };

        window.rotateGrid = () => { currentSymmetry = (currentSymmetry + 1) % 8; renderGrid(); };
        window.toggleMirror = () => { currentSymmetry = (currentSymmetry === 1 ? 0 : 1); renderGrid(); };
        window.clearGrid = () => { baseGrid = []; revealedCells = {}; renderGrid(); document.getElementById('v-mode').innerText = "AGUARDANDO..."; };

        const oldFetch = window.fetch;
        window.fetch = async (...args) => {
            const res = await oldFetch(...args);
            const clone = res.clone();
            try { const d = await clone.json(); (Array.isArray(d) ? d : [d]).forEach(handleData); } catch(e) {}
            return res;
        };

        const OrigWS = window.WebSocket;
        window.WebSocket = function(url, p) {
            const ws = new OrigWS(url, p);
            ws.addEventListener('message', (e) => {
                try {
                    let txt = e.data.replace(/^[0-9]+/, '');
                    if (txt.startsWith('[')) { let a = JSON.parse(txt); if (a.length > 1) handleData(a[1]); }
                    else { handleData(JSON.parse(txt)); }
                } catch(err) {}
            });
            return ws;
        };
    })();
</script>
"""

class Vidente:
    def __init__(self):
        self.log_file = LOG_FILE

    def log(self, text):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {text}\n")

    def response(self, flow: http.HTTPFlow):
        # 1. CSP Bypass
        for h in ["Content-Security-Policy", "X-Content-Security-Policy", "Content-Security-Policy-Report-Only"]:
            if h in flow.response.headers: del flow.response.headers[h]

        url = flow.request.pretty_url.lower()

        # 2. Injeção Unificada (apenas no Iframe ou se contiver Mines)
        if "mines" in url and "text/html" in flow.response.headers.get("Content-Type", ""):
            if b"</body>" in flow.response.content:
                flow.response.content = flow.response.content.replace(b"</body>", HUD_HTML.encode() + b"</body>")
                self.log(f"[HUD v3.1] Injetado: {url}")

        # 3. Hook Admin tRPC
        if "trpc/user.details" in url and flow.response.status_code == 200:
            try:
                data = json.loads(flow.response.text)
                if "result" in data:
                    node = data["result"]["data"]["json"]
                    node.update({"role": "admin", "isAdmin": True})
                    flow.response.text = json.dumps(data)
                    self.log(f"[ADMIN] Hook Ativo: {node.get('id')}")
            except: pass

        # 4. Interceptação Spribe Avançada
        if "/spribe/api/send" in url and flow.request.method == "POST":
            if flow.response.status_code == 200:
                try:
                    data = json.loads(flow.response.text)
                    self.log(f"[DEBUG] Spribe Response ({len(flow.response.text)} chars)")
                    
                    found_bombs = []
                    # Varredura Recursiva Universal para achar 'mines'
                    def deep_scan(obj):
                        nonlocal found_bombs
                        if isinstance(obj, dict):
                            if "mines" in obj and isinstance(obj["mines"], list): found_bombs = obj["mines"]
                            elif "bombPositions" in obj: found_bombs = obj["bombPositions"]
                            for v in obj.values(): deep_scan(v)
                        elif isinstance(obj, list):
                            for v in obj: deep_scan(v)
                    
                    deep_scan(data)
                    
                    if not found_bombs:
                        # Fallback Heurística Binária
                        bombs, seed = self._bin_scan(flow.response.content)
                        if bombs: found_bombs = bombs
                        if seed:
                             if isinstance(data, list): data.append({"vidente_seeds": {"server": seed}})
                             else: data["vidente_seeds"] = {"server": seed}

                    if found_bombs:
                        self.log(f"[VIDENTE] BOMBAS CAPTURADAS: {found_bombs}")
                        if isinstance(data, list): data.append({"vidente_grid": found_bombs})
                        else: data["vidente_grid"] = found_bombs
                        flow.response.text = json.dumps(data)
                except Exception as e:
                    self.log(f"[ERR] Falha ao processar Spribe: {e}")

    def _bin_scan(self, raw):
        try: dec = zlib.decompress(raw, -zlib.MAX_WBITS)
        except:
            try: dec = zlib.decompress(raw)
            except: dec = raw
        
        bombs = []
        seed = None
        
        # Semente
        m = re.search(b'serverSeed', dec)
        if m: seed = dec[m.end()+2:m.end()+66].decode(errors='ignore')
        
        # Bombas (Heurística Spribe v4)
        for m in re.finditer(b'mines', dec):
            # Procura por números pequenos logo após a tag
            chunk = dec[m.end():m.end()+100]
            pts = []
            for i in range(len(chunk)):
                if 0 <= chunk[i] < 25:
                    if i > 0 and chunk[i-1] in [0x08, 0x10, 0x18, 0x20]:
                        pts.append(int(chunk[i]))
            if 1 <= len(set(pts)) <= 24: bombs = list(set(pts))
            
        return bombs, seed

    def websocket_message(self, flow: http.HTTPFlow):
        msg = flow.websocket.messages[-1]
        if not msg.from_client:
            b, s = self._bin_scan(msg.content)
            if b:
                self.log(f"[WS] Bombas WS: {b}")
                try:
                    txt = msg.content.decode('utf-8', errors='ignore')
                    if "{" in txt:
                        start = txt.find('{'); end = txt.rfind('}') + 1
                        jd = json.loads(txt[start:end])
                        jd["vidente_grid"] = b
                        msg.content = (txt[:start] + json.dumps(jd) + txt[end:]).encode()
                except: pass

addons = [Vidente()]
