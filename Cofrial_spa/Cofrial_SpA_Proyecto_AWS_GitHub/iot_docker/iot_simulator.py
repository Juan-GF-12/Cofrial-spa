import os
import time
import random
import pymysql

host = os.environ.get("RDS_HOST", "localhost")
user = os.environ.get("RDS_USER", "admin")
password = os.environ.get("RDS_PASS", "")
dbname = os.environ.get("RDS_DB", "cofrial_db")

print(f"[IoT Docker] Iniciando simulacion continua hacia RDS: {host}...")

while True:
    try:
        conn = pymysql.connect(host=host, user=user, password=password, database=dbname, port=3306, autocommit=True)
        cur = conn.cursor()
        sample_trucks = [f"CAM-COF-{i:03d}" for i in random.sample(range(1, 51), 6)]
        for main_t in ["CAM-COF-001", "CAM-COF-002", "CAM-COF-003", "CAM-COF-004"]:
            if main_t not in sample_trucks:
                sample_trucks.append(main_t)

        for cid in sample_trucks:
            if random.random() < 0.18:
                temp = round(random.uniform(4.8, 9.4), 2)
                alerta = True
            else:
                temp = round(random.uniform(0.4, 3.7), 2)
                alerta = False

            lat = round(-38.7359 + random.uniform(-0.18, 0.18), 5)
            lon = round(-72.5904 + random.uniform(-0.18, 0.18), 5)
            comb = random.randint(28, 98)

            cur.execute("""
                INSERT INTO TELEMETRIA_IOT (camion_id, temp_camara, lat, `long`, combustible_pct, alerta_ruptura_frio)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (cid, temp, lat, lon, comb, alerta))

        cur.execute("""
            DELETE FROM TELEMETRIA_IOT
            WHERE id_telemetria NOT IN (
                SELECT id_telemetria FROM (
                    SELECT id_telemetria FROM TELEMETRIA_IOT ORDER BY id_telemetria DESC LIMIT 500
                ) AS t
            );
        """)
        conn.close()
        print("[IoT Docker] Lote de telemetria inyectado en Amazon RDS OK.")
    except Exception as e:
        print("[IoT Docker] Error temporal:", e)
    time.sleep(4)
