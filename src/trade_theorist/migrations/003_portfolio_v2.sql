CREATE TABLE v2_records (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL UNIQUE,
    record_type TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    portfolio_id TEXT,
    body TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE
);
CREATE INDEX v2_scope ON v2_records(experiment_id, portfolio_id, record_type, sequence);
CREATE UNIQUE INDEX v2_event_key ON v2_records(json_extract(body, '$.idempotency_key')) WHERE record_type='ledger_event';
CREATE UNIQUE INDEX v2_event_sequence ON v2_records(portfolio_id, json_extract(body, '$.sequence')) WHERE record_type='ledger_event';
CREATE UNIQUE INDEX v2_segment ON v2_records(portfolio_id, json_extract(body, '$.ordinal')) WHERE record_type='funded_segment';
CREATE UNIQUE INDEX v2_lot_revision ON v2_records(portfolio_id, json_extract(body, '$.lot_id'), json_extract(body, '$.projection_revision')) WHERE record_type='lot';
CREATE UNIQUE INDEX v2_projection ON v2_records(portfolio_id, json_extract(body, '$.segment_id'), json_extract(body, '$.revision')) WHERE record_type='projection';
CREATE UNIQUE INDEX v2_client_id ON v2_records(json_extract(body, '$.client_order_id')) WHERE record_type='submission_mapping';
CREATE UNIQUE INDEX v2_internal_order ON v2_records(json_extract(body, '$.internal_order_id')) WHERE record_type='submission_mapping';
CREATE UNIQUE INDEX v2_outbox_revision ON v2_records(json_extract(body, '$.mapping_id'), json_extract(body, '$.revision')) WHERE record_type='outbox';
CREATE UNIQUE INDEX v2_provider_event ON v2_records(json_extract(body, '$.provider_event_id')) WHERE record_type='broker_update';
CREATE UNIQUE INDEX v2_incremental_fill ON v2_records(portfolio_id, json_extract(body, '$.payload.incremental_fill_id')) WHERE record_type='ledger_event' AND json_extract(body, '$.event_type')='fill';
CREATE UNIQUE INDEX v2_update_fill ON v2_records(json_extract(body, '$.incremental_fill_id')) WHERE record_type='broker_update' AND json_extract(body, '$.incremental_fill_id') IS NOT NULL;
CREATE UNIQUE INDEX v2_initial_funding ON v2_records(json_extract(body, '$.segment_id')) WHERE record_type='ledger_event' AND json_extract(body, '$.event_type')='funding';
CREATE TABLE v2_broker_bindings (mapping_id TEXT PRIMARY KEY REFERENCES v2_records(id), broker_order_id TEXT NOT NULL UNIQUE);
CREATE TABLE v2_quarantine (content_hash TEXT PRIMARY KEY, reason TEXT NOT NULL, observed_at TEXT NOT NULL);
CREATE TRIGGER v2_records_no_update BEFORE UPDATE ON v2_records BEGIN SELECT RAISE(ABORT, 'append only'); END;
CREATE TRIGGER v2_records_no_delete BEFORE DELETE ON v2_records BEGIN SELECT RAISE(ABORT, 'append only'); END;
CREATE TRIGGER v2_broker_bindings_no_update BEFORE UPDATE ON v2_broker_bindings BEGIN SELECT RAISE(ABORT, 'append only'); END;
CREATE TRIGGER v2_broker_bindings_no_delete BEFORE DELETE ON v2_broker_bindings BEGIN SELECT RAISE(ABORT, 'append only'); END;
CREATE TRIGGER v2_quarantine_no_update BEFORE UPDATE ON v2_quarantine BEGIN SELECT RAISE(ABORT, 'append only'); END;
CREATE TRIGGER v2_quarantine_no_delete BEFORE DELETE ON v2_quarantine BEGIN SELECT RAISE(ABORT, 'append only'); END;
