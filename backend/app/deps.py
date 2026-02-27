"""
Dependencies for routes — auth, rate limits, etc.
Route handlers should import these aliases instead of touching auth internals.
"""
from typing import Annotated, Optional

from fastapi import Depends
from sqlmodel import Session

from app.db import get_session
from app.models.user import User
from app.services.auth import get_current_user, get_optional_user

# --- Base Dependency ---
DbSession = Annotated[Session, Depends(get_session)]

# --- Auth Dependencies ---
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]

