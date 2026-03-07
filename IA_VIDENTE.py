# ==============================================================================
# IA VIDENTE - v3.0 PREDIÇÃO ABSOLUTA (Cortex & WS Edition)
# ==============================================================================
import os
import json
import re
import zlib
from datetime import datetime
from mitmproxy import http, ctx

# Configurações
LOG_FILE = "vidente_history.log"
VERSION = "3.0.0"

# HUD Injetado (Arrastável, Transparente e com Hook de WebSocket + Admin)
HUD_HTML = """
<div id="vidente-hud" style="position:fixed; top:20px; right:20px; width:280px; background:rgba(10,10,10,0.85); border:1px solid #0ff; border-radius:12px; z-index:999999; color:white; font-family:monospace; padding:15px; box-shadow:0 0 15px rgba(0, 255, 255, 0.4); backdrop-filter: blur(5px); cursor: move; user-select: none; transition: box-shadow 0.3s;">
    <div style="font-weight:bold; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #333; padding-bottom: 5px;">
        <span style="color:#0ff; text-shadow: 0 0 5px #0ff;">🔮 VIDENTE v3.0</span>
        <span id="v-status" style="font-size:10px; color:#0f0;">WS: ATIVO</span>
    </div>
    
    <div id="v-grid" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:4px; margin:10px 0; background:rgba(0,0,0,0.5); padding:8px; border-radius:8px;">
        <!-- Board gerado via JS -->
    </div>

    <div id="v-seeds" style="font-size:9px; color:#aaa; margin-bottom:10px; text-align:left; background:rgba(255,255,255,0.05); padding:5px; border-radius:5px; display:none;">
        <b>SEEDS DETECTADOS:</b><br>
        <span id="v-server-seed">S: ---</span><br>
        <span id="v-client-seed">C: ---</span>
    </div>
    
    <div style="font-size:10px; margin-top:10px; display:flex; gap:5px; justify-content:center; flex-wrap:wrap;">
        <button onclick="rotateGrid()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px; cursor:pointer; border-radius:4px; flex:1;">ROTAR</button>
        <button onclick="toggleMirror()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px; cursor:pointer; border-radius:4px; flex:1;">ESPELHAR</button>
        <button onclick="clearGrid()" style="background:#222; border:1px solid #f00; color:#f00; padding:5px; cursor:pointer; border-radius:4px; flex:1;">LIMPAR</button>
        <button id="btn-admin" onclick="triggerAdmin()" style="background:linear-gradient(45deg, #f0f, #00f); border:none; color:white; padding:5px; cursor:pointer; border-radius:4px; font-size:9px; font-weight:bold; display:none; flex:1;">ADMIN PANEL</button>
    </div>
    <div id="v-mode" style="font-size:10px; color:#aaa; margin-top:8px; text-align:center;">AGUARDANDO APOSTA...</div>
</div>

<script>
    // --- LÓGICA DE ARRASTAR O HUD (DRAG & DROP) ---
    const hud = document.getElementById('vidente-hud');
    let isDragging = false, startX, startY, initialLeft, initialTop;
    
    hud.addEventListener('mousedown', (e) => {
        if(e.target.tagName === 'BUTTON') return;
        isDragging = true;
        hud.style.boxShadow = "0 0 25px rgba(0, 255, 255, 0.8)";
        startX = e.clientX; startY = e.clientY;
        const rect = hud.getBoundingClientRect();
        initialLeft = rect.left; initialTop = rect.top;
        hud.style.right = 'auto'; hud.style.bottom = 'auto';
        hud.style.left = initialLeft + 'px'; hud.style.top = initialTop + 'px';
    });

    window.addEventListener('mousemove', (e) => {
        if(!isDragging) return;
        const dx = e.clientX - startX; const dy = e.clientY - startY;
        hud.style.left = (initialLeft + dx) + 'px'; hud.style.top = (initialTop + dy) + 'px';
    });

    window.addEventListener('mouseup', () => { isDragging = false; hud.style.boxShadow = "0 0 15px rgba(0, 255, 255, 0.4)"; });

    // --- LÓGICA DO GRID E CALIBRAÇÃO ---
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
            cell.style.background = transformed.includes(i) ? 'rgba(255,50,50,0.6)' : '#1a1a1a';
            cell.style.border = transformed.includes(i) ? '1px solid #f00' : '1px solid #333';
            cell.style.borderRadius = '4px'; cell.style.position = 'relative';
            if (revealedCells[i]) {
                cell.style.background = revealedCells[i] === 'mine' ? '#411' : '#141';
                cell.innerHTML = `<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:12px;">${revealedCells[i] === 'mine' ? '💥' : '💎'}</span>`;
            } else if (transformed.includes(i)) {
                cell.innerHTML = '<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); opacity:0.9; font-size:12px;">💣</span>';
            }
            gridDiv.appendChild(cell);
        }
    };

    const applySymmetry = (mines, sym) => {
        return mines.map(idx => {
            let r = Math.floor(idx / 5); let c = idx % 5;
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
        if (data.vidente_grid && data.vidente_grid.length > 0) {
            baseGrid = data.vidente_grid;
            document.getElementById('v-mode').innerText = "PREVISÃO CARREGADA";
            document.getElementById('v-mode').style.color = "#0f0";
            renderGrid();
        }
        if (data.vidente_seeds) {
             document.getElementById('v-seeds').style.display = 'block';
             document.getElementById('v-server-seed').innerText = "S: " + data.vidente_seeds.server.substring(0,20) + "...";
             document.getElementById('v-client-seed').innerText = "C: " + (data.vidente_seeds.client || "DEMO");
        }
        if (data.vidente_admin) { document.getElementById('btn-admin').style.display = 'block'; }
        if (data.mines && Array.isArray(data.mines)) { baseGrid = data.mines; renderGrid(); }
        if (data.dt && data.dt.cellNumber !== undefined) {
             revealedCells[data.dt.cellNumber] = data.dt.win > 0 ? 'gem' : 'mine';
             renderGrid();
        }
        const scan = (obj) => {
            if (!obj || typeof obj !== 'object') return;
            if (Array.isArray(obj) && obj.length === 25) {
                const b = obj.map((v, i) => (v === 1 || v === true || v === 'bomb') ? i : -1).filter(x => x !== -1);
                if (b.length > 0 && b.length < 25 && baseGrid.length === 0) { baseGrid = b; renderGrid(); }
            }
            Object.values(obj).forEach(val => { if(typeof val === 'object') scan(val); });
        };
        scan(data);
    };

    window.rotateGrid = () => { currentSymmetry = (currentSymmetry + 1) % 8; renderGrid(); };
    window.clearGrid = () => { baseGrid = []; revealedCells = {}; renderGrid(); document.getElementById('v-mode').innerText = "AGUARDANDO..."; document.getElementById('v-mode').style.color = "#aaa"; };
    window.toggleMirror = () => { currentSymmetry = (currentSymmetry === 1 ? 0 : 1); renderGrid(); };
    window.triggerAdmin = () => { window.location.href = '/admin'; };

    const oldFetch = window.fetch;
    window.fetch = async (...args) => {
        const res = await oldFetch(...args);
        const clone = res.clone();
        try { const d = await clone.json(); handleData(d); } catch(e) {}
        return res;
    };
    
    const OrigWebSocket = window.WebSocket;
    window.WebSocket = function(url, protocols) {
        const ws = new OrigWebSocket(url, protocols);
        ws.addEventListener('message', function(event) {
            try {
                if (typeof event.data === 'string') {
                    let cleanData = event.data.replace(/^[0-9]+/, '');
                    if (cleanData.startsWith('[')) {
                        let parsedArray = JSON.parse(cleanData);
                        if (parsedArray.length > 1) handleData(parsedArray[1]);
                    } else { handleData(JSON.parse(cleanData)); }
                }
            } catch(e) {}
        });
        return ws;
    };
</script>
"""

