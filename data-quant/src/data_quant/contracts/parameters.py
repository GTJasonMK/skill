"""Strict, machine-queryable parameters for native Manifest diagnostics."""

from __future__ import annotations

from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictParameters(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        hide_input_in_errors=True,
        allow_inf_nan=False,
    )


class FactorICParameters(StrictParameters):
    signal: str | None = Field(default=None, min_length=1)
    label: str | None = Field(default=None, min_length=1)
    min_assets: int = Field(default=5, ge=2)


class FamaMacBethParameters(StrictParameters):
    label: str | None = Field(default=None, min_length=1)
    features: list[str] | None = Field(default=None)
    min_assets: int = Field(default=5, ge=2)
    intercept: bool = True
    annualization: int = Field(default=12, ge=1)


class PurgedWalkForwardParameters(StrictParameters):
    label: str | None = Field(default=None, min_length=1)
    train_periods: int = Field(ge=1)
    test_periods: int = Field(ge=1)
    step_periods: int | None = Field(default=None, ge=1)
    embargo: str = "0s"
    expanding: bool = False

    @field_validator("embargo")
    @classmethod
    def embargo_is_non_negative_duration(cls, value: str) -> str:
        try:
            duration = pd.Timedelta(value)
        except ValueError as exc:
            raise ValueError("embargo must be a pandas-compatible duration.") from exc
        if duration < pd.Timedelta(0):
            raise ValueError("embargo must be non-negative.")
        return value


class CorporateActionAdjustmentParameters(StrictParameters):
    evaluated_at: str = Field(min_length=1)
    max_bar_gap: str = "7D"
    maximum_return_error: float = Field(default=1e-8, ge=0)
    minimum_actions: int = Field(default=1, ge=1)
    dividend_withholding_rate: float = Field(default=0.0, ge=0, le=1)
    allow_late_revisions: bool = True

    @field_validator("evaluated_at")
    @classmethod
    def corporate_action_evaluation_has_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("evaluated_at must include an explicit timezone.")
        return value

    @field_validator("max_bar_gap")
    @classmethod
    def corporate_action_gap_is_positive(cls, value: str) -> str:
        try:
            duration = pd.Timedelta(value)
        except ValueError as exc:
            raise ValueError("max_bar_gap must be a pandas-compatible duration.") from exc
        if duration <= pd.Timedelta(0):
            raise ValueError("max_bar_gap must be positive.")
        return value


class PortfolioBacktestParameters(StrictParameters):
    weight_type: str | None = Field(default=None, min_length=1)
    label: str | None = Field(default=None, min_length=1)
    cost_bps_per_one_way_turnover: float = Field(default=0.0, ge=0)
    annualization: int = Field(default=252, ge=1)
    risk_free_annual: float = 0.0
    cash_rate_annual: float = Field(default=0.0, ge=0)
    financing_rate_annual: float = Field(default=0.0, ge=0)
    short_borrow_rate_annual: float = Field(default=0.0, ge=0)
    secured_financing_spread_bps: float = Field(default=0.0, ge=0)
    collateralization_ratio: float = Field(default=0.0, ge=0, le=1)
    financing_convexity_bps: float = Field(default=0.0, ge=0)
    financing_curve_id: str | None = Field(default=None, min_length=1)
    initial_nav: float = Field(default=1.0, gt=0)


class PortfolioEligibilityParameters(StrictParameters):
    universe_id: str = Field(min_length=1)
    weight_type: str | None = Field(default=None, min_length=1)
    label: str | None = Field(default=None, min_length=1)
    require_total_return: Literal[True] = True
    require_borrow_for_shorts: Literal[True] = True


class ShortBorrowCapacityParameters(StrictParameters):
    weight_type: str | None = Field(default=None, min_length=1)
    venue: str | None = Field(default=None, min_length=1)
    portfolio_value: float = Field(gt=0)
    holding_period: str = "1D"
    max_quote_age: str = "1D"
    minimum_borrow_buffer: float = Field(default=1.0, ge=1)
    maximum_blended_fee_annual: float = Field(default=1.0, ge=0)
    unscheduled_recall_fraction: float = Field(default=0.0, ge=0, le=1)
    maximum_lender_concentration: float = Field(default=1.0, gt=0, le=1)

    @field_validator("holding_period", "max_quote_age")
    @classmethod
    def short_borrow_durations_are_positive(cls, value: str) -> str:
        try:
            duration = pd.Timedelta(value)
        except ValueError as exc:
            raise ValueError("short-borrow durations must be pandas-compatible.") from exc
        if duration <= pd.Timedelta(0):
            raise ValueError("short-borrow durations must be positive.")
        return value


