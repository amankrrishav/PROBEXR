"""
Document management tests — list, delete, pagination, auth guards.
"""
import pytest
from httpx import AsyncClient


# ---- List Documents ----

@pytest.mark.asyncio
async def test_list_documents_empty(authed_client: AsyncClient):
    """New user with no documents gets empty list."""
    res = await authed_client.get("/documents/")
    assert res.status_code == 200
    data = res.json()
    assert data["documents"] == []
    assert data["total"] == 0
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_documents_with_data(authed_client: AsyncClient, document_id: int):
    """After ingesting a document, it appears in the list."""
    res = await authed_client.get("/documents/")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    doc_ids = [d["id"] for d in data["documents"]]
    assert document_id in doc_ids
    # Each document should have expected fields
    doc = data["documents"][0]
    assert "title" in doc
    assert "word_count" in doc
    assert "created_at" in doc


@pytest.mark.asyncio
async def test_list_documents_pagination(authed_client: AsyncClient):
    """Pagination params are respected."""
    # Ingest 3 documents
    for i in range(3):
        await authed_client.post(
            "/ingest/text",
            json={"text": f"Document number {i}. " * 20, "title": f"Doc {i}"},
        )

    # Page 1, per_page=2
    res = await authed_client.get("/documents/?page=1&per_page=2")
    assert res.status_code == 200
    data = res.json()
    assert len(data["documents"]) == 2
    assert data["total"] == 3
    assert data["pages"] == 2

    # Page 2
    res2 = await authed_client.get("/documents/?page=2&per_page=2")
    data2 = res2.json()
    assert len(data2["documents"]) == 1


@pytest.mark.asyncio
async def test_list_documents_unauthenticated(client: AsyncClient):
    res = await client.get("/documents/")
    assert res.status_code == 401


# ---- Delete Document ----

@pytest.mark.asyncio
async def test_delete_document_success(authed_client: AsyncClient, document_id: int):
    res = await authed_client.delete(f"/documents/{document_id}")
    assert res.status_code == 204

    # Verify it's gone
    list_res = await authed_client.get("/documents/")
    doc_ids = [d["id"] for d in list_res.json()["documents"]]
    assert document_id not in doc_ids


@pytest.mark.asyncio
async def test_delete_document_not_found(authed_client: AsyncClient):
    res = await authed_client.delete("/documents/999999")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_unauthenticated(client: AsyncClient):
    res = await client.delete("/documents/1")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_delete_document_wrong_user(client: AsyncClient, document_id: int):
    """User B cannot delete User A's document."""
    from tests.conftest import verify_user_email

    # Register and verify a second user
    res = await client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "OtherPass123!"},
    )
    assert res.status_code == 201
    other_token = res.json()["access_token"]
    await verify_user_email(client, "other@example.com")

    client.cookies.set("access_token", f"Bearer {other_token}")
    del_res = await client.delete(f"/documents/{document_id}")
    assert del_res.status_code == 404  # appears as not found for wrong user

# ---------------------------------------------------------------------------
# N-12: Document.url field has max_length=2048
# ---------------------------------------------------------------------------

def test_document_url_has_max_length():
    """Document.url must define max_length to prevent unbounded storage."""
    import inspect
    src = open('app/models/document.py').read()
    url_lines = [l for l in src.split('\n') if 'url' in l and 'Field' in l]
    assert url_lines, "Document must have a url field with Field()"
    assert any('max_length' in l for l in url_lines), (
        f"Document.url must have max_length constraint. Found: {url_lines}"
    )