from __future__ import annotations

from dataclasses import dataclass

import altair as alt
import pandas as pd


MAX_CHART_COLUMNS = 8


@dataclass(frozen=True)
class EdaReport:
    summary_statistics: pd.DataFrame
    missing_value_heatmap: pd.DataFrame
    correlation_matrix: pd.DataFrame
    outliers: pd.DataFrame
    duplicate_analysis: pd.DataFrame
    data_quality_report: pd.DataFrame
    numeric_columns: list[str]


def generate_eda_report(dataframe: pd.DataFrame) -> EdaReport:
    numeric_columns = [str(column) for column in dataframe.select_dtypes(include="number").columns]

    return EdaReport(
        summary_statistics=build_summary_statistics(dataframe),
        missing_value_heatmap=build_missing_value_heatmap(dataframe),
        correlation_matrix=build_correlation_matrix(dataframe),
        outliers=detect_outliers(dataframe),
        duplicate_analysis=analyze_duplicates(dataframe),
        data_quality_report=build_data_quality_report(dataframe),
        numeric_columns=numeric_columns,
    )


def build_summary_statistics(dataframe: pd.DataFrame) -> pd.DataFrame:
    summary = dataframe.describe(include="all").transpose()
    summary.index.name = "column"
    return summary.reset_index()


def build_missing_value_heatmap(dataframe: pd.DataFrame) -> pd.DataFrame:
    missing_map = dataframe.isna().astype(int).copy()
    missing_map.insert(0, "row", range(1, len(missing_map) + 1))
    return missing_map


def build_correlation_matrix(dataframe: pd.DataFrame) -> pd.DataFrame:
    numeric_dataframe = dataframe.select_dtypes(include="number")
    if numeric_dataframe.empty:
        return pd.DataFrame()
    return numeric_dataframe.corr(numeric_only=True).round(3)


def detect_outliers(dataframe: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    numeric_dataframe = dataframe.select_dtypes(include="number")

    for column in numeric_dataframe.columns:
        series = numeric_dataframe[column].dropna()
        if series.empty:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outlier_count = int(((series < lower_bound) | (series > upper_bound)).sum())

        rows.append(
            {
                "column": str(column),
                "q1": round(q1, 4),
                "q3": round(q3, 4),
                "iqr": round(float(iqr), 4),
                "lower_bound": round(float(lower_bound), 4),
                "upper_bound": round(float(upper_bound), 4),
                "outliers": outlier_count,
                "outlier_percent": round(outlier_count / len(dataframe) * 100, 2),
            }
        )

    return pd.DataFrame(rows).sort_values("outliers", ascending=False, ignore_index=True) if rows else pd.DataFrame()


def analyze_duplicates(dataframe: pd.DataFrame) -> pd.DataFrame:
    duplicate_mask = dataframe.duplicated(keep=False)
    duplicate_row_count = int(dataframe.duplicated().sum())
    duplicate_group_count = int(dataframe.loc[duplicate_mask].drop_duplicates().shape[0]) if duplicate_mask.any() else 0

    return pd.DataFrame(
        [
            {"metric": "Total rows", "value": len(dataframe)},
            {"metric": "Duplicate rows", "value": duplicate_row_count},
            {"metric": "Duplicate row groups", "value": duplicate_group_count},
            {"metric": "Duplicate percent", "value": round(duplicate_row_count / len(dataframe) * 100, 2)},
        ]
    )


def build_data_quality_report(dataframe: pd.DataFrame) -> pd.DataFrame:
    missing_counts = dataframe.isna().sum()
    duplicate_count = int(dataframe.duplicated().sum())
    outliers = detect_outliers(dataframe)
    outlier_lookup = (
        outliers.set_index("column")["outliers"].to_dict()
        if not outliers.empty and "column" in outliers.columns
        else {}
    )

    rows = []
    for column in dataframe.columns:
        column_name = str(column)
        missing_count = int(missing_counts[column])
        unique_count = int(dataframe[column].nunique(dropna=True))
        quality_score = calculate_column_quality_score(
            row_count=len(dataframe),
            missing_count=missing_count,
            duplicate_count=duplicate_count,
            outlier_count=int(outlier_lookup.get(column_name, 0)),
        )

        rows.append(
            {
                "column": column_name,
                "type": str(dataframe[column].dtype),
                "missing_values": missing_count,
                "missing_percent": round(missing_count / len(dataframe) * 100, 2),
                "unique_values": unique_count,
                "outliers": int(outlier_lookup.get(column_name, 0)),
                "quality_score": quality_score,
            }
        )

    return pd.DataFrame(rows).sort_values("quality_score", ascending=True, ignore_index=True)


def calculate_column_quality_score(
    row_count: int,
    missing_count: int,
    duplicate_count: int,
    outlier_count: int,
) -> float:
    if row_count == 0:
        return 0.0

    missing_penalty = missing_count / row_count * 45
    duplicate_penalty = duplicate_count / row_count * 20
    outlier_penalty = outlier_count / row_count * 20
    return round(max(0.0, 100 - missing_penalty - duplicate_penalty - outlier_penalty), 2)


def create_missing_value_heatmap(dataframe: pd.DataFrame) -> alt.Chart | None:
    if dataframe.empty:
        return None

    sample = dataframe.head(250).isna().reset_index(names="row")
    long_form = sample.melt(id_vars="row", var_name="column", value_name="missing")
    long_form["status"] = long_form["missing"].map({True: "Missing", False: "Present"})

    return (
        alt.Chart(long_form)
        .mark_rect()
        .encode(
            x=alt.X("column:N", title="Column", sort=None),
            y=alt.Y("row:O", title="Row"),
            color=alt.Color(
                "status:N",
                title="Status",
                scale=alt.Scale(domain=["Present", "Missing"], range=["#1e293b", "#ef4444"]),
            ),
            tooltip=["row:O", "column:N", "status:N"],
        )
        .properties(height=260)
    )


def create_correlation_heatmap(correlation_matrix: pd.DataFrame) -> alt.Chart | None:
    if correlation_matrix.empty:
        return None

    correlation_long = correlation_matrix.reset_index(names="feature_x").melt(
        id_vars="feature_x",
        var_name="feature_y",
        value_name="correlation",
    )

    return (
        alt.Chart(correlation_long)
        .mark_rect()
        .encode(
            x=alt.X("feature_x:N", title=""),
            y=alt.Y("feature_y:N", title=""),
            color=alt.Color(
                "correlation:Q",
                scale=alt.Scale(scheme="blueorange", domain=[-1, 1]),
                title="Correlation",
            ),
            tooltip=["feature_x:N", "feature_y:N", alt.Tooltip("correlation:Q", format=".3f")],
        )
        .properties(height=320)
    )


def create_histogram(dataframe: pd.DataFrame, column: str) -> alt.Chart:
    return (
        alt.Chart(dataframe[[column]].dropna())
        .mark_bar(color="#60a5fa", opacity=0.86)
        .encode(
            x=alt.X(f"{column}:Q", bin=alt.Bin(maxbins=35), title=column),
            y=alt.Y("count():Q", title="Records"),
            tooltip=[alt.Tooltip("count():Q", title="Records")],
        )
        .properties(height=220)
    )


def create_boxplot(dataframe: pd.DataFrame, column: str) -> alt.Chart:
    return (
        alt.Chart(dataframe[[column]].dropna())
        .mark_boxplot(color="#22c55e", extent=1.5)
        .encode(
            y=alt.Y(f"{column}:Q", title=column),
            tooltip=[alt.Tooltip(f"{column}:Q", title=column)],
        )
        .properties(height=220)
    )
