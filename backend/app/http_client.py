import httpx
from typing import Optional

# Global httpx.AsyncClient instantiated during app lifespan
# Reusing this client avoids establishing new TCP/TLS connections per request
client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    """Get the global HTTP client."""
    global client
    if client is None:
        # Fallback for tests or extreme edge cases, though lifespan should handle this
        client = httpx.AsyncClient()
    return client
