FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including LibreOffice and Java
# This is required for the DOCX -> PDF pipeline
RUN apt-get update && apt-get install -y \
    libreoffice \
    default-jre \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port (Railway respects $PORT but 8000 is a good default)
EXPOSE 8000

# Command to run the application using Uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
