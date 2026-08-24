from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import duckdb
import pandas as pd

from data_quant.contracts.manifest import DataSourceSpec
from data_quant.io import read_source


def bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": ["2024-01-02T07:00:00Z", "2024-01-03T07:00:00Z"],
            "asset_id": ["A", "A"],
            "close": [10.0, 10.5],
            "currency": ["CNY", "CNY"],
            "adjustment_state": ["raw", "raw"],
        }
    )


def spec(uri: str, source_format: str, options: dict | None = None) -> DataSourceSpec:
    return DataSourceSpec.model_validate(
        {
            "id": source_format,
            "uri": uri,
            "format": source_format,
            "table_type": "market_bars",
            "options": options or {},
        }
    )


def assert_bars(source: DataSourceSpec) -> None:
    table = read_source(source)
    assert table.contract.table_type == "market_bars"
    assert len(table.frame) == 2
    assert str(table.frame["timestamp"].dtype).endswith("UTC]")


def test_csv_and_parquet_adapters(tmp_path: Path) -> None:
    csv_path = tmp_path / "bars.csv"
    parquet_path = tmp_path / "bars.parquet"
    bars().to_csv(csv_path, index=False)
    bars().to_parquet(parquet_path, index=False)
    assert_bars(spec(str(csv_path), "csv"))
    assert_bars(spec(str(parquet_path), "parquet"))


def test_sqlite_and_sqlalchemy_adapters(tmp_path: Path) -> None:
    database = tmp_path / "bars.sqlite"
    with closing(sqlite3.connect(database)) as connection:
        bars().to_sql("bars", connection, index=False)
    assert_bars(spec(str(database), "sqlite", {"query": "SELECT * FROM bars"}))
    assert_bars(spec(f"sqlite:///{database}", "sql", {"query": "SELECT * FROM bars"}))


def test_duckdb_adapter(tmp_path: Path) -> None:
    database = tmp_path / "bars.duckdb"
    with duckdb.connect(str(database)) as connection:
        connection.register("bars_frame", bars())
        connection.execute("CREATE TABLE bars AS SELECT * FROM bars_frame")
    assert_bars(spec(str(database), "duckdb", {"query": "SELECT * FROM bars"}))
