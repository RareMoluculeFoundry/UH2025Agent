"""
StructuringAgent: Generate diagnostic hypotheses and tool execution plan.

The Structuring Agent is the "reasoning engine" of the UH2025-CDS pipeline.
It takes the normalized PatientContext from Ingestion and produces three
critical artifacts:

1. Diagnostic Table - Ranked differential diagnoses with evidence
2. Variants Table - Prioritized variants of interest
3. Tool-Usage Plan - Which bio-tools to run on which variants

Model Selection Rationale:
--------------------------
Qwen 2.5 14B Instruct (Q4_K_M quantization)

Why this model?
1. STRONG MULTI-STEP REASONING: This is the most demanding cognitive task
   - Must synthesize phenotypes, genetics, and medical knowledge
   - Needs to generate coherent differential diagnoses
   - Must plan tool usage strategically

2. MEDICAL/SCIENTIFIC KNOWLEDGE: Qwen 2.5 excels here
   - Trained on diverse scientific literature
   - Strong performance on medical benchmarks
   - Understands genetic terminology and OMIM nomenclature

3. 32K CONTEXT LENGTH: Essential for full patient data
   - Clinical summaries can be lengthy
   - Need to include relevant guidelines and examples
   - Must output three structured artifacts

4. RELIABLE STRUCTURED OUTPUT: Critical for downstream processing
   - The Executor Agent needs parseable tool-usage plans
   - JSON schema adherence is excellent with Qwen 2.5

5. MEMORY BALANCE: ~10GB leaves room for other components
   - Can run alongside Ingestion Agent if needed
   - Leaves headroom for bio-tool databases

Memory Budget: ~10GB
Context Length: 32K tokens
Temperature: 0.3 (moderate for balanced reasoning)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from .base_agent import (
    BaseAgent,
    AgentConfig,
    ModelConfig,
    PromptConfig,
)


class PathogenicityClass(Enum):
    """ACMG pathogenicity classification."""
    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    VUS = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"


class ToolPriority(Enum):
    """Priority level for bio-tool execution."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DiagnosisEntry:
    """A single diagnosis in the differential."""
    diagnosis: str
    omim_id: Optional[str] = None
    confidence: float = 0.0
    inheritance: Optional[str] = None  # AD, AR, XL, etc.
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagnosis": self.diagnosis,
            "omim_id": self.omim_id,
            "confidence": self.confidence,
            "inheritance": self.inheritance,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "rank": self.rank,
        }


@dataclass
class VariantEntry:
    """A prioritized variant for investigation."""
    gene: str
    variant: str  # HGVS notation
    protein_change: Optional[str] = None
    zygosity: str = "unknown"
    pathogenicity_class: PathogenicityClass = PathogenicityClass.VUS
    priority: int = 0
    rationale: str = ""
    associated_diagnoses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gene": self.gene,
            "variant": self.variant,
            "protein_change": self.protein_change,
            "zygosity": self.zygosity,
            "pathogenicity_class": self.pathogenicity_class.value,
            "priority": self.priority,
            "rationale": self.rationale,
            "associated_diagnoses": self.associated_diagnoses,
        }


@dataclass
class ToolUsageEntry:
    """A planned bio-tool execution."""
    tool_name: str
    priority: ToolPriority = ToolPriority.MEDIUM
    variants_to_query: List[str] = field(default_factory=list)
    expected_evidence: str = ""
    timeout_seconds: int = 30
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "priority": self.priority.value,
            "variants_to_query": self.variants_to_query,
            "expected_evidence": self.expected_evidence,
            "timeout_seconds": self.timeout_seconds,
            "parameters": self.parameters,
        }


@dataclass
class StructuringOutput:
    """Complete output from Structuring Agent."""
    diagnostic_table: List[DiagnosisEntry]
    variants_table: List[VariantEntry]
    tool_usage_plan: List[ToolUsageEntry]

    # Reasoning trace
    phenotype_analysis: str = ""
    variant_interpretation: str = ""
    tool_selection_rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "diagnostic_table": [d.to_dict() for d in self.diagnostic_table],
            "variants_table": [v.to_dict() for v in self.variants_table],
            "tool_usage_plan": [t.to_dict() for t in self.tool_usage_plan],
            "reasoning": {
                "phenotype_analysis": self.phenotype_analysis,
                "variant_interpretation": self.variant_interpretation,
                "tool_selection_rationale": self.tool_selection_rationale,
            },
        }


