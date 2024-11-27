# backend/Dockerfile

# Use official Python image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    texlive-full \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
COPY backend/base-requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r base-requirements.txt
RUN pip install -r requirements.txt
RUN python3 -m spacy download en_core_web_sm

COPY backend/app /app/app
# Copy project
COPY backend/migrations /app/migrations
COPY backend/.env /app/.env

# Expose port
EXPOSE 8000

# Run Alembic migrations and start the server
CMD ["bash", "-c", "alembic -c migrations/alembic.ini upgrade head || { echo 'Alembic failed'; exit 1; } && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
