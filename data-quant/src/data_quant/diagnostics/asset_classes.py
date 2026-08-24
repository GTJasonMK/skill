"""Native, offline-only diagnostics for non-equity asset classes."""

from __future__ import annotations

import math
from typing import Any, cast

import numpy as np
import pandas as pd
from scipy.optimize import brentq, curve_fit

from data_quant import __version__
from data_quant.asset_classes import (
    black_scholes,
    build_unadjusted_continuous_futures,
    fx_forward_outright,
    implied_volatility,
    liquidation_buffer_fraction,
    perpetual_funding_cashflow,
    price_cashflows,
)
from data_quant.asset_classes.options import OptionType
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.contracts.parameters import (
    CryptoCrossMarginParameters,
    CryptoMarginStressParameters,
    FixedIncomeCurveStressParameters,
    FixedIncomePriceReconciliationParameters,
    FixedIncomeRiskParameters,
    FuturesRollExecutionParameters,
    FuturesRollParameters,
    FXForwardCheckParameters,
    FXRolloverParameters,
    OptionHedgeReplayParameters,
    OptionSurfaceParameters,
    OptionSurfaceSmoothingParameters,
)
from data_quant.io.validation import parse_utc_timestamp
from data_quant.registry import register_diagnostic


def _select_one(
    frame: pd.DataFrame,
    column: str,
    requested: str | None,
    diagnostic_id: str,
) -> tuple[pd.DataFrame, str]:
    values = sorted(frame[column].dropna().astype(str).unique())
    if requested is None:
        if len(values) != 1:
            raise ValueError(f"{diagnostic_id} requires one {column}; available values: {values}")
        requested = values[0]
    selected = frame[frame[column].astype(str) == requested].copy()
    if selected.empty:
        raise ValueError(f"{diagnostic_id} selection {column}={requested!r} has no rows.")
    return selected, requested


def _gap(code: str, message: str) -> DiagnosticMessage:
    return DiagnosticMessage(code=code, message=message, severity="warning")


def _migration_continuous_futures(
    joined: pd.DataFrame,
    *,
    metric: str,
    roll_days_before_expiry: int,
    confirmation_periods: int,
) -> pd.DataFrame:
    data = joined.copy()
    data["timestamp"] = parse_utc_timestamp(data["timestamp"], "timestamp")
    data["expiry_at"] = parse_utc_timestamp(data["expiry_at"], "expiry_at")
    if metric not in data or data[metric].isna().any():
        raise ValueError(f"Futures {metric} roll requires complete {metric} observations.")
    data[metric] = pd.to_numeric(data[metric], errors="raise")
    if (data[metric] < 0).any():
        raise ValueError(f"Futures {metric} observations must be non-negative.")
    expiries = (
        data[["contract_id", "expiry_at"]]
        .drop_duplicates()
        .sort_values("expiry_at")
        .set_index("contract_id")["expiry_at"]
    )
    contract_order = expiries.index.astype(str).tolist()
    current_index = 0
    confirmation = 0
    last_contract: str | None = None
    rows = []
    threshold = pd.Timedelta(days=roll_days_before_expiry)
    for timestamp, group in data.sort_values(["timestamp", "expiry_at"]).groupby(
        "timestamp",
        sort=True,
    ):
        available = set(group["contract_id"].astype(str))
        while current_index < len(contract_order) - 1 and contract_order[current_index] not in available:
            current_index += 1
            confirmation = 0
        current_contract = contract_order[current_index]
        while (
            current_index < len(contract_order) - 1
            and pd.Timestamp(timestamp) >= expiries.loc[current_contract] - threshold
            and contract_order[current_index + 1] in available
        ):
            current_index += 1
            current_contract = contract_order[current_index]
            confirmation = 0
        if current_index < len(contract_order) - 1:
            next_contract = contract_order[current_index + 1]
            if current_contract in available and next_contract in available:
                current_value = float(
                    group.loc[group["contract_id"].astype(str) == current_contract, metric].iloc[0]
                )
                next_value = float(
                    group.loc[group["contract_id"].astype(str) == next_contract, metric].iloc[0]
                )
                confirmation = confirmation + 1 if next_value > current_value else 0
                if confirmation >= confirmation_periods:
                    current_index += 1
                    current_contract = next_contract
                    confirmation = 0
        selected = group[group["contract_id"].astype(str) == current_contract]
        if selected.empty:
            raise ValueError(f"Selected futures contract {current_contract!r} has no bar at {timestamp}.")
        selected_row = selected.iloc[0]
        rolled = last_contract is not None and current_contract != last_contract
        rows.append(
            {
                "timestamp": timestamp,
                "contract_id": current_contract,
                "expiry_at": selected_row["expiry_at"],
                "price": float(selected_row["close"]),
                "previous_contract": last_contract if rolled else None,
                "roll": rolled,
                "selection_metric": metric,
                "selection_metric_value": float(selected_row[metric]),
            }
        )
        last_contract = current_contract
    return pd.DataFrame(rows)


