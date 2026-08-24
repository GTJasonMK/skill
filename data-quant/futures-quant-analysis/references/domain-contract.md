# Futures Domain Contract

Required contract metadata: permanent contract ID, root/underlying, venue, currency, multiplier, tick, listing, first-notice, last-trade, expiry, settlement method, margin regime, and effective rule source.

Required market evidence: timestamped raw contract price/settlement, volume, open interest, bid/ask when available, limits, session, and tradability state.

Continuous-series output must record active contract, previous contract, roll flag, roll rule, roll decision time, raw price, and whether any adjustment was applied. Back-adjusted values are prohibited as execution prices.

PnL must reconcile price movement × multiplier × signed contracts, roll transactions, fees, funding/collateral, margin cashflows, and delivery/close-out treatment.

Minimum gates: PIT contract selection, executable roll timing, margin sufficiency, cost/capacity, limit-move stress, and actual-contract PnL reconciliation.
