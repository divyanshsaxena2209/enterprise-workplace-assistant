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

# Lambda runs with a read-only application directory; place model and temp caches in /tmp.
ENV HOME=/tmp XDG_CACHE_HOME=/tmp/.cache HF_HOME=/tmp/huggingface FASTEMBED_CACHE_PATH=/tmp/fastembed_cache TMPDIR=/tmp

# AWS Lambda Runtime Interface Client + Mangum expose this FastAPI app through a Function URL.
ENTRYPOINT ["/usr/local/bin/python", "-m", "awslambdaric"]
CMD ["app.lambda_handler.handler"]
