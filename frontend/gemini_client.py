from __future__ import annotations

import os

import httpx
import streamlit as st


def get_backend_url() -> str:
    return os.getenv("FRONTEND_BACKEND_URL", "http://localhost:8000").rstrip("/")


def request_gemini_response(
    question: str,
    dataset_context: str | None = None,
    session_id: str = "default",
) -> dict[str, object] | None:
    backend_url = os.getenv("FRONTEND_BACKEND_URL", "http://localhost:8000").rstrip("/")

    try:
        response = httpx.post(
            f"{backend_url}/api/v1/chat/gemini",
            json={"question": question, "dataset_context": dataset_context, "session_id": session_id},
            timeout=35,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as error:
        detail = error.response.json().get("detail", "Gemini request failed.")
        st.warning(detail)
    except httpx.TimeoutException:
        st.warning("Gemini request timed out.")
    except httpx.HTTPError:
        st.warning("Backend is not reachable. Start the FastAPI server to use Gemini chat.")

    return None


def load_chat_history(session_id: str) -> list[dict[str, str]] | None:
    try:
        response = httpx.get(f"{get_backend_url()}/api/v1/chat/history/{session_id}", timeout=10)
        response.raise_for_status()
        messages = response.json().get("messages", [])
        return [{"role": message["role"], "content": message["content"]} for message in messages]
    except httpx.HTTPError:
        return None


def reset_chat_history(session_id: str) -> None:
    try:
        httpx.delete(f"{get_backend_url()}/api/v1/chat/history/{session_id}", timeout=10)
    except httpx.HTTPError:
        return
