from __future__ import annotations

import json
from pathlib import Path

from backend.app.application.schemas.memory import ChatMessage


class ConversationMemoryError(RuntimeError):
    """Raised when chat memory cannot be read or written."""


class ConversationMemory:
    def __init__(self, history_path: str, memory_limit: int = 10) -> None:
        self._history_path = Path(history_path)
        self._memory_limit = memory_limit

    def get_messages(self, session_id: str) -> list[ChatMessage]:
        store = self._read_store()
        return [ChatMessage.model_validate(message) for message in store.get(session_id, [])]

    def get_recent_context(self, session_id: str) -> str:
        messages = self.get_messages(session_id)[-self._memory_limit :]
        if not messages:
            return "No previous conversation."

        return "\n".join(f"{message.role}: {message.content}" for message in messages)

    def append_exchange(self, session_id: str, user_message: str, assistant_message: str) -> None:
        store = self._read_store()
        messages = store.setdefault(session_id, [])
        messages.append(ChatMessage(role="user", content=user_message).model_dump(mode="json"))
        messages.append(ChatMessage(role="assistant", content=assistant_message).model_dump(mode="json"))
        self._write_store(store)

    def reset(self, session_id: str) -> None:
        store = self._read_store()
        store.pop(session_id, None)
        self._write_store(store)

    def _read_store(self) -> dict[str, list[dict]]:
        if not self._history_path.exists():
            return {}

        try:
            with self._history_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise ConversationMemoryError("Chat history file is corrupted.") from error

        if not isinstance(data, dict):
            raise ConversationMemoryError("Chat history file has an invalid format.")
        return data

    def _write_store(self, store: dict[str, list[dict]]) -> None:
        self._history_path.parent.mkdir(parents=True, exist_ok=True)
        with self._history_path.open("w", encoding="utf-8") as file:
            json.dump(store, file, indent=2)


def build_context_with_memory(dataset_context: str | None, conversation_context: str) -> str:
    dataset_block = dataset_context.strip() if dataset_context else "No dataset context was provided."
    return f"Previous conversation:\n{conversation_context}\n\nDataset context:\n{dataset_block}"
