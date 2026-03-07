# ==============================================================================
# IA VIDENTE - v2.1 VIP & ADMIN (Cortex Edition)
# ==============================================================================
import os
import json
import re
import zlib
from datetime import datetime
from mitmproxy import http, ctx

# Configurações
LOG_FILE = "vidente_history.log"
VERSION = "2.1.0"

HUD_HTML = """
<div id="vidente-hud" style="position:fixed; top:10px; left:50%; transform:translateX(-50%); width:340px; background:rgba(0,0,0,0.95); border:2px solid #0ff; border-radius:15px; z-index:10000; color:white; font-family:sans-serif; padding:15px; box-shadow:0 0 25px rgba(0,255,255,0.5); text-align:center; backdrop-filter:blur(10px);">
    <div style="font-weight:bold; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
        <span style="color:#0ff; text-shadow:0 0 5px #0ff;">🔮 VIDENTE v2.1 VIP</span>
        <span id="v-status" style="font-size:10px; color:#0f0;">ONLINE</span>
    </div>
    
    <div id="v-grid" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:5px; margin:10px 0; background:#111; padding:10px; border-radius:8px; border:1px solid #333;">
        <!-- Board gerado via JS -->
    </div>

    <div id="v-seeds" style="font-size:9px; color:#aaa; margin-bottom:10px; text-align:left; background:rgba(255,255,255,0.05); padding:5px; border-radius:5px; display:none;">
        <b>SEEDS DETECTADOS:</b><br>
        <span id="v-server-seed">S: ---</span><br>
        <span id="v-client-seed">C: ---</span>
    </div>
    
    <div style="font-size:11px; margin-top:10px; display:flex; gap:5px; justify-content:center; flex-wrap:wrap;">
        <button onclick="rotateGrid()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px 8px; cursor:pointer; border-radius:5px; font-size:10px;">GIRAR</button>
        <button onclick="toggleMirror()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px 8px; cursor:pointer; border-radius:5px; font-size:10px;">ESPELHAR</button>
        <button onclick="clearGrid()" style="background:#222; border:1px solid #f00; color:#f00; padding:5px 8px; cursor:pointer; border-radius:5px; font-size:10px;">LIMPAR</button>
        <button id="btn-admin" onclick="triggerAdmin()" style="background:linear-gradient(45deg, #f0f, #00f); border:none; color:white; padding:5px 8px; cursor:pointer; border-radius:5px; font-size:10px; font-weight:bold; display:none;">ADMIN PANEL</button>
    </div>
    <div id="v-mode" style="font-size:9px; color:#0ff; margin-top:8px;">AGUARDANDO APOSTA...</div>
</div>

<script>
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
            cell.style.background = transformed.includes(i) ? 'rgba(255,0,0,0.4)' : '#222';
            cell.style.border = '1px solid #333'; cell.style.borderRadius = '3px';
            cell.style.position = 'relative';
            if (revealedCells[i]) {
                cell.style.background = revealedCells[i] === 'mine' ? '#611' : '#161';
                cell.innerHTML = `<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);">${revealedCells[i] === 'mine' ? '💥' : '💎'}</span>`;
            } else if (transformed.includes(i)) {
                cell.innerHTML = '<span style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); opacity:0.8;">💣</span>';
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

    const autoCalibrate = () => {
        if (Object.keys(revealedCells).length === 0 || baseGrid.length === 0) return;
        for (let s = 0; s < 8; s++) {
            let transformed = applySymmetry(baseGrid, s);
            let match = true;
            for (let [idx, type] of Object.entries(revealedCells)) {
                let cellIdx = parseInt(idx);
                let isBombInState = transformed.includes(cellIdx);
                if (type === 'mine' && !isBombInState) match = false;
                if (type === 'gem' && isBombInState) match = false;
                if (!match) break;
            }
            if (match) { currentSymmetry = s; document.getElementById('v-mode').innerText = "V2.1 SYNC: S" + s; renderGrid(); return; }
        }
    };

    const handleData = (data) => {
        if (data.vidente_grid) { baseGrid = data.vidente_grid; renderGrid(); autoCalibrate(); }
        if (data.vidente_seeds) {
             document.getElementById('v-seeds').style.display = 'block';
             document.getElementById('v-server-seed').innerText = "S: " + data.vidente_seeds.server.substring(0,20) + "...";
             document.getElementById('v-client-seed').innerText = "C: " + (data.vidente_seeds.client || "DEMO");
        }
        if (data.vidente_admin) { document.getElementById('btn-admin').style.display = 'block'; }
        if (data.dt && data.dt.cellNumber !== undefined) {
             revealedCells[data.dt.cellNumber] = data.dt.win > 0 ? 'gem' : 'mine';
             autoCalibrate(); renderGrid();
        }
        const scan = (obj) => {
            if (!obj) return;
            if (Array.isArray(obj) && obj.length === 25) {
                const b = obj.map((v, i) => (v === 1 || v === true) ? i : -1).filter(x => x !== -1);
                if (b.length > 0 && b.length < 25) { baseGrid = b; renderGrid(); autoCalibrate(); }
            }
            if (typeof obj === 'object') Object.values(obj).forEach(scan);
        };
        scan(data);
    };

    window.rotateGrid = () => { currentSymmetry = (currentSymmetry + 1) % 8; renderGrid(); };
    window.clearGrid = () => { baseGrid = []; revealedCells = {}; renderGrid(); document.getElementById('v-mode').innerText = "AGUARDANDO..."; };
    window.toggleMirror = () => { currentSymmetry = (currentSymmetry === 1 ? 0 : 1); renderGrid(); };
    window.triggerAdmin = () => { window.location.href = '/admin'; };

    const oldFetch = window.fetch;
    window.fetch = async (...args) => {
        const res = await oldFetch(...args);
        const clone = res.clone();
        try { const d = await clone.json(); handleData(d); } catch(e) {}
        return res;
    };
</script>
"""

