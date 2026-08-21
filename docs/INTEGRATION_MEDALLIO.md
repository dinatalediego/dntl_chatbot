# Medallio → NIDO

The repositories do not import each other. `bd_replica_crm` owns replication/freshness; `dntl_chatbot` owns conversations/decisions/outcomes.

After a successful Medallio refresh, emit `medallio.table.refreshed.v1` using HMAC headers. The event transports no lead PII; NIDO then reads `raw_cygnus.clientes_proyectos` using a SELECT-only PostgreSQL user and its own watermark cursor.
