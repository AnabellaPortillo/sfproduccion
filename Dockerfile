FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Crear la base de datos y cargar datos iniciales en el primer arranque
ENTRYPOINT ["sh", "-c", "python seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

EXPOSE 8000
