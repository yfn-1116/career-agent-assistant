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
COPY startup.sh startup.sh
RUN chmod +x startup.sh

# Expose both FastAPI backend and Streamlit frontend
EXPOSE 8000 8501

# Run both services via startup script
CMD ["./startup.sh"]
