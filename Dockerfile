# -----------------------------
# Base stage: official Python image
# -----------------------------
FROM python:3.10-slim

# Prevent Python from writing .pyc files and ensure immediate output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------------------------
# Install system dependencies
# -----------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    default-mysql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Create working directory
# -----------------------------
WORKDIR /app

# -----------------------------
# Copy dependency files first (for cache)
# -----------------------------
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Copy the rest of the project
# -----------------------------
COPY . .

# -----------------------------
# Run ETL script by default
# -----------------------------
CMD ["python", "etl/etl_main.py"]