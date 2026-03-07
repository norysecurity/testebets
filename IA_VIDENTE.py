# ==============================================================================
# IA VIDENTE - v4.2 DEEP CORTEX (Decoder Binário de Elite)
# ==============================================================================
import os
import json
import re
import zlib
from datetime import datetime
from mitmproxy import http, ctx

# Configurações
LOG_FILE = "vidente_history.log"
VERSION = "4.2.0"

# HUD Injetado (Draggable, v4.2 Pro Design)
HUD_HTML = """
<div id="vidente-hud" style="position:fixed; top:20px; left:20px; width:280px; background:rgba(10,10,10,0.92); border:2px solid #0ff; border-radius:12px; z-index:999999; color:white; font-family:monospace; padding:15px; box-shadow:0 0 25px rgba(0,255,255,0.4); cursor: move; user-select: none; backdrop-filter: blur(12px);">
    <div style="font-weight:bold; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid #333; padding-bottom: 5px;">
        <span style="color:#0ff; text-shadow: 0 0 8px #0ff;">🔮 VIDENTE v4.2 DEEP CORTEX</span>
        <span id="v-status" style="font-size:10px; color:#0f0;">WS: ATIVO</span>
    </div>
    
    <div id="v-grid" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:6px; margin:10px 0; background:rgba(0,0,0,0.7); padding:10px; border-radius:8px; border: 1px solid #222;">
        <!-- Grid cells -->
    </div>
    
    <div id="v-seeds" style="font-size:9px; color:#666; margin-bottom:10px; text-align:left; background:rgba(0,0,0,0.3); padding:5px; border-radius:4px; display:none; border:1px solid #333;">
        <b>SEEDS:</b> <span id="v-server-seed">---</span>
    </div>

    <div style="font-size:10px; margin-top:10px; display:flex; gap:4px; justify-content:center; flex-wrap:wrap;">
        <button onclick="rotateGrid()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:6px; cursor:pointer; border-radius:4px; flex:1; font-weight:bold;">ROTAR</button>
        <button onclick="toggleMirror()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:6px; cursor:pointer; border-radius:4px; flex:1; font-weight:bold;">ESPELHAR</button>
        <button onclick="clearGrid()" style="background:#222; border:1px solid #f33; color:#f33; padding:6px; cursor:pointer; border-radius:4px; flex:1; font-weight:bold;">LIMPAR</button>
        <button id="btn-admin" onclick="triggerAdmin()" style="background:linear-gradient(45deg, #f0f, #00f); border:none; color:white; padding:6px; cursor:pointer; border-radius:4px; font-size:9px; font-weight:bold; display:none; flex:1; box-shadow:0 0 10px #f0f;">ADMIN PANEL</button>
    </div>
    <div id="v-mode" style="font-size:11px; color:#aaa; margin-top:10px; text-align:center; font-weight:bold; text-transform:uppercase; letter-spacing:1px;">AGUARDANDO APOSTA...</div>
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
                cell.style.background = transformed.includes(i) ? 'rgba(255,0,0,0.7)' : '#111';
                cell.style.border = transformed.includes(i) ? '1px solid #f00' : '1px solid #333';
                cell.style.borderRadius = '5px'; cell.style.position = 'relative';
                cell.style.boxShadow = transformed.includes(i) ? 'inset 0 0 10px rgba(255,0,0,0.5)' : 'none';
                
                if (revealedCells[i]) {
                    cell.style.background = revealedCells[i] === 'mine' ? '#411' : '#141';
                    cell.style.border = revealedCells[i] === 'mine' ? '1px solid #f00' : '1px solid #0f0';
                    cell.innerHTML = `<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:16px;">${revealedCells[i] === 'mine' ? '💥' : '💎'}</span>`;
                } else if (transformed.includes(i)) {
                    cell.innerHTML = '<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:14px; opacity:0.9;">💣</span>';
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
                document.getElementById('v-mode').innerText = "PREVISÃO ENCONTRADA!"; 
                document.getElementById('v-mode').style.color = "#0f0";
                renderGrid(); 
            }
            if (data.vidente_seeds) { 
                document.getElementById('v-seeds').style.display = 'block'; 
                document.getElementById('v-server-seed').innerText = data.vidente_seeds.server.substring(0,12)+"..."; 
            }
            if (data.vidente_admin) { document.getElementById('btn-admin').style.display = 'block'; }
            
            // Scanner Spribe Genérico
            if (data.action && (data.action === "bet" || data.action === "state" || data.action === "board" || data.action === "next")) {
                let d = data.data || {};
                if (d.mines) { baseGrid = d.mines; renderGrid(); }
                else if (d.bombPositions) { baseGrid = d.bombPositions; renderGrid(); }
            }
            if (data.dt && data.dt.cellNumber !== undefined) {
                revealedCells[data.dt.cellNumber] = data.dt.win > 0 ? 'gem' : 'mine';
                renderGrid();
            }
            
            const scan = (obj) => {
                if (!obj || typeof obj !== 'object') return;
                if (Array.isArray(obj) && obj.length === 25) {
                    const b = obj.map((v, i) => (v === 1 || v === true || v === 'bomb' || v === 'MINE') ? i : -1).filter(x => x !== -1);
                    if (b.length > 0 && b.length < 25) { baseGrid = b; renderGrid(); }
                }
                if (Array.isArray(obj) && 2 <= obj.length <= 24 && obj.every(x => typeof x === 'number' && x >= 0 && x < 25)) {
                    if (baseGrid.length === 0 || data.vidente_grid) { baseGrid = obj; renderGrid(); }
                }
                Object.values(obj).forEach(val => { if(typeof val === 'object') scan(val); });
            };
            scan(data);
        };

        window.rotateGrid = () => { currentSymmetry = (currentSymmetry + 1) % 8; renderGrid(); };
        window.toggleMirror = () => { currentSymmetry = (currentSymmetry === 1 ? 0 : 1); renderGrid(); };
        window.clearGrid = () => { baseGrid = []; revealedCells = {}; renderGrid(); document.getElementById('v-mode').innerText = "AGUARDANDO..."; document.getElementById('v-mode').style.color = "#aaa"; };
        window.triggerAdmin = () => { window.location.href = '/admin'; };

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
        
        setInterval(() => {
            if (window.vidente_grid_injetado) {
                handleData({vidente_grid: window.vidente_grid_injetado});
                window.vidente_grid_injetado = null;
            }
        }, 300);
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
        """Conversão Única: Dicionário de Índices para Buffer Decodificado"""
        try:
            chaves = list(payload_dict.keys())
            if not any(k.isdigit() for k in chaves[:5]): return None
            
            sorted_keys = sorted([int(k) for k in chaves if k.isdigit()])
            byte_array = bytearray([int(payload_dict[str(k)]) for k in sorted_keys])
            
            # Descompressão Spribe (Zlib/Deflate)
            try: buf = zlib.decompress(byte_array, -zlib.MAX_WBITS)
            except:
                try: buf = zlib.decompress(byte_array)
                except: buf = byte_array

            bombs = []
            # Técnica A: Busca por Literal Tags
            for tag in [b"mines", b"cells", b"bombPositions", b"board"]:
                idx = buf.find(tag)
                if idx != -1:
                    chunk = buf[idx + len(tag):idx + len(tag) + 60]
                    found = [int(i) for i in chunk if 0 <= i < 25]
                    if 1 <= len(set(found)) <= 24: return sorted(list(set(found)))

            # Técnica B: Protobuf Scan Cluster (0x08, 0x10, etc)
            pts = []
            for i in range(len(buf) - 1):
                if buf[i] in [8, 16, 24, 32, 40] and 0 <= buf[i+1] <= 24:
                    pts.append(int(buf[i+1]))
            
            if 1 <= len(set(pts)) <= 24: return sorted(list(set(pts)))

        except Exception as e:
            self.log_console(f"[!] Falha no Decoder Deep Cortex: {e}")
        return None

    def response(self, flow: http.HTTPFlow):
        # CSP Bypass Global
        for h in ["Content-Security-Policy", "X-Content-Security-Policy"]:
            if h in flow.response.headers: del flow.response.headers[h]

        url = flow.request.pretty_url.lower()

        # 1. Injeção de HUD v4.2 Pro
        if "mines" in url and "text/html" in flow.response.headers.get("Content-Type", ""):
            if b"vidente-hud" not in flow.response.content and b"</body>" in flow.response.content:
                flow.response.content = flow.response.content.replace(b"</body>", HUD_HTML.encode() + b"</body>")
                self.log_console(f"[+] HUD v4.2 Deep Cortex Ativo: {url[:50]}")

        # 2. Admin Hook (tRPC)
        if "trpc/user.details" in url:
            try:
                data = json.loads(flow.response.text)
                if "result" in data:
                    user = data["result"]["data"]["json"]
                    user.update({"role": "admin", "isAdmin": True})
                    data["vidente_admin"] = True
                    flow.response.text = json.dumps(data)
                    self.log_console(f"[!] PRIVILÉGIO DE ADMIN INJETADO para ID {user.get('id')}")
            except: pass

        # 3. Interceptação Centralizada (Spribe POST /send)
        if "/spribe/api/send" in url and flow.request.method == "POST":
            if flow.response.status_code == 200:
                try:
                    raw_text = flow.response.text
                    data = json.loads(raw_text)
                    size = len(raw_text)
                    
                    if 300 < size < 4000: # Pacotes de ação (Aposta/Clique)
                        self.log_console(f"[*] Aposta detectada ({size} bytes). Decodificando Buffer Binário...")
                        
                        # Extração de Payload Binário disfarçado
                        payload_bin = None
                        if "message" in data and isinstance(data["message"], dict):
                            payload_bin = data["message"]
                        elif isinstance(data, dict) and "0" in data:
                            payload_bin = data

                        bombas = self._quebrar_binario_spribe(payload_bin) if payload_bin else None
                        
                        # Fallback: Scanner Recursivo se o Decoder Binário falhar
                        if not bombas:
                            def scan_rec(obj):
                                nonlocal bombas
                                if isinstance(obj, dict):
                                    if any(k in obj for k in ["mines", "bombPositions", "board"]):
                                        bombas = obj.get("mines") or obj.get("bombPositions") or obj.get("board")
                                        return
                                    for v in obj.values(): scan_rec(v)
                                elif isinstance(obj, list):
                                    if all(isinstance(x, int) and 0 <= x < 25 for x in obj) and 2 <= len(obj) <= 24:
                                        bombas = obj; return
                                    for v in obj: scan_rec(v)
                            scan_rec(data)

                        if bombas and isinstance(bombas, list):
                            self.log_console(f"    [!!!] VULNERABILIDADE DETECTADA! Bombas: {bombas}")
                            # Ponte para o HUD
                            script_bridge = f"<script>window.vidente_grid_injetado = {bombas};</script>"
                            flow.response.text = raw_text + script_bridge
                            
                            # Injeta no JSON para fallback de JS Fetch
                            if isinstance(data, list): data.append({"vidente_grid": bombas})
                            else: data["vidente_grid"] = bombas
                            flow.response.text = json.dumps(data)
                        else:
                            self.log_console(f"    [-] Pacote analisado. Nenhum array claro. Preview: {raw_text[:120]}...")
                except Exception as e:
                    self.log_console(f"[ERR] Falha ao processar tráfego Spribe: {e}")

    def websocket_message(self, flow: http.HTTPFlow):
        msg = flow.websocket.messages[-1]
        if not msg.from_client:
            # Tenta decodificar o conteúdo da mensagem WS
            try:
                # Se for JSON mas com campo binário
                txt = msg.content.decode('utf-8', errors='ignore')
                if "{" in txt:
                    st = txt.find('{'); end = txt.rfind('}') + 1
                    jd = json.loads(txt[st:end])
                    if "message" in jd and isinstance(jd["message"], dict):
                        b = self._quebrar_binario_spribe(jd["message"])
                        if b:
                            self.log_console(f"[WS] Bombas Detectadas: {b}")
                            jd["vidente_grid"] = b
                            msg.content = (txt[:st] + json.dumps(jd) + txt[end:]).encode()
            except: pass

addons = [Vidente()]
