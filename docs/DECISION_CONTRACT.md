# Decision Contract v0.1

**Decision:** for an eligible digital lead, should NIDO start a WhatsApp conversation immediately or let business-as-usual (BAU) continue?

- Treatment: `CONTACT_NOW` by NIDO.
- Control: `BAU`; NIDO sends nothing and the normal commercial process continues.
- Primary outcome: `REPLIED_24H`.
- Secondary outcomes: `QUALIFIED_24H`, `APPOINTMENT_7D`, `SEPARATION_14D`, `MINUTA_30D`, `OPT_OUT`.
- `t0`: `eligible_at`.
- Claim rule: no improvement claim without a comparable observable control.

The audit chain is: `assignment -> decision -> action -> message/delivery -> outcome`.

Evidence states: `MEASUREMENT_NOT_READY`, `NO_COMPARABLE_CONTROL`, `COLLECTING_EVIDENCE`, `INCONCLUSIVE`, `SUPPORTS_IMPROVEMENT`, `SUPPORTS_HARM`.
