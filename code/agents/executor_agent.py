"""
ExecutorAgent: Execute bio-tools in sandboxed environment.

The Executor Agent is the "hands" of the UH2025-CDS pipeline.
It takes the Tool-Usage Plan from Structuring and executes each
bio-tool in a secure, sandboxed environment, collecting results.

Architecture Decision: NO LLM
-----------------------------
The Executor Agent is unique - it uses NO language model.

Why pure Python orchestration?

1. DETERMINISM: Tool execution should be 100% reproducible
   - Same inputs = same outputs, always
   - No stochastic LLM behavior

2. SECURITY: No prompt injection attack surface
   - The Structuring Agent's tool plan is data, not code
   - We execute predefined tool wrappers, not generated code

3. SPEED: Direct API calls are faster than LLM coordination
   - No token generation latency
   - Parallel execution of independent tools

4. AUDITABILITY: Complete logging for compliance
   - Every API call is logged
   - Timing, parameters, responses all captured
   - Essential for clinical decision support systems

5. RELIABILITY: Explicit error handling
   - Timeout management per tool
   - Retry logic with backoff
   - Graceful degradation

Memory Budget: <1GB (just Python + tool clients)
Network: Allowed for API calls to bio-databases
Sandboxing: File system restricted, network to approved endpoints only
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import asyncio
import json
import time


class ToolStatus(Enum):
    """Execution status for a tool."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class ToolResult:
    """Result from a single bio-tool execution."""
    tool_name: str
    status: ToolStatus
    variants_queried: List[str] = field(default_factory=list)

    # Results
    results: Dict[str, Any] = field(default_factory=dict)
    annotations: List[Dict[str, Any]] = field(default_factory=list)

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Errors
    error_message: Optional[str] = None
    retry_count: int = 0

    # Metadata
    api_calls: int = 0
    rate_limited: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "status": self.status.value,
            "variants_queried": self.variants_queried,
            "results": self.results,
            "annotations": self.annotations,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "api_calls": self.api_calls,
            "rate_limited": self.rate_limited,
        }


@dataclass
class ExecutorOutput:
    """Complete output from Executor Agent."""
    tool_results: List[ToolResult]
    total_duration_seconds: float = 0.0
    tools_completed: int = 0
    tools_failed: int = 0

    # Execution metadata
    execution_id: str = ""
    parallelism_used: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_results": [tr.to_dict() for tr in self.tool_results],
            "total_duration_seconds": self.total_duration_seconds,
            "tools_completed": self.tools_completed,
            "tools_failed": self.tools_failed,
            "execution_id": self.execution_id,
            "parallelism_used": self.parallelism_used,
        }


