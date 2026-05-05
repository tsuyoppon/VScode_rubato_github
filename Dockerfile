# Dockerfile for t3.medium optimized deployment (4GB RAM, 2 vCPU)
FROM python:3.10-slim-bullseye

# Set environment variables for t3.medium optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TORCH_NUM_THREADS=2 \
    OMP_NUM_THREADS=2 \
    MKL_NUM_THREADS=2

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir torch==2.3.1 torchvision==0.18.1 --index-url https://download.pytorch.org/whl/cpu

# Copy application code
COPY app_minimal.py .
COPY auth_config.py .
COPY two_level_vit_predict_for_webap2.py .
COPY Twolevel_Vit_trialnew.py .
COPY model_downloader.py .
COPY config.py .
COPY admin_logger.py .
COPY admin_dashboard.py .

# Create directories for models and logs
RUN mkdir -p /app/models /app/logs

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app_minimal.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false"]