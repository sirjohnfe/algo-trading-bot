# Use official Python runtime
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# gcc/g++ needed for some math libs if wheels not found
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Strategy Code
COPY . .

# Environment Variables (Placeholder - should be injected at runtime)
# ENV APCA_API_KEY_ID=...

# Default Command: Scheduler Mode
CMD ["python", "main.py"]
