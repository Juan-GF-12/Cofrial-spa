import os
import pymysql

host = os.environ.get("RDS_HOST", "localhost")
user = os.environ.get("RDS_USER", "admin")
password = os.environ.get("RDS_PASS", "")
dbname = os.environ.get("RDS_DB", "cofrial_db")

conn = pymysql.connect(host=host, user=user, password=password, port=3306, autocommit=True)
cur = conn.cursor()
cur.execute(f"CREATE DATABASE IF NOT EXISTS {dbname} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
cur.execute(f"USE {dbname};")

sql_statements = [
    """CREATE TABLE IF NOT EXISTS CATEGORIA_PRODUCTO (
        id_categoria INT AUTO_INCREMENT PRIMARY KEY,
        nombre_categoria VARCHAR(80) NOT NULL,
        temp_min_req FLOAT NOT NULL,
        temp_max_req FLOAT NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS LISTA_PRECIO (
        id_lista_precio INT AUTO_INCREMENT PRIMARY KEY,
        codigo_perfil VARCHAR(10) NOT NULL,
        nombre_lista VARCHAR(80) NOT NULL,
        plazo_pago_dias INT NOT NULL DEFAULT 0
    );""",
    """CREATE TABLE IF NOT EXISTS PRODUCTO (
        id_producto INT AUTO_INCREMENT PRIMARY KEY,
        id_categoria INT NOT NULL,
        codigo_sku VARCHAR(30) UNIQUE NOT NULL,
        nombre_producto VARCHAR(120) NOT NULL,
        unidad_medida VARCHAR(20) NOT NULL,
        stock_actual DECIMAL(10,2) NOT NULL,
        precio_b2b DECIMAL(12,2) NOT NULL,
        precio_b2c DECIMAL(12,2) NOT NULL,
        FOREIGN KEY (id_categoria) REFERENCES CATEGORIA_PRODUCTO(id_categoria)
    );""",
    """CREATE TABLE IF NOT EXISTS CLIENTE (
        id_cliente INT AUTO_INCREMENT PRIMARY KEY,
        id_lista_precio INT NOT NULL,
        rut_cliente VARCHAR(15) UNIQUE NOT NULL,
        tipo_perfil VARCHAR(10) NOT NULL,
        razon_social_nombre VARCHAR(150) NOT NULL,
        giro_institucion VARCHAR(100),
        email_contacto VARCHAR(120),
        comuna VARCHAR(80) NOT NULL,
        FOREIGN KEY (id_lista_precio) REFERENCES LISTA_PRECIO(id_lista_precio)
    );""",
    """CREATE TABLE IF NOT EXISTS OPORTUNIDAD_CRM (
        id_oportunidad INT AUTO_INCREMENT PRIMARY KEY,
        id_cliente INT NOT NULL,
        etapa_pipeline VARCHAR(50) NOT NULL,
        ejecutivo_asignado VARCHAR(100) NOT NULL,
        canal_origen VARCHAR(40) NOT NULL,
        monto_estimado_clp DECIMAL(14,2) NOT NULL,
        clasificacion_ia_requerimiento VARCHAR(80),
        resumen_ia_solicitud TEXT,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_cliente) REFERENCES CLIENTE(id_cliente)
    );""",
    """CREATE TABLE IF NOT EXISTS PEDIDO (
        id_pedido INT AUTO_INCREMENT PRIMARY KEY,
        id_cliente INT NOT NULL,
        fecha_emision DATETIME DEFAULT CURRENT_TIMESTAMP,
        canal_venta VARCHAR(25) NOT NULL,
        estado_pedido VARCHAR(35) NOT NULL,
        monto_total DECIMAL(14,2) NOT NULL,
        camion_asignado VARCHAR(20) NOT NULL,
        FOREIGN KEY (id_cliente) REFERENCES CLIENTE(id_cliente)
    );""",
    """CREATE TABLE IF NOT EXISTS DETALLE_PEDIDO (
        id_detalle_pedido INT AUTO_INCREMENT PRIMARY KEY,
        id_pedido INT NOT NULL,
        id_producto INT NOT NULL,
        cantidad DECIMAL(10,2) NOT NULL,
        precio_unitario_aplicado DECIMAL(12,2) NOT NULL,
        FOREIGN KEY (id_pedido) REFERENCES PEDIDO(id_pedido),
        FOREIGN KEY (id_producto) REFERENCES PRODUCTO(id_producto)
    );""",
    """CREATE TABLE IF NOT EXISTS CAMION_FRIGORIFICO (
        camion_id VARCHAR(20) PRIMARY KEY,
        patente VARCHAR(12) NOT NULL,
        conductor VARCHAR(80) NOT NULL,
        ruta_actual VARCHAR(100) NOT NULL,
        rango_temp_min FLOAT NOT NULL,
        rango_temp_max FLOAT NOT NULL
    );""",
    """CREATE TABLE IF NOT EXISTS TELEMETRIA_IOT (
        id_telemetria BIGINT AUTO_INCREMENT PRIMARY KEY,
        camion_id VARCHAR(20) NOT NULL,
        timestamp_lectura DATETIME DEFAULT CURRENT_TIMESTAMP,
        temp_camara FLOAT NOT NULL,
        lat FLOAT NOT NULL,
        `long` FLOAT NOT NULL,
        combustible_pct INT NOT NULL,
        alerta_ruptura_frio BOOLEAN NOT NULL,
        FOREIGN KEY (camion_id) REFERENCES CAMION_FRIGORIFICO(camion_id)
    );"""
]

for stmt in sql_statements:
    cur.execute(stmt)

cur.execute("SELECT COUNT(*) FROM PRODUCTO;")
if cur.fetchone()[0] == 0:
    cur.execute("INSERT INTO CATEGORIA_PRODUCTO (nombre_categoria, temp_min_req, temp_max_req) VALUES ('Carnicos Refrigerados Vacuno', 0.0, 4.0), ('Congelados Industriales', -22.0, -18.0), ('Insumos Clinicos Termolables', 2.0, 8.0);")
    cur.execute("INSERT INTO LISTA_PRECIO (codigo_perfil, nombre_lista, plazo_pago_dias) VALUES ('B2B', 'Convenio Institucional Hospitales y Supermercados', 30), ('B2C', 'Tarifa Minorista Publico General', 0);")
    cur.execute("""INSERT INTO PRODUCTO (id_categoria, codigo_sku, nombre_producto, unidad_medida, stock_actual, precio_b2b, precio_b2c) VALUES
        (1, 'COF-VAC-001', 'Lomo Vetado Envasado al Vacio (Caja 20 kg)', 'CAJA 20KG', 180, 168000, 215000),
        (1, 'COF-VAC-002', 'Posta Negra Seleccion Institucional (Caja 15 kg)', 'CAJA 15KG', 240, 112000, 145000),
        (2, 'COF-CON-003', 'Pechuga Deshuesada Congelada IQF (Bloque 10 kg)', 'CAJA 10KG', 320, 42000, 56000),
        (2, 'COF-CON-004', 'Filete de Salmon Austral Ultra-Congelado (-20C)', 'CAJA 10KG', 95, 98000, 129000),
        (3, 'COF-CLI-005', 'Kit Nutricion Parenteral Refrigerada Hospitalaria', 'LOTE 12 UN', 150, 135000, 172000),
        (3, 'COF-CLI-006', 'Suero Biologico Cadena de Frio Certificada (2C-8C)', 'CAJA 24 UN', 210, 64000, 84000);""")
    cur.execute("""INSERT INTO CLIENTE (id_lista_precio, rut_cliente, tipo_perfil, razon_social_nombre, giro_institucion, email_contacto, comuna) VALUES
        (1, '61.608.100-K', 'B2B', 'Hospital Dr. Hernan Henriquez Aravena', 'Salud Publica / Hospital', 'abastecimiento@hhha.cl', 'Temuco'),
        (1, '76.112.450-8', 'B2B', 'Supermercados Cencosud Araucania', 'Retail Alimenticio', 'logistica.sur@cencosud.cl', 'Temuco'),
        (1, '77.890.123-4', 'B2B', 'Clinica Alemana de Temuco', 'Clinica Privada', 'compras@alemana.cl', 'Temuco'),
        (2, '18.456.789-2', 'B2C', 'Juan Garrido Fuentes (Cliente Directo B2C)', 'Consumidor Particular', 'juan.garrido@inacapmail.cl', 'Temuco'),
        (2, '15.987.321-5', 'B2C', 'Restaurante Fogones del Sur', 'Gastronomia Local', 'pedidos@fogones.cl', 'Villarrica');""")

    rutas = ['Ruta 5 Sur: Temuco -> Hospital HHHA', 'Ruta Villarrica-Pucon', 'Ruta Angol-Malleco', 'Ruta Imperial-Carahue', 'Ruta Lautaro-Victoria']
    for i in range(1, 51):
        cid = f"CAM-COF-{i:03d}"
        pat = f"RF-CL-{10+i}"
        cond = f"Conductor Flota #{i}"
        ruta = rutas[i % len(rutas)]
        cur.execute("INSERT IGNORE INTO CAMION_FRIGORIFICO VALUES (%s, %s, %s, %s, 0.0, 4.0);", (cid, pat, cond, ruta))

    cur.execute("""INSERT INTO OPORTUNIDAD_CRM (id_cliente, etapa_pipeline, ejecutivo_asignado, canal_origen, monto_estimado_clp, clasificacion_ia_requerimiento, resumen_ia_solicitud) VALUES
        (1, '5. Cerrado Ganado', 'Camila Rojas', 'E-commerce B2B', 2680000, 'URGENCIA CLINICA HOSPITALARIA', 'Abastecimiento prioritario de lotes refrigerados y nutricion parenteral con monitoreo IoT activo.'),
        (2, '3. Cotizado', 'Diego Munoz', 'Portal B2B', 5400000, 'ABASTECIMIENTO MAYORISTA B2B', 'Solicitud de 30 cajas de Lomo Vetado y 40 bloques IQF para sucursales de Temuco.'),
        (3, '6. Monitoreo Postventa Frio', 'Camila Rojas', 'Asistente IA', 1350000, 'AUDITORIA CADENA DE FRIO', 'Verificacion de trazabilidad termica (0C a 4C) en despacho hacia Clinica Alemana.'),
        (4, '5. Cerrado Ganado', 'Venta Automatica Web', 'E-commerce B2C', 201000, 'COMPRA DIRECTA MINORISTA B2C', 'Pedido minorista pagado en pasarela web con despacho urbano en Temuco.');""")

    cur.execute("""INSERT INTO PEDIDO (id_cliente, canal_venta, estado_pedido, monto_total, camion_asignado) VALUES
        (1, 'E-commerce B2B', 'En Ruta IoT', 2680000, 'CAM-COF-001'),
        (2, 'E-commerce B2B', 'En Ruta IoT', 1840000, 'CAM-COF-002'),
        (3, 'E-commerce B2B', 'Entregado Conforme', 1350000, 'CAM-COF-003'),
        (4, 'E-commerce B2C', 'En Ruta IoT', 201000, 'CAM-COF-004');""")

print("Base de datos 3NF en Amazon RDS inicializada con exito.")
