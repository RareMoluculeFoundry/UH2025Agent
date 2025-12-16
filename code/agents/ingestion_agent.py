"""
IngestionAgent: Parse and normalize clinical input data.

The Ingestion Agent is the first step in the UH2025-CDS pipeline.
It reads raw clinical summaries (PDF, Markdown, text) and genomic
data (VCF, JSON) and converts them into a normalized Patient Context
object for downstream processing.

Model Selection Rationale:
--------------------------
Llama 3.2 3B Instruct (Q4_K_M quantization)

Why this model?
1. SPEED: ~100+ tokens/sec on M4 Apple Silicon
   - Ingestion needs to be fast; it's the pipeline entry point
   - Users expect quick response when uploading patient data

2. INSTRUCTION FOLLOWING: Excellent at structured extraction
   - Llama 3.2 was specifically trained for instruction following
   - Consistent output format is critical for downstream agents

3. MEMORY FOOTPRINT: Only ~2GB
   - Allows other models to be pre-loaded
   - Or enables resource-constrained deployments

4. SUFFICIENT CAPABILITY: Clinical text extraction is well-suited
   - We're not doing complex reasoning here
   - Just parsing and normalization
   - A larger model would be overkill

Memory Budget: ~2GB (can stay loaded alongside Structuring Agent)
Context Length: 8K tokens (sufficient for typical clinical summaries)
Temperature: 0.1 (low for deterministic, consistent extraction)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base_agent import (
    BaseAgent,
    AgentConfig,
    ModelConfig,
    PromptConfig,
)


@dataclass
class Variant:
    """Genomic variant representation."""
    gene: str
    chromosome: str
    position: int
    reference: str
    alternate: str
    variant_id: Optional[str] = None  # rsID or ClinVar ID
    protein_change: Optional[str] = None
    transcript: Optional[str] = None
    zygosity: str = "unknown"  # heterozygous, homozygous, hemizygous
    quality: Optional[float] = None
    filter_status: str = "PASS"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gene": self.gene,
            "chromosome": self.chromosome,
            "position": self.position,
            "reference": self.reference,
            "alternate": self.alternate,
            "variant_id": self.variant_id,
            "protein_change": self.protein_change,
            "transcript": self.transcript,
            "zygosity": self.zygosity,
            "quality": self.quality,
            "filter_status": self.filter_status,
        }


@dataclass
class PatientContext:
    """
    Normalized patient context output from Ingestion Agent.

    This is the standardized format passed to the Structuring Agent.
    """
    patient_id: str

    # Demographics
    age: Optional[int] = None
    sex: Optional[str] = None
    ethnicity: Optional[str] = None

    # Clinical presentation
    chief_complaint: str = ""
    history_present_illness: str = ""
    past_medical_history: List[str] = field(default_factory=list)
    family_history: str = ""

    # Physical exam
    physical_exam: Dict[str, Any] = field(default_factory=dict)

    # Genomic data
    variants: List[Variant] = field(default_factory=list)

    # Metadata
    source_files: List[str] = field(default_factory=list)
    extraction_confidence: float = 0.0
    extraction_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "demographics": {
                "age": self.age,
                "sex": self.sex,
                "ethnicity": self.ethnicity,
            },
            "clinical_presentation": {
                "chief_complaint": self.chief_complaint,
                "history_present_illness": self.history_present_illness,
                "past_medical_history": self.past_medical_history,
                "family_history": self.family_history,
            },
            "physical_exam": self.physical_exam,
            "variants": [v.to_dict() for v in self.variants],
            "metadata": {
                "source_files": self.source_files,
                "extraction_confidence": self.extraction_confidence,
                "extraction_warnings": self.extraction_warnings,
            },
        }


class IngestionAgent(BaseAgent):
    """
    Ingestion Agent: Parse and normalize clinical input data.

    Input: Raw clinical summary (text/markdown/PDF) + genomic data (VCF/JSON)
    Output: Normalized PatientContext object

    This agent uses Llama 3.2 3B for fast, accurate text extraction.
    """

    AGENT_TYPE = "ingestion"
    DEFAULT_MODEL = "llama-3.2-3b-instruct"
    DEFAULT_QUANTIZATION = "Q4_K_M"
    DEFAULT_CONTEXT_LENGTH = 8192
    DEFAULT_TEMPERATURE = 0.1  # Low for deterministic extraction
    DEFAULT_MEMORY_GB = 2.0

    def _default_config(self) -> AgentConfig:
        """Create default configuration for Ingestion Agent."""
        return AgentConfig(
            agent_id="ingestion_v1",
            agent_type=self.AGENT_TYPE,
            model=ModelConfig(
                name=self.DEFAULT_MODEL,
                quantization=self.DEFAULT_QUANTIZATION,
                context_length=self.DEFAULT_CONTEXT_LENGTH,
                temperature=self.DEFAULT_TEMPERATURE,
                memory_gb=self.DEFAULT_MEMORY_GB,
            ),
            prompt=PromptConfig(
                template_path="prompts/ingestion_v1.yaml",
                system_message=INGESTION_SYSTEM_PROMPT,
                version="v1",
            ),
            timeout_seconds=120,  # Fast model, should complete quickly
            collect_rlhf=True,
        )

    def _validate_input(self, inputs: Dict[str, Any]) -> Optional[str]:
        """
        Validate ingestion inputs.

        Required:
        - clinical_summary: str (raw clinical text)

        Optional:
        - genomic_data: dict (VCF-style variant data)
        - patient_id: str (if not provided, will be generated)
        """
        if "clinical_summary" not in inputs:
            return "Missing required field: clinical_summary"

        if not isinstance(inputs["clinical_summary"], str):
            return "clinical_summary must be a string"

        if len(inputs["clinical_summary"].strip()) == 0:
            return "clinical_summary cannot be empty"

        return None

    def _execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute clinical data extraction.

        This is where the LLM is called to parse the clinical summary
        and extract structured information.
        """
        import json

        clinical_summary = inputs["clinical_summary"]
        genomic_data = inputs.get("genomic_data", {})
        patient_id = inputs.get("patient_id", self._generate_patient_id())
        use_stub = inputs.get("use_stub", False)

        # Build prompt
        prompt = self.render_prompt({
            "clinical_summary": clinical_summary,
            "patient_id": patient_id,
        })

        # Call LLM via LangChain LlamaCpp
        if use_stub or self._model is None:
            # Fall back to stub if model not loaded or explicitly requested
            extracted_data = self._stub_extraction(clinical_summary, patient_id)
        else:
            # Invoke LLM and parse JSON response
            llm_response = self.invoke_llm(prompt)
            extracted_data = self._parse_llm_response(llm_response, patient_id)

        # Parse genomic data if provided
        variants = self._parse_variants(genomic_data)
        extracted_data["variants"] = [v.to_dict() for v in variants]

        # Create PatientContext
        patient_context = PatientContext(
            patient_id=patient_id,
            age=extracted_data.get("demographics", {}).get("age"),
            sex=extracted_data.get("demographics", {}).get("sex"),
            ethnicity=extracted_data.get("demographics", {}).get("ethnicity"),
            chief_complaint=extracted_data.get("chief_complaint", ""),
            history_present_illness=extracted_data.get("history_present_illness", ""),
            past_medical_history=extracted_data.get("past_medical_history", []),
            family_history=extracted_data.get("family_history", ""),
            physical_exam=extracted_data.get("physical_exam", {}),
            variants=variants,
            source_files=inputs.get("source_files", []),
            extraction_confidence=extracted_data.get("confidence", 0.0),
            extraction_warnings=extracted_data.get("warnings", []),
        )

        return {
            "patient_context": patient_context.to_dict(),
            "raw_extraction": extracted_data,
            "input_tokens": len(prompt.split()),  # Rough estimate
            "output_tokens": 500,  # Placeholder
        }

    def _get_feedback_schema(self) -> Dict[str, Any]:
        """
        RLHF feedback schema for Ingestion Agent.

        Experts can correct:
        - Demographics extraction
        - Clinical presentation parsing
        - Variant identification
        """
        return {
            "type": "object",
            "title": "Ingestion Feedback",
            "description": "Review and correct the clinical data extraction",
            "properties": {
                "correctness": {
                    "type": "string",
                    "enum": ["correct", "partial", "incorrect"],
                    "description": "Overall extraction accuracy",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Your confidence in the extraction (0-1)",
                },
                "corrections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "original": {"type": "string"},
                            "corrected": {"type": "string"},
                            "rationale": {"type": "string"},
                        },
                    },
                    "description": "Specific field corrections",
                },
                "missing_information": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Information present in source but not extracted",
                },
                "notes": {
                    "type": "string",
                    "description": "Additional feedback notes",
                },
            },
            "required": ["correctness", "confidence"],
        }

    def _generate_patient_id(self) -> str:
        """Generate a unique patient ID."""
        from datetime import datetime
        import random
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        suffix = random.randint(1000, 9999)
        return f"PAT-{timestamp}-{suffix}"

    def _parse_variants(self, genomic_data: Dict[str, Any]) -> List[Variant]:
        """
        Parse genomic data into Variant objects.

        Supports VCF-style JSON format.
        """
        variants = []
        raw_variants = genomic_data.get("variants", [])

        for v in raw_variants:
            variant = Variant(
                gene=v.get("gene", "UNKNOWN"),
                chromosome=v.get("chrom", v.get("chromosome", "")),
                position=v.get("pos", v.get("position", 0)),
                reference=v.get("ref", v.get("reference", "")),
                alternate=v.get("alt", v.get("alternate", "")),
                variant_id=v.get("id", v.get("variant_id")),
                protein_change=v.get("protein_change", v.get("hgvsp")),
                transcript=v.get("transcript"),
                zygosity=v.get("zygosity", "unknown"),
                quality=v.get("qual", v.get("quality")),
                filter_status=v.get("filter", "PASS"),
            )
            variants.append(variant)

        return variants

    def _parse_llm_response(
        self, response: str, patient_id: str
    ) -> Dict[str, Any]:
        """
        Parse LLM JSON response into extraction data.

        Uses the robust JSON extractor with multiple fallback strategies:
        1. Direct JSON parse
        2. Extract from markdown code blocks
        3. Find JSON patterns with regex
        4. Repair common JSON errors
        """
        from code.llm import extract_json, INGESTION_SCHEMA
        import logging
        logger = logging.getLogger(__name__)

        logger.debug(f"Raw LLM response length: {len(response)} chars")

        # Use robust JSON extractor
        expected_keys = ["demographics", "chief_complaint"]
        data, confidence, warnings = extract_json(
            response,
            expected_keys=expected_keys,
            default=INGESTION_SCHEMA.copy(),
        )
        logger.info(f"JSON extraction confidence: {confidence:.2f}")

        # Ensure patient_id is set
        data["patient_id"] = patient_id

        # Use extracted confidence or keep default
        if "confidence" not in data or data["confidence"] == 0.5:
            data["confidence"] = confidence

        # Merge extraction warnings
        if "warnings" not in data:
            data["warnings"] = []
        data["warnings"].extend(warnings)

        # If extraction mostly failed, store raw response for debugging
        if confidence < 0.5:
            data["_raw_llm_response"] = response[:1000]
            if not data.get("chief_complaint"):
                data["chief_complaint"] = "[Extraction incomplete - see warnings]"
            if not data.get("history_present_illness"):
                # Try to use raw response as HPI
                data["history_present_illness"] = self._extract_hpi_fallback(response)

        return data

    def _extract_hpi_fallback(self, response: str) -> str:
        """
        Extract history of present illness from raw response as fallback.

        When JSON parsing fails, try to extract useful clinical content.
        """
        # Remove any JSON-like content
        import re
        cleaned = re.sub(r'\{[\s\S]*\}', '', response)
        cleaned = re.sub(r'```[\s\S]*```', '', cleaned)

        # Take first 500 chars of meaningful content
        lines = [l.strip() for l in cleaned.split('\n') if l.strip()]
        content = ' '.join(lines)[:500]

        return content if content else "[No extractable content]"

    def _stub_extraction(
        self, clinical_summary: str, patient_id: str
    ) -> Dict[str, Any]:
        """
        Stub extraction for development/testing.

        Used when LLM is not loaded or explicitly requested via use_stub=True.
        """
        # Simple keyword-based extraction for demonstration
        summary_lower = clinical_summary.lower()

        # Age extraction (very basic)
        age = None
        for pattern in ["year-old", "years old", "yo ", "y/o"]:
            if pattern in summary_lower:
                # Find number before pattern
                idx = summary_lower.find(pattern)
                words = summary_lower[:idx].split()
                if words:
                    try:
                        age = int(words[-1])
                    except ValueError:
                        pass
                break

        # Sex extraction
        sex = None
        if "female" in summary_lower or " she " in summary_lower:
            sex = "female"
        elif "male" in summary_lower or " he " in summary_lower:
            sex = "male"

        return {
            "patient_id": patient_id,
            "demographics": {
                "age": age,
                "sex": sex,
                "ethnicity": None,
            },
            "chief_complaint": "[STUB] Chief complaint to be extracted by LLM",
            "history_present_illness": "[STUB] HPI to be extracted by LLM",
            "past_medical_history": [],
            "family_history": "[STUB] Family history to be extracted by LLM",
            "physical_exam": {},
            "confidence": 0.5,  # Low confidence for stub
            "warnings": ["Using stub extraction - LLM not connected"],
        }


# System prompt for Ingestion Agent
INGESTION_SYSTEM_PROMPT = """You are a clinical data extraction specialist for the UH2025-CDS rare disease diagnostic system.

Your task is to parse unstructured clinical summaries and extract structured information.

EXTRACTION GUIDELINES:
1. Be conservative - only extract information that is explicitly stated
2. Use standard medical terminology
3. Flag ambiguous or conflicting information
4. Preserve original phrasing for symptoms and complaints
5. Note any information that may be missing or incomplete

OUTPUT FORMAT:
You must output a valid JSON object with the following structure:

{
  "patient_id": "string",
  "demographics": {
    "age": number or null,
    "sex": "male" | "female" | null,
    "ethnicity": "string" or null
  },
  "chief_complaint": "string",
  "history_present_illness": "string",
  "past_medical_history": ["string"],
  "family_history": "string",
  "physical_exam": {
    "general": "string",
    "neurological": "string",
    "musculoskeletal": "string",
    ...
  },
  "confidence": number (0-1),
  "warnings": ["string"]
}

Extract information carefully and completely. If information is not present, use null or empty values."""
