# ==============================================================================
# IA VIDENTE - v2.0 PREDIÇÃO ABSOLUTA (Cortex Edition)
# ==============================================================================
import os
import json
import re
import zlib
from datetime import datetime
from mitmproxy import http, ctx

# Configurações
LOG_FILE = "vidente_history.log"
VERSION = "2.0.2"

HUD_HTML = """
<div id="vidente-hud" style="position:fixed; top:10px; left:50%; transform:translateX(-50%); width:320px; background:rgba(0,0,0,0.9); border:2px solid #0ff; border-radius:15px; z-index:10000; color:white; font-family:sans-serif; padding:15px; box-shadow:0 0 20px #0ff; text-align:center;">
    <div style="font-weight:bold; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
        <span>🔮 IA VIDENTE v2.0</span>
        <span id="v-status" style="font-size:10px; color:#aaa;">SINCRONIZADO</span>
    </div>
    
    <div id="v-grid" style="display:grid; grid-template-columns: repeat(5, 1fr); gap:5px; margin:10px 0; background:#111; padding:10px; border-radius:8px;">
        <!-- Gerado via JS -->
    </div>
    
    <div style="font-size:11px; margin-top:10px; display:flex; gap:5px; justify-content:center;">
        <button onclick="rotateGrid()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px 10px; cursor:pointer; border-radius:5px;">ROTACIONAR</button>
        <button onclick="toggleMirror()" style="background:#222; border:1px solid #0ff; color:#0ff; padding:5px 10px; cursor:pointer; border-radius:5px;">ESPELHAR</button>
        <button onclick="clearGrid()" style="background:#222; border:1px solid #f00; color:#f00; padding:5px 10px; cursor:pointer; border-radius:5px;">LIMPAR</button>
    </div>
    <div id="v-mode" style="font-size:9px; color:#0ff; margin-top:5px;">MODO: AUTO-DETECT</div>
</div>

<script>
    let baseGrid = [];
    let currentSymmetry = 0; // 0..7
    let revealedCells = {}; // {index: type} 

    const renderGrid = (mines) => {
        if (mines) baseGrid = mines;
        const gridDiv = document.getElementById('v-grid');
        gridDiv.innerHTML = '';
        
        let transformed = applySymmetry(baseGrid, currentSymmetry);
        
        for (let i = 0; i < 25; i++) {
            const cell = document.createElement('div');
            cell.style.width = '100%';
            cell.style.paddingBottom = '100%';
            cell.style.background = transformed.includes(i) ? 'rgba(255,0,0,0.4)' : '#222';
            cell.style.border = '1px solid #333';
            cell.style.borderRadius = '3px';
            cell.style.position = 'relative';
            cell.style.boxShadow = transformed.includes(i) ? '0 0 10px rgba(255,0,0,0.3)' : 'none';
            
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
            let r = Math.floor(idx / 5);
            let c = idx % 5;
            if (sym === 1) c = 4 - c; // Mirror X
            if (sym === 2) r = 4 - r; // Mirror Y
            if (sym === 3) { let t = r; r = c; c = 4 - t; } // Rot 90
            if (sym === 4) { r = 4 - r; c = 4 - c; } // Rot 180
            if (sym === 5) { let t = r; r = 4 - c; c = t; } // Rot 270
            if (sym === 6) { let t = r; r = c; c = t; } // Transpose
            if (sym === 7) { let t = r; r = 4 - c; c = 4 - r; } // Anti-Transpose
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
            if (match) {
                currentSymmetry = s;
                document.getElementById('v-mode').innerText = "CALIBRADO: S" + s;
                renderGrid();
                return;
            }
        }
    };

    const handleData = (data) => {
        if (data.vidente_grid) {
            baseGrid = data.vidente_grid;
            renderGrid();
            autoCalibrate();
        }
        // Interceptar revelações
        if (data.dt && data.dt.cellNumber !== undefined) {
             revealedCells[data.dt.cellNumber] = data.dt.win > 0 ? 'gem' : 'mine';
             autoCalibrate();
             renderGrid();
        }
        // Buscar em estruturas genéricas
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
    window.clearGrid = () => { baseGrid = []; revealedCells = {}; renderGrid(); document.getElementById('v-mode').innerText = "MODO: AUTO-DETECT"; };
    window.toggleMirror = () => { currentSymmetry = (currentSymmetry === 1 ? 0 : 1); renderGrid(); };

    // Hooks
    const oldFetch = window.fetch;
    window.fetch = async (...args) => {
        const res = await oldFetch(...args);
        const clone = res.clone();
        try { const d = await clone.json(); handleData(d); } catch(e) {}
        return res;
    };
    
    setInterval(() => {
        try {
            const s = window.state || window.game || (window.app && window.app.state);
            if (s && s.mines && s.mines.length > 0) handleData({vidente_grid: s.mines});
        } catch(e) {}
    }, 1000);
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

        # 1. Injeção de HUD
        if "mines" in flow.request.pretty_url and "text/html" in flow.response.headers.get("Content-Type", ""):
            flow.response.content = flow.response.content.replace(b"</body>", HUD_HTML.encode() + b"</body>")
            self.log(f"HUD v2.0 Injetado: {flow.request.pretty_url}")

        # 2. Proxy de Inteligência (Spribe)
        if "spribe" in flow.request.pretty_url and flow.response.status_code == 200:
            try:
                data = json.loads(flow.response.text)
                msg = data.get("message")
                if not msg: return
                
                # Converter para bytes
                if isinstance(msg, list): 
                    raw = bytearray()
                    for m in msg: raw.extend([m.get(k, 0) for k in sorted(m.keys(), key=int)])
                else: 
                    raw = bytes([msg.get(k, 0) for k in sorted(msg.keys(), key=int)])
                
                decoded = raw
                try: decoded = zlib.decompress(raw, -zlib.MAX_WBITS)
                except: 
                    try: decoded = zlib.decompress(raw)
                    except: pass
                
                # Busca por Bombas
                bombs = []
                # Padrão A: cellNumber (Semântico)
                for m in re.finditer(b"cellNumber", decoded):
                    v_offset = m.end() + 4
                    if v_offset < len(decoded):
                        val = decoded[v_offset]
                        if 0 <= val < 25: bombs.append(int(val))
                
                # Padrão B: Tag 0x08/0x10 (Heurístico)
                if not bombs and len(raw) > 150:
                    potential = []
                    for i in range(1, len(decoded) - 1):
                        val = decoded[i]
                        if 0 <= val < 25 and decoded[i-1] in [0x08, 0x10, 0x18, 0x20]:
                            potential.append(int(val))
                    if 3 <= len(set(potential)) <= 10: bombs = list(set(potential))

                if bombs:
                    data["vidente_grid"] = bombs
                    flow.response.text = json.dumps(data)
                    self.log(f"BOMBAS_DETEC: {bombs} (Size: {len(raw)})")
            except: pass

addons = [Vidente()]
