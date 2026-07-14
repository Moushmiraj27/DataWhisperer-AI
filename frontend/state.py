from __future__ import annotations

import streamlit as st


DEFAULT_SUGGESTIONS = [
    "Summarize this dataset",
    "Which columns have missing values?",
    "What trends stand out?",
    "Suggest useful visualizations",
]


def initialize_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("recent_chats", ["Sales analysis", "Customer churn review", "CSV quality check"])
    st.session_state.setdefault("suggested_question", None)


def queue_question(question: str) -> None:
    st.session_state.suggested_question = question


def consume_queued_question() -> str | None:
    question = st.session_state.get("suggested_question")
    st.session_state.suggested_question = None
    return question


def add_chat_exchange(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": "The analysis engine is not connected yet. This dashboard is ready for the next feature layer.",
        }
    )
