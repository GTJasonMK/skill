# Fixed-Income Domain Contract

Instrument fields: permanent ID, issuer, currency, issue/maturity, coupon/amortization schedule, day-count, business-day rule, settlement lag, seniority, call/put/prepayment/default terms and effective source.

Market fields: timestamp, clean/dirty price, accrued interest, yield/spread convention, bid/ask, size, evaluated/traded flag, curve IDs, FX and repo/funding assumptions.

Every result records compounding frequency, curve snapshot, valuation time and units. Cashflow pricing must reconcile present values; duration/convexity must state whether they are Macaulay, modified, effective or key-rate.

Minimum gates: complete cashflows, point-in-time curve, settlement convention, executable liquidity, funding, credit/default stress and return attribution.
