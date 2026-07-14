from __future__ import annotations

import os

import httpx
import streamlit as st


def request_gemini_response(question: str, dataset_context: str | None = None) -> dict[str, object] | None:
    backend_url = os.getenv("FRONTEND_BACKEND_URL", "http://localhost:8000").rstrip("/")

    try:
        response = httpx.post(
            f"{backend_url}/api/v1/chat/gemini",
            json={"question": question, "dataset_context": dataset_context},
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
