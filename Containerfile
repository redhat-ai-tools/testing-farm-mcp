FROM registry.redhat.io/ubi9/python-311

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py ./
COPY *.env* ./

# Expose port for SSE transport (configurable via environment)
EXPOSE 8000

# Health check for SSE transport
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD if [ "$MCP_TRANSPORT" = "sse" ]; then \
            curl -f http://localhost:${MCP_PORT}/health || exit 1; \
        else \
            echo "stdio transport - no health check needed"; \
        fi

# Default command
CMD ["python", "server.py"]
