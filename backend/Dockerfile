FROM python:3.10-slim

WORKDIR /app

# Keep only build tools needed by native Python dependencies. DOCX ingestion uses
# docx2txt directly, so the Lambda image does not need a desktop Office/JRE stack.
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Lambda runs with a read-only application directory; place model and temp caches in /tmp.
ENV PYTHONPATH=/app HOME=/tmp XDG_CACHE_HOME=/tmp/.cache HF_HOME=/tmp/huggingface FASTEMBED_CACHE_PATH=/tmp/fastembed_cache TMPDIR=/tmp

# Fail the image build if the dedicated deletion-sync handler is missing from the packaged app.
RUN python -c "import app.lambdas.cognito_user_delete_sync as sync; assert callable(sync.handler)"

# AWS Lambda Runtime Interface Client + Mangum expose this FastAPI app through a Function URL.
ENTRYPOINT ["/usr/local/bin/python", "-m", "awslambdaric"]
CMD ["app.lambda_handler.handler"]
