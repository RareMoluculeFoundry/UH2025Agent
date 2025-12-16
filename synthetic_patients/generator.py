"""
Synthetic Patient Generator

Generates realistic synthetic patient cases from disease seed prompts.
These synthetic patients are used for:
- Pipeline testing without PHI exposure
- RLHF data collection in the Diagnostic Arena
- Algorithm benchmarking with known ground truth

NO REAL PATIENT DATA IS USED.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import random
import hashlib
import yaml


class ComplexityLevel(Enum):
    """Diagnostic complexity level for synthetic cases."""
    STRAIGHTFORWARD = "straightforward"  # Clear phenotype-genotype match
    MODERATE = "moderate"  # Some ambiguity, multiple candidates
    CHALLENGING = "challenging"  # Red herrings, phenocopies, compound het
    EXPERT = "expert"  # Rare presentation, novel variants


@dataclass
class DiseaseSeed:
    """
    Seed configuration for synthetic patient generation.

    Contains the disease category, example conditions, relevant genes,
    and phenotypic features to guide generation.
    """
    disease_category: str
    example_conditions: List[str]
    genes_of_interest: List[str]
    phenotype_features: List[str]
    inheritance_patterns: List[str] = field(default_factory=list)

    # Generation hints
    typical_age_range: tuple = (0, 80)
    sex_bias: Optional[str] = None  # "male", "female", or None
    complexity_distribution: Dict[str, float] = field(default_factory=dict)

    # Ground truth for evaluation
    canonical_variants: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "DiseaseSeed":
        """Load disease seed from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "disease_category": self.disease_category,
            "example_conditions": self.example_conditions,
            "genes_of_interest": self.genes_of_interest,
            "phenotype_features": self.phenotype_features,
            "inheritance_patterns": self.inheritance_patterns,
        }


