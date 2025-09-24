# SynVectorDB githubshare - Docker Image
# Multi-stage build for optimized production image

# Build stage
FROM python:3.10-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY streamlit_app/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Create non-root user
RUN groupadd -r synvectordb && useradd -r -g synvectordb synvectordb

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/synvectordb/.local

# Copy application files
COPY streamlit_app/ ./streamlit_app/
COPY data/ ./data/
COPY manage.sh ./
COPY test_suite.py ./
COPY README.md ./

# Create logs directory
RUN mkdir -p logs

# Set permissions
RUN chown -R synvectordb:synvectordb /app
RUN chmod +x manage.sh test_suite.py

# Switch to non-root user
USER synvectordb

# Add local Python packages to PATH
ENV PATH=/home/synvectordb/.local/bin:$PATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/healthz || exit 1

# Expose port
EXPOSE 8501

# Default command
CMD ["python", "-m", "streamlit", "run", "streamlit_app/Home.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
