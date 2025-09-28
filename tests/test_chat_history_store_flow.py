from app.chat_history_store import ChatHistoryStore


def test_ensure_session_creates_placeholder(tmp_path):
    db_path = tmp_path / "history.db"
    store = ChatHistoryStore(db_path=str(db_path))

    user_id = "tester"
    session_id = "session-placeholder"

    store.ensure_session(user_id, session_id)
    sessions = store.list_sessions(user_id)

    assert len(sessions) == 1
    record = sessions[0]
    assert record.session_id == session_id
    assert record.message_count == 0
    assert record.title == "New Conversation"


def test_sync_session_persists_transcript(tmp_path):
    db_path = tmp_path / "history.db"
    store = ChatHistoryStore(db_path=str(db_path))

    user_id = "tester"
    session_id = "session-123"
    messages = [
        {
            "role": "user",
            "content": "Hi there",
            "timestamp": "2024-01-01T00:00:00Z",
        },
        {
            "role": "assistant",
            "content": "Hello!",
            "timestamp": "2024-01-01T00:00:10Z",
        },
    ]

    store.sync_session(user_id, session_id, messages)

    sessions = store.list_sessions(user_id)
    assert len(sessions) == 1
    record = sessions[0]
    assert record.session_id == session_id
    assert record.message_count == len(messages)
    assert record.last_message_preview is not None

    transcript = store.get_transcript(user_id, session_id)
    assert transcript == messages

    removed = store.delete_session(user_id, session_id)
    assert removed is True
    assert store.get_transcript(user_id, session_id) == []
