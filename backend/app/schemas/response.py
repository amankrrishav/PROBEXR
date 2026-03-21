"""
Standard API response envelope for consistent client-side parsing.

Usage in routers:
    from app.schemas.response import APIResponse, paginated_response

    @router.get("/items")
    async def list_items(pagination: Pagination) -> APIResponse:
        items = ...
        return paginated_response(items, total=100, skip=pagination.skip, limit=pagination.limit)
"""
from typing import Any, Optional

from pydantic import BaseModel


class PaginationMeta(BaseModel):
    total: int
    skip: int
    limit: int
    has_more: bool


class APIResponse(BaseModel):
    """Standard response envelope. All list/detail endpoints should use this."""
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    meta: Optional[dict] = None


def paginated_response(
    data: Any,
    *,
    total: int,
    skip: int,
    limit: int,
) -> APIResponse:
    """Helper to build a paginated response."""
    return APIResponse(
        data=data,
        meta=PaginationMeta(
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        ).model_dump(),
    )
