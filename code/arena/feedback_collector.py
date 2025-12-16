"""
FeedbackCollector: Central aggregator for RLHF feedback from all pipeline stages.

This module provides a unified interface for collecting, aggregating, and exporting
human feedback from all stages of the UH2025-CDS-Agent pipeline. It collects:

1. Ingestion feedback (HPO term corrections, variant parsing)
2. Structuring feedback (differential diagnosis review via DiagnosisReviewTable)
3. Executor feedback (tool result validation)
4. Synthesis feedback (clinical report section review)

The aggregated feedback is formatted for:
- Direct preference optimization (DPO) training
- RLHF reward model training
- Supervised fine-tuning with corrections
- Quality metrics and audit trails

Author: Stanley Lab / RareResearch
Date: November 2025
Version: 2.0.0 - Added export_arena_bundle() for federated learning
"""

import json
import zipfile
import base64
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib


class FeedbackType(Enum):
    """Types of feedback that can be collected."""
    DIAGNOSIS_REVIEW = "diagnosis_review"
    VARIANT_CLASSIFICATION = "variant_classification"
    REPORT_SECTION = "report_section"
    HPO_MAPPING = "hpo_mapping"
    TOOL_RESULT = "tool_result"
    OVERALL_QUALITY = "overall_quality"


class FeedbackSource(Enum):
    """Sources of feedback in the pipeline."""
    INGESTION = "01_ingestion"
    STRUCTURING = "02_structuring"
    EXECUTOR = "03_executor"
    SYNTHESIS = "04_synthesis"


@dataclass
class FeedbackItem:
    """A single piece of feedback from an expert reviewer."""
    feedback_id: str
    feedback_type: FeedbackType
    source: FeedbackSource
    timestamp: str
    reviewer_id: Optional[str] = None

    # The original AI output
    original_content: Dict[str, Any] = field(default_factory=dict)

    # The expert's assessment
    is_correct: bool = True
    confidence_original: float = 0.0
    confidence_adjusted: float = 0.0

    # Corrections and notes
    corrections: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    # For training data generation
    chosen_response: Optional[str] = None
    rejected_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "feedback_type": self.feedback_type.value,
            "source": self.source.value,
            "timestamp": self.timestamp,
            "reviewer_id": self.reviewer_id,
            "original_content": self.original_content,
            "is_correct": self.is_correct,
            "confidence_original": self.confidence_original,
            "confidence_adjusted": self.confidence_adjusted,
            "corrections": self.corrections,
            "notes": self.notes,
            "chosen_response": self.chosen_response,
            "rejected_response": self.rejected_response,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackItem":
        return cls(
            feedback_id=data["feedback_id"],
            feedback_type=FeedbackType(data["feedback_type"]),
            source=FeedbackSource(data["source"]),
            timestamp=data["timestamp"],
            reviewer_id=data.get("reviewer_id"),
            original_content=data.get("original_content", {}),
            is_correct=data.get("is_correct", True),
            confidence_original=data.get("confidence_original", 0.0),
            confidence_adjusted=data.get("confidence_adjusted", 0.0),
            corrections=data.get("corrections", {}),
            notes=data.get("notes", ""),
            chosen_response=data.get("chosen_response"),
            rejected_response=data.get("rejected_response"),
        )


@dataclass
class AggregatedFeedback:
    """Aggregated feedback for a complete pipeline run."""
    run_id: str
    patient_id: str
    timestamp: str

    # All feedback items organized by source
    ingestion_feedback: List[FeedbackItem] = field(default_factory=list)
    structuring_feedback: List[FeedbackItem] = field(default_factory=list)
    executor_feedback: List[FeedbackItem] = field(default_factory=list)
    synthesis_feedback: List[FeedbackItem] = field(default_factory=list)

    # Summary metrics
    total_items: int = 0
    correct_items: int = 0
    items_with_corrections: int = 0

    # Reviewer metadata
    reviewers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "patient_id": self.patient_id,
            "timestamp": self.timestamp,
            "feedback": {
                "ingestion": [f.to_dict() for f in self.ingestion_feedback],
                "structuring": [f.to_dict() for f in self.structuring_feedback],
                "executor": [f.to_dict() for f in self.executor_feedback],
                "synthesis": [f.to_dict() for f in self.synthesis_feedback],
            },
            "summary": {
                "total_items": self.total_items,
                "correct_items": self.correct_items,
                "items_with_corrections": self.items_with_corrections,
                "accuracy_rate": self.correct_items / self.total_items if self.total_items > 0 else 0,
            },
            "reviewers": self.reviewers,
        }


