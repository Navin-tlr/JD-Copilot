FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HUB_ENABLE_HF_TRANSFER=0

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        git-lfs \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Copy and install python deps first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Configure SSL CA bundle via certifi
RUN python - <<'PY'
import certifi, os
ca = certifi.where()
print('Using CA bundle:', ca)
open('/etc/ssl/certs/ca-certificates.crt','a').close()
os.environ['SSL_CERT_FILE']=ca
os.environ['REQUESTS_CA_BUNDLE']=ca
PY

# Pre-fetch Docling models to avoid first-run failures
RUN python dev_tools/prefetch_docling_models.py

# Default: start API (ingest should be run separately or as part of init)
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


