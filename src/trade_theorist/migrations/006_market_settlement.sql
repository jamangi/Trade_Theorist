-- Preserve admission records; receipt/exception time conservatively bounds wire dispatch.
ALTER TABLE market_attempts ADD COLUMN settled REAL;
CREATE INDEX market_attempt_charge_time ON market_attempts(COALESCE(settled,dispatched));