@register_diagnostic(
    "futures-roll",
    "futures_roll",
    required_table_types=("futures_contracts", "market_bars"),
    manifest_stage="research",
    parameter_model=FuturesRollParameters,
    description="Build an expiry-rule continuous futures series and attribute observable roll gaps.",
)
def futures_roll_artifact(
    contracts: pd.DataFrame,
    bars: pd.DataFrame,
    *,
    root: str | None = None,
    roll_days_before_expiry: int = 5,
    roll_method: str = "expiry",
    confirmation_periods: int = 2,
    collateral_rate_annual: float = 0.0,
    annualization: int = 252,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    contracts, root = _select_one(contracts.copy(), "root", root, "futures-roll")
    if roll_method not in {"expiry", "volume", "open_interest"}:
        raise ValueError("roll_method must be expiry, volume, or open_interest.")
    if confirmation_periods < 1 or collateral_rate_annual <= -1 or annualization < 1:
        raise ValueError("Futures roll confirmation, collateral, or annualization is invalid.")
    bar_columns = ["timestamp", "asset_id", "close", "currency", "adjustment_state"]
    if roll_method != "expiry":
        bar_columns.append(roll_method)
    missing_bar_columns = [column for column in bar_columns if column not in bars]
    if missing_bar_columns:
        raise ValueError(f"futures-roll bars missing columns: {missing_bar_columns}")
    joined = bars[bar_columns].merge(
        contracts[
            [
                "contract_id",
                "expiry_at",
                "listed_at",
                "last_trade_at",
                "currency",
            ]
        ],
        left_on="asset_id",
        right_on="contract_id",
        how="inner",
        suffixes=("", "_contract"),
        validate="many_to_one",
    )
    if joined.empty:
        raise ValueError("futures-roll found no market bars for selected contracts.")
    for column in ("timestamp", "listed_at", "last_trade_at", "expiry_at"):
        joined[column] = parse_utc_timestamp(joined[column], column)
    if (joined["timestamp"] < joined["listed_at"]).any() or (
        joined["timestamp"] > joined["last_trade_at"]
    ).any():
        raise ValueError("futures-roll bars fall outside the listed/last-trade lifecycle.")
    if (joined["currency"].astype(str) != joined["currency_contract"].astype(str)).any():
        raise ValueError("futures-roll bar and contract currencies must match.")
    if joined["adjustment_state"].astype(str).ne("raw").any():
        raise ValueError("futures-roll requires raw, unadjusted contract bars.")
    if roll_method == "expiry":
        continuous = build_unadjusted_continuous_futures(
            joined,
            timestamp_col="timestamp",
            contract_col="contract_id",
            price_col="close",
            expiry_col="expiry_at",
            roll_days_before_expiry=roll_days_before_expiry,
        )
        continuous["selection_metric"] = "expiry"
        continuous["selection_metric_value"] = None
    else:
        continuous = _migration_continuous_futures(
            joined,
            metric=roll_method,
            roll_days_before_expiry=roll_days_before_expiry,
            confirmation_periods=confirmation_periods,
        )
    lookup = joined.set_index(["timestamp", "contract_id"])["close"]
    details: list[dict[str, Any]] = []
    missing_gap_count = 0
    prior_selected_price: float | None = None
    for row in continuous.to_dict("records"):
        previous = row["previous_contract"]
        previous_price: float | None = None
        roll_gap: float | None = None
        if bool(row["roll"]) and isinstance(previous, str):
            try:
                previous_price = float(lookup.loc[(row["timestamp"], previous)])
                roll_gap = float(row["price"]) - previous_price
            except KeyError:
                missing_gap_count += 1
        selected_price = float(row["price"])
        unadjusted_price_return = (
            selected_price / prior_selected_price - 1.0 if prior_selected_price is not None else None
        )
        roll_gap_adjustment = (
            roll_gap / prior_selected_price
            if roll_gap is not None and prior_selected_price is not None
            else 0.0
            if prior_selected_price is not None and not bool(row["roll"])
            else None
        )
        futures_return = (
            unadjusted_price_return - roll_gap_adjustment
            if unadjusted_price_return is not None and roll_gap_adjustment is not None
            else None
        )
        collateral_return = collateral_rate_annual / annualization if futures_return is not None else None
        total_return = (
            futures_return + collateral_return
            if futures_return is not None and collateral_return is not None
            else None
        )
        details.append(
            {
                "timestamp": pd.Timestamp(row["timestamp"]).isoformat(),
                "contract_id": str(row["contract_id"]),
                "expiry_at": pd.Timestamp(row["expiry_at"]).isoformat(),
                "price": selected_price,
                "selection_metric": str(row["selection_metric"]),
                "selection_metric_value": (
                    float(row["selection_metric_value"]) if pd.notna(row["selection_metric_value"]) else None
                ),
                "previous_contract": previous if isinstance(previous, str) else None,
                "roll": bool(row["roll"]),
                "previous_contract_price": previous_price,
                "roll_gap": roll_gap,
                "roll_gap_fraction": (
                    roll_gap / previous_price if roll_gap is not None and previous_price is not None else None
                ),
                "unadjusted_price_return": unadjusted_price_return,
                "roll_gap_adjustment": roll_gap_adjustment,
                "futures_return": futures_return,
                "collateral_return": collateral_return,
                "total_return_with_collateral": total_return,
            }
        )
        prior_selected_price = selected_price
    warnings = (
        [
            DiagnosticMessage(
                code="roll_gap_quote_missing",
                message=f"{missing_gap_count} roll event(s) lack a same-timestamp old-contract quote.",
                severity="warning",
            )
        ]
        if missing_gap_count
        else []
    )
    roll_gaps = [row["roll_gap"] for row in details if row["roll_gap"] is not None]
    futures_returns = [row["futures_return"] for row in details if row["futures_return"] is not None]
    total_returns = [
        row["total_return_with_collateral"]
        for row in details
        if row["total_return_with_collateral"] is not None
    ]
    return ArtifactEnvelope(
        artifact_type="futures_roll",
        run_id=run_id,
        producer=ProducerReference(name="futures-roll", version=__version__),
        parameters={
            "root": root,
            "roll_days_before_expiry": roll_days_before_expiry,
            "roll_method": roll_method,
            "confirmation_periods": confirmation_periods,
            "collateral_rate_annual": collateral_rate_annual,
            "annualization": annualization,
        },
        summary={
            "period_count": len(details),
            "roll_count": sum(bool(row["roll"]) for row in details),
            "attributed_roll_count": len(roll_gaps),
            "total_observable_roll_gap": float(sum(roll_gaps)),
            "cumulative_futures_return": float(np.prod([1.0 + value for value in futures_returns]) - 1.0),
            "cumulative_total_return_with_collateral": float(
                np.prod([1.0 + value for value in total_returns]) - 1.0
            ),
            "total_collateral_return": float(sum(row["collateral_return"] or 0.0 for row in details)),
        },
        warnings=warnings,
        evidence_gaps=[
            _gap(
                "futures_roll_scope",
                "Selection and roll-gap adjustment do not model bid/ask roll execution, fees, "
                "daily variation-margin cash timing, margin requirements, limits, or collateral haircuts.",
            )
        ],
        details=details,
        provenance={
            "series_adjustment": "none",
            "return_adjustment": "same_timestamp_observable_roll_gap",
            "live_order_submission": False,
        },
    ).finalize()


@register_diagnostic(
    "futures-roll-execution",
    "futures_roll_execution",
    required_table_types=(
        "futures_contracts",
        "market_bars",
        "market_quotes",
        "futures_margin_terms",
    ),
    manifest_stage="execution",
    parameter_model=FuturesRollExecutionParameters,
    description="Replay bid/ask futures rolls with daily variation margin, fees, and margin gates.",
)
def futures_roll_execution_artifact(
    contracts: pd.DataFrame,
    bars: pd.DataFrame,
    quotes: pd.DataFrame,
    margin_terms: pd.DataFrame,
    position_limits: pd.DataFrame | None = None,
    *,
    position_quantity: float,
    initial_cash: float,
    root: str | None = None,
    roll_days_before_expiry: int = 5,
    roll_method: str = "expiry",
    confirmation_periods: int = 2,
    per_contract_fee: float = 0.0,
    exchange_fee_bps: float = 0.0,
    max_roll_participation: float = 1.0,
    roll_impact_coefficient_bps: float = 0.0,
    collateral_rate_annual: float = 0.0,
    collateral_haircut: float = 0.0,
    collateral_fx_rate: float = 1.0,
    maximum_gross_notional: float | None = None,
    annualization: int = 252,
    daily_loss_limit_fraction: float = 0.10,
    enforce_position_limits: bool = False,
    allow_physical_delivery: bool = False,
    force_liquidate_on_margin_breach: bool = False,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if (
        position_quantity == 0
        or initial_cash <= 0
        or per_contract_fee < 0
        or exchange_fee_bps < 0
        or not 0 < max_roll_participation <= 1
        or roll_impact_coefficient_bps < 0
        or collateral_rate_annual <= -1
        or not 0 <= collateral_haircut < 1
        or collateral_fx_rate <= 0
        or (maximum_gross_notional is not None and maximum_gross_notional <= 0)
        or annualization < 1
        or daily_loss_limit_fraction <= 0
        or not all(
            math.isfinite(value)
            for value in (
                position_quantity,
                initial_cash,
                per_contract_fee,
                exchange_fee_bps,
                collateral_rate_annual,
                collateral_haircut,
                collateral_fx_rate,
                daily_loss_limit_fraction,
            )
        )
    ):
        raise ValueError("Futures roll execution cash, fees, haircut, or limits are invalid.")
    roll_selection = futures_roll_artifact(
        contracts,
        bars,
        root=root,
        roll_days_before_expiry=roll_days_before_expiry,
        roll_method=roll_method,
        confirmation_periods=confirmation_periods,
        collateral_rate_annual=0.0,
        annualization=annualization,
        run_id=run_id,
    )
    root = str(roll_selection.parameters["root"])
    selected_contracts = contracts[contracts["root"].astype(str) == root].copy()
    if selected_contracts["contract_id"].astype(str).duplicated().any():
        raise ValueError("Futures contract terms must be unique by contract_id.")
    contract_lookup = selected_contracts.set_index(selected_contracts["contract_id"].astype(str))
    quote_frame = quotes.copy()
    quote_frame["timestamp"] = parse_utc_timestamp(quote_frame["timestamp"], "timestamp")
    bar_frame = bars[bars["asset_id"].astype(str).isin(contract_lookup.index)].copy()
    bar_frame["timestamp"] = parse_utc_timestamp(bar_frame["timestamp"], "timestamp")
    bar_frame["close"] = pd.to_numeric(bar_frame["close"], errors="coerce")
    if not np.isfinite(bar_frame["close"]).all() or (bar_frame["close"] <= 0).any():
        raise ValueError("Futures settlement bars require finite positive closes.")
    terms = margin_terms.copy()
    for column in ("effective_from", "available_at"):
        terms[column] = parse_utc_timestamp(terms[column], column)
    for column in (
        "initial_margin_per_contract",
        "maintenance_margin_per_contract",
        "daily_price_limit_fraction",
    ):
        terms[column] = pd.to_numeric(terms[column], errors="coerce")
    numeric_term_columns = [
        "initial_margin_per_contract",
        "maintenance_margin_per_contract",
        "daily_price_limit_fraction",
    ]
    if not np.isfinite(terms[numeric_term_columns].to_numpy(dtype=float)).all():
        raise ValueError("Futures margin terms must be finite.")

    limits: pd.DataFrame | None = None
    if position_limits is not None:
        limits = position_limits.copy()
        for column in ("effective_from", "available_at"):
            limits[column] = parse_utc_timestamp(limits[column], column)
        limits["max_contracts"] = pd.to_numeric(limits["max_contracts"], errors="coerce")
        if not np.isfinite(limits["max_contracts"].to_numpy(dtype=float)).all():
            raise ValueError("Futures position limits must be finite.")

    def position_limit(contract_id: str, timestamp: pd.Timestamp) -> tuple[float, str] | None:
        if limits is None:
            return None
        venue = str(contract_lookup.loc[contract_id, "venue"])
        selected = limits[
            (limits["contract_id"].astype(str) == contract_id)
            & (limits["venue"].astype(str) == venue)
            & (limits["effective_from"] <= timestamp)
            & (limits["available_at"] <= timestamp)
        ]
        if selected.empty:
            if enforce_position_limits:
                raise ValueError(f"No PIT futures position limit covers {contract_id!r} at {timestamp}.")
            return None
        selected = selected[selected["effective_from"] == selected["effective_from"].max()]
        if len(selected) != 1:
            raise ValueError(f"Futures position limits are ambiguous for {contract_id!r}.")
        limit = float(selected.iloc[0]["max_contracts"])
        if not math.isfinite(limit) or limit <= 0:
            raise ValueError(f"Futures position limit is invalid for {contract_id!r}.")
        return limit, str(selected.iloc[0]["limit_source"])

    def contract_terms(contract_id: str, timestamp: pd.Timestamp) -> pd.Series:
        venue = str(contract_lookup.loc[contract_id, "venue"])
        currency = str(contract_lookup.loc[contract_id, "currency"])
        selected = terms[
            (terms["contract_id"].astype(str) == contract_id)
            & (terms["venue"].astype(str) == venue)
            & (terms["effective_from"] <= timestamp)
            & (terms["available_at"] <= timestamp)
        ]
        if selected.empty:
            raise ValueError(f"No PIT futures margin terms cover {contract_id!r} at {timestamp}.")
        selected = selected[selected["effective_from"] == selected["effective_from"].max()]
        if len(selected) != 1:
            raise ValueError(f"Futures margin terms are ambiguous for {contract_id!r}.")
        row = selected.iloc[0]
        initial = float(row["initial_margin_per_contract"])
        maintenance = float(row["maintenance_margin_per_contract"])
        price_limit = float(row["daily_price_limit_fraction"])
        if (
            maintenance <= 0
            or initial < maintenance
            or not 0 < price_limit < 1
            or str(row["currency"]) != currency
        ):
            raise ValueError(f"Futures margin or price-limit terms are invalid for {contract_id!r}.")
        return row

    def execution_price(
        contract_id: str,
        timestamp: pd.Timestamp,
        action: str,
        quantity: float,
    ) -> float:
        venue = str(contract_lookup.loc[contract_id, "venue"])
        selected = quote_frame[
            (quote_frame["asset_id"].astype(str) == contract_id)
            & (quote_frame["venue"].astype(str) == venue)
            & (quote_frame["timestamp"] == timestamp)
        ]
        if len(selected) != 1:
            raise ValueError(f"Futures roll requires one exact-timestamp quote for {contract_id!r}.")
        bid = float(selected.iloc[0]["bid"])
        ask = float(selected.iloc[0]["ask"])
        if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask < bid:
            raise ValueError(f"Futures quote bid/ask is invalid for {contract_id!r}.")
        reference = ask if action == "buy" else bid
        if "volume" not in selected.columns or pd.isna(selected.iloc[0].get("volume")):
            return reference
        volume = float(selected.iloc[0]["volume"])
        if volume <= 0:
            raise ValueError(f"Futures quote volume must be positive for {contract_id!r}.")
        participation = abs(quantity) / volume
        if participation > max_roll_participation:
            blockers.append(
                DiagnosticMessage(
                    code="futures_roll_depth",
                    message="Roll quantity exceeds quote-volume participation capacity.",
                    severity="blocker",
                    context={
                        "contract_id": contract_id,
                        "timestamp": timestamp.isoformat(),
                        "quantity": abs(quantity),
                        "volume": volume,
                        "participation": participation,
                        "limit": max_roll_participation,
                    },
                )
            )
        direction = 1.0 if action == "buy" else -1.0
        impact = roll_impact_coefficient_bps * participation
        return reference * (1.0 + direction * impact / 10_000.0)

    details: list[dict[str, Any]] = []
    blockers: list[DiagnosticMessage] = []
    warnings = list(roll_selection.warnings)
    cash = initial_cash
    live_quantity = position_quantity
    prior_contract: str | None = None
    prior_settlement: float | None = None
    total_variation_margin = 0.0
    total_fees = 0.0
    total_collateral_return = 0.0
    delivery_count = 0
    forced_liquidation_count = 0
    minimum_margin_buffer = math.inf
    for selected in roll_selection.details:
        timestamp = pd.Timestamp(selected["timestamp"])
        contract_id = str(selected["contract_id"])
        settlement = float(selected["price"])
        multiplier = float(contract_lookup.loc[contract_id, "multiplier"])
        if not math.isfinite(multiplier) or multiplier <= 0:
            raise ValueError(f"Futures multiplier is invalid for {contract_id!r}.")
        rolled = bool(selected["roll"]) and live_quantity != 0
        close_price: float | None = None
        open_price: float | None = None
        fees = 0.0
        forced_today = False
        delivery_today = False
        if live_quantity == 0 or prior_contract is None or prior_settlement is None:
            variation_margin = 0.0
        elif rolled:
            close_action = "sell" if live_quantity > 0 else "buy"
            open_action = "buy" if live_quantity > 0 else "sell"
            close_price = execution_price(prior_contract, timestamp, close_action, abs(live_quantity))
            open_price = execution_price(contract_id, timestamp, open_action, abs(live_quantity))
            prior_multiplier = float(contract_lookup.loc[prior_contract, "multiplier"])
            variation_margin = live_quantity * prior_multiplier * (
                close_price - prior_settlement
            ) + live_quantity * multiplier * (settlement - open_price)
            traded_notional = abs(live_quantity) * (prior_multiplier * close_price + multiplier * open_price)
            fees = abs(live_quantity) * 2.0 * per_contract_fee + (
                traded_notional * exchange_fee_bps / 10_000.0
            )
        else:
            variation_margin = live_quantity * multiplier * (settlement - prior_settlement)
        collateral_return = cash * collateral_rate_annual / annualization
        intraday_margin_call = False
        if (
            live_quantity != 0
            and prior_settlement is not None
            and not rolled
            and {"high", "low"}.issubset(bar_frame.columns)
        ):
            session_bar = bar_frame[
                (bar_frame["asset_id"].astype(str) == contract_id) & (bar_frame["timestamp"] == timestamp)
            ]
            if len(session_bar) == 1:
                high = pd.to_numeric(session_bar.iloc[0]["high"], errors="coerce")
                low = pd.to_numeric(session_bar.iloc[0]["low"], errors="coerce")
                if pd.notna(high) and pd.notna(low) and high >= low > 0:
                    worst = float(low if live_quantity > 0 else high)
                    intra_vm = live_quantity * multiplier * (worst - prior_settlement)
                    intra_cash = cash + intra_vm + collateral_return - fees
                    intra_available = intra_cash * collateral_fx_rate * (1.0 - collateral_haircut)
                    intra_maint = abs(live_quantity) * float(
                        contract_terms(contract_id, timestamp)["maintenance_margin_per_contract"]
                    )
                    if intra_available < intra_maint:
                        intraday_margin_call = True
                        blockers.append(
                            DiagnosticMessage(
                                code="futures_intraday_margin_call",
                                message="Intraday high/low mark would breach maintenance margin.",
                                severity="blocker",
                                context={
                                    "timestamp": timestamp.isoformat(),
                                    "contract_id": contract_id,
                                    "worst_price": worst,
                                    "intraday_available_collateral": intra_available,
                                    "maintenance_requirement": intra_maint,
                                },
                            )
                        )
        net_cashflow = variation_margin + collateral_return - fees
        cash += net_cashflow
        total_variation_margin += variation_margin
        total_fees += fees
        total_collateral_return += collateral_return
        terms_row = contract_terms(contract_id, timestamp)
        initial_requirement = abs(live_quantity) * float(terms_row["initial_margin_per_contract"])
        maintenance_requirement = abs(live_quantity) * float(terms_row["maintenance_margin_per_contract"])
        limit_result = position_limit(contract_id, timestamp)
        if limit_result is not None and live_quantity != 0:
            position_limit_value, limit_source = limit_result
            if abs(live_quantity) > position_limit_value:
                blockers.append(
                    DiagnosticMessage(
                        code="futures_position_limit_breach",
                        message="Position quantity exceeds the effective PIT position limit.",
                        severity="blocker",
                        context={
                            "timestamp": timestamp.isoformat(),
                            "contract_id": contract_id,
                            "position_quantity": abs(live_quantity),
                            "max_contracts": position_limit_value,
                            "limit_source": limit_source,
                        },
                    )
                )
        available_collateral = cash * collateral_fx_rate * (1.0 - collateral_haircut)
        gross_notional = abs(live_quantity) * multiplier * settlement
        if maximum_gross_notional is not None and gross_notional > maximum_gross_notional:
            blockers.append(
                DiagnosticMessage(
                    code="futures_collateral_concentration",
                    message="Gross futures notional exceeds the configured concentration cap.",
                    severity="blocker",
                    context={
                        "timestamp": timestamp.isoformat(),
                        "contract_id": contract_id,
                        "gross_notional": gross_notional,
                        "limit": maximum_gross_notional,
                    },
                )
            )
        margin_buffer = available_collateral - maintenance_requirement
        minimum_margin_buffer = min(minimum_margin_buffer, margin_buffer)
        if available_collateral < maintenance_requirement:
            blockers.append(
                DiagnosticMessage(
                    code="futures_maintenance_margin_breach",
                    message="End-of-day haircut-adjusted collateral is below maintenance margin.",
                    severity="blocker",
                    context={
                        "timestamp": timestamp.isoformat(),
                        "contract_id": contract_id,
                        "available_collateral": available_collateral,
                        "maintenance_requirement": maintenance_requirement,
                    },
                )
            )
        elif available_collateral < initial_requirement:
            warnings.append(
                DiagnosticMessage(
                    code="futures_initial_margin_shortfall",
                    message="Collateral remains above maintenance but below initial margin.",
                    severity="warning",
                    context={"timestamp": timestamp.isoformat(), "contract_id": contract_id},
                )
            )
            if force_liquidate_on_margin_breach and live_quantity != 0:
                close_action = "sell" if live_quantity > 0 else "buy"
                try:
                    liquidation_price = execution_price(
                        contract_id, timestamp, close_action, abs(live_quantity)
                    )
                except ValueError:
                    liquidation_price = settlement
                slippage = live_quantity * multiplier * (liquidation_price - settlement)
                cash += slippage
                net_cashflow += slippage
                forced_liquidation_count += 1
                live_quantity = 0.0
                forced_today = True
        daily_loss_fraction = max(0.0, -net_cashflow) / initial_cash
        if daily_loss_fraction > daily_loss_limit_fraction:
            blockers.append(
                DiagnosticMessage(
                    code="futures_daily_loss_limit",
                    message="Daily futures cash loss exceeds the configured initial-cash limit.",
                    severity="blocker",
                    context={
                        "timestamp": timestamp.isoformat(),
                        "loss_fraction": daily_loss_fraction,
                        "limit": daily_loss_limit_fraction,
                    },
                )
            )
        contract_history = bar_frame[
            (bar_frame["asset_id"].astype(str) == contract_id) & (bar_frame["timestamp"] <= timestamp)
        ].sort_values("timestamp")
        settlement_return = None
        if len(contract_history) >= 2:
            previous_close = float(contract_history.iloc[-2]["close"])
            settlement_return = settlement / previous_close - 1.0
            price_limit = float(terms_row["daily_price_limit_fraction"])
            if abs(settlement_return) > price_limit:
                blockers.append(
                    DiagnosticMessage(
                        code="futures_daily_price_limit_breach",
                        message="Observed settlement move exceeds the effective exchange price limit.",
                        severity="blocker",
                        context={
                            "timestamp": timestamp.isoformat(),
                            "contract_id": contract_id,
                            "settlement_return": settlement_return,
                            "limit": price_limit,
                        },
                    )
                )
        last_trade = parse_utc_timestamp(
            pd.Series([contract_lookup.loc[contract_id, "last_trade_at"]]),
            "last_trade_at",
        ).iloc[0]
        if live_quantity != 0 and timestamp >= last_trade:
            if not allow_physical_delivery:
                blockers.append(
                    DiagnosticMessage(
                        code="futures_unplanned_delivery",
                        message="Position is still open on the contract last-trade/delivery date.",
                        severity="blocker",
                        context={
                            "timestamp": timestamp.isoformat(),
                            "contract_id": contract_id,
                            "last_trade_at": pd.Timestamp(last_trade).isoformat(),
                        },
                    )
                )
            delivery_today = True
            delivery_count += 1
            live_quantity = 0.0
        details.append(
            {
                "timestamp": timestamp.isoformat(),
                "contract_id": contract_id,
                "previous_contract": prior_contract if rolled else None,
                "roll": rolled,
                "settlement_price": settlement,
                "roll_close_price": close_price,
                "roll_open_price": open_price,
                "settlement_return": settlement_return,
                "variation_margin_cashflow": variation_margin,
                "collateral_return": collateral_return,
                "fees": fees,
                "net_cashflow": net_cashflow,
                "cash_balance": cash,
                "initial_margin_requirement": initial_requirement,
                "maintenance_margin_requirement": maintenance_requirement,
                "available_collateral_after_haircut": available_collateral,
                "gross_notional": gross_notional,
                "margin_buffer": margin_buffer,
                "forced_liquidation": forced_today,
                "intraday_margin_call": intraday_margin_call,
                "delivery": delivery_today,
                "live_quantity": live_quantity,
            }
        )
        prior_contract = contract_id
        prior_settlement = settlement
    return ArtifactEnvelope(
        artifact_type="futures_roll_execution",
        run_id=run_id,
        producer=ProducerReference(name="futures-roll-execution", version=__version__),
        parameters={
            "root": root,
            "position_quantity": position_quantity,
            "initial_cash": initial_cash,
            "roll_days_before_expiry": roll_days_before_expiry,
            "roll_method": roll_method,
            "confirmation_periods": confirmation_periods,
            "per_contract_fee": per_contract_fee,
            "exchange_fee_bps": exchange_fee_bps,
            "max_roll_participation": max_roll_participation,
            "roll_impact_coefficient_bps": roll_impact_coefficient_bps,
            "collateral_rate_annual": collateral_rate_annual,
            "collateral_haircut": collateral_haircut,
            "collateral_fx_rate": collateral_fx_rate,
            "maximum_gross_notional": maximum_gross_notional,
            "annualization": annualization,
            "daily_loss_limit_fraction": daily_loss_limit_fraction,
            "enforce_position_limits": enforce_position_limits,
            "allow_physical_delivery": allow_physical_delivery,
            "force_liquidate_on_margin_breach": force_liquidate_on_margin_breach,
        },
        summary={
            "period_count": len(details),
            "roll_count": sum(bool(row["roll"]) for row in details),
            "total_variation_margin": total_variation_margin,
            "total_fees": total_fees,
            "total_collateral_return": total_collateral_return,
            "ending_cash": cash,
            "minimum_margin_buffer": minimum_margin_buffer,
            "position_limits_enforced": enforce_position_limits,
            "delivery_count": delivery_count,
            "forced_liquidation_count": forced_liquidation_count,
            "blocker_count": len(blockers),
        },
        warnings=warnings,
        blockers=blockers,
        evidence_gaps=[
            _gap(
                "futures_roll_execution_scope",
                "Exact-snapshot bid/ask replay and end-of-day variation margin omit intraday margin "
                "exchange fee tiers. Intraday margin uses session high/low versus prior settle. "
                "Roll depth is quote-volume participation; impact "
                "is linear in that fraction. Collateral FX is a static "
                "rate; concentration is a gross-notional cap. Delivery is last-trade cash flatten.",
            )
        ],
        details=details,
        provenance={
            "execution": "offline_exact_timestamp_bid_ask",
            "variation_margin_timing": "end_of_day",
            "live_order_submission": False,
        },
    ).finalize()


@register_diagnostic(
    "option-surface-check",
    "option_surface",
    required_table_types=("option_contracts", "market_quotes"),
    manifest_stage="risk",
    parameter_model=OptionSurfaceParameters,
    description="Recover European implied volatility and check static strike/parity consistency.",
)
def option_surface_artifact(
    contracts: pd.DataFrame,
    quotes: pd.DataFrame,
    *,
    spot: float,
    underlying_id: str | None = None,
    expiry_at: str | None = None,
    risk_free_rate: float = 0.0,
    dividend_yield: float = 0.0,
    parity_tolerance: float = 0.01,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if spot <= 0 or parity_tolerance < 0:
        raise ValueError("spot must be positive and parity_tolerance non-negative.")
    contracts, underlying_id = _select_one(
        contracts.copy(), "underlying_id", underlying_id, "option-surface-check"
    )
    contracts["expiry_at"] = parse_utc_timestamp(contracts["expiry_at"], "expiry_at")
    if expiry_at is None:
        expiries = sorted(contracts["expiry_at"].unique())
        if len(expiries) != 1:
            raise ValueError("option-surface-check requires one expiry_at selection.")
        selected_expiry = pd.Timestamp(expiries[0])
    else:
        selected_expiry = parse_utc_timestamp(pd.Series([expiry_at]), "expiry_at").iloc[0]
        contracts = contracts[contracts["expiry_at"] == selected_expiry]
    if contracts.empty:
        raise ValueError("option-surface-check selected expiry has no contracts.")
    quotes = quotes.copy()
    quotes["timestamp"] = parse_utc_timestamp(quotes["timestamp"], "timestamp")
    latest = quotes[quotes["asset_id"].isin(contracts["option_id"])]["timestamp"].max()
    if pd.isna(latest):
        raise ValueError("option-surface-check found no quotes for selected options.")
    surface = contracts.merge(
        quotes[quotes["timestamp"] == latest],
        left_on=["option_id", "venue"],
        right_on=["asset_id", "venue"],
        how="inner",
        validate="one_to_one",
    )
    if len(surface) < 2:
        raise ValueError("option-surface-check requires at least two same-timestamp option quotes.")
    surface["bid"] = pd.to_numeric(surface["bid"], errors="coerce")
    surface["ask"] = pd.to_numeric(surface["ask"], errors="coerce")
    if surface[["bid", "ask"]].isna().any().any() or (surface["bid"] <= 0).any():
        raise ValueError("Option quotes must contain finite positive bids and asks.")
    if (surface["ask"] < surface["bid"]).any():
        raise ValueError("Option ask cannot be below bid.")
    if selected_expiry <= latest:
        raise ValueError("Option expiry must follow the quote timestamp.")
    years = float((selected_expiry - latest).total_seconds() / (365.25 * 24 * 3600))
    surface["mid"] = (surface["bid"] + surface["ask"]) / 2.0
    blockers: list[DiagnosticMessage] = []
    details: list[dict[str, Any]] = []
    for row in surface.sort_values(["option_type", "strike"]).to_dict("records"):
        try:
            volatility = implied_volatility(
                float(row["mid"]),
                spot,
                float(row["strike"]),
                years,
                risk_free_rate=risk_free_rate,
                dividend_yield=dividend_yield,
                option_type=cast(OptionType, str(row["option_type"])),
            )
        except ValueError as exc:
            volatility = None
            blockers.append(
                DiagnosticMessage(
                    code="option_price_outside_model_bounds",
                    message=f"Option {row['option_id']} has no bracketed European implied volatility: {exc}",
                    severity="blocker",
                )
            )
        details.append(
            {
                "option_id": str(row["option_id"]),
                "option_type": str(row["option_type"]),
                "strike": float(row["strike"]),
                "bid": float(row["bid"]),
                "ask": float(row["ask"]),
                "mid": float(row["mid"]),
                "implied_volatility": volatility,
            }
        )
    tolerance_value = parity_tolerance * spot
    for option_type in ("call", "put"):
        typed = sorted(
            (row for row in details if row["option_type"] == option_type),
            key=lambda row: row["strike"],
        )
        mids = np.array([row["mid"] for row in typed], dtype=float)
        strikes = np.array([row["strike"] for row in typed], dtype=float)
        if len(mids) >= 2:
            violation = (
                (np.diff(mids) > tolerance_value).any()
                if option_type == "call"
                else (np.diff(mids) < -tolerance_value).any()
            )
            if violation:
                blockers.append(
                    DiagnosticMessage(
                        code="option_strike_monotonicity",
                        message=f"{option_type} mids violate strike monotonicity.",
                        severity="blocker",
                    )
                )
        if len(mids) >= 3:
            slopes = np.diff(mids) / np.diff(strikes)
            if (np.diff(slopes) < -parity_tolerance).any():
                blockers.append(
                    DiagnosticMessage(
                        code="option_butterfly_convexity",
                        message=f"{option_type} mids violate strike convexity.",
                        severity="blocker",
                    )
                )
    warnings: list[DiagnosticMessage] = []
    calls = {row["strike"]: row["mid"] for row in details if row["option_type"] == "call"}
    puts = {row["strike"]: row["mid"] for row in details if row["option_type"] == "put"}
    parity_errors = []
    for strike in sorted(calls.keys() & puts.keys()):
        target = spot * math.exp(-dividend_yield * years) - strike * math.exp(-risk_free_rate * years)
        parity_errors.append(abs((calls[strike] - puts[strike]) - target) / spot)
    if parity_errors and max(parity_errors) > parity_tolerance:
        warnings.append(
            DiagnosticMessage(
                code="put_call_parity_deviation",
                message="Observed mids exceed the configured normalized put-call parity tolerance.",
                severity="warning",
                context={"max_normalized_error": max(parity_errors)},
            )
        )
    return ArtifactEnvelope(
        artifact_type="option_surface",
        run_id=run_id,
        producer=ProducerReference(name="option-surface-check", version=__version__),
        parameters={
            "underlying_id": underlying_id,
            "expiry_at": selected_expiry.isoformat(),
            "spot": spot,
            "risk_free_rate": risk_free_rate,
            "dividend_yield": dividend_yield,
            "parity_tolerance": parity_tolerance,
        },
        summary={
            "quote_at": pd.Timestamp(latest).isoformat(),
            "option_count": len(details),
            "iv_count": sum(row["implied_volatility"] is not None for row in details),
            "blocker_count": len(blockers),
            "max_parity_error": max(parity_errors) if parity_errors else None,
        },
        warnings=warnings,
        blockers=blockers,
        evidence_gaps=[
            _gap(
                "option_model_scope",
                "European Black-Scholes checks do not prove American exercise, dividends, "
                "borrow, surface dynamics, executable hedges, or margin.",
            )
        ],
        details=details,
        provenance={"quote_selection": "latest_common_timestamp", "live_order_submission": False},
    ).finalize()


@register_diagnostic(
    "option-surface-smooth",
    "option_surface_smooth",
    required_table_types=("option_contracts", "market_quotes"),
    manifest_stage="risk",
    parameter_model=OptionSurfaceSmoothingParameters,
    description="Build a PIT multi-expiry/moneyness European IV surface with bounded interpolation.",
)
def option_surface_smooth_artifact(
    contracts: pd.DataFrame,
    quotes: pd.DataFrame,
    *,
    underlying_id: str,
    venue: str,
    evaluated_at: str,
    spot: float,
    risk_free_rate: float = 0.0,
    dividend_yield: float = 0.0,
    min_expiries: int = 2,
    min_strikes_per_expiry: int = 3,
    moneyness_grid: list[float] | None = None,
    tenor_grid_years: list[float] | None = None,
    smoothing_window: int = 3,
    smoothing_method: str = "rolling_median",
    max_moneyness_gap: float = 0.25,
    max_tenor_gap_years: float = 1.0,
    max_iv_jump: float = 0.50,
    enforce_arbitrage_free: bool = True,
    calendar_variance_tolerance: float = 1e-8,
    butterfly_convexity_tolerance: float = 1e-8,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    moneyness_grid = moneyness_grid or [-0.20, -0.10, 0.0, 0.10, 0.20]
    tenor_grid_years = tenor_grid_years or []
    if (
        spot <= 0
        or min_expiries < 2
        or min_strikes_per_expiry < 2
        or smoothing_window < 1
        or smoothing_window % 2 == 0
        or smoothing_method
        not in {
            "rolling_median",
            "quadratic_total_variance",
            "cubic_total_variance",
            "svi_total_variance",
            "raw_svi_total_variance",
            "ssvi_total_variance",
        }
        or max_moneyness_gap <= 0
        or max_tenor_gap_years <= 0
        or max_iv_jump <= 0
        or calendar_variance_tolerance < 0
        or butterfly_convexity_tolerance < 0
        or moneyness_grid != sorted(set(moneyness_grid))
        or any(tenor <= 0 for tenor in tenor_grid_years)
        or tenor_grid_years != sorted(set(tenor_grid_years))
    ):
        raise ValueError("Option surface smoothing parameters are invalid.")
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    selected_contracts = contracts[
        (contracts["underlying_id"].astype(str) == underlying_id) & (contracts["venue"].astype(str) == venue)
    ].copy()
    if selected_contracts.empty:
        raise ValueError("No option contracts match the requested underlying and venue.")
    selected_contracts["listed_at"] = parse_utc_timestamp(selected_contracts["listed_at"], "listed_at")
    selected_contracts["expiry_at"] = parse_utc_timestamp(selected_contracts["expiry_at"], "expiry_at")
    selected_contracts = selected_contracts[
        (selected_contracts["listed_at"] <= evaluated)
        & (selected_contracts["expiry_at"] > evaluated)
        & selected_contracts["exercise_style"].astype(str).str.lower().eq("european")
    ].copy()
    if selected_contracts.empty:
        raise ValueError("No PIT European option contracts remain at evaluated_at.")
    selected_quotes = quotes[
        (quotes["venue"].astype(str) == venue)
        & quotes["asset_id"].astype(str).isin(selected_contracts["option_id"].astype(str))
    ].copy()
    selected_quotes["timestamp"] = parse_utc_timestamp(selected_quotes["timestamp"], "timestamp")
    selected_quotes = selected_quotes[selected_quotes["timestamp"] <= evaluated]
    if selected_quotes.empty:
        raise ValueError("No PIT option quotes are available at evaluated_at.")
    common_counts = selected_quotes.groupby("timestamp")["asset_id"].nunique()
    common_timestamps = common_counts[common_counts == len(selected_contracts)].index
    if len(common_timestamps) == 0:
        raise ValueError("No common PIT quote timestamp covers the selected option surface.")
    quote_at = max(common_timestamps)
    selected_quotes = selected_quotes[selected_quotes["timestamp"] == quote_at].copy()
    surface = selected_contracts.merge(
        selected_quotes,
        left_on=["option_id", "venue"],
        right_on=["asset_id", "venue"],
        how="inner",
        validate="one_to_one",
    )
    if surface.empty:
        raise ValueError("PIT option surface has no joined contracts and quotes.")
    for column in ("bid", "ask", "strike"):
        surface[column] = pd.to_numeric(surface[column], errors="coerce")
    if (
        surface[["bid", "ask", "strike"]].isna().any().any()
        or (surface["bid"] <= 0).any()
        or (surface["ask"] < surface["bid"]).any()
        or (surface["strike"] <= 0).any()
    ):
        raise ValueError("Option surface bids, asks, and strikes must be finite and valid.")
    years_at_quote = (surface["expiry_at"] - quote_at).dt.total_seconds() / (365.25 * 24 * 3600)
    surface["years_to_expiry"] = years_at_quote
    surface["mid"] = (surface["bid"] + surface["ask"]) / 2.0
    raw_rows: list[dict[str, Any]] = []
    blockers: list[DiagnosticMessage] = []
    for row in surface.to_dict("records"):
        try:
            iv = implied_volatility(
                float(row["mid"]),
                spot,
                float(row["strike"]),
                float(row["years_to_expiry"]),
                risk_free_rate=risk_free_rate,
                dividend_yield=dividend_yield,
                option_type=cast(OptionType, str(row["option_type"])),
            )
        except ValueError as exc:
            blockers.append(
                DiagnosticMessage(
                    code="option_surface_iv_failure",
                    message=f"Option {row['option_id']} has no valid European IV: {exc}",
                    severity="blocker",
                )
            )
            continue
        raw_rows.append(
            {
                "option_id": str(row["option_id"]),
                "option_type": str(row["option_type"]),
                "expiry_at": pd.Timestamp(row["expiry_at"]).isoformat(),
                "years_to_expiry": float(row["years_to_expiry"]),
                "strike": float(row["strike"]),
                "log_moneyness": math.log(float(row["strike"]) / spot),
                "implied_volatility": float(iv),
                "bid": float(row["bid"]),
                "ask": float(row["ask"]),
            }
        )
    if not raw_rows:
        raise ValueError("No valid implied-volatility nodes remain after PIT recovery.")
    raw_frame = pd.DataFrame(raw_rows)
    node_rows: list[dict[str, Any]] = []
    for expiry, group in raw_frame.groupby("expiry_at", sort=True):
        grouped = (
            group.groupby("log_moneyness", as_index=False)
            .agg(
                years_to_expiry=("years_to_expiry", "first"),
                implied_volatility=("implied_volatility", "mean"),
                quote_count=("option_id", "count"),
            )
            .sort_values("log_moneyness")
            .reset_index(drop=True)
        )
        if len(grouped) < min_strikes_per_expiry:
            blockers.append(
                DiagnosticMessage(
                    code="option_surface_insufficient_strikes",
                    message=f"Expiry {expiry} has fewer than the required moneyness nodes.",
                    severity="blocker",
                    context={"node_count": len(grouped), "required": min_strikes_per_expiry},
                )
            )
            continue
        if smoothing_method == "svi_total_variance":
            tenor = float(grouped["years_to_expiry"].iloc[0])
            ks = grouped["log_moneyness"].to_numpy(dtype=float)
            total_variance = (grouped["implied_volatility"].to_numpy(dtype=float) ** 2) * tenor
            if len(ks) < 3:
                blockers.append(
                    DiagnosticMessage(
                        code="option_surface_spline_sample",
                        message=f"Expiry {expiry} needs three nodes for a restricted SVI fit.",
                        severity="blocker",
                    )
                )
                continue

            def restricted_svi(log_m, level, slope, width):
                return level + slope * np.sqrt(np.square(log_m) + width * width)

            if float(np.std(total_variance)) < 1e-12:
                fitted = np.full_like(total_variance, float(np.mean(total_variance)))
            else:
                try:
                    fitted_params, _ = curve_fit(
                        restricted_svi,
                        ks,
                        total_variance,
                        p0=(float(np.mean(total_variance)), 0.01, 0.10),
                        bounds=(0.0, np.inf),
                        maxfev=2000,
                    )
                except (RuntimeError, ValueError) as exc:
                    blockers.append(
                        DiagnosticMessage(
                            code="option_surface_svi_fit",
                            message=f"Expiry {expiry} restricted SVI fit failed: {exc}",
                            severity="blocker",
                        )
                    )
                    continue
                fitted = restricted_svi(ks, *fitted_params)
            smooth_values = pd.Series(np.sqrt(np.maximum(fitted, 1e-12) / tenor), index=grouped.index)
        elif smoothing_method == "raw_svi_total_variance":
            tenor = float(grouped["years_to_expiry"].iloc[0])
            ks = grouped["log_moneyness"].to_numpy(dtype=float)
            total_variance = (grouped["implied_volatility"].to_numpy(dtype=float) ** 2) * tenor
            if len(ks) < 5:
                blockers.append(
                    DiagnosticMessage(
                        code="option_surface_spline_sample",
                        message=f"Expiry {expiry} needs five nodes for a raw SVI fit.",
                        severity="blocker",
                    )
                )
                continue

            def raw_svi(log_m, level, slope, rho, midpoint, width):
                spread = log_m - midpoint
                return level + slope * (rho * spread + np.sqrt(spread * spread + width * width))

            if float(np.std(total_variance)) < 1e-12:
                fitted = np.full_like(total_variance, float(np.mean(total_variance)))
            else:
                try:
                    fitted_params, _ = curve_fit(
                        raw_svi,
                        ks,
                        total_variance,
                        p0=(float(np.mean(total_variance)), 0.05, 0.0, 0.0, 0.10),
                        bounds=(
                            (0.0, 0.0, -0.999, -2.0, 1e-6),
                            (np.inf, np.inf, 0.999, 2.0, np.inf),
                        ),
                        maxfev=4000,
                    )
                except (RuntimeError, ValueError) as exc:
                    blockers.append(
                        DiagnosticMessage(
                            code="option_surface_svi_fit",
                            message=f"Expiry {expiry} raw SVI fit failed: {exc}",
                            severity="blocker",
                        )
                    )
                    continue
                level, slope, rho, _midpoint, width = (float(value) for value in fitted_params)
                floor = level + slope * width * math.sqrt(max(0.0, 1.0 - rho * rho))
                if floor < -1e-8:
                    blockers.append(
                        DiagnosticMessage(
                            code="option_surface_svi_calendar",
                            message=f"Expiry {expiry} raw SVI violates the Gatheral positivity floor.",
                            severity="blocker",
                            context={"a_plus_b_sigma_sqrt": floor},
                        )
                    )
                fitted = raw_svi(ks, *fitted_params)
            smooth_values = pd.Series(np.sqrt(np.maximum(fitted, 1e-12) / tenor), index=grouped.index)
        elif smoothing_method == "ssvi_total_variance":
            smooth_values = (
                grouped["implied_volatility"]
                .rolling(window=smoothing_window, center=True, min_periods=1)
                .median()
            )
        elif smoothing_method in {"quadratic_total_variance", "cubic_total_variance"}:
            tenor = float(grouped["years_to_expiry"].iloc[0])
            ks = grouped["log_moneyness"].to_numpy(dtype=float)
            total_variance = (grouped["implied_volatility"].to_numpy(dtype=float) ** 2) * tenor
            degree = 3 if smoothing_method == "cubic_total_variance" else 2
            if len(ks) < degree + 1:
                blockers.append(
                    DiagnosticMessage(
                        code="option_surface_spline_sample",
                        message=(
                            f"Expiry {expiry} needs {degree + 1} nodes for a "
                            f"degree-{degree} total-variance fit."
                        ),
                        severity="blocker",
                    )
                )
                continue
            coeffs = np.polyfit(ks, total_variance, deg=degree)
            if degree == 2:
                quadratic, linear, intercept = coeffs
                cubic = 0.0
            else:
                cubic, quadratic, linear, intercept = coeffs
            second_left = 2.0 * quadratic + 6.0 * cubic * float(ks.min())
            second_right = 2.0 * quadratic + 6.0 * cubic * float(ks.max())
            if min(second_left, second_right) < -1e-8:
                blockers.append(
                    DiagnosticMessage(
                        code="option_surface_spline_convexity",
                        message=(f"Expiry {expiry} total-variance fit is not convex on the strike interval."),
                        severity="blocker",
                        context={
                            "second_derivative_left": float(second_left),
                            "second_derivative_right": float(second_right),
                        },
                    )
                )
            fitted = intercept + linear * ks + quadratic * ks * ks + cubic * ks * ks * ks
            smooth_values = pd.Series(np.sqrt(np.maximum(fitted, 1e-12) / tenor), index=grouped.index)
        else:
            smooth_values = (
                grouped["implied_volatility"]
                .rolling(window=smoothing_window, center=True, min_periods=1)
                .median()
            )
        for index, row in grouped.iterrows():
            node_rows.append(
                {
                    "detail_type": "raw_smoothed_node",
                    "expiry_at": expiry,
                    "years_to_expiry": float(row["years_to_expiry"]),
                    "log_moneyness": float(row["log_moneyness"]),
                    "raw_iv": float(row["implied_volatility"]),
                    "smoothed_iv": float(smooth_values.iloc[index]),
                    "quote_count": int(row["quote_count"]),
                }
            )
        if len(grouped) >= 2:
            jumps = np.abs(np.diff(smooth_values.to_numpy(dtype=float)))
            if np.any(jumps > max_iv_jump):
                blockers.append(
                    DiagnosticMessage(
                        code="option_surface_iv_jump",
                        message=f"Expiry {expiry} has an excessive adjacent smoothed IV jump.",
                        severity="blocker",
                        context={"max_jump": float(jumps.max()), "limit": max_iv_jump},
                    )
                )
    observed_expiries = sorted(
        {float(row["years_to_expiry"]) for row in node_rows if row["detail_type"] == "raw_smoothed_node"}
    )
    if len(observed_expiries) < min_expiries:
        blockers.append(
            DiagnosticMessage(
                code="option_surface_insufficient_expiries",
                message="The PIT surface has fewer than the required usable expiries.",
                severity="blocker",
                context={"expiry_count": len(observed_expiries), "required": min_expiries},
            )
        )
    if smoothing_method == "ssvi_total_variance" and len(observed_expiries) >= 2:
        theta_by_tenor = {}
        for tenor in observed_expiries:
            nodes = [row for row in node_rows if row["years_to_expiry"] == tenor]
            atm = min(nodes, key=lambda row: abs(float(row["log_moneyness"])))
            theta_by_tenor[tenor] = max(1e-12, float(atm["smoothed_iv"]) ** 2 * tenor)
        thetas = [theta_by_tenor[tenor] for tenor in observed_expiries]
        if any(later + 1e-12 < earlier for earlier, later in zip(thetas, thetas[1:], strict=False)):
            blockers.append(
                DiagnosticMessage(
                    code="option_surface_ssvi_calendar",
                    message="SSVI ATM total variance decreases across expiries.",
                    severity="blocker",
                    context={"theta": thetas},
                )
            )
        ks = np.array([float(row["log_moneyness"]) for row in node_rows], dtype=float)
        tenors = np.array([float(row["years_to_expiry"]) for row in node_rows], dtype=float)
        weights = np.array(
            [float(row["smoothed_iv"]) ** 2 * float(row["years_to_expiry"]) for row in node_rows],
            dtype=float,
        )
        theta_obs = np.array([theta_by_tenor[float(tenor)] for tenor in tenors], dtype=float)

        def ssvi(log_m, rho, eta):
            phi = eta / np.sqrt(theta_obs)
            return (theta_obs / 2.0) * (
                1.0 + rho * phi * log_m + np.sqrt((phi * log_m + rho) ** 2 + (1.0 - rho * rho))
            )

        try:
            params, _ = curve_fit(
                ssvi,
                ks,
                weights,
                p0=(0.0, 1.0),
                bounds=((-0.999, 1e-6), (0.999, np.inf)),
                maxfev=3000,
            )
            fitted = ssvi(ks, *params)
            for index, row in enumerate(node_rows):
                row["smoothed_iv"] = float(
                    math.sqrt(max(fitted[index], 1e-12) / float(row["years_to_expiry"]))
                )
        except (RuntimeError, ValueError) as exc:
            blockers.append(
                DiagnosticMessage(
                    code="option_surface_ssvi_fit",
                    message=f"SSVI term-structure fit failed: {exc}",
                    severity="blocker",
                )
            )
    by_tenor: dict[float, tuple[np.ndarray, np.ndarray]] = {}
    for tenor in observed_expiries:
        nodes = [row for row in node_rows if row["years_to_expiry"] == tenor]
        by_tenor[tenor] = (
            np.array([row["log_moneyness"] for row in nodes], dtype=float),
            np.array([row["smoothed_iv"] for row in nodes], dtype=float),
        )

    def interpolate_moneyness(tenor: float, target: float) -> float | None:
        xs, ys = by_tenor[tenor]
        if target < xs[0] or target > xs[-1]:
            return None
        position = int(np.searchsorted(xs, target))
        if position == 0:
            return float(ys[0])
        if position == len(xs):
            return float(ys[-1])
        gap = xs[position] - xs[position - 1]
        if gap > max_moneyness_gap:
            return None
        return float(np.interp(target, xs[position - 1 : position + 1], ys[position - 1 : position + 1]))

    target_tenors = (tenor_grid_years or observed_expiries) if observed_expiries else []
    smoothed_details: list[dict[str, Any]] = []
    for target_tenor in target_tenors:
        if target_tenor < observed_expiries[0] or target_tenor > observed_expiries[-1]:
            blockers.append(
                DiagnosticMessage(
                    code="option_surface_term_extrapolation",
                    message="Requested tenor lies outside the observed PIT expiry range.",
                    severity="blocker",
                    context={"target_tenor_years": target_tenor},
                )
            )
            continue
        for target_moneyness in moneyness_grid:
            term_nodes = [
                (tenor, interpolate_moneyness(tenor, target_moneyness)) for tenor in observed_expiries
            ]
            term_nodes = [(tenor, value) for tenor, value in term_nodes if value is not None]
            if not term_nodes:
                blockers.append(
                    DiagnosticMessage(
                        code="option_surface_moneyness_gap",
                        message="Requested moneyness lies outside a bounded observed surface region.",
                        severity="blocker",
                        context={
                            "target_tenor_years": target_tenor,
                            "target_log_moneyness": target_moneyness,
                        },
                    )
                )
                continue
            if len(term_nodes) == 1:
                interpolated_iv = term_nodes[0][1] if target_tenor == term_nodes[0][0] else None
            else:
                tenors = np.array([node[0] for node in term_nodes], dtype=float)
                values = np.array([node[1] for node in term_nodes], dtype=float)
                position = int(np.searchsorted(tenors, target_tenor))
                if position == 0 or position == len(tenors):
                    interpolated_iv = None
                else:
                    gap = tenors[position] - tenors[position - 1]
                    interpolated_iv = (
                        float(
                            np.interp(
                                target_tenor,
                                tenors[position - 1 : position + 1],
                                values[position - 1 : position + 1],
                            )
                        )
                        if gap <= max_tenor_gap_years
                        else None
                    )
                if target_tenor in tenors:
                    interpolated_iv = float(values[np.where(tenors == target_tenor)[0][0]])
            if interpolated_iv is None:
                blockers.append(
                    DiagnosticMessage(
                        code="option_surface_term_gap",
                        message=(
                            "Requested tenor cannot be interpolated without extrapolation or a large gap."
                        ),
                        severity="blocker",
                        context={
                            "target_tenor_years": target_tenor,
                            "target_log_moneyness": target_moneyness,
                        },
                    )
                )
                continue
            smoothed_details.append(
                {
                    "detail_type": "smoothed_surface_node",
                    "target_tenor_years": float(target_tenor),
                    "target_log_moneyness": float(target_moneyness),
                    "smoothed_implied_volatility": interpolated_iv,
                }
            )
    calendar_violations = 0
    butterfly_violations = 0
    if enforce_arbitrage_free and smoothed_details:
        by_moneyness: dict[float, list[dict[str, Any]]] = {}
        by_tenor_nodes: dict[float, list[dict[str, Any]]] = {}
        for node in smoothed_details:
            by_moneyness.setdefault(float(node["target_log_moneyness"]), []).append(node)
            by_tenor_nodes.setdefault(float(node["target_tenor_years"]), []).append(node)
        for moneyness, nodes in by_moneyness.items():
            ordered = sorted(nodes, key=lambda item: float(item["target_tenor_years"]))
            previous_variance: float | None = None
            for node in ordered:
                total_variance = float(node["smoothed_implied_volatility"]) ** 2 * float(
                    node["target_tenor_years"]
                )
                if (
                    previous_variance is not None
                    and total_variance + calendar_variance_tolerance < previous_variance
                ):
                    calendar_violations += 1
                    blockers.append(
                        DiagnosticMessage(
                            code="option_surface_calendar_arbitrage",
                            message="Smoothed total variance decreases across tenors at fixed moneyness.",
                            severity="blocker",
                            context={
                                "target_log_moneyness": moneyness,
                                "previous_total_variance": previous_variance,
                                "total_variance": total_variance,
                            },
                        )
                    )
                previous_variance = total_variance
        for tenor, nodes in by_tenor_nodes.items():
            ordered = sorted(nodes, key=lambda item: float(item["target_log_moneyness"]))
            if len(ordered) < 3:
                continue
            strikes = [spot * math.exp(float(node["target_log_moneyness"])) for node in ordered]
            calls = [
                black_scholes(
                    spot,
                    strike,
                    tenor,
                    float(node["smoothed_implied_volatility"]),
                    risk_free_rate=risk_free_rate,
                    dividend_yield=dividend_yield,
                    option_type="call",
                ).price
                for node, strike in zip(ordered, strikes, strict=True)
            ]
            for index in range(1, len(ordered) - 1):
                left_slope = (calls[index] - calls[index - 1]) / (strikes[index] - strikes[index - 1])
                right_slope = (calls[index + 1] - calls[index]) / (strikes[index + 1] - strikes[index])
                if right_slope + butterfly_convexity_tolerance < left_slope:
                    butterfly_violations += 1
                    blockers.append(
                        DiagnosticMessage(
                            code="option_surface_butterfly_arbitrage",
                            message="Smoothed call prices are not convex in strike at a tenor.",
                            severity="blocker",
                            context={
                                "target_tenor_years": tenor,
                                "target_log_moneyness": float(ordered[index]["target_log_moneyness"]),
                            },
                        )
                    )
    warnings: list[DiagnosticMessage] = []
    if raw_frame["option_type"].nunique() < 2:
        warnings.append(
            DiagnosticMessage(
                code="option_surface_single_side",
                message="Surface contains only calls or only puts; put-call parity is not testable.",
                severity="warning",
            )
        )
    details = node_rows + smoothed_details
    return ArtifactEnvelope(
        artifact_type="option_surface_smooth",
        run_id=run_id,
        producer=ProducerReference(name="option-surface-smooth", version=__version__),
        parameters={
            "underlying_id": underlying_id,
            "venue": venue,
            "evaluated_at": evaluated.isoformat(),
            "spot": spot,
            "risk_free_rate": risk_free_rate,
            "dividend_yield": dividend_yield,
            "min_expiries": min_expiries,
            "min_strikes_per_expiry": min_strikes_per_expiry,
            "moneyness_grid": moneyness_grid,
            "tenor_grid_years": tenor_grid_years,
            "smoothing_window": smoothing_window,
            "smoothing_method": smoothing_method,
            "max_moneyness_gap": max_moneyness_gap,
            "max_tenor_gap_years": max_tenor_gap_years,
            "max_iv_jump": max_iv_jump,
            "enforce_arbitrage_free": enforce_arbitrage_free,
            "calendar_variance_tolerance": calendar_variance_tolerance,
            "butterfly_convexity_tolerance": butterfly_convexity_tolerance,
        },
        summary={
            "quote_at": pd.Timestamp(quote_at).isoformat(),
            "observed_expiry_count": len(observed_expiries),
            "raw_node_count": len(node_rows),
            "smoothed_node_count": len(smoothed_details),
            "calendar_arbitrage_violations": calendar_violations,
            "butterfly_arbitrage_violations": butterfly_violations,
            "blocker_count": len(blockers),
        },
        warnings=warnings,
        blockers=blockers,
        evidence_gaps=[
            _gap(
                "option_surface_smoothing_scope",
                "PIT linear interpolation, rolling-median smoothing, and discrete calendar/butterfly "
                "gates omit a fitted arbitrage-free spline, stochastic rates/dividends/borrow, "
                "American exercise/assignment, and quote depth.",
            )
        ],
        details=details,
        provenance={
            "quote_selection": "latest_common_timestamp_at_or_before_evaluation",
            "surface_coordinates": "log_strike_over_spot_and_years_to_expiry",
            "smoothing": {
                "ssvi_total_variance": "ssvi_power_law_then_bounded_linear_interpolation",
                "raw_svi_total_variance": "raw_svi_total_variance_then_bounded_linear_interpolation",
                "svi_total_variance": "restricted_svi_total_variance_then_bounded_linear_interpolation",
                "cubic_total_variance": "cubic_total_variance_then_bounded_linear_interpolation",
                "quadratic_total_variance": "quadratic_total_variance_then_bounded_linear_interpolation",
            }.get(smoothing_method, "centered_rolling_median_then_bounded_linear_interpolation"),
            "arbitrage_constraints": "calendar_total_variance_and_call_butterfly",
            "live_order_submission": False,
        },
    ).finalize()


@register_diagnostic(
    "option-hedge-replay",
    "option_hedge_replay",
    required_table_types=("option_contracts", "market_quotes", "market_bars"),
    manifest_stage="risk",
    parameter_model=OptionHedgeReplayParameters,
    description="Replay a discrete European delta hedge and attribute realized mark-to-market PnL.",
)
def option_hedge_replay_artifact(
    contracts: pd.DataFrame,
    quotes: pd.DataFrame,
    underlying_bars: pd.DataFrame,
    exercise_events: pd.DataFrame | None = None,
    *,
    option_id: str,
    option_quantity: float,
    risk_free_rate: float = 0.0,
    dividend_yield: float = 0.0,
    transaction_cost_bps: float = 0.0,
    max_spread_fraction: float = 0.20,
    hedge_fill_mode: str = "mid",
    allow_american_exercise: bool = False,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    selected = contracts[contracts["option_id"].astype(str) == option_id].copy()
    if len(selected) != 1:
        raise ValueError(f"option-hedge-replay requires exactly one option_id={option_id!r}.")
    contract = selected.iloc[0]
    exercise_style = str(contract["exercise_style"]).lower()
    if exercise_style not in {"european", "american"}:
        raise ValueError("exercise_style must be European or American.")
    expiry = parse_utc_timestamp(pd.Series([contract["expiry_at"]]), "expiry_at").iloc[0]
    underlying_id = str(contract["underlying_id"])
    venue = str(contract["venue"])
    contract_currency = str(contract["currency"])
    exercise_event: dict[str, Any] | None = None
    if exercise_style == "european":
        if exercise_events is not None and not exercise_events.empty:
            raise ValueError("European option replay cannot consume exercise events.")
    else:
        if not allow_american_exercise:
            raise ValueError("American exercise requires allow_american_exercise=true.")
        if exercise_events is None:
            raise ValueError("American exercise requires a PIT option exercise-event input.")
        events = exercise_events[exercise_events["option_id"].astype(str) == option_id].copy()
        for column in ("event_at", "available_at"):
            events[column] = parse_utc_timestamp(events[column], column)
        events = events[events["available_at"] <= events["event_at"]].sort_values("event_at")
        if len(events) != 1:
            raise ValueError("American replay requires exactly one PIT exercise or assignment event.")
        event = events.iloc[0]
        event_type = str(event["event_type"]).lower()
        event_quantity = float(event["quantity"])
        event_price = float(event["underlying_price"])
        if event_type not in {"exercise", "assignment"}:
            raise ValueError("Option event_type must be exercise or assignment.")
        if (
            event_quantity <= 0
            or not math.isfinite(event_price)
            or event_price <= 0
            or str(event["currency"]) != contract_currency
            or pd.Timestamp(event["event_at"]) >= expiry
        ):
            raise ValueError("American option exercise event terms are invalid.")
        exercise_event = {
            "event_at": pd.Timestamp(event["event_at"]),
            "event_type": event_type,
            "quantity": event_quantity,
            "underlying_price": event_price,
        }
    option_quotes = quotes[
        (quotes["asset_id"].astype(str) == option_id) & (quotes["venue"].astype(str) == venue)
    ].copy()
    bars = underlying_bars[underlying_bars["asset_id"].astype(str) == underlying_id].copy()
    option_quotes["timestamp"] = parse_utc_timestamp(option_quotes["timestamp"], "timestamp")
    bars["timestamp"] = parse_utc_timestamp(bars["timestamp"], "timestamp")
    option_quotes = option_quotes[option_quotes["timestamp"] < expiry]
    observations = option_quotes.merge(
        bars[["timestamp", "close", "currency", "adjustment_state"]],
        on="timestamp",
        how="inner",
        suffixes=("_option", "_underlying"),
        validate="one_to_one",
    ).sort_values("timestamp")
    if len(observations) != len(option_quotes) or len(observations) < 2:
        raise ValueError(
            "option-hedge-replay requires at least two exactly aligned option/spot observations."
        )
    if (
        observations["currency_option"].astype(str).ne(contract_currency).any()
        or observations["currency_underlying"].astype(str).ne(contract_currency).any()
    ):
        raise ValueError("Option, underlying, and quote currencies must match.")
    if observations["adjustment_state"].astype(str).ne("raw").any():
        raise ValueError("option-hedge-replay requires raw underlying bars.")
    for column in ("bid", "ask", "close"):
        observations[column] = pd.to_numeric(observations[column], errors="coerce")
    if observations[["bid", "ask", "close"]].isna().any().any():
        raise ValueError("Option hedge prices must be finite and non-null.")
    if (
        (observations["bid"] <= 0).any()
        or (observations["ask"] < observations["bid"]).any()
        or (observations["close"] <= 0).any()
    ):
        raise ValueError("Option bid/ask and underlying prices are invalid.")
    if hedge_fill_mode not in {"mid", "bid_ask"}:
        raise ValueError("hedge_fill_mode must be 'mid' or 'bid_ask'.")
    if hedge_fill_mode == "bid_ask":
        underlying_quotes = quotes[quotes["asset_id"].astype(str) == underlying_id].copy()
        if underlying_quotes.empty:
            raise ValueError("bid/ask hedge fills require underlying market quotes.")
        underlying_quotes["timestamp"] = parse_utc_timestamp(underlying_quotes["timestamp"], "timestamp")
        venue_matches = underlying_quotes[underlying_quotes["venue"].astype(str) == venue]
        if not venue_matches.empty:
            underlying_quotes = venue_matches
        for column in ("bid", "ask"):
            underlying_quotes[column] = pd.to_numeric(underlying_quotes[column], errors="coerce")
        if (
            underlying_quotes[["bid", "ask"]].isna().any().any()
            or (underlying_quotes["bid"] <= 0).any()
            or (underlying_quotes["ask"] < underlying_quotes["bid"]).any()
        ):
            raise ValueError("Underlying hedge bid/ask quotes are invalid.")
        if underlying_quotes["timestamp"].duplicated().any():
            raise ValueError("Underlying hedge quotes must be unique by timestamp.")
        observations = observations.merge(
            underlying_quotes[["timestamp", "bid", "ask"]].rename(
                columns={"bid": "spot_bid", "ask": "spot_ask"}
            ),
            on="timestamp",
            how="left",
            validate="one_to_one",
        )
        if observations[["spot_bid", "spot_ask"]].isna().any().any():
            raise ValueError("Every hedge observation requires an aligned underlying bid/ask.")
    else:
        observations["spot_bid"] = observations["close"]
        observations["spot_ask"] = observations["close"]
    multiplier = float(contract["multiplier"])
    exercise_event_index: int | None = None
    if exercise_event is not None:
        event_at = pd.Timestamp(exercise_event["event_at"])
        matching = observations.index[observations["timestamp"] == event_at]
        if len(matching) != 1:
            raise ValueError("American exercise event must align exactly to an option/spot observation.")
        exercise_event_index = int(observations.index.get_loc(matching[0]))
        if not math.isclose(
            float(observations.loc[matching[0], "close"]),
            float(exercise_event["underlying_price"]),
            rel_tol=1e-9,
            abs_tol=1e-8,
        ):
            raise ValueError("American exercise event underlying price must match the aligned bar.")
        if not math.isclose(
            float(exercise_event["quantity"]), abs(option_quantity), rel_tol=1e-9, abs_tol=1e-9
        ):
            raise ValueError("Partial American exercise or assignment is not supported by this replay.")
    if multiplier <= 0 or option_quantity == 0 or transaction_cost_bps < 0:
        raise ValueError("Option quantity, multiplier, or transaction cost is invalid.")
    blockers: list[DiagnosticMessage] = []
    analytics_rows: list[dict[str, Any]] = []
    for row in observations.to_dict("records"):
        timestamp = pd.Timestamp(row["timestamp"])
        years = float((expiry - timestamp).total_seconds() / (365.25 * 24 * 3600))
        spot = float(row["close"])
        mid = float((row["bid"] + row["ask"]) / 2.0)
        volatility = implied_volatility(
            mid,
            spot,
            float(contract["strike"]),
            years,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            option_type=cast(OptionType, str(contract["option_type"])),
        )
        analytics = black_scholes(
            spot,
            float(contract["strike"]),
            years,
            volatility,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            option_type=cast(OptionType, str(contract["option_type"])),
        )
        spread_fraction = float((row["ask"] - row["bid"]) / mid)
        if spread_fraction > max_spread_fraction:
            blockers.append(
                DiagnosticMessage(
                    code="option_hedge_spread_limit",
                    message="Option bid/ask spread exceeds the configured replay limit.",
                    severity="blocker",
                    context={
                        "timestamp": timestamp.isoformat(),
                        "spread_fraction": spread_fraction,
                        "limit": max_spread_fraction,
                    },
                )
            )
        analytics_rows.append(
            {
                "timestamp": timestamp,
                "spot": spot,
                "option_mid": mid,
                "spread_fraction": spread_fraction,
                "implied_volatility": volatility,
                "delta": analytics.delta,
                "gamma": analytics.gamma,
                "vega": analytics.vega,
                "theta": analytics.theta,
                "rho": analytics.rho,
                "target_hedge_quantity": -option_quantity * multiplier * analytics.delta,
                "spot_bid": float(row["spot_bid"]),
                "spot_ask": float(row["spot_ask"]),
            }
        )
    if exercise_event_index is not None and exercise_event is not None:
        if exercise_event_index < 1:
            raise ValueError("American exercise event requires at least one prior hedge observation.")
        event_row = analytics_rows[exercise_event_index]
        event_spot = float(event_row["spot"])
        option_type = str(contract["option_type"]).lower()
        intrinsic = (
            max(event_spot - float(contract["strike"]), 0.0)
            if option_type == "call"
            else max(float(contract["strike"]) - event_spot, 0.0)
        )
        event_row["option_mid"] = intrinsic
        event_row["target_hedge_quantity"] = 0.0
        event_row["exercise_event_type"] = exercise_event["event_type"]
        event_row["exercise_intrinsic"] = intrinsic
        analytics_rows = analytics_rows[: exercise_event_index + 1]
    cost_rate = transaction_cost_bps / 10_000.0

    def hedge_fill_cost(quantity_delta: float, row: dict[str, Any]) -> float:
        if quantity_delta == 0:
            return 0.0
        fill_price = float(row["spot_ask"] if quantity_delta > 0 else row["spot_bid"])
        spread_cost = abs(quantity_delta) * abs(fill_price - float(row["spot"]))
        return spread_cost + abs(quantity_delta) * fill_price * cost_rate

    initial_hedge_cost = hedge_fill_cost(
        float(analytics_rows[0]["target_hedge_quantity"]),
        analytics_rows[0],
    )
    details: list[dict[str, Any]] = []
    for index, (start, end) in enumerate(zip(analytics_rows, analytics_rows[1:], strict=False)):
        option_pnl = option_quantity * multiplier * (float(end["option_mid"]) - float(start["option_mid"]))
        hedge_pnl = float(start["target_hedge_quantity"]) * (float(end["spot"]) - float(start["spot"]))
        rebalance_cost = (
            hedge_fill_cost(
                float(end["target_hedge_quantity"]) - float(start["target_hedge_quantity"]),
                end,
            )
            if index < len(analytics_rows) - 2
            else 0.0
        )
        hedge_cost = rebalance_cost + (initial_hedge_cost if index == 0 else 0.0)
        residual = option_pnl + hedge_pnl
        details.append(
            {
                "start_at": pd.Timestamp(start["timestamp"]).isoformat(),
                "end_at": pd.Timestamp(end["timestamp"]).isoformat(),
                "start_spot": float(start["spot"]),
                "end_spot": float(end["spot"]),
                "start_option_mid": float(start["option_mid"]),
                "end_option_mid": float(end["option_mid"]),
                "start_implied_volatility": float(start["implied_volatility"]),
                "end_implied_volatility": float(end["implied_volatility"]),
                "start_delta": float(start["delta"]),
                "end_delta": float(end["delta"]),
                "start_gamma": float(start["gamma"]),
                "end_gamma": float(end["gamma"]),
                "start_vega": float(start["vega"]),
                "end_vega": float(end["vega"]),
                "start_theta": float(start["theta"]),
                "end_theta": float(end["theta"]),
                "hedge_quantity": float(start["target_hedge_quantity"]),
                "option_pnl": option_pnl,
                "hedge_pnl": hedge_pnl,
                "hedge_transaction_cost": hedge_cost,
                "exercise_event_type": end.get("exercise_event_type"),
                "exercise_intrinsic": end.get("exercise_intrinsic"),
                "exercise_settlement_cashflow": (
                    option_quantity * multiplier * float(end["exercise_intrinsic"])
                    if end.get("exercise_intrinsic") is not None
                    else 0.0
                ),
                "delta_hedged_residual_before_cost": residual,
                "net_hedged_pnl": residual - hedge_cost,
            }
        )
    iv_values = [float(row["implied_volatility"]) for row in analytics_rows]
    return ArtifactEnvelope(
        artifact_type="option_hedge_replay",
        run_id=run_id,
        producer=ProducerReference(name="option-hedge-replay", version=__version__),
        parameters={
            "option_id": option_id,
            "option_quantity": option_quantity,
            "risk_free_rate": risk_free_rate,
            "dividend_yield": dividend_yield,
            "transaction_cost_bps": transaction_cost_bps,
            "max_spread_fraction": max_spread_fraction,
            "hedge_fill_mode": hedge_fill_mode,
            "allow_american_exercise": allow_american_exercise,
        },
        summary={
            "underlying_id": underlying_id,
            "observation_count": len(analytics_rows),
            "interval_count": len(details),
            "total_option_pnl": float(sum(row["option_pnl"] for row in details)),
            "total_hedge_pnl": float(sum(row["hedge_pnl"] for row in details)),
            "total_hedge_transaction_cost": float(sum(row["hedge_transaction_cost"] for row in details)),
            "total_net_hedged_pnl": float(sum(row["net_hedged_pnl"] for row in details)),
            "minimum_implied_volatility": min(iv_values),
            "maximum_implied_volatility": max(iv_values),
            "exercise_event_count": int(exercise_event is not None),
            "exercise_event_type": exercise_event["event_type"] if exercise_event else None,
            "exercise_settlement_cashflow": float(
                sum(row["exercise_settlement_cashflow"] for row in details)
            ),
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            _gap(
                "option_hedge_scope",
                "Discrete Black-Scholes delta replay with mid or bid/ask underlying fills omits "
                "cash financing, dividends/corporate-action adjustments, jumps, "
                "volatility-surface interpolation, margin, and option close-out execution.",
            )
        ],
        details=details,
        provenance={
            "pricing_model": (
                "black_scholes_until_american_event_intrinsic_settlement"
                if exercise_event is not None
                else "black_scholes_european"
            ),
            "hedge_timing": "aligned_observation_close",
            "hedge_fill": ("underlying_bid_ask" if hedge_fill_mode == "bid_ask" else "underlying_close_mid"),
            "live_order_submission": False,
        },
    ).finalize()


def _fixed_income_year_fraction(
    start: pd.Timestamp,
    end: pd.Timestamp,
    day_count: str,
) -> float:
    convention = day_count.upper().replace(" ", "")
    if convention in {"ACT/365", "ACT/365F"}:
        return float((end - start).days / 365.0)
    if convention == "ACT/360":
        return float((end - start).days / 360.0)
    if convention in {"30/360", "30/360US"}:
        start_day = min(start.day, 30)
        end_day = min(end.day, 30) if start_day == 30 else end.day
        days = (end.year - start.year) * 360 + (end.month - start.month) * 30 + end_day - start_day
        return float(days / 360.0)
    raise ValueError(f"Unsupported fixed-income day_count {day_count!r}.")


def _adjust_payment_date(
    payment: pd.Timestamp,
    sessions: pd.DatetimeIndex,
    convention: str,
) -> pd.Timestamp:
    normalized = payment.tz_localize(None).normalize()
    rule = convention.lower().replace("-", "_").replace(" ", "_")
    if rule == "unadjusted":
        return normalized
    following = sessions[sessions >= normalized]
    preceding = sessions[sessions <= normalized]
    if rule in {"following", "modified_following"}:
        if following.empty:
            raise ValueError(f"Calendar does not cover following adjustment for {normalized.date()}.")
        adjusted = following[0]
        if rule == "modified_following" and adjusted.month != normalized.month:
            if preceding.empty:
                raise ValueError(f"Calendar does not cover preceding adjustment for {normalized.date()}.")
            adjusted = preceding[-1]
        return adjusted
    if rule == "preceding":
        if preceding.empty:
            raise ValueError(f"Calendar does not cover preceding adjustment for {normalized.date()}.")
        return preceding[-1]
    raise ValueError(f"Unsupported business_day_convention {convention!r}.")


def _coupon_schedule(
    issue: pd.Timestamp,
    maturity: pd.Timestamp,
    frequency: int,
    sessions: pd.DatetimeIndex,
    convention: str,
) -> list[pd.Timestamp]:
    if frequency < 1 or 12 % frequency:
        raise ValueError("coupon_frequency must be a positive divisor of 12.")
    months = 12 // frequency
    preserve_month_end = maturity.is_month_end
    dates = []
    cursor = maturity
    while cursor > issue:
        dates.append(cursor)
        cursor = cursor - pd.DateOffset(months=months)
        if preserve_month_end:
            cursor = cursor + pd.offsets.MonthEnd(0)
    adjusted = sorted({_adjust_payment_date(date, sessions, convention) for date in dates if date > issue})
    if not adjusted:
        raise ValueError("Fixed-income schedule has no coupon/payment dates.")
    return adjusted


@register_diagnostic(
    "fixed-income-price-reconciliation",
    "fixed_income_price_reconciliation",
    required_table_types=(
        "fixed_income_instruments",
        "fixed_income_cashflows",
        "fixed_income_price_quotes",
    ),
    manifest_stage="validation",
    parameter_model=FixedIncomePriceReconciliationParameters,
    description="Reconcile explicit irregular accruals, accrued interest, and clean/dirty prices.",
)
def fixed_income_price_reconciliation_artifact(
    instruments: pd.DataFrame,
    cashflows: pd.DataFrame,
    price_quotes: pd.DataFrame,
    rate_fixings: pd.DataFrame | None = None,
    *,
    instrument_id: str,
    valuation_at: str,
    venue: str | None = None,
    max_quote_age: str = "1D",
    maximum_price_error: float = 1e-8,
    maximum_coupon_error: float = 1e-8,
    require_irregular_stub: bool = False,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    valuation = parse_utc_timestamp(pd.Series([valuation_at]), "valuation_at").iloc[0]
    maximum_age = pd.Timedelta(max_quote_age)
    if maximum_age <= pd.Timedelta(0) or maximum_price_error < 0 or maximum_coupon_error < 0:
        raise ValueError("Fixed-income reconciliation age or error limits are invalid.")
    selected = instruments[instruments["instrument_id"].astype(str) == instrument_id]
    if len(selected) != 1:
        raise ValueError(f"fixed-income-price-reconciliation requires one instrument_id={instrument_id!r}.")
    instrument = selected.iloc[0]
    issue = parse_utc_timestamp(pd.Series([instrument["issue_at"]]), "issue_at").iloc[0]
    maturity = parse_utc_timestamp(pd.Series([instrument["maturity_at"]]), "maturity_at").iloc[0]
    face_value = float(instrument["face_value"])
    coupon_rate = float(instrument["coupon_rate"])
    frequency = int(instrument["coupon_frequency"])
    coupon_type_value = instrument.get("coupon_type", "fixed")
    coupon_type = "fixed" if pd.isna(coupon_type_value) else str(coupon_type_value).lower()
    amortization_value = instrument.get("amortization_type", "bullet")
    amortization_type = "bullet" if pd.isna(amortization_value) else str(amortization_value).lower()
    spread_value = instrument.get("coupon_spread_bps", 0.0)
    coupon_spread_bps = 0.0 if pd.isna(spread_value) else float(spread_value)
    ex_coupon_value = instrument.get("ex_coupon_days", 0)
    ex_coupon_days = 0 if pd.isna(ex_coupon_value) else int(ex_coupon_value)
    if ex_coupon_days < 0 or (not pd.isna(ex_coupon_value) and float(ex_coupon_value) != ex_coupon_days):
        raise ValueError("ex_coupon_days must be a non-negative integer.")
    if coupon_type not in {"fixed", "floating"}:
        raise ValueError("coupon_type must be fixed or floating.")
    if amortization_type not in {"bullet", "scheduled"}:
        raise ValueError("amortization_type must be bullet or scheduled.")
    if (
        face_value <= 0
        or coupon_rate < 0
        or not math.isfinite(coupon_spread_bps)
        or frequency < 1
        or 12 % frequency
        or not issue < maturity
    ):
        raise ValueError("Fixed-income instrument terms are invalid for reconciliation.")
    selected_fixings: pd.DataFrame | None = None
    if coupon_type == "floating":
        if rate_fixings is None:
            raise ValueError("Floating coupons require a PIT fixed-income rate-fixings input.")
        selected_fixings = rate_fixings[rate_fixings["instrument_id"].astype(str) == instrument_id].copy()
        for column in ("reset_at", "available_at"):
            selected_fixings[column] = parse_utc_timestamp(selected_fixings[column], column)
        selected_fixings = selected_fixings[selected_fixings["available_at"] <= valuation].copy()
        if selected_fixings.empty:
            raise ValueError("No PIT floating-coupon rate fixing is available at valuation_at.")
        if selected_fixings["currency"].astype(str).ne(str(instrument["currency"])).any():
            raise ValueError("Instrument and floating rate-fixing currencies must match.")
        selected_fixings["reference_rate"] = pd.to_numeric(
            selected_fixings["reference_rate"], errors="coerce"
        )
        if not np.isfinite(selected_fixings["reference_rate"].to_numpy(dtype=float)).all():
            raise ValueError("Floating-coupon rate fixings must be finite.")
    selected_cashflows = cashflows[cashflows["instrument_id"].astype(str) == instrument_id].copy()
    for column in ("available_at", "accrual_start", "accrual_end", "payment_at"):
        selected_cashflows[column] = parse_utc_timestamp(selected_cashflows[column], column)
    selected_cashflows = selected_cashflows[selected_cashflows["available_at"] <= valuation].sort_values(
        "available_at"
    )
    selected_cashflows = selected_cashflows.drop_duplicates("cashflow_id", keep="last")
    if selected_cashflows.empty:
        raise ValueError("No PIT fixed-income cashflow schedule is available at valuation_at.")
    for column in (
        "coupon_amount",
        "principal_amount",
        "coupon_rate",
        "principal_balance_start",
        "principal_balance_end",
    ):
        if column in selected_cashflows.columns:
            selected_cashflows[column] = pd.to_numeric(selected_cashflows[column], errors="coerce")
    numeric_columns = ["coupon_amount", "principal_amount"]
    for optional_column in ("coupon_rate", "principal_balance_start", "principal_balance_end"):
        if optional_column in selected_cashflows.columns:
            numeric_columns.append(optional_column)
    if not np.isfinite(selected_cashflows[numeric_columns].dropna().to_numpy(dtype=float)).all():
        raise ValueError("Fixed-income cashflows contain non-finite numeric values.")
    if amortization_type == "scheduled" and not {
        "principal_balance_start",
        "principal_balance_end",
    }.issubset(selected_cashflows.columns):
        raise ValueError("Scheduled amortization requires explicit principal balances.")
    if (
        selected_cashflows["coupon_amount"].lt(0).any()
        or selected_cashflows["principal_amount"].lt(0).any()
        or (selected_cashflows["accrual_end"] <= selected_cashflows["accrual_start"]).any()
        or (selected_cashflows["payment_at"] < selected_cashflows["accrual_end"]).any()
    ):
        raise ValueError("Fixed-income cashflows contain invalid dates or amounts.")
    schedule = selected_cashflows.sort_values("accrual_start").reset_index(drop=True)
    if (
        pd.Timestamp(schedule.iloc[0]["accrual_start"]) != issue
        or pd.Timestamp(schedule.iloc[-1]["accrual_end"]) != maturity
        or (
            schedule["accrual_start"].iloc[1:].reset_index(drop=True)
            != schedule["accrual_end"].iloc[:-1].reset_index(drop=True)
        ).any()
    ):
        raise ValueError("Fixed-income cashflow accrual periods must cover issue through maturity.")
    currency = str(instrument["currency"])
    if schedule["currency"].astype(str).ne(currency).any():
        raise ValueError("Instrument and contractual cashflow currencies must match.")
    months = 12 // frequency
    blockers: list[DiagnosticMessage] = []
    cashflow_details = []
    expected_coupon_by_id: dict[str, float] = {}
    irregular_stub_count = 0
    running_balance = face_value
    for row in schedule.itertuples(index=False):
        values = row._asdict()
        accrual_start = pd.Timestamp(values["accrual_start"])
        accrual_end = pd.Timestamp(values["accrual_end"])
        regular_end = accrual_start + pd.DateOffset(months=months)
        if accrual_start.is_month_end:
            regular_end = regular_end + pd.offsets.MonthEnd(0)
        irregular_stub = regular_end.normalize() != accrual_end.normalize()
        irregular_stub_count += int(irregular_stub)
        accrual_fraction = _fixed_income_year_fraction(
            accrual_start,
            accrual_end,
            str(instrument["day_count"]),
        )
        if coupon_type == "floating":
            assert selected_fixings is not None
            eligible_fixings = selected_fixings[selected_fixings["reset_at"] <= accrual_start].sort_values(
                ["reset_at", "available_at"]
            )
            if eligible_fixings.empty:
                raise ValueError(
                    f"No PIT floating rate fixing covers accrual start {accrual_start.isoformat()}."
                )
            fixing = eligible_fixings.iloc[-1]
            reference_rate = float(fixing["reference_rate"])
            effective_coupon_rate = reference_rate + coupon_spread_bps / 10_000.0
        else:
            reference_rate = None
            effective_coupon_rate = coupon_rate
        balance_start_value = values.get("principal_balance_start")
        balance_end_value = values.get("principal_balance_end")
        if pd.isna(balance_start_value):
            balance_start = running_balance
        else:
            balance_start = float(balance_start_value)
        if balance_start < 0 or abs(balance_start - running_balance) > maximum_coupon_error:
            raise ValueError("Fixed-income principal balances are not continuous across periods.")
        expected_coupon = balance_start * effective_coupon_rate * accrual_fraction
        if expected_coupon < 0:
            raise ValueError("Fixed-income effective coupon rate cannot produce a negative coupon.")
        coupon_error = abs(float(values["coupon_amount"]) - expected_coupon)
        expected_balance_end = balance_start - float(values["principal_amount"])
        if pd.isna(balance_end_value):
            balance_end = expected_balance_end
        else:
            balance_end = float(balance_end_value)
        principal_balance_error = abs(balance_end - expected_balance_end)
        if balance_end < 0 or principal_balance_error > maximum_coupon_error:
            blockers.append(
                DiagnosticMessage(
                    code="fixed_income_amortization_balance_mismatch",
                    message="Reported principal balances do not reconcile to principal cashflow.",
                    severity="blocker",
                    context={
                        "cashflow_id": str(values["cashflow_id"]),
                        "balance_start": balance_start,
                        "reported_balance_end": balance_end,
                        "expected_balance_end": expected_balance_end,
                        "error": principal_balance_error,
                    },
                )
            )
        reported_coupon_rate = values.get("coupon_rate")
        coupon_rate_error = None
        if not pd.isna(reported_coupon_rate):
            coupon_rate_error = abs(float(reported_coupon_rate) - effective_coupon_rate)
            if coupon_rate_error > maximum_coupon_error:
                blockers.append(
                    DiagnosticMessage(
                        code="fixed_income_coupon_rate_mismatch",
                        message="Reported coupon rate does not match PIT floating-rate economics.",
                        severity="blocker",
                        context={
                            "cashflow_id": str(values["cashflow_id"]),
                            "reported_coupon_rate": float(reported_coupon_rate),
                            "expected_coupon_rate": effective_coupon_rate,
                            "error": coupon_rate_error,
                        },
                    )
                )
        detail = {
            "detail_type": "cashflow",
            "cashflow_id": str(values["cashflow_id"]),
            "accrual_start": accrual_start.isoformat(),
            "accrual_end": accrual_end.isoformat(),
            "payment_at": pd.Timestamp(values["payment_at"]).isoformat(),
            "irregular_stub": irregular_stub,
            "accrual_year_fraction": accrual_fraction,
            "coupon_type": coupon_type,
            "reference_rate": reference_rate,
            "coupon_spread_bps": coupon_spread_bps,
            "ex_coupon_days": ex_coupon_days,
            "effective_coupon_rate": effective_coupon_rate,
            "expected_coupon_amount": expected_coupon,
            "reported_coupon_amount": float(values["coupon_amount"]),
            "coupon_error": coupon_error,
            "reported_coupon_rate": (None if pd.isna(reported_coupon_rate) else float(reported_coupon_rate)),
            "coupon_rate_error": coupon_rate_error,
            "principal_amount": float(values["principal_amount"]),
            "principal_balance_start": balance_start,
            "principal_balance_end": balance_end,
            "principal_balance_error": principal_balance_error,
        }
        cashflow_details.append(detail)
        expected_coupon_by_id[str(values["cashflow_id"])] = expected_coupon
        running_balance = balance_end
        if coupon_error > maximum_coupon_error:
            blockers.append(
                DiagnosticMessage(
                    code="fixed_income_coupon_amount_mismatch",
                    message="Contractual coupon amount does not match the explicit accrual fraction.",
                    severity="blocker",
                    context=detail,
                )
            )
    if amortization_type == "scheduled" and abs(running_balance) > maximum_coupon_error:
        blockers.append(
            DiagnosticMessage(
                code="fixed_income_amortization_unpaid_balance",
                message="Scheduled amortization does not reduce principal to zero at maturity.",
                severity="blocker",
                context={"ending_balance": running_balance},
            )
        )
    principal_error = abs(float(schedule["principal_amount"].sum()) - face_value)
    if principal_error > maximum_coupon_error:
        blockers.append(
            DiagnosticMessage(
                code="fixed_income_principal_mismatch",
                message="Contractual principal cashflows do not reconcile to face value.",
                severity="blocker",
                context={
                    "reported_principal": float(schedule["principal_amount"].sum()),
                    "face_value": face_value,
                    "error": principal_error,
                },
            )
        )
    if require_irregular_stub and irregular_stub_count == 0:
        blockers.append(
            DiagnosticMessage(
                code="fixed_income_irregular_stub_missing",
                message="The schedule does not contain the required explicit irregular stub.",
                severity="blocker",
            )
        )
    quotes = price_quotes[price_quotes["instrument_id"].astype(str) == instrument_id].copy()
    for column in ("observed_at", "available_at", "settlement_at"):
        quotes[column] = parse_utc_timestamp(quotes[column], column)
    quotes = quotes[(quotes["observed_at"] <= valuation) & (quotes["available_at"] <= valuation)].copy()
    venues = sorted(quotes["venue"].dropna().astype(str).unique())
    if venue is None:
        if len(venues) != 1:
            raise ValueError(f"Select one fixed-income quote venue; available: {venues}")
        venue = venues[0]
    quotes = quotes[quotes["venue"].astype(str) == venue].sort_values("observed_at")
    if quotes.empty:
        raise ValueError(f"No PIT fixed-income quote exists for venue={venue!r}.")
    quote = quotes.iloc[-1]
    for column in ("clean_price", "dirty_price", "accrued_interest"):
        value = float(quote[column])
        if not math.isfinite(value):
            raise ValueError("Fixed-income clean, dirty, and accrued prices must be finite.")
    clean_price = float(quote["clean_price"])
    dirty_price = float(quote["dirty_price"])
    reported_accrued = float(quote["accrued_interest"])
    if clean_price <= 0 or dirty_price <= 0:
        raise ValueError("Fixed-income clean and dirty prices must be positive.")
    if str(quote["currency"]) != currency:
        raise ValueError("Fixed-income quote and instrument currencies must match.")
    settlement = pd.Timestamp(quote["settlement_at"])
    active_period = schedule[
        (schedule["accrual_start"] <= settlement) & (schedule["accrual_end"] > settlement)
    ]
    if len(active_period) != 1:
        raise ValueError("Quote settlement must fall in exactly one explicit accrual period.")
    active = active_period.iloc[0]
    payment_at = pd.Timestamp(active["payment_at"])
    ex_coupon_start = payment_at - pd.Timedelta(days=ex_coupon_days)
    ex_coupon_active = ex_coupon_days > 0 and settlement >= ex_coupon_start and settlement < payment_at
    if reported_accrued < 0 and not ex_coupon_active:
        raise ValueError("Negative accrued interest requires an active declared ex-coupon window.")
    full_fraction = _fixed_income_year_fraction(
        pd.Timestamp(active["accrual_start"]),
        pd.Timestamp(active["accrual_end"]),
        str(instrument["day_count"]),
    )
    elapsed_fraction = _fixed_income_year_fraction(
        pd.Timestamp(active["accrual_start"]),
        settlement,
        str(instrument["day_count"]),
    )
    expected_full_coupon = expected_coupon_by_id[str(active["cashflow_id"])]
    normal_accrued = expected_full_coupon * elapsed_fraction / full_fraction / face_value * 100.0
    computed_accrued = normal_accrued - (
        expected_full_coupon / face_value * 100.0 if ex_coupon_active else 0.0
    )
    quote_age = valuation - pd.Timestamp(quote["observed_at"])
    accrued_error = abs(reported_accrued - computed_accrued)
    dirty_identity_error = abs(dirty_price - clean_price - reported_accrued)
    dirty_computed_error = abs(dirty_price - clean_price - computed_accrued)
    price_detail = {
        "detail_type": "price",
        "observed_at": pd.Timestamp(quote["observed_at"]).isoformat(),
        "settlement_at": settlement.isoformat(),
        "venue": venue,
        "clean_price": clean_price,
        "dirty_price": dirty_price,
        "reported_accrued_interest": reported_accrued,
        "computed_accrued_interest": computed_accrued,
        "accrued_interest_error": accrued_error,
        "dirty_identity_error": dirty_identity_error,
        "dirty_computed_error": dirty_computed_error,
        "quote_age": str(quote_age),
        "ex_coupon_days": ex_coupon_days,
        "ex_coupon_start": ex_coupon_start.isoformat() if ex_coupon_days else None,
        "ex_coupon_active": ex_coupon_active,
        "normal_accrued_interest": normal_accrued,
    }
    for breached, code, message in (
        (
            quote_age > maximum_age,
            "fixed_income_price_quote_stale",
            "Fixed-income price quote exceeds max_quote_age.",
        ),
        (
            accrued_error > maximum_price_error,
            "fixed_income_accrued_mismatch",
            "Reported accrued interest does not match explicit accrual economics.",
        ),
        (
            dirty_identity_error > maximum_price_error or dirty_computed_error > maximum_price_error,
            "fixed_income_clean_dirty_mismatch",
            "Dirty price does not reconcile to clean price plus accrued interest.",
        ),
    ):
        if breached:
            blockers.append(
                DiagnosticMessage(
                    code=code,
                    message=message,
                    severity="blocker",
                    context=price_detail,
                )
            )
    return ArtifactEnvelope(
        artifact_type="fixed_income_price_reconciliation",
        run_id=run_id,
        producer=ProducerReference(
            name="fixed-income-price-reconciliation",
            version=__version__,
        ),
        parameters={
            "instrument_id": instrument_id,
            "valuation_at": valuation.isoformat(),
            "venue": venue,
            "max_quote_age": str(maximum_age),
            "maximum_price_error": maximum_price_error,
            "maximum_coupon_error": maximum_coupon_error,
            "require_irregular_stub": require_irregular_stub,
            "coupon_type": coupon_type,
            "amortization_type": amortization_type,
            "coupon_spread_bps": coupon_spread_bps,
            "ex_coupon_days": ex_coupon_days,
        },
        summary={
            "cashflow_count": len(schedule),
            "irregular_stub_count": irregular_stub_count,
            "principal_error": principal_error,
            "floating_coupon_count": int(coupon_type == "floating") * len(schedule),
            "amortization_type": amortization_type,
            "ending_principal_balance": running_balance,
            "ex_coupon_days": ex_coupon_days,
            "ex_coupon_active": ex_coupon_active,
            "computed_accrued_interest": computed_accrued,
            "accrued_interest_error": accrued_error,
            "dirty_identity_error": dirty_identity_error,
            "dirty_computed_error": dirty_computed_error,
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            _gap(
                "fixed_income_price_reconciliation_scope",
                "Explicit accrual reconciliation omits settlement fails, taxes, withholding, "
                "inflation indexation, optionality, and vendor-specific quote conventions.",
            )
        ],
        details=[*cashflow_details, price_detail],
        provenance={
            "price_quote_basis": "per_100_face",
            "ex_coupon_adjustment": "subtract_full_coupon_after_detachment"
            if ex_coupon_days
            else "not_declared",
            "coupon_calculation": "pit_reference_rate_plus_spread_times_explicit_accrual_balance"
            if coupon_type == "floating"
            else "explicit_coupon_rate_times_accrual_balance",
            "live_order_submission": False,
        },
    ).finalize()


@register_diagnostic(
    "fixed-income-curve-stress",
    "fixed_income_curve_stress",
    required_table_types=("fixed_income_instruments", "yield_curve_nodes", "calendar_sessions"),
    manifest_stage="risk",
    parameter_model=FixedIncomeCurveStressParameters,
    description="Price an exact dated coupon schedule from PIT zero nodes and run key-rate scenarios.",
)
def fixed_income_curve_stress_artifact(
    instruments: pd.DataFrame,
    curve_nodes: pd.DataFrame,
    calendar_sessions: pd.DataFrame,
    *,
    instrument_id: str,
    curve_id: str,
    calendar_id: str,
    valuation_at: str,
    scenarios: list[dict[str, Any]],
    loss_limit_fraction: float = 0.10,
    spread_nodes: pd.DataFrame | None = None,
    spread_curve_id: str | None = None,
    require_spread_curve: bool = False,
    projection_curve_id: str | None = None,
    call_price_per_100: float | None = None,
    call_style: str = "american",
    rate_volatility: float = 0.0,
    market_dirty_price: float | None = None,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    selected = instruments[instruments["instrument_id"].astype(str) == instrument_id]
    if len(selected) != 1:
        raise ValueError(f"fixed-income-curve-stress requires one instrument_id={instrument_id!r}.")
    instrument = selected.iloc[0]
    valuation = parse_utc_timestamp(pd.Series([valuation_at]), "valuation_at").iloc[0]
    issue = parse_utc_timestamp(pd.Series([instrument["issue_at"]]), "issue_at").iloc[0]
    maturity = parse_utc_timestamp(pd.Series([instrument["maturity_at"]]), "maturity_at").iloc[0]
    if not issue < valuation < maturity:
        raise ValueError("Fixed-income valuation must fall strictly between issue and maturity.")
    calendar = calendar_sessions[calendar_sessions["calendar_id"].astype(str) == calendar_id].copy()
    if calendar.empty:
        raise ValueError(f"No calendar sessions exist for calendar_id={calendar_id!r}.")
    sessions = pd.DatetimeIndex(pd.to_datetime(calendar["session"], errors="raise")).normalize()
    sessions = sessions.sort_values().drop_duplicates()
    payment_dates = _coupon_schedule(
        issue,
        maturity,
        int(instrument["coupon_frequency"]),
        sessions,
        str(instrument["business_day_convention"]),
    )
    valuation_date = valuation.tz_localize(None).normalize()
    future_dates = [date for date in payment_dates if date > valuation_date]
    if not future_dates:
        raise ValueError("Fixed-income instrument has no future cashflows at valuation_at.")
    face_value = float(instrument["face_value"])
    coupon_rate = float(instrument["coupon_rate"])
    frequency = int(instrument["coupon_frequency"])
    if face_value <= 0 or coupon_rate < 0:
        raise ValueError("Fixed-income face value must be positive and coupon rate non-negative.")
    coupon = face_value * coupon_rate / frequency
    cashflows = [coupon + (face_value if date == payment_dates[-1] else 0.0) for date in future_dates]
    times = np.array(
        [
            _fixed_income_year_fraction(
                valuation_date,
                date,
                str(instrument["day_count"]),
            )
            for date in future_dates
        ],
        dtype=float,
    )
    curve = curve_nodes[curve_nodes["curve_id"].astype(str) == curve_id].copy()
    curve["observed_at"] = parse_utc_timestamp(curve["observed_at"], "observed_at")
    curve["available_at"] = parse_utc_timestamp(curve["available_at"], "available_at")
    curve = curve[(curve["observed_at"] <= valuation) & (curve["available_at"] <= valuation)]
    if curve.empty:
        raise ValueError("No point-in-time yield curve is available at valuation_at.")
    curve = curve[curve["observed_at"] == curve["observed_at"].max()].copy()
    if curve["currency"].astype(str).nunique() != 1 or str(curve["currency"].iloc[0]) != str(
        instrument["currency"]
    ):
        raise ValueError("Yield curve and instrument currencies must match exactly.")
    if curve["compounding"].astype(str).nunique() != 1:
        raise ValueError("Select one curve compounding convention.")
    compounding = str(curve["compounding"].iloc[0])
    if compounding not in {"continuous", "annual"}:
        raise ValueError("Curve compounding must be continuous or annual.")
    curve["tenor_years"] = pd.to_numeric(curve["tenor_years"], errors="coerce")
    curve["zero_rate"] = pd.to_numeric(curve["zero_rate"], errors="coerce")
    curve = curve.sort_values("tenor_years")
    tenors = curve["tenor_years"].to_numpy(dtype=float)
    rates = curve["zero_rate"].to_numpy(dtype=float)
    if (
        len(tenors) < 2
        or not np.isfinite(tenors).all()
        or not np.isfinite(rates).all()
        or (tenors <= 0).any()
        or (np.diff(tenors) <= 0).any()
        or times.min() < tenors.min()
        or times.max() > tenors.max()
    ):
        raise ValueError("Yield nodes must be finite, increasing, and bracket every cashflow tenor.")

    if require_spread_curve and spread_curve_id is None:
        raise ValueError("require_spread_curve requires spread_curve_id.")
    spread_curve_observed_at: pd.Timestamp | None = None
    spread_tenors = np.array([], dtype=float)
    spread_bps = np.array([], dtype=float)
    if spread_nodes is None:
        if spread_curve_id is not None or require_spread_curve:
            raise ValueError("A requested spread curve has no declared spread-node input.")
        interpolated_spread_bps = np.zeros_like(times)
    else:
        if spread_curve_id is None:
            raise ValueError("spread_nodes requires an explicit spread_curve_id.")
        spread = spread_nodes[
            (spread_nodes["spread_curve_id"].astype(str) == spread_curve_id)
            & (spread_nodes["instrument_id"].astype(str) == instrument_id)
        ].copy()
        spread["observed_at"] = parse_utc_timestamp(spread["observed_at"], "observed_at")
        spread["available_at"] = parse_utc_timestamp(spread["available_at"], "available_at")
        spread = spread[(spread["observed_at"] <= valuation) & (spread["available_at"] <= valuation)].copy()
        if spread.empty:
            raise ValueError("No point-in-time spread curve is available at valuation_at.")
        spread_curve_observed_at = pd.Timestamp(spread["observed_at"].max())
        spread = spread[spread["observed_at"] == spread_curve_observed_at].copy()
        if spread["currency"].astype(str).nunique() != 1 or str(spread["currency"].iloc[0]) != str(
            instrument["currency"]
        ):
            raise ValueError("Spread curve and instrument currencies must match exactly.")
        spread["tenor_years"] = pd.to_numeric(spread["tenor_years"], errors="coerce")
        spread["spread_bps"] = pd.to_numeric(spread["spread_bps"], errors="coerce")
        spread = spread.sort_values("tenor_years")
        spread_tenors = spread["tenor_years"].to_numpy(dtype=float)
        spread_bps = spread["spread_bps"].to_numpy(dtype=float)
        if (
            len(spread_tenors) < 2
            or not np.isfinite(spread_tenors).all()
            or not np.isfinite(spread_bps).all()
            or (spread_tenors <= 0).any()
            or (np.diff(spread_tenors) <= 0).any()
            or times.min() < spread_tenors.min()
            or times.max() > spread_tenors.max()
        ):
            raise ValueError(
                "Spread nodes must be finite, increasing, and bracket every cashflow tenor; "
                "spread extrapolation is prohibited."
            )
        interpolated_spread_bps = np.interp(times, spread_tenors, spread_bps)

    interpolated_zero_rates = np.interp(times, tenors, rates)
    raw_coupon_type = instrument["coupon_type"] if "coupon_type" in instrument.index else None
    coupon_type = str(raw_coupon_type).lower() if pd.notna(raw_coupon_type) else "fixed"
    if coupon_type not in {"fixed", "floating"}:
        raise ValueError("coupon_type must be fixed or floating.")
    if coupon_type == "floating":
        if projection_curve_id is None:
            raise ValueError("Floating coupons require projection_curve_id.")
        projection = curve_nodes[curve_nodes["curve_id"].astype(str) == projection_curve_id].copy()
        projection["observed_at"] = parse_utc_timestamp(projection["observed_at"], "observed_at")
        projection["available_at"] = parse_utc_timestamp(projection["available_at"], "available_at")
        projection = projection[
            (projection["observed_at"] <= valuation) & (projection["available_at"] <= valuation)
        ]
        if projection.empty:
            raise ValueError("No point-in-time projection curve is available at valuation_at.")
        projection = projection[projection["observed_at"] == projection["observed_at"].max()].copy()
        if str(projection["compounding"].iloc[0]) != compounding:
            raise ValueError("Projection and discount curves must share compounding.")
        projection["tenor_years"] = pd.to_numeric(projection["tenor_years"], errors="coerce")
        projection["zero_rate"] = pd.to_numeric(projection["zero_rate"], errors="coerce")
        projection = projection.sort_values("tenor_years")
        proj_tenors = projection["tenor_years"].to_numpy(dtype=float)
        proj_rates = projection["zero_rate"].to_numpy(dtype=float)
        if (
            times.min() < proj_tenors.min()
            or times.max() > proj_tenors.max()
            or (np.diff(proj_tenors) <= 0).any()
        ):
            raise ValueError("Projection nodes must bracket every cashflow tenor.")

        def projection_df(tenor: float) -> float:
            rate = float(np.interp(tenor, proj_tenors, proj_rates))
            if compounding == "continuous":
                return math.exp(-rate * tenor)
            if rate <= -1:
                raise ValueError("Projection zero rates must exceed -1.")
            return float((1.0 + rate) ** (-tenor))

        raw_spread = instrument["coupon_spread_bps"] if "coupon_spread_bps" in instrument.index else 0.0
        coupon_spread = float(raw_spread or 0.0) / 10_000.0
        previous_time = 0.0
        projected = []
        for index, tenor in enumerate(times):
            year_frac = float(tenor - previous_time)
            forward = (projection_df(previous_time) / projection_df(float(tenor)) - 1.0) / year_frac
            amount = face_value * (forward + coupon_spread) * year_frac
            if index == len(times) - 1:
                amount += face_value
            projected.append(amount)
            previous_time = float(tenor)
        cashflows = projected
    elif projection_curve_id is not None:
        raise ValueError("projection_curve_id is only valid for floating coupons.")

    option_adjusted_spread = 0.0

    def price(node_rates: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
        interpolated = (
            np.interp(times, tenors, node_rates) + interpolated_spread_bps / 10_000.0 + option_adjusted_spread
        )
        if compounding == "continuous":
            discounts = np.exp(-interpolated * times)
        else:
            if (interpolated <= -1).any():
                raise ValueError("Annual-compounded zero rates must exceed -1.")
            discounts = np.power(1.0 + interpolated, -times)
        present_values = np.asarray(cashflows, dtype=float) * discounts
        dirty = float(present_values.sum())
        if call_price_per_100 is not None:
            if call_style not in {"american", "bermudan"}:
                raise ValueError("call_style must be american or bermudan.")
            cap = call_price_per_100 / 100.0 * face_value
            if call_style == "bermudan":
                value = float(cashflows[-1])
                for index in range(len(times) - 2, -1, -1):
                    dt = float(times[index + 1] - times[index])
                    base_step = float(discounts[index + 1] / discounts[index])
                    if rate_volatility > 0 and dt > 0:
                        shock = rate_volatility * math.sqrt(dt)
                        step_up = base_step * math.exp(-shock * dt)
                        step_down = base_step * math.exp(shock * dt)
                        hold_up = float(cashflows[index]) + step_up * value
                        hold_down = float(cashflows[index]) + step_down * value
                        value = 0.5 * (min(hold_up, cap) + min(hold_down, cap))
                    else:
                        hold = float(cashflows[index]) + base_step * value
                        value = min(hold, cap)
                dirty = float(discounts[0] * value)
            elif dirty > cap:
                dirty = cap
        return dirty, interpolated, present_values

    base_price, interpolated_rates, present_values = price(rates)
    if market_dirty_price is not None:
        if market_dirty_price <= 0:
            raise ValueError("market_dirty_price must be positive.")

        def price_gap(spread: float) -> float:
            return price(rates + spread)[0] - market_dirty_price

        lower, upper = -0.10, 0.10
        lower_gap, upper_gap = price_gap(lower), price_gap(upper)
        if lower_gap * upper_gap > 0:
            raise ValueError("No option-adjusted spread brackets the market dirty price.")
        option_adjusted_spread = float(brentq(price_gap, lower, upper))
        base_price, interpolated_rates, present_values = price(rates)
    up_one_price, _, _ = price(rates + 0.0001)
    dv01 = base_price - up_one_price
    modified_duration = dv01 / (base_price * 0.0001) if base_price > 0 else None
    scenario_details = []
    scenario_losses: list[float] = []
    blockers: list[DiagnosticMessage] = []
    for scenario in scenarios:
        shocked = rates + float(scenario.get("parallel_bps", 0.0)) / 10_000.0
        for tenor_text, shock_bps in scenario.get("node_shocks_bps", {}).items():
            tenor = float(tenor_text)
            matching = np.flatnonzero(np.isclose(tenors, tenor, rtol=0, atol=1e-12))
            if len(matching) != 1:
                raise ValueError(
                    f"Curve scenario {scenario['name']!r} references missing tenor {tenor_text!r}."
                )
            shocked[matching[0]] += float(shock_bps) / 10_000.0
        scenario_price, _, _ = price(shocked)
        pnl = scenario_price - base_price
        loss_fraction = max(0.0, -pnl / base_price)
        detail = {
            "scenario": str(scenario["name"]),
            "price": scenario_price,
            "pnl": pnl,
            "loss_fraction": loss_fraction,
            "limit": loss_limit_fraction,
            "breach": loss_fraction > loss_limit_fraction,
        }
        scenario_details.append(detail)
        scenario_losses.append(loss_fraction)
        if detail["breach"]:
            blockers.append(
                DiagnosticMessage(
                    code="fixed_income_curve_loss_limit",
                    message=f"Curve scenario {scenario['name']!r} exceeds the configured loss limit.",
                    severity="blocker",
                    context=detail,
                )
            )
    cashflow_details = [
        {
            "payment_date": date.date().isoformat(),
            "year_fraction": float(times[index]),
            "cashflow": float(cashflows[index]),
            "zero_rate": float(interpolated_zero_rates[index]),
            "spread_bps": float(interpolated_spread_bps[index]),
            "discount_rate": float(interpolated_rates[index]),
            "present_value": float(present_values[index]),
        }
        for index, date in enumerate(future_dates)
    ]
    return ArtifactEnvelope(
        artifact_type="fixed_income_curve_stress",
        run_id=run_id,
        producer=ProducerReference(name="fixed-income-curve-stress", version=__version__),
        parameters={
            "instrument_id": instrument_id,
            "curve_id": curve_id,
            "calendar_id": calendar_id,
            "valuation_at": valuation.isoformat(),
            "scenarios": scenarios,
            "loss_limit_fraction": loss_limit_fraction,
            "spread_curve_id": spread_curve_id,
            "require_spread_curve": require_spread_curve,
            "projection_curve_id": projection_curve_id,
            "call_price_per_100": call_price_per_100,
            "call_style": call_style,
            "rate_volatility": rate_volatility,
            "market_dirty_price": market_dirty_price,
        },
        summary={
            "curve_observed_at": pd.Timestamp(curve["observed_at"].iloc[0]).isoformat(),
            "spread_curve_observed_at": (
                spread_curve_observed_at.isoformat() if spread_curve_observed_at is not None else None
            ),
            "spread_node_count": len(spread_tenors),
            "cashflow_count": len(cashflow_details),
            "dirty_price": base_price,
            "oas_bps": option_adjusted_spread * 10_000.0,
            "coupon_type": coupon_type,
            "embedded_option_exercised": (
                call_price_per_100 is not None and base_price == call_price_per_100 / 100.0 * face_value
            ),
            "parallel_dv01": dv01,
            "modified_duration": modified_duration,
            "worst_scenario_loss_fraction": max(scenario_losses, default=None),
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            _gap(
                "fixed_income_curve_scope",
                "Dated contractual cashflows, optional projection-curve floating forwards, and a "
                "single American-style call cap omit Bermudan schedules, full OAS calibration, "
                "credit migration/default, liquidity, taxes, and settlement execution.",
            )
        ],
        details=[
            *({"detail_type": "cashflow", **detail} for detail in cashflow_details),
            *({"detail_type": "scenario", **detail} for detail in scenario_details),
        ],
        provenance={
            "curve_interpolation": "linear_zero_rate",
            "spread_curve_interpolation": "linear_bps" if spread_curve_id is not None else None,
            "curve_extrapolation": False,
            "spread_curve_extrapolation": False,
            "floating_projection": "simple_forward_from_projection_zeros",
            "embedded_option": (
                "bermudan_two_state_rate_tree"
                if call_style == "bermudan" and rate_volatility > 0
                else "bermudan_coupon_date_call"
                if call_style == "bermudan"
                else "dirty_price_call_cap"
            ),
            "oas_solver": "brentq_parallel_zero_spread",
            "live_order_submission": False,
        },
    ).finalize()


@register_diagnostic(
    "fixed-income-shock",
    "fixed_income_risk",
    required_table_types=("fixed_income_instruments",),
    manifest_stage="risk",
    parameter_model=FixedIncomeRiskParameters,
    description="Reconstruct level-coupon cashflows and report parallel-yield shock risk.",
)
def fixed_income_risk_artifact(
    instruments: pd.DataFrame,
    *,
    valuation_at: str,
    yield_rate: float,
    instrument_id: str | None = None,
    parallel_shock_bps: float = 100.0,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    instruments = instruments.copy()
    if instrument_id is not None:
        instruments = instruments[instruments["instrument_id"].astype(str) == instrument_id]
    if instruments.empty:
        raise ValueError("fixed-income-shock selected no instruments.")
    if parallel_shock_bps <= 0:
        raise ValueError("parallel_shock_bps must be positive.")
    valuation = parse_utc_timestamp(pd.Series([valuation_at]), "valuation_at").iloc[0]
    instruments["maturity_at"] = parse_utc_timestamp(instruments["maturity_at"], "maturity_at")
    details: list[dict[str, Any]] = []
    shock = parallel_shock_bps / 10_000.0
    for row in instruments.to_dict("records"):
        years = float((pd.Timestamp(row["maturity_at"]) - valuation).total_seconds() / (365.25 * 86400))
        if years <= 0:
            raise ValueError(f"Instrument {row['instrument_id']} is mature at valuation_at.")
        frequency = int(row["coupon_frequency"])
        if frequency <= 0:
            raise ValueError("coupon_frequency must be positive.")
        face = float(row["face_value"])
        coupon = face * float(row["coupon_rate"]) / frequency
        count = max(1, math.ceil(years * frequency))
        times = years - np.arange(count - 1, -1, -1, dtype=float) / frequency
        times = times[times > 0]
        cashflows: np.ndarray = np.full(len(times), coupon, dtype=float)
        cashflows[-1] += face
        base = price_cashflows(times, cashflows, yield_rate=yield_rate, compounding_frequency=frequency)
        up = price_cashflows(
            times,
            cashflows,
            yield_rate=yield_rate + shock,
            compounding_frequency=frequency,
        )
        down = price_cashflows(
            times,
            cashflows,
            yield_rate=yield_rate - shock,
            compounding_frequency=frequency,
        )
        details.append(
            {
                "instrument_id": str(row["instrument_id"]),
                "currency": str(row["currency"]),
                "maturity_at": pd.Timestamp(row["maturity_at"]).isoformat(),
                "cashflow_count": len(times),
                "price": base.price,
                "macaulay_duration": base.macaulay_duration,
                "modified_duration": base.modified_duration,
                "convexity": base.convexity,
                "up_shock_price": up.price,
                "down_shock_price": down.price,
                "up_shock_return": up.price / base.price - 1.0,
                "down_shock_return": down.price / base.price - 1.0,
            }
        )
    return ArtifactEnvelope(
        artifact_type="fixed_income_risk",
        run_id=run_id,
        producer=ProducerReference(name="fixed-income-shock", version=__version__),
        parameters={
            "instrument_id": instrument_id,
            "valuation_at": valuation.isoformat(),
            "yield_rate": yield_rate,
            "parallel_shock_bps": parallel_shock_bps,
        },
        summary={
            "instrument_count": len(details),
            "total_price": sum(row["price"] for row in details),
            "worst_up_shock_return": min(row["up_shock_return"] for row in details),
        },
        evidence_gaps=[
            _gap(
                "fixed_income_schedule_scope",
                "Evenly spaced level-coupon reconstruction omits exact day-count/accrual "
                "calendars, optionality, curve nodes, credit migration, liquidity, and settlement.",
            )
        ],
        details=details,
        provenance={"shock_type": "parallel_yield", "live_order_submission": False},
    ).finalize()


@register_diagnostic(
    "fx-rollover",
    "fx_rollover",
    required_table_types=("fx_quotes",),
    manifest_stage="research",
    parameter_model=FXRolloverParameters,
    description="Compute covered-interest-parity rollover levels from explicit quote direction and rates.",
)
def fx_rollover_artifact(
    quotes: pd.DataFrame,
    *,
    base_rate: float,
    quote_rate: float,
    tenor_days: int,
    base_currency: str | None = None,
    quote_currency: str | None = None,
    notional_base: float = 1.0,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if tenor_days <= 0 or notional_base <= 0:
        raise ValueError("tenor_days and notional_base must be positive.")
    quotes, base_currency = _select_one(quotes.copy(), "base_currency", base_currency, "fx-rollover")
    quotes, quote_currency = _select_one(quotes, "quote_currency", quote_currency, "fx-rollover")
    if base_currency == quote_currency:
        raise ValueError("FX base and quote currencies must differ.")
    quotes["timestamp"] = parse_utc_timestamp(quotes["timestamp"], "timestamp")
    latest = quotes["timestamp"].max()
    selected = quotes[quotes["timestamp"] == latest].copy()
    selected["bid"] = pd.to_numeric(selected["bid"], errors="coerce")
    selected["ask"] = pd.to_numeric(selected["ask"], errors="coerce")
    if selected[["bid", "ask"]].isna().any().any() or (selected["bid"] <= 0).any():
        raise ValueError("FX quotes must contain finite positive bid and ask values.")
    if (selected["ask"] < selected["bid"]).any():
        raise ValueError("FX ask cannot be below bid.")
    years = tenor_days / 365.0
    details = []
    for row in selected.to_dict("records"):
        mid = (float(row["bid"]) + float(row["ask"])) / 2.0
        forward = fx_forward_outright(
            mid,
            base_rate=base_rate,
            quote_rate=quote_rate,
            time_years=years,
        )
        details.append(
            {
                "venue": str(row["venue"]),
                "spot_mid": mid,
                "spot_spread": float(row["ask"]) - float(row["bid"]),
                "forward_outright": forward,
                "forward_points": forward - mid,
                "rollover_quote_cashflow": (forward - mid) * notional_base,
            }
        )
    return ArtifactEnvelope(
        artifact_type="fx_rollover",
        run_id=run_id,
        producer=ProducerReference(name="fx-rollover", version=__version__),
        parameters={
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "base_rate": base_rate,
            "quote_rate": quote_rate,
            "tenor_days": tenor_days,
            "notional_base": notional_base,
        },
        summary={
            "quote_at": pd.Timestamp(latest).isoformat(),
            "venue_count": len(details),
            "mean_forward_points": float(np.mean([row["forward_points"] for row in details])),
        },
        evidence_gaps=[
            _gap(
                "fx_rollover_scope",
                "CIP diagnostics omit holiday-adjusted value dates, cross-currency basis, "
                "forward bid/ask, funding limits, and settlement risk.",
            )
        ],
        details=details,
        provenance={"quote_direction": "quote_per_base", "live_order_submission": False},
    ).finalize()


def _fx_joint_value_dates(
    calendar_sessions: pd.DataFrame,
    *,
    base_calendar_id: str,
    quote_calendar_id: str,
    trade_date: pd.Timestamp,
    settlement_lag_business_days: int,
    tenor_days: int,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    base_sessions = pd.DatetimeIndex(
        pd.to_datetime(
            calendar_sessions[calendar_sessions["calendar_id"].astype(str) == base_calendar_id]["session"],
            errors="raise",
        )
    ).normalize()
    quote_sessions = pd.DatetimeIndex(
        pd.to_datetime(
            calendar_sessions[calendar_sessions["calendar_id"].astype(str) == quote_calendar_id]["session"],
            errors="raise",
        )
    ).normalize()
    joint = base_sessions.intersection(quote_sessions).sort_values().drop_duplicates()
    if joint.empty:
        raise ValueError("Base and quote calendars have no joint settlement sessions.")
    normalized_trade = trade_date.tz_localize(None).normalize()
    if settlement_lag_business_days == 0:
        candidates = joint[joint >= normalized_trade]
        index = 0
    else:
        candidates = joint[joint > normalized_trade]
        index = settlement_lag_business_days - 1
    if len(candidates) <= index:
        raise ValueError("Joint calendars do not cover the configured spot settlement lag.")
    spot_date = candidates[index]
    forward_candidates = joint[joint >= spot_date + pd.Timedelta(days=tenor_days)]
    if forward_candidates.empty:
        raise ValueError("Joint calendars do not cover the holiday-adjusted forward value date.")
    return spot_date, forward_candidates[0]


@register_diagnostic(
    "fx-forward-check",
    "fx_forward_check",
    required_table_types=("fx_quotes", "fx_forward_quotes", "calendar_sessions"),
    manifest_stage="research",
    parameter_model=FXForwardCheckParameters,
    description="Check holiday-adjusted executable forwards against basis-adjusted covered parity.",
)
def fx_forward_check_artifact(
    spot_quotes: pd.DataFrame,
    forward_quotes: pd.DataFrame,
    calendar_sessions: pd.DataFrame,
    *,
    base_currency: str,
    quote_currency: str,
    base_calendar_id: str,
    quote_calendar_id: str,
    base_rate: float,
    quote_rate: float,
    base_rate_bid: float | None = None,
    base_rate_ask: float | None = None,
    quote_rate_bid: float | None = None,
    quote_rate_ask: float | None = None,
    tenor_days: int,
    cross_currency_basis_bps: float = 0.0,
    settlement_lag_business_days: int = 2,
    notional_base: float = 1.0,
    deviation_tolerance_bps: float = 5.0,
    allow_broken_date_interpolation: bool = False,
    cls_cutoff_utc: str | None = None,
    enforce_cls_cutoff: bool = False,
    maximum_funding_notional: float | None = None,
    cls_member_venues: list[str] | None = None,
    nostro_capacity_base: float | None = None,
    settlement_fail_probability: float = 0.0,
    settlement_fail_lgd: float = 1.0,
    settlement_fail_loss_limit: float | None = None,
    settlement_side: str = "buy_base",
    require_replacement_cost: bool = False,
    replacement_evaluated_at: str | None = None,
    replacement_quotes: pd.DataFrame | None = None,
    spot_venue: str | None = None,
    forward_venue: str | None = None,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    if (
        base_currency == quote_currency
        or tenor_days < 1
        or settlement_lag_business_days < 0
        or notional_base <= 0
        or deviation_tolerance_bps < 0
        or (maximum_funding_notional is not None and maximum_funding_notional <= 0)
        or not 0 <= settlement_fail_probability <= 1
        or not 0 <= settlement_fail_lgd <= 1
        or (settlement_fail_loss_limit is not None and settlement_fail_loss_limit < 0)
    ):
        raise ValueError("FX forward currencies, tenor, settlement lag, or limits are invalid.")
    spots = spot_quotes[
        (spot_quotes["base_currency"].astype(str) == base_currency)
        & (spot_quotes["quote_currency"].astype(str) == quote_currency)
    ].copy()
    spots, spot_venue = _select_one(spots, "venue", spot_venue, "fx-forward-check")
    spots["timestamp"] = parse_utc_timestamp(spots["timestamp"], "timestamp")
    spot_at = spots["timestamp"].max()
    spot = spots[spots["timestamp"] == spot_at]
    if len(spot) != 1:
        raise ValueError("fx-forward-check requires one latest spot quote.")
    spot_row = spot.iloc[0]
    spot_bid = float(spot_row["bid"])
    spot_ask = float(spot_row["ask"])
    if spot_bid <= 0 or spot_ask < spot_bid:
        raise ValueError("FX spot bid/ask is invalid.")
    missed_cls_cutoff = False
    if cls_cutoff_utc is not None:
        parts = cls_cutoff_utc.split(":")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("cls_cutoff_utc must be HH:MM.")
        cutoff_minutes = int(parts[0]) * 60 + int(parts[1])
        if not 0 <= cutoff_minutes <= 23 * 60 + 59:
            raise ValueError("cls_cutoff_utc must be a valid UTC clock time.")
        trade = pd.Timestamp(spot_at)
        if trade.tzinfo is None:
            raise ValueError("FX spot timestamp must include an explicit timezone.")
        trade_utc = trade.tz_convert("UTC")
        trade_minutes = trade_utc.hour * 60 + trade_utc.minute
        missed_cls_cutoff = trade_minutes > cutoff_minutes
    expected_spot_date, expected_forward_date = _fx_joint_value_dates(
        calendar_sessions,
        base_calendar_id=base_calendar_id,
        quote_calendar_id=quote_calendar_id,
        trade_date=pd.Timestamp(spot_at),
        settlement_lag_business_days=settlement_lag_business_days,
        tenor_days=tenor_days,
    )
    quoted_spot_date = (
        parse_utc_timestamp(
            pd.Series([spot_row["spot_date"]]),
            "spot_date",
        )
        .iloc[0]
        .tz_localize(None)
        .normalize()
    )
    if quoted_spot_date != expected_spot_date:
        raise ValueError("FX spot quote value date does not match the joint-calendar settlement convention.")
    forwards = forward_quotes[
        (forward_quotes["base_currency"].astype(str) == base_currency)
        & (forward_quotes["quote_currency"].astype(str) == quote_currency)
    ].copy()
    forwards, forward_venue = _select_one(
        forwards,
        "venue",
        forward_venue,
        "fx-forward-check",
    )
    forwards["timestamp"] = parse_utc_timestamp(forwards["timestamp"], "timestamp")
    forwards["value_date_parsed"] = pd.to_datetime(
        forwards["value_date"],
        errors="raise",
    ).dt.normalize()
    forwards = forwards[(forwards["timestamp"] <= spot_at)]
    if forwards.empty:
        raise ValueError("No observable forward quotes precede the spot timestamp.")
    forwards = forwards[forwards["timestamp"] == forwards["timestamp"].max()]
    forwards = forwards.drop_duplicates(subset="value_date_parsed", keep="last")
    if (expected_forward_date in forwards["value_date_parsed"].to_numpy()) and len(
        forwards[forwards["value_date_parsed"] == expected_forward_date]
    ) == 1:
        forward_row = forwards[forwards["value_date_parsed"] == expected_forward_date].iloc[0]
        interpolation = None
    else:
        if not allow_broken_date_interpolation:
            raise ValueError("No observable forward quote matches the holiday-adjusted value date.")
        bracketing = forwards.sort_values("value_date_parsed")
        earlier = bracketing[bracketing["value_date_parsed"] < expected_forward_date]
        later = bracketing[bracketing["value_date_parsed"] > expected_forward_date]
        if earlier.empty or later.empty:
            raise ValueError("Broken-date interpolation requires quotes bracketing the value date.")
        before = earlier.iloc[-1]
        after = later.iloc[0]
        x0 = float((before["value_date_parsed"] - expected_spot_date).days)
        x1 = float((after["value_date_parsed"] - expected_spot_date).days)
        x = float((expected_forward_date - expected_spot_date).days)
        weight = (x - x0) / (x1 - x0)

        def interpolate(row_pair: str) -> float:
            y0 = float(before[row_pair])
            y1 = float(after[row_pair])
            return y0 + weight * (y1 - y0)

        forward_row = pd.Series(
            {
                "bid": interpolate("bid"),
                "ask": interpolate("ask"),
                "quote_type": before["quote_type"],
                "value_date": before["value_date"],
                "value_date_parsed": expected_forward_date,
            }
        )
        interpolation = {
            "before_value_date": before["value_date_parsed"].date().isoformat(),
            "after_value_date": after["value_date_parsed"].date().isoformat(),
            "weight": weight,
        }
    quoted_bid = float(forward_row["bid"])
    quoted_ask = float(forward_row["ask"])
    if quoted_ask < quoted_bid:
        raise ValueError("FX forward ask cannot be below bid.")
    quote_type = str(forward_row["quote_type"])
    if quote_type == "outright":
        forward_bid, forward_ask = quoted_bid, quoted_ask
    elif quote_type == "points":
        forward_bid, forward_ask = spot_bid + quoted_bid, spot_ask + quoted_ask
    else:
        raise ValueError("FX forward quote_type must be outright or points.")
    if forward_bid <= 0 or forward_ask < forward_bid:
        raise ValueError("FX forward outright bid/ask is invalid.")
    years = (expected_forward_date - expected_spot_date).days / 365.0
    rate_bid_ask_available = all(
        value is not None for value in (base_rate_bid, base_rate_ask, quote_rate_bid, quote_rate_ask)
    )
    if rate_bid_ask_available:
        # Forward bid = spot bid * exp((quote_bid - base_ask + basis) * t)
        # Forward ask = spot ask * exp((quote_ask - base_bid + basis) * t)
        quote_rate_bid_v = cast(float, quote_rate_bid)
        quote_rate_ask_v = cast(float, quote_rate_ask)
        base_rate_bid_v = cast(float, base_rate_bid)
        base_rate_ask_v = cast(float, base_rate_ask)
        carry_bid_rate = quote_rate_bid_v - base_rate_ask_v + cross_currency_basis_bps / 10_000.0
        carry_ask_rate = quote_rate_ask_v - base_rate_bid_v + cross_currency_basis_bps / 10_000.0
        theoretical_bid = spot_bid * math.exp(carry_bid_rate * years)
        theoretical_ask = spot_ask * math.exp(carry_ask_rate * years)
        if theoretical_ask < theoretical_bid:
            raise ValueError("Rate bid/ask cannot invert the theoretical forward quote.")
        rate_quote_mode = "bid_ask"
    else:
        carry_rate = quote_rate - base_rate + cross_currency_basis_bps / 10_000.0
        carry_factor = math.exp(carry_rate * years)
        theoretical_bid = spot_bid * carry_factor
        theoretical_ask = spot_ask * carry_factor
        rate_quote_mode = "mid"
    spot_mid = (spot_bid + spot_ask) / 2.0
    forward_mid = (forward_bid + forward_ask) / 2.0
    theoretical_mid = (theoretical_bid + theoretical_ask) / 2.0
    deviation_bps = (forward_mid / theoretical_mid - 1.0) * 10_000.0
    implied_basis_bps = (math.log(forward_mid / spot_mid) / years - (quote_rate - base_rate)) * 10_000.0
    blockers = []
    if abs(deviation_bps) > deviation_tolerance_bps:
        blockers.append(
            DiagnosticMessage(
                code="fx_forward_deviation_limit",
                message="Observed forward midpoint deviates beyond the basis-adjusted CIP tolerance.",
                severity="blocker",
                context={
                    "deviation_bps": deviation_bps,
                    "tolerance_bps": deviation_tolerance_bps,
                },
            )
        )
    if enforce_cls_cutoff and missed_cls_cutoff:
        blockers.append(
            DiagnosticMessage(
                code="fx_cls_cutoff",
                message="Spot timestamp is after the configured CLS cutoff.",
                severity="blocker",
                context={
                    "spot_at": pd.Timestamp(spot_at).isoformat(),
                    "cls_cutoff_utc": cls_cutoff_utc,
                },
            )
        )
    if maximum_funding_notional is not None and notional_base > maximum_funding_notional:
        blockers.append(
            DiagnosticMessage(
                code="fx_funding_limit",
                message="Forward notional exceeds the configured funding limit.",
                severity="blocker",
                context={
                    "notional_base": notional_base,
                    "limit": maximum_funding_notional,
                },
            )
        )
    cls_member_venues = cls_member_venues or []
    if cls_member_venues and spot_venue not in cls_member_venues:
        blockers.append(
            DiagnosticMessage(
                code="fx_cls_membership",
                message="Spot venue is not on the configured CLS membership list.",
                severity="blocker",
                context={"spot_venue": spot_venue, "cls_member_venues": cls_member_venues},
            )
        )
    if nostro_capacity_base is not None and notional_base > nostro_capacity_base:
        blockers.append(
            DiagnosticMessage(
                code="fx_nostro_limit",
                message="Forward notional exceeds the configured nostro capacity.",
                severity="blocker",
                context={
                    "notional_base": notional_base,
                    "limit": nostro_capacity_base,
                },
            )
        )
    if settlement_side not in {"buy_base", "sell_base"}:
        raise ValueError("settlement_side must be buy_base or sell_base.")
    replacement_cost_quote = 0.0
    replacement_cost_base = 0.0
    replacement_expected_loss = 0.0
    replacement_quote_at: str | None = None
    replacement_available_at: str | None = None
    if require_replacement_cost:
        if replacement_quotes is None:
            blockers.append(
                DiagnosticMessage(
                    code="fx_replacement_cost_data",
                    message="Replacement-cost mode requires a PIT fx_replacement_quotes input.",
                    severity="blocker",
                )
            )
        else:
            replacement_at = (
                parse_utc_timestamp(
                    pd.Series([replacement_evaluated_at]),
                    "replacement_evaluated_at",
                ).iloc[0]
                if replacement_evaluated_at is not None
                else pd.Timestamp(expected_forward_date).tz_localize("UTC")
            )
            replacement = replacement_quotes[
                (replacement_quotes["base_currency"].astype(str) == base_currency)
                & (replacement_quotes["quote_currency"].astype(str) == quote_currency)
            ].copy()
            replacement, _ = _select_one(
                replacement,
                "venue",
                forward_venue,
                "fx-forward-check replacement-cost",
            )
            replacement["observed_at"] = parse_utc_timestamp(replacement["observed_at"], "observed_at")
            replacement["available_at"] = parse_utc_timestamp(replacement["available_at"], "available_at")
            replacement["value_date_parsed"] = pd.to_datetime(
                replacement["value_date"], errors="raise"
            ).dt.normalize()
            replacement = replacement[
                (replacement["available_at"] <= replacement_at)
                & (replacement["value_date_parsed"] == expected_forward_date)
            ].sort_values(["available_at", "observed_at"])
            if replacement.empty:
                blockers.append(
                    DiagnosticMessage(
                        code="fx_replacement_cost_pit",
                        message="No PIT replacement quote is available for the forward value date.",
                        severity="blocker",
                        context={"evaluated_at": replacement_at.isoformat()},
                    )
                )
            else:
                replacement_row = replacement.iloc[-1]
                replacement_bid = float(replacement_row["bid"])
                replacement_ask = float(replacement_row["ask"])
                if replacement_bid <= 0 or replacement_ask < replacement_bid:
                    raise ValueError("FX replacement bid/ask is invalid.")
                adverse_rate = replacement_ask if settlement_side == "buy_base" else replacement_bid
                rate_move = (
                    adverse_rate - forward_mid
                    if settlement_side == "buy_base"
                    else forward_mid - adverse_rate
                )
                replacement_cost_quote = notional_base * max(0.0, rate_move)
                replacement_cost_base = replacement_cost_quote / max(
                    (replacement_bid + replacement_ask) / 2.0, 1e-12
                )
                replacement_expected_loss = (
                    replacement_cost_base * settlement_fail_probability * settlement_fail_lgd
                )
                replacement_quote_at = pd.Timestamp(replacement_row["observed_at"]).isoformat()
                replacement_available_at = pd.Timestamp(replacement_row["available_at"]).isoformat()
    settlement_fail_loss = notional_base * settlement_fail_probability * settlement_fail_lgd
    settlement_fail_total_loss = settlement_fail_loss + replacement_expected_loss
    if settlement_fail_loss_limit is not None and settlement_fail_total_loss > settlement_fail_loss_limit:
        blockers.append(
            DiagnosticMessage(
                code="fx_settlement_fail_credit",
                message="Expected settlement-fail loss exceeds the configured credit limit.",
                severity="blocker",
                context={
                    "expected_loss": settlement_fail_loss,
                    "limit": settlement_fail_loss_limit,
                },
            )
        )
    details = [
        {
            "spot_venue": spot_venue,
            "forward_venue": forward_venue,
            "spot_at": pd.Timestamp(spot_at).isoformat(),
            "spot_value_date": expected_spot_date.date().isoformat(),
            "forward_value_date": expected_forward_date.date().isoformat(),
            "year_fraction": years,
            "spot_bid": spot_bid,
            "spot_ask": spot_ask,
            "forward_bid": forward_bid,
            "forward_ask": forward_ask,
            "theoretical_forward_bid": theoretical_bid,
            "theoretical_forward_ask": theoretical_ask,
            "forward_points_mid": forward_mid - spot_mid,
            "implied_cross_currency_basis_bps": implied_basis_bps,
            "deviation_bps": deviation_bps,
            "rate_quote_mode": rate_quote_mode,
            "rollover_quote_cashflow": (forward_mid - spot_mid) * notional_base,
            "replacement_cost_quote": replacement_cost_quote,
            "replacement_cost_base": replacement_cost_base,
            "replacement_expected_loss": replacement_expected_loss,
            "replacement_quote_at": replacement_quote_at,
            "replacement_available_at": replacement_available_at,
        }
    ]
    return ArtifactEnvelope(
        artifact_type="fx_forward_check",
        run_id=run_id,
        producer=ProducerReference(name="fx-forward-check", version=__version__),
        parameters={
            "base_currency": base_currency,
            "quote_currency": quote_currency,
            "base_calendar_id": base_calendar_id,
            "quote_calendar_id": quote_calendar_id,
            "base_rate": base_rate,
            "quote_rate": quote_rate,
            "base_rate_bid": base_rate_bid,
            "base_rate_ask": base_rate_ask,
            "quote_rate_bid": quote_rate_bid,
            "quote_rate_ask": quote_rate_ask,
            "cross_currency_basis_bps": cross_currency_basis_bps,
            "tenor_days": tenor_days,
            "settlement_lag_business_days": settlement_lag_business_days,
            "notional_base": notional_base,
            "deviation_tolerance_bps": deviation_tolerance_bps,
            "allow_broken_date_interpolation": allow_broken_date_interpolation,
            "cls_cutoff_utc": cls_cutoff_utc,
            "enforce_cls_cutoff": enforce_cls_cutoff,
            "maximum_funding_notional": maximum_funding_notional,
            "cls_member_venues": cls_member_venues,
            "nostro_capacity_base": nostro_capacity_base,
            "settlement_fail_probability": settlement_fail_probability,
            "settlement_fail_lgd": settlement_fail_lgd,
            "settlement_fail_loss_limit": settlement_fail_loss_limit,
            "settlement_side": settlement_side,
            "require_replacement_cost": require_replacement_cost,
            "replacement_evaluated_at": replacement_evaluated_at,
            "spot_venue": spot_venue,
            "forward_venue": forward_venue,
        },
        summary={
            "spot_value_date": expected_spot_date.date().isoformat(),
            "forward_value_date": expected_forward_date.date().isoformat(),
            "forward_spread": forward_ask - forward_bid,
            "rate_quote_mode": rate_quote_mode,
            "implied_cross_currency_basis_bps": implied_basis_bps,
            "deviation_bps": deviation_bps,
            "broken_date_interpolation": interpolation,
            "missed_cls_cutoff": missed_cls_cutoff,
            "funding_utilization": (
                notional_base / maximum_funding_notional if maximum_funding_notional is not None else None
            ),
            "settlement_fail_loss": settlement_fail_loss,
            "replacement_cost_quote": replacement_cost_quote,
            "replacement_cost_base": replacement_cost_base,
            "replacement_expected_loss": replacement_expected_loss,
            "replacement_quote_at": replacement_quote_at,
            "replacement_available_at": replacement_available_at,
            "settlement_fail_total_loss": settlement_fail_total_loss,
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            _gap(
                "fx_forward_check_scope",
                "Joint-session adjustment, executable quote bounds, rate-curve bid/ask, "
                "broken-date interpolation, UTC CLS cutoff, venue membership, and notional "
                "nostro/funding caps omit live nostro ledgers and live order submission.",
            )
        ],
        details=details,
        provenance={
            "quote_direction": "quote_per_base",
            "forward_points_unit": "quote_currency_per_base_currency",
            "basis_sign": "added_to_quote_minus_base_continuous_rate",
            "cls_cutoff": "utc_clock_time",
            "cls_membership": "configured_venue_allowlist",
            "funding_limit": "notional_cap",
            "nostro_limit": "base_notional_cap",
            "settlement_fail": "notional_times_probability_times_lgd",
            "replacement_cost": (
                "adverse_pit_bid_ask_replacement_quote" if require_replacement_cost else "not_requested"
            ),
            "live_order_submission": False,
        },
    ).finalize()


def _crypto_margin_tier_snapshot(
    tiers: pd.DataFrame,
    *,
    instrument_id: str,
    evaluated_at: pd.Timestamp,
) -> pd.DataFrame:
    selected = tiers[tiers["instrument_id"].astype(str) == instrument_id].copy()
    selected["effective_from"] = parse_utc_timestamp(selected["effective_from"], "effective_from")
    selected["available_at"] = parse_utc_timestamp(selected["available_at"], "available_at")
    selected = selected[
        (selected["effective_from"] <= evaluated_at) & (selected["available_at"] <= evaluated_at)
    ]
    if selected.empty:
        raise ValueError(f"No PIT margin tiers are available for {instrument_id!r}.")
    selected = selected[selected["effective_from"] == selected["effective_from"].max()].copy()
    if "notional_cap" not in selected:
        selected["notional_cap"] = pd.Series(float("nan"), index=selected.index, dtype=float)
    for column in (
        "notional_floor",
        "notional_cap",
        "initial_margin_rate",
        "maintenance_margin_rate",
        "liquidation_fee_rate",
    ):
        selected[column] = pd.to_numeric(selected[column], errors="coerce")
    selected = selected.sort_values("notional_floor").reset_index(drop=True)
    required_numeric = [
        "notional_floor",
        "initial_margin_rate",
        "maintenance_margin_rate",
        "liquidation_fee_rate",
    ]
    if selected[required_numeric].isna().any().any() or float(selected.loc[0, "notional_floor"]) != 0.0:
        raise ValueError(f"Margin tiers for {instrument_id!r} must start at zero notional.")
    for index, row in selected.iterrows():
        floor = float(row["notional_floor"])
        cap = float(row["notional_cap"]) if pd.notna(row["notional_cap"]) else None
        initial_rate = float(row["initial_margin_rate"])
        maintenance_rate = float(row["maintenance_margin_rate"])
        fee_rate = float(row["liquidation_fee_rate"])
        if (
            floor < 0
            or (cap is not None and cap <= floor)
            or not 0 < maintenance_rate <= initial_rate < 1
            or fee_rate < 0
        ):
            raise ValueError(f"Margin tier values for {instrument_id!r} are invalid.")
        if index < len(selected) - 1:
            next_floor = float(selected.loc[index + 1, "notional_floor"])
            if cap is None or not math.isclose(cap, next_floor, rel_tol=0, abs_tol=1e-12):
                raise ValueError(f"Margin tiers for {instrument_id!r} must be contiguous.")
        elif cap is not None:
            raise ValueError(f"Final margin tier for {instrument_id!r} must have no cap.")
    return selected


def _crypto_tiered_charge(
    tiers: pd.DataFrame,
    notional: float,
    rate_column: str,
) -> float:
    charge = 0.0
    for _, tier in tiers.iterrows():
        floor = float(tier["notional_floor"])
        cap = float(tier["notional_cap"]) if pd.notna(tier["notional_cap"]) else math.inf
        if notional <= floor:
            break
        band = min(notional, cap) - floor
        if band <= 0:
            continue
        charge += band * float(tier[rate_column])
    return charge


@register_diagnostic(
    "crypto-cross-margin-stress",
    "crypto_cross_margin_stress",
    required_table_types=(
        "crypto_instruments",
        "crypto_positions",
        "market_quotes",
        "crypto_margin_tiers",
    ),
    manifest_stage="risk",
    parameter_model=CryptoCrossMarginParameters,
    description="Stress tiered cross-margin equity and model insurance-fund/ADL liquidation waterfall.",
)
def crypto_cross_margin_stress_artifact(
    instruments: pd.DataFrame,
    positions: pd.DataFrame,
    quotes: pd.DataFrame,
    margin_tiers: pd.DataFrame,
    *,
    venue: str,
    account_id: str,
    evaluated_at: str,
    initial_collateral: float,
    collateral_haircut: float = 0.0,
    collateral_fx_rates: dict[str, float] | None = None,
    insurance_fund: float = 0.0,
    venue_default_recovery_rate: float = 0.0,
    venue_default_loss_limit_fraction: float = 0.20,
    funding_rates: dict[str, float] | None = None,
    stress_shocks: list[float] | None = None,
    adl_ranking: str = "pnl_leverage",
    liquidation_mode: str = "all_or_nothing",
    order_book_impact_bps: float = 0.0,
    intraday_path: list[float] | None = None,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    funding_rates = funding_rates or {}
    collateral_fx_rates = collateral_fx_rates or {}
    shocks = stress_shocks or [-0.30, -0.10, 0.10]
    if (
        initial_collateral <= 0
        or not 0 <= collateral_haircut < 1
        or any(rate <= 0 for rate in collateral_fx_rates.values())
        or insurance_fund < 0
        or not 0 <= venue_default_recovery_rate <= 1
        or venue_default_loss_limit_fraction <= 0
        or order_book_impact_bps < 0
        or not shocks
        or any(shock <= -1 for shock in shocks)
        or adl_ranking not in {"pnl_leverage", "unrealized_pnl"}
        or liquidation_mode not in {"all_or_nothing", "sequential"}
    ):
        raise ValueError("Crypto cross-margin collateral, recovery, limit, or shocks are invalid.")
    evaluated = parse_utc_timestamp(pd.Series([evaluated_at]), "evaluated_at").iloc[0]
    selected_positions = positions[
        (positions["venue"].astype(str) == venue) & (positions["account_id"].astype(str) == account_id)
    ].copy()
    selected_positions["observed_at"] = parse_utc_timestamp(
        selected_positions["observed_at"],
        "observed_at",
    )
    selected_positions["available_at"] = parse_utc_timestamp(
        selected_positions["available_at"],
        "available_at",
    )
    selected_positions = selected_positions[
        (selected_positions["observed_at"] <= evaluated) & (selected_positions["available_at"] <= evaluated)
    ]
    if selected_positions.empty:
        raise ValueError("No point-in-time crypto positions are available for the account.")
    selected_positions = selected_positions[
        selected_positions["observed_at"] == selected_positions["observed_at"].max()
    ].copy()
    selected_positions["signed_quantity"] = pd.to_numeric(
        selected_positions["signed_quantity"], errors="coerce"
    )
    selected_positions["entry_price"] = pd.to_numeric(selected_positions["entry_price"], errors="coerce")
    if (
        selected_positions[["signed_quantity", "entry_price"]].isna().any().any()
        or selected_positions["signed_quantity"].eq(0).any()
        or (selected_positions["entry_price"] <= 0).any()
    ):
        raise ValueError("Crypto positions require nonzero quantities and positive entry prices.")
    instrument_ids = set(selected_positions["instrument_id"].astype(str))
    unknown_funding = sorted(set(funding_rates) - instrument_ids)
    if unknown_funding:
        raise ValueError(f"funding_rates references instruments outside the account: {unknown_funding}")
    selected_instruments = instruments[
        (instruments["venue"].astype(str) == venue)
        & instruments["instrument_id"].astype(str).isin(instrument_ids)
    ].copy()
    if set(selected_instruments["instrument_id"].astype(str)) != instrument_ids:
        raise ValueError("Crypto position instruments are missing canonical terms.")
    if selected_instruments["margin_mode"].astype(str).ne("cross").any():
        raise ValueError("crypto-cross-margin-stress requires cross margin instruments.")
    if selected_instruments["collateral_asset"].astype(str).nunique() != 1:
        raise ValueError("Cross-margin positions must share one collateral asset.")
    collateral_asset = str(selected_instruments["collateral_asset"].iloc[0])
    quote_assets = set(selected_instruments["quote_asset"].astype(str))
    missing_fx = sorted(
        asset for asset in quote_assets if asset != collateral_asset and asset not in collateral_fx_rates
    )
    if missing_fx:
        raise ValueError(f"collateral_fx_rates is missing quote assets: {missing_fx}")
    unknown_fx = sorted(set(collateral_fx_rates) - quote_assets)
    if unknown_fx:
        raise ValueError(f"collateral_fx_rates references unknown quote assets: {unknown_fx}")
    selected_quotes = quotes[
        (quotes["venue"].astype(str) == venue) & quotes["asset_id"].astype(str).isin(instrument_ids)
    ].copy()
    selected_quotes["timestamp"] = parse_utc_timestamp(selected_quotes["timestamp"], "timestamp")
    selected_quotes = selected_quotes[selected_quotes["timestamp"] <= evaluated]
    selected_quotes = selected_quotes.sort_values("timestamp").groupby("asset_id", sort=False).tail(1)
    if set(selected_quotes["asset_id"].astype(str)) != instrument_ids:
        raise ValueError("Every cross-margin position requires an observable mark quote.")
    for column in ("bid", "ask"):
        selected_quotes[column] = pd.to_numeric(selected_quotes[column], errors="coerce")
    if "volume" not in selected_quotes:
        if order_book_impact_bps > 0:
            raise ValueError("Crypto order-book impact requires positive market quote volume.")
        selected_quotes["volume"] = float("inf")
    else:
        selected_quotes["volume"] = pd.to_numeric(selected_quotes["volume"], errors="coerce")
    if (
        selected_quotes[["bid", "ask", "volume"]].isna().any().any()
        or (selected_quotes["bid"] <= 0).any()
        or (selected_quotes["ask"] < selected_quotes["bid"]).any()
        or (selected_quotes["volume"] <= 0).any()
    ):
        raise ValueError("Crypto mark quotes require valid bid/ask and positive volume.")
    terms = selected_positions.merge(
        selected_instruments[["instrument_id", "multiplier", "quote_asset", "collateral_asset"]],
        on="instrument_id",
        how="left",
        validate="one_to_one",
    ).merge(
        selected_quotes[["asset_id", "bid", "ask", "volume", "currency"]],
        left_on="instrument_id",
        right_on="asset_id",
        how="left",
        validate="one_to_one",
    )
    if (terms["quote_asset"].astype(str) != terms["currency"].astype(str)).any():
        raise ValueError("Crypto quote currencies must match canonical instrument quote assets.")
    terms["multiplier"] = pd.to_numeric(terms["multiplier"], errors="coerce")
    terms["volume"] = pd.to_numeric(terms["volume"], errors="coerce")
    if (
        terms["multiplier"].isna().any()
        or (terms["multiplier"] <= 0).any()
        or terms["volume"].isna().any()
        or (terms["volume"] <= 0).any()
    ):
        raise ValueError("Crypto contract multipliers must be finite and positive.")
    terms["mark"] = (terms["bid"] + terms["ask"]) / 2.0
    tier_snapshots = {
        instrument_id: _crypto_margin_tier_snapshot(
            margin_tiers[
                (margin_tiers["venue"].astype(str) == venue)
                & (margin_tiers["instrument_id"].astype(str) == instrument_id)
            ],
            instrument_id=instrument_id,
            evaluated_at=evaluated,
        )
        for instrument_id in sorted(instrument_ids)
    }
    available_collateral = initial_collateral * (1.0 - collateral_haircut)

    def to_collateral(amount: float, quote_asset: str) -> float:
        if quote_asset == collateral_asset:
            return amount
        return amount * float(collateral_fx_rates[quote_asset])

    def evaluate(
        shock: float,
        quantity_override: dict[str, float] | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        active_mode = mode or liquidation_mode
        total_pnl = 0.0
        total_funding = 0.0
        maintenance = 0.0
        liquidation_fees = 0.0
        gross_notional = 0.0
        liquidation_impact_cost = 0.0
        position_scores: list[dict[str, Any]] = []
        for row in terms.to_dict("records"):
            instrument_id = str(row["instrument_id"])
            quote_asset = str(row["quote_asset"])
            stressed_mark = float(row["mark"]) * (1.0 + shock)
            quantity = (
                quantity_override[instrument_id]
                if quantity_override is not None and instrument_id in quantity_override
                else float(row["signed_quantity"])
            )
            if quantity == 0:
                continue
            multiplier = float(row["multiplier"])
            notional = to_collateral(abs(quantity) * multiplier * stressed_mark, quote_asset)
            pnl = to_collateral(
                quantity * multiplier * (stressed_mark - float(row["entry_price"])),
                quote_asset,
            )
            funding = to_collateral(
                -(quantity * multiplier * stressed_mark * float(funding_rates.get(instrument_id, 0.0))),
                quote_asset,
            )
            gross_notional += notional
            total_pnl += pnl
            total_funding += funding
            tiers = tier_snapshots[instrument_id]
            quote_notional = abs(quantity) * multiplier * stressed_mark
            participation = abs(quantity) / float(row["volume"])
            impact_bps = order_book_impact_bps * min(participation, 1.0)
            liquidation_price = stressed_mark * (1.0 - math.copysign(impact_bps / 10_000.0, quantity))
            position_liquidation_impact = to_collateral(
                quantity * multiplier * (liquidation_price - stressed_mark),
                quote_asset,
            )
            position_maintenance = to_collateral(
                _crypto_tiered_charge(tiers, quote_notional, "maintenance_margin_rate"),
                quote_asset,
            )
            position_fee = to_collateral(
                _crypto_tiered_charge(tiers, quote_notional, "liquidation_fee_rate"),
                quote_asset,
            )
            maintenance += position_maintenance
            liquidation_fees += position_fee
            position_scores.append(
                {
                    "instrument_id": instrument_id,
                    "signed_quantity": quantity,
                    "notional": notional,
                    "unrealized_pnl": pnl,
                    "maintenance": position_maintenance,
                    "liquidation_fee": position_fee,
                    "order_book_participation": participation,
                    "liquidation_impact_bps": impact_bps,
                    "liquidation_impact_cost": position_liquidation_impact,
                }
            )
        equity = available_collateral + total_pnl + total_funding
        liquidation_sequence: list[str] = []
        remaining_maintenance = maintenance
        remaining_equity = equity
        applied_fees = 0.0
        applied_impact = 0.0
        if equity < maintenance:
            if active_mode == "all_or_nothing":
                liquidation_sequence = [str(item["instrument_id"]) for item in position_scores]
                applied_fees = liquidation_fees
                applied_impact = sum(float(item["liquidation_impact_cost"]) for item in position_scores)
                liquidation_impact_cost = applied_impact
                remaining_maintenance = 0.0
                remaining_equity = equity - applied_fees + applied_impact
            else:
                ordered = sorted(
                    position_scores,
                    key=lambda item: (
                        float(item["unrealized_pnl"]),
                        -float(item["notional"]),
                        str(item["instrument_id"]),
                    ),
                )
                for item in ordered:
                    if remaining_equity >= remaining_maintenance:
                        break
                    remaining_equity -= float(item["liquidation_fee"])
                    item_impact = float(item["liquidation_impact_cost"])
                    remaining_equity += item_impact
                    applied_impact += item_impact
                    liquidation_impact_cost += item_impact
                    remaining_maintenance = max(0.0, remaining_maintenance - float(item["maintenance"]))
                    applied_fees += float(item["liquidation_fee"])
                    liquidation_sequence.append(str(item["instrument_id"]))
        liquidated = bool(liquidation_sequence)
        residual_breach = remaining_equity < remaining_maintenance
        if active_mode == "all_or_nothing" and liquidated:
            shortfall = max(0.0, maintenance + liquidation_fees - applied_impact - equity)
        else:
            shortfall = max(0.0, remaining_maintenance - remaining_equity) if residual_breach else 0.0
        insurance_used = min(insurance_fund, shortfall)
        socialized_loss = shortfall - insurance_used
        equity_base = equity if equity > 0 else initial_collateral
        profitable = []
        for position in position_scores:
            leverage = float(position["notional"]) / equity_base
            score = (
                float(position["unrealized_pnl"]) * leverage
                if adl_ranking == "pnl_leverage"
                else float(position["unrealized_pnl"])
            )
            if position["unrealized_pnl"] > 0:
                profitable.append(
                    {
                        **position,
                        "effective_leverage": leverage,
                        "adl_score": score,
                    }
                )
        profitable.sort(key=lambda item: (-float(item["adl_score"]), str(item["instrument_id"])))
        for rank, position in enumerate(profitable, start=1):
            position["adl_rank"] = rank
        return {
            "detail_type": "price_stress",
            "shock": shock,
            "gross_notional": gross_notional,
            "unrealized_pnl": total_pnl,
            "funding_cashflow": total_funding,
            "equity": equity,
            "maintenance_requirement": maintenance,
            "liquidation_fees": applied_fees,
            "liquidation_impact_cost": liquidation_impact_cost,
            "liquidated": liquidated,
            "liquidation_mode": active_mode,
            "liquidation_sequence": liquidation_sequence,
            "remaining_maintenance": remaining_maintenance,
            "remaining_equity": remaining_equity,
            "waterfall_shortfall": shortfall,
            "insurance_fund_used": insurance_used,
            "socialized_loss": socialized_loss,
            "adl_required": socialized_loss > 0,
            "adl_queue": profitable,
        }

    details = [evaluate(shock) for shock in shocks]
    path = list(intraday_path or [])
    live_quantities = {
        str(row["instrument_id"]): float(row["signed_quantity"]) for row in terms.to_dict("records")
    }
    for index, shock in enumerate(path):
        snap = evaluate(shock, quantity_override=live_quantities, mode="sequential")
        snap["detail_type"] = "intraday_print"
        snap["print_index"] = index
        for instrument_id in snap["liquidation_sequence"]:
            live_quantities[instrument_id] = 0.0
        snap["remaining_quantities"] = dict(live_quantities)
        details.append(snap)
    current = evaluate(0.0)
    recoverable_equity = max(0.0, float(current["equity"]))
    default_recovery = recoverable_equity * venue_default_recovery_rate
    default_loss = recoverable_equity - default_recovery
    default_loss_fraction = default_loss / initial_collateral
    details.append(
        {
            "detail_type": "venue_default",
            "pre_default_equity": recoverable_equity,
            "recovery_rate": venue_default_recovery_rate,
            "recovered_equity": default_recovery,
            "default_loss": default_loss,
            "default_loss_fraction": default_loss_fraction,
            "limit": venue_default_loss_limit_fraction,
            "breach": default_loss_fraction > venue_default_loss_limit_fraction,
        }
    )
    blockers: list[DiagnosticMessage] = []
    for detail in details:
        if detail["detail_type"] in {"price_stress", "intraday_print"} and detail["liquidated"]:
            blockers.append(
                DiagnosticMessage(
                    code="crypto_cross_margin_liquidation",
                    message="A cross-margin price stress breaches maintenance margin.",
                    severity="blocker",
                    context=detail,
                )
            )
            if detail["adl_required"]:
                blockers.append(
                    DiagnosticMessage(
                        code="crypto_adl_required",
                        message="Liquidation shortfall exceeds the configured insurance fund.",
                        severity="blocker",
                        context=detail,
                    )
                )
        if detail["detail_type"] == "venue_default" and detail["breach"]:
            blockers.append(
                DiagnosticMessage(
                    code="crypto_venue_default_loss_limit",
                    message="Venue-default recovery loss exceeds the configured account limit.",
                    severity="blocker",
                    context=detail,
                )
            )
    stress_details = [detail for detail in details if detail["detail_type"] == "price_stress"]
    return ArtifactEnvelope(
        artifact_type="crypto_cross_margin_stress",
        run_id=run_id,
        producer=ProducerReference(name="crypto-cross-margin-stress", version=__version__),
        parameters={
            "venue": venue,
            "account_id": account_id,
            "evaluated_at": evaluated.isoformat(),
            "initial_collateral": initial_collateral,
            "collateral_haircut": collateral_haircut,
            "collateral_fx_rates": collateral_fx_rates,
            "insurance_fund": insurance_fund,
            "venue_default_recovery_rate": venue_default_recovery_rate,
            "venue_default_loss_limit_fraction": venue_default_loss_limit_fraction,
            "funding_rates": funding_rates,
            "stress_shocks": shocks,
            "adl_ranking": adl_ranking,
            "liquidation_mode": liquidation_mode,
            "order_book_impact_bps": order_book_impact_bps,
            "intraday_path": path,
        },
        summary={
            "position_count": len(terms),
            "intraday_print_count": len(path),
            "collateral_asset": collateral_asset,
            "available_collateral": available_collateral,
            "worst_stress_equity": min(float(detail["equity"]) for detail in stress_details),
            "liquidation_scenario_count": sum(bool(detail["liquidated"]) for detail in stress_details),
            "intraday_liquidation_print_count": sum(
                bool(detail["liquidated"]) for detail in details if detail["detail_type"] == "intraday_print"
            ),
            "maximum_socialized_loss": max(float(detail["socialized_loss"]) for detail in stress_details),
            "maximum_liquidation_impact_cost": min(
                float(detail["liquidation_impact_cost"]) for detail in stress_details
            ),
            "venue_default_loss": default_loss,
            "venue_default_loss_fraction": default_loss_fraction,
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            _gap(
                "crypto_cross_margin_scope",
                "Cumulative tier deductions and "
                + (
                    "volume-participation order-book impact were applied at liquidation; "
                    if order_book_impact_bps > 0
                    else "linear marks omit order-book impact; "
                )
                + "bankruptcy-price rules and recovery timing remain unmodeled. "
                + (
                    "Intraday path liquidation is explicitly evaluated sequentially between prints "
                    "with remaining quantities recorded after each print."
                    if path
                    else "No intraday path was supplied, so between-print sequencing is not evidenced."
                )
                + " Collateral haircut/FX is a static rate conversion. "
                "ADL ranking is this account's profitable legs only, scored by unrealized "
                "PnL or PnL times effective leverage.",
            )
        ],
        details=details,
        provenance={
            "margin_mode": "cross",
            "tier_application": "cumulative_tiered_deduction",
            "liquidation_waterfall": ["account_equity", "insurance_fund", "socialized_loss_adl"],
            "adl_ranking": adl_ranking,
            "liquidation_mode": liquidation_mode,
            "order_book_impact": (
                "linear_volume_participation" if order_book_impact_bps > 0 else "not_requested"
            ),
            "intraday_liquidation": ("sequential_between_prints" if path else "not_requested"),
            "intraday_quantity_evidence": (
                "remaining_quantities_after_each_print" if path else "not_requested"
            ),
            "live_order_submission": False,
        },
    ).finalize()


@register_diagnostic(
    "crypto-margin-stress",
    "crypto_margin_stress",
    required_table_types=("crypto_instruments", "market_quotes"),
    manifest_stage="risk",
    parameter_model=CryptoMarginStressParameters,
    description="Apply linear price/funding shocks against explicit crypto maintenance margin.",
)
def crypto_margin_stress_artifact(
    instruments: pd.DataFrame,
    quotes: pd.DataFrame,
    *,
    signed_quantity: float,
    initial_equity: float,
    maintenance_margin_rate: float,
    venue: str | None = None,
    instrument_id: str | None = None,
    funding_rate: float = 0.0,
    stress_shocks: list[float] | None = None,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    shocks = stress_shocks if stress_shocks is not None else [-0.20, -0.10, 0.10]
    if signed_quantity == 0 or initial_equity <= 0 or not 0 < maintenance_margin_rate < 1:
        raise ValueError("Crypto quantity/equity/margin parameters are invalid.")
    if not shocks or any(shock <= -1 for shock in shocks):
        raise ValueError("Crypto stress_shocks must be non-empty and greater than -1.")
    instruments, venue = _select_one(instruments.copy(), "venue", venue, "crypto-margin-stress")
    instruments, instrument_id = _select_one(
        instruments, "instrument_id", instrument_id, "crypto-margin-stress"
    )
    instrument = instruments.iloc[0]
    quotes = quotes[
        (quotes["asset_id"].astype(str) == instrument_id) & (quotes["venue"].astype(str) == venue)
    ].copy()
    if quotes.empty:
        raise ValueError("crypto-margin-stress found no matching market quote.")
    quotes["timestamp"] = parse_utc_timestamp(quotes["timestamp"], "timestamp")
    quote = quotes.loc[quotes["timestamp"].idxmax()]
    bid = float(quote["bid"])
    ask = float(quote["ask"])
    if bid <= 0 or ask < bid:
        raise ValueError("Crypto quote must have positive bid and ask >= bid.")
    mark = (bid + ask) / 2.0
    multiplier = float(instrument["multiplier"])
    if multiplier <= 0:
        raise ValueError("Crypto instrument multiplier must be positive.")
    funding_cashflow = perpetual_funding_cashflow(
        signed_quantity * multiplier,
        mark,
        funding_rate,
    )
    equity_after_funding = initial_equity + funding_cashflow
    details = []
    blockers: list[DiagnosticMessage] = []
    for shock in shocks:
        stressed_price = mark * (1.0 + shock)
        pnl = signed_quantity * multiplier * (stressed_price - mark)
        stressed_equity = equity_after_funding + pnl
        stressed_notional = abs(signed_quantity * multiplier * stressed_price)
        maintenance = stressed_notional * maintenance_margin_rate
        buffer = liquidation_buffer_fraction(stressed_equity, maintenance, stressed_notional)
        row = {
            "shock": shock,
            "stressed_price": stressed_price,
            "pnl": pnl,
            "equity": stressed_equity,
            "maintenance_margin": maintenance,
            "liquidation_buffer_fraction": buffer,
        }
        details.append(row)
        if stressed_equity <= maintenance:
            blockers.append(
                DiagnosticMessage(
                    code="crypto_maintenance_margin_breach",
                    message=f"Price shock {shock:.2%} breaches maintenance margin.",
                    severity="blocker",
                    context=row,
                )
            )
    initial_notional = abs(signed_quantity * multiplier * mark)
    initial_maintenance = initial_notional * maintenance_margin_rate
    return ArtifactEnvelope(
        artifact_type="crypto_margin_stress",
        run_id=run_id,
        producer=ProducerReference(name="crypto-margin-stress", version=__version__),
        parameters={
            "venue": venue,
            "instrument_id": instrument_id,
            "signed_quantity": signed_quantity,
            "initial_equity": initial_equity,
            "maintenance_margin_rate": maintenance_margin_rate,
            "funding_rate": funding_rate,
            "stress_shocks": shocks,
        },
        summary={
            "quote_at": pd.Timestamp(quote["timestamp"]).isoformat(),
            "mark_price": mark,
            "initial_notional": initial_notional,
            "initial_maintenance_margin": initial_maintenance,
            "funding_cashflow": funding_cashflow,
            "initial_liquidation_buffer_fraction": liquidation_buffer_fraction(
                equity_after_funding,
                initial_maintenance,
                initial_notional,
            ),
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            _gap(
                "crypto_margin_scope",
                "Linear isolated-position stress omits cross-margin offsets, tiered maintenance, "
                "liquidation fees, insurance funds, ADL, oracle failure, and venue default.",
            )
        ],
        details=details,
        provenance={
            "instrument_type": str(instrument["instrument_type"]),
            "margin_mode": str(instrument["margin_mode"]),
            "live_order_submission": False,
        },
    ).finalize()
