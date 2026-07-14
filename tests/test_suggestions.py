import pandas as pd

from frontend.suggestions import generate_suggested_questions, infer_business_context


def test_generate_suggested_questions_uses_column_names_and_types() -> None:
    dataframe = pd.DataFrame(
        {
            "order_date": ["2026-01-01", "2026-01-02"],
            "region": ["West", "East"],
            "sales": [100, 150],
            "profit": [20, None],
        }
    )

    suggestions = generate_suggested_questions(dataframe)

    assert any("sales" in suggestion and "region" in suggestion for suggestion in suggestions)
    assert any("order_date" in suggestion for suggestion in suggestions)
    assert any("profit" in suggestion and "missing values" in suggestion for suggestion in suggestions)
    assert any("business takeaways" in suggestion for suggestion in suggestions)


def test_generate_suggested_questions_uses_business_context() -> None:
    dataframe = pd.DataFrame(
        {
            "customer_segment": ["Enterprise", "SMB"],
            "campaign_channel": ["Email", "Search"],
            "conversion_rate": [0.12, 0.08],
        }
    )

    suggestions = generate_suggested_questions(dataframe)

    assert "customer" in infer_business_context(list(dataframe.columns))
    assert "marketing" in infer_business_context(list(dataframe.columns))
    assert any("customer segments" in suggestion for suggestion in suggestions)
    assert any("channel or campaign" in suggestion for suggestion in suggestions)


def test_generate_suggested_questions_returns_defaults_without_data() -> None:
    assert generate_suggested_questions(None)[0] == "Summarize this dataset"
