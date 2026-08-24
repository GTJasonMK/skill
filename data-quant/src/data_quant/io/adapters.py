"""Input adapters for canonical Data-Quant tables."""

from __future__ import annotations

import importlib.util
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import pandas as pd

from data_quant.contracts.manifest import DataSourceSpec
from data_quant.contracts.tables import get_table_contract
from data_quant.io.validation import CanonicalTable, canonicalize_table


def _require_env(names: list[str]) -> None:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise ValueError(f"Missing required credential environment variables: {missing}")


def _require_module(module: str, extra: str) -> None:
    if importlib.util.find_spec(module) is None:
        raise RuntimeError(f"Input format requires {module!r}. Install with: pip install -e '.[{extra}]'")


def read_source(spec: DataSourceSpec) -> CanonicalTable:
    _require_env(spec.credential_env)
    options: dict[str, Any] = dict(spec.options)

    if spec.format == "csv":
        frame = pd.read_csv(Path(spec.uri), **options)
    elif spec.format == "parquet":
        _require_module("pyarrow", "io")
        frame = pd.read_parquet(spec.uri, **options)
    elif spec.format == "duckdb":
        _require_module("duckdb", "io")
        import duckdb

        query = options.pop("query", None)
        if not query:
            raise ValueError("DuckDB sources require options.query.")
        if options:
            raise ValueError(f"Unknown DuckDB source options: {sorted(options)}")
        with duckdb.connect(spec.uri, read_only=True) as connection:
            frame = connection.execute(query).fetchdf()
    elif spec.format == "sqlite":
        query = options.pop("query", None)
        if not query:
            raise ValueError("SQLite sources require options.query.")
        if options:
            raise ValueError(f"Unknown SQLite source options: {sorted(options)}")
        with closing(sqlite3.connect(spec.uri)) as connection:
            frame = pd.read_sql_query(query, connection)
    elif spec.format == "sql":
        _require_module("sqlalchemy", "io")
        from sqlalchemy import create_engine

        query = options.pop("query", None)
        if not query:
            raise ValueError("SQL sources require options.query.")
        engine = create_engine(spec.uri)
        try:
            frame = pd.read_sql_query(query, engine, **options)
        finally:
            engine.dispose()
    else:  # pragma: no cover - protected by Pydantic Literal
        raise ValueError(f"Unsupported source format: {spec.format}")

    contract = get_table_contract(spec.table_type)
    if contract.schema_version != spec.contract_version:
        raise ValueError(
            f"Table contract version mismatch for {spec.id}: requested {spec.contract_version}, "
            f"available {contract.schema_version}."
        )
    return canonicalize_table(frame, contract, column_mapping=spec.column_mapping)
