"""
Prompt templates for RareLLM differential diagnosis, tool calls, and reporting.
"""

import json
from typing import Dict, List, Any


def format_differential_diagnosis_prompt(
    clinical_text: str,
    clinical_features: Dict[str, Any],
    variants: List[Dict[str, Any]],
    max_diagnoses: int = 5
) -> str:
    """
    Format prompt for differential diagnosis generation.

    Args:
        clinical_text: Full clinical summary text
        clinical_features: Dict with phenotypes, onset, inheritance, triggers
        variants: List of variant dicts with gene, variant, protein_change, etc.
        max_diagnoses: Maximum number of diagnoses to return

    Returns:
        Formatted prompt string for LLM
    """
    # Build phenotype list
    phenotype_lines = []
    for p in clinical_features.get('phenotypes', []):
        phenotype_lines.append(f"- {p['label']} ({p['term']})")
    phenotype_str = "\n".join(phenotype_lines)

    # Build variant list
    variant_lines = []
    for v in variants:
        protein_change = v.get('protein_change', v.get('variant', 'unknown'))
        zygosity = v.get('zygosity', 'unknown')
        variant_lines.append(f"- {v['gene']}: {protein_change} ({zygosity})")
    variant_str = "\n".join(variant_lines)

    # Build clinical context
    onset = clinical_features.get('onset', 'unknown')
    inheritance = clinical_features.get('inheritance', 'unknown')
    triggers = clinical_features.get('triggers', [])
    triggers_str = ", ".join(triggers) if triggers else "None specified"

    prompt = f"""You are an expert medical geneticist specializing in rare genetic disorders. Your task is to generate a differential diagnosis for a patient with a suspected rare disease.

## Patient Clinical Summary
{clinical_text[:2000]}

## Phenotypic Features (HPO Terms)
{phenotype_str}

**Clinical Context:**
- Age of Onset: {onset}
- Inheritance Pattern: {inheritance}
- Triggers: {triggers_str}

## Genetic Variants Identified
{variant_str}

## Task
Generate a ranked differential diagnosis with the top {max_diagnoses} candidate rare diseases.

For each diagnosis, provide:
1. **disease**: Full disease name
2. **omim_id**: OMIM identifier (if available)
3. **confidence**: Confidence score from 0.0 to 1.0
4. **genes**: List of primary genes involved
5. **inheritance_pattern**: Mode of inheritance
6. **supporting_evidence**: List of 2-4 specific pieces of evidence supporting this diagnosis
7. **phenotype_overlap**: List of key matching phenotypes

Consider:
- Genetic evidence strength (variant pathogenicity, gene-disease associations)
- Phenotypic overlap (how many clinical features match)
- Inheritance pattern compatibility
- Disease prevalence and likelihood

**IMPORTANT**: Respond ONLY with valid JSON in this exact structure:
```json
{{
  "differential_diagnosis": [
    {{
      "disease": "Disease Name",
      "omim_id": "######",
      "confidence": 0.85,
      "genes": ["GENE1", "GENE2"],
      "inheritance_pattern": "autosomal_dominant",
      "supporting_evidence": [
        "Evidence point 1",
        "Evidence point 2"
      ],
      "phenotype_overlap": ["feature1", "feature2"]
    }}
  ],
  "reasoning_summary": "Brief explanation of diagnostic reasoning"
}}
```

Generate the differential diagnosis now:"""

    return prompt


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response, extracting JSON even if embedded in text.

    Args:
        response_text: Raw LLM output

    Returns:
        Parsed JSON dict

    Raises:
        ValueError: If JSON cannot be extracted or parsed
    """
    # Try direct JSON parsing first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from code blocks
    import re

    # Look for JSON in ```json ... ``` blocks
    json_block_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
    if json_block_match:
        try:
            return json.loads(json_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Look for JSON in ``` ... ``` blocks
    code_block_match = re.search(r'```\s*\n(.*?)\n```', response_text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Look for JSON between curly braces
    brace_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # If all else fails, raise error
    raise ValueError(f"Could not parse JSON from LLM response. Response preview: {response_text[:500]}")


def validate_differential_diagnosis(data: Dict[str, Any]) -> bool:
    """
    Validate differential diagnosis structure.

    Args:
        data: Parsed LLM response

    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required top-level keys
        if "differential_diagnosis" not in data:
            return False

        diagnoses = data["differential_diagnosis"]
        if not isinstance(diagnoses, list) or len(diagnoses) == 0:
            return False

        # Check first diagnosis has required fields
        first_diagnosis = diagnoses[0]
        required_fields = ["disease", "confidence", "genes", "supporting_evidence"]

        for field in required_fields:
            if field not in first_diagnosis:
                return False

        return True

    except Exception:
        return False