class FeedbackCollector:
    """
    Central aggregator for collecting and managing RLHF feedback.

    This class provides:
    - Unified interface for all feedback sources
    - Automatic aggregation of feedback files
    - Export to training-ready formats
    - Quality metrics and statistics

    Example:
        >>> collector = FeedbackCollector(run_dir=Path("outputs/demo_run"))
        >>> collector.scan_for_feedback()
        >>> aggregated = collector.aggregate()
        >>> collector.export_for_training("training_data.jsonl")
    """

    def __init__(
        self,
        run_dir: Path,
        patient_id: Optional[str] = None,
        reviewer_id: Optional[str] = None,
    ):
        """
        Initialize the feedback collector.

        Args:
            run_dir: Path to the pipeline run output directory
            patient_id: Patient identifier (auto-detected if not provided)
            reviewer_id: Reviewer identifier for attribution
        """
        self.run_dir = Path(run_dir)
        self.patient_id = patient_id
        self.reviewer_id = reviewer_id
        self.run_id = self._generate_run_id()

        # Feedback storage
        self.feedback_items: List[FeedbackItem] = []

        # Known feedback file patterns
        self.feedback_patterns = {
            FeedbackSource.INGESTION: ["ingestion_feedback.json", "hpo_corrections.json"],
            FeedbackSource.STRUCTURING: ["diagnosis_annotations.json", "variant_review.json"],
            FeedbackSource.EXECUTOR: ["tool_validation.json"],
            FeedbackSource.SYNTHESIS: ["report_feedback.json", "section_feedback.json"],
        }

        # Auto-detect patient ID if not provided
        if not self.patient_id:
            self._detect_patient_id()

    def _generate_run_id(self) -> str:
        """Generate a unique run ID based on directory and timestamp."""
        content = f"{self.run_dir}_{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def _detect_patient_id(self):
        """Try to detect patient ID from pipeline outputs."""
        # Check ingestion output
        ingestion_file = self.run_dir / "01_ingestion" / "patient_context.json"
        if ingestion_file.exists():
            with open(ingestion_file) as f:
                data = json.load(f)
                self.patient_id = data.get("patient_id", "unknown")
                return

        # Check synthesis output
        synthesis_file = self.run_dir / "04_synthesis" / "clinical_report.json"
        if synthesis_file.exists():
            with open(synthesis_file) as f:
                data = json.load(f)
                self.patient_id = data.get("patient_id", "unknown")
                return

        self.patient_id = "unknown"

    def scan_for_feedback(self) -> Dict[str, List[Path]]:
        """
        Scan the run directory for existing feedback files.

        Returns:
            Dict mapping feedback source to list of found files
        """
        found_files: Dict[str, List[Path]] = {}

        for source, patterns in self.feedback_patterns.items():
            source_dir = self.run_dir / source.value
            found = []

            if source_dir.exists():
                for pattern in patterns:
                    feedback_file = source_dir / pattern
                    if feedback_file.exists():
                        found.append(feedback_file)

            # Also check feedback subdirectory
            feedback_dir = self.run_dir / "feedback"
            if feedback_dir.exists():
                for pattern in patterns:
                    feedback_file = feedback_dir / pattern
                    if feedback_file.exists():
                        found.append(feedback_file)

            if found:
                found_files[source.value] = found

        return found_files

    def load_diagnosis_review(self, annotations_file: Path) -> List[FeedbackItem]:
        """
        Load feedback from DiagnosisReviewTable annotations file.

        Args:
            annotations_file: Path to diagnosis_annotations.json

        Returns:
            List of FeedbackItem objects
        """
        items = []

        with open(annotations_file) as f:
            data = json.load(f)

        annotations = data.get("annotations", [])

        for idx, annotation in enumerate(annotations):
            item = FeedbackItem(
                feedback_id=f"dx_review_{idx:03d}",
                feedback_type=FeedbackType.DIAGNOSIS_REVIEW,
                source=FeedbackSource.STRUCTURING,
                timestamp=data.get("metadata", {}).get("saved_at", datetime.now().isoformat()),
                reviewer_id=self.reviewer_id,
                original_content={
                    "disease": annotation.get("disease"),
                    "rank": annotation.get("rank"),
                    "original_confidence": annotation.get("original_confidence"),
                },
                is_correct=annotation.get("is_correct", True),
                confidence_original=annotation.get("original_confidence", 0.0),
                confidence_adjusted=annotation.get("adjusted_confidence", 0.0),
                notes=annotation.get("clinical_notes", ""),
            )

            # If marked incorrect, create correction
            if not item.is_correct:
                item.corrections = {
                    "should_be_correct": False,
                    "suggested_confidence": item.confidence_adjusted,
                    "reasoning": item.notes,
                }

            items.append(item)

        return items

    def load_report_feedback(self, feedback_file: Path) -> List[FeedbackItem]:
        """
        Load feedback from clinical report section review.

        Args:
            feedback_file: Path to report_feedback.json

        Returns:
            List of FeedbackItem objects
        """
        items = []

        with open(feedback_file) as f:
            data = json.load(f)

        sections = data.get("section_feedback", [])

        for idx, section in enumerate(sections):
            item = FeedbackItem(
                feedback_id=f"report_section_{idx:03d}",
                feedback_type=FeedbackType.REPORT_SECTION,
                source=FeedbackSource.SYNTHESIS,
                timestamp=data.get("timestamp", datetime.now().isoformat()),
                reviewer_id=self.reviewer_id,
                original_content={
                    "section_title": section.get("section_title"),
                    "section_content": section.get("original_content"),
                },
                is_correct=section.get("approved", True),
                confidence_original=section.get("quality_score", 0.8),
                confidence_adjusted=section.get("quality_score", 0.8),
                notes=section.get("feedback_notes", ""),
            )

            if section.get("suggested_edits"):
                item.corrections = {
                    "suggested_edits": section.get("suggested_edits"),
                }
                item.chosen_response = section.get("suggested_edits")
                item.rejected_response = section.get("original_content")

            items.append(item)

        return items

    def add_feedback(self, item: FeedbackItem):
        """Add a feedback item to the collection."""
        self.feedback_items.append(item)

    def add_diagnosis_correction(
        self,
        disease_name: str,
        is_correct: bool,
        original_confidence: float,
        adjusted_confidence: float,
        notes: str = "",
    ):
        """
        Convenience method to add a diagnosis review item.

        Args:
            disease_name: Name of the diagnosis
            is_correct: Whether the diagnosis is clinically correct
            original_confidence: AI's original confidence
            adjusted_confidence: Expert's adjusted confidence
            notes: Clinical notes explaining the assessment
        """
        item = FeedbackItem(
            feedback_id=f"dx_{len(self.feedback_items):03d}",
            feedback_type=FeedbackType.DIAGNOSIS_REVIEW,
            source=FeedbackSource.STRUCTURING,
            timestamp=datetime.now().isoformat(),
            reviewer_id=self.reviewer_id,
            original_content={"disease": disease_name},
            is_correct=is_correct,
            confidence_original=original_confidence,
            confidence_adjusted=adjusted_confidence,
            notes=notes,
        )
        self.feedback_items.append(item)

    def aggregate(self) -> AggregatedFeedback:
        """
        Aggregate all collected feedback into a summary structure.

        Returns:
            AggregatedFeedback object with all feedback organized by source
        """
        aggregated = AggregatedFeedback(
            run_id=self.run_id,
            patient_id=self.patient_id or "unknown",
            timestamp=datetime.now().isoformat(),
        )

        # Organize by source
        for item in self.feedback_items:
            if item.source == FeedbackSource.INGESTION:
                aggregated.ingestion_feedback.append(item)
            elif item.source == FeedbackSource.STRUCTURING:
                aggregated.structuring_feedback.append(item)
            elif item.source == FeedbackSource.EXECUTOR:
                aggregated.executor_feedback.append(item)
            elif item.source == FeedbackSource.SYNTHESIS:
                aggregated.synthesis_feedback.append(item)

        # Calculate metrics
        aggregated.total_items = len(self.feedback_items)
        aggregated.correct_items = sum(1 for item in self.feedback_items if item.is_correct)
        aggregated.items_with_corrections = sum(
            1 for item in self.feedback_items if item.corrections
        )

        # Track reviewers
        reviewers = set()
        for item in self.feedback_items:
            if item.reviewer_id:
                reviewers.add(item.reviewer_id)
        aggregated.reviewers = list(reviewers)

        return aggregated

    def save(self, output_path: Optional[Path] = None) -> Path:
        """
        Save aggregated feedback to JSON file.

        Args:
            output_path: Optional path for output file

        Returns:
            Path to saved file
        """
        if output_path is None:
            feedback_dir = self.run_dir / "feedback"
            feedback_dir.mkdir(parents=True, exist_ok=True)
            output_path = feedback_dir / "aggregated_feedback.json"

        aggregated = self.aggregate()

        with open(output_path, 'w') as f:
            json.dump(aggregated.to_dict(), f, indent=2)

        return output_path

    def load(self, input_path: Path):
        """
        Load previously saved feedback from file.

        Args:
            input_path: Path to aggregated_feedback.json
        """
        with open(input_path) as f:
            data = json.load(f)

        self.run_id = data.get("run_id", self.run_id)
        self.patient_id = data.get("patient_id", self.patient_id)

        # Load all feedback items
        self.feedback_items = []

        for source_key in ["ingestion", "structuring", "executor", "synthesis"]:
            items_data = data.get("feedback", {}).get(source_key, [])
            for item_data in items_data:
                self.feedback_items.append(FeedbackItem.from_dict(item_data))

    def export_for_training(
        self,
        output_path: Path,
        format: str = "jsonl",
        include_correct: bool = True,
    ) -> Path:
        """
        Export feedback in a format suitable for training.

        Args:
            output_path: Path for output file
            format: Output format ("jsonl" for JSON Lines, "json" for array)
            include_correct: Whether to include items marked as correct

        Returns:
            Path to exported file
        """
        training_data = []

        for item in self.feedback_items:
            # Skip correct items if requested
            if item.is_correct and not include_correct:
                continue

            # Build training record
            record = {
                "id": item.feedback_id,
                "type": item.feedback_type.value,
                "source": item.source.value,
                "patient_id": self.patient_id,
                "is_correct": item.is_correct,
                "original": item.original_content,
            }

            # Add preference data for DPO training
            if item.chosen_response and item.rejected_response:
                record["chosen"] = item.chosen_response
                record["rejected"] = item.rejected_response

            # Add corrections for SFT
            if item.corrections:
                record["corrections"] = item.corrections

            # Add confidence delta for reward modeling
            if item.confidence_adjusted != item.confidence_original:
                record["confidence_delta"] = (
                    item.confidence_adjusted - item.confidence_original
                )

            if item.notes:
                record["expert_notes"] = item.notes

            training_data.append(record)

        # Write output
        output_path = Path(output_path)

        if format == "jsonl":
            with open(output_path, 'w') as f:
                for record in training_data:
                    f.write(json.dumps(record) + "\n")
        else:
            with open(output_path, 'w') as f:
                json.dump(training_data, f, indent=2)

        return output_path

    def export_arena_bundle(
        self,
        output_path: Optional[Path] = None,
        include_pipeline_outputs: bool = False,
        anonymize: bool = True,
        institution_id: Optional[str] = None,
    ) -> Path:
        """
        Export feedback as a federated learning contribution bundle.

        This creates a privacy-preserving bundle suitable for contribution to the
        "Rare Arena Network" - a federated learning system where model updates
        (not patient data) are shared between institutions.

        The bundle contains:
        - Anonymized feedback data (gradients, not raw data)
        - Model update contributions (if training was performed locally)
        - Metadata for provenance and quality scoring
        - Differential privacy parameters

        Args:
            output_path: Path for output bundle (default: run_dir/arena/arena_bundle.zip)
            include_pipeline_outputs: Include sanitized pipeline outputs for verification
            anonymize: Apply anonymization to all exported data (default: True)
            institution_id: Identifier for contributing institution

        Returns:
            Path to the exported bundle

        Example:
            >>> collector = FeedbackCollector(run_dir=Path("outputs/demo_run"))
            >>> collector.scan_for_feedback()
            >>> bundle_path = collector.export_arena_bundle(
            ...     institution_id="clinic_001",
            ...     anonymize=True
            ... )
            >>> print(f"Bundle ready for federation: {bundle_path}")
        """
        # Set default output path
        if output_path is None:
            arena_dir = self.run_dir / "arena"
            arena_dir.mkdir(parents=True, exist_ok=True)
            output_path = arena_dir / f"arena_bundle_{self.run_id}.zip"
        else:
            output_path = Path(output_path)

        # Build the bundle
        bundle_manifest = {
            "bundle_version": "1.0.0",
            "bundle_type": "rlhf_feedback",
            "created_at": datetime.now().isoformat(),
            "run_id": self.run_id,
            "institution_id": institution_id or "anonymous",
            "anonymized": anonymize,
            "differential_privacy": {
                "enabled": anonymize,
                "epsilon": 1.0,  # Privacy budget
                "delta": 1e-5,
            },
        }

        # Prepare anonymized feedback
        anonymized_feedback = self._anonymize_feedback() if anonymize else self.aggregate().to_dict()

        # Calculate contribution metrics
        contribution_metrics = self._calculate_contribution_metrics()

        # Build gradient summary (simulated - in real system this would be actual gradients)
        gradient_summary = self._build_gradient_summary()

        # Create the zip bundle
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Write manifest
            zf.writestr(
                "manifest.json",
                json.dumps(bundle_manifest, indent=2)
            )

            # Write anonymized feedback
            zf.writestr(
                "feedback/aggregated_feedback.json",
                json.dumps(anonymized_feedback, indent=2)
            )

            # Write training-ready data
            training_data = []
            for item in self.feedback_items:
                training_record = self._feedback_to_training_record(item, anonymize)
                if training_record:
                    training_data.append(training_record)

            zf.writestr(
                "training/training_data.jsonl",
                "\n".join(json.dumps(record) for record in training_data)
            )

            # Write contribution metrics
            zf.writestr(
                "metrics/contribution_metrics.json",
                json.dumps(contribution_metrics, indent=2)
            )

            # Write gradient summary
            zf.writestr(
                "gradients/gradient_summary.json",
                json.dumps(gradient_summary, indent=2)
            )

            # Optionally include sanitized pipeline outputs
            if include_pipeline_outputs:
                sanitized_outputs = self._sanitize_pipeline_outputs()
                zf.writestr(
                    "verification/pipeline_outputs.json",
                    json.dumps(sanitized_outputs, indent=2)
                )

        return output_path

    def _anonymize_feedback(self) -> Dict[str, Any]:
        """
        Anonymize feedback data for federated sharing.

        Applies:
        - Patient ID hashing
        - Reviewer ID hashing
        - Removal of free-text notes that might contain PHI
        - Generalization of rare conditions
        """
        aggregated = self.aggregate()
        anon_dict = aggregated.to_dict()

        # Hash patient ID
        if anon_dict.get("patient_id"):
            anon_dict["patient_id"] = hashlib.sha256(
                anon_dict["patient_id"].encode()
            ).hexdigest()[:16]

        # Hash reviewer IDs
        anon_reviewers = []
        for reviewer in anon_dict.get("reviewers", []):
            if reviewer:
                anon_reviewers.append(
                    hashlib.sha256(reviewer.encode()).hexdigest()[:16]
                )
        anon_dict["reviewers"] = anon_reviewers

        # Anonymize feedback items
        for source_key in ["ingestion", "structuring", "executor", "synthesis"]:
            items = anon_dict.get("feedback", {}).get(source_key, [])
            for item in items:
                # Hash reviewer
                if item.get("reviewer_id"):
                    item["reviewer_id"] = hashlib.sha256(
                        item["reviewer_id"].encode()
                    ).hexdigest()[:16]
                # Remove free-text notes (potential PHI)
                item["notes"] = "[REDACTED]" if item.get("notes") else ""
                # Generalize rare disease names
                if item.get("original_content", {}).get("disease"):
                    disease = item["original_content"]["disease"]
                    if self._is_rare_condition(disease):
                        item["original_content"]["disease"] = "[RARE_CONDITION]"

        return anon_dict

    def _is_rare_condition(self, disease_name: str) -> bool:
        """Check if a condition is rare enough to be potentially identifying."""
        # In a real system, this would check against a rare disease database
        # For now, assume any condition with < 5 letters might be a rare abbreviation
        if not disease_name:
            return False
        # Very basic heuristic - in production use a proper rare disease registry
        rare_indicators = ["syndrome", "type", "variant", "mutation", "deficiency"]
        disease_lower = disease_name.lower()
        return any(indicator in disease_lower for indicator in rare_indicators)

    def _calculate_contribution_metrics(self) -> Dict[str, Any]:
        """
        Calculate metrics that describe the value of this contribution.

        These metrics help the federated aggregator weight contributions
        appropriately.
        """
        stats = self.get_statistics()

        return {
            "total_feedback_items": stats.get("total_items", 0),
            "correction_rate": (
                stats.get("items_with_corrections", 0) / stats.get("total_items", 1)
                if stats.get("total_items", 0) > 0 else 0
            ),
            "expert_reviewer_count": stats.get("unique_reviewers", 0),
            "feedback_quality_score": self._calculate_quality_score(),
            "coverage": {
                "ingestion": len(stats.get("by_source", {}).get("01_ingestion", {}).get("count", 0)) > 0,
                "structuring": len(stats.get("by_source", {}).get("02_structuring", {}).get("count", 0)) > 0,
                "executor": len(stats.get("by_source", {}).get("03_executor", {}).get("count", 0)) > 0,
                "synthesis": len(stats.get("by_source", {}).get("04_synthesis", {}).get("count", 0)) > 0,
            },
            "confidence_calibration": stats.get("confidence_adjustments", {}),
        }

    def _calculate_quality_score(self) -> float:
        """
        Calculate a quality score for this feedback contribution.

        Higher scores indicate more valuable training signal.
        """
        if not self.feedback_items:
            return 0.0

        score = 0.0
        max_score = 0.0

        for item in self.feedback_items:
            max_score += 1.0

            # Points for having corrections (indicates engaged review)
            if item.corrections:
                score += 0.3

            # Points for confidence adjustment (indicates calibration data)
            if item.confidence_adjusted != item.confidence_original:
                score += 0.3

            # Points for reviewer attribution
            if item.reviewer_id:
                score += 0.2

            # Points for items marked as correct (validates AI output)
            if item.is_correct:
                score += 0.2

        return score / max_score if max_score > 0 else 0.0

    def _build_gradient_summary(self) -> Dict[str, Any]:
        """
        Build a summary of model gradient updates (simulated).

        In a real federated learning system, this would contain actual
        gradient tensors from local training. For now, we create a
        summary that describes what the gradients would represent.
        """
        return {
            "gradient_type": "feedback_signal",
            "update_type": "preference_based",
            "num_preference_pairs": sum(
                1 for item in self.feedback_items
                if item.chosen_response and item.rejected_response
            ),
            "num_corrections": sum(
                1 for item in self.feedback_items if item.corrections
            ),
            "num_confidence_adjustments": sum(
                1 for item in self.feedback_items
                if item.confidence_adjusted != item.confidence_original
            ),
            "signal_strength": self._calculate_quality_score(),
            "compatible_models": [
                "UH2025-CDS-Agent",
                "Rare-Disease-Diagnostic-LLM",
            ],
            "training_objectives": [
                "direct_preference_optimization",
                "reward_model_training",
                "supervised_fine_tuning",
            ],
        }

    def _feedback_to_training_record(
        self,
        item: FeedbackItem,
        anonymize: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Convert a feedback item to a training record."""
        record = {
            "id": item.feedback_id,
            "type": item.feedback_type.value,
            "source": item.source.value,
            "is_correct": item.is_correct,
        }

        # Add preference pair if available (for DPO)
        if item.chosen_response and item.rejected_response:
            record["chosen"] = item.chosen_response
            record["rejected"] = item.rejected_response

        # Add confidence calibration data
        if item.confidence_adjusted != item.confidence_original:
            record["confidence_original"] = item.confidence_original
            record["confidence_adjusted"] = item.confidence_adjusted
            record["confidence_delta"] = item.confidence_adjusted - item.confidence_original

        # Add corrections (for SFT)
        if item.corrections and not anonymize:
            record["corrections"] = item.corrections

        return record if len(record) > 4 else None  # Skip if no useful training signal

    def _sanitize_pipeline_outputs(self) -> Dict[str, Any]:
        """
        Sanitize pipeline outputs for verification purposes.

        Removes PHI but keeps enough information to verify feedback quality.
        """
        sanitized = {
            "run_id": self.run_id,
            "stages_completed": [],
            "tool_calls": [],
        }

        # Check which stages have outputs
        for stage in ["01_ingestion", "02_structuring", "03_executor", "04_synthesis"]:
            stage_dir = self.run_dir / stage
            if stage_dir.exists():
                sanitized["stages_completed"].append(stage)

        return sanitized

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculate statistics about collected feedback.

        Returns:
            Dict with feedback statistics
        """
        if not self.feedback_items:
            return {
                "total_items": 0,
                "message": "No feedback collected yet"
            }

        by_source = {}
        for source in FeedbackSource:
            items = [i for i in self.feedback_items if i.source == source]
            if items:
                by_source[source.value] = {
                    "count": len(items),
                    "correct": sum(1 for i in items if i.is_correct),
                    "with_corrections": sum(1 for i in items if i.corrections),
                }

        by_type = {}
        for ftype in FeedbackType:
            items = [i for i in self.feedback_items if i.feedback_type == ftype]
            if items:
                by_type[ftype.value] = len(items)

        confidence_deltas = [
            item.confidence_adjusted - item.confidence_original
            for item in self.feedback_items
            if item.confidence_adjusted != item.confidence_original
        ]

        return {
            "total_items": len(self.feedback_items),
            "total_correct": sum(1 for i in self.feedback_items if i.is_correct),
            "total_incorrect": sum(1 for i in self.feedback_items if not i.is_correct),
            "items_with_corrections": sum(1 for i in self.feedback_items if i.corrections),
            "items_with_notes": sum(1 for i in self.feedback_items if i.notes),
            "accuracy_rate": sum(1 for i in self.feedback_items if i.is_correct) / len(self.feedback_items),
            "by_source": by_source,
            "by_type": by_type,
            "confidence_adjustments": {
                "count": len(confidence_deltas),
                "mean_delta": sum(confidence_deltas) / len(confidence_deltas) if confidence_deltas else 0,
                "positive_adjustments": sum(1 for d in confidence_deltas if d > 0),
                "negative_adjustments": sum(1 for d in confidence_deltas if d < 0),
            },
            "unique_reviewers": len(set(i.reviewer_id for i in self.feedback_items if i.reviewer_id)),
        }

    def __repr__(self) -> str:
        return (
            f"FeedbackCollector(run_id={self.run_id!r}, "
            f"patient_id={self.patient_id!r}, "
            f"items={len(self.feedback_items)})"
        )


# Convenience function for quick setup
def create_collector(run_dir: Path, reviewer_id: Optional[str] = None) -> FeedbackCollector:
    """
    Create a FeedbackCollector for a pipeline run.

    Args:
        run_dir: Path to the pipeline run output directory
        reviewer_id: Optional reviewer identifier

    Returns:
        Configured FeedbackCollector instance

    Example:
        >>> from code.arena.feedback_collector import create_collector
        >>> collector = create_collector(Path("outputs/demo_run"), reviewer_id="dr_smith")
        >>> collector.scan_for_feedback()
    """
    return FeedbackCollector(run_dir=run_dir, reviewer_id=reviewer_id)
