# Hugging Face Spaces — Dockerfile
# Runs FastAPI backend (port 8000) + Gradio frontend (port 7860) in one container.

FROM python:3.13-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user (HF Spaces runs as UID 1000)
RUN useradd -m -u 1000 user && \
    chown -R user:user /app

USER user

# Expose the Gradio port (required by HF Spaces)
EXPOSE 7860

# Start FastAPI in the background, wait for it, then launch Gradio
CMD python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 & \
    sleep 3 && \
    python frontend/app.py
