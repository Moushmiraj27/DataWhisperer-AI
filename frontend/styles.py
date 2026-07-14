import streamlit as st


def apply_dark_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
        }

        .stApp {
            background:
                radial-gradient(circle at 20% 0%, rgba(47, 95, 255, 0.16), transparent 34rem),
                linear-gradient(135deg, #0c111d 0%, #111827 52%, #0a0f1a 100%);
            color: #edf2f7;
        }

        [data-testid="stSidebar"] {
            background: #0b1220;
            border-right: 1px solid rgba(148, 163, 184, 0.16);
        }

        [data-testid="stSidebar"] * {
            color: #e5e7eb;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        h1, h2, h3 {
            letter-spacing: 0;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        .dw-hero {
            border: 1px solid rgba(148, 163, 184, 0.18);
            background: rgba(15, 23, 42, 0.78);
            border-radius: 8px;
            padding: 1.25rem 1.35rem;
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
        }

        .dw-kicker {
            color: #8fb4ff;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }

        .dw-muted {
            color: #94a3b8;
            font-size: 0.95rem;
        }

        .dw-panel {
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.72);
            border-radius: 8px;
            padding: 1rem;
            min-height: 100%;
        }

        .dw-panel-title {
            color: #f8fafc;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }

        .dw-metric-grid {
            display: grid;
            gap: 0.75rem;
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .dw-metric {
            border: 1px solid rgba(148, 163, 184, 0.14);
            background: rgba(2, 6, 23, 0.42);
            border-radius: 8px;
            padding: 0.85rem;
        }

        .dw-metric-label {
            color: #94a3b8;
            font-size: 0.78rem;
        }

        .dw-metric-value {
            color: #f8fafc;
            font-size: 1.35rem;
            font-weight: 800;
            line-height: 1.2;
        }

        .dw-chat-box {
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(2, 6, 23, 0.28);
            border-radius: 8px;
            padding: 0.8rem;
        }

        .dw-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.6rem;
        }

        .dw-chip {
            border: 1px solid rgba(96, 165, 250, 0.28);
            background: rgba(37, 99, 235, 0.12);
            border-radius: 999px;
            color: #bfdbfe;
            display: inline-flex;
            font-size: 0.8rem;
            padding: 0.25rem 0.6rem;
        }

        .dw-skeleton {
            height: 0.75rem;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(148, 163, 184, 0.12), rgba(148, 163, 184, 0.3), rgba(148, 163, 184, 0.12));
            background-size: 220% 100%;
            animation: dw-shimmer 1.4s ease-in-out infinite;
            margin: 0.55rem 0;
        }

        @keyframes dw-shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        [data-testid="stFileUploader"] {
            border: 1px dashed rgba(96, 165, 250, 0.4);
            background: rgba(2, 6, 23, 0.28);
            border-radius: 8px;
            padding: 0.7rem;
        }

        .stChatMessage {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.12);
            border-radius: 8px;
        }

        .stDataFrame {
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 8px;
            overflow: hidden;
        }

        @media (max-width: 900px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .dw-metric-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
