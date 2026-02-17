# Multi-stage build for the web interface

# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
# Use npm install instead of npm ci for better error visibility
RUN npm install --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend build from previous stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:////app/data/beverage_brands.db
ENV FRONTEND_BUILD_PATH=/app/frontend/build

# Expose port
EXPOSE 8000

# Initialize database and start server
CMD ["sh", "-c", "cd /app/backend && python init_db.py && uvicorn app:app --host 0.0.0.0 --port 8000"]
