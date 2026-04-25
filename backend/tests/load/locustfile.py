"""
Load/stress test script using Locust.

Task #45: Verify rate limiting, connection pool behavior, and overall API
throughput under concurrent load.

Usage:
    pip install locust
    locust -f tests/load/locustfile.py --host http://localhost:8000/api/v1

Then open http://localhost:8089 to control the test.
"""

from locust import HttpUser, between, task

SAMPLE_TEXT = (
    "Artificial intelligence has transformed the technology landscape dramatically. "
    "Machine learning algorithms now power recommendation systems, natural language "
    "processing, and computer vision applications across industries. Researchers "
    "continue to push the boundaries of what is possible with deep learning "
    "architectures. Companies invest billions of dollars annually in AI research and "
    "development. The impact of these technologies extends beyond the tech sector "
    "into healthcare, finance, education, and manufacturing. Despite rapid progress, "
    "significant challenges remain in areas such as model interpretability, data "
    "privacy, and ethical deployment."
)


class HealthCheckUser(HttpUser):
    """Lightweight user that just hits health endpoints."""

    wait_time = between(0.5, 2)
    weight = 3  # 3x more common than other users

    @task
    def health(self):
        self.client.get("/health")

    @task
    def ready(self):
        self.client.get("/ready")


class SummarizeUser(HttpUser):
    """Simulates a user summarizing text."""

    wait_time = between(2, 5)
    weight = 2

    @task(3)
    def summarize_brief(self):
        self.client.post(
            "/summarize",
            json={"text": SAMPLE_TEXT, "length": "brief"},
        )

    @task(2)
    def summarize_standard(self):
        self.client.post(
            "/summarize",
            json={"text": SAMPLE_TEXT, "length": "standard"},
        )

    @task(1)
    def summarize_detailed(self):
        self.client.post(
            "/summarize",
            json={"text": SAMPLE_TEXT, "length": "detailed"},
        )


class AuthUser(HttpUser):
    """Tests auth rate limiting and login flow under load."""

    wait_time = between(1, 3)
    weight = 1

    @task(5)
    def login_attempt(self):
        """Simulate login attempts (many will fail — that's the point)."""
        self.client.post(
            "/auth/login",
            json={"email": "loadtest@example.com", "password": "WrongPass123!"},
            catch_response=True,
        )

    @task(1)
    def register_attempt(self):
        """Attempt registration (will hit duplicate after first success)."""
        import uuid

        email = f"loadtest-{uuid.uuid4().hex[:8]}@example.com"
        self.client.post(
            "/auth/register",
            json={"email": email, "password": "LoadTest123!@#"},
            catch_response=True,
        )


class DocumentUser(HttpUser):
    """Tests document listing with ETag support."""

    wait_time = between(2, 5)
    weight = 1

    @task
    def list_documents(self):
        self.client.get("/documents/")

    @task
    def list_documents_with_etag(self):
        """First request gets ETag, second should get 304."""
        res = self.client.get("/documents/", name="/documents/ (initial)")
        etag = res.headers.get("etag")
        if etag:
            self.client.get(
                "/documents/",
                headers={"If-None-Match": etag},
                name="/documents/ (etag)",
            )
