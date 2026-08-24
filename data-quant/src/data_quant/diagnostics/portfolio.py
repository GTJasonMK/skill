"""Native portfolio diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from data_quant import __version__
from data_quant.backtest import run_portfolio_backtest
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.contracts.parameters import (
    PortfolioBacktestParameters,
    PortfolioEligibilityParameters,
    ShortBorrowCapacityParameters,
)
from data_quant.io.validation import parse_utc_timestamp
from data_quant.registry import register_diagnostic


@register_diagnostic(
    "portfolio-backtest",
    "portfolio_backtest",
    required_table_types=("portfolio_weights", "return_labels"),
    manifest_stage="portfolio",
    parameter_model=PortfolioBacktestParameters,
    description="Run an offline vectorized backtest with costs, timing, and optional PIT financing curves.",
)
def portfolio_backtest_artifact(
    weights: pd.DataFrame,
    return_labels: pd.DataFrame,
    *,
    cost_bps_per_one_way_turnover: float = 0.0,
    annualization: int = 252,
    risk_free_annual: float = 0.0,
    cash_rate_annual: float = 0.0,
    financing_rate_annual: float = 0.0,
    short_borrow_rate_annual: float = 0.0,
    secured_financing_spread_bps: float = 0.0,
    collateralization_ratio: float = 0.0,
    financing_convexity_bps: float = 0.0,
    financing_curves: pd.DataFrame | None = None,
    financing_curve_id: str | None = None,
    initial_nav: float = 1.0,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    return run_portfolio_backtest(
        weights,
        return_labels,
        cost_bps_per_one_way_turnover=cost_bps_per_one_way_turnover,
        annualization=annualization,
        risk_free_annual=risk_free_annual,
        cash_rate_annual=cash_rate_annual,
        financing_rate_annual=financing_rate_annual,
        short_borrow_rate_annual=short_borrow_rate_annual,
        secured_financing_spread_bps=secured_financing_spread_bps,
        collateralization_ratio=collateralization_ratio,
        financing_convexity_bps=financing_convexity_bps,
        financing_curves=financing_curves,
        financing_curve_id=financing_curve_id,
        initial_nav=initial_nav,
        run_id=run_id,
    ).artifact


@register_diagnostic(
    "portfolio-eligibility",
    "portfolio_eligibility",
    required_table_types=(
        "portfolio_weights",
        "return_labels",
        "universe_membership",
        "corporate_actions",
        "borrow_availability",
    ),
    manifest_stage="portfolio",
    parameter_model=PortfolioEligibilityParameters,
    description="Audit dynamic-universe, total-return, corporate-action, and short-borrow eligibility.",
)
def portfolio_eligibility_artifact(
    weights: pd.DataFrame,
    labels: pd.DataFrame,
    membership: pd.DataFrame,
    corporate_actions: pd.DataFrame,
    borrow: pd.DataFrame,
    *,
    universe_id: str,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    weights = weights.copy()
    labels = labels.copy()
    membership = membership[membership["universe_id"].astype(str) == universe_id].copy()
    corporate_actions = corporate_actions.copy()
    borrow = borrow.copy()
    for temporal in (membership, borrow):
        if "effective_to" not in temporal:
            temporal["effective_to"] = pd.Series(
                pd.NaT,
                index=temporal.index,
                dtype="datetime64[ns, UTC]",
            )
    if "max_quantity" not in borrow:
        borrow["max_quantity"] = pd.Series(float("nan"), index=borrow.index, dtype=float)
    for frame, columns in (
        (weights, ("decision_at",)),
        (labels, ("decision_at", "return_start", "return_end")),
        (membership, ("effective_from", "effective_to", "available_at")),
        (corporate_actions, ("effective_at", "available_at")),
        (borrow, ("effective_from", "effective_to", "available_at")),
    ):
        for column in columns:
            if column in frame:
                frame[column] = parse_utc_timestamp(frame[column], column)
    blockers: list[DiagnosticMessage] = []
    details = []
    for row in weights[weights["weight"] != 0].sort_values(["decision_at", "asset_id"]).to_dict(
        "records"
    ):
        decision = pd.Timestamp(row["decision_at"])
        asset_id = str(row["asset_id"])
        member = membership[
            (membership["asset_id"].astype(str) == asset_id)
            & (membership["effective_from"] <= decision)
            & (membership["effective_to"].isna() | (membership["effective_to"] > decision))
            & (membership["available_at"] <= decision)
            & membership["eligible"].eq(True)
        ]
        label = labels[
            (labels["decision_at"] == decision)
            & (labels["asset_id"].astype(str) == asset_id)
        ]
        issues: list[str] = []
        if len(member) != 1:
            issues.append("universe_ineligible_or_ambiguous")
        if len(label) != 1:
            issues.append("return_label_missing_or_ambiguous")
            action_count = 0
            action_types: list[str] = []
        else:
            label_row = label.iloc[0]
            if str(label_row["corporate_action_policy"]) != "total_return":
                issues.append("return_label_not_total_return")
            actions = corporate_actions[
                (corporate_actions["asset_id"].astype(str) == asset_id)
                & (corporate_actions["effective_at"] >= label_row["return_start"])
                & (corporate_actions["effective_at"] <= label_row["return_end"])
            ]
            action_count = len(actions)
            action_types = sorted(actions["action_type"].astype(str).unique())
        borrow_fee: float | None = None
        if float(row["weight"]) < 0:
            available_borrow = borrow[
                (borrow["asset_id"].astype(str) == asset_id)
                & (borrow["effective_from"] <= decision)
                & (borrow["effective_to"].isna() | (borrow["effective_to"] > decision))
                & (borrow["available_at"] <= decision)
                & borrow["borrowable"].eq(True)
                & (borrow["fee_rate_annual"] >= 0)
                & (borrow["max_quantity"].isna() | (borrow["max_quantity"] > 0))
                & (borrow["currency"].astype(str) == str(row["currency"]))
            ]
            if len(available_borrow) != 1:
                issues.append("borrow_unavailable_or_ambiguous")
            else:
                borrow_fee = float(available_borrow.iloc[0]["fee_rate_annual"])
        detail = {
            "decision_at": decision.isoformat(),
            "asset_id": asset_id,
            "weight": float(row["weight"]),
            "universe_id": universe_id,
            "corporate_action_count": action_count,
            "corporate_action_types": action_types,
            "borrow_fee_rate_annual": borrow_fee,
            "issues": issues,
        }
        details.append(detail)
        for issue in issues:
            blockers.append(
                DiagnosticMessage(
                    code=issue,
                    message=f"Portfolio eligibility failed for {asset_id} at {decision.isoformat()}.",
                    severity="blocker",
                    context=detail,
                )
            )
    return ArtifactEnvelope(
        artifact_type="portfolio_eligibility",
        run_id=run_id,
        producer=ProducerReference(name="portfolio-eligibility", version=__version__),
        parameters={
            "universe_id": universe_id,
            "require_total_return": True,
            "require_borrow_for_shorts": True,
        },
        summary={
            "position_period_count": len(details),
            "short_position_period_count": sum(row["weight"] < 0 for row in details),
            "corporate_action_count": sum(row["corporate_action_count"] for row in details),
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="eligibility_evidence_scope",
                message=(
                    "Membership, total-return declaration, and borrow flags do not prove adjustment "
                    "calculation, locate quantity, recalls, trading capacity, or executable fills."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={"live_order_submission": False},
    ).finalize()


@register_diagnostic(
    "short-borrow-capacity",
    "short_borrow_capacity",
    required_table_types=("portfolio_weights", "market_quotes", "borrow_locates"),
    manifest_stage="portfolio",
    parameter_model=ShortBorrowCapacityParameters,
    description="Gate short weights on PIT locate quantity, horizon recalls, quote age, and fees.",
)
def short_borrow_capacity_artifact(
    weights: pd.DataFrame,
    quotes: pd.DataFrame,
    locates: pd.DataFrame,
    *,
    portfolio_value: float,
    holding_period: str = "1D",
    max_quote_age: str = "1D",
    minimum_borrow_buffer: float = 1.0,
    maximum_blended_fee_annual: float = 1.0,
    unscheduled_recall_fraction: float = 0.0,
    maximum_lender_concentration: float = 1.0,
    venue: str | None = None,
    run_id: str | None = None,
) -> ArtifactEnvelope:
    holding = pd.Timedelta(holding_period)
    maximum_quote_age = pd.Timedelta(max_quote_age)
    if (
        portfolio_value <= 0
        or holding <= pd.Timedelta(0)
        or maximum_quote_age <= pd.Timedelta(0)
        or minimum_borrow_buffer < 1
        or maximum_blended_fee_annual < 0
        or not 0 <= unscheduled_recall_fraction <= 1
        or not 0 < maximum_lender_concentration <= 1
    ):
        raise ValueError("Short-borrow capacity assumptions are invalid.")
    weight_frame = weights.copy()
    weight_frame["decision_at"] = parse_utc_timestamp(
        weight_frame["decision_at"], "decision_at"
    )
    weight_frame["weight"] = pd.to_numeric(weight_frame["weight"], errors="coerce")
    if not np.isfinite(weight_frame["weight"].to_numpy(dtype=float)).all():
        raise ValueError("Portfolio weights must be finite for short-borrow capacity.")
    weight_frame = weight_frame[weight_frame["weight"] < 0].copy()
    quote_frame = quotes.copy()
    quote_frame["timestamp"] = parse_utc_timestamp(quote_frame["timestamp"], "timestamp")
    for column in ("bid", "ask"):
        quote_frame[column] = pd.to_numeric(quote_frame[column], errors="coerce")
    if (
        not np.isfinite(quote_frame[["bid", "ask"]].to_numpy(dtype=float)).all()
        or quote_frame["bid"].le(0).any()
        or quote_frame["ask"].lt(quote_frame["bid"]).any()
    ):
        raise ValueError("Borrow-capacity quotes require finite positive bid/ask spreads.")
    venues = sorted(quote_frame["venue"].dropna().astype(str).unique())
    if venue is None:
        if len(venues) != 1:
            raise ValueError(f"short-borrow-capacity must select one venue; available: {venues}")
        venue = venues[0]
    if venue not in venues:
        raise ValueError(f"Unknown quote venue {venue!r}; available: {venues}")
    quote_frame = quote_frame[quote_frame["venue"].astype(str) == venue].copy()
    locate_frame = locates.copy()
    for column in ("available_at", "effective_from", "expires_at", "recalled_at"):
        locate_frame[column] = parse_utc_timestamp(locate_frame[column], column)
    for column in ("located_quantity", "remaining_quantity", "fee_rate_annual"):
        locate_frame[column] = pd.to_numeric(locate_frame[column], errors="coerce")
    numeric = locate_frame[["located_quantity", "remaining_quantity", "fee_rate_annual"]]
    if (
        not np.isfinite(numeric.to_numpy(dtype=float)).all()
        or locate_frame["located_quantity"].le(0).any()
        or locate_frame["remaining_quantity"].lt(0).any()
        or (locate_frame["remaining_quantity"] > locate_frame["located_quantity"]).any()
        or locate_frame["fee_rate_annual"].lt(0).any()
        or (locate_frame["expires_at"] <= locate_frame["effective_from"]).any()
        or (
            locate_frame["recalled_at"].notna()
            & (locate_frame["recalled_at"] < locate_frame["effective_from"])
        ).any()
        or not locate_frame["status"].astype(str).isin(
            {"active", "used", "cancelled", "expired", "recalled"}
        ).all()
    ):
        raise ValueError("Borrow locates contain invalid quantities, fees, lifecycle, or status.")
    blockers: list[DiagnosticMessage] = []
    details = []
    total_required_quantity = 0.0
    total_buffered_required_quantity = 0.0
    used_by_locate: dict[str, float] = {}
    for row in weight_frame.sort_values(["decision_at", "asset_id"]).itertuples(index=False):
        decision = pd.Timestamp(row.decision_at)
        asset_id = str(row.asset_id)
        horizon = decision + holding
        decision_nav = portfolio_value
        if "nav" in weight_frame.columns:
            nav_values = pd.to_numeric(
                weight_frame.loc[weight_frame["decision_at"] == decision, "nav"],
                errors="coerce",
            ).dropna()
            unique_nav = pd.unique(nav_values)
            if len(unique_nav) == 1:
                if float(unique_nav[0]) <= 0:
                    raise ValueError("portfolio nav must be positive.")
                decision_nav = float(unique_nav[0])
            elif len(unique_nav) > 1:
                raise ValueError("portfolio nav must be one positive value per decision.")
        asset_quotes = quote_frame[
            (quote_frame["asset_id"].astype(str) == asset_id)
            & (quote_frame["timestamp"] <= decision)
        ].sort_values("timestamp")
        base_detail: dict[str, object] = {
            "decision_at": decision.isoformat(),
            "holding_horizon": horizon.isoformat(),
            "asset_id": asset_id,
            "weight": float(row.weight),
            "portfolio_value": decision_nav,
            "venue": venue,
        }
        if asset_quotes.empty:
            blockers.append(
                DiagnosticMessage(
                    code="borrow_quote_missing",
                    message="No historical quote is observable by the short decision.",
                    severity="blocker",
                    context=base_detail,
                )
            )
            details.append({**base_detail, "status": "quote_missing"})
            continue
        quote = asset_quotes.iloc[-1]
        quote_at = pd.Timestamp(quote["timestamp"])
        quote_age = decision - quote_at
        midpoint = (float(quote["bid"]) + float(quote["ask"])) / 2.0
        required_quantity = abs(float(row.weight)) * decision_nav / midpoint
        buffered_required_quantity = required_quantity * minimum_borrow_buffer
        total_required_quantity += required_quantity
        total_buffered_required_quantity += buffered_required_quantity
        asset_locates = locate_frame[
            (locate_frame["asset_id"].astype(str) == asset_id)
            & (locate_frame["available_at"] <= decision)
        ].sort_values("available_at")
        latest_locates = asset_locates.drop_duplicates("locate_id", keep="last")
        active_now = latest_locates[
            latest_locates["status"].astype(str).eq("active")
            & (latest_locates["effective_from"] <= decision)
            & (latest_locates["expires_at"] > decision)
            & (
                latest_locates["recalled_at"].isna()
                | (latest_locates["recalled_at"] > decision)
            )
        ].copy()
        if not active_now.empty and (
            active_now["currency"].astype(str) != str(row.currency)
        ).any():
            raise ValueError("Borrow locate and portfolio weight currencies must match.")
        stable = active_now[
            (active_now["expires_at"] > horizon)
            & (active_now["recalled_at"].isna() | (active_now["recalled_at"] > horizon))
        ].sort_values("fee_rate_annual")
        def usable_quantity(locate_row: pd.Series) -> float:
            locate_id = str(locate_row["locate_id"])
            leftover = max(
                0.0,
                float(locate_row["remaining_quantity"]) - used_by_locate.get(locate_id, 0.0),
            )
            return leftover * (1.0 - unscheduled_recall_fraction)

        available_now = float(sum(usable_quantity(row) for _, row in active_now.iterrows()))
        available_through_horizon = float(
            sum(usable_quantity(row) for _, row in stable.iterrows())
        )
        remaining = buffered_required_quantity
        allocated = 0.0
        fee_notional = 0.0
        allocated_by_lender: dict[str, float] = {}
        for locate in stable.itertuples(index=False):
            locate_id = str(locate.locate_id)
            already_used = used_by_locate.get(locate_id, 0.0)
            usable = max(0.0, float(locate.remaining_quantity) - already_used)
            usable *= 1.0 - unscheduled_recall_fraction
            quantity = min(usable, remaining)
            if quantity <= 0:
                continue
            allocated += quantity
            fee_notional += quantity * float(locate.fee_rate_annual)
            used_by_locate[locate_id] = already_used + quantity
            lender_id = locate.lender_id if hasattr(locate, "lender_id") else None
            lender = str(lender_id) if lender_id is not None and pd.notna(lender_id) else locate_id
            allocated_by_lender[lender] = allocated_by_lender.get(lender, 0.0) + quantity
            remaining -= quantity
            if remaining <= 1e-12:
                break
        blended_fee = fee_notional / allocated if allocated > 0 else None
        lender_concentration = (
            max(allocated_by_lender.values()) / allocated if allocated > 0 else None
        )
        scheduled_recall_quantity = float(
            active_now[
                active_now["recalled_at"].notna()
                & (active_now["recalled_at"] <= horizon)
            ]["remaining_quantity"].sum()
        )
        expiring_quantity = float(
            active_now[active_now["expires_at"] <= horizon]["remaining_quantity"].sum()
        )
        detail = {
            **base_detail,
            "quote_at": quote_at.isoformat(),
            "quote_age": str(quote_age),
            "midpoint": midpoint,
            "required_quantity": required_quantity,
            "buffered_required_quantity": buffered_required_quantity,
            "available_quantity_now": available_now,
            "available_quantity_through_horizon": available_through_horizon,
            "scheduled_recall_quantity": scheduled_recall_quantity,
            "expiring_quantity": expiring_quantity,
            "allocated_quantity": allocated,
            "blended_fee_rate_annual": blended_fee,
            "lender_concentration": lender_concentration,
            "unscheduled_recall_fraction": unscheduled_recall_fraction,
            "status": "pass",
        }
        issues: list[tuple[str, str]] = []
        if quote_age > maximum_quote_age:
            issues.append(("borrow_quote_stale", "Borrow sizing quote exceeds max_quote_age."))
        if available_through_horizon + 1e-12 < buffered_required_quantity:
            issues.append(
                (
                    "borrow_locate_capacity",
                    "PIT locate quantity surviving the holding horizon is insufficient.",
                )
            )
            if scheduled_recall_quantity > 0:
                issues.append(
                    (
                        "borrow_recall_within_horizon",
                        "A known recall removes required locate capacity within the holding horizon.",
                    )
                )
            if expiring_quantity > 0:
                issues.append(
                    (
                        "borrow_expiry_within_horizon",
                        "Locate expiry removes required capacity within the holding horizon.",
                    )
                )
        if blended_fee is not None and blended_fee > maximum_blended_fee_annual:
            issues.append(
                (
                    "borrow_fee_limit",
                    "Cheapest sufficient locate allocation exceeds the annual fee limit.",
                )
            )
        if (
            lender_concentration is not None
            and lender_concentration > maximum_lender_concentration
        ):
            issues.append(
                (
                    "borrow_lender_concentration",
                    "Allocated locates exceed the configured single-lender concentration.",
                )
            )
        if issues:
            detail["status"] = "blocked"
        details.append(detail)
        for code, message in issues:
            blockers.append(
                DiagnosticMessage(
                    code=code,
                    message=message,
                    severity="blocker",
                    context=detail,
                )
            )
    return ArtifactEnvelope(
        artifact_type="short_borrow_capacity",
        run_id=run_id,
        producer=ProducerReference(name="short-borrow-capacity", version=__version__),
        parameters={
            "portfolio_value": portfolio_value,
            "holding_period": str(holding),
            "max_quote_age": str(maximum_quote_age),
            "minimum_borrow_buffer": minimum_borrow_buffer,
            "maximum_blended_fee_annual": maximum_blended_fee_annual,
            "unscheduled_recall_fraction": unscheduled_recall_fraction,
            "maximum_lender_concentration": maximum_lender_concentration,
            "venue": venue,
        },
        summary={
            "short_position_period_count": len(details),
            "required_quantity": total_required_quantity,
            "buffered_required_quantity": total_buffered_required_quantity,
            "blocker_count": len(blockers),
        },
        blockers=blockers,
        evidence_gaps=[
            DiagnosticMessage(
                code="short_borrow_capacity_scope",
                message=(
                    "Static portfolio value and historical midpoint sizing do not prove "
                    "intraday fee changes, settlement, rehypothecation, tax, or executable "
                    "short sales. Locate reuse is sequential remaining-quantity consumption; "
                    "unscheduled recall is a flat remaining-quantity haircut."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={
            "locate_snapshot_selection": "latest_available_per_locate_at_decision",
            "fee_allocation": "cheapest_horizon_stable_capacity_first",
            "locate_reuse": "sequential_remaining_quantity",
            "unscheduled_recall": "flat_remaining_quantity_haircut",
            "live_order_submission": False,
        },
    ).finalize()
