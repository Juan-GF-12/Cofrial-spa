FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir pymysql
COPY iot_simulator.py /app/iot_simulator.py
CMD ["python", "-u", "iot_simulator.py"]
