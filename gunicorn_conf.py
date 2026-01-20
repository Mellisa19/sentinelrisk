# Gunicorn Configuration

# Bind to 0.0.0.0 to expose externally (in container)
bind = "0.0.0.0:8000"

# Workers: Generally 2-4 x (Num Cores). Starting with 2 for safety.
workers = 2

# Worker Class: Critical for FastAPI/Asyncio
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
