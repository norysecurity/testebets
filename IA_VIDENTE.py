# ==============================================================================
# IA VIDENTE - v4.0 PRO DEBUG & PREDIÇÃO (Console + WS + Admin)
# ==============================================================================
import os
import json
import re
import zlib
from datetime import datetime
from mitmproxy import http, ctx

# Configurações
LOG_FILE = "vidente_history.log"
VERSION = "4.0.0"

# HUD Injetado (Draggable, Transparente, WS Hook + Admin)
HUD_HTML = """
<div id="vidente-hud" style="position:fixed; top:20px; left:20px; width:280px; background:rgba(10,10,10,0.92); border:2px solid #0ff; border-radius:12px; z-index:999999; color:white; font-family:monospace; padding:15px; box-shadow:0 0 20px #0ff; cursor: move; user-select: none; backdrop-filter: blur(10px);">
    <div style="font-weight:bold; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #333; padding-bottom: 5px;">
        <span style="color:#0ff; text-shadow: 0 0 5px #0ff;">🔮 VIDENTE v4.0 PRO</span>
        <span id="v-status" style="font-size:10px; color:#0f0;">WS: ATIVO</span>
    </div>
    
    <div id="v-grid" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:4px; margin:10px 0; background:rgba(0,0,0,0.6); padding:8px; border-radius:8px; border: 1px solid #222;">
        <!-- Grid cells -->
    </div>
    
    <div id="v-seeds" style="font-size:9px; color:#666; margin-bottom:10px; text-align:left; background:rgba(0,0,0,0.3); padding:5px; border-radius:4px; display:none;">
        <b>SEEDS:</b> <span id="v-server-seed">---</span>
    </div>

    <div style="font-size:10px; margin-top:10px; display:flex; gap:4px; justify-content:center; flex-wrap:wrap;">
        <button onclick="rotateGrid()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px; cursor:pointer; border-radius:4px; flex:1;">ROTAR</button>
        <button onclick="toggleMirror()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px; cursor:pointer; border-radius:4px; flex:1;">ESPELHAR</button>
        <button onclick="clearGrid()" style="background:#222; border:1px solid #f33; color:#f33; padding:5px; cursor:pointer; border-radius:4px; flex:1;">CLEAN</button>
        <button id="btn-admin" onclick="triggerAdmin()" style="background:linear-gradient(45deg, #f0f, #00f); border:none; color:white; padding:5px; cursor:pointer; border-radius:4px; font-size:9px; font-weight:bold; display:none; flex:1;">ADMIN PANEL</button>
    </div>
    <div id="v-mode" style="font-size:10px; color:#aaa; margin-top:8px; text-align:center; font-weight:bold;">AGUARDANDO APOSTA...</div>
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
                cell.style.background = transformed.includes(i) ? 'rgba(255,0,0,0.6)' : '#111';
                cell.style.border = transformed.includes(i) ? '1px solid #0ff' : '1px solid #333';
                cell.style.borderRadius = '3px';
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
            if (data.vidente_grid) { 
                baseGrid = data.vidente_grid; 
                document.getElementById('v-mode').innerText = "PREDICÇÃO REAL!"; 
                document.getElementById('v-mode').style.color = "#0f0";
                renderGrid(); 
            }
            if (data.vidente_seeds) { 
                document.getElementById('v-seeds').style.display = 'block'; 
                document.getElementById('v-server-seed').innerText = data.vidente_seeds.server.substring(0,10)+"..."; 
            }
            if (data.vidente_admin) { document.getElementById('btn-admin').style.display = 'block'; }
            
            // Suporte para Spribe (bet/state)
            if (data.action && (data.action === "bet" || data.action === "state" || data.action === "board")) {
                let d = data.data || {};
                if (d.mines) { baseGrid = d.mines; renderGrid(); }
                else if (d.bombPositions) { baseGrid = d.bombPositions; renderGrid(); }
            }
            if (data.dt && data.dt.cellNumber !== undefined) {
                revealedCells[data.dt.cellNumber] = data.dt.win > 0 ? 'gem' : 'mine';
                renderGrid();
            }
            
            // Scanner Universal Recursivo (v4.0 Pro)
            const scan = (obj) => {
                if (!obj || typeof obj !== 'object') return;
                if (Array.isArray(obj) && obj.length === 25) {
                    const b = obj.map((v, i) => (v === 1 || v === true || v === 'bomb' || v === 'MINE') ? i : -1).filter(x => x !== -1);
                    if (b.length > 0 && b.length < 25) { 
                        baseGrid = b; 
                        document.getElementById('v-mode').innerText = "VULNERABILIDADE DETECTADA!";
                        renderGrid(); 
                    }
                }
                if (Array.isArray(obj) && 2 <= obj.length <= 24 && obj.every(x => typeof x === 'number' && x >= 0 && x < 25)) {
                    if (baseGrid.length === 0) { baseGrid = obj; renderGrid(); }
                }
                Object.values(obj).forEach(val => { if(typeof val === 'object') scan(val); });
            };
            scan(data);
        };

        window.rotateGrid = () => { currentSymmetry = (currentSymmetry + 1) % 8; renderGrid(); };
        window.toggleMirror = () => { currentSymmetry = (currentSymmetry === 1 ? 0 : 1); renderGrid(); };
        window.clearGrid = () => { baseGrid = []; revealedCells = {}; renderGrid(); document.getElementById('v-mode').innerText = "AGUARDANDO..."; document.getElementById('v-mode').style.color = "#aaa"; };
        window.triggerAdmin = () => { window.location.href = '/admin'; };

        // Proxy Fetch
        const oldFetch = window.fetch;
        window.fetch = async (...args) => {
            const res = await oldFetch(...args);
            const clone = res.clone();
            try { const d = await clone.json(); (Array.isArray(d) ? d : [d]).forEach(handleData); } catch(e) {}
            return res;
        };

        // Proxy WebSocket
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
        
        // Listener para injeções via Flow
        setInterval(() => {
            if (window.vidente_grid_injetado) {
                handleData({vidente_grid: window.vidente_grid_injetado});
                window.vidente_grid_injetado = null;
            }
        }, 500);
    })();
</script>
"""

