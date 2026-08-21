CREATE ROLE nido_reader LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
GRANT CONNECT ON DATABASE medallio_dw TO nido_reader;
GRANT USAGE ON SCHEMA raw_cygnus TO nido_reader;
GRANT SELECT ON TABLE raw_cygnus.clientes_proyectos TO nido_reader;
