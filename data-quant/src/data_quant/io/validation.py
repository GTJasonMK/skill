"""Validation and canonicalization for tabular inputs."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import pandas as pd

from data_quant.contracts.artifacts import DiagnosticMessage
from data_quant.contracts.tables import TableContract


@dataclass
class CanonicalTable:
    frame: pd.DataFrame
    contract: TableContract
    warnings: list[DiagnosticMessage] = field(default_factory=list)
    evidence_gaps: list[DiagnosticMessage] = field(default_factory=list)


def parse_utc_timestamp(series: pd.Series, column: str) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=True, format="mixed")
    invalid = series.notna() & parsed.isna()
    if invalid.any():
        examples = series[invalid].astype(str).head(5).tolist()
        raise ValueError(f"Column {column!r} contains unparseable timestamps: {examples}")
    non_null = series[series.notna()]
    naive = non_null.map(lambda value: pd.Timestamp(value).tzinfo is None)
    if not naive.empty and naive.any():
        examples = non_null[naive].astype(str).head(5).tolist()
        raise ValueError(
            f"Column {column!r} contains timestamps without an explicit timezone: {examples}"
        )
    return parsed


def parse_date_or_utc_timestamp(series: pd.Series, column: str) -> pd.Series:
    """Parse an ISO calendar date or a timezone-aware timestamp, never a naive timestamp."""

    non_null = series[series.notna()]
    date_only = non_null.astype(str).str.fullmatch(r"\d{4}-\d{2}-\d{2}")
    if date_only.all():
        parsed = pd.to_datetime(series, errors="coerce", format="%Y-%m-%d")
        invalid = series.notna() & parsed.isna()
        if invalid.any():
            examples = series[invalid].astype(str).head(5).tolist()
            raise ValueError(f"Column {column!r} contains unparseable calendar dates: {examples}")
        return parsed
    if date_only.any():
        raise ValueError(f"Column {column!r} mixes calendar dates and timestamps.")
    return parse_utc_timestamp(series, column)


def _validate_numeric(series: pd.Series, column: str, nullable: bool) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    invalid = series.notna() & numeric.isna()
    if invalid.any():
        examples = series[invalid].astype(str).head(5).tolist()
        raise ValueError(f"Column {column!r} contains non-numeric values: {examples}")
    finite_mask = numeric.notna() & ~numeric.map(math.isfinite)
    if finite_mask.any():
        raise ValueError(f"Column {column!r} contains non-finite numeric values.")
    if not nullable and numeric.isna().any():
        raise ValueError(f"Column {column!r} is non-nullable but contains missing values.")
    return numeric


def canonicalize_table(
    frame: pd.DataFrame,
    contract: TableContract,
    *,
    column_mapping: dict[str, str] | None = None,
) -> CanonicalTable:
    df = frame.copy()
    if column_mapping:
        missing_source = [source for source in column_mapping if source not in df.columns]
        if missing_source:
            raise ValueError(f"Source columns not found for mapping: {missing_source}")
        targets = list(column_mapping.values())
        if len(targets) != len(set(targets)):
            raise ValueError("column_mapping contains duplicate target columns.")
        df = df.rename(columns=column_mapping)

    missing = [column for column in contract.required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for {contract.table_type}: {missing}")

    by_name = {item.name: item for item in contract.fields}
    for column, field_contract in by_name.items():
        if column not in df.columns:
            continue
        if field_contract.logical_type == "timestamp":
            df[column] = parse_utc_timestamp(df[column], column)
        elif field_contract.logical_type == "date":
            parsed = pd.to_datetime(df[column], errors="coerce")
            invalid = df[column].notna() & parsed.isna()
            if invalid.any():
                raise ValueError(f"Column {column!r} contains unparseable dates.")
            df[column] = parsed.dt.date
        elif field_contract.logical_type in {"number", "integer"}:
            numeric = _validate_numeric(df[column], column, field_contract.nullable)
            df[column] = numeric.astype("Int64") if field_contract.logical_type == "integer" else numeric
        elif field_contract.logical_type == "boolean":
            valid = df[column].dropna().isin([True, False])
            if not valid.all():
                raise ValueError(f"Column {column!r} must contain booleans after mapping.")
        elif field_contract.logical_type == "string":
            if not field_contract.nullable and df[column].isna().any():
                raise ValueError(f"Column {column!r} is non-nullable but contains missing values.")
            df[column] = df[column].astype("string")

    if contract.primary_key:
        duplicate_mask = df.duplicated(contract.primary_key, keep=False)
        if duplicate_mask.any():
            examples = df.loc[duplicate_mask, contract.primary_key].head(5).to_dict("records")
            raise ValueError(f"Duplicate primary keys for {contract.table_type}: {examples}")
        if df[contract.primary_key].isna().any().any():
            raise ValueError(f"Primary key columns cannot contain missing values: {contract.primary_key}")

    return CanonicalTable(frame=df, contract=contract)
