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

# Default command
CMD ["python", "server.py"]
