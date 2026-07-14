import streamlit as st

from frontend.components import (
    render_chat_interface,
    render_automated_eda,
    render_dataset_insights,
    render_dataset_preview,
    render_header,
    render_sidebar,
    render_suggested_questions,
    render_upload_panel,
)
from frontend.state import initialize_session_state
from frontend.styles import apply_dark_theme


def main() -> None:
    st.set_page_config(
        page_title="DataWhisperer AI",
        page_icon=":material/query_stats:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_dark_theme()
    initialize_session_state()
    render_sidebar()
    render_header()

    st.write("")
    left_column, right_column = st.columns([1.05, 1.45], gap="large")

    with left_column:
        upload_result = render_upload_panel()
        dataframe = upload_result[0] if upload_result else None
        profile = upload_result[1] if upload_result else None
        eda_report = upload_result[2] if upload_result else None
        st.write("")
        render_suggested_questions(dataframe)

    with right_column:
        render_chat_interface()
        st.write("")
        render_dataset_preview(dataframe)
        st.write("")
        render_dataset_insights(profile)
        st.write("")
        render_automated_eda(dataframe, eda_report)


if __name__ == "__main__":
    main()
