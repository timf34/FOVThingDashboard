# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install debugging tools
RUN apt-get update && apt-get install -y procps net-tools curl

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy certificates first and set proper permissions
COPY aws-iot-certs/ ./aws-iot-certs/
RUN chmod 600 ./aws-iot-certs/**/private.pem.key

# Copy the rest of the application
COPY . .

# Verify that certificates exist
RUN ls -la ./aws-iot-certs/fov-dashboard-dublin-client/

# Run FastAPI using Uvicorn with more verbose logging
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]