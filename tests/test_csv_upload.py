from __future__ import annotations

from dataclasses import dataclass

import pytest

from io import BytesIO

from frontend.csv_upload import CsvValidationError, format_bytes, load_csv, load_csv_from_buffer, profile_dataset, validate_csv_file


@dataclass
class FakeUpload:
    name: str
    content: bytes

    @property
    def size(self) -> int:
        return len(self.content)

    def getvalue(self) -> bytes:
        return self.content


def test_load_csv_validates_and_loads_dataframe() -> None:
    upload = FakeUpload(
        name="customers.csv",
        content=b"id,name,score\n1,Ada,10\n2,Grace,\n2,Grace,\n",
    )

    dataframe = load_csv(upload)
    profile = profile_dataset(dataframe)

    assert profile.row_count == 3
    assert profile.column_count == 3
    assert profile.missing_value_count == 2
    assert profile.duplicate_row_count == 1
    assert profile.memory_usage_bytes > 0
    assert set(profile.column_types["column"]) == {"id", "name", "score"}


def test_load_csv_rejects_non_csv_file() -> None:
    upload = FakeUpload(name="customers.xlsx", content=b"id,name\n1,Ada\n")

    with pytest.raises(CsvValidationError, match="Only .csv files"):
        load_csv(upload)


def test_validate_csv_file_rejects_empty_upload() -> None:
    upload = FakeUpload(name="empty.csv", content=b"")

    with pytest.raises(CsvValidationError, match="empty"):
        validate_csv_file(upload)


def test_validate_csv_file_rejects_oversized_upload() -> None:
    upload = FakeUpload(name="large.csv", content=b"x" * (1024 * 1024 + 1))

    with pytest.raises(CsvValidationError, match="1 MB or smaller"):
        validate_csv_file(upload, max_size_mb=1)


def test_load_csv_from_buffer_uses_same_dataframe_validation() -> None:
    dataframe = load_csv_from_buffer(BytesIO(b"region,sales\nWest,100\nEast,150\n"))

    assert list(dataframe.columns) == ["region", "sales"]
    assert dataframe["sales"].sum() == 250


def test_load_csv_rejects_files_without_data_rows() -> None:
    upload = FakeUpload(name="header_only.csv", content=b"id,name\n")

    with pytest.raises(CsvValidationError, match="contains no rows"):
        load_csv(upload)


def test_format_bytes_uses_readable_units() -> None:
    assert format_bytes(512) == "512 B"
    assert format_bytes(2048) == "2.0 KB"
