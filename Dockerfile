FROM python:3.12-slim

# Prevent Python from writing .pyc files & buffer stdout/stderr for real-time logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies if required (e.g., gcc/libpq if using PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /lib/apt/lists/*

# Copy and install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create volume target directory for SQLite database persistence
RUN mkdir -p /app/data

CMD ["python", "main.py"]