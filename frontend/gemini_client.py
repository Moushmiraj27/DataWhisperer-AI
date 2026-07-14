from __future__ import annotations

import asyncio
import os
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx
import streamlit as st


def get_backend_url() -> str:
    return os.getenv("FRONTEND_BACKEND_URL", "http://localhost:8000").rstrip("/")


def request_gemini_response(
    question: str,
    dataset_context: str | None = None,
    session_id: str = "default",
) -> dict[str, object] | None:
    return run_async(
        request_gemini_response_async(
            question=question,
            dataset_context=dataset_context,
            session_id=session_id,
        )
    )


async def request_gemini_response_async(
    question: str,
    dataset_context: str | None = None,
    session_id: str = "default",
) -> dict[str, object] | None:
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.post(
                f"{get_backend_url()}/api/v1/chat/gemini",
                json={"question": question, "dataset_context": dataset_context, "session_id": session_id},
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as error:
        detail = extract_error_detail(error.response)
        st.warning(detail)
    except httpx.TimeoutException:
        st.warning("Gemini request timed out.")
    except httpx.HTTPError:
        st.warning("Backend is not reachable. Start the FastAPI server to use Gemini chat.")

    return None


def extract_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return "Gemini request failed."

    detail = payload.get("detail") if isinstance(payload, dict) else None
    return str(detail) if detail else "Gemini request failed."


def load_chat_history(session_id: str) -> list[dict[str, str]] | None:
    return run_async(load_chat_history_async(session_id))


async def load_chat_history_async(session_id: str) -> list[dict[str, str]] | None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{get_backend_url()}/api/v1/chat/history/{session_id}")
        response.raise_for_status()
        messages = response.json().get("messages", [])
        return [{"role": message["role"], "content": message["content"]} for message in messages]
    except httpx.HTTPError:
        return None


def reset_chat_history(session_id: str) -> None:
    run_async(reset_chat_history_async(session_id))


async def reset_chat_history_async(session_id: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.delete(f"{get_backend_url()}/api/v1/chat/history/{session_id}")
    except httpx.HTTPError:
        return


def run_async(coroutine: Coroutine[Any, Any, Any]) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coroutine).result()
