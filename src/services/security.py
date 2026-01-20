import os
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

# Define the API Key header name
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Load API Key from environment, default for dev
SENTINEL_API_KEY = os.getenv("SENTINEL_API_KEY", "sentinel-dev-key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Validates the API Key from the request header.
    """
    if api_key == SENTINEL_API_KEY:
        return api_key
    
    # If key is missing or invalid
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials"
    )
