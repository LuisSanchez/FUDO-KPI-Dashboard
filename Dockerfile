# Pizza EBITDA Simulator — single image: React frontend + Django backend.
# Build:  docker build -t omp .
# Run:    docker run -p 8000:8000 omp
# Then open http://localhost:8000

# -----------------------------------------------------------------------------
# Stage 1: Build React frontend
# -----------------------------------------------------------------------------
FROM node:25-alpine3.22 AS frontend-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --legacy-peer-deps 2>/dev/null || npm install --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Django backend + serve frontend
# -----------------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=pizza_simulator.settings

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend code
COPY backend/ ./

# Copy built frontend into backend static area (Django will serve it)
COPY --from=frontend-build /app/frontend/build ./frontend_build

# Create media directory for uploads
RUN mkdir -p media

EXPOSE 8000

# Run migrations then start server (static files served from frontend_build/static)
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn pizza_simulator.wsgi:application --bind 0.0.0.0:8000 --timeout 120 --graceful-timeout 30"]
