# FX Domain Contract

Canonical quote fields: timestamp, base currency, quote currency, bid, ask, venue/source, spot date, settlement calendar and fixing/stream type. The stored price is always quote units per base unit.

Forward fields: tenor/value date, outright bid/ask or forward points, base/quote curves, collateral currency, compounding and source snapshot.

Every conversion and PnL output records numeraire, pair orientation and rate timestamp. Cross rates require synchronized source quotes; stale-leg results are warnings or blockers according to the horizon.

Minimum gates: orientation, dual-calendar settlement, executable spread, carry/funding decomposition, currency attribution and gap/funding stress.
