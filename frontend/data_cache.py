from __future__ import annotations

import hashlib
from io import BytesIO

import pandas as pd
import streamlit as st

from frontend.csv_upload import DatasetProfile, load_csv_from_buffer, profile_dataset
from frontend.eda import EdaReport, generate_eda_report
from frontend.suggestions import generate_suggested_questions


def get_file_fingerprint(filename: str, content: bytes) -> str:
    digest = hashlib.sha256(content).hexdigest()
    return f"{filename}:{len(content)}:{digest}"


@st.cache_data(show_spinner=False)
def load_dataframe_cached(file_fingerprint: str, _content: bytes) -> pd.DataFrame:
    _ = file_fingerprint
    return load_csv_from_buffer(BytesIO(_content))


@st.cache_data(show_spinner=False)
def profile_dataset_cached(file_fingerprint: str, _dataframe: pd.DataFrame) -> DatasetProfile:
    _ = file_fingerprint
    return profile_dataset(_dataframe)


@st.cache_data(show_spinner=False)
def generate_eda_report_cached(file_fingerprint: str, _dataframe: pd.DataFrame) -> EdaReport:
    _ = file_fingerprint
    return generate_eda_report(_dataframe)


@st.cache_data(show_spinner=False)
def generate_suggestions_cached(file_fingerprint: str, _dataframe: pd.DataFrame) -> list[str]:
    _ = file_fingerprint
    return generate_suggested_questions(_dataframe)
