CREATE TABLE market_quota (id INTEGER PRIMARY KEY CHECK(id=1), policy TEXT NOT NULL, logical REAL NOT NULL, cooldown REAL NOT NULL, next_dispatch REAL NOT NULL, effective_limit INTEGER NOT NULL);
CREATE TABLE market_work (id TEXT PRIMARY KEY, query_hash TEXT NOT NULL UNIQUE, query TEXT NOT NULL, body TEXT NOT NULL);
CREATE TABLE market_attempts (sequence INTEGER PRIMARY KEY AUTOINCREMENT, work_id TEXT NOT NULL REFERENCES market_work(id), dispatched REAL NOT NULL, request_hash TEXT NOT NULL, outcome TEXT NOT NULL);
CREATE INDEX market_attempt_time ON market_attempts(dispatched);
CREATE TABLE market_pages (work_id TEXT NOT NULL REFERENCES market_work(id), segment INTEGER NOT NULL, number INTEGER NOT NULL, body TEXT NOT NULL, PRIMARY KEY(work_id,segment,number));
CREATE TABLE market_observations (id TEXT PRIMARY KEY, compatibility TEXT NOT NULL, symbol TEXT NOT NULL, event_at TEXT NOT NULL, received_at TEXT NOT NULL, body TEXT NOT NULL);
CREATE INDEX market_observation_query ON market_observations(compatibility,symbol,event_at);
CREATE TABLE market_windows (compatibility TEXT NOT NULL, symbol TEXT NOT NULL, start TEXT NOT NULL, end TEXT NOT NULL, PRIMARY KEY(compatibility,symbol,start,end));
