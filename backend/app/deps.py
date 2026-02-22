"""
Dependencies for routes — optional auth, rate limits, etc.
Add get_current_user, require_plan("pro"), etc. when you add subscription/auth.
"""
from typing import Annotated

from fastapi import Depends

# Future: from app.services.auth import get_current_user, get_optional_user
# Future: from app.services.limits import check_usage_limit


def get_optional_user():
    """
    Placeholder: no auth yet. When you add auth (JWT or API key),
    return the current user or None for anonymous. Then use in routers:
    user = Depends(get_optional_user); if user: check_plan(user.plan)
    """
    return None


# Type alias for route injection when auth exists
OptionalUser = Annotated[None, Depends(get_optional_user)]
