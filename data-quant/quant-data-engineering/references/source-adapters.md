# Source Adapters, Credentials, And Lineage

## Built-In Sources

- CSV: core dependency path.
- Parquet/Arrow: `io` extra.
- DuckDB: `io` extra, read-only query.
- SQLite: standard-library connection plus pandas.
- Generic SQLAlchemy: `io` extra.

## Adapter Contract

An adapter must provide source identity, table type, schema version, source-to-canonical column mapping, read options, input fingerprint or query snapshot evidence, and credential environment-variable names. It returns an owned DataFrame for canonicalization; it does not leak a live database connection into an Artifact.

## Credential Rules

- Manifests name environment variables; they never contain secret values.
- Credential-bearing URI userinfo and sensitive query parameters are rejected before a run starts and are hidden from validation errors.
- A missing credential fails before a query runs.
- Artifacts store a safe source identifier and digest, never a password-bearing DSN.

## Vendor Semantics

Do not guess whether a field is raw, adjusted, announcement-time, revision-time, total-return, float-adjusted, or point-in-time. Record the official vendor/exchange definition and effective date. If unavailable, mark the field unverified and cap the result at research-only.

## Lineage

For each run preserve input URI or safe source ID, content/query digest, row count, contract version, column mapping, runtime version, manifest digest, and generated Artifact IDs.
