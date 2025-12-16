"""
JSON Extractor: Robust extraction of JSON from LLM responses.

Local GGUF models often produce JSON embedded in markdown code blocks,
wrapped in explanatory text, or with minor formatting issues.

This module provides multiple fallback strategies:
1. Direct JSON parse
2. Extract from markdown ```json blocks
3. Find JSON-like patterns with regex
4. Repair common JSON errors (trailing commas, unquoted keys)
5. Return structured error object if all else fails

Author: Stanley Lab / RareResearch
Date: November 2025
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union


class JSONExtractionError(Exception):
    """Raised when JSON extraction fails completely."""
    pass


def extract_json(
    response: str,
    expected_keys: Optional[List[str]] = None,
    default: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], float, List[str]]:
    """
    Extract JSON from an LLM response with multiple fallback strategies.

    Args:
        response: Raw LLM response text
        expected_keys: Optional list of keys to validate in extracted JSON
        default: Default dict to return if extraction fails

    Returns:
        Tuple of (extracted_dict, confidence_score, warnings)
        - confidence_score: 1.0 = perfect, 0.5 = partial, 0.1 = failed
        - warnings: List of issues encountered during extraction
    """
    warnings = []

    if not response or not response.strip():
        warnings.append("Empty response from LLM")
        return default or {}, 0.0, warnings

    # Strategy 1: Direct JSON parse (best case)
    result, confidence = _try_direct_parse(response)
    if result is not None:
        if expected_keys:
            missing = [k for k in expected_keys if k not in result]
            if missing:
                warnings.append(f"Missing expected keys: {missing}")
                confidence *= 0.8
        return result, confidence, warnings

    # Strategy 2: Extract from markdown code blocks
    result, confidence = _extract_from_code_blocks(response)
    if result is not None:
        warnings.append("JSON extracted from markdown code block")
        if expected_keys:
            missing = [k for k in expected_keys if k not in result]
            if missing:
                warnings.append(f"Missing expected keys: {missing}")
                confidence *= 0.8
        return result, confidence, warnings

    # Strategy 3: Find JSON-like patterns with regex
    result, confidence = _extract_json_pattern(response)
    if result is not None:
        warnings.append("JSON extracted via pattern matching")
        if expected_keys:
            missing = [k for k in expected_keys if k not in result]
            if missing:
                warnings.append(f"Missing expected keys: {missing}")
                confidence *= 0.8
        return result, confidence, warnings

    # Strategy 4: Try repairing common JSON errors
    result, confidence = _try_repair_json(response)
    if result is not None:
        warnings.append("JSON repaired from malformed response")
        if expected_keys:
            missing = [k for k in expected_keys if k not in result]
            if missing:
                warnings.append(f"Missing expected keys: {missing}")
                confidence *= 0.7
        return result, confidence, warnings

    # All strategies failed
    warnings.append("All JSON extraction strategies failed")
    return default or {}, 0.1, warnings


def _try_direct_parse(text: str) -> Tuple[Optional[Dict[str, Any]], float]:
    """Try to parse the text directly as JSON."""
    cleaned = text.strip()

    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result, 1.0
        elif isinstance(result, list):
            # If we got a list, wrap it
            return {"items": result}, 0.9
    except json.JSONDecodeError:
        pass

    return None, 0.0


def _extract_from_code_blocks(text: str) -> Tuple[Optional[Dict[str, Any]], float]:
    """Extract JSON from markdown code blocks."""
    # Try ```json blocks first
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```JSON\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            cleaned = match.strip()
            try:
                result = json.loads(cleaned)
                if isinstance(result, dict):
                    return result, 0.95
                elif isinstance(result, list):
                    return {"items": result}, 0.85
            except json.JSONDecodeError:
                continue

    return None, 0.0


def _extract_json_pattern(text: str) -> Tuple[Optional[Dict[str, Any]], float]:
    """Find JSON objects using brace matching."""
    # Find all potential JSON objects (starting with { ending with })
    # Track brace depth and find balanced JSON objects

    depth = 0
    start_idx = -1
    candidates = []
    in_string = False
    escape_next = False

    for i, char in enumerate(text):
        # Handle string escaping
        if escape_next:
            escape_next = False
            continue
        if char == '\\' and in_string:
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue

        # Track braces outside of strings
        if char == '{':
            if depth == 0:
                start_idx = i
            depth += 1
        elif char == '}':
            if depth > 0:  # Only decrement if we have open braces
                depth -= 1
                if depth == 0 and start_idx >= 0:
                    candidates.append((start_idx, i+1, text[start_idx:i+1]))
                    start_idx = -1

    # Try each candidate, prefer ones that start earlier (more likely to be the main JSON)
    # Sort by start position, then by length (longer is better for same start)
    candidates.sort(key=lambda x: (x[0], -x[1]))

    for start, end, candidate in candidates[:5]:  # Try top 5
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                return result, 0.85
        except json.JSONDecodeError:
            # Try removing any trailing garbage after the JSON
            # Sometimes models add extra } or text after
            try:
                # Try to find where valid JSON ends
                for trim_len in range(1, min(50, len(candidate))):
                    trimmed = candidate[:-trim_len]
                    if trimmed.endswith('}'):
                        result = json.loads(trimmed)
                        if isinstance(result, dict):
                            return result, 0.75
            except json.JSONDecodeError:
                continue

    return None, 0.0


def _try_repair_json(text: str) -> Tuple[Optional[Dict[str, Any]], float]:
    """Try to repair common JSON formatting issues."""
    # Find JSON-like content
    json_match = re.search(r'\{[\s\S]*\}', text)
    if not json_match:
        return None, 0.0

    candidate = json_match.group()

    # Common repairs:
    # 1. Remove trailing commas before } or ]
    candidate = re.sub(r',\s*([}\]])', r'\1', candidate)

    # 2. Fix unquoted keys (simple cases)
    candidate = re.sub(r'(\{|\,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', candidate)

    # 3. Replace single quotes with double quotes
    # (careful with escaped quotes inside strings)
    candidate = candidate.replace("'", '"')

    # 4. Fix missing quotes around string values
    # This is risky but sometimes helps
    candidate = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_\s]*[a-zA-Z0-9_])(\s*[,}\]])', r': "\1"\2', candidate)

    try:
        result = json.loads(candidate)
        if isinstance(result, dict):
            return result, 0.7
    except json.JSONDecodeError:
        pass

    return None, 0.0


def enforce_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    fill_defaults: bool = True,
) -> Dict[str, Any]:
    """
    Enforce a schema on extracted JSON, filling in defaults for missing fields.

    Args:
        data: Extracted JSON dict
        schema: Schema dict with {key: default_value} structure
        fill_defaults: Whether to fill missing keys with defaults

    Returns:
        Schema-compliant dict
    """
    result = dict(data)

    if fill_defaults:
        for key, default in schema.items():
            if key not in result:
                result[key] = default

    return result


# Convenience schemas for each agent type
INGESTION_SCHEMA = {
    "patient_id": "",
    "demographics": {
        "age": None,
        "sex": None,
        "ethnicity": None,
    },
    "chief_complaint": "",
    "history_present_illness": "",
    "past_medical_history": [],
    "family_history": "",
    "physical_exam": {},
    "confidence": 0.5,
    "warnings": [],
}

STRUCTURING_SCHEMA = {
    "diagnostic_table": [],
    "variants_table": [],
    "tool_usage_plan": [],
    "reasoning": {
        "phenotype_analysis": "",
        "variant_interpretation": "",
        "tool_selection_rationale": "",
    },
}

SYNTHESIS_SCHEMA = {
    "sections": {
        "executive_summary": {"title": "Executive Summary", "content": ""},
        "primary_diagnosis": {"title": "Primary Diagnosis", "content": ""},
        "differential_diagnoses": {"title": "Differential Diagnoses", "content": ""},
        "variant_analysis": {"title": "Variant Analysis", "content": ""},
        "tool_results_summary": {"title": "Bio-Tool Results Summary", "content": ""},
        "recommendations": {"title": "Recommendations", "content": ""},
        "limitations": {"title": "Limitations", "content": ""},
    },
    "confidence_score": 0.5,
}
