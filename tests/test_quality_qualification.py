"""Original rows challenge qualification claims; no account data or transport."""
from types import SimpleNamespace
import unittest

from trade_theorist.adapters.alpaca_market_data import quality_report


def row(symbol="instrument:first", session="2099-01-02", feed="sip", revision=1):
    return SimpleNamespace(payload=dict(kind="bar", instrument_id=symbol, session=session, feed=feed, adjustment="raw"),
                           observation=dict(revision=revision))


class QualityQualificationTests(unittest.TestCase):
    def report(self, records, **changes):
        args = dict(feed="sip", expected_sessions=("2099-01-02", "2099-01-03"),
                    expected_instruments=("instrument:first", "instrument:second"),
                    normalized=records, sample_kind="authorized_account")
        return quality_report(**(args | changes))

    def complete(self):
        return [row(s, day) for s in ("instrument:first", "instrument:second") for day in ("2099-01-02", "2099-01-03")]

    def test_each_instrument_requires_every_session(self):
        result = self.report([row(session="2099-01-02"), row(session="2099-01-03")])
        self.assertEqual(result.coverage_status, "blocked")
        self.assertEqual(result.missing_sessions, ())  # Legacy aggregate is insufficient.
        self.assertEqual(result.missing_pairs, (("instrument:second", "2099-01-02"), ("instrument:second", "2099-01-03")))

    def test_complete_scoped_sample_and_generator_revisions(self):
        values = self.complete() + [row(revision=2)]
        result = self.report(iter(values))
        self.assertEqual(result.coverage_status, "qualified")
        self.assertEqual(result.revision_count, 1)
        self.assertEqual(result.missing_pairs, ())
        self.assertEqual(result.expected_instruments, ("instrument:first", "instrument:second"))

    def test_quarantine_cannot_qualify_even_with_complete_coverage(self):
        result = self.report(self.complete(), quarantine=iter([object()]))
        self.assertEqual((result.coverage_status, result.quarantine_count), ("blocked", 1))

    def test_mixed_feed_or_universe_cannot_fill_gaps(self):
        wrong = [row("instrument:second", day, feed="iex") for day in ("2099-01-02", "2099-01-03")]
        result = self.report([row(session=day) for day in ("2099-01-02", "2099-01-03")] + wrong)
        self.assertEqual(result.coverage_status, "blocked")
        self.assertEqual(len(result.missing_pairs), 2)
        self.assertEqual(self.report(self.complete() + [row("instrument:outside")]).coverage_status, "blocked")

    def test_missing_declared_scope_and_unspecified_authority_stay_blocked(self):
        self.assertEqual(self.report(self.complete(), expected_instruments=()).coverage_status, "blocked")
        self.assertEqual(self.report([], expected_sessions=()).coverage_status, "blocked")
        result = quality_report(feed="sip", expected_sessions=("2099-01-02",), expected_instruments=("instrument:first",), normalized=[row()])
        self.assertEqual(result.coverage_status, "blocked")
        self.assertEqual(result.sample_kind, "unverified")

    def test_fixture_scope_and_unexpected_adjustments_never_promote(self):
        self.assertEqual(self.report(self.complete(), sample_kind="recorded_fixture").coverage_status, "blocked")
        values = self.complete(); values[-1].payload["adjustment"] = "split"
        self.assertEqual(self.report(values).coverage_status, "blocked")


if __name__ == "__main__": unittest.main()
