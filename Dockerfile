# -----------------------------
# Base stage: official Python image
# -----------------------------
# Python 3.12: required by the pinned data stack (numpy 2.5.3 needs >=3.12,
# pandas 3.0.5 needs >=3.11). Do not downgrade below 3.12.
FROM python:3.12-slim

# Prevent Python from writing .pyc files and ensure immediate output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# -----------------------------
# Install system dependencies
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
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

# Streamlit port
EXPOSE 8501

# -----------------------------
# Run the dashboard by default (use docker-compose for the ETL service)
# -----------------------------
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
