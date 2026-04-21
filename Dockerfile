FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY bot /app/bot
COPY migrations /app/migrations
COPY frontend /app/frontend
COPY landing /app/landing
COPY certs /app/certs
COPY settings.py /app/settings.py
COPY alembic.ini /app/alembic.ini

EXPOSE 8000