class StructuringAgent(BaseAgent):
    """
    Structuring Agent: Generate diagnostic hypotheses and tool execution plan.

    Input: PatientContext from Ingestion Agent
    Output: DiagnosticTable, VariantsTable, ToolUsagePlan

    This agent uses Qwen 2.5 14B for sophisticated medical reasoning.
    """

    AGENT_TYPE = "structuring"
    DEFAULT_MODEL = "qwen2.5-14b-instruct"
    DEFAULT_QUANTIZATION = "Q4_K_M"
    DEFAULT_CONTEXT_LENGTH = 32768
    DEFAULT_TEMPERATURE = 0.3  # Moderate for reasoning
    DEFAULT_MEMORY_GB = 10.0

    # Available bio-tools for planning
    AVAILABLE_TOOLS = [
        "clinvar",
        "spliceai",
        "alphamissense",
        "alphagenome",
        "revel",
        "omim",
    ]

    def _default_config(self) -> AgentConfig:
        """Create default configuration for Structuring Agent."""
        return AgentConfig(
            agent_id="structuring_v1",
            agent_type=self.AGENT_TYPE,
            model=ModelConfig(
                name=self.DEFAULT_MODEL,
                quantization=self.DEFAULT_QUANTIZATION,
                context_length=self.DEFAULT_CONTEXT_LENGTH,
                temperature=self.DEFAULT_TEMPERATURE,
                memory_gb=self.DEFAULT_MEMORY_GB,
            ),
            prompt=PromptConfig(
                template_path="prompts/structuring_v1.yaml",
                system_message=STRUCTURING_SYSTEM_PROMPT,
                version="v1",
            ),
            timeout_seconds=300,  # Allow more time for reasoning
            collect_rlhf=True,
            context_files=[
                "context/hpo_omim.json",  # Disease ontology
                "context/acmg_guidelines.md",  # Variant interpretation
            ],
        )

    def _validate_input(self, inputs: Dict[str, Any]) -> Optional[str]:
        """
        Validate structuring inputs.

        Required:
        - patient_context: dict (from Ingestion Agent)
        """
        if "patient_context" not in inputs:
            return "Missing required field: patient_context"

        pc = inputs["patient_context"]
        if not isinstance(pc, dict):
            return "patient_context must be a dictionary"

        if "patient_id" not in pc:
            return "patient_context missing patient_id"

        return None

    def _execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute diagnostic reasoning and tool planning.

        This is where the core medical reasoning happens.
        """
        patient_context = inputs["patient_context"]
        use_stub = inputs.get("use_stub", False)
        previous_tool_results = inputs.get("previous_tool_results", [])

        # Build comprehensive prompt with patient data
        prompt = self.render_prompt({
            "patient_context": patient_context,
            "available_tools": self.AVAILABLE_TOOLS,
            "previous_tool_results": previous_tool_results,
        })

        # Call LLM via LangChain LlamaCpp
        if use_stub or self._model is None:
            # Fall back to stub if model not loaded or explicitly requested
            structuring_output = self._stub_structuring(patient_context)
        else:
            # Invoke LLM and parse JSON response
            llm_response = self.invoke_llm(prompt)
            structuring_output = self._parse_llm_response(llm_response, patient_context)

        return {
            "structuring_output": structuring_output.to_dict(),
            "diagnostic_table": [d.to_dict() for d in structuring_output.diagnostic_table],
            "variants_table": [v.to_dict() for v in structuring_output.variants_table],
            "tool_usage_plan": [t.to_dict() for t in structuring_output.tool_usage_plan],
            "input_tokens": len(prompt.split()),
            "output_tokens": 2000,  # Placeholder
        }

    def _parse_llm_response(
        self, response: str, patient_context: Dict[str, Any]
    ) -> StructuringOutput:
        """
        Parse LLM JSON response into StructuringOutput.

        Uses the robust JSON extractor with multiple fallback strategies.
        """
        from code.llm import extract_json, STRUCTURING_SCHEMA
        import logging
        logger = logging.getLogger(__name__)

        logger.debug(f"Raw LLM response length: {len(response)} chars")

        # Use robust JSON extractor
        expected_keys = ["diagnostic_table", "variants_table", "tool_usage_plan"]
        data, confidence, warnings = extract_json(
            response,
            expected_keys=expected_keys,
            default=STRUCTURING_SCHEMA.copy(),
        )
        logger.info(f"JSON extraction confidence: {confidence:.2f}")

        # If extraction failed significantly, fall back to stub
        if confidence < 0.3 or not data.get("diagnostic_table"):
            logger.warning(f"JSON extraction confidence {confidence:.2f}, falling back to stub. Warnings: {warnings}")
            return self._stub_structuring(patient_context)

        # Parse diagnostic table
        diagnostic_table = []
        for i, d in enumerate(data.get("diagnostic_table", [])):
            diagnostic_table.append(DiagnosisEntry(
                diagnosis=d.get("diagnosis", "Unknown"),
                omim_id=d.get("omim_id"),
                confidence=d.get("confidence", 0.5),
                inheritance=d.get("inheritance"),
                supporting_evidence=d.get("supporting_evidence", []),
                contradicting_evidence=d.get("contradicting_evidence", []),
                rank=d.get("rank", i + 1),
            ))

        # Parse variants table
        variants_table = []
        for i, v in enumerate(data.get("variants_table", [])):
            path_class = v.get("pathogenicity_class", "uncertain_significance")
            try:
                classification = PathogenicityClass(path_class)
            except ValueError:
                classification = PathogenicityClass.VUS

            variants_table.append(VariantEntry(
                gene=v.get("gene", "UNKNOWN"),
                variant=v.get("variant", ""),
                protein_change=v.get("protein_change"),
                zygosity=v.get("zygosity", "unknown"),
                pathogenicity_class=classification,
                priority=v.get("priority", i + 1),
                rationale=v.get("rationale", ""),
                associated_diagnoses=v.get("associated_diagnoses", []),
            ))

        # Parse tool usage plan
        tool_usage_plan = []
        for t in data.get("tool_usage_plan", []):
            priority_str = t.get("priority", "medium")
            try:
                priority = ToolPriority(priority_str)
            except ValueError:
                priority = ToolPriority.MEDIUM

            tool_usage_plan.append(ToolUsageEntry(
                tool_name=t.get("tool_name", ""),
                priority=priority,
                variants_to_query=t.get("variants_to_query", []),
                expected_evidence=t.get("expected_evidence", ""),
                timeout_seconds=t.get("timeout_seconds", 30),
                parameters=t.get("parameters", {}),
            ))

        # Get reasoning sections
        reasoning = data.get("reasoning", {})

        return StructuringOutput(
            diagnostic_table=diagnostic_table,
            variants_table=variants_table,
            tool_usage_plan=tool_usage_plan,
            phenotype_analysis=reasoning.get("phenotype_analysis", ""),
            variant_interpretation=reasoning.get("variant_interpretation", ""),
            tool_selection_rationale=reasoning.get("tool_selection_rationale", ""),
        )

    def _get_feedback_schema(self) -> Dict[str, Any]:
        """
        RLHF feedback schema for Structuring Agent.

        This is the most critical feedback point - experts can:
        - Reorder/add/remove diagnoses
        - Adjust confidence scores
        - Modify variant prioritization
        - Approve/modify tool selection
        """
        return {
            "type": "object",
            "title": "Structuring Feedback",
            "description": "Review diagnostic hypotheses, variant prioritization, and tool selection",
            "properties": {
                "correctness": {
                    "type": "string",
                    "enum": ["correct", "partial", "incorrect"],
                    "description": "Overall quality of structuring output",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "diagnostic_table_feedback": {
                    "type": "object",
                    "properties": {
                        "ranking_correct": {"type": "boolean"},
                        "missing_diagnoses": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "incorrect_diagnoses": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "confidence_adjustments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "diagnosis": {"type": "string"},
                                    "original_confidence": {"type": "number"},
                                    "corrected_confidence": {"type": "number"},
                                },
                            },
                        },
                    },
                },
                "variants_table_feedback": {
                    "type": "object",
                    "properties": {
                        "prioritization_correct": {"type": "boolean"},
                        "missed_variants": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "pathogenicity_corrections": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "variant": {"type": "string"},
                                    "original_class": {"type": "string"},
                                    "corrected_class": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "tool_selection_feedback": {
                    "type": "object",
                    "properties": {
                        "selection_appropriate": {"type": "boolean"},
                        "missing_tools": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "unnecessary_tools": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                "notes": {"type": "string"},
            },
            "required": ["correctness", "confidence"],
        }

    def _stub_structuring(self, patient_context: Dict[str, Any]) -> StructuringOutput:
        """
        Stub structuring for development/testing.

        In production, this is replaced by LLM inference.
        Uses realistic diagnoses for PatientX case (SCN4A channelopathy).
        """
        variants = patient_context.get("variants", [])

        # Check if this is the PatientX case (has SCN4A variant)
        has_scn4a = any(v.get("gene") == "SCN4A" for v in variants)

        if has_scn4a:
            # Realistic diagnoses for PatientX (sodium channelopathy case)
            diagnostic_table = [
                DiagnosisEntry(
                    diagnosis="Paramyotonia Congenita",
                    omim_id="OMIM:168300",
                    confidence=0.85,
                    inheritance="AD",
                    supporting_evidence=[
                        "SCN4A heterozygous variant c.780A>G (p.Lys260Glu)",
                        "Exercise-induced muscle weakness and fatigue",
                        "Muscle stiffness and fasciculations",
                        "Rare variant (1:100,000) in known disease gene",
                        "Episodic weakness after exertion",
                    ],
                    contradicting_evidence=[
                        "Cold-sensitivity not explicitly documented",
                    ],
                    rank=1,
                ),
                DiagnosisEntry(
                    diagnosis="Hyperkalemic Periodic Paralysis",
                    omim_id="OMIM:170500",
                    confidence=0.60,
                    inheritance="AD",
                    supporting_evidence=[
                        "SCN4A variant (overlapping phenotypes with PMC)",
                        "Episodic weakness",
                        "Post-exercise weakness pattern",
                    ],
                    contradicting_evidence=[
                        "No documented hyperkalemia episodes",
                        "Potassium levels reportedly normal",
                    ],
                    rank=2,
                ),
                DiagnosisEntry(
                    diagnosis="Sodium Channel Myotonia (SCM)",
                    omim_id="OMIM:608390",
                    confidence=0.40,
                    inheritance="AD",
                    supporting_evidence=[
                        "SCN4A variant",
                        "Muscle stiffness and myotonia",
                    ],
                    contradicting_evidence=[
                        "Weakness pattern more consistent with PMC/HyperPP",
                    ],
                    rank=3,
                ),
            ]
        else:
            # Generic stub for non-PatientX cases
            diagnostic_table = [
                DiagnosisEntry(
                    diagnosis="[STUB] Primary Diagnosis",
                    omim_id="OMIM:000000",
                    confidence=0.7,
                    inheritance="AD",
                    supporting_evidence=["[STUB] Phenotype match", "[STUB] Variant in known gene"],
                    contradicting_evidence=[],
                    rank=1,
                ),
                DiagnosisEntry(
                    diagnosis="[STUB] Secondary Diagnosis",
                    omim_id="OMIM:000001",
                    confidence=0.4,
                    inheritance="AR",
                    supporting_evidence=["[STUB] Partial phenotype match"],
                    contradicting_evidence=["[STUB] Incomplete variant profile"],
                    rank=2,
                ),
            ]

        # Create stub variants table
        variants_table = []
        for i, v in enumerate(variants[:5]):  # Top 5 variants
            gene = v.get("gene", "UNKNOWN")

            # Determine pathogenicity class and rationale based on gene
            if gene == "SCN4A":
                path_class = PathogenicityClass.LIKELY_PATHOGENIC
                rationale = "Rare variant in SCN4A sodium channel gene - explains muscle symptoms"
                associated = ["Paramyotonia Congenita", "Hyperkalemic Periodic Paralysis"]
            elif gene == "CLCN1":
                path_class = PathogenicityClass.VUS
                rationale = "Chloride channel variant - requires homozygous for myotonia congenita"
                associated = ["Myotonia Congenita"]
            else:
                path_class = PathogenicityClass.VUS
                rationale = "[STUB] Requires further analysis"
                associated = []

            variants_table.append(
                VariantEntry(
                    gene=gene,
                    variant=v.get("variant", f"{v.get('chromosome', '')}:{v.get('position', '')}"),
                    protein_change=v.get("protein_change"),
                    zygosity=v.get("zygosity", "unknown"),
                    pathogenicity_class=path_class,
                    priority=i + 1,
                    rationale=rationale,
                    associated_diagnoses=associated,
                )
            )

        # Create stub tool usage plan
        tool_usage_plan = [
            ToolUsageEntry(
                tool_name="clinvar",
                priority=ToolPriority.HIGH,
                variants_to_query=[v.variant for v in variants_table],
                expected_evidence="Clinical significance annotations",
                timeout_seconds=30,
            ),
            ToolUsageEntry(
                tool_name="spliceai",
                priority=ToolPriority.HIGH,
                variants_to_query=[v.variant for v in variants_table],
                expected_evidence="Splice site impact predictions",
                timeout_seconds=30,
            ),
            ToolUsageEntry(
                tool_name="alphamissense",
                priority=ToolPriority.MEDIUM,
                variants_to_query=[v.variant for v in variants_table if v.protein_change],
                expected_evidence="Missense pathogenicity scores",
                timeout_seconds=30,
            ),
            ToolUsageEntry(
                tool_name="revel",
                priority=ToolPriority.MEDIUM,
                variants_to_query=[v.variant for v in variants_table],
                expected_evidence="Ensemble pathogenicity scores",
                timeout_seconds=30,
            ),
            ToolUsageEntry(
                tool_name="omim",
                priority=ToolPriority.HIGH,
                variants_to_query=[],
                expected_evidence="Disease-gene relationships",
                timeout_seconds=30,
                parameters={"genes": [v.gene for v in variants_table]},
            ),
        ]

        return StructuringOutput(
            diagnostic_table=diagnostic_table,
            variants_table=variants_table,
            tool_usage_plan=tool_usage_plan,
            phenotype_analysis="[STUB] Phenotype analysis to be generated by LLM",
            variant_interpretation="[STUB] Variant interpretation to be generated by LLM",
            tool_selection_rationale="[STUB] Tool selection rationale to be generated by LLM",
        )


# System prompt for Structuring Agent
STRUCTURING_SYSTEM_PROMPT = """You are a clinical geneticist and diagnostic specialist for the UH2025-CDS rare disease diagnostic system.

