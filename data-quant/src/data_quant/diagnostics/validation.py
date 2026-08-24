"""Native time-aware validation diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data_quant import __version__
from data_quant.contracts.artifacts import (
    ArtifactEnvelope,
    DiagnosticMessage,
    ProducerReference,
)
from data_quant.contracts.parameters import (
    CorporateActionAdjustmentParameters,
    PurgedWalkForwardParameters,
)
from data_quant.io.validation import parse_utc_timestamp
from data_quant.registry import register_diagnostic
from data_quant.validation import purged_walk_forward_split, split_artifact


@register_diagnostic(
    "purged-walk-forward",
    "validation_split",
    required_table_types=("return_labels",),
    manifest_stage="validation",
    parameter_model=PurgedWalkForwardParameters,
    description="Build walk-forward folds that purge overlapping labels and apply an embargo.",
)
def purged_walk_forward_artifact(
    labels: pd.DataFrame,
    *,
    train_periods: int,
    test_periods: int,
    step_periods: int | None = None,
    embargo: str = "0s",
    expanding: bool = False,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    embargo_delta = pd.Timedelta(embargo)
    folds = purged_walk_forward_split(
        labels,
        observation_time_col="decision_at",
        label_end_time_col="return_end",
        train_periods=train_periods,
        test_periods=test_periods,
        step_periods=step_periods,
        embargo=embargo_delta,
        expanding=expanding,
    )
    return split_artifact(
        folds,
        method="purged-walk-forward",
        parameters={
            "observation_time_col": "decision_at",
            "label_end_time_col": "return_end",
            "train_periods": train_periods,
            "test_periods": test_periods,
            "step_periods": step_periods,
            "embargo": str(embargo_delta),
            "expanding": expanding,
        },
        run_id=run_id,
    )


@register_diagnostic(
    "corporate-action-adjustment",
    "corporate_action_adjustment",
    required_table_types=("market_bars", "corporate_actions"),
    manifest_stage="validation",
    parameter_model=CorporateActionAdjustmentParameters,
    description="Reconcile split and cash-dividend economics to total-return-adjusted bars.",
)
def corporate_action_adjustment_artifact(
    bars: pd.DataFrame,
    corporate_actions: pd.DataFrame,
    *,
    evaluated_at: str,
    max_bar_gap: str = "7D",
    maximum_return_error: float = 1e-8,
    minimum_actions: int = 1,
    dividend_withholding_rate: float = 0.0,
    allow_late_revisions: bool = True,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    maximum_gap = pd.Timedelta(max_bar_gap)
    if (
        maximum_gap <= pd.Timedelta(0)
        or maximum_return_error < 0
        or minimum_actions < 1
        or not 0 <= dividend_withholding_rate <= 1
    ):
        raise ValueError("Corporate-action adjustment limits are invalid.")
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    action_frame = corporate_actions.copy()
    for column in ("announced_at", "available_at", "effective_at"):
        action_frame[column] = parse_utc_timestamp(action_frame[column], column)
    action_frame["value"] = pd.to_numeric(action_frame["value"], errors="coerce")
    action_frame = action_frame[
        (action_frame["available_at"] <= evaluated)
        & (action_frame["effective_at"] <= evaluated)
    ].copy()
    if not np.isfinite(action_frame["value"].to_numpy(dtype=float)).all():
        raise ValueError("Corporate-action values selected for reconciliation must be finite.")
    blockers: list[DiagnosticMessage] = []
    selected_rows = []
    for (asset_id_value, action_id_value), versions in action_frame.groupby(
        ["asset_id", "action_id"], sort=True
    ):
        ordered = versions.sort_values("available_at")
        first = ordered.iloc[0]
        last = ordered.iloc[-1]
        late = False
        for version in ordered.iloc[1:].to_dict("records"):
            if pd.Timestamp(version["available_at"]) > pd.Timestamp(
                first["effective_at"]
            ) and float(version["value"]) != float(first["value"]):
                late = True
                break
        if late and not allow_late_revisions:
            blockers.append(
                DiagnosticMessage(
                    code="corporate_action_late_revision",
                    message=(
                        "A vendor revision after the effective timestamp changed the action value."
                    ),
                    severity="blocker",
                    context={
                        "asset_id": str(asset_id_value),
                        "action_id": str(action_id_value),
                        "first_available_at": pd.Timestamp(first["available_at"]).isoformat(),
                        "revised_available_at": pd.Timestamp(last["available_at"]).isoformat(),
                    },
                )
            )
        last_row = last.to_dict()
        last_row["revision_count"] = int(len(ordered))
        last_row["late_revision"] = late
        selected_rows.append(last_row)
    action_frame = pd.DataFrame(selected_rows) if selected_rows else action_frame.iloc[0:0].copy()
    bar_frame = bars.copy()
    bar_frame["timestamp"] = parse_utc_timestamp(bar_frame["timestamp"], "timestamp")
    bar_frame["close"] = pd.to_numeric(bar_frame["close"], errors="coerce")
    bar_frame = bar_frame[bar_frame["timestamp"] <= evaluated].copy()
    if (
        not np.isfinite(bar_frame["close"].to_numpy(dtype=float)).all()
        or bar_frame["close"].le(0).any()
    ):
        raise ValueError("Corporate-action reconciliation requires finite positive closes.")
    raw = bar_frame[bar_frame["adjustment_state"].astype(str) == "raw"].copy()
    adjusted = bar_frame[
        bar_frame["adjustment_state"].astype(str) == "total_return_adjusted"
    ].copy()
    details = []
    return_errors: list[float] = []
    reconciled_count = 0
    grouped_actions = action_frame.groupby(["asset_id", "effective_at"], sort=True)
    for (asset_id_value, effective_at_value), event_actions in grouped_actions:
        asset_id = str(asset_id_value)
        effective_at = pd.Timestamp(effective_at_value)
        base_detail: dict[str, object] = {
            "asset_id": asset_id,
            "effective_at": effective_at.isoformat(),
            "action_ids": sorted(event_actions["action_id"].astype(str).tolist()),
            "action_types": sorted(event_actions["action_type"].astype(str).tolist()),
        }
        action_types = [str(row["action_type"]) for row in event_actions.to_dict("records")]
        unsupported = sorted(
            {
                action_type
                for action_type in action_types
                if action_type
                not in {
                    "split",
                    "cash_dividend",
                    "spin_off",
                    "rights",
                    "merger",
                    "conversion",
                    "stock_merger",
                    "fractional_cash_in_lieu",
                }
            }
        )
        if unsupported:
            blockers.append(
                DiagnosticMessage(
                    code="corporate_action_type_unsupported",
                    message=f"Corporate action type {unsupported[0]!r} is not reconciled.",
                    severity="blocker",
                    context={**base_detail, "unsupported_types": unsupported},
                )
            )
            details.append({**base_detail, "status": "unsupported_type"})
            continue
        asset_raw = raw[raw["asset_id"].astype(str) == asset_id]
        before = asset_raw[asset_raw["timestamp"] < effective_at].sort_values("timestamp")
        after = asset_raw[asset_raw["timestamp"] >= effective_at].sort_values("timestamp")
        if before.empty or after.empty:
            blockers.append(
                DiagnosticMessage(
                    code="corporate_action_raw_bar_missing",
                    message="A raw close is missing on one side of the corporate action.",
                    severity="blocker",
                    context=base_detail,
                )
            )
            details.append({**base_detail, "status": "raw_bar_missing"})
            continue
        previous_raw = before.iloc[-1]
        next_raw = after.iloc[0]
        previous_at = pd.Timestamp(previous_raw["timestamp"])
        next_at = pd.Timestamp(next_raw["timestamp"])
        if effective_at - previous_at > maximum_gap or next_at - effective_at > maximum_gap:
            blockers.append(
                DiagnosticMessage(
                    code="corporate_action_bar_gap",
                    message="Raw bars around the corporate action exceed max_bar_gap.",
                    severity="blocker",
                    context={
                        **base_detail,
                        "previous_bar_at": previous_at.isoformat(),
                        "next_bar_at": next_at.isoformat(),
                    },
                )
            )
            details.append({**base_detail, "status": "bar_gap"})
            continue
        asset_adjusted = adjusted[adjusted["asset_id"].astype(str) == asset_id]
        adjusted_pair = asset_adjusted[
            asset_adjusted["timestamp"].isin([previous_at, next_at])
        ].set_index("timestamp")
        if previous_at not in adjusted_pair.index or next_at not in adjusted_pair.index:
            blockers.append(
                DiagnosticMessage(
                    code="corporate_action_adjusted_bar_missing",
                    message="Adjusted closes do not align to both raw event-boundary timestamps.",
                    severity="blocker",
                    context=base_detail,
                )
            )
            details.append({**base_detail, "status": "adjusted_bar_missing"})
            continue
        currencies = {
            str(previous_raw["currency"]),
            str(next_raw["currency"]),
            str(adjusted_pair.loc[previous_at, "currency"]),
            str(adjusted_pair.loc[next_at, "currency"]),
        }
        split_factor = 1.0
        rights_factor = 1.0
        cash_equivalent = 0.0
        currency_failed = False
        for action in event_actions.to_dict("records"):
            action_type = str(action["action_type"])
            value = float(action["value"])
            action_currency = action.get("currency")
            if action_type in {"split", "rights", "conversion", "stock_merger"} and value <= 0:
                raise ValueError("Share-exchange ratios and rights factors must be positive.")
            if action_type in {
                "cash_dividend",
                "spin_off",
                "merger",
                "fractional_cash_in_lieu",
            } and value < 0:
                raise ValueError("Cash-equivalent corporate actions must be non-negative.")
            if action_type in {
                "cash_dividend",
                "spin_off",
                "merger",
                "fractional_cash_in_lieu",
            }:
                if pd.isna(action_currency):
                    blockers.append(
                        DiagnosticMessage(
                            code="corporate_action_currency",
                            message=(
                                "Bar and cash-equivalent action currencies must be "
                                "explicit and identical."
                            ),
                            severity="blocker",
                            context={**base_detail, "currencies": sorted(currencies)},
                        )
                    )
                    details.append({**base_detail, "status": "currency_mismatch"})
                    currency_failed = True
                    break
                currencies.add(str(action_currency))
                if action_type == "cash_dividend":
                    cash_equivalent += value * (1.0 - dividend_withholding_rate)
                else:
                    cash_equivalent += value
            elif action_type in {"split", "conversion", "stock_merger"}:
                split_factor *= value
            else:
                rights_factor *= value
        if currency_failed:
            continue
        if len(currencies) != 1:
            blockers.append(
                DiagnosticMessage(
                    code="corporate_action_currency",
                    message=(
                        "Bar and cash-equivalent action currencies must be "
                        "explicit and identical."
                    ),
                    severity="blocker",
                    context={**base_detail, "currencies": sorted(currencies)},
                )
            )
            details.append({**base_detail, "status": "currency_mismatch"})
            continue
        previous_close = float(previous_raw["close"])
        next_close = float(next_raw["close"])
        expected_multiplier = (
            (next_close + cash_equivalent) * split_factor * rights_factor / previous_close
        )
        observed_multiplier = float(adjusted_pair.loc[next_at, "close"]) / float(
            adjusted_pair.loc[previous_at, "close"]
        )
        return_error = abs(observed_multiplier - expected_multiplier)
        detail = {
            **base_detail,
            "status": "pass" if return_error <= maximum_return_error else "mismatch",
            "previous_bar_at": previous_at.isoformat(),
            "next_bar_at": next_at.isoformat(),
            "split_factor": split_factor,
            "rights_factor": rights_factor,
            "cash_equivalent": cash_equivalent,
            "expected_total_return": expected_multiplier - 1.0,
            "observed_adjusted_return": observed_multiplier - 1.0,
            "absolute_return_error": return_error,
            "action_order": "split_then_rights_then_cash_equivalent",
        }
        details.append(detail)
        return_errors.append(return_error)
        reconciled_count += 1
        if return_error > maximum_return_error:
            blockers.append(
                DiagnosticMessage(
                    code="corporate_action_adjustment_mismatch",
                    message="Adjusted-bar return does not reconcile to corporate-action economics.",
                    severity="blocker",
                    context=detail,
                )
            )
    if len(action_frame) < minimum_actions:
        blockers.append(
            DiagnosticMessage(
                code="corporate_action_sample_size",
                message="Observable corporate actions are below the configured minimum.",
                severity="blocker",
                context={"observable_actions": len(action_frame), "minimum": minimum_actions},
            )
        )
    return ArtifactEnvelope(
        artifact_type="corporate_action_adjustment",
        run_id=run_id,
        producer=ProducerReference(name="corporate-action-adjustment", version=__version__),
        parameters={
            "evaluated_at": evaluated.isoformat(),
            "max_bar_gap": str(maximum_gap),
            "maximum_return_error": maximum_return_error,
            "minimum_actions": minimum_actions,
            "dividend_withholding_rate": dividend_withholding_rate,
            "allow_late_revisions": allow_late_revisions,
            "raw_adjustment_state": "raw",
            "adjusted_adjustment_state": "total_return_adjusted",
        },
        summary={
            "observable_action_count": len(action_frame),
            "event_count": len(grouped_actions),
            "reconciled_event_count": reconciled_count,
            "maximum_absolute_return_error": max(return_errors, default=None),
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="corporate_action_adjustment_scope",
                message=(
                    "Adjacent-close reconciliation covers split, conversion, stock-merger "
                    "exchange ratios, cash dividend after flat withholding, spin-off, cash "
                    "merger, rights, and fractional cash-in-lieu. Late vendor revisions use the "
                    "latest PIT available_at and can fail closed. Odd-lot specials beyond one "
                    "cash-in-lieu amount remain out of scope."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={
            "split_value_semantics": "new_shares_per_old_share",
            "cash_dividend_value_semantics": "cash_per_pre_event_share",
            "spin_off_value_semantics": "cash_equivalent_per_parent_share",
            "merger_value_semantics": "cash_consideration_per_share",
            "stock_merger_value_semantics": "acquirer_shares_per_target_share",
            "fractional_cash_in_lieu_value_semantics": "cash_per_share",
            "conversion_value_semantics": "new_shares_per_old_share",
            "rights_value_semantics": "pre_event_price_adjustment_factor",
            "dividend_withholding": "flat_rate_on_cash_dividend",
            "simultaneous_action_order": "split_then_rights_then_cash_equivalent",
            "vendor_revision": "latest_available_at_or_before_evaluation",
            "live_order_submission": False,
        },
    ).finalize()
