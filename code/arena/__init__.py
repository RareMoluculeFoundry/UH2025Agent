"""
Arena Package: RLHF Infrastructure for UH2025Agent

This package provides the feedback collection, aggregation, and export
infrastructure for collecting Human-in-the-Loop (HITL) annotations
that feed into the Reinforcement Learning from Human Feedback (RLHF) pipeline.

Components:
- FeedbackCollector: Central aggregator for all feedback sources
- FeedbackItem: Individual feedback record
- AggregatedFeedback: Summary of all feedback for a run
- FeedbackType, FeedbackSource: Enums for categorization

Author: Stanley Lab / RareResearch
Date: November 2025
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Stanley Lab / RareResearch"

from .feedback_collector import (
    FeedbackCollector,
    FeedbackItem,
    AggregatedFeedback,
    FeedbackType,
    FeedbackSource,
    create_collector,
)

__all__ = [
    '__version__',
    '__author__',
    'FeedbackCollector',
    'FeedbackItem',
    'AggregatedFeedback',
    'FeedbackType',
    'FeedbackSource',
    'create_collector',
]
