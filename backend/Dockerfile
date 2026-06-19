# Base Python image
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc build-essential

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend scripts
COPY . .

# Ensure agent runs continuously without buffering output
CMD ["python", "-u", "run_live.py"]
