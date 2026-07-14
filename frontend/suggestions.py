from __future__ import annotations

import pandas as pd


DEFAULT_SUGGESTIONS = [
    "Summarize this dataset",
    "Which columns have missing values?",
    "What trends stand out?",
    "Suggest useful visualizations",
]


BUSINESS_CONTEXT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sales": ("sales", "revenue", "order", "deal", "amount", "price"),
    "customer": ("customer", "client", "user", "segment", "churn", "retention"),
    "finance": ("profit", "margin", "cost", "expense", "budget", "income"),
    "marketing": ("campaign", "channel", "click", "conversion", "lead", "impression"),
    "operations": ("inventory", "delivery", "shipment", "supplier", "stock", "warehouse"),
    "product": ("product", "sku", "category", "brand", "item"),
    "time": ("date", "month", "year", "week", "time", "period"),
}


def generate_suggested_questions(dataframe: pd.DataFrame | None, limit: int = 8) -> list[str]:
    if dataframe is None or dataframe.empty:
        return DEFAULT_SUGGESTIONS

    columns = [str(column) for column in dataframe.columns]
    numeric_columns = [str(column) for column in dataframe.select_dtypes(include="number").columns]
    datetime_columns = infer_datetime_columns(dataframe)
    categorical_columns = [
        str(column)
        for column in dataframe.columns
        if not pd.api.types.is_numeric_dtype(dataframe[column]) and str(column) not in datetime_columns
    ]
    missing_columns = [
        str(column)
        for column in dataframe.columns
        if int(dataframe[column].isna().sum()) > 0
    ]
    domains = infer_business_context(columns)

    suggestions: list[str] = []
    add_unique(suggestions, "Summarize this dataset and highlight the most important business takeaways")

    if numeric_columns:
        add_unique(suggestions, f"What are the key statistics for {format_column_list(numeric_columns[:3])}?")

    if categorical_columns and numeric_columns:
        add_unique(
            suggestions,
            f"How does {numeric_columns[0]} vary by {categorical_columns[0]}?",
        )

    if datetime_columns and numeric_columns:
        add_unique(
            suggestions,
            f"What trend does {numeric_columns[0]} show over {datetime_columns[0]}?",
        )

    if len(numeric_columns) >= 2:
        add_unique(
            suggestions,
            f"Which numeric columns are most correlated with {numeric_columns[0]}?",
        )

    if missing_columns:
        add_unique(
            suggestions,
            f"Which records have missing values in {format_column_list(missing_columns[:3])}, and how should they be handled?",
        )

    if categorical_columns:
        add_unique(
            suggestions,
            f"What are the top categories in {categorical_columns[0]}?",
        )

    add_domain_suggestions(suggestions, domains, numeric_columns, categorical_columns, datetime_columns)
    add_unique(suggestions, "What visualizations would best explain this dataset?")
    add_unique(suggestions, f"Are there anomalies or outliers in {format_column_list(numeric_columns[:3] or columns[:3])}?")

    return suggestions[:limit]


def infer_datetime_columns(dataframe: pd.DataFrame) -> list[str]:
    datetime_columns = [str(column) for column in dataframe.select_dtypes(include=["datetime", "datetimetz"]).columns]
    for column in dataframe.columns:
        column_name = str(column)
        lowered = column_name.lower()
        if column_name in datetime_columns:
            continue
        if any(token in lowered for token in ("date", "time", "month", "year", "period")):
            datetime_columns.append(column_name)
    return datetime_columns


def infer_business_context(columns: list[str]) -> list[str]:
    lowered_columns = " ".join(column.lower() for column in columns)
    return [
        domain
        for domain, keywords in BUSINESS_CONTEXT_KEYWORDS.items()
        if any(keyword in lowered_columns for keyword in keywords)
    ]


def add_domain_suggestions(
    suggestions: list[str],
    domains: list[str],
    numeric_columns: list[str],
    categorical_columns: list[str],
    datetime_columns: list[str],
) -> None:
    measure = numeric_columns[0] if numeric_columns else "the main metric"
    category = categorical_columns[0] if categorical_columns else "segment"
    time_column = datetime_columns[0] if datetime_columns else "time"

    if "sales" in domains:
        add_unique(suggestions, f"Which {category} contributes the most to {measure}?")
        add_unique(suggestions, f"What is driving changes in {measure} over {time_column}?")

    if "customer" in domains:
        add_unique(suggestions, f"Which customer segments show the strongest performance by {measure}?")

    if "finance" in domains:
        add_unique(suggestions, f"Where are profit, cost, or margin risks visible in this data?")

    if "marketing" in domains:
        add_unique(suggestions, f"Which channel or campaign appears to perform best?")

    if "operations" in domains:
        add_unique(suggestions, f"Where are operational delays, shortages, or efficiency issues visible?")

    if "product" in domains:
        add_unique(suggestions, f"Which products or categories stand out by {measure}?")


def add_unique(suggestions: list[str], question: str) -> None:
    if question and question not in suggestions:
        suggestions.append(question)


def format_column_list(columns: list[str]) -> str:
    if not columns:
        return "the available columns"
    if len(columns) == 1:
        return columns[0]
    if len(columns) == 2:
        return f"{columns[0]} and {columns[1]}"
    return f"{', '.join(columns[:-1])}, and {columns[-1]}"
