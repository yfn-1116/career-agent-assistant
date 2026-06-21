FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[demo]"

# Copy source
COPY src/ src/
COPY demo/ demo/
COPY data/ data/

# Default: Streamlit demo
EXPOSE 8501
CMD ["streamlit", "run", "demo/streamlit/app.py", \
     "--server.address=0.0.0.0", "--server.port=8501"]