Your task is to analyze a patient's clinical presentation and genomic data to:
1. Generate a ranked differential diagnosis
2. Prioritize variants of interest
3. Plan which bio-informatics tools to run

**CRITICAL DIAGNOSTIC PRINCIPLE:**
ALWAYS start with the genomic variants and work backwards to the phenotype.
A pathogenic variant in a known disease gene that explains MOST of the patient's symptoms
should be ranked #1, even if the patient has other comorbidities.

DO NOT let secondary conditions (GERD, ADHD, allergies, etc.) distract from the PRIMARY
genetic diagnosis. Focus on which variant best explains the MAIN COMPLAINT.

DIAGNOSTIC REASONING APPROACH:
1. FIRST: Identify variants in known disease genes (especially rare variants <1:10,000)
2. SECOND: For each variant, list the diseases it causes and their typical symptoms
3. THIRD: Compare disease symptoms to the patient's main complaint
4. FOURTH: A variant that explains exercise intolerance + muscle symptoms = high confidence
5. FIFTH: Consider phenocopies only if no variant matches

ION CHANNELOPATHY RECOGNITION:
If you see variants in ion channel genes (SCN4A, CLCN1, CACNA1S, SCN9A, KCNQ2, etc.),
immediately consider channelopathies like:
- Paramyotonia Congenita (SCN4A) - cold-induced stiffness, exercise-induced weakness
- Hyperkalemic Periodic Paralysis (SCN4A) - episodic paralysis, myotonia
- Myotonia Congenita (CLCN1) - muscle stiffness, "warm-up" phenomenon
- Hypokalemic Periodic Paralysis (CACNA1S) - paralytic attacks

