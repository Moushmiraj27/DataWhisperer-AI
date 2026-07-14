from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO, Protocol

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


MAX_UPLOAD_SIZE_MB = 100


class UploadedCsv(Protocol):
    name: str
    size: int

    def getvalue(self) -> bytes:
        ...


class CsvValidationError(ValueError):
    """Raised when an uploaded CSV file cannot be accepted."""


@dataclass(frozen=True)
class DatasetProfile:
    row_count: int
    column_count: int
    missing_value_count: int
    duplicate_row_count: int
    memory_usage_bytes: int
    memory_usage_display: str
    column_types: pd.DataFrame
    missing_values: pd.DataFrame
    statistics: pd.DataFrame


def validate_csv_file(uploaded_file: UploadedCsv | None, max_size_mb: int = MAX_UPLOAD_SIZE_MB) -> None:
    if uploaded_file is None:
        raise CsvValidationError("Please upload a CSV file.")

    filename = uploaded_file.name.strip()
    if not filename.lower().endswith(".csv"):
        raise CsvValidationError("Only .csv files are supported.")

    if uploaded_file.size <= 0:
        raise CsvValidationError("The uploaded CSV file is empty.")

    max_size_bytes = max_size_mb * 1024 * 1024
    if uploaded_file.size > max_size_bytes:
        raise CsvValidationError(f"CSV file must be {max_size_mb} MB or smaller.")


def load_csv(uploaded_file: UploadedCsv) -> pd.DataFrame:
    validate_csv_file(uploaded_file)

    try:
        dataframe = pd.read_csv(BytesIO(uploaded_file.getvalue()))
    except EmptyDataError as error:
        raise CsvValidationError("The CSV file does not contain any readable data.") from error
    except ParserError as error:
        raise CsvValidationError("The CSV file could not be parsed. Check the delimiter and row format.") from error
    except UnicodeDecodeError as error:
        raise CsvValidationError("The CSV file encoding is not supported. Please upload a UTF-8 CSV.") from error

    validate_dataframe(dataframe)
    return dataframe


def load_csv_from_buffer(buffer: BinaryIO) -> pd.DataFrame:
    try:
        dataframe = pd.read_csv(buffer)
    except EmptyDataError as error:
        raise CsvValidationError("The CSV file does not contain any readable data.") from error
    except ParserError as error:
        raise CsvValidationError("The CSV file could not be parsed. Check the delimiter and row format.") from error
    except UnicodeDecodeError as error:
        raise CsvValidationError("The CSV file encoding is not supported. Please upload a UTF-8 CSV.") from error

    validate_dataframe(dataframe)
    return dataframe


def validate_dataframe(dataframe: pd.DataFrame) -> None:
    if dataframe.empty:
        raise CsvValidationError("The CSV file loaded successfully but contains no rows.")

    if len(dataframe.columns) == 0:
        raise CsvValidationError("The CSV file does not contain any columns.")

    unnamed_columns = [column for column in dataframe.columns if str(column).startswith("Unnamed:")]
    if len(unnamed_columns) == len(dataframe.columns):
        raise CsvValidationError("The CSV file appears to be missing a header row.")


def profile_dataset(dataframe: pd.DataFrame) -> DatasetProfile:
    missing_values = build_missing_values_table(dataframe)
    column_types = build_column_types_table(dataframe)
    statistics = build_statistics_table(dataframe)
    memory_usage_bytes = int(dataframe.memory_usage(deep=True).sum())

    return DatasetProfile(
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        missing_value_count=int(dataframe.isna().sum().sum()),
        duplicate_row_count=int(dataframe.duplicated().sum()),
        memory_usage_bytes=memory_usage_bytes,
        memory_usage_display=format_bytes(memory_usage_bytes),
        column_types=column_types,
        missing_values=missing_values,
        statistics=statistics,
    )


def build_missing_values_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    missing_counts = dataframe.isna().sum()
    missing_percentages = (missing_counts / len(dataframe) * 100).round(2)

    return pd.DataFrame(
        {
            "column": missing_counts.index.astype(str),
            "missing_values": missing_counts.astype(int).values,
            "missing_percent": missing_percentages.values,
        }
    ).sort_values(["missing_values", "column"], ascending=[False, True], ignore_index=True)


def build_column_types_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    unique_counts = dataframe.nunique(dropna=True)
    non_null_counts = dataframe.notna().sum()

    return pd.DataFrame(
        {
            "column": [str(column) for column in dataframe.columns],
            "type": [str(dtype) for dtype in dataframe.dtypes],
            "non_null": non_null_counts.astype(int).values,
            "unique_values": unique_counts.astype(int).values,
        }
    )


def build_statistics_table(dataframe: pd.DataFrame) -> pd.DataFrame:
    statistics = dataframe.describe(include="all").transpose()
    statistics.index.name = "column"
    return statistics.reset_index()


def format_bytes(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024

    return f"{size_bytes} B"