class Vidente:
    def __init__(self):
        self.log_file = LOG_FILE

    def log_console(self, text):
        """Imprime na tela (terminal) e salva no arquivo"""
        ts = datetime.now().strftime('%H:%M:%S')
        msg = f"[{ts}] {text}"
        print(msg)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def response(self, flow: http.HTTPFlow):
        # 1. CSP Bypass
        for h in ["Content-Security-Policy", "X-Content-Security-Policy", "Content-Security-Policy-Report-Only"]:
            if h in flow.response.headers: del flow.response.headers[h]

        url = flow.request.pretty_url.lower()

        # 2. Injeção de HUD (Spribe context)
        if "mines" in url and "text/html" in flow.response.headers.get("Content-Type", ""):
            if b"</body>" in flow.response.content:
                flow.response.content = flow.response.content.replace(b"</body>", HUD_HTML.encode() + b"</body>")
                self.log_console(f"[+] HUD v4.0 Pro Injetado na página!")

        # 3. Hook Admin (tRPC)
        if "trpc/user.details" in url and flow.response.status_code == 200:
            try:
                data = json.loads(flow.response.text)
                if "result" in data:
                    unode = data["result"]["data"]["json"]
                    unode.update({"role": "admin", "isAdmin": True, "permissions": ["*"]})
                    data["vidente_admin"] = True
                    flow.response.text = json.dumps(data)
                    self.log_console(f"[!] Escalando Privilégios para ID: {unode.get('id')}")
            except: pass

        # 4. Interceptação Centralizada Spribe (/spribe/api/send)
        if "/spribe/api/send" in url and flow.request.method == "POST":
            if flow.response.status_code == 200:
                try:
                    raw_text = flow.response.text
                    data = json.loads(raw_text)
                    size = len(raw_text)
                    
                    if size < 2000: # Focar em pacotes de ação (bet/win/click)
                        self.log_console(f"[*] Pacote Spribe Interceptado ({size} bytes). Analisando...")
                        
                        found_bombs = []
                        # Heurística de Varredura Recursiva v4
                        def deep_scan(obj):
                            nonlocal found_bombs
                            if isinstance(obj, dict):
                                if any(x in obj for x in ["mines", "bombPositions", "board", "cells"]):
                                    found_bombs = obj.get("mines") or obj.get("bombPositions") or obj.get("board") or obj.get("cells")
                                    return
                                for v in obj.values(): deep_scan(v)
                            elif isinstance(obj, list):
                                if all(isinstance(x, int) and 0 <= x < 25 for x in obj) and 2 <= len(obj) <= 24:
                                    found_bombs = obj
                                    return
                                for v in obj: deep_scan(v)
                        
                        deep_scan(data)
                        
                        # Fallback Heurística Binária (Mines/Protobuf)
                        if not found_bombs or not isinstance(found_bombs, list):
                            bin_bombs, seed = self._bin_scan(flow.response.content)
                            if bin_bombs: found_bombs = bin_bombs
                            if seed:
                                 if isinstance(data, list): data.append({"vidente_seeds": {"server": seed}})
                                 else: data["vidente_seeds"] = {"server": seed}

                        if found_bombs and isinstance(found_bombs, list):
                            self.log_console(f"    [!!!] VULNERABILIDADE DETECTADA: Bombas: {found_bombs}")
                            if isinstance(data, list): data.append({"vidente_grid": found_bombs})
                            else: data["vidente_grid"] = found_bombs
                            flow.response.text = json.dumps(data)
                        else:
                            self.log_console(f"    [-] Nenhuma mina clara encontrada. Preview: {raw_text[:150]}...")
                except Exception as e:
                    self.log_console(f"[ERR] Falha ao processar Spribe Send: {e}")

    def _bin_scan(self, raw):
        try: dec = zlib.decompress(raw, -zlib.MAX_WBITS)
        except:
            try: dec = zlib.decompress(raw)
            except: dec = raw
        
        bombs, seed = [], None
        m = re.search(b'serverSeed', dec)
        if m: seed = dec[m.end()+2:m.end()+66].decode(errors='ignore')
        
        for k in [b'mines', b'board', b'cells']:
            if k in dec:
                chunk = dec[dec.find(k):dec.find(k)+120]
                pts = [int(chunk[i]) for i in range(len(chunk)) if 0 <= chunk[i] < 25 and i > 0 and chunk[i-1] in [0x08, 0x10, 0x18, 0x20]]
                if 2 <= len(set(pts)) <= 24: bombs = list(set(pts))
        return bombs, seed

    def websocket_message(self, flow: http.HTTPFlow):
        msg = flow.websocket.messages[-1]
        if not msg.from_client:
            b, s = self._bin_scan(msg.content)
            if b:
                self.log_console(f"[WS] Bombas Detectadas em Tempo Real: {b}")
                try:
                    txt = msg.content.decode('utf-8', errors='ignore')
                    if "{" in txt:
                        st = txt.find('{'); end = txt.rfind('}') + 1
                        jd = json.loads(txt[st:end])
                        jd["vidente_grid"] = b
                        msg.content = (txt[:st] + json.dumps(jd) + txt[end:]).encode()
                except: pass

addons = [Vidente()]
