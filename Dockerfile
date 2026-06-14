# syntax=docker/dockerfile:1.7

# ==========================================
# Frontend Build Stage
# ==========================================
FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY frontend/ .

RUN npm run build


# ==========================================
# Backend Stage
# ==========================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY main.py .
COPY src ./src

# Copy frontend build result
COPY --from=frontend-builder /frontend/dist ./dist

EXPOSE 8021

CMD ["python", "main.py"]