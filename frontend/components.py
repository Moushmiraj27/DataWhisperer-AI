from __future__ import annotations

import os
import time
from typing import Any

import pandas as pd
import streamlit as st

from frontend.csv_upload import CsvValidationError, DatasetProfile, load_csv, profile_dataset
from frontend.eda import (
    EdaReport,
    create_boxplot,
    create_correlation_heatmap,
    create_histogram,
    create_missing_value_heatmap,
    generate_eda_report,
)
from frontend.state import DEFAULT_SUGGESTIONS, add_chat_exchange, consume_queued_question, queue_question


def render_sidebar() -> None:
    backend_url = os.getenv("FRONTEND_BACKEND_URL", "http://localhost:8000")

    with st.sidebar:
        st.markdown("### DataWhisperer AI")
        st.caption("Workspace")

        if st.button("New chat", icon=":material/add_comment:", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.divider()
        render_recent_chats()

        st.divider()
        st.text_input("Backend URL", value=backend_url, disabled=True)
        st.caption("Environment: development")


def render_recent_chats() -> None:
    st.markdown("#### Recent Chats")
    for chat_title in st.session_state.recent_chats:
        st.button(chat_title, icon=":material/forum:", use_container_width=True)


def render_header() -> None:
    st.markdown(
        """
        <div class="dw-hero">
            <div class="dw-kicker">AI data workspace</div>
            <h1 style="margin:0;">DataWhisperer AI</h1>
            <div class="dw-muted">Upload CSV files, inspect your data, and prepare questions for intelligent analysis.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_panel() -> tuple[pd.DataFrame, DatasetProfile, EdaReport] | None:
    st.markdown('<div class="dw-panel-title">Dataset</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

    if uploaded_file is None:
        render_empty_dataset_state()
        return None

    try:
        with st.spinner("Reading CSV..."):
            time.sleep(0.35)
            dataframe = load_csv(uploaded_file)
            profile = profile_dataset(dataframe)
            eda_report = generate_eda_report(dataframe)
    except CsvValidationError as error:
        st.error(str(error))
        return None

    st.success(f"Loaded `{uploaded_file.name}` successfully.")
    render_dataset_metrics(profile)
    return dataframe, profile, eda_report


def render_empty_dataset_state() -> None:
    st.info("Upload a CSV file to preview rows, columns, and dataset structure.")
    st.markdown(
        """
        <div class="dw-skeleton" style="width: 82%;"></div>
        <div class="dw-skeleton" style="width: 66%;"></div>
        <div class="dw-skeleton" style="width: 74%;"></div>
        """,
        unsafe_allow_html=True,
    )


def render_dataset_metrics(profile: DatasetProfile) -> None:
    st.markdown(
        f"""
        <div class="dw-metric-grid">
            <div class="dw-metric">
                <div class="dw-metric-label">Rows</div>
                <div class="dw-metric-value">{profile.row_count:,}</div>
            </div>
            <div class="dw-metric">
                <div class="dw-metric-label">Columns</div>
                <div class="dw-metric-value">{profile.column_count:,}</div>
            </div>
            <div class="dw-metric">
                <div class="dw-metric-label">Missing</div>
                <div class="dw-metric-value">{profile.missing_value_count:,}</div>
            </div>
            <div class="dw-metric">
                <div class="dw-metric-label">Duplicates</div>
                <div class="dw-metric-value">{profile.duplicate_row_count:,}</div>
            </div>
            <div class="dw-metric">
                <div class="dw-metric-label">Memory</div>
                <div class="dw-metric-value">{profile.memory_usage_display}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dataset_preview(dataframe: pd.DataFrame | None) -> None:
    st.markdown('<div class="dw-panel-title">Dataset Preview</div>', unsafe_allow_html=True)

    if dataframe is None:
        st.dataframe(pd.DataFrame(columns=["Upload", "a", "CSV", "to", "preview"]), use_container_width=True)
        return

    preview_rows = st.slider("Preview rows", min_value=5, max_value=50, value=10, step=5)
    st.dataframe(dataframe.head(preview_rows), use_container_width=True, hide_index=True)


def render_dataset_insights(profile: DatasetProfile | None) -> None:
    st.markdown('<div class="dw-panel-title">Dataset Statistics</div>', unsafe_allow_html=True)

    if profile is None:
        st.info("Upload a CSV file to view statistics, missing values, duplicates, column types, and memory usage.")
        return

    overview_tab, missing_tab, types_tab, statistics_tab = st.tabs(
        ["Overview", "Missing Values", "Column Types", "Statistics"]
    )

    with overview_tab:
        st.markdown(
            f"""
            <div class="dw-metric-grid">
                <div class="dw-metric">
                    <div class="dw-metric-label">Total Cells</div>
                    <div class="dw-metric-value">{profile.row_count * profile.column_count:,}</div>
                </div>
                <div class="dw-metric">
                    <div class="dw-metric-label">Duplicate Rows</div>
                    <div class="dw-metric-value">{profile.duplicate_row_count:,}</div>
                </div>
                <div class="dw-metric">
                    <div class="dw-metric-label">Memory Usage</div>
                    <div class="dw-metric-value">{profile.memory_usage_display}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with missing_tab:
        st.dataframe(profile.missing_values, use_container_width=True, hide_index=True)

    with types_tab:
        st.dataframe(profile.column_types, use_container_width=True, hide_index=True)

    with statistics_tab:
        st.dataframe(profile.statistics, use_container_width=True, hide_index=True)


def render_automated_eda(dataframe: pd.DataFrame | None, report: EdaReport | None) -> None:
    st.markdown('<div class="dw-panel-title">Automated EDA</div>', unsafe_allow_html=True)

    if dataframe is None or report is None:
        st.info("Upload a CSV file to generate automated exploratory data analysis.")
        return

    summary_tab, missing_tab, correlation_tab, distributions_tab, outliers_tab, quality_tab = st.tabs(
        ["Summary", "Missing Heatmap", "Correlation", "Distributions", "Outliers", "Quality"]
    )

    with summary_tab:
        st.dataframe(report.summary_statistics, use_container_width=True, hide_index=True)

    with missing_tab:
        missing_chart = create_missing_value_heatmap(dataframe)
        if missing_chart is None:
            st.info("No rows available for a missing value heatmap.")
        else:
            st.altair_chart(missing_chart, use_container_width=True)
            st.caption("Heatmap samples the first 250 rows for readability.")

    with correlation_tab:
        correlation_chart = create_correlation_heatmap(report.correlation_matrix)
        if correlation_chart is None:
            st.info("No numeric columns are available for correlation analysis.")
        else:
            st.altair_chart(correlation_chart, use_container_width=True)
            st.dataframe(report.correlation_matrix, use_container_width=True)

    with distributions_tab:
        if not report.numeric_columns:
            st.info("No numeric columns are available for histograms or boxplots.")
        else:
            selected_columns = st.multiselect(
                "Numeric columns",
                options=report.numeric_columns,
                default=report.numeric_columns[: min(3, len(report.numeric_columns))],
            )
            for column in selected_columns[:8]:
                histogram_column, boxplot_column = st.columns(2)
                with histogram_column:
                    st.altair_chart(create_histogram(dataframe, column), use_container_width=True)
                with boxplot_column:
                    st.altair_chart(create_boxplot(dataframe, column), use_container_width=True)

    with outliers_tab:
        if report.outliers.empty:
            st.info("No numeric columns are available for outlier detection.")
        else:
            st.dataframe(report.outliers, use_container_width=True, hide_index=True)

    with quality_tab:
        st.dataframe(report.duplicate_analysis, use_container_width=True, hide_index=True)
        st.write("")
        st.dataframe(report.data_quality_report, use_container_width=True, hide_index=True)


def render_suggested_questions(dataframe: pd.DataFrame | None) -> None:
    st.markdown('<div class="dw-panel-title">Suggested Questions</div>', unsafe_allow_html=True)

    suggestions = build_suggestions(dataframe)
    for index, question in enumerate(suggestions):
        if st.button(question, key=f"suggestion_{index}", icon=":material/auto_awesome:", use_container_width=True):
            queue_question(question)


def build_suggestions(dataframe: pd.DataFrame | None) -> list[str]:
    if dataframe is None or dataframe.empty:
        return DEFAULT_SUGGESTIONS

    first_columns = ", ".join(str(column) for column in dataframe.columns[:3])
    return [
        "Summarize this dataset",
        "Which columns have missing values?",
        f"What patterns appear in {first_columns}?",
        "Suggest the best charts for this data",
    ]


def render_chat_interface() -> None:
    st.markdown('<div class="dw-panel-title">Chat</div>', unsafe_allow_html=True)

    queued_question = consume_queued_question()
    if queued_question:
        process_prompt(queued_question)

    chat_container = st.container(height=420)
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                """
                <div class="dw-chat-box">
                    <div class="dw-muted">Start with a suggested question or type your own prompt below.</div>
                    <div class="dw-chip-row">
                        <span class="dw-chip">CSV-aware</span>
                        <span class="dw-chip">Analysis-ready</span>
                        <span class="dw-chip">Clean Architecture</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=get_avatar(message["role"])):
                st.write(message["content"])

    prompt = st.chat_input("Ask a question about your dataset")
    if prompt:
        process_prompt(prompt)
        st.rerun()


def process_prompt(prompt: str) -> None:
    with st.spinner("Preparing response..."):
        time.sleep(0.45)
        add_chat_exchange(prompt)


def get_avatar(role: str) -> Any:
    if role == "assistant":
        return ":material/neurology:"
    return ":material/person:"
