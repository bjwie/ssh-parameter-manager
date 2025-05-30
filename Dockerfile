# SSH Parameter Manager Dockerfile
FROM python:3.9-slim

# Set metadata
LABEL maintainer="SSH Parameter Manager Team"
LABEL description="A professional tool for managing Symfony parameters.yml files via SSH"
LABEL version="2.1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=web_server.py
ENV FLASK_ENV=production

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY *.html ./
COPY ssh_config.example.yml ./

# Create directories for data
RUN mkdir -p /app/logs /app/backups /app/downloaded_configs

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Create SSH directory for the app user
RUN mkdir -p /home/app/.ssh && \
    chmod 700 /home/app/.ssh

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Default command
CMD ["python", "web_server.py"]