class Vidente:
    def __init__(self):
        self.log_file = LOG_FILE

    def log(self, text):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {text}\n")

    def response(self, flow: http.HTTPFlow):
        # CSP Bypass
        for h in ["Content-Security-Policy", "X-Content-Security-Policy", "Content-Security-Policy-Report-Only"]:
            if h in flow.response.headers: del flow.response.headers[h]

        url = flow.request.pretty_url

        # 1. Injeção de HUD
        if "mines" in url and "text/html" in flow.response.headers.get("Content-Type", ""):
            flow.response.content = flow.response.content.replace(b"</body>", HUD_HTML.encode() + b"</body>")
            self.log(f"HUD v2.1 Injetado: {url}")

        # 2. Hook de Privilégios (Admin Escalation)
        if "trpc/user.details" in url and flow.response.status_code == 200:
            try:
                data = json.loads(flow.response.text)
                # Injetar super-user nas respostas do site principal
                if "result" in data:
                    user_node = data["result"]["data"]["json"]
                    user_node["role"] = "admin"
                    user_node["isAdmin"] = True
                    user_node["isVip"] = True
                    user_node["permissions"] = ["*", "admin", "superadmin"]
                    data["vidente_admin"] = True
                    flow.response.text = json.dumps(data)
                    self.log(f"ESCALAÇÃO DE PRIVILÉGIOS ATIVA para {user_node.get('id')}")
            except Exception as e:
                self.log(f"Erro Admin Hook: {e}")

        # 3. Detector de Sementes e Minas (Spribe)
        if "spribe" in url and flow.response.status_code == 200:
            try:
                data = json.loads(flow.response.text)
                msg_field = data.get("message")
                if not msg_field: return
                
                # Deserializar Protobuf Simplificado
                if isinstance(msg_field, list): 
                    raw = bytearray()
                    for m in msg_field: raw.extend([m.get(k, 0) for k in sorted(m.keys(), key=int)])
                else: 
                    raw = bytes([msg_field.get(k, 0) for k in sorted(msg_field.keys(), key=int)])
                
                decoded = raw
                try: decoded = zlib.decompress(raw, -zlib.MAX_WBITS)
                except: 
                    try: decoded = zlib.decompress(raw)
                    except: pass
                
                # Extrair Seeds (Sementes)
                seeds = {}
                seed_match = re.search(b'serverSeed', decoded)
                if seed_match:
                    s_start = seed_match.end() + 2
                    seeds["server"] = decoded[s_start:s_start+64].decode(errors='ignore')
                    self.log(f"SEED DETECTADO: {seeds['server']}")
                
                # Busca por Bombas (Heurística v2.1)
                bombs = []
                for m in re.finditer(b"cellNumber", decoded):
                    v_off = m.end() + 4
                    if v_off < len(decoded): bombs.append(int(decoded[v_off]))
                
                if not bombs and len(raw) > 150:
                    potential = []
                    for i in range(1, len(decoded) - 1):
                        if 0 <= decoded[i] < 25 and decoded[i-1] in [0x08, 0x10, 0x18, 0x20]:
                            potential.append(int(decoded[i]))
                    if 3 <= len(set(potential)) <= 10: bombs = list(set(potential))

                if bombs or seeds:
                    data["vidente_grid"] = bombs
                    data["vidente_seeds"] = seeds if seeds else None
                    flow.response.text = json.dumps(data)
                    self.log(f"PREDIÇÃO_V21: {bombs} | Seeds? {'SIM' if seeds else 'NÃO'}")
            except: pass

addons = [Vidente()]
