FROM python:3.10-slim
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:1.1.0 /lambda-adapter /opt/extensions/lambda-adapter

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
ENV PORT=8000 AWS_LWA_PORT=8000 AWS_LWA_READINESS_CHECK_PATH=/health AWS_LWA_ASYNC_INIT=true

# Command to run the application using Uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
