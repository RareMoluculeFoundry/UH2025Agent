"""
Checkpoint Management for Human-in-the-Loop Reviews

This module provides checkpoint functionality for pausing the
pipeline to collect human feedback at critical decision points.

Key Features:
- Save/restore pipeline state
- Collect structured human feedback
- Resume execution after review

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import uuid


@dataclass
class HumanReviewCheckpoint:
    """
    Checkpoint capturing pipeline state for human review.

    Attributes:
        checkpoint_id: Unique identifier
        patient_id: Patient being analyzed
        stage: Pipeline stage at checkpoint
        timestamp: When checkpoint was created
        state_snapshot: Complete pipeline state
        requires_approval: Fields requiring human approval
        feedback: Human feedback (filled after review)
        approved: Whether review was approved
        reviewer_id: ID of human reviewer
    """
    checkpoint_id: str
    patient_id: str
    stage: str
    timestamp: str
    state_snapshot: Dict[str, Any]
    requires_approval: List[str] = field(default_factory=list)
    feedback: Dict[str, Any] = field(default_factory=dict)
    approved: bool = False
    reviewer_id: Optional[str] = None
    review_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "patient_id": self.patient_id,
            "stage": self.stage,
            "timestamp": self.timestamp,
            "state_snapshot": self.state_snapshot,
            "requires_approval": self.requires_approval,
            "feedback": self.feedback,
            "approved": self.approved,
            "reviewer_id": self.reviewer_id,
            "review_timestamp": self.review_timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanReviewCheckpoint":
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            patient_id=data["patient_id"],
            stage=data["stage"],
            timestamp=data["timestamp"],
            state_snapshot=data["state_snapshot"],
            requires_approval=data.get("requires_approval", []),
            feedback=data.get("feedback", {}),
            approved=data.get("approved", False),
            reviewer_id=data.get("reviewer_id"),
            review_timestamp=data.get("review_timestamp"),
        )


class CheckpointManager:
    """
    Manager for pipeline checkpoints and human reviews.

    Provides functionality to:
    - Create checkpoints at any pipeline stage
    - Save/load checkpoints to disk
    - Collect and validate human feedback
    - Resume pipeline after review

    Usage:
        manager = CheckpointManager(checkpoint_dir="./checkpoints")

        # Create checkpoint
        checkpoint = manager.create_checkpoint(
            state=current_state,
            stage="structuring",
            requires_approval=["diagnostic_hypotheses"]
        )

        # Save to disk
        manager.save_checkpoint(checkpoint)

        # Later: Load and review
        checkpoint = manager.load_checkpoint(checkpoint_id)
        checkpoint = manager.submit_review(
            checkpoint_id=checkpoint.checkpoint_id,
            feedback={"approved": True, "notes": "Looks good"},
            reviewer_id="clinician-001"
        )

        # Resume pipeline with approved state
        resumed_state = manager.get_approved_state(checkpoint)
    """

    def __init__(self, checkpoint_dir: Optional[Path] = None):
        """
        Initialize the checkpoint manager.

        Args:
            checkpoint_dir: Directory for storing checkpoints.
                          Defaults to ./checkpoints/
        """
        self.checkpoint_dir = checkpoint_dir or Path("./checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._pending_checkpoints: Dict[str, HumanReviewCheckpoint] = {}

    def create_checkpoint(
        self,
        state: Dict[str, Any],
        stage: str,
        requires_approval: Optional[List[str]] = None,
    ) -> HumanReviewCheckpoint:
        """
        Create a new checkpoint from pipeline state.

        Args:
            state: Current pipeline state
            stage: Current pipeline stage
            requires_approval: State fields requiring human review

        Returns:
            HumanReviewCheckpoint instance
        """
        checkpoint = HumanReviewCheckpoint(
            checkpoint_id=str(uuid.uuid4())[:8],
            patient_id=state.get("patient_id", "unknown"),
            stage=stage,
            timestamp=datetime.now().isoformat(),
            state_snapshot=state.copy(),
            requires_approval=requires_approval or [],
        )

        self._pending_checkpoints[checkpoint.checkpoint_id] = checkpoint
        return checkpoint

    def save_checkpoint(self, checkpoint: HumanReviewCheckpoint) -> Path:
        """
        Save checkpoint to disk.

        Args:
            checkpoint: Checkpoint to save

        Returns:
            Path to saved checkpoint file
        """
        filename = f"checkpoint_{checkpoint.checkpoint_id}.json"
        filepath = self.checkpoint_dir / filename

        with open(filepath, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2, default=str)

        return filepath

    def load_checkpoint(self, checkpoint_id: str) -> HumanReviewCheckpoint:
        """
        Load checkpoint from disk.

        Args:
            checkpoint_id: ID of checkpoint to load

        Returns:
            HumanReviewCheckpoint instance
        """
        # Check in-memory first
        if checkpoint_id in self._pending_checkpoints:
            return self._pending_checkpoints[checkpoint_id]

        # Load from disk
        filename = f"checkpoint_{checkpoint_id}.json"
        filepath = self.checkpoint_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")

        with open(filepath) as f:
            data = json.load(f)

        checkpoint = HumanReviewCheckpoint.from_dict(data)
        self._pending_checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def list_pending_checkpoints(self) -> List[HumanReviewCheckpoint]:
        """
        List all pending (not yet reviewed) checkpoints.

        Returns:
            List of pending checkpoints
        """
        pending = []

        # Scan checkpoint directory
        for filepath in self.checkpoint_dir.glob("checkpoint_*.json"):
            with open(filepath) as f:
                data = json.load(f)
            checkpoint = HumanReviewCheckpoint.from_dict(data)
            if not checkpoint.approved:
                pending.append(checkpoint)

        return pending

    def submit_review(
        self,
        checkpoint_id: str,
        feedback: Dict[str, Any],
        reviewer_id: str,
        approved: bool = True,
    ) -> HumanReviewCheckpoint:
        """
        Submit human review for a checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to review
            feedback: Human feedback dictionary
            reviewer_id: ID of the human reviewer
            approved: Whether the review approves the checkpoint

        Returns:
            Updated checkpoint with feedback
        """
        checkpoint = self.load_checkpoint(checkpoint_id)

        checkpoint.feedback = feedback
        checkpoint.reviewer_id = reviewer_id
        checkpoint.approved = approved
        checkpoint.review_timestamp = datetime.now().isoformat()

        # Save updated checkpoint
        self.save_checkpoint(checkpoint)

        return checkpoint

    def get_approved_state(
        self,
        checkpoint: HumanReviewCheckpoint,
    ) -> Dict[str, Any]:
        """
        Get the pipeline state to resume after approval.

        Applies any corrections from human feedback to the state.

        Args:
            checkpoint: Approved checkpoint

        Returns:
            State dictionary ready for pipeline resumption
        """
        if not checkpoint.approved:
            raise ValueError("Cannot resume from unapproved checkpoint")

        state = checkpoint.state_snapshot.copy()

        # Apply corrections from feedback
        corrections = checkpoint.feedback.get("corrections", {})
        for field, value in corrections.items():
            if field in state:
                state[field] = value

        # Update metadata
        state["human_feedback"] = checkpoint.feedback
        state["awaiting_human_review"] = False

        return state

    def get_review_summary(
        self,
        checkpoint: HumanReviewCheckpoint,
    ) -> Dict[str, Any]:
        """
        Get a summary of the checkpoint for review display.

        Args:
            checkpoint: Checkpoint to summarize

        Returns:
            Summary dictionary for UI display
        """
        state = checkpoint.state_snapshot

        summary = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "patient_id": checkpoint.patient_id,
            "stage": checkpoint.stage,
            "timestamp": checkpoint.timestamp,
            "status": "approved" if checkpoint.approved else "pending",
        }

        # Add stage-specific summary
        if checkpoint.stage == "ingestion":
            patient_context = state.get("patient_context", {})
            summary["summary"] = {
                "demographics": patient_context.get("demographics", {}),
                "chief_complaint": patient_context.get("clinical_presentation", {}).get("chief_complaint", ""),
                "variants_count": len(state.get("variants_table", [])),
                "confidence": state.get("ingestion_confidence", 0),
            }

        elif checkpoint.stage == "structuring":
            hypotheses = state.get("diagnostic_hypotheses", [])
            summary["summary"] = {
                "hypotheses_count": len(hypotheses),
                "top_hypothesis": hypotheses[0] if hypotheses else None,
                "tools_planned": len(state.get("tool_usage_plan", [])),
                "iteration": state.get("iteration", 0),
            }

        elif checkpoint.stage == "executor":
            summary["summary"] = {
                "tools_completed": state.get("tools_completed", 0),
                "tools_failed": state.get("tools_failed", 0),
                "results_count": len(state.get("tool_results", [])),
            }

        return summary


def get_feedback_schema(stage: str) -> Dict[str, Any]:
    """
    Get JSON Schema for human feedback at a given stage.

    Args:
        stage: Pipeline stage name

    Returns:
        JSON Schema for feedback collection
    """
    base_schema = {
        "type": "object",
        "properties": {
            "approved": {
                "type": "boolean",
                "description": "Whether to approve and continue",
            },
            "notes": {
                "type": "string",
                "description": "General review notes",
            },
            "corrections": {
                "type": "object",
                "description": "Field-level corrections",
            },
        },
        "required": ["approved"],
    }

    # Add stage-specific fields
    if stage == "ingestion":
        base_schema["properties"]["corrections"]["properties"] = {
            "demographics": {"type": "object"},
            "chief_complaint": {"type": "string"},
            "variants_to_add": {"type": "array"},
            "variants_to_remove": {"type": "array"},
        }

    elif stage == "structuring":
        base_schema["properties"]["corrections"]["properties"] = {
            "hypotheses_to_add": {"type": "array"},
            "hypotheses_to_remove": {"type": "array"},
            "tools_to_add": {"type": "array"},
            "tools_to_remove": {"type": "array"},
            "confidence_overrides": {"type": "object"},
        }

    elif stage == "executor":
        base_schema["properties"]["corrections"]["properties"] = {
            "invalid_results": {"type": "array"},
            "result_corrections": {"type": "object"},
            "additional_tools": {"type": "array"},
        }

    return base_schema
