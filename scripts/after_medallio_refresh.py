import json
import time
from uuid import uuid4

import httpx
from sqlalchemy import MetaData, Table, create_engine, func, select

from app.config import get_settings
from app.security import sign_payload

settings = get_settings()


def main() -> None:
    engine = create_engine(settings.medallio_database_url, pool_pre_ping=True)
    schema = settings.medallio_schema if engine.dialect.name == "postgresql" else None
    table = Table(settings.medallio_table, MetaData(), autoload_with=engine, schema=schema)
    with engine.connect() as conn:
        watermark = conn.scalar(select(func.max(table.c[settings.medallio_watermark_column])))
    run_id = str(uuid4())
    event = {"event_id": f"medallio:{run_id}", "event_type": "medallio.table.refreshed.v1", "run_id": run_id, "source_table": f"{settings.medallio_schema}.{settings.medallio_table}", "status": "SUCCESS", "rows_loaded": 0, "watermark": watermark.isoformat() if watermark else None}
    body = json.dumps(event, separators=(",", ":")).encode()
    timestamp = str(int(time.time()))
    response = httpx.post(f"{settings.nido_base_url}/webhooks/medallio", content=body, headers={"X-NIDO-Timestamp": timestamp, "X-NIDO-Signature": sign_payload(settings.nido_webhook_secret, timestamp, body), "Content-Type": "application/json"}, timeout=30)
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()
