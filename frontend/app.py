import streamlit as st

from frontend.components import (
    render_chat_interface,
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
        dataframe = render_upload_panel()
        st.write("")
        render_suggested_questions(dataframe)

    with right_column:
        render_chat_interface()
        st.write("")
        render_dataset_preview(dataframe)


if __name__ == "__main__":
    main()
