import os
import json
import requests
import pymysql
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

RDS_HOST = os.environ.get("RDS_HOST", "localhost")
RDS_USER = os.environ.get("RDS_USER", "admin")
RDS_PASS = os.environ.get("RDS_PASS", "")
RDS_DB = os.environ.get("RDS_DB", "cofrial_db")


def get_db():
    return pymysql.connect(
        host=RDS_HOST, user=RDS_USER, password=RDS_PASS, database=RDS_DB,
        port=3306, cursorclass=pymysql.cursors.DictCursor, autocommit=True
    )


def classify_with_public_ai(cliente_nombre, canal, texto_req):
    """Consume API publica de IA Generativa (Pollinations LLM Free-Tier, Costo Cero) con respaldo deterministico."""
    prompt = (
        f"Eres el motor de IA del CRM de Cofrial SpA (logistica de cadena de frio en Temuco). "
        f"Clasifica este requerimiento del cliente '{cliente_nombre}' ({canal}): '{texto_req}'. "
        f"Responde SOLO en formato JSON exacto con dos claves: "
        f"\"categoria\" (elige una: URGENCIA CLINICA HOSPITALARIA, ABASTECIMIENTO MAYORISTA B2B, ALERTA CADENA DE FRIO, COMPRA MINORISTA B2C) "
        f"y \"resumen\" (sintesis ejecutiva de 18 palabras indicando accion recomendada)."
    )
    try:
        resp = requests.post(
            "https://text.pollinations.ai/",
            json={
                "messages": [
                    {"role": "system", "content": "Responde unicamente con un objeto JSON valido sin markdown."},
                    {"role": "user", "content": prompt}
                ],
                "model": "openai",
                "jsonMode": True
            },
            timeout=6
        )
        if resp.status_code == 200:
            raw = resp.text.strip().strip("`")
            if raw.startswith("json"):
                raw = raw[4:].strip()
            data = json.loads(raw)
            cat = data.get("categoria", "PRIORIDAD COMERCIAL IA").upper()
            res = data.get("resumen", f"[IA LLM Publica] Solicitud procesada: {texto_req[:90]}")
            return cat, f"[API LLM Free-Tier] {res}"
    except Exception:
        pass
    t_low = texto_req.lower()
    if "hospital" in t_low or "clinica" in t_low or "urgente" in t_low or "suero" in t_low:
        cat = "URGENCIA CLINICA HOSPITALARIA"
    elif "frio" in t_low or "temperatura" in t_low or "merma" in t_low:
        cat = "ALERTA CADENA DE FRIO"
    elif "B2B" in canal:
        cat = "ABASTECIMIENTO MAYORISTA B2B"
    else:
        cat = "COMPRA MINORISTA B2C"
    return cat, f"[IA Clasificador Automatico] Prioridad asignada ({cat}): {texto_req[:100]}"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Cofrial SpA — Ecosistema Cloud AWS (E-commerce B2B/B2C + CRM + IoT + BI)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    :root {
      --bg: #0f172a; --card: #1e293b; --border: #334155; --text: #f8fafc;
      --muted: #94a3b8; --primary: #0ea5e9; --success: #10b981; --danger: #ef4444;
    }
    * { box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
    body { margin: 0; background: var(--bg); color: var(--text); }
    header {
      background: #020617; border-bottom: 1px solid var(--border); padding: 14px 24px;
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .logo {
      background: linear-gradient(135deg, #0ea5e9, #2563eb); color: white;
      font-weight: 800; padding: 8px 12px; border-radius: 8px;
    }
    .status-pill {
      background: rgba(16,185,129,0.15); border: 1px solid var(--success); color: #34d399;
      padding: 5px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
    }
    nav { display: flex; gap: 8px; flex-wrap: wrap; }
    .tab-btn {
      background: var(--card); color: var(--text); border: 1px solid var(--border);
      padding: 9px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 13px;
    }
    .tab-btn.active { background: var(--primary); border-color: var(--primary); color: #fff; }
    main { max-width: 1400px; margin: 0 auto; padding: 20px; }
    .section { display: none; }
    .section.active { display: block; }
    .grid-3 { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
    .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-bottom: 20px; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
    .kpi-title { font-size: 12px; color: var(--muted); text-transform: uppercase; }
    .kpi-val { font-size: 26px; font-weight: 800; margin-top: 6px; }
    .profile-bar {
      display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;
      gap: 12px; margin-bottom: 16px; background: #172554; border: 1px solid #1d4ed8; padding: 12px 16px; border-radius: 10px;
    }
    select, input, textarea {
      background: #0f172a; color: white; border: 1px solid var(--border);
      padding: 8px 12px; border-radius: 6px; font-size: 13px; width: 100%;
    }
    .prod-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 14px; }
    .prod-card {
      background: #0f172a; border: 1px solid var(--border); border-radius: 10px; padding: 14px;
      display: flex; flex-direction: column; justify-content: space-between;
    }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
    .badge-cold { background: rgba(14,165,233,0.2); color: #38bdf8; border: 1px solid #0284c7; }
    .badge-ok { background: rgba(16,185,129,0.2); color: #34d399; }
    .badge-alert { background: rgba(239,68,68,0.25); color: #f87171; border: 1px solid #ef4444; }
    .btn { background: var(--primary); color: white; border: none; padding: 9px 14px; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 13px; }
    .btn-success { background: var(--success); width: 100%; margin-top: 10px; padding: 11px; font-size: 14px; }
    .btn-danger { background: var(--danger); }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 9px 10px; border-bottom: 1px solid var(--border); text-align: left; }
    th { color: var(--muted); font-size: 11px; text-transform: uppercase; background: #0f172a; }
    #map { height: 290px; border-radius: 10px; border: 1px solid var(--border); }
    @media (max-width: 900px) { .grid-3 { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="logo">❄️ COFRIAL SpA</div>
      <div>
        <div style="font-weight:700; font-size:15px;">Ecosistema Cloud Transaccional & Cadena de Frío Inteligente</div>
        <div style="font-size:12px; color:var(--muted);">AWS EC2 + Amazon RDS (MySQL 3NF) + Docker IoT (50 Camiones) + BI & API IA</div>
      </div>
    </div>
    <div class="status-pill">● Conectado en Vivo a Amazon RDS</div>
    <nav>
      <button class="tab-btn active" onclick="showTab('ecommerce', this)">1. Portal E-Commerce (B2B / B2C)</button>
      <button class="tab-btn" onclick="showTab('crm', this)">2. Consola CRM + Asistente IA</button>
      <button class="tab-btn" onclick="showTab('bi', this)">3. Dashboard BI + Telemetría Docker IoT</button>
    </nav>
  </header>
  <main>
    <section id="ecommerce" class="section active">
      <div class="profile-bar">
        <div style="flex:1; min-width:260px;">
          <label style="font-size:12px; color:#93c5fd; font-weight:700;">SELECCIÓN DE PERFIL Y CLIENTE ACTIVO (DIFERENCIACIÓN B2B / B2C):</label>
          <select id="clienteSelect" onchange="changeProfile()" style="margin-top:4px;"></select>
        </div>
        <div id="profileBadge" style="font-size:13px; font-weight:700; color:#38bdf8;"></div>
      </div>
      <div class="grid-3">
        <div class="card">
          <h3 style="margin-top:0;">Catálogo de Productos Refrigerados y Congelados</h3>
          <div id="catalogGrid" class="prod-grid"></div>
        </div>
        <div class="card">
          <h3 style="margin-top:0;">🛒 Carrito de Compras Transaccional</h3>
          <div id="cartItems" style="min-height:120px; font-size:13px; color:var(--muted);">El carrito está vacío.</div>
          <div style="border-top:1px solid var(--border); margin-top:12px; padding-top:12px;">
            <div style="display:flex; justify-content:space-between; font-size:13px;"><span>Monto Neto:</span><strong id="cartNeto">$0 CLP</strong></div>
            <div style="display:flex; justify-content:space-between; font-size:13px; margin-top:4px;"><span>IVA (19%):</span><strong id="cartIva">$0 CLP</strong></div>
            <div style="display:flex; justify-content:space-between; font-size:17px; margin-top:8px; color:#38bdf8;"><span>Total Orden:</span><strong id="cartTotal">$0 CLP</strong></div>
            <button class="btn btn-success" onclick="checkoutOrder()">Confirmar Orden y Asignar Camión IoT en RDS</button>
            <div id="orderMsg" style="margin-top:10px; font-size:13px; font-weight:600;"></div>
          </div>
        </div>
      </div>
    </section>
    <section id="crm" class="section">
      <div class="grid-3">
        <div class="card">
          <h3 style="margin-top:0;">📊 Pipeline Comercial CRM & Seguimiento de Órdenes Web</h3>
          <div style="overflow-x:auto;">
            <table><thead><tr><th>ID</th><th>Cliente</th><th>Etapa</th><th>Clasificación IA</th><th>Resumen IA</th><th>Monto</th></tr></thead><tbody id="crmTableBody"></tbody></table>
          </div>
          <h3 style="margin-top:24px;">🚚 Órdenes Emitidas y Camión Asignado</h3>
          <div style="overflow-x:auto;">
            <table><thead><tr><th>Pedido #</th><th>Cliente</th><th>Canal</th><th>Estado</th><th>Camión IoT</th><th>Total CLP</th></tr></thead><tbody id="ordersTableBody"></tbody></table>
          </div>
        </div>
        <div class="card">
          <h3 style="margin-top:0;">🤖 Clasificador de Requerimientos (API Pública IA)</h3>
          <select id="crmClienteSelect" style="margin-bottom:10px;"></select>
          <select id="crmEtapaSelect" style="margin-bottom:10px;">
            <option value="1. Lead Capturado">1. Lead Capturado</option>
            <option value="2. Calificado">2. Calificado</option>
            <option value="3. Cotizado">3. Cotizado</option>
            <option value="4. Negociación">4. Negociación</option>
            <option value="5. Cerrado Ganado">5. Cerrado Ganado</option>
            <option value="6. Monitoreo Postventa Frío">6. Monitoreo Postventa Frío</option>
          </select>
          <input type="number" id="crmMonto" value="1450000" style="margin-bottom:10px;"/>
          <textarea id="crmTexto" rows="4" placeholder="Escribe la solicitud del cliente..."></textarea>
          <button class="btn btn-success" onclick="submitCrmAi()">Clasificar con API IA y Guardar en RDS</button>
          <div id="crmAiResult" style="margin-top:12px; font-size:13px;"></div>
        </div>
      </div>
    </section>
    <section id="bi" class="section">
      <div class="kpi-row">
        <div class="card"><div class="kpi-title">Volumen Total Ventas (RDS)</div><div class="kpi-val" id="kpiVentas" style="color:#38bdf8;">$0</div></div>
        <div class="card"><div class="kpi-title">Pedidos B2B vs B2C</div><div class="kpi-val" id="kpiCanales">0 / 0</div></div>
        <div class="card"><div class="kpi-title">Cumplimiento Cadena de Frío</div><div class="kpi-val" id="kpiCumplimiento" style="color:#34d399;">100%</div></div>
        <div class="card"><div class="kpi-title">Alertas Ruptura de Frío (IoT)</div><div class="kpi-val" id="kpiAlertas" style="color:#ef4444;">0</div></div>
      </div>
      <div class="grid-3">
        <div class="card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h3 style="margin:0;">📡 Telemetría en Tiempo Real — Docker en EC2</h3>
            <button class="btn btn-danger" onclick="forceRupture()">🔥 Simular Ruptura de Frío Crítica Ahora</button>
          </div>
          <div style="overflow-x:auto; max-height:340px;">
            <table><thead><tr><th>Hora</th><th>camion_id</th><th>temp_camara</th><th>lat / long</th><th>combustible_pct</th><th>alerta_ruptura_frio</th></tr></thead><tbody id="iotTableBody"></tbody></table>
          </div>
        </div>
        <div class="card">
          <h3 style="margin-top:0;">🗺️ Geolocalización GPS en Ruta</h3>
          <div id="map"></div>
          <h3 style="margin-top:16px;">📈 Cruce Comercial vs Alertas Térmicas</h3>
          <canvas id="biChart" height="150"></canvas>
        </div>
      </div>
    </section>
  </main>
  <script>
    let state = { clientes: [], productos: [], cart: [], selectedCliente: null };
    let map = null, markers = [], biChart = null;
    function formatCLP(n) { return '$' + Math.round(Number(n || 0)).toLocaleString('es-CL') + ' CLP'; }
    function showTab(tabId, btn) {
      document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById(tabId).classList.add('active'); btn.classList.add('active');
      if (tabId === 'bi') {
        setTimeout(() => {
          if (!map) { map = L.map('map').setView([-38.7359, -72.5904], 9); L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map); }
          else { map.invalidateSize(); }
          refreshAll();
        }, 150);
      }
    }
    async function refreshAll() {
      const res = await fetch('/api/dashboard'); const data = await res.json();
      state.clientes = data.clientes; state.productos = data.productos;
      const cSel = document.getElementById('clienteSelect'), crmCSel = document.getElementById('crmClienteSelect');
      if (cSel.options.length === 0 && state.clientes.length > 0) {
        state.clientes.forEach(c => {
          const opt = `<option value="${c.id_cliente}">[${c.tipo_perfil}] ${c.razon_social_nombre} (${c.rut_cliente})</option>`;
          cSel.insertAdjacentHTML('beforeend', opt); crmCSel.insertAdjacentHTML('beforeend', opt);
        });
        state.selectedCliente = state.clientes[0];
      }
      renderCatalog(); renderCrmAndOrders(data.oportunidades, data.pedidos); renderBiAndIot(data.kpis, data.telemetria);
    }
    function changeProfile() { state.selectedCliente = state.clientes.find(c => c.id_cliente === Number(document.getElementById('clienteSelect').value)); state.cart = []; renderCart(); renderCatalog(); }
    function renderCatalog() {
      if (!state.selectedCliente) return;
      const isB2B = state.selectedCliente.tipo_perfil === 'B2B';
      document.getElementById('profileBadge').innerHTML = isB2B ? '🏢 Perfil: B2B Institucional' : '🛍️ Perfil: B2C Público General';
      document.getElementById('catalogGrid').innerHTML = state.productos.map(p => {
        const precio = isB2B ? p.precio_b2b : p.precio_b2c;
        return `<div class="prod-card"><div><span class="badge badge-cold">❄️ ${p.temp_min_req}°C a ${p.temp_max_req}°C</span><div style="font-weight:700; margin-top:8px;">${p.nombre_producto}</div><div style="font-size:12px; color:var(--muted);">Stock RDS: ${p.stock_actual}</div></div><div style="margin-top:12px;"><div style="font-size:17px; font-weight:800; color:#38bdf8; margin-bottom:8px;">${formatCLP(precio)}</div><button class="btn" style="width:100%;" onclick="addToCart(${p.id_producto})">+ Agregar al Carrito</button></div></div>`;
      }).join('');
    }
    function addToCart(idProd) {
      const p = state.productos.find(x => x.id_producto === idProd); if (!p || !state.selectedCliente) return;
      const precio = Number(state.selectedCliente.tipo_perfil === 'B2B' ? p.precio_b2b : p.precio_b2c);
      const item = state.cart.find(x => x.id_producto === idProd);
      if (item) item.cantidad += 1; else state.cart.push({ id_producto: p.id_producto, nombre: p.nombre_producto, precio, cantidad: 1 });
      renderCart();
    }
    function renderCart() {
      const box = document.getElementById('cartItems');
      if (state.cart.length === 0) { box.innerHTML = 'El carrito está vacío.'; document.getElementById('cartNeto').textContent = '$0 CLP'; document.getElementById('cartIva').textContent = '$0 CLP'; document.getElementById('cartTotal').textContent = '$0 CLP'; return; }
      let neto = 0;
      box.innerHTML = state.cart.map(it => { neto += it.precio * it.cantidad; return `<div style="display:flex; justify-content:space-between; margin-bottom:8px; color:white;"><span>${it.cantidad}x ${it.nombre}</span><strong>${formatCLP(it.precio * it.cantidad)}</strong></div>`; }).join('');
      const iva = Math.round(neto * 0.19);
      document.getElementById('cartNeto').textContent = formatCLP(neto); document.getElementById('cartIva').textContent = formatCLP(iva); document.getElementById('cartTotal').textContent = formatCLP(neto + iva);
    }
    async function checkoutOrder() {
      if (state.cart.length === 0) return;
      const res = await fetch('/api/order', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ id_cliente: state.selectedCliente.id_cliente, items: state.cart }) });
      const out = await res.json();
      if (out.ok) { document.getElementById('orderMsg').innerHTML = `<span style="color:#34d399;">✔ Orden #${out.id_pedido} guardada en RDS (${out.camion_asignado}).</span>`; state.cart = []; renderCart(); refreshAll(); }
    }
    function renderCrmAndOrders(ops, pedidos) {
      document.getElementById('crmTableBody').innerHTML = ops.map(o => `<tr><td>#${o.id_oportunidad}</td><td><strong>${o.razon_social_nombre}</strong></td><td><span class="badge badge-cold">${o.etapa_pipeline}</span></td><td><span class="badge badge-alert">${o.clasificacion_ia_requerimiento || ''}</span></td><td style="font-size:12px;">${o.resumen_ia_solicitud || ''}</td><td><strong>${formatCLP(o.monto_estimado_clp)}</strong></td></tr>`).join('');
      document.getElementById('ordersTableBody').innerHTML = pedidos.map(p => `<tr><td>#${p.id_pedido}</td><td>${p.razon_social_nombre}</td><td>${p.canal_venta}</td><td>${p.estado_pedido}</td><td><strong>${p.camion_asignado}</strong></td><td><strong>${formatCLP(p.monto_total)}</strong></td></tr>`).join('');
    }
    async function submitCrmAi() {
      const res = await fetch('/api/crm_ai', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ id_cliente: Number(document.getElementById('crmClienteSelect').value), etapa: document.getElementById('crmEtapaSelect').value, monto: Number(document.getElementById('crmMonto').value || 500000), texto: document.getElementById('crmTexto').value.trim() || 'Solicitud urgente hospitalaria' }) });
      const out = await res.json();
      if (out.ok) { document.getElementById('crmAiResult').innerHTML = `<span style="color:#34d399;">✔ Clasificado: ${out.categoria}</span>`; document.getElementById('crmTexto').value = ''; refreshAll(); }
    }
    function renderBiAndIot(kpis, telemetria) {
      document.getElementById('kpiVentas').textContent = formatCLP(kpis.ventas_totales); document.getElementById('kpiCanales').textContent = `${kpis.pedidos_b2b} B2B / ${kpis.pedidos_b2c} B2C`; document.getElementById('kpiCumplimiento').textContent = `${kpis.cumplimiento_frio_pct}%`; document.getElementById('kpiAlertas').textContent = kpis.alertas_criticas;
      document.getElementById('iotTableBody').innerHTML = telemetria.map(t => { const a = Number(t.alerta_ruptura_frio) === 1; return `<tr><td>${t.timestamp_lectura}</td><td><strong>${t.camion_id}</strong></td><td>${Number(t.temp_camara).toFixed(2)} °C</td><td>${Number(t.lat).toFixed(4)}, ${Number(t.long).toFixed(4)}</td><td>${t.combustible_pct}%</td><td><span class="badge ${a ? 'badge-alert' : 'badge-ok'}">${a ? 'TRUE' : 'FALSE'}</span></td></tr>`; }).join('');
      if (map) {
        markers.forEach(m => map.removeLayer(m)); markers = [];
        telemetria.slice(0, 10).forEach(t => { const a = Number(t.alerta_ruptura_frio) === 1; markers.push(L.circleMarker([t.lat, t.long], { radius: 8, color: a ? '#ef4444' : '#10b981', fillOpacity: 0.85 }).addTo(map).bindPopup(`${t.camion_id}: ${t.temp_camara} °C`)); });
      }
      const ctx = document.getElementById('biChart');
      if (ctx) {
        const vals = [kpis.ventas_b2b / 1000, kpis.ventas_b2c / 1000, kpis.alertas_criticas * 100];
        if (!biChart) biChart = new Chart(ctx, { type: 'bar', data: { labels: ['B2B (Miles CLP)', 'B2C (Miles CLP)', 'Riesgo Frío'], datasets: [{ label: 'BI en Vivo', data: vals, backgroundColor: ['#0ea5e9', '#10b981', '#ef4444'] }] } });
        else { biChart.data.datasets[0].data = vals; biChart.update(); }
      }
    }
    async function forceRupture() { await fetch('/api/force_rupture', { method: 'POST' }); refreshAll(); }
    refreshAll(); setInterval(refreshAll, 4000);
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/dashboard")
def api_dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM CLIENTE ORDER BY id_cliente;")
    clientes = cur.fetchall()
    cur.execute("""
        SELECT p.*, c.temp_min_req, c.temp_max_req
        FROM PRODUCTO p JOIN CATEGORIA_PRODUCTO c ON p.id_categoria = c.id_categoria
        ORDER BY p.id_producto;
    """)
    productos = cur.fetchall()
    for pr in productos:
        pr["stock_actual"] = float(pr["stock_actual"])
        pr["precio_b2b"] = float(pr["precio_b2b"])
        pr["precio_b2c"] = float(pr["precio_b2c"])

    cur.execute("""
        SELECT o.*, c.razon_social_nombre
        FROM OPORTUNIDAD_CRM o JOIN CLIENTE c ON o.id_cliente = c.id_cliente
        ORDER BY o.id_oportunidad DESC LIMIT 15;
    """)
    oportunidades = cur.fetchall()
    for op in oportunidades:
        op["monto_estimado_clp"] = float(op["monto_estimado_clp"])
        op["fecha_creacion"] = str(op["fecha_creacion"])

    cur.execute("""
        SELECT p.*, c.razon_social_nombre
        FROM PEDIDO p JOIN CLIENTE c ON p.id_cliente = c.id_cliente
        ORDER BY p.id_pedido DESC LIMIT 15;
    """)
    pedidos = cur.fetchall()
    for pe in pedidos:
        pe["monto_total"] = float(pe["monto_total"])
        pe["fecha_emision"] = str(pe["fecha_emision"])

    cur.execute("""
        SELECT id_telemetria, camion_id, DATE_FORMAT(timestamp_lectura, '%%H:%%i:%%s') as timestamp_lectura,
               temp_camara, lat, `long`, combustible_pct, alerta_ruptura_frio
        FROM TELEMETRIA_IOT
        ORDER BY id_telemetria DESC LIMIT 25;
    """)
    telemetria = cur.fetchall()

    cur.execute("SELECT COALESCE(SUM(monto_total),0) AS total FROM PEDIDO;")
    ventas_totales = float(cur.fetchone()["total"])
    cur.execute("SELECT COALESCE(SUM(monto_total),0) AS total, COUNT(*) AS cnt FROM PEDIDO WHERE canal_venta LIKE '%%B2B%%';")
    r_b2b = cur.fetchone()
    cur.execute("SELECT COALESCE(SUM(monto_total),0) AS total, COUNT(*) AS cnt FROM PEDIDO WHERE canal_venta LIKE '%%B2C%%';")
    r_b2c = cur.fetchone()

    total_iot = len(telemetria) if telemetria else 1
    alertas_cnt = sum(1 for t in telemetria if t["alerta_ruptura_frio"])
    cumplimiento = round(((total_iot - alertas_cnt) / total_iot) * 100, 1)

    conn.close()
    return jsonify({
        "clientes": clientes,
        "productos": productos,
        "oportunidades": oportunidades,
        "pedidos": pedidos,
        "telemetria": telemetria,
        "kpis": {
            "ventas_totales": ventas_totales,
            "ventas_b2b": float(r_b2b["total"]),
            "ventas_b2c": float(r_b2c["total"]),
            "pedidos_b2b": int(r_b2b["cnt"]),
            "pedidos_b2c": int(r_b2c["cnt"]),
            "alertas_criticas": alertas_cnt,
            "cumplimiento_frio_pct": cumplimiento
        }
    })


@app.route("/api/order", methods=["POST"])
def api_order():
    body = request.get_json(force=True)
    id_cliente = int(body["id_cliente"])
    items = body["items"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM CLIENTE WHERE id_cliente=%s;", (id_cliente,))
    cli = cur.fetchone()
    canal = f"E-commerce {cli['tipo_perfil']}"
    neto = sum(float(i["precio"]) * float(i["cantidad"]) for i in items)
    total = round(neto * 1.19)
    camion = f"CAM-COF-00{(id_cliente % 5) + 1}"

    cur.execute("""
        INSERT INTO PEDIDO (id_cliente, canal_venta, estado_pedido, monto_total, camion_asignado)
        VALUES (%s, %s, 'En Ruta IoT', %s, %s);
    """, (id_cliente, canal, total, camion))
    id_pedido = cur.lastrowid

    for it in items:
        cur.execute("""
            INSERT INTO DETALLE_PEDIDO (id_pedido, id_producto, cantidad, precio_unitario_aplicado)
            VALUES (%s, %s, %s, %s);
        """, (id_pedido, it["id_producto"], it["cantidad"], it["precio"]))
        cur.execute("UPDATE PRODUCTO SET stock_actual = GREATEST(0, stock_actual - %s) WHERE id_producto=%s;", (it["cantidad"], it["id_producto"]))

    cat, res_ia = classify_with_public_ai(cli["razon_social_nombre"], canal, f"Nueva orden web #{id_pedido} por {total} CLP asignada a {camion}")
    cur.execute("""
        INSERT INTO OPORTUNIDAD_CRM (id_cliente, etapa_pipeline, ejecutivo_asignado, canal_origen, monto_estimado_clp, clasificacion_ia_requerimiento, resumen_ia_solicitud)
        VALUES (%s, '5. Cerrado Ganado', 'Automatizacion E-commerce', %s, %s, %s, %s);
    """, (id_cliente, canal, total, cat, res_ia))

    conn.close()
    return jsonify({"ok": True, "id_pedido": id_pedido, "camion_asignado": camion})


@app.route("/api/crm_ai", methods=["POST"])
def api_crm_ai():
    body = request.get_json(force=True)
    id_cliente = int(body["id_cliente"])
    etapa = body["etapa"]
    monto = float(body["monto"])
    texto = body["texto"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM CLIENTE WHERE id_cliente=%s;", (id_cliente,))
    cli = cur.fetchone()
    cat, res_ia = classify_with_public_ai(cli["razon_social_nombre"], cli["tipo_perfil"], texto)

    cur.execute("""
        INSERT INTO OPORTUNIDAD_CRM (id_cliente, etapa_pipeline, ejecutivo_asignado, canal_origen, monto_estimado_clp, clasificacion_ia_requerimiento, resumen_ia_solicitud)
        VALUES (%s, %s, 'Asistente IA Cloud', 'Portal Web + API IA', %s, %s, %s);
    """, (id_cliente, etapa, monto, cat, res_ia))
    conn.close()
    return jsonify({"ok": True, "categoria": cat, "resumen": res_ia})


@app.route("/api/force_rupture", methods=["POST"])
def api_force_rupture():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO TELEMETRIA_IOT (camion_id, temp_camara, lat, `long`, combustible_pct, alerta_ruptura_frio)
        VALUES ('CAM-COF-001', 9.6, -38.7395, -72.5980, 64, 1);
    """)
    cur.execute("""
        INSERT INTO OPORTUNIDAD_CRM (id_cliente, etapa_pipeline, ejecutivo_asignado, canal_origen, monto_estimado_clp, clasificacion_ia_requerimiento, resumen_ia_solicitud)
        VALUES (1, '6. Monitoreo Postventa Frio', 'Alerta Automatica Docker IoT', 'Telemetria Docker EC2', 2680000, 'ALERTA CRITICA RUPTURA FRIO', '[Alerta IoT -> CRM] Camion CAM-COF-001 reporta 9.6 C en ruta a Hospital HHHA.');
    """)
    conn.close()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
