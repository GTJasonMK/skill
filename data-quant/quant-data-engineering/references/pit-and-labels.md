# Point-In-Time, Calendar, Corporate Action, And Label Rules

## Observable Time

A record may be used only when every required availability constraint is no later than the decision timestamp. When a record has both vendor availability and revision time, the observable time is the later of the two for that version.

Do not substitute fiscal period end, trade date, current database update time, or the latest vendor snapshot for historical availability.

## Calendar And Timezone

- Parse timestamps before sorting.
- Store UTC plus the explicit IANA venue timezone.
- In a Run Manifest, `calendar.sessions_source` names a declared `calendar_sessions` data-source ID; every row must match the declared calendar ID and IANA timezone.
- Use effective exchange sessions including holidays, half days, and rule changes.
- A date-only same-day signal/execution pair is an evidence gap unless the price convention proves executability.
- Cross-market joins require each venue session and a declared synchronization rule.

## Corporate Actions And Identity

- Preserve raw prices, adjustment factors, and total-return values separately.
- An action cannot change the historical observable dataset before its announcement/effective evidence permits it.
- Map symbol changes, mergers, spin-offs, delistings, and cross-listings through permanent IDs and effective intervals.
- Distinguish delisting, suspension, no quote, market holiday, and bad data.

## Return Labels

Every label records:

- decision time;
- simulated execution time and price convention;
- return start/end;
- label end time for purging;
- `return_type` (`simple`/`log`) and `return_basis` (`gross`/`excess`); excess labels also name their benchmark;
- currency and benchmark;
- gap policy and whether the horizon overlaps adjacent labels.

A label that begins before execution or uses a future-known universe is invalid, not merely a warning.
