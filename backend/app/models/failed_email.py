"""Dead-letter model for failed email deliveries.

When an email send fails, the details are persisted here for
manual review, retry, or alerting.
"""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class FailedEmail(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    to_email: str = Field(max_length=320, index=True)
    subject: str = Field(max_length=500)
    error: str = Field(default="")
    template: str = Field(default="", max_length=100)  # e.g. "verification", "magic_link"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    retried_at: datetime | None = Field(default=None)
    retry_count: int = Field(default=0)
