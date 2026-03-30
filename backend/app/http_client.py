
import httpx

# Global httpx.AsyncClient instantiated during app lifespan
# Reusing this client avoids establishing new TCP/TLS connections per request
client: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    """Get the global HTTP client."""
    global client
    if client is None:
        # Fallback for tests or extreme edge cases, though lifespan should handle this
        client = httpx.AsyncClient()
    return client
