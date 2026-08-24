"""Canonical table contracts and semantic field definitions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LogicalType = Literal["string", "integer", "number", "boolean", "date", "timestamp", "json"]


class FieldContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    logical_type: LogicalType
    required: bool = True
    nullable: bool = False
    unit: str | None = None
    description: str = ""


class TableContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_type: str = Field(min_length=1)
    schema_version: str = "1.0"
    fields: list[FieldContract]
    primary_key: list[str] = Field(default_factory=list)
    timestamp_fields: list[str] = Field(default_factory=list)
    description: str = ""

    @property
    def required_columns(self) -> list[str]:
        return [field.name for field in self.fields if field.required]


CONTRACTS: dict[str, TableContract] = {}


def _register(contract: TableContract) -> TableContract:
    if contract.table_type in CONTRACTS:
        raise ValueError(f"Duplicate table contract: {contract.table_type}")
    CONTRACTS[contract.table_type] = contract
    return contract


SECURITY_MASTER = _register(
    TableContract(
        table_type="security_master",
        description="Effective-dated permanent identifiers and tradable symbols.",
        primary_key=["asset_id", "effective_from"],
        timestamp_fields=["effective_from", "effective_to"],
        fields=[
            FieldContract(
                name="asset_id",
                logical_type="string",
                description="Permanent instrument identifier.",
            ),
            FieldContract(name="symbol", logical_type="string"),
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="asset_class", logical_type="string"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="effective_from", logical_type="timestamp"),
            FieldContract(
                name="effective_to", logical_type="timestamp", required=False, nullable=True
            ),
        ],
    )
)

MARKET_BARS = _register(
    TableContract(
        table_type="market_bars",
        description="Timestamped market bars with explicit currency and adjustment state.",
        primary_key=["timestamp", "asset_id", "adjustment_state"],
        timestamp_fields=["timestamp"],
        fields=[
            FieldContract(name="timestamp", logical_type="timestamp"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="open", logical_type="number", required=False, nullable=True, unit="price"),
            FieldContract(name="high", logical_type="number", required=False, nullable=True, unit="price"),
            FieldContract(name="low", logical_type="number", required=False, nullable=True, unit="price"),
            FieldContract(name="close", logical_type="number", unit="price"),
            FieldContract(
                name="volume", logical_type="number", required=False, nullable=True, unit="quantity"
            ),
            FieldContract(
                name="open_interest", logical_type="number", required=False, nullable=True, unit="quantity"
            ),
            FieldContract(
                name="turnover", logical_type="number", required=False, nullable=True, unit="currency"
            ),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="adjustment_state", logical_type="string"),
        ],
    )
)

MARKET_QUOTES = _register(
    TableContract(
        table_type="market_quotes",
        description="Timestamped bid/ask snapshots for deterministic offline execution replay.",
        primary_key=["timestamp", "asset_id", "venue"],
        timestamp_fields=["timestamp"],
        fields=[
            FieldContract(name="timestamp", logical_type="timestamp"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="bid", logical_type="number", unit="price"),
            FieldContract(name="ask", logical_type="number", unit="price"),
            FieldContract(name="volume", logical_type="number", unit="quantity"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="venue", logical_type="string"),
        ],
    )
)

CORPORATE_ACTIONS = _register(
    TableContract(
        table_type="corporate_actions",
        description="Corporate actions with announcement, availability, and vendor revisions.",
        primary_key=["asset_id", "action_id", "available_at"],
        timestamp_fields=["announced_at", "available_at", "effective_at"],
        fields=[
            FieldContract(name="action_id", logical_type="string"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="action_type", logical_type="string"),
            FieldContract(name="announced_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="effective_at", logical_type="timestamp"),
            FieldContract(name="value", logical_type="number", required=False, nullable=True),
            FieldContract(name="currency", logical_type="string", required=False, nullable=True),
        ],
    )
)

UNIVERSE_MEMBERSHIP = _register(
    TableContract(
        table_type="universe_membership",
        description="Effective-dated and point-in-time-observable universe membership.",
        primary_key=["universe_id", "asset_id", "effective_from"],
        timestamp_fields=["effective_from", "effective_to", "available_at"],
        fields=[
            FieldContract(name="universe_id", logical_type="string"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="effective_from", logical_type="timestamp"),
            FieldContract(
                name="effective_to", logical_type="timestamp", required=False, nullable=True
            ),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="eligible", logical_type="boolean"),
        ],
    )
)

BORROW_AVAILABILITY = _register(
    TableContract(
        table_type="borrow_availability",
        description="Point-in-time effective borrow eligibility and indicative annual fee.",
        primary_key=["asset_id", "effective_from"],
        timestamp_fields=["effective_from", "effective_to", "available_at"],
        fields=[
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="effective_from", logical_type="timestamp"),
            FieldContract(
                name="effective_to", logical_type="timestamp", required=False, nullable=True
            ),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="borrowable", logical_type="boolean"),
            FieldContract(name="fee_rate_annual", logical_type="number"),
            FieldContract(
                name="max_quantity", logical_type="number", required=False, nullable=True
            ),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

BORROW_LOCATES = _register(
    TableContract(
        table_type="borrow_locates",
        description="Point-in-time short-borrow locate quantities, fees, expiries, and recalls.",
        primary_key=["locate_id", "available_at"],
        timestamp_fields=[
            "available_at",
            "effective_from",
            "expires_at",
            "recalled_at",
        ],
        fields=[
            FieldContract(name="locate_id", logical_type="string"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="effective_from", logical_type="timestamp"),
            FieldContract(name="expires_at", logical_type="timestamp"),
            FieldContract(
                name="recalled_at", logical_type="timestamp", required=False, nullable=True
            ),
            FieldContract(name="located_quantity", logical_type="number", unit="shares"),
            FieldContract(name="remaining_quantity", logical_type="number", unit="shares"),
            FieldContract(name="fee_rate_annual", logical_type="number", unit="decimal_rate"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="status", logical_type="string"),
            FieldContract(
                name="lender_id", logical_type="string", required=False, nullable=True
            ),
        ],
    )
)

FUNDAMENTALS_PIT = _register(
    TableContract(
        table_type="fundamentals_pit",
        description="Versioned fundamental observations as available at each decision time.",
        primary_key=["asset_id", "field", "period_end", "available_at"],
        timestamp_fields=["period_end", "announced_at", "available_at", "revision_at"],
        fields=[
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="field", logical_type="string"),
            FieldContract(name="value", logical_type="number"),
            FieldContract(name="period_end", logical_type="timestamp"),
            FieldContract(name="announced_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="revision_at", logical_type="timestamp", required=False, nullable=True),
            FieldContract(name="currency", logical_type="string", required=False, nullable=True),
            FieldContract(name="unit", logical_type="string", required=False, nullable=True),
        ],
    )
)

FACTOR_PANEL = _register(
    TableContract(
        table_type="factor_panel",
        description="Point-in-time factor values keyed by decision timestamp and asset.",
        primary_key=["as_of", "asset_id", "signal"],
        timestamp_fields=["as_of", "available_at"],
        fields=[
            FieldContract(name="as_of", logical_type="timestamp"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="signal", logical_type="string"),
            FieldContract(name="value", logical_type="number"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="transform_chain", logical_type="json", required=False, nullable=True),
        ],
    )
)

FACTOR_EXPOSURES = _register(
    TableContract(
        table_type="factor_exposures",
        description="Point-in-time standardized asset exposures for a declared factor model.",
        primary_key=["as_of", "factor_model_id", "asset_id", "factor_id"],
        timestamp_fields=["as_of", "available_at"],
        fields=[
            FieldContract(name="as_of", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="factor_model_id", logical_type="string"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="factor_id", logical_type="string"),
            FieldContract(name="exposure", logical_type="number"),
        ],
    )
)

FACTOR_RETURNS = _register(
    TableContract(
        table_type="factor_returns",
        description="Realized factor returns aligned to one explicit attribution window.",
        primary_key=["factor_model_id", "return_start", "return_end", "factor_id"],
        timestamp_fields=["return_start", "return_end", "available_at"],
        fields=[
            FieldContract(name="factor_model_id", logical_type="string"),
            FieldContract(name="factor_id", logical_type="string"),
            FieldContract(name="return_start", logical_type="timestamp"),
            FieldContract(name="return_end", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="return_value", logical_type="number", unit="decimal_return"),
            FieldContract(name="return_type", logical_type="string"),
            FieldContract(name="return_basis", logical_type="string"),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

MODEL_PREDICTIONS = _register(
    TableContract(
        table_type="model_predictions",
        description="Point-in-time model predictions aligned to an asset decision and target label.",
        primary_key=["decision_at", "model_id", "model_version", "asset_id", "target_label"],
        timestamp_fields=["decision_at", "available_at"],
        fields=[
            FieldContract(name="decision_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="model_id", logical_type="string"),
            FieldContract(name="model_version", logical_type="string"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="target_label", logical_type="string"),
            FieldContract(name="prediction", logical_type="number"),
            FieldContract(name="prediction_type", logical_type="string"),
        ],
    )
)

SERVICE_HEALTH_WINDOWS = _register(
    TableContract(
        table_type="service_health_windows",
        description="Observable service availability, traffic, error, and latency windows.",
        primary_key=["service_id", "environment", "window_start", "window_end"],
        timestamp_fields=["window_start", "window_end", "available_at"],
        fields=[
            FieldContract(name="service_id", logical_type="string"),
            FieldContract(name="environment", logical_type="string"),
            FieldContract(name="window_start", logical_type="timestamp"),
            FieldContract(name="window_end", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="status", logical_type="string"),
            FieldContract(name="request_count", logical_type="integer"),
            FieldContract(name="error_count", logical_type="integer"),
            FieldContract(name="uptime_fraction", logical_type="number"),
            FieldContract(name="latency_p95_ms", logical_type="number", unit="milliseconds"),
        ],
    )
)

RETURN_LABELS = _register(
    TableContract(
        table_type="return_labels",
        description="Execution-aligned forward return labels with explicit end time.",
        primary_key=["decision_at", "asset_id", "label"],
        timestamp_fields=["decision_at", "execution_at", "return_start", "return_end"],
        fields=[
            FieldContract(name="decision_at", logical_type="timestamp"),
            FieldContract(name="execution_at", logical_type="timestamp"),
            FieldContract(name="return_start", logical_type="timestamp"),
            FieldContract(name="return_end", logical_type="timestamp"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="label", logical_type="string"),
            FieldContract(name="return_value", logical_type="number", unit="decimal_return"),
            FieldContract(name="return_type", logical_type="string"),
            FieldContract(name="return_basis", logical_type="string"),
            FieldContract(name="corporate_action_policy", logical_type="string"),
            FieldContract(name="benchmark", logical_type="string", required=False, nullable=True),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

FINANCING_CURVES = _register(
    TableContract(
        table_type="financing_curves",
        description="Point-in-time cash-deposit and unsecured-financing simple annual-rate curves.",
        primary_key=["curve_id", "currency", "rate_type", "effective_from", "tenor_days"],
        timestamp_fields=["effective_from", "effective_to", "available_at"],
        fields=[
            FieldContract(name="curve_id", logical_type="string"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="rate_type", logical_type="string"),
            FieldContract(name="effective_from", logical_type="timestamp"),
            FieldContract(
                name="effective_to", logical_type="timestamp", required=False, nullable=True
            ),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="tenor_days", logical_type="integer", unit="calendar_days"),
            FieldContract(name="annual_rate", logical_type="number", unit="decimal_rate"),
            FieldContract(name="day_count_basis", logical_type="string"),
            FieldContract(name="compounding", logical_type="string"),
        ],
    )
)

PORTFOLIO_WEIGHTS = _register(
    TableContract(
        table_type="portfolio_weights",
        description="Decision-timestamped target or actual portfolio weights.",
        primary_key=["decision_at", "asset_id", "weight_type"],
        timestamp_fields=["decision_at"],
        fields=[
            FieldContract(name="decision_at", logical_type="timestamp"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="weight", logical_type="number", unit="fraction_of_nav"),
            FieldContract(name="weight_type", logical_type="string"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(
                name="nav",
                logical_type="number",
                required=False,
                nullable=True,
                unit="currency",
            ),
        ],
    )
)

ORDERS = _register(
    TableContract(
        table_type="orders",
        description="Orders with decision, submission, status, and venue evidence.",
        primary_key=["order_id"],
        timestamp_fields=["decision_at", "submitted_at", "acknowledged_at", "expires_at"],
        fields=[
            FieldContract(name="order_id", logical_type="string"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="decision_at", logical_type="timestamp"),
            FieldContract(name="submitted_at", logical_type="timestamp"),
            FieldContract(
                name="acknowledged_at", logical_type="timestamp", required=False, nullable=True
            ),
            FieldContract(name="side", logical_type="string"),
            FieldContract(name="quantity", logical_type="number", unit="quantity"),
            FieldContract(name="order_type", logical_type="string"),
            FieldContract(
                name="limit_price", logical_type="number", required=False, nullable=True, unit="price"
            ),
            FieldContract(
                name="expires_at", logical_type="timestamp", required=False, nullable=True
            ),
            FieldContract(
                name="time_in_force", logical_type="string", required=False, nullable=True
            ),
            FieldContract(
                name="queue_priority",
                logical_type="integer",
                required=False,
                nullable=True,
            ),
            FieldContract(
                name="amended_at",
                logical_type="timestamp",
                required=False,
                nullable=True,
            ),
            FieldContract(
                name="amend_limit_price",
                logical_type="number",
                required=False,
                nullable=True,
                unit="price",
            ),
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="status", logical_type="string"),
        ],
    )
)

FILLS = _register(
    TableContract(
        table_type="fills",
        description="Execution fills linked to orders.",
        primary_key=["fill_id"],
        timestamp_fields=["filled_at"],
        fields=[
            FieldContract(name="fill_id", logical_type="string"),
            FieldContract(name="order_id", logical_type="string"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="filled_at", logical_type="timestamp"),
            FieldContract(name="quantity", logical_type="number", unit="quantity"),
            FieldContract(name="price", logical_type="number", unit="price"),
            FieldContract(name="fees", logical_type="number", unit="currency"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="venue", logical_type="string"),
        ],
    )
)

CALENDAR_SESSIONS = _register(
    TableContract(
        table_type="calendar_sessions",
        description="Effective exchange sessions with timezone-aware open and close times.",
        primary_key=["calendar_id", "session"],
        timestamp_fields=["open_at", "close_at"],
        fields=[
            FieldContract(name="calendar_id", logical_type="string"),
            FieldContract(name="session", logical_type="date"),
            FieldContract(name="timezone", logical_type="string"),
            FieldContract(name="open_at", logical_type="timestamp"),
            FieldContract(name="close_at", logical_type="timestamp"),
            FieldContract(name="is_half_day", logical_type="boolean", required=False, nullable=True),
        ],
    )
)


FUTURES_CONTRACTS = _register(
    TableContract(
        table_type="futures_contracts",
        description="Effective futures contract lifecycle and economic terms.",
        primary_key=["contract_id"],
        timestamp_fields=["listed_at", "first_notice_at", "last_trade_at", "expiry_at"],
        fields=[
            FieldContract(name="contract_id", logical_type="string"),
            FieldContract(name="root", logical_type="string"),
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="multiplier", logical_type="number"),
            FieldContract(name="tick_size", logical_type="number"),
            FieldContract(name="listed_at", logical_type="timestamp"),
            FieldContract(
                name="first_notice_at", logical_type="timestamp", required=False, nullable=True
            ),
            FieldContract(name="last_trade_at", logical_type="timestamp"),
            FieldContract(name="expiry_at", logical_type="timestamp"),
            FieldContract(name="settlement_type", logical_type="string"),
        ],
    )
)

FUTURES_MARGIN_TERMS = _register(
    TableContract(
        table_type="futures_margin_terms",
        description="PIT contract margin requirements and exchange daily price limits.",
        primary_key=["venue", "contract_id", "effective_from"],
        timestamp_fields=["effective_from", "available_at"],
        fields=[
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="contract_id", logical_type="string"),
            FieldContract(name="effective_from", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="initial_margin_per_contract", logical_type="number"),
            FieldContract(name="maintenance_margin_per_contract", logical_type="number"),
            FieldContract(name="daily_price_limit_fraction", logical_type="number"),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

FUTURES_POSITION_LIMITS = _register(
    TableContract(
        table_type="futures_position_limits",
        description="PIT exchange or venue position limits per futures contract.",
        primary_key=["venue", "contract_id", "effective_from"],
        timestamp_fields=["effective_from", "available_at"],
        fields=[
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="contract_id", logical_type="string"),
            FieldContract(name="effective_from", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="max_contracts", logical_type="number"),
            FieldContract(name="limit_source", logical_type="string"),
        ],
    )
)

OPTION_CONTRACTS = _register(
    TableContract(
        table_type="option_contracts",
        description="Effective option terms and underlying linkage.",
        primary_key=["option_id"],
        timestamp_fields=["listed_at", "expiry_at"],
        fields=[
            FieldContract(name="option_id", logical_type="string"),
            FieldContract(name="underlying_id", logical_type="string"),
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="option_type", logical_type="string"),
            FieldContract(name="strike", logical_type="number", unit="price"),
            FieldContract(name="expiry_at", logical_type="timestamp"),
            FieldContract(name="exercise_style", logical_type="string"),
            FieldContract(name="settlement_type", logical_type="string"),
            FieldContract(name="multiplier", logical_type="number"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="listed_at", logical_type="timestamp"),
        ],
    )
)

OPTION_EXERCISE_EVENTS = _register(
    TableContract(
        table_type="option_exercise_events",
        description="PIT offline American option exercise or assignment events.",
        primary_key=["option_id", "event_at", "event_type"],
        timestamp_fields=["event_at", "available_at"],
        fields=[
            FieldContract(name="option_id", logical_type="string"),
            FieldContract(name="event_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="event_type", logical_type="string"),
            FieldContract(name="quantity", logical_type="number"),
            FieldContract(name="underlying_price", logical_type="number", unit="price"),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

CREDIT_EXPOSURES = _register(
    TableContract(
        table_type="credit_exposures",
        description="Point-in-time credit exposures with rating, duration, and recovery assumptions.",
        primary_key=["observed_at", "portfolio_id", "instrument_id"],
        timestamp_fields=["observed_at", "available_at"],
        fields=[
            FieldContract(name="observed_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="portfolio_id", logical_type="string"),
            FieldContract(name="instrument_id", logical_type="string"),
            FieldContract(name="rating", logical_type="string"),
            FieldContract(name="market_value", logical_type="number"),
            FieldContract(name="modified_duration", logical_type="number"),
            FieldContract(
                name="convexity", logical_type="number", required=False, nullable=True
            ),
            FieldContract(name="recovery_rate", logical_type="number"),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

CREDIT_TRANSITION_MATRIX = _register(
    TableContract(
        table_type="credit_transition_matrix",
        description="PIT rating-transition probabilities including an explicit default state.",
        primary_key=["matrix_id", "observed_at", "from_rating", "to_rating"],
        timestamp_fields=["observed_at", "available_at"],
        fields=[
            FieldContract(name="matrix_id", logical_type="string"),
            FieldContract(name="observed_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="horizon_years", logical_type="number"),
            FieldContract(name="from_rating", logical_type="string"),
            FieldContract(name="to_rating", logical_type="string"),
            FieldContract(name="probability", logical_type="number"),
        ],
    )
)

YIELD_CURVE_NODES = _register(
    TableContract(
        table_type="yield_curve_nodes",
        description="Point-in-time zero-rate curve nodes with explicit compounding and currency.",
        primary_key=["curve_id", "observed_at", "tenor_years"],
        timestamp_fields=["observed_at", "available_at"],
        fields=[
            FieldContract(name="curve_id", logical_type="string"),
            FieldContract(name="observed_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="tenor_years", logical_type="number"),
            FieldContract(name="zero_rate", logical_type="number"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="compounding", logical_type="string"),
        ],
    )
)

FIXED_INCOME_SPREAD_NODES = _register(
    TableContract(
        table_type="fixed_income_spread_nodes",
        description="PIT instrument spread nodes applied to risk-free zero-rate discounting.",
        primary_key=["spread_curve_id", "instrument_id", "observed_at", "tenor_years"],
        timestamp_fields=["observed_at", "available_at"],
        fields=[
            FieldContract(name="spread_curve_id", logical_type="string"),
            FieldContract(name="instrument_id", logical_type="string"),
            FieldContract(name="observed_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="tenor_years", logical_type="number"),
            FieldContract(name="spread_bps", logical_type="number", unit="basis_points"),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

FIXED_INCOME_INSTRUMENTS = _register(
    TableContract(
        table_type="fixed_income_instruments",
        description="Bond and fixed-income terms required to reconstruct cashflows.",
        primary_key=["instrument_id"],
        timestamp_fields=["issue_at", "maturity_at"],
        fields=[
            FieldContract(name="instrument_id", logical_type="string"),
            FieldContract(name="issuer_id", logical_type="string"),
            FieldContract(name="currency", logical_type="string"),
            FieldContract(name="issue_at", logical_type="timestamp"),
            FieldContract(name="maturity_at", logical_type="timestamp"),
            FieldContract(name="coupon_rate", logical_type="number"),
            FieldContract(name="coupon_frequency", logical_type="integer"),
            FieldContract(
                name="coupon_type",
                logical_type="string",
                required=False,
                nullable=True,
                description="fixed or floating; omitted means fixed for compatibility.",
            ),
            FieldContract(
                name="coupon_spread_bps",
                logical_type="number",
                required=False,
                nullable=True,
                unit="basis_points",
            ),
            FieldContract(
                name="amortization_type",
                logical_type="string",
                required=False,
                nullable=True,
                description="bullet or scheduled; omitted means bullet for compatibility.",
            ),
            FieldContract(
                name="ex_coupon_days",
                logical_type="integer",
                required=False,
                nullable=True,
                description="Calendar days before payment when accrued interest detaches.",
            ),
            FieldContract(name="day_count", logical_type="string"),
            FieldContract(name="business_day_convention", logical_type="string"),
            FieldContract(name="face_value", logical_type="number", unit="currency"),
        ],
    )
)

FIXED_INCOME_CASHFLOWS = _register(
    TableContract(
        table_type="fixed_income_cashflows",
        description="PIT explicit fixed-income accrual periods and contractual payments.",
        primary_key=["instrument_id", "cashflow_id", "available_at"],
        timestamp_fields=[
            "available_at",
            "accrual_start",
            "accrual_end",
            "payment_at",
        ],
        fields=[
            FieldContract(name="instrument_id", logical_type="string"),
            FieldContract(name="cashflow_id", logical_type="string"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="accrual_start", logical_type="timestamp"),
            FieldContract(name="accrual_end", logical_type="timestamp"),
            FieldContract(name="payment_at", logical_type="timestamp"),
            FieldContract(name="coupon_amount", logical_type="number", unit="currency"),
            FieldContract(name="principal_amount", logical_type="number", unit="currency"),
            FieldContract(
                name="coupon_rate",
                logical_type="number",
                required=False,
                nullable=True,
            ),
            FieldContract(
                name="principal_balance_start",
                logical_type="number",
                required=False,
                nullable=True,
                unit="currency",
            ),
            FieldContract(
                name="principal_balance_end",
                logical_type="number",
                required=False,
                nullable=True,
                unit="currency",
            ),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

FIXED_INCOME_RATE_FIXINGS = _register(
    TableContract(
        table_type="fixed_income_rate_fixings",
        description="PIT reference-rate fixings for floating fixed-income coupons.",
        primary_key=["instrument_id", "reset_at", "available_at"],
        timestamp_fields=["reset_at", "available_at"],
        fields=[
            FieldContract(name="instrument_id", logical_type="string"),
            FieldContract(name="reset_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="reference_rate", logical_type="number"),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

FIXED_INCOME_PRICE_QUOTES = _register(
    TableContract(
        table_type="fixed_income_price_quotes",
        description="PIT clean, dirty, and accrued fixed-income price observations per 100 face.",
        primary_key=["observed_at", "instrument_id", "venue"],
        timestamp_fields=["observed_at", "available_at", "settlement_at"],
        fields=[
            FieldContract(name="observed_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="settlement_at", logical_type="timestamp"),
            FieldContract(name="instrument_id", logical_type="string"),
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="clean_price", logical_type="number", unit="per_100_face"),
            FieldContract(name="dirty_price", logical_type="number", unit="per_100_face"),
            FieldContract(name="accrued_interest", logical_type="number", unit="per_100_face"),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)

FX_QUOTES = _register(
    TableContract(
        table_type="fx_quotes",
        description="Timestamped FX quotes stored as quote currency per base currency.",
        primary_key=["timestamp", "base_currency", "quote_currency", "venue"],
        timestamp_fields=["timestamp", "spot_date"],
        fields=[
            FieldContract(name="timestamp", logical_type="timestamp"),
            FieldContract(name="base_currency", logical_type="string"),
            FieldContract(name="quote_currency", logical_type="string"),
            FieldContract(name="bid", logical_type="number"),
            FieldContract(name="ask", logical_type="number"),
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="spot_date", logical_type="timestamp"),
        ],
    )
)

FX_FORWARD_QUOTES = _register(
    TableContract(
        table_type="fx_forward_quotes",
        description="Timestamped outright or decimal-points FX forward bid/ask quotes.",
        primary_key=["timestamp", "value_date", "base_currency", "quote_currency", "venue"],
        timestamp_fields=["timestamp"],
        fields=[
            FieldContract(name="timestamp", logical_type="timestamp"),
            FieldContract(name="value_date", logical_type="date"),
            FieldContract(name="base_currency", logical_type="string"),
            FieldContract(name="quote_currency", logical_type="string"),
            FieldContract(name="bid", logical_type="number"),
            FieldContract(name="ask", logical_type="number"),
            FieldContract(name="quote_type", logical_type="string"),
            FieldContract(name="venue", logical_type="string"),
        ],
    )
)

FX_REPLACEMENT_QUOTES = _register(
    TableContract(
        table_type="fx_replacement_quotes",
        description="PIT FX replacement quotes available at a settlement-fail evaluation time.",
        primary_key=[
            "observed_at",
            "available_at",
            "value_date",
            "base_currency",
            "quote_currency",
            "venue",
        ],
        timestamp_fields=["observed_at", "available_at"],
        fields=[
            FieldContract(name="observed_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="value_date", logical_type="date"),
            FieldContract(name="base_currency", logical_type="string"),
            FieldContract(name="quote_currency", logical_type="string"),
            FieldContract(name="bid", logical_type="number"),
            FieldContract(name="ask", logical_type="number"),
            FieldContract(name="venue", logical_type="string"),
        ],
    )
)


CRYPTO_POSITIONS = _register(
    TableContract(
        table_type="crypto_positions",
        description="Point-in-time venue-account positions with entry prices for offline stress.",
        primary_key=["observed_at", "venue", "account_id", "instrument_id"],
        timestamp_fields=["observed_at", "available_at"],
        fields=[
            FieldContract(name="observed_at", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="account_id", logical_type="string"),
            FieldContract(name="instrument_id", logical_type="string"),
            FieldContract(name="signed_quantity", logical_type="number"),
            FieldContract(name="entry_price", logical_type="number"),
        ],
    )
)

CRYPTO_MARGIN_TIERS = _register(
    TableContract(
        table_type="crypto_margin_tiers",
        description="Effective-dated linear-contract margin and liquidation-fee tiers.",
        primary_key=["venue", "instrument_id", "effective_from", "notional_floor"],
        timestamp_fields=["effective_from", "available_at"],
        fields=[
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="instrument_id", logical_type="string"),
            FieldContract(name="effective_from", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="notional_floor", logical_type="number"),
            FieldContract(
                name="notional_cap", logical_type="number", required=False, nullable=True
            ),
            FieldContract(name="initial_margin_rate", logical_type="number"),
            FieldContract(name="maintenance_margin_rate", logical_type="number"),
            FieldContract(name="liquidation_fee_rate", logical_type="number"),
        ],
    )
)

CRYPTO_INSTRUMENTS = _register(
    TableContract(
        table_type="crypto_instruments",
        description="Venue-specific crypto spot, perpetual, and dated-future terms.",
        primary_key=["venue", "instrument_id"],
        timestamp_fields=["listed_at", "delisted_at", "expiry_at"],
        fields=[
            FieldContract(name="venue", logical_type="string"),
            FieldContract(name="instrument_id", logical_type="string"),
            FieldContract(name="instrument_type", logical_type="string"),
            FieldContract(name="base_asset", logical_type="string"),
            FieldContract(name="quote_asset", logical_type="string"),
            FieldContract(name="settlement_asset", logical_type="string"),
            FieldContract(name="collateral_asset", logical_type="string"),
            FieldContract(name="multiplier", logical_type="number"),
            FieldContract(name="listed_at", logical_type="timestamp"),
            FieldContract(name="delisted_at", logical_type="timestamp", required=False, nullable=True),
            FieldContract(name="expiry_at", logical_type="timestamp", required=False, nullable=True),
            FieldContract(name="margin_mode", logical_type="string"),
        ],
    )
)


SYNTHETIC_PROBES = _register(
    TableContract(
        table_type="synthetic_probes",
        description="Independent synthetic reachability probes executed per service window.",
        primary_key=["service_id", "environment", "probe_start"],
        timestamp_fields=["probe_start", "probe_end", "available_at"],
        fields=[
            FieldContract(name="service_id", logical_type="string"),
            FieldContract(name="environment", logical_type="string"),
            FieldContract(name="probe_start", logical_type="timestamp"),
            FieldContract(name="probe_end", logical_type="timestamp"),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="probe_type", logical_type="string"),
            FieldContract(name="success", logical_type="boolean"),
            FieldContract(name="latency_ms", logical_type="number", unit="milliseconds"),
            FieldContract(name="status_code", logical_type="integer", required=False, nullable=True),
        ],
    )
)

SERVICE_DEPENDENCIES = _register(
    TableContract(
        table_type="service_dependencies",
        description="Effective-dated service dependency graph and recovery objectives.",
        primary_key=["service_id", "environment", "depends_on", "effective_from"],
        timestamp_fields=["effective_from", "effective_to", "available_at"],
        fields=[
            FieldContract(name="service_id", logical_type="string"),
            FieldContract(name="environment", logical_type="string"),
            FieldContract(name="depends_on", logical_type="string"),
            FieldContract(name="effective_from", logical_type="timestamp"),
            FieldContract(
                name="effective_to", logical_type="timestamp", required=False, nullable=True
            ),
            FieldContract(name="available_at", logical_type="timestamp"),
            FieldContract(name="recovery_time_objective", logical_type="number", unit="seconds"),
            FieldContract(name="recovery_point_objective", logical_type="number", unit="seconds"),
            FieldContract(name="region", logical_type="string", required=False, nullable=True),
        ],
    )
)


SOURCE_CHANGE_APPROVALS = _register(
    TableContract(
        table_type="source_change_approvals",
        description="Offline approvals for source-card refresh, add, or retire requests.",
        primary_key=["source_id", "approved_at", "action"],
        timestamp_fields=["requested_at", "approved_at"],
        fields=[
            FieldContract(name="source_id", logical_type="string"),
            FieldContract(name="requested_at", logical_type="timestamp"),
            FieldContract(name="approved_at", logical_type="timestamp"),
            FieldContract(name="approver", logical_type="string"),
            FieldContract(name="action", logical_type="string"),
            FieldContract(name="status", logical_type="string"),
        ],
    )
)

SOURCE_CARDS = _register(
    TableContract(
        table_type="source_cards",
        description="Effective-dated official or vendor source cards used to gate rule freshness.",
        primary_key=["source_id", "accessed_at"],
        timestamp_fields=["accessed_at"],
        fields=[
            FieldContract(name="source_id", logical_type="string"),
            FieldContract(name="source_kind", logical_type="string"),
            FieldContract(name="publisher", logical_type="string"),
            FieldContract(name="venue", logical_type="string", required=False, nullable=True),
            FieldContract(name="accessed_at", logical_type="timestamp"),
            FieldContract(name="effective_from", logical_type="string"),
            FieldContract(name="confidence", logical_type="string"),
            FieldContract(name="content_digest", logical_type="string"),
        ],
    )
)

TAX_LOTS = _register(
    TableContract(
        table_type="tax_lots",
        description="Open tax lots with acquisition time, remaining quantity, and cost basis.",
        primary_key=["lot_id"],
        timestamp_fields=["acquired_at"],
        fields=[
            FieldContract(name="lot_id", logical_type="string"),
            FieldContract(name="asset_id", logical_type="string"),
            FieldContract(name="acquired_at", logical_type="timestamp"),
            FieldContract(name="quantity", logical_type="number", unit="quantity"),
            FieldContract(name="cost_price", logical_type="number", unit="price"),
            FieldContract(name="currency", logical_type="string"),
        ],
    )
)


def get_table_contract(table_type: str) -> TableContract:
    try:
        return CONTRACTS[table_type]
    except KeyError as exc:
        known = ", ".join(sorted(CONTRACTS))
        raise KeyError(f"Unknown table type {table_type!r}. Known table types: {known}") from exc
