from backend.app.infrastructure.persistence.conversation_memory import ConversationMemory, build_context_with_memory


def test_conversation_memory_persists_history(tmp_path) -> None:
    history_path = tmp_path / "chat_history.json"
    memory = ConversationMemory(str(history_path), memory_limit=4)

    memory.append_exchange("session-1", "What are missing values?", "There are two missing values.")
    reloaded_memory = ConversationMemory(str(history_path), memory_limit=4)

    messages = reloaded_memory.get_messages("session-1")

    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[0].content == "What are missing values?"
    assert messages[1].content == "There are two missing values."


def test_conversation_memory_returns_recent_context(tmp_path) -> None:
    memory = ConversationMemory(str(tmp_path / "chat_history.json"), memory_limit=2)
    memory.append_exchange("session-1", "Question one", "Answer one")
    memory.append_exchange("session-1", "Question two", "Answer two")

    context = memory.get_recent_context("session-1")

    assert "Question one" not in context
    assert "Question two" in context
    assert "Answer two" in context


def test_conversation_memory_resets_session(tmp_path) -> None:
    memory = ConversationMemory(str(tmp_path / "chat_history.json"))
    memory.append_exchange("session-1", "Question", "Answer")

    memory.reset("session-1")

    assert memory.get_messages("session-1") == []


def test_build_context_with_memory_includes_history_and_dataset() -> None:
    context = build_context_with_memory("Rows: 3", "user: What changed?")

    assert "Previous conversation:" in context
    assert "user: What changed?" in context
    assert "Rows: 3" in context
