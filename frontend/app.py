import os

import streamlit as st


def main() -> None:
    backend_url = os.getenv("FRONTEND_BACKEND_URL", "http://localhost:8000")

    st.set_page_config(
        page_title="DataWhisperer AI",
        layout="wide",
    )

    st.title("DataWhisperer AI")
    st.caption("Frontend shell is ready. Application features are not implemented yet.")

    with st.sidebar:
        st.subheader("Configuration")
        st.text_input("Backend URL", value=backend_url, disabled=True)

    st.info("Project boilerplate is set up and ready for feature development.")


if __name__ == "__main__":
    main()