class Vidente:
    def __init__(self):
        self.log_file = LOG_FILE
        if not os.path.exists(self.log_file): open(self.log_file, "w").close()

    def log(self, text):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {text}\n")
            
    def _analisar_payload_binario(self, raw_bytes):
        try: decoded = zlib.decompress(raw_bytes, -zlib.MAX_WBITS)
        except:
            try: decoded = zlib.decompress(raw_bytes)
            except: decoded = raw_bytes
            
        bombs = []
        seeds = {}
        
        # Sementes (Spribe)
        seed_match = re.search(b'serverSeed', decoded)
        if seed_match:
            s_start = seed_match.end() + 2
            seeds["server"] = decoded[s_start:s_start+64].decode(errors='ignore')

        for key in [b"mines", b"cells", b"bombPositions"]:
            if key in decoded:
                idx = decoded.find(key) + len(key)
                for i in range(idx, min(idx+50, len(decoded))):
                    val = decoded[i]
                    if 0 <= val < 25 and len(bombs) < 24: bombs.append(int(val))
                if bombs: return list(set(bombs)), seeds
                
        if len(decoded) > 50:
            potential = []
            for i in range(1, len(decoded) - 1):
                val = decoded[i]
                if 0 <= val < 25 and decoded[i-1] in [0x08, 0x10, 0x18, 0x20, 0x28]:
                    potential.append(int(val))
            unique_bombs = list(set(potential))
            if 2 <= len(unique_bombs) < 25: return unique_bombs, seeds
                
        return None, seeds

    def response(self, flow: http.HTTPFlow):
        # 1. CSP Bypass
        for h in ["Content-Security-Policy", "X-Content-Security-Policy", "Content-Security-Policy-Report-Only"]:
            if h in flow.response.headers: del flow.response.headers[h]

        # 2. Injeção HUD Arrastável
        if "text/html" in flow.response.headers.get("Content-Type", ""):
            if b"</body>" in flow.response.content:
                flow.response.content = flow.response.content.replace(b"</body>", HUD_HTML.encode() + b"</body>")
                self.log(f"[HUD] v3.0 Injetado: {flow.request.pretty_url}")

        req_url = flow.request.pretty_url.lower()

        # 3. Escalabilidade Admin (tRPC Hook)
        if "trpc/user.details" in req_url and flow.response.status_code == 200:
            try:
                data = json.loads(flow.response.text)
                if "result" in data:
                    unode = data["result"]["data"]["json"]
                    unode["role"] = "admin"
                    unode["isAdmin"] = True
                    unode["permissions"] = ["*"]
                    data["vidente_admin"] = True
                    flow.response.text = json.dumps(data)
                    self.log(f"[ADMIN] Hook Ativo para ID {unode.get('id')}")
            except: pass

        # 4. Interceptação Centralizada Spribe (/api/send)
        if "/spribe/api/send" in req_url and flow.request.method == "POST":
            if flow.response.status_code == 200:
                try:
                    data = json.loads(flow.response.text)
                    bombs = []
                    
                    if isinstance(data, list):
                        for item in data:
                            msg = item.get("message", {})
                            msg_data = msg.get("data", {})
                            action = msg.get("action", "")
                            if action in ["bet", "state", "board", "init"]:
                                if "mines" in msg_data: bombs = msg_data["mines"]
                                elif "bombPositions" in msg_data: bombs = msg_data["bombPositions"]
                    
                    if not bombs and flow.response.content:
                        # Tentar análise binária se o JSON não for óbvio
                        raw_msg = flow.response.content
                        bin_bombs, seeds = self._analisar_payload_binario(raw_msg)
                        if bin_bombs: bombs = bin_bombs
                        if seeds: data["vidente_seeds"] = seeds

                    if bombs:
                        if isinstance(data, list): data.append({"vidente_grid": bombs})
                        else: data["vidente_grid"] = bombs
                        flow.response.text = json.dumps(data)
                        self.log(f"[VIDENTE-v3] Predição Capturada: {bombs}")
                except Exception as e: self.log(f"Erro Spribe Send: {e}")

    def websocket_message(self, flow: http.HTTPFlow):
        msg = flow.websocket.messages[-1]
        if not msg.from_client:
            bombs, seeds = self._analisar_payload_binario(msg.content)
            if bombs:
                self.log(f"[WS] Bombas Detectadas: {bombs}")
                try:
                    txt = msg.content.decode('utf-8', errors='ignore')
                    if "{" in txt:
                        start, end = txt.find('{'), txt.rfind('}') + 1
                        jd = json.loads(txt[start:end])
                        jd["vidente_grid"] = bombs
                        if seeds: jd["vidente_seeds"] = seeds
                        msg.content = (txt[:start] + json.dumps(jd) + txt[end:]).encode('utf-8')
                        self.log("[WS] Injeção real-time concluída.")
                except: pass

addons = [Vidente()]
