# Data-Quant Source Governance

## Source Card

Every external market rule, vendor field, model API, or asset-class convention that can change a decision records:

```yaml
source_id: stable-id
source_kind: local_mirror | local_file | official_snapshot
publisher: exchange, regulator, vendor, library, or paper
jurisdiction_or_venue: scope
url_or_document: authoritative location
content_digest: sha256-tree-v1:<digest> | sha256:<digest>
effective_from: ISO date or null
effective_to: ISO date or null
accessed_at: explicit-timezone ISO timestamp
applies_to: fields, rules, formulas, or adapters
confidence: authoritative | corroborated | provisional
snapshot_path: required local normalized card for official_snapshot
notes: limitations and local-version checks
```

## Priority

1. Effective official exchange/regulator/vendor documentation.
2. Current official library/API documentation checked against the installed version.
3. Peer-reviewed or canonical method source.
4. Book-derived workflow guidance.
5. Generic defaults, which may guide research but never replace missing market evidence.

## Freshness

- Effective-dated rules remain valid for their historical interval even if superseded.
- A source without an effective date cannot silently govern historical simulation.
- Vendor changes, renamed fields, calendar changes, tax/fee changes, margin tiers, price limits, funding formulas, and venue priority rules require a new source-card revision.
- Unknown or stale source evidence is an `evidence_gap`; it caps the claim at research-only when the rule affects executability.

## Controlled Official Snapshots

`references/official-sources/` contains normalized, effective-dated cards for the five asset classes plus venue-product rule and vendor data-dictionary boundaries: U.S. futures position-limit rules, OCC options disclosure, FINRA TRACE, CLS FX settlement, CFTC crypto-leverage jurisdiction, venue product rules, and vendor data-dictionary evidence. A card binds publisher, HTTPS URL, access/effective times, retrieval status, optional retrieved-response SHA-256, explicitly bounded implementation claims, and limitations. The registry separately binds the card bytes with SHA-256; validation rejects tampering, metadata drift, non-authoritative classification, unsafe paths, missing effective dates, or claims that do not require a fresh check.

A `metadata_only` card is discovery evidence, not a copy of the source and not support for a numeric market-rule claim. A `retrieved` response digest proves which response was observed but does not preserve or license the complete upstream document. Runtime adapters must still ingest effective-dated rule values explicitly; these cards define evidence boundaries rather than hidden defaults. `--sync` refreshes local card digests only and never performs unattended network retrieval.

## Book-Derived Mirrors

The workspace authoring root is `${bundle_root}/../source/` (`../../source/` relative to this document). `source-registry.yaml` is authoritative for exact authoring paths, mirror targets, access timestamps, effective dates, and content digests. `scripts/sync_source_skills.py` verifies authoring trees when available and always verifies each self-contained frozen mirror against its governed digest; `--sync` refreshes mirrors and those local digests. Root contracts and runtime code are integration overlays and do not rewrite the original source summaries.