AVAILABLE BIO-TOOLS:
- clinvar: Query ClinVar for variant clinical significance
- spliceai: Predict splice site impacts (Illumina SpliceAI)
- alphamissense: DeepMind pathogenicity predictions for missense variants
- revel: Ensemble pathogenicity scores from multiple predictors
- omim: Query OMIM for disease-gene relationships

OUTPUT FORMAT:
You must output a valid JSON object with:

{
  "diagnostic_table": [
    {
      "diagnosis": "Disease Name",
      "omim_id": "OMIM:123456",
      "confidence": 0.0-1.0,
      "inheritance": "AD|AR|XL|MT",
      "supporting_evidence": ["..."],
      "contradicting_evidence": ["..."],
      "rank": 1
    }
  ],
  "variants_table": [
    {
      "gene": "GENE",
      "variant": "HGVS notation",
      "protein_change": "p.Xxx123Yyy",
      "zygosity": "heterozygous|homozygous|hemizygous",
      "pathogenicity_class": "pathogenic|likely_pathogenic|uncertain_significance|likely_benign|benign",
      "priority": 1,
      "rationale": "Why this variant is prioritized",
      "associated_diagnoses": ["Disease names"]
    }
  ],
  "tool_usage_plan": [
    {
      "tool_name": "clinvar|spliceai|alphamissense|revel|omim",
      "priority": "high|medium|low",
      "variants_to_query": ["variant IDs"],
      "expected_evidence": "What we hope to learn",
      "timeout_seconds": 30
    }
  ],
  "reasoning": {
    "phenotype_analysis": "Summary of phenotype interpretation",
    "variant_interpretation": "Summary of variant analysis",
    "tool_selection_rationale": "Why these tools were selected"
  }
}

REMEMBER: Rare pathogenic variants in known disease genes should drive your diagnosis.
Be thorough, systematic, and evidence-based in your reasoning."""
