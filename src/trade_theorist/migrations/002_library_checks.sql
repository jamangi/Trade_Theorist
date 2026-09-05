CREATE TABLE library_checks (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    requested_url TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    result TEXT NOT NULL
);
CREATE INDEX library_checks_source ON library_checks(source_id, sequence);
CREATE TABLE library_reviews (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    reason TEXT NOT NULL
);
CREATE TRIGGER checks_no_update BEFORE UPDATE ON library_checks BEGIN SELECT RAISE(ABORT, 'append only'); END;
CREATE TRIGGER checks_no_delete BEFORE DELETE ON library_checks BEGIN SELECT RAISE(ABORT, 'append only'); END;
CREATE TRIGGER reviews_no_update BEFORE UPDATE ON library_reviews BEGIN SELECT RAISE(ABORT, 'append only'); END;
CREATE TRIGGER reviews_no_delete BEFORE DELETE ON library_reviews BEGIN SELECT RAISE(ABORT, 'append only'); END;