class ExecutionReplayParameters(StrictParameters):
    max_participation: float = Field(default=0.10, gt=0, le=1)
    commission_bps: float = Field(default=0.0, ge=0)
    slippage_bps: float = Field(default=0.0, ge=0)
    impact_model: Literal["linear", "square_root"] = "linear"
    impact_coefficient_bps: float = Field(default=0.0, ge=0)
    permanent_impact_coefficient_bps: float = Field(default=0.0, ge=0)
    hidden_liquidity_fraction: float = Field(default=0.0, ge=0, le=1)
    hidden_spread_bps: float = Field(default=0.0, ge=0)
    initial_cash: float = Field(default=1_000_000.0, gt=0)

    @model_validator(mode="after")
    def impact_model_matches_coefficient(self) -> ExecutionReplayParameters:
        if self.impact_model == "linear" and self.impact_coefficient_bps < 0:
            raise ValueError("linear impact_coefficient_bps must be non-negative.")
        if self.impact_model == "square_root" and self.impact_coefficient_bps < 0:
            raise ValueError("square_root impact_coefficient_bps must be non-negative.")
        return self


class RebalanceReplayParameters(ExecutionReplayParameters):
    current_weight_type: str = Field(default="current", min_length=1)
    target_weight_type: str = Field(default="target", min_length=1)
    portfolio_value: float = Field(gt=0)
    min_trade_notional: float = Field(default=0.0, ge=0)
    lot_size: float = Field(default=1.0, gt=0)
    time_in_force: Literal["gtc", "ioc"] = "gtc"
    net_across_decisions: bool = False

    @model_validator(mode="after")
    def weight_types_differ(self) -> RebalanceReplayParameters:
        if self.current_weight_type == self.target_weight_type:
            raise ValueError("current_weight_type and target_weight_type must differ.")
        return self


class CovarianceRiskParameters(StrictParameters):
    label: str | None = Field(default=None, min_length=1)
    return_basis: Literal["gross", "excess"] | None = None
    weight_type: str | None = Field(default=None, min_length=1)
    estimator: Literal["sample", "ewma", "ledoit_wolf", "regime"] = "sample"
    annualization: float = Field(default=252.0, gt=0)
    decay: float = Field(default=0.94, gt=0, lt=1)
    shrinkage_target: Literal["constant_correlation", "diagonal_variance"] = "constant_correlation"
    stress_regime: Literal["high", "low"] = "high"


class FactorRiskParameters(StrictParameters):
    factor_model_id: str = Field(min_length=1)
    decision_at: str = Field(min_length=1)
    weight_type: str = Field(min_length=1)
    return_basis: Literal["gross", "excess"] = "gross"
    lookback_periods: int = Field(default=60, ge=3)
    minimum_observations: int = Field(default=20, ge=3)
    annualization: float = Field(default=252.0, gt=0)
    maximum_annualized_factor_volatility: float = Field(default=1.0, ge=0)
    maximum_covariance_condition_number: float = Field(default=1e8, gt=1)
    factor_exposure_limits: dict[str, float] = Field(default_factory=dict)
    factor_component_volatility_limits: dict[str, float] = Field(default_factory=dict)
    specific_risk_volatilities: dict[str, float] = Field(default_factory=dict)
    maximum_annualized_total_volatility: float | None = Field(default=None, gt=0)

    @field_validator("decision_at")
    @classmethod
    def factor_risk_decision_has_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("factor risk decision_at must include an explicit timezone.")
        return value

    @field_validator("factor_exposure_limits", "factor_component_volatility_limits")
    @classmethod
    def factor_risk_limits_are_positive(cls, value: dict[str, float]) -> dict[str, float]:
        if any(limit <= 0 for limit in value.values()):
            raise ValueError("Factor risk per-factor limits must be positive.")
        return value

    @field_validator("specific_risk_volatilities")
    @classmethod
    def specific_volatilities_are_positive(cls, value: dict[str, float]) -> dict[str, float]:
        if any(vol < 0 for vol in value.values()):
            raise ValueError("specific_risk_volatilities must be non-negative.")
        return value

    @model_validator(mode="after")
    def factor_risk_sample_sizes_are_ordered(self) -> FactorRiskParameters:
        if self.minimum_observations > self.lookback_periods:
            raise ValueError("minimum_observations cannot exceed lookback_periods.")
        return self


