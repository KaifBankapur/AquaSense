# AquaSense backend — FastAPI serving the Parquet analytical layer.
# The Spark pipeline itself runs on the host (Windows: needs JDK 17 + winutils);
# this image serves whatever `./bigdata` is mounted at /app/bigdata.

FROM python:3.14-slim

# PySpark is imported by /api/health; a JRE keeps the image self-sufficient.
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend

# Config resolves project root as the parent of backend/app/core/config.py
# (3 levels up from core) -> /app. The analytical layer is mounted at
# /app/bigdata via docker-compose.
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]