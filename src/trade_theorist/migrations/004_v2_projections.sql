CREATE UNIQUE INDEX v2_accounting_plan ON v2_records(portfolio_id) WHERE record_type='accounting_plan';
CREATE UNIQUE INDEX v2_execution_terms ON v2_records(json_extract(body, '$.order_id')) WHERE record_type='execution_terms';
CREATE UNIQUE INDEX v2_result_revision ON v2_records(portfolio_id, json_extract(body, '$.segment_id'), json_extract(body, '$.projection_revision')) WHERE record_type='performance_result';
