# NIDO — Núcleo Inteligente de Diálogo y Oportunidades

NIDO is a closed-loop real-estate conversational agent. It is intentionally isolated from `bd_replica_crm` and integrates through a versioned HTTP event.

```text
Sperant/Redshift → MEDALLIO → refresh success → medallio.table.refreshed.v1
                                              ↓
                                    NIDO reads PostgreSQL
                                              ↓
                               lead → experiment assignment
                               ├─ TREATMENT → CONTACT_NOW → Action → WhatsApp
                               └─ CONTROL   → BAU (NIDO silent)
                                              ↓
                                  REPLIED_24H / later CRM outcomes
                                              ↓
                                    uplift + CI95 + evidence status
```

## Decision v0.1

For an eligible new digital lead: **should NIDO initiate WhatsApp immediately, or should business-as-usual continue?**

NIDO separates `Decision`, `Action`, message/delivery status and `Outcome`. It refuses to claim improvement when CONTROL outcomes are not equivalently observable.

## Local start

```powershell
git clone https://github.com/dinatalediego/dntl_chatbot.git
cd dntl_chatbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

PostgreSQL setup examples are in `sql/`. Keep NIDO writes in `nido_db`; grant only SELECT on `medallio_dw.raw_cygnus.clientes_proyectos`.

## Medallio bridge

After a successful `bd_replica_crm` hourly refresh:

```powershell
python scripts\after_medallio_refresh.py
```

The webhook carries refresh metadata, not lead PII. NIDO uses its own watermark to read new rows.

## Experiment safety

Start plumbing tests with:

```env
EXPERIMENT_CONTROL_PCT=0
CONTROL_OUTCOME_OBSERVABLE=false
```

Only enable a real 50/50 when BAU is protected and its outcomes are observable:

```env
EXPERIMENT_CONTROL_PCT=50
CONTROL_OUTCOME_OBSERVABLE=true
```

## WhatsApp test

**Do not buy a third number yet.** First use Meta's Cloud API test business phone number as the bot/sender and one of your personal WhatsApp numbers as the test lead. See `docs/PHONE_TEST_PLAN.md`.

## Quality gates

CI runs Ruff, Bandit and Pytest. Local bootstrap tests cover decision policy, BAU control, HMAC security, event contract and full mock closed loop.
