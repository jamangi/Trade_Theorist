"""Execution-time tool allowlists for market experiments.

Prompt text is not a security boundary.  A historical-restricted run receives no
network-capable tools at construction time, even if a caller asks for them.
"""

from ..contracts import ContractError


NETWORK_TOOLS = frozenset({"web", "browser", "http", "market_data_live", "broker"})


def allowed_tools(regime, requested=()):
    requested = frozenset(requested)
    if regime == "historical_restricted":
        return requested - NETWORK_TOOLS
    if regime in ("fixture", "hindsight"):
        return requested - frozenset({"broker"})
    if regime in ("forward_shadow", "forward_paper"):
        return requested - frozenset({"web", "browser", "broker"})
    raise ContractError("Unknown experiment regime")


def enforce_tool_access(regime, provided):
    provided = frozenset(provided)
    permitted = allowed_tools(regime, provided)
    blocked = provided - permitted
    if blocked:
        raise ContractError("Run was constructed with prohibited tools")
    return permitted