@dataclass
class SyntheticPatient:
    """
    A generated synthetic patient case.

    Contains clinical summary, genomic data, and ground truth labels.
    """
    patient_id: str
    generated_at: datetime

    # Clinical data
    clinical_summary: str
    demographics: Dict[str, Any]

    # Genomic data
    variants: List[Dict[str, Any]]

    # Ground truth (for evaluation)
    ground_truth_diagnosis: str
    ground_truth_genes: List[str]
    ground_truth_variants: List[str]
    complexity_level: ComplexityLevel

    # Generation metadata
    disease_seed: str
    generation_prompt: str
    red_herrings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "generated_at": self.generated_at.isoformat(),
            "clinical_summary": self.clinical_summary,
            "demographics": self.demographics,
            "variants": self.variants,
            "ground_truth": {
                "diagnosis": self.ground_truth_diagnosis,
                "genes": self.ground_truth_genes,
                "variants": self.ground_truth_variants,
                "complexity": self.complexity_level.value,
            },
            "metadata": {
                "disease_seed": self.disease_seed,
                "red_herrings": self.red_herrings,
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def save(self, output_dir: str) -> str:
        """Save synthetic patient to file."""
        path = Path(output_dir) / f"{self.patient_id}.json"
        with open(path, "w") as f:
            f.write(self.to_json())
        return str(path)


class SyntheticPatientGenerator:
    """
    Generate synthetic patient cases for the Diagnostic Arena.

    Uses disease seed prompts to generate realistic clinical summaries
    and genomic data via LLM, with known ground truth for evaluation.

    Example usage:
    ```python
    generator = SyntheticPatientGenerator()
    seed = generator.load_seed("ion_channelopathy")
    patient = generator.generate(seed, complexity=ComplexityLevel.MODERATE)
    print(patient.clinical_summary)
    ```
    """

    def __init__(
        self,
        model_name: str = "qwen2.5-14b-instruct",
        seed_directory: Optional[str] = None,
    ):
        """
        Initialize generator.

        Args:
            model_name: LLM to use for generation
            seed_directory: Path to disease seed YAML files
        """
        self.model_name = model_name
        self.seed_directory = seed_directory or str(
            Path(__file__).parent / "prompts" / "rare_disease_seeds"
        )
        self._seeds_cache: Dict[str, DiseaseSeed] = {}

    def load_seed(self, seed_name: str) -> DiseaseSeed:
        """
        Load a disease seed by name.

        Args:
            seed_name: Name of the seed (e.g., "ion_channelopathy")

        Returns:
            DiseaseSeed configuration
        """
        if seed_name in self._seeds_cache:
            return self._seeds_cache[seed_name]

        yaml_path = Path(self.seed_directory) / f"{seed_name}.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"Disease seed not found: {yaml_path}")

        seed = DiseaseSeed.from_yaml(str(yaml_path))
        self._seeds_cache[seed_name] = seed
        return seed

    def list_seeds(self) -> List[str]:
        """List available disease seeds."""
        seed_dir = Path(self.seed_directory)
        if not seed_dir.exists():
            return []
        return [f.stem for f in seed_dir.glob("*.yaml")]

    def generate(
        self,
        seed: DiseaseSeed,
        complexity: ComplexityLevel = ComplexityLevel.MODERATE,
        target_diagnosis: Optional[str] = None,
    ) -> SyntheticPatient:
        """
        Generate a synthetic patient from a disease seed.

        Args:
            seed: Disease seed configuration
            complexity: Desired diagnostic complexity
            target_diagnosis: Specific diagnosis to simulate (optional)

        Returns:
            Generated SyntheticPatient
        """
        # Generate patient ID
        patient_id = self._generate_patient_id(seed)

        # Select target diagnosis if not specified
        if target_diagnosis is None:
            target_diagnosis = random.choice(seed.example_conditions)

        # Generate demographics
        demographics = self._generate_demographics(seed)

        # Build generation prompt
        generation_prompt = self._build_generation_prompt(
            seed, target_diagnosis, demographics, complexity
        )

        # Generate clinical summary via LLM
        # TODO: Connect to actual LLM backend
        clinical_summary = self._stub_generate_summary(
            seed, target_diagnosis, demographics, complexity
        )

        # Generate synthetic variants
        variants = self._generate_variants(seed, target_diagnosis, complexity)

        # Add red herrings for higher complexity
        red_herrings = []
        if complexity in [ComplexityLevel.CHALLENGING, ComplexityLevel.EXPERT]:
            red_herrings = self._generate_red_herrings(seed)

        return SyntheticPatient(
            patient_id=patient_id,
            generated_at=datetime.now(),
            clinical_summary=clinical_summary,
            demographics=demographics,
            variants=variants,
            ground_truth_diagnosis=target_diagnosis,
            ground_truth_genes=seed.genes_of_interest[:2],
            ground_truth_variants=[v["variant_id"] for v in variants if v.get("causal")],
            complexity_level=complexity,
            disease_seed=seed.disease_category,
            generation_prompt=generation_prompt,
            red_herrings=red_herrings,
        )

    def generate_batch(
        self,
        seed: DiseaseSeed,
        count: int = 10,
        complexity_distribution: Optional[Dict[ComplexityLevel, float]] = None,
    ) -> List[SyntheticPatient]:
        """
        Generate a batch of synthetic patients.

        Args:
            seed: Disease seed configuration
            count: Number of patients to generate
            complexity_distribution: Distribution of complexity levels

        Returns:
            List of generated patients
        """
        if complexity_distribution is None:
            complexity_distribution = {
                ComplexityLevel.STRAIGHTFORWARD: 0.3,
                ComplexityLevel.MODERATE: 0.4,
                ComplexityLevel.CHALLENGING: 0.2,
                ComplexityLevel.EXPERT: 0.1,
            }

        patients = []
        for _ in range(count):
            # Sample complexity level
            complexity = random.choices(
                list(complexity_distribution.keys()),
                weights=list(complexity_distribution.values()),
            )[0]

            patient = self.generate(seed, complexity)
            patients.append(patient)

        return patients

    def _generate_patient_id(self, seed: DiseaseSeed) -> str:
        """Generate unique patient ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        category_hash = hashlib.md5(seed.disease_category.encode()).hexdigest()[:4]
        random_suffix = random.randint(1000, 9999)
        return f"SYNTH-{category_hash.upper()}-{timestamp}-{random_suffix}"

    def _generate_demographics(self, seed: DiseaseSeed) -> Dict[str, Any]:
        """Generate synthetic demographics."""
        age = random.randint(*seed.typical_age_range)

        if seed.sex_bias:
            sex = seed.sex_bias if random.random() > 0.3 else (
                "male" if seed.sex_bias == "female" else "female"
            )
        else:
            sex = random.choice(["male", "female"])

        ethnicities = [
            "European", "African", "East Asian", "South Asian",
            "Hispanic/Latino", "Middle Eastern", "Mixed",
        ]

        return {
            "age": age,
            "sex": sex,
            "ethnicity": random.choice(ethnicities),
        }

    def _build_generation_prompt(
        self,
        seed: DiseaseSeed,
        target_diagnosis: str,
        demographics: Dict[str, Any],
        complexity: ComplexityLevel,
    ) -> str:
        """Build the prompt for clinical summary generation."""
        complexity_instructions = {
            ComplexityLevel.STRAIGHTFORWARD: (
                "Create a straightforward case with classic presentation. "
                "The diagnosis should be relatively obvious to an expert."
            ),
            ComplexityLevel.MODERATE: (
                "Create a case with some diagnostic ambiguity. "
                "Include 2-3 possible diagnoses but make the correct one identifiable."
            ),
            ComplexityLevel.CHALLENGING: (
                "Create a challenging case with atypical features. "
                "Include red herrings and consider phenocopies."
            ),
            ComplexityLevel.EXPERT: (
                "Create an expert-level case. Consider rare presentations, "
                "variable expressivity, or novel variants. Make it genuinely difficult."
            ),
        }

        return f"""Generate a realistic clinical summary for a synthetic patient.

DISEASE CATEGORY: {seed.disease_category}
TARGET DIAGNOSIS: {target_diagnosis}
COMPLEXITY: {complexity.value}

PATIENT DEMOGRAPHICS:
- Age: {demographics['age']} years
- Sex: {demographics['sex']}
- Ethnicity: {demographics['ethnicity']}

GENES TO CONSIDER: {', '.join(seed.genes_of_interest)}
PHENOTYPE FEATURES TO INCLUDE: {', '.join(seed.phenotype_features)}
INHERITANCE PATTERNS: {', '.join(seed.inheritance_patterns)}

INSTRUCTIONS:
{complexity_instructions[complexity]}

Generate a clinical summary that includes:
1. Chief complaint and history of present illness
2. Relevant past medical history
3. Family history (consistent with inheritance pattern)
4. Physical examination findings
5. Any prior test results

The summary should be realistic enough to test a diagnostic AI system.
Do NOT explicitly state the diagnosis - let it be inferred from the presentation.
"""

    def _stub_generate_summary(
        self,
        seed: DiseaseSeed,
        target_diagnosis: str,
        demographics: Dict[str, Any],
        complexity: ComplexityLevel,
    ) -> str:
        """
        Stub clinical summary generation.

        In production, this would call the LLM.
        """
        age = demographics["age"]
        sex = demographics["sex"]
        pronoun = "she" if sex == "female" else "he"
        possessive = "her" if sex == "female" else "his"

        phenotypes = random.sample(
            seed.phenotype_features,
            min(3, len(seed.phenotype_features))
        )

        return f"""[SYNTHETIC PATIENT - STUB GENERATION]

CLINICAL SUMMARY

Demographics: {age}-year-old {sex}

Chief Complaint:
{phenotypes[0].capitalize()} for the past {random.randint(1, 24)} months.

History of Present Illness:
The patient presents with a {random.randint(1, 24)}-month history of {phenotypes[0]}.
{pronoun.capitalize()} reports {', '.join(phenotypes[1:]) if len(phenotypes) > 1 else 'associated symptoms'}.
Symptoms are {random.choice(['progressive', 'episodic', 'stable'])}.
{random.choice(['Triggered by', 'Worsened by', 'Associated with'])} {random.choice(['cold exposure', 'exercise', 'stress', 'fasting'])}.

Past Medical History:
- Otherwise healthy
- No prior hospitalizations
- No surgeries

Family History:
{random.choice(['Father', 'Mother', 'Paternal grandmother', 'Maternal uncle'])} with similar symptoms (suggests {seed.inheritance_patterns[0] if seed.inheritance_patterns else 'unknown'} inheritance).

Physical Examination:
- General: Alert, oriented, no acute distress
- Relevant findings: {phenotypes[0]}
- Neurological: [STUB - requires LLM generation]
- Musculoskeletal: [STUB - requires LLM generation]

Prior Testing:
- Basic metabolic panel: [STUB]
- EMG: [STUB - if applicable]

GROUND TRUTH: {target_diagnosis}
COMPLEXITY: {complexity.value}

[This is a STUB. Real generation requires LLM backend connection.]
"""

    def _generate_variants(
        self,
        seed: DiseaseSeed,
        target_diagnosis: str,
        complexity: ComplexityLevel,
    ) -> List[Dict[str, Any]]:
        """Generate synthetic variants based on disease seed."""
        variants = []

        # Add causal variant(s)
        if seed.canonical_variants:
            causal = random.choice(seed.canonical_variants)
            causal["causal"] = True
            variants.append(causal)
        else:
            # Generate stub causal variant
            gene = random.choice(seed.genes_of_interest)
            variants.append({
                "gene": gene,
                "chromosome": str(random.randint(1, 22)),
                "position": random.randint(1000000, 100000000),
                "reference": random.choice(["A", "C", "G", "T"]),
                "alternate": random.choice(["A", "C", "G", "T"]),
                "variant_id": f"SYNTH_{gene}_{random.randint(1000, 9999)}",
                "protein_change": f"p.{random.choice(['Arg', 'Gly', 'Ala'])}{random.randint(100, 500)}{random.choice(['Gln', 'His', 'Pro'])}",
                "zygosity": "heterozygous",
                "causal": True,
            })

        # Add benign variants (noise)
        num_benign = random.randint(5, 15)
        for _ in range(num_benign):
            variants.append({
                "gene": f"GENE{random.randint(1, 1000)}",
                "chromosome": str(random.randint(1, 22)),
                "position": random.randint(1000000, 100000000),
                "reference": random.choice(["A", "C", "G", "T"]),
                "alternate": random.choice(["A", "C", "G", "T"]),
                "variant_id": f"rs{random.randint(100000, 999999)}",
                "zygosity": random.choice(["heterozygous", "homozygous"]),
                "causal": False,
            })

        return variants

    def _generate_red_herrings(self, seed: DiseaseSeed) -> List[str]:
        """Generate red herring features for complex cases."""
        red_herrings = [
            "Incidental finding on imaging",
            "Lab abnormality unrelated to primary condition",
            "Medication side effect mimicking symptoms",
            "Comorbid condition with overlapping features",
            "VUS in unrelated gene",
        ]
        return random.sample(red_herrings, min(2, len(red_herrings)))