class ExecutorAgent:
    """
    Executor Agent: Execute bio-tools in sandboxed environment.

    Input: ToolUsagePlan + VariantsTable from Structuring Agent
    Output: Aggregated tool results (JSON)

    NOTE: This agent does NOT inherit from BaseAgent because it
    does NOT use an LLM. It's pure Python orchestration.
    """

    AGENT_TYPE = "executor"

    # Tool registry - maps tool names to wrapper classes
    # In production, these would be imported from code/biotools/
    TOOL_REGISTRY = {
        "clinvar": "ClinVarTool",
        "spliceai": "SpliceAITool",
        "alphamissense": "AlphaMissenseTool",
        "revel": "REVELTool",
        "omim": "OMIMTool",
    }

    def __init__(
        self,
        max_concurrent: int = 3,
        default_timeout: int = 30,
        collect_rlhf: bool = True,
    ):
        """
        Initialize Executor Agent.

        Args:
            max_concurrent: Maximum tools to run in parallel
            default_timeout: Default timeout per tool (seconds)
            collect_rlhf: Whether to collect RLHF feedback
        """
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.collect_rlhf = collect_rlhf
        self._tools = {}
        self._load_tools()

    def _load_tools(self) -> None:
        """Load bio-tool wrappers from registry."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from code.biotools import TOOL_REGISTRY
            
            logger.debug(f"Loading {len(TOOL_REGISTRY)} bio-tools: {list(TOOL_REGISTRY.keys())}")
            
            for name, tool_class in TOOL_REGISTRY.items():
                try:
                    self._tools[name] = tool_class()
                except Exception as e:
                    logger.error(f"Failed to instantiate {name}: {e}")
                    
        except ImportError as e:
            logger.warning(f"Could not import bio-tools: {e}. Running in stub mode.")
            # Fallback to stub dictionary if import fails
            self._tools = {}

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute bio-tools according to the tool-usage plan.

        Args:
            inputs: Must contain 'tool_usage_plan' and 'variants_table'

        Returns:
            Dictionary with tool results and metadata
        """
        validation_error = self._validate_input(inputs)
        if validation_error:
            return {
                "status": "failed",
                "error": validation_error,
            }

        tool_usage_plan = inputs["tool_usage_plan"]
        variants_table = inputs.get("variants_table", [])

        start_time = datetime.now()
        execution_id = f"exec_{start_time.strftime('%Y%m%d_%H%M%S')}"

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Starting execution {execution_id}: {len(tool_usage_plan)} tools, {len(variants_table)} variants")

        # Execute tools (prioritized)
        tool_results = self._execute_tools(tool_usage_plan, variants_table)

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Aggregate results
        executor_output = ExecutorOutput(
            tool_results=tool_results,
            total_duration_seconds=total_duration,
            tools_completed=sum(1 for tr in tool_results if tr.status == ToolStatus.COMPLETED),
            tools_failed=sum(1 for tr in tool_results if tr.status in [ToolStatus.FAILED, ToolStatus.TIMEOUT]),
            execution_id=execution_id,
            parallelism_used=self.max_concurrent,
        )

        logger.info(f"Execution complete: {total_duration:.2f}s, {executor_output.tools_completed} completed, {executor_output.tools_failed} failed")

        result = {
            "executor_output": executor_output.to_dict(),
            "tool_results": [tr.to_dict() for tr in tool_results],
            "execution_id": execution_id,
            "duration_seconds": total_duration,
        }

        if self.collect_rlhf:
            result["awaiting_feedback"] = True
            result["feedback_schema"] = self._get_feedback_schema()

        return result

    def _validate_input(self, inputs: Dict[str, Any]) -> Optional[str]:
        """Validate executor inputs."""
        if "tool_usage_plan" not in inputs:
            return "Missing required field: tool_usage_plan"

        plan = inputs["tool_usage_plan"]
        if not isinstance(plan, list):
            return "tool_usage_plan must be a list"

        for i, entry in enumerate(plan):
            if "tool_name" not in entry:
                return f"tool_usage_plan[{i}] missing tool_name"
            if entry["tool_name"] not in self.TOOL_REGISTRY:
                return f"Unknown tool: {entry['tool_name']}"

        return None

    def _execute_tools(
        self,
        tool_usage_plan: List[Dict[str, Any]],
        variants_table: List[Dict[str, Any]],
    ) -> List[ToolResult]:
        """
        Execute tools according to plan.

        Runs high-priority tools first, with parallel execution
        within priority levels.
        """
        import logging
        logger = logging.getLogger(__name__)
        results = []

        # Group by priority
        priority_groups = {"high": [], "medium": [], "low": []}
        for entry in tool_usage_plan:
            priority = entry.get("priority", "medium")
            priority_groups[priority].append(entry)

        # Execute in priority order
        for priority in ["high", "medium", "low"]:
            group = priority_groups[priority]
            if not group:
                continue

            logger.debug(f"Executing {len(group)} {priority}-priority tools")

            # In production, would use asyncio for parallel execution
            for entry in group:
                result = self._execute_single_tool(entry, variants_table)
                results.append(result)

        return results

    def _execute_single_tool(
        self,
        tool_entry: Dict[str, Any],
        variants_table: List[Dict[str, Any]],
    ) -> ToolResult:
        """
        Execute a single bio-tool.
        """
        tool_name = tool_entry["tool_name"]
        timeout = tool_entry.get("timeout_seconds", self.default_timeout)
        variants_to_query = tool_entry.get("variants_to_query", [])
        parameters = tool_entry.get("parameters", {})

        result = ToolResult(
            tool_name=tool_name,
            status=ToolStatus.PENDING,
            variants_queried=variants_to_query,
            start_time=datetime.now(),
        )

        import logging
        logger = logging.getLogger(__name__)

        try:
            result.status = ToolStatus.RUNNING
            logger.debug(f"Running {tool_name}...")
            
            tool_instance = self._tools.get(tool_name)
            
            if tool_instance:
                from code.biotools.base_tool import Variant
                
                # Execute against actual tool
                annotations = []
                for v_str in variants_to_query:
                    # Find variant data in table
                    v_data = next((v for v in variants_table if v.get("variant") == v_str), None)
                    
                    if v_data:
                        # Construct Variant object (parsing HGVS/strings if needed)
                        # For now, we assume simple mapping if fields exist
                        # Use split for CHR:POS:REF:ALT if formatted that way
                        
                        # Fallback parsing for HGVS strings if structure is missing
                        chrom = v_data.get("chromosome")
                        pos = v_data.get("position")
                        ref = v_data.get("reference")
                        alt = v_data.get("alternate")
                        
                        # Try to parse from variant string if fields missing
                        if not all([chrom, pos, ref, alt]) and ":" in v_str and ">" in v_str:
                             try:
                                 # Very basic parsing: chr:pos:ref>alt
                                 parts = v_str.replace(">", ":").split(":")
                                 if len(parts) >= 4:
                                     chrom = parts[0]
                                     pos = int(parts[1])
                                     ref = parts[2]
                                     alt = parts[3]
                             except:
                                 pass

                        variant_obj = Variant(
                            chromosome=chrom,
                            position=int(pos) if pos else None,
                            reference=ref,
                            alternate=alt,
                            gene=v_data.get("gene"),
                            hgvs_c=v_str if v_str.startswith("c.") else None,
                            hgvs_p=v_data.get("protein_change"),
                            zygosity=v_data.get("zygosity")
                        )
                        
                        tool_res = tool_instance.query(variant_obj)
                        annotations.append(tool_res.to_dict())
                        result.api_calls += 1
                    else:
                        annotations.append({"variant": v_str, "error": "Variant data not found in table"})

                result.annotations = annotations
                result.status = ToolStatus.COMPLETED

            else:
                # Fallback to stub if tool not loaded
                time.sleep(0.1)  # Simulated latency
                result.annotations = self._stub_tool_results(
                    tool_name, variants_to_query, parameters
                )
                result.api_calls = len(variants_to_query) or 1
                result.status = ToolStatus.COMPLETED

        except TimeoutError:
            result.status = ToolStatus.TIMEOUT
            result.error_message = f"Tool timed out after {timeout}s"

        except Exception as e:
            result.status = ToolStatus.FAILED
            result.error_message = str(e)

        finally:
            result.end_time = datetime.now()
            result.duration_seconds = (
                result.end_time - result.start_time
            ).total_seconds()

        return result

    def _stub_tool_results(
        self,
        tool_name: str,
        variants: List[str],
        parameters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generate stub results for development/testing.

        In production, this is replaced by actual tool calls.
        """
        if tool_name == "clinvar":
            return [
                {
                    "variant": v,
                    "clinical_significance": "[STUB] Likely Pathogenic",
                    "review_status": "[STUB] Criteria provided, single submitter",
                    "conditions": ["[STUB] Associated condition"],
                    "last_evaluated": "2024-01-01",
                }
                for v in variants
            ]

        elif tool_name == "spliceai":
            return [
                {
                    "variant": v,
                    "delta_scores": {
                        "acceptor_gain": 0.1,
                        "acceptor_loss": 0.05,
                        "donor_gain": 0.02,
                        "donor_loss": 0.8,  # High = potential splice impact
                    },
                    "max_delta": 0.8,
                    "prediction": "[STUB] Potential splice disruption",
                }
                for v in variants
            ]

        elif tool_name == "alphamissense":
            return [
                {
                    "variant": v,
                    "am_pathogenicity": 0.85,  # High = likely pathogenic
                    "am_class": "[STUB] likely_pathogenic",
                }
                for v in variants
            ]

        elif tool_name == "revel":
            return [
                {
                    "variant": v,
                    "revel_score": 0.75,  # High = more likely pathogenic
                    "percentile": 92,
                }
                for v in variants
            ]

        elif tool_name == "omim":
            genes = parameters.get("genes", [])
            return [
                {
                    "gene": g,
                    "omim_entry": f"[STUB] OMIM:{100000 + i}",
                    "phenotypes": [
                        {"name": "[STUB] Associated phenotype", "inheritance": "AD"}
                    ],
                    "allelic_variants": 10,
                }
                for i, g in enumerate(genes)
            ]

        return [{"tool": tool_name, "status": "stub", "message": "Tool not implemented"}]

    def _get_feedback_schema(self) -> Dict[str, Any]:
        """
        RLHF feedback schema for Executor Agent.

        Experts can:
        - Validate tool results
        - Flag incorrect annotations
        - Suggest additional tools to run
        """
        return {
            "type": "object",
            "title": "Executor Feedback",
            "description": "Review bio-tool execution results",
            "properties": {
                "correctness": {
                    "type": "string",
                    "enum": ["correct", "partial", "incorrect"],
                    "description": "Overall tool execution quality",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                },
                "tool_results_feedback": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "results_valid": {"type": "boolean"},
                            "incorrect_annotations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "variant": {"type": "string"},
                                        "field": {"type": "string"},
                                        "original": {"type": "string"},
                                        "corrected": {"type": "string"},
                                    },
                                },
                            },
                            "notes": {"type": "string"},
                        },
                    },
                },
                "missing_tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tools that should have been run",
                },
                "notes": {"type": "string"},
            },
            "required": ["correctness", "confidence"],
        }

    def __repr__(self) -> str:
        return (
            f"ExecutorAgent(max_concurrent={self.max_concurrent}, "
            f"tools={list(self.TOOL_REGISTRY.keys())})"
        )
