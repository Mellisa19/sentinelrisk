# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create a non-root user and switch to it
RUN useradd -m sentinel && chown -R sentinel /app
USER sentinel

# Expose port
EXPOSE 8000

# Command to run the application
# Using Gunicorn with Uvicorn workers for production performance
CMD ["gunicorn", "-c", "gunicorn_conf.py", "src.services.api:app"]
