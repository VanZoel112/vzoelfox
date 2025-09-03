# VzoelFox Userbot Dockerfile
# Founder: Vzoel Fox's Ltpn 🤩
# Multi-stage build untuk optimized image size

# Build stage
FROM python:3.11-slim as builder

LABEL maintainer="Vzoel Fox's Ltpn"
LABEL description="VzoelFox Premium Telegram Userbot"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN useradd -r -s /bin/false -m -d /app vzoel

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/sessions && \
    chown -R vzoel:vzoel /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Switch to non-root user
USER vzoel

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)" || exit 1

# Expose port (if needed for web interface)
EXPOSE 8080

# Default command
CMD ["python3", "main.py"]