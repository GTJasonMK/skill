# Options Domain Contract

Canonical contract fields: option ID, underlying ID, venue, option type, strike, expiry, exercise style, settlement, multiplier, currency, listing/effective interval and adjustment lineage.

Quote fields: timestamp, bid, ask, last, size, volume, open interest, underlying mark, rate curve reference, dividend/borrow assumption and tradability state.

Analytics output records model, spot, strike, time convention, volatility scale, rate, dividend yield, price, delta, gamma, vega, theta and solver bounds. Implied volatility failure is explicit when the market price is outside the configured bracket.

A strategy gate requires executable quotes, contract-adjustment handling, hedge schedule, fees/slippage, margin/assignment treatment, scenario stress and PnL attribution.
