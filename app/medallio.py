from datetime import datetime, timedelta, timezone

from sqlalchemy import MetaData, Table, create_engine, inspect, select

from .config import get_settings

settings = get_settings()
NAME = ["nombre_cliente", "cliente", "nombres", "nombre"]
PHONE = ["telefono", "celular", "telefono_cliente", "celular_cliente"]
PROJECT = ["nombre_proyecto", "proyecto", "codigo_proyecto"]
OPTIN = ["whatsapp_opt_in", "opt_in_whatsapp", "consentimiento_whatsapp"]


def _pick(columns: set[str], candidates: list[str]) -> str | None:
    return next((x for x in candidates if x in columns), None)


def fetch_updated_leads(since: datetime | None, until: datetime | None) -> list[dict]:
    engine = create_engine(settings.medallio_database_url, pool_pre_ping=True)
    schema = settings.medallio_schema if engine.dialect.name == "postgresql" else None
    cols = {c["name"] for c in inspect(engine).get_columns(settings.medallio_table, schema=schema)}
    required = {settings.medallio_id_column, settings.medallio_watermark_column}
    if missing := required - cols:
        raise RuntimeError(f"Missing Medallio columns: {sorted(missing)}")
    selected = [settings.medallio_id_column, settings.medallio_watermark_column]
    for group in (NAME, PHONE, PROJECT, OPTIN):
        if (col := _pick(cols, group)) and col not in selected:
            selected.append(col)
    table = Table(settings.medallio_table, MetaData(), autoload_with=engine, schema=schema)
    wm = table.c[settings.medallio_watermark_column]
    effective_since = since or datetime.now(timezone.utc) - timedelta(hours=24)
    stmt = select(*(table.c[c] for c in selected)).where(wm > effective_since)
    if until:
        stmt = stmt.where(wm <= until)
    with engine.connect() as conn:
        rows = conn.execute(stmt.order_by(wm)).mappings().all()
    def value(row, candidates):
        return next((row[c] for c in candidates if c in row and row[c] not in (None, "")), None)
    return [{
        "source_lead_id": str(r[settings.medallio_id_column]),
        "source_updated_at": r[settings.medallio_watermark_column],
        "person_name": value(r, NAME),
        "phone_e164": value(r, PHONE),
        "project": value(r, PROJECT),
        "opted_in": bool(value(r, OPTIN)),
        "source_snapshot": {k: v for k, v in dict(r).items() if k not in PHONE},
    } for r in rows]
