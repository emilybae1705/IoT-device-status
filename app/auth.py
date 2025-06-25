from fastapi import HTTPException, Header
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


def verify_api_key(x_api_key: Optional[str] = Header(None, alias="x-api-key")):
    """Verify API key for authentication"""

    api_key = os.getenv("API_KEY")

    # skip authentication if no API key is configured
    if not api_key:
        return "no_auth_required"

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="missing API key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key
    if api_key != x_api_key:
        raise HTTPException(
            status_code=401,
            detail="invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return x_api_key