class FactorAttributionParameters(StrictParameters):
    factor_model_id: str = Field(min_length=1)
    decision_at: str = Field(min_length=1)
    evaluated_at: str = Field(min_length=1)
    label: str = Field(min_length=1)
    weight_type: str = Field(min_length=1)
    return_basis: Literal["gross", "excess"] = "gross"
    factor_exposure_limits: dict[str, float] = Field(default_factory=dict)
    gross_exposure_limit: float = Field(default=2.0, gt=0)
    specific_contribution_limit: float = Field(default=0.05, ge=0)

    @field_validator("decision_at", "evaluated_at")
    @classmethod
    def attribution_timestamps_have_timezones(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("factor attribution timestamps must include explicit timezones.")
        return value

    @field_validator("factor_exposure_limits")
    @classmethod
    def factor_limits_are_positive(cls, value: dict[str, float]) -> dict[str, float]:
        if any(limit <= 0 for limit in value.values()):
            raise ValueError("factor_exposure_limits must be positive.")
        return value

    @model_validator(mode="after")
    def attribution_evaluation_follows_decision(self) -> FactorAttributionParameters:
        if pd.Timestamp(self.evaluated_at) < pd.Timestamp(self.decision_at):
            raise ValueError("evaluated_at must not precede decision_at.")
        return self


class ModelCalibrationParameters(StrictParameters):
    model_id: str = Field(min_length=1)
    model_version: str | None = Field(default=None, min_length=1)
    label: str = Field(min_length=1)
    evaluated_at: str = Field(min_length=1)
    return_basis: Literal["gross", "excess"] = "gross"
    positive_return_threshold: float = 0.0
    bins: int = Field(default=10, ge=2)
    min_observations: int = Field(default=30, ge=10)
    max_brier_score: float = Field(default=0.25, ge=0, le=1)
    max_log_loss: float = Field(default=1.0, gt=0)
    max_expected_calibration_error: float = Field(default=0.10, ge=0, le=1)
    min_calibration_slope: float = 0.50
    max_calibration_slope: float = 1.50
    max_abs_calibration_intercept: float = Field(default=0.10, ge=0)
    bootstrap_resamples: int = Field(default=200, ge=50)
    bootstrap_confidence: float = Field(default=0.90, gt=0.5, lt=1)
    stability_min_class_observations: int = Field(default=20, ge=10)
    max_class_conditional_ece_gap: float = Field(default=0.10, ge=0)

    @field_validator("evaluated_at")
    @classmethod
    def calibration_evaluation_has_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("evaluated_at must include an explicit timezone.")
        return value

    @model_validator(mode="after")
    def calibration_slope_bounds_are_ordered(self) -> ModelCalibrationParameters:
        if self.max_calibration_slope <= self.min_calibration_slope:
            raise ValueError("max_calibration_slope must exceed min_calibration_slope.")
        return self


class ServiceHealthParameters(StrictParameters):
    required_service_ids: list[str] = Field(min_length=1)
    environment: str = Field(min_length=1)
    evaluated_at: str = Field(min_length=1)
    lookback: str = "1h"
    max_observation_age: str = "10m"
    minimum_window_coverage_fraction: float = Field(default=0.90, ge=0, le=1)
    minimum_uptime_fraction: float = Field(default=0.999, ge=0, le=1)
    maximum_error_rate: float = Field(default=0.01, ge=0, le=1)
    maximum_latency_p95_ms: float = Field(default=1_000.0, ge=0)
    minimum_request_count: int = Field(default=1, ge=0)

    @field_validator("required_service_ids")
    @classmethod
    def service_ids_are_unique(cls, value: list[str]) -> list[str]:
        if any(not service_id for service_id in value) or len(value) != len(set(value)):
            raise ValueError("required_service_ids must contain unique non-empty IDs.")
        return value

    @field_validator("evaluated_at")
    @classmethod
    def service_evaluation_has_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("evaluated_at must include an explicit timezone.")
        return value

    @field_validator("lookback", "max_observation_age")
    @classmethod
    def service_durations_are_positive(cls, value: str) -> str:
        try:
            duration = pd.Timedelta(value)
        except ValueError as exc:
            raise ValueError("service-health durations must be pandas-compatible.") from exc
        if duration <= pd.Timedelta(0):
            raise ValueError("service-health durations must be positive.")
        return value


class FeatureDriftParameters(StrictParameters):
    reference_source: str = Field(min_length=1)
    current_source: str = Field(min_length=1)
    columns: list[str] = Field(min_length=1)
    bins: int = Field(default=10, ge=2)
    warning_threshold: float = Field(default=0.10, ge=0)
    blocker_threshold: float = Field(default=0.25, gt=0)

    @field_validator("columns")
    @classmethod
    def columns_are_unique_and_nonempty(cls, values: list[str]) -> list[str]:
        if any(not value for value in values) or len(values) != len(set(values)):
            raise ValueError("columns must contain unique, non-empty names.")
        return values

    @model_validator(mode="after")
    def blocker_exceeds_warning(self) -> FeatureDriftParameters:
        if self.blocker_threshold <= self.warning_threshold:
            raise ValueError("blocker_threshold must exceed warning_threshold.")
        return self


class DependencyHealthParameters(StrictParameters):
    required_service_ids: list[str] = Field(min_length=1)
    environment: str = Field(min_length=1)
    evaluated_at: str = Field(min_length=1)
    lookback: str = "1h"
    minimum_probe_success_fraction: float = Field(default=0.99, ge=0, le=1)
    maximum_synthetic_latency_ms: float = Field(default=500.0, ge=0)
    minimum_dependency_redundancy: int = Field(default=2, ge=1)

    @field_validator("required_service_ids")
    @classmethod
    def dependency_service_ids_are_unique(cls, value: list[str]) -> list[str]:
        if any(not service_id for service_id in value) or len(value) != len(set(value)):
            raise ValueError("required_service_ids must contain unique non-empty IDs.")
        return value

    @field_validator("evaluated_at")
    @classmethod
    def dependency_evaluation_has_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("evaluated_at must include an explicit timezone.")
        return value

    @field_validator("lookback")
    @classmethod
    def dependency_lookback_is_positive(cls, value: str) -> str:
        try:
            duration = pd.Timedelta(value)
        except ValueError as exc:
            raise ValueError("lookback must be pandas-compatible.") from exc
        if duration <= pd.Timedelta(0):
            raise ValueError("lookback must be positive.")
        return value


class FuturesRollParameters(StrictParameters):
    root: str | None = Field(default=None, min_length=1)
    roll_days_before_expiry: int = Field(default=5, ge=0)
    roll_method: Literal["expiry", "volume", "open_interest"] = "expiry"
    confirmation_periods: int = Field(default=2, ge=1)
    collateral_rate_annual: float = Field(default=0.0, gt=-1)
    annualization: int = Field(default=252, ge=1)


class FuturesRollExecutionParameters(StrictParameters):
    root: str | None = Field(default=None, min_length=1)
    position_quantity: float
    initial_cash: float = Field(gt=0)
    roll_days_before_expiry: int = Field(default=5, ge=0)
    roll_method: Literal["expiry", "volume", "open_interest"] = "expiry"
    confirmation_periods: int = Field(default=2, ge=1)
    per_contract_fee: float = Field(default=0.0, ge=0)
    exchange_fee_bps: float = Field(default=0.0, ge=0)
    max_roll_participation: float = Field(default=1.0, gt=0, le=1)
    roll_impact_coefficient_bps: float = Field(default=0.0, ge=0)
    collateral_rate_annual: float = Field(default=0.0, gt=-1)
    collateral_haircut: float = Field(default=0.0, ge=0, lt=1)
    collateral_fx_rate: float = Field(default=1.0, gt=0)
    maximum_gross_notional: float | None = Field(default=None, gt=0)
    annualization: int = Field(default=252, ge=1)
    daily_loss_limit_fraction: float = Field(default=0.10, gt=0)
    enforce_position_limits: bool = False
    allow_physical_delivery: bool = False
    force_liquidate_on_margin_breach: bool = False

    @field_validator("position_quantity")
    @classmethod
    def futures_position_is_nonzero(cls, value: float) -> float:
        if value == 0:
            raise ValueError("position_quantity must be non-zero.")
        return value


class OptionSurfaceSmoothingParameters(StrictParameters):
    underlying_id: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    evaluated_at: str = Field(min_length=1)
    spot: float = Field(gt=0)
    risk_free_rate: float = 0.0
    dividend_yield: float = 0.0
    min_expiries: int = Field(default=2, ge=2)
    min_strikes_per_expiry: int = Field(default=3, ge=2)
    moneyness_grid: list[float] = Field(default=[-0.20, -0.10, 0.0, 0.10, 0.20], min_length=1)
    tenor_grid_years: list[float] = Field(default_factory=list)
    smoothing_window: int = Field(default=3, ge=1)
    smoothing_method: Literal[
        "rolling_median",
        "quadratic_total_variance",
        "cubic_total_variance",
        "svi_total_variance",
        "raw_svi_total_variance",
        "ssvi_total_variance",
    ] = "rolling_median"
    max_moneyness_gap: float = Field(default=0.25, gt=0)
    max_tenor_gap_years: float = Field(default=1.0, gt=0)
    max_iv_jump: float = Field(default=0.50, gt=0)
    enforce_arbitrage_free: bool = True
    calendar_variance_tolerance: float = Field(default=1e-8, ge=0)
    butterfly_convexity_tolerance: float = Field(default=1e-8, ge=0)

    @field_validator("evaluated_at")
    @classmethod
    def surface_evaluation_is_explicit_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("evaluated_at must include an explicit timezone.")
        return value

    @field_validator("moneyness_grid")
    @classmethod
    def moneyness_grid_is_sorted_and_unique(cls, value: list[float]) -> list[float]:
        if value != sorted(set(value)):
            raise ValueError("moneyness_grid must be sorted and unique.")
        return value

    @field_validator("tenor_grid_years")
    @classmethod
    def tenor_grid_is_positive_sorted(cls, value: list[float]) -> list[float]:
        if any(tenor <= 0 for tenor in value) or value != sorted(set(value)):
            raise ValueError("tenor_grid_years must be positive, sorted, and unique.")
        return value

    @field_validator("smoothing_window")
    @classmethod
    def smoothing_window_is_odd(cls, value: int) -> int:
        if value % 2 == 0:
            raise ValueError("smoothing_window must be odd.")
        return value


class OptionSurfaceParameters(StrictParameters):
    underlying_id: str | None = Field(default=None, min_length=1)
    expiry_at: str | None = Field(default=None, min_length=1)
    spot: float = Field(gt=0)
    risk_free_rate: float = 0.0
    dividend_yield: float = 0.0
    parity_tolerance: float = Field(default=0.01, ge=0)

    @field_validator("expiry_at")
    @classmethod
    def expiry_is_explicit_timezone(cls, value: str | None) -> str | None:
        if value is not None and pd.Timestamp(value).tzinfo is None:
            raise ValueError("expiry_at must include an explicit timezone.")
        return value


class OptionHedgeReplayParameters(StrictParameters):
    option_id: str = Field(min_length=1)
    option_quantity: float
    risk_free_rate: float = 0.0
    dividend_yield: float = 0.0
    transaction_cost_bps: float = Field(default=0.0, ge=0)
    max_spread_fraction: float = Field(default=0.20, gt=0)
    hedge_fill_mode: Literal["mid", "bid_ask"] = "mid"
    allow_american_exercise: bool = False

    @field_validator("option_quantity")
    @classmethod
    def option_position_is_nonzero(cls, value: float) -> float:
        if value == 0:
            raise ValueError("option_quantity must be non-zero.")
        return value


class FixedIncomeRiskParameters(StrictParameters):
    instrument_id: str | None = Field(default=None, min_length=1)
    valuation_at: str = Field(min_length=1)
    yield_rate: float = Field(gt=-1)
    parallel_shock_bps: float = Field(default=100.0, gt=0)

    @field_validator("valuation_at")
    @classmethod
    def valuation_is_explicit_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("valuation_at must include an explicit timezone.")
        return value


class CurveShockScenario(StrictParameters):
    name: str = Field(min_length=1)
    parallel_bps: float = 0.0
    node_shocks_bps: dict[str, float] = Field(default_factory=dict)

    @field_validator("node_shocks_bps")
    @classmethod
    def node_tenors_are_positive_numbers(cls, value: dict[str, float]) -> dict[str, float]:
        if any(float(key) <= 0 for key in value):
            raise ValueError("node_shocks_bps keys must be positive numeric tenors.")
        return value


class FixedIncomeCurveStressParameters(StrictParameters):
    instrument_id: str = Field(min_length=1)
    curve_id: str = Field(min_length=1)
    calendar_id: str = Field(min_length=1)
    valuation_at: str = Field(min_length=1)
    scenarios: list[CurveShockScenario] = Field(min_length=1)
    loss_limit_fraction: float = Field(default=0.10, gt=0)
    spread_curve_id: str | None = Field(default=None, min_length=1)
    require_spread_curve: bool = False
    projection_curve_id: str | None = Field(default=None, min_length=1)
    call_price_per_100: float | None = Field(default=None, gt=0)
    call_style: Literal["american", "bermudan"] = "american"
    rate_volatility: float = Field(default=0.0, ge=0)
    market_dirty_price: float | None = Field(default=None, gt=0)

    @field_validator("valuation_at")
    @classmethod
    def curve_valuation_is_explicit_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("valuation_at must include an explicit timezone.")
        return value

    @field_validator("scenarios")
    @classmethod
    def curve_scenario_names_are_unique(
        cls,
        value: list[CurveShockScenario],
    ) -> list[CurveShockScenario]:
        names = [scenario.name for scenario in value]
        if len(names) != len(set(names)):
            raise ValueError("curve scenario names must be unique.")
        return value
    @model_validator(mode="after")
    def required_spread_curve_has_id(self) -> FixedIncomeCurveStressParameters:
        if self.require_spread_curve and self.spread_curve_id is None:
            raise ValueError("require_spread_curve requires spread_curve_id.")
        return self


class FixedIncomePriceReconciliationParameters(StrictParameters):
    instrument_id: str = Field(min_length=1)
    valuation_at: str = Field(min_length=1)
    venue: str | None = Field(default=None, min_length=1)
    max_quote_age: str = "1D"
    maximum_price_error: float = Field(default=1e-8, ge=0)
    maximum_coupon_error: float = Field(default=1e-8, ge=0)
    require_irregular_stub: bool = False

    @field_validator("valuation_at")
    @classmethod
    def fixed_income_price_valuation_has_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("valuation_at must include an explicit timezone.")
        return value

    @field_validator("max_quote_age")
    @classmethod
    def fixed_income_quote_age_is_positive(cls, value: str) -> str:
        try:
            duration = pd.Timedelta(value)
        except ValueError as exc:
            raise ValueError("max_quote_age must be a pandas-compatible duration.") from exc
        if duration <= pd.Timedelta(0):
            raise ValueError("max_quote_age must be positive.")
        return value


class CreditMigrationParameters(StrictParameters):
    portfolio_id: str = Field(min_length=1)
    matrix_id: str = Field(min_length=1)
    evaluated_at: str = Field(min_length=1)
    default_rating: str = Field(default="D", min_length=1)
    rating_spreads_bps: dict[str, float] = Field(min_length=1)
    rating_liquidity_bps: dict[str, float] = Field(default_factory=dict)
    default_probability_multiplier: float = Field(default=1.0, ge=1)
    loss_limit_fraction: float = Field(default=0.05, gt=0)
    row_sum_tolerance: float = Field(default=1e-8, gt=0)
    recovery_volatility: float = Field(default=0.0, ge=0)
    recovery_confidence: float = Field(default=0.95, gt=0.5, lt=1)
    migration_correlation: float = Field(default=0.0, ge=0, lt=1)
    tail_confidence: float = Field(default=0.99, gt=0.5, lt=1)
    tail_loss_limit_fraction: float | None = Field(default=None, gt=0)
    realized_default_settlement_fraction: float | None = Field(default=None, ge=0, le=1)

    @field_validator("evaluated_at")
    @classmethod
    def credit_evaluation_is_explicit_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("evaluated_at must include an explicit timezone.")
        return value

    @field_validator("rating_spreads_bps")
    @classmethod
    def credit_spreads_are_non_negative(cls, value: dict[str, float]) -> dict[str, float]:
        if any(spread < 0 for spread in value.values()):
            raise ValueError("rating_spreads_bps must be non-negative.")
        return value

    @field_validator("rating_liquidity_bps")
    @classmethod
    def credit_liquidity_is_non_negative(cls, value: dict[str, float]) -> dict[str, float]:
        if any(liq < 0 for liq in value.values()):
            raise ValueError("rating_liquidity_bps must be non-negative.")
        return value

    @model_validator(mode="after")
    def credit_liquidity_keys_subset_of_spreads(self) -> CreditMigrationParameters:
        unknown = set(self.rating_liquidity_bps) - set(self.rating_spreads_bps)
        if unknown:
            raise ValueError(f"rating_liquidity_bps has unknown ratings: {sorted(unknown)}")
        return self


class FXRolloverParameters(StrictParameters):
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    quote_currency: str | None = Field(default=None, min_length=3, max_length=3)
    base_rate: float
    quote_rate: float
    tenor_days: int = Field(ge=1)
    notional_base: float = Field(default=1.0, gt=0)


class FXForwardCheckParameters(StrictParameters):
    base_currency: str = Field(min_length=3, max_length=3)
    quote_currency: str = Field(min_length=3, max_length=3)
    base_calendar_id: str = Field(min_length=1)
    quote_calendar_id: str = Field(min_length=1)
    base_rate: float
    quote_rate: float
    base_rate_bid: float | None = None
    base_rate_ask: float | None = None
    quote_rate_bid: float | None = None
    quote_rate_ask: float | None = None
    cross_currency_basis_bps: float = 0.0
    tenor_days: int = Field(ge=1)
    settlement_lag_business_days: int = Field(default=2, ge=0)
    notional_base: float = Field(default=1.0, gt=0)
    deviation_tolerance_bps: float = Field(default=5.0, ge=0)
    allow_broken_date_interpolation: bool = False
    cls_cutoff_utc: str | None = Field(default=None, min_length=4)
    enforce_cls_cutoff: bool = False
    maximum_funding_notional: float | None = Field(default=None, gt=0)
    cls_member_venues: list[str] = Field(default_factory=list)
    nostro_capacity_base: float | None = Field(default=None, gt=0)
    settlement_fail_probability: float = Field(default=0.0, ge=0, le=1)
    settlement_fail_lgd: float = Field(default=1.0, ge=0, le=1)
    settlement_fail_loss_limit: float | None = Field(default=None, ge=0)
    settlement_side: Literal["buy_base", "sell_base"] = "buy_base"
    require_replacement_cost: bool = False
    replacement_evaluated_at: str | None = None
    spot_venue: str | None = Field(default=None, min_length=1)
    forward_venue: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def fx_currencies_differ(self) -> FXForwardCheckParameters:
        if self.base_currency == self.quote_currency:
            raise ValueError("base_currency and quote_currency must differ.")
        for pair in (
            (self.base_rate_bid, self.base_rate_ask),
            (self.quote_rate_bid, self.quote_rate_ask),
        ):
            if pair[0] is not None and pair[1] is not None and pair[0] > pair[1]:
                raise ValueError("rate bid cannot exceed rate ask.")
        return self

    @field_validator("cls_cutoff_utc")
    @classmethod
    def cls_cutoff_is_hhmm(cls, value: str | None) -> str | None:
        if value is None:
            return value
        parts = value.split(":")
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("cls_cutoff_utc must be HH:MM.")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("cls_cutoff_utc must be a valid UTC clock time.")
        return f"{hour:02d}:{minute:02d}"

    @field_validator("cls_member_venues")
    @classmethod
    def cls_venues_are_unique(cls, value: list[str]) -> list[str]:
        if any(not venue for venue in value) or len(value) != len(set(value)):
            raise ValueError("cls_member_venues must contain unique non-empty venues.")
        return value


class CryptoCrossMarginParameters(StrictParameters):
    venue: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    evaluated_at: str = Field(min_length=1)
    initial_collateral: float = Field(gt=0)
    collateral_haircut: float = Field(default=0.0, ge=0, lt=1)
    collateral_fx_rates: dict[str, float] = Field(default_factory=dict)
    insurance_fund: float = Field(default=0.0, ge=0)
    venue_default_recovery_rate: float = Field(default=0.0, ge=0, le=1)
    venue_default_loss_limit_fraction: float = Field(default=0.20, gt=0)
    funding_rates: dict[str, float] = Field(default_factory=dict)
    stress_shocks: list[float] = Field(default=[-0.30, -0.10, 0.10], min_length=1)
    adl_ranking: Literal["pnl_leverage", "unrealized_pnl"] = "pnl_leverage"
    liquidation_mode: Literal["all_or_nothing", "sequential"] = "all_or_nothing"
    order_book_impact_bps: float = Field(default=0.0, ge=0)
    intraday_path: list[float] = Field(default_factory=list)

    @field_validator("intraday_path")
    @classmethod
    def intraday_path_preserves_prices(cls, value: list[float]) -> list[float]:
        if any(shock <= -1 for shock in value):
            raise ValueError("intraday_path shocks must be greater than -1.")
        return value

    @field_validator("evaluated_at")
    @classmethod
    def crypto_evaluation_is_explicit_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("evaluated_at must include an explicit timezone.")
        return value

    @field_validator("stress_shocks")
    @classmethod
    def cross_margin_shocks_preserve_prices(cls, value: list[float]) -> list[float]:
        if any(shock <= -1 for shock in value) or len(value) != len(set(value)):
            raise ValueError("stress_shocks must be unique and greater than -1.")
        return value

    @field_validator("collateral_fx_rates")
    @classmethod
    def collateral_fx_rates_are_positive(cls, value: dict[str, float]) -> dict[str, float]:
        if any(rate <= 0 for rate in value.values()):
            raise ValueError("collateral_fx_rates must be positive.")
        return value


class CryptoMarginStressParameters(StrictParameters):
    venue: str | None = Field(default=None, min_length=1)
    instrument_id: str | None = Field(default=None, min_length=1)
    signed_quantity: float
    initial_equity: float = Field(gt=0)
    maintenance_margin_rate: float = Field(gt=0, lt=1)
    funding_rate: float = 0.0
    stress_shocks: list[float] = Field(default=[-0.20, -0.10, 0.10], min_length=1)

    @field_validator("signed_quantity")
    @classmethod
    def quantity_is_nonzero(cls, value: float) -> float:
        if value == 0:
            raise ValueError("signed_quantity must be non-zero.")
        return value

    @field_validator("stress_shocks")
    @classmethod
    def shocks_preserve_positive_prices(cls, values: list[float]) -> list[float]:
        if any(value <= -1 for value in values) or len(values) != len(set(values)):
            raise ValueError("stress_shocks must be unique and greater than -1.")
        return values


class StressScenario(StrictParameters):
    name: str = Field(min_length=1)
    asset_shocks: dict[str, float] = Field(min_length=1)
    cash_shock: float = 0.0


class PortfolioStressParameters(StrictParameters):
    label: str | None = Field(default=None, min_length=1)
    return_basis: Literal["gross", "excess"] | None = None
    weight_type: str | None = Field(default=None, min_length=1)
    confidence: float = Field(default=0.95, gt=0.5, lt=1)
    loss_limit: float = Field(default=0.10, gt=0)
    scenarios: list[StressScenario] = Field(min_length=1)

    @field_validator("scenarios")
    @classmethod
    def scenario_names_are_unique(cls, values: list[StressScenario]) -> list[StressScenario]:
        names = [value.name for value in values]
        if len(names) != len(set(names)):
            raise ValueError("scenario names must be unique.")
        return values


class SignalHealthParameters(StrictParameters):
    signal: str | None = Field(default=None, min_length=1)
    label: str | None = Field(default=None, min_length=1)
    evaluated_at: str = Field(min_length=1)
    max_signal_age: str = "2D"
    min_assets: int = Field(default=5, ge=2)
    recent_periods: int = Field(default=3, ge=1)
    min_baseline_periods: int = Field(default=5, ge=1)
    min_recent_rank_ic: float = Field(default=0.0, ge=-1, le=1)
    max_rank_ic_degradation: float = Field(default=0.10, ge=0, le=2)
    min_latest_std: float = Field(default=1e-12, ge=0)

    @field_validator("evaluated_at")
    @classmethod
    def evaluation_is_explicit_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("evaluated_at must include an explicit timezone.")
        return value

    @field_validator("max_signal_age")
    @classmethod
    def signal_age_is_non_negative_duration(cls, value: str) -> str:
        duration = pd.Timedelta(value)
        if duration < pd.Timedelta(0):
            raise ValueError("max_signal_age must be non-negative.")
        return value


class SourceRuleFreshnessParameters(StrictParameters):
    required_source_ids: list[str] = Field(min_length=1)
    evaluated_at: str = Field(min_length=1)
    max_card_age: str = "365D"
    require_authoritative: bool = True
    require_change_approval: bool = False
    max_approval_age: str = "365D"

    @field_validator("required_source_ids")
    @classmethod
    def source_ids_are_unique(cls, value: list[str]) -> list[str]:
        if any(not source_id for source_id in value) or len(value) != len(set(value)):
            raise ValueError("required_source_ids must contain unique non-empty IDs.")
        return value

    @field_validator("evaluated_at")
    @classmethod
    def source_evaluation_has_timezone(cls, value: str) -> str:
        if pd.Timestamp(value).tzinfo is None:
            raise ValueError("evaluated_at must include an explicit timezone.")
        return value

    @field_validator("max_card_age", "max_approval_age")
    @classmethod
    def source_age_is_positive(cls, value: str) -> str:
        try:
            duration = pd.Timedelta(value)
        except ValueError as exc:
            raise ValueError("source-rule ages must be pandas-compatible.") from exc
        if duration <= pd.Timedelta(0):
            raise ValueError("source-rule ages must be positive.")
        return value
