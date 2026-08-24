"""Fail-closed vectorized portfolio backtesting for canonical weights and labels."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from data_quant import __version__
from data_quant.contracts.artifacts import ArtifactEnvelope, DiagnosticMessage, ProducerReference
from data_quant.io.validation import parse_utc_timestamp
from data_quant.statistics import probabilistic_sharpe_ratio


@dataclass(frozen=True)
class PortfolioBacktestResult:
    """Period-level results and their immutable Artifact envelope."""

    periods: pd.DataFrame
    artifact: ArtifactEnvelope


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _numeric(series: pd.Series, column: str) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    invalid = series.notna() & values.isna()
    if invalid.any():
        examples = series[invalid].astype(str).head(5).tolist()
        raise ValueError(f"Column {column!r} contains non-numeric values: {examples}")
    if values.isna().any() or (~values.map(math.isfinite)).any():
        raise ValueError(f"Column {column!r} must contain finite, non-null values.")
    return values.astype(float)


def _prepare_weights(frame: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        frame,
        ("decision_at", "asset_id", "weight", "weight_type", "currency"),
        "Portfolio weights",
    )
    data = frame.copy()
    data["decision_at"] = parse_utc_timestamp(data["decision_at"], "decision_at")
    data["weight"] = _numeric(data["weight"], "weight")
    if data["decision_at"].isna().any() or data["asset_id"].isna().any():
        raise ValueError("Portfolio weight keys cannot be missing.")
    data["asset_id"] = data["asset_id"].astype(str)
    if data["asset_id"].str.strip().eq("").any():
        raise ValueError("Portfolio asset_id cannot be empty.")
    if data["weight_type"].nunique(dropna=False) != 1:
        raise ValueError("Select exactly one weight_type before backtesting.")
    if data["currency"].nunique(dropna=False) != 1:
        raise ValueError("Portfolio weights must use exactly one currency.")
    if data[["weight_type", "currency"]].isna().any().any():
        raise ValueError("Portfolio weight_type and currency cannot be missing.")
    if data["currency"].astype(str).str.strip().eq("").any():
        raise ValueError("Portfolio currency cannot be empty.")
    duplicate = data.duplicated(["decision_at", "asset_id"], keep=False)
    if duplicate.any():
        examples = data.loc[duplicate, ["decision_at", "asset_id"]].head(5).to_dict("records")
        raise ValueError(f"Portfolio weights contain duplicate decision/asset keys: {examples}")
    return data


def _prepare_returns(frame: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        frame,
        (
            "decision_at",
            "execution_at",
            "return_start",
            "return_end",
            "asset_id",
            "label",
            "return_value",
            "return_type",
            "return_basis",
            "corporate_action_policy",
            "currency",
        ),
        "Return labels",
    )
    data = frame.copy()
    for column in ("decision_at", "execution_at", "return_start", "return_end"):
        data[column] = parse_utc_timestamp(data[column], column)
        if data[column].isna().any():
            raise ValueError(f"Return label column {column!r} cannot be missing.")
    data["return_value"] = _numeric(data["return_value"], "return_value")
    if data["asset_id"].isna().any():
        raise ValueError("Return label asset_id cannot be missing.")
    data["asset_id"] = data["asset_id"].astype(str)
    if data["asset_id"].str.strip().eq("").any():
        raise ValueError("Return label asset_id cannot be empty.")
    semantic_columns = [
        "label",
        "return_type",
        "return_basis",
        "corporate_action_policy",
        "currency",
    ]
    if data[semantic_columns].isna().any().any():
        raise ValueError("Return label semantics cannot be missing.")
    for column in semantic_columns:
        data[column] = data[column].astype(str)
        if data[column].str.strip().eq("").any():
            raise ValueError(f"Return label column {column!r} cannot be empty.")
        if data[column].nunique() != 1:
            name = "return label" if column == "label" else column
            raise ValueError(f"Select exactly one {name} before backtesting.")
    if data["return_type"].iloc[0] != "simple":
        raise ValueError("Portfolio NAV backtesting requires simple return labels.")
    if data["return_basis"].iloc[0] != "gross":
        raise ValueError("Portfolio NAV backtesting requires gross, not excess, return labels.")
    if data["corporate_action_policy"].iloc[0] != "total_return":
        raise ValueError("Portfolio NAV backtesting requires total_return corporate-action labels.")
    duplicate = data.duplicated(["decision_at", "asset_id"], keep=False)
    if duplicate.any():
        examples = data.loc[duplicate, ["decision_at", "asset_id"]].head(5).to_dict("records")
        raise ValueError(f"Return labels contain duplicate decision/asset keys: {examples}")
    if (data["execution_at"] < data["decision_at"]).any():
        raise ValueError("Return-label execution_at cannot precede decision_at.")
    if (data["return_start"] < data["execution_at"]).any():
        raise ValueError("return_start cannot precede the executable decision time.")
    if (data["return_end"] <= data["return_start"]).any():
        raise ValueError("return_end must be later than return_start.")
    ordered = data.sort_values(["asset_id", "return_start", "return_end"])
    previous_end = ordered.groupby("asset_id", sort=False)["return_end"].shift()
    if (ordered["return_start"] < previous_end).any():
        raise ValueError("Return-label windows cannot overlap within an asset.")
    return data


def _prepare_financing_curves(
    frame: pd.DataFrame,
    requested_curve_id: str | None,
) -> tuple[pd.DataFrame, str]:
    _require_columns(
        frame,
        (
            "curve_id",
            "currency",
            "rate_type",
            "effective_from",
            "effective_to",
            "available_at",
            "tenor_days",
            "annual_rate",
            "day_count_basis",
            "compounding",
        ),
        "Financing curves",
    )
    data = frame.copy()
    for column in ("effective_from", "effective_to", "available_at"):
        data[column] = parse_utc_timestamp(data[column], column)
    data["tenor_days"] = _numeric(data["tenor_days"], "tenor_days")
    data["annual_rate"] = _numeric(data["annual_rate"], "annual_rate")
    if (data["tenor_days"] < 0).any() or (data["tenor_days"] % 1 != 0).any():
        raise ValueError("Financing curve tenor_days must be non-negative integers.")
    if (data["effective_to"].notna() & (data["effective_to"] <= data["effective_from"])).any():
        raise ValueError("Financing curve effective_to must be later than effective_from.")
    if not data["rate_type"].astype(str).isin({"cash", "financing"}).all():
        raise ValueError("Financing curve rate_type must be cash or financing.")
    if not data["day_count_basis"].astype(str).isin({"ACT/360", "ACT/365"}).all():
        raise ValueError("Financing curves support ACT/360 or ACT/365 day count.")
    if data["compounding"].astype(str).ne("simple").any():
        raise ValueError("Financing curves currently require simple compounding.")
    curve_ids = sorted(data["curve_id"].dropna().astype(str).unique())
    if requested_curve_id is None:
        if len(curve_ids) != 1:
            raise ValueError(f"Select one financing_curve_id; available: {curve_ids}")
        requested_curve_id = curve_ids[0]
    if requested_curve_id not in curve_ids:
        raise ValueError(f"Unknown financing_curve_id {requested_curve_id!r}; available: {curve_ids}")
    data = data[data["curve_id"].astype(str) == requested_curve_id].copy()
    duplicate = data.duplicated(
        ["currency", "rate_type", "effective_from", "tenor_days"], keep=False
    )
    if duplicate.any():
        raise ValueError("Financing curves contain duplicate effective tenor nodes.")
    return data, requested_curve_id


def _financing_rate(
    curves: pd.DataFrame,
    *,
    decision_at: pd.Timestamp,
    period_days: float,
    currency: str,
    rate_type: str,
) -> tuple[float, float, str]:
    candidates = curves[
        (curves["currency"].astype(str) == currency)
        & (curves["rate_type"].astype(str) == rate_type)
        & (curves["available_at"] <= decision_at)
        & (curves["effective_from"] <= decision_at)
        & (curves["effective_to"].isna() | (curves["effective_to"] > decision_at))
    ].copy()
    if candidates.empty:
        raise ValueError(
            f"No PIT {rate_type} financing curve is effective for {currency} at {decision_at}."
        )
    effective_from = pd.Timestamp(candidates["effective_from"].max())
    nodes = candidates[candidates["effective_from"] == effective_from].sort_values("tenor_days")
    bases = sorted(nodes["day_count_basis"].astype(str).unique())
    if len(bases) != 1:
        raise ValueError("Selected financing curve nodes must use one day-count basis.")
    tenors = nodes["tenor_days"].to_numpy(dtype=float)
    rates = nodes["annual_rate"].to_numpy(dtype=float)
    if len(tenors) == 0 or period_days < tenors[0] or period_days > tenors[-1]:
        raise ValueError(
            f"Financing curve does not bound the {period_days:g}-day holding period; "
            "extrapolation is prohibited."
        )
    upper_index = int(tenors.searchsorted(period_days, side="left"))
    if tenors[upper_index] == period_days or upper_index == 0:
        annual_rate = float(rates[upper_index])
    else:
        lower_index = upper_index - 1
        fraction = (period_days - tenors[lower_index]) / (
            tenors[upper_index] - tenors[lower_index]
        )
        annual_rate = float(
            rates[lower_index] + fraction * (rates[upper_index] - rates[lower_index])
        )
    basis_days = 360.0 if bases[0] == "ACT/360" else 365.0
    return annual_rate, period_days / basis_days, effective_from.isoformat()


def _return_summary(
    returns: pd.Series,
    annualization: int,
    risk_free_annual: float,
) -> dict[str, float | int | None]:
    count = int(len(returns))
    if count == 0:
        raise ValueError("A portfolio backtest requires at least one return period.")
    wealth = (1.0 + returns).cumprod()
    if (wealth <= 0).any():
        raise ValueError("Net portfolio wealth reached zero or below.")
    stdev = float(returns.std(ddof=1)) if count >= 2 else None
    annualized_volatility = stdev * math.sqrt(annualization) if stdev is not None else None
    sharpe = None
    if stdev is not None and stdev > 0:
        sharpe = float((returns.mean() - risk_free_annual / annualization) / stdev * math.sqrt(annualization))
    drawdown = wealth / wealth.cummax() - 1.0
    psr = None
    if stdev is not None and stdev > 0 and count >= 3:
        try:
            psr = float(probabilistic_sharpe_ratio(returns.tolist(), periods_per_year=annualization))
        except ValueError:
            psr = None
    return {
        "n": count,
        "cumulative_return": float(wealth.iloc[-1] - 1.0),
        "annualized_return_geometric": float(wealth.iloc[-1] ** (annualization / count) - 1.0),
        "annualized_volatility": annualized_volatility,
        "sharpe": sharpe,
        "probabilistic_sharpe_ratio": psr,
        "max_drawdown": float(drawdown.min()),
    }


def run_portfolio_backtest(
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
) -> PortfolioBacktestResult:
    """Apply beginning-of-period weights to aligned returns without simulating live orders."""

    if cost_bps_per_one_way_turnover < 0:
        raise ValueError("Transaction cost bps must be non-negative.")
    if annualization <= 0:
        raise ValueError("annualization must be positive.")
    rates = [risk_free_annual, cash_rate_annual, financing_rate_annual, short_borrow_rate_annual]
    if not all(math.isfinite(rate) for rate in rates):
        raise ValueError("Annual rate assumptions must be finite.")
    if min(cash_rate_annual, financing_rate_annual, short_borrow_rate_annual) < 0:
        raise ValueError("Cash, financing, and short-borrow rates must be non-negative.")
    if (
        secured_financing_spread_bps < 0
        or not 0 <= collateralization_ratio <= 1
        or financing_convexity_bps < 0
    ):
        raise ValueError("Secured financing spread, collateralization, or convexity is invalid.")
    if not math.isfinite(initial_nav) or initial_nav <= 0:
        raise ValueError("initial_nav must be finite and positive.")
    prepared_curves = None
    selected_curve_id = None
    if financing_curves is not None:
        if cash_rate_annual != 0 or financing_rate_annual != 0:
            raise ValueError("Flat cash/financing rates cannot be combined with financing_curves.")
        prepared_curves, selected_curve_id = _prepare_financing_curves(
            financing_curves,
            financing_curve_id,
        )
    elif financing_curve_id is not None:
        raise ValueError("financing_curve_id requires financing_curves.")

    prepared_weights = _prepare_weights(weights)
    prepared_returns = _prepare_returns(return_labels)
    if prepared_weights.empty or prepared_returns.empty:
        raise ValueError("Portfolio weights and return labels cannot be empty.")
    weight_currency = str(prepared_weights["currency"].iloc[0])
    return_currency = str(prepared_returns["currency"].iloc[0])
    if weight_currency != return_currency:
        raise ValueError(
            f"Portfolio weight currency {weight_currency!r} does not match return currency "
            f"{return_currency!r}."
        )

    keys = ["decision_at", "asset_id"]
    aligned = prepared_weights[keys + ["weight"]].merge(
        prepared_returns[keys + ["return_value", "return_start", "return_end"]],
        on=keys,
        how="left",
        validate="one_to_one",
    )
    missing = aligned[aligned["return_value"].isna() & aligned["weight"].ne(0.0)]
    if not missing.empty:
        examples = missing[keys].head(5).to_dict("records")
        raise ValueError(f"Non-zero portfolio weights lack aligned return labels: {examples}")
    aligned["return_value"] = aligned["return_value"].fillna(0.0)
    rows: list[dict[str, object]] = []
    previous = pd.Series(dtype=float)
    nav = float(initial_nav)
    for decision_at, group in aligned.sort_values(keys).groupby("decision_at", sort=True):
        current = group.set_index("asset_id")["weight"].astype(float)
        asset_returns = group.set_index("asset_id")["return_value"].astype(float)
        union = previous.index.union(current.index)
        turnover = float(
            0.5
            * (
                current.reindex(union, fill_value=0.0)
                - previous.reindex(union, fill_value=0.0)
            ).abs().sum()
        )
        gross_return = float((current * asset_returns.reindex(current.index)).sum())
        cost = float(turnover * cost_bps_per_one_way_turnover / 10_000.0)
        net_exposure = float(current.sum())
        cash_weight = 1.0 - net_exposure
        funding_rate_type = "cash" if cash_weight >= 0 else "financing"
        financing_curve_effective_from = None
        if abs(cash_weight) < 1e-15:
            funding_rate = 0.0
            financing_day_fraction = 0.0
            funding_rate_source = "not_applicable"
        elif prepared_curves is None:
            funding_rate = cash_rate_annual if cash_weight >= 0 else financing_rate_annual
            financing_day_fraction = 1.0 / annualization
            funding_rate_source = "flat_annual_assumption"
        else:
            windows = group[["return_start", "return_end"]].dropna().drop_duplicates()
            if len(windows) != 1:
                raise ValueError(
                    "Each portfolio decision requires one common realized return window for curve financing."
                )
            return_start = pd.Timestamp(windows.iloc[0]["return_start"])
            return_end = pd.Timestamp(windows.iloc[0]["return_end"])
            period_days = (return_end - return_start).total_seconds() / 86_400.0
            funding_rate, financing_day_fraction, financing_curve_effective_from = _financing_rate(
                prepared_curves,
                decision_at=pd.Timestamp(decision_at),
                period_days=period_days,
                currency=weight_currency,
                rate_type=funding_rate_type,
            )
            funding_rate_source = "pit_financing_curve"
        if cash_weight < 0 and collateralization_ratio > 0:
            secured_rate = funding_rate - secured_financing_spread_bps / 10_000.0
            funding_rate = (
                (1.0 - collateralization_ratio) * funding_rate
                + collateralization_ratio * secured_rate
            )
            funding_rate_type = "blended_secured_financing"
        if cash_weight < 0 and financing_convexity_bps > 0:
            funding_rate += financing_convexity_bps / 10_000.0 * (cash_weight**2)
            funding_rate_type = "convex_leverage_financing"
        cash_financing_return = cash_weight * funding_rate * financing_day_fraction
        short_exposure = float(current[current < 0].abs().sum())
        short_borrow_cost = short_exposure * short_borrow_rate_annual / annualization
        net_return = gross_return + cash_financing_return - short_borrow_cost - cost
        if net_return <= -1.0:
            raise ValueError(
                f"Net return at {decision_at} is {net_return}; portfolio wealth would be non-positive."
            )
        nav *= 1.0 + net_return
        gross_exposure = float(current.abs().sum())
        rows.append(
            {
                "decision_at": decision_at,
                "asset_count": int(len(current)),
                "gross_return": gross_return,
                "one_way_turnover": turnover,
                "cost_fraction": cost,
                "cash_weight": cash_weight,
                "cash_financing_annual_rate": funding_rate,
                "cash_financing_day_fraction": financing_day_fraction,
                "cash_financing_rate_type": funding_rate_type,
                "cash_financing_rate_source": funding_rate_source,
                "collateralization_ratio": collateralization_ratio,
                "financing_curve_effective_from": financing_curve_effective_from,
                "cash_financing_return": cash_financing_return,
                "short_exposure": short_exposure,
                "short_borrow_cost": short_borrow_cost,
                "net_return": net_return,
                "gross_exposure": gross_exposure,
                "net_exposure": net_exposure,
                "concentration_hhi": (
                    float(((current.abs() / gross_exposure) ** 2).sum()) if gross_exposure else None
                ),
                "nav": nav,
            }
        )
        previous = current

    periods = pd.DataFrame(rows)
    gross_summary = _return_summary(periods["gross_return"], annualization, risk_free_annual)
    net_summary = _return_summary(periods["net_return"], annualization, risk_free_annual)
    details = [
        {
            **row,
            "decision_at": pd.Timestamp(row["decision_at"]).isoformat(),
        }
        for row in periods.to_dict("records")
    ]
    artifact = ArtifactEnvelope(
        artifact_type="portfolio_backtest",
        run_id=run_id,
        producer=ProducerReference(name="portfolio-backtest", version=__version__),
        parameters={
            "annualization": annualization,
            "risk_free_annual": risk_free_annual,
            "cash_rate_annual": cash_rate_annual,
            "financing_rate_annual": financing_rate_annual,
            "short_borrow_rate_annual": short_borrow_rate_annual,
            "secured_financing_spread_bps": secured_financing_spread_bps,
            "collateralization_ratio": collateralization_ratio,
            "financing_convexity_bps": financing_convexity_bps,
            "financing_curve_id": selected_curve_id,
            "financing_rate_source": (
                "pit_financing_curve" if prepared_curves is not None else "flat_annual_assumption"
            ),
            "initial_nav": initial_nav,
            "cost_bps_per_one_way_turnover": cost_bps_per_one_way_turnover,
            "weight_timing": "beginning_of_period",
            "initial_turnover": "half_gross_exposure",
            "weight_type": str(prepared_weights["weight_type"].iloc[0]),
            "label": str(prepared_returns["label"].iloc[0]),
            "return_type": "simple",
            "return_basis": "gross",
            "corporate_action_policy": "total_return",
            "currency": weight_currency,
        },
        summary={
            "period_count": int(len(periods)),
            "weight_row_count": int(len(prepared_weights)),
            "return_row_count": int(len(prepared_returns)),
            "gross_return_summary": gross_summary,
            "net_return_summary": net_summary,
            "mean_one_way_turnover": float(periods["one_way_turnover"].mean()),
            "annualized_one_way_turnover": float(periods["one_way_turnover"].mean() * annualization),
            "total_cash_financing_return": float(periods["cash_financing_return"].sum()),
            "total_short_borrow_cost": float(periods["short_borrow_cost"].sum()),
            "max_gross_exposure": float(periods["gross_exposure"].max()),
            "ending_nav": float(periods["nav"].iloc[-1]),
        },
        warnings=[
            DiagnosticMessage(
                code="diagnostic_backtest_only",
                message="This vectorized backtest is a research diagnostic, not an order or fill simulator.",
                severity="warning",
            )
        ],
        evidence_gaps=[
            DiagnosticMessage(
                code="execution_tradability_not_proven",
                message=(
                    "A total-return declaration and cash/financing assumptions do not prove "
                    "universe eligibility, corporate-action adjustment quality, locate/recall availability, "
                    "market impact, or executable fills; audit those before promotion."
                ),
                severity="warning",
            )
        ],
        details=details,
        provenance={"engine": "vectorized_offline", "live_order_submission": False},
    ).finalize()
    return PortfolioBacktestResult(periods=periods, artifact=artifact)
