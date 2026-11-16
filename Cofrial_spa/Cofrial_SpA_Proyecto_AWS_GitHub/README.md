# Cofrial SpA — Prototipo de Transformación Digital Operativa (AWS + Docker IoT + BI + IA)

**Autor:** Juan Garrido Fuentes  
**Asignatura:** Transformación Digital (TIEL15) — INACAP Sede Temuco  
**Docente:** Felipe Andrés Henríquez Vilugron  

## Estructura del Repositorio

* `database/init_db.py`: Script de creación del esquema relacional normalizado en **3NF** en **Amazon RDS (MySQL)** y carga inicial de datos (productos refrigerados, clientes B2B/B2C, listas de precios, oportunidades CRM y 50 camiones `CAM-COF-001` a `CAM-COF-050`).
* `web_app/app.py`: Aplicación web unificada en **Flask + Gunicorn** que implementa:
  1. **Portal E-Commerce B2B / B2C** con diferenciación tarifaria por perfil, carrito de compras y descuento atómico de stock en RDS.
  2. **Consola CRM Operativa + Asistente IA (Costo Cero)** conectada a la API pública gratuita `https://text.pollinations.ai/` para clasificar requerimientos comerciales y clínicos.
  3. **Dashboard de Business Intelligence (BI)** en tiempo real con KPIs, gráfico comparativo (Chart.js) y mapa GPS de La Araucanía (Leaflet).
* `iot_docker/Dockerfile` y `iot_docker/iot_simulator.py`: Contenedor Docker ejecutado en **Amazon EC2** que inyecta continuamente en RDS los parámetros exigidos (`camion_id`, `temp_camara`, `lat`, `long`, `combustible_pct`, `alerta_ruptura_frio`).
* `.env.example`: Plantilla de variables de entorno para conexión a Amazon RDS.

## Despliegue Rápido en AWS EC2 (Ubuntu)

1. Configurar las variables de entorno de Amazon RDS (`RDS_HOST`, `RDS_USER`, `RDS_PASS`, `RDS_DB`).
2. Inicializar la base de datos en 3NF:
   ```bash
   python3 database/init_db.py
   ```
3. Levantar el contenedor Docker IoT:
   ```bash
   cd iot_docker
   docker build -t cofrial-iot-simulator .
   docker run -d --name cofrial-iot-node --restart unless-stopped -e RDS_HOST=... -e RDS_USER=... -e RDS_PASS=... -e RDS_DB=cofrial_db cofrial-iot-simulator
   ```
4. Ejecutar la aplicación web:
   ```bash
   cd web_app
   pip install -r requirements.txt
   gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
   ```
