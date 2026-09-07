"""Crash-resumable heartbeat coordination and exact-input model caching."""

from .orchestrator import (
    Heartbeat,
    HeartbeatInterrupted,
    ModelCallCache,
    PHASES,
)

__all__ = ["Heartbeat", "HeartbeatInterrupted", "ModelCallCache", "PHASES"]


def prepare_market_data(coordinator, value, *, consumer, max_attempts, deadline, **run_options):
    """Preparation callback before a heartbeat phase transaction, with no allowance of its own.

    Step 07 owns experiment-specific freezing and abstention; callers must inspect
    telemetry before entering a decision phase. This helper grants no eligibility.
    """
    work = coordinator.submit(value, consumer=consumer, max_attempts=max_attempts, deadline=deadline)
    return coordinator.run(work, **run_options)


__all__.append("prepare_market_data")


def run_forward_round(coordinator, manifest_id, recorded_provider, **options):
    """V2 paired preparation/decision entry; it owns no separate request budget."""
    from ..forward.shared import ForwardRound
    return ForwardRound(coordinator, manifest_id).execute(recorded_provider, **options)


__all__.append("run_forward_round")
