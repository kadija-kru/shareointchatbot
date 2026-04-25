FROM python:3.11-slim

WORKDIR /app

# System dependencies required by faiss-cpu and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY app/ ./app/
COPY data/ ./data/

# Entrypoint script (waits for Ollama + pulls model)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create index persistence directory
RUN mkdir -p /app/.index

# Streamlit config to disable telemetry and set defaults
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501

EXPOSE 8501

ENTRYPOINT ["/entrypoint.sh"]
