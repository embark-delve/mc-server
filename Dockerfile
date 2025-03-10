FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create volume mount points
RUN mkdir -p /data /plugins /config /backups
VOLUME ["/data", "/plugins", "/config", "/backups"]

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set entrypoint
ENTRYPOINT ["python", "minecraft-server.py"]

# Default command
CMD ["--help"] 