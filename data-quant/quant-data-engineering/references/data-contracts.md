# Canonical Quant Data Contracts

The machine definitions live in `../../src/data_quant/contracts/tables.py`; generated table schemas live in `../../schemas/tables/`. This reference explains all registered contracts and their intended use.

| Table | Primary purpose | Critical keys/times |
| --- | --- | --- |
| `security_master` | Permanent ID and effective symbol/venue mapping | asset ID, effective from/to |
| `market_bars` | Raw or explicitly adjusted OHLCV plus optional open interest | timestamp, asset ID, currency, adjustment state |
| `market_quotes` | Historical bid/ask observations for deterministic replay | timestamp, asset ID, venue, bid/ask |
| `corporate_actions` | Dividends, splits, rights, conversions, vendor revisions | asset/action IDs, announced, available, effective; versions keyed by available_at |
| `universe_membership` | Historical eligibility/index membership | universe, asset, effective interval, available time |
| `borrow_availability` | Point-in-time short-borrow eligibility and indicative fee | asset, effective interval, available time, fee, currency |
| `borrow_locates` | PIT locate lifecycle, remaining quantity, fee, expiry, recall, optional lender | locate/asset, available/effective/expiry/recall times, quantity/status, lender |
| `fundamentals_pit` | Versioned accounting/vendor facts | period end, announced, available, revision |
| `factor_panel` | Point-in-time signal observations | as-of, asset, signal, available time |
| `factor_exposures` | PIT standardized asset exposures for one factor model | as-of/available times, model, asset, factor, exposure |
| `factor_returns` | Realized factor returns aligned to an attribution window | model/factor, return start/end, available time, type/basis/currency |
| `fixed_income_cashflows` | PIT explicit coupon accrual periods, rates, balances, and contractual principal | instrument/cashflow, availability, accrual start/end, payment, coupon/principal/balance |
| `fixed_income_rate_fixings` | PIT reference-rate fixings for floating coupons | instrument, reset/available times, reference rate, currency |
| `fixed_income_price_quotes` | PIT clean/dirty/accrued fixed-income prices per 100 face | observation/availability/settlement, instrument/venue, clean/dirty/accrued |
| `model_predictions` | PIT model outputs aligned to decisions and target labels | decision/available times, model/version, asset, label, prediction type/value |
| `service_health_windows` | Observable service availability and traffic windows | service/environment, window/available times, status, requests/errors, uptime, p95 latency |
| `synthetic_probes` | Independent synthetic reachability probes per service window | service/environment, probe/available times, type, success, latency, status |
| `service_dependencies` | Effective-dated service dependency graph and recovery objectives | service/environment, dependency, effective/available times, RTO/RPO, region |
| `return_labels` | Execution-aligned forward outcomes | decision/execution/start/end, label, type/basis, corporate-action policy, currency |
| `financing_curves` | PIT cash-deposit and unsecured-financing simple annual curves | curve/currency/rate type, effective/available times, tenor, day count |
| `portfolio_weights` | Target or actual portfolio weights | decision, asset, weight type, currency, optional nav |
| `source_cards` | Official/vendor source-card freshness evidence | source id, kind, accessed/effective times, confidence, digest |
| `source_change_approvals` | Offline source-card refresh/add/retire approvals | source, requested/approved times, approver, action, status |
| `tax_lots` | Open tax lots with acquisition time and cost basis | lot, asset, acquired time, remaining quantity, cost, currency |
| `orders` | Offline order intents and lifecycle timing | order, asset, decision/submission/expiry, side/type/limit, time-in-force, optional queue priority, optional amend |
| `fills` | Historical or simulated execution evidence | fill/order IDs, fill time, price, quantity, venue |
| `calendar_sessions` | Effective trading sessions | calendar, session, UTC open/close, timezone |
| `futures_contracts` | Effective-dated futures contract specifications | contract/underlying, expiry, multiplier, currency, available time |
| `futures_margin_terms` | PIT per-contract margins and exchange daily price limits | venue/contract, effective/available times, initial/maintenance margin, price-limit fraction |
| `futures_position_limits` | PIT exchange or venue position limits | venue/contract, effective/available times, max contracts, limit source |
| `option_contracts` | Effective-dated option contract specifications | option/underlying, expiry, strike, call/put, style, available time |
| `option_exercise_events` | PIT offline American exercise or assignment events | option, event/available times, type, quantity, underlying price, currency |
| `credit_exposures` | PIT portfolio credit values and loss assumptions | observed/available times, portfolio/instrument, rating, duration, recovery, currency |
| `credit_transition_matrix` | PIT rating migration/default probabilities | matrix, observed/available times, horizon, from/to rating, probability |
| `yield_curve_nodes` | PIT zero-rate curve observations | curve, observed/available times, tenor, rate, compounding, currency |
| `fixed_income_spread_nodes` | PIT instrument spread nodes for discounting | spread curve/instrument, observed/available times, tenor, spread bps, currency |
| `fixed_income_instruments` | Bond terms, coupon mode/spread, amortization mode, and ex-coupon window | instrument, issuer, issue/maturity, coupon, day count, currency, amortization, ex-coupon days |
| `fx_quotes` | Venue-specific spot bid/ask currency-pair observations | timestamp, spot value date, base/quote currencies, venue |
| `fx_forward_quotes` | Outright or decimal-points forward bid/ask observations | timestamp, value date, quote type, base/quote currencies, venue |
| `fx_replacement_quotes` | PIT replacement bid/ask quotes selected at settlement-fail evaluation time | observed/available times, value date, base/quote currencies, venue |
| `crypto_positions` | PIT venue-account positions for offline margin stress | observed/available times, venue, account, instrument, signed quantity, entry price |
| `crypto_margin_tiers` | Effective margin and liquidation-fee brackets | venue/instrument, effective/available times, notional bounds, margin/fee rates |
| `crypto_instruments` | Effective-dated spot/perpetual venue specifications | venue/instrument, kind, base/quote, multiplier, margin currency |

## Contract Rules

- Primary keys are unique and non-null.
- Timestamps are timezone-aware UTC internally; local venue timezone is metadata, not an implicit assumption.
- Numeric values are finite; JSON uses `null` rather than NaN/Infinity.
- Every monetary value declares currency; every return declares simple/log, gross/excess, horizon, and timing.
- Source fields are mapped rather than overwritten; provenance preserves original column names and input digest.
- Large row-level results are Parquet sidecars, not unbounded JSON arrays.
