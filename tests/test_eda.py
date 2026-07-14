from __future__ import annotations

import pandas as pd

from frontend.eda import generate_eda_report


def test_generate_eda_report_builds_expected_tables() -> None:
    dataframe = pd.DataFrame(
        {
            "age": [21, 22, 23, 24, 1000, 22],
            "score": [80, 81, None, 83, 84, 81],
            "city": ["Pune", "Delhi", "Pune", None, "Mumbai", "Delhi"],
        }
    )

    report = generate_eda_report(dataframe)

    assert not report.summary_statistics.empty
    assert report.missing_value_heatmap.shape == (6, 4)
    assert set(report.correlation_matrix.columns) == {"age", "score"}
    assert int(report.outliers.loc[report.outliers["column"] == "age", "outliers"].iloc[0]) == 1
    assert report.duplicate_analysis.loc[0, "metric"] == "Total rows"
    assert set(report.data_quality_report["column"]) == {"age", "score", "city"}


def test_generate_eda_report_handles_non_numeric_data() -> None:
    dataframe = pd.DataFrame({"name": ["Ada", "Grace", "Ada"], "team": ["A", "B", "A"]})

    report = generate_eda_report(dataframe)

    assert report.correlation_matrix.empty
    assert report.outliers.empty
    assert report.numeric_columns == []
    assert int(report.duplicate_analysis.loc[1, "value"]) == 1
