"""Bounded, provider-neutral recommendation construction."""

from .recommend import OpinionAdapter, OPINION_OUTPUT, recommendation_request

__all__ = ["OpinionAdapter", "OPINION_OUTPUT", "recommendation_request"]
