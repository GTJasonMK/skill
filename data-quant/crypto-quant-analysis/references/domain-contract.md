# Crypto Domain Contract

Instrument fields: venue, permanent instrument ID, spot/perpetual/future type, base/quote/settlement/collateral assets, multiplier, expiry, margin mode, funding schedule, tick/lot, listing/delisting and effective rule source.

Market fields: exchange timestamp, receipt timestamp, bid/ask/trades/depth, mark/index, funding prediction/realization, open interest, margin tier, outage/tradability state and venue status.

On-chain fields additionally record chain, block height/hash, block time, finality, indexer receipt and first strategy availability.

Minimum gates: venue-specific PIT, funding/cost reconciliation, liquidation/margin stress, outage/depeg scenarios, transfer/custody/counterparty limits and no surviving-venue bias.
