# Use Python 3.9 slim base image
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies for pandas, numpy, sentence-transformers, etc.
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (leverage Docker build cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project into the container
COPY . .

# Default command: run orchestrator
CMD ["python", "src/orchestrator.py"]
