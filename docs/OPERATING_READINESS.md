# Operating readiness v0.1

## Works
API starts; mock cycle closes; HMAC validates.

## Operates
NIDO DB isolated; Medallio SELECT-only; successful refresh emits event; retries are idempotent; Decision and Action are separate; CI is green.

## Measures
CONTROL=BAU; TREATMENT=NIDO; primary outcome=`REPLIED_24H`; API exposes sample sizes, rates, uplift, CI95 and evidence state. Keep `CONTROL_OUTCOME_OBSERVABLE=false` until BAU outcomes are captured equivalently.
