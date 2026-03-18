"""
tests/test_chat_ordering.py — A-09: Chat history ORDER BY id tiebreaker

Verifies that the chat history query uses both created_at AND id as
ORDER BY columns so that messages with the same timestamp are always
returned in a deterministic order.
"""
import inspect


def test_chat_history_has_id_tiebreaker():
    """The chat history ORDER BY must include desc(ChatMessage.id) as a tiebreaker."""
    from app.services import chat
    src = inspect.getsource(chat)
    assert "desc(ChatMessage.id)" in src, (
        "Chat history ORDER BY must include desc(ChatMessage.id) as a tiebreaker "
        "to prevent non-deterministic ordering when two messages share the same timestamp"
    )


def test_chat_history_orders_by_created_at_first():
    """created_at must still be the primary sort key."""
    from app.services import chat
    src = inspect.getsource(chat)
    assert "desc(ChatMessage.created_at)" in src, (
        "Chat history must still order by created_at as the primary sort key"
    )


def test_chat_history_has_both_order_columns():
    """Both created_at and id must appear in the same order_by call."""
    from app.services import chat
    src = inspect.getsource(chat)
    # Find the order_by line and verify it contains both
    order_lines = [l for l in src.split('\n') if 'order_by' in l and 'ChatMessage' in l]
    assert any(
        'created_at' in l and 'id' in l
        for l in order_lines
    ), f"Expected order_by with both created_at and id, got: {order_lines}"