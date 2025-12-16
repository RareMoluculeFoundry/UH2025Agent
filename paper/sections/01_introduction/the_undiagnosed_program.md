# The Undiagnosed Program: Mission, Origin, and Crisis

## 1.1 The Cederroth Story: Where This Began

In Sweden, Helene and Mikk Cederroth lost three of their four children—Wilhelm, Hugo, and Emma—to an undiagnosed degenerative genetic disease. For years, the family traveled across Europe, consulting specialists at university hospitals, undergoing countless tests, and waiting—always waiting—for answers that never came.

They watched their children decline without knowing why. Without a name for what was happening. Without knowing if it could be prevented in future generations. Without hope of treatment.

> "The worst part wasn't the disease—it was the not knowing. Every doctor had a different theory. Every test came back inconclusive. We spent years in a medical maze, and our children paid the price."
> — Helene Cederroth

From this profound tragedy emerged the **Wilhelm Foundation**, named in memory of their children. Their mission is singular and urgent: **to ensure no family endures what they did.**

The Cederroths' story is not an outlier—it is emblematic of the experience shared by approximately **350 million people worldwide** affected by rare diseases. If this population were a single nation, it would be the third-largest country on Earth, trailing only China and India.

## 1.2 The Diagnostic Odyssey: The Scale of the Crisis

The medical system is designed for common diseases with clear diagnostic pathways. Rare diseases fall through the cracks—not because the knowledge doesn't exist, but because it's siloed, fragmented, and inaccessible.

**The Numbers:**
- **7,000–10,000** unique rare conditions identified
- **350 million** people affected worldwide
- **80%** of rare diseases have genetic origins
- **50%** of cases affect children

**The "Diagnostic Odyssey":**

Patients with undiagnosed rare diseases face a harrowing journey:

| Metric | Reality |
|--------|---------|
| Average time to diagnosis | **6+ years** |
| Specialists consulted before diagnosis | **7+ on average** |
| Children who die before age 5 without diagnosis | **30%** |
| Patients remaining undiagnosed after WES | **60%** |

Each statistic represents families like the Cederroths—years of uncertainty, false leads, and accumulating medical debt without answers.

**The "Labeling vs. Root Cause" Problem:**

Patients accumulate diagnostic codes without receiving true diagnoses. A child may be labeled with "developmental delay," "hypotonia," and "failure to thrive"—descriptions of symptoms, not explanations of cause. Doctors label what they see because they cannot identify what they don't understand.

## 1.3 The Economic Toll

The financial burden of the diagnostic odyssey is staggering:

**Per-Patient Costs:**
- Healthcare costs **7.6x higher** than general population
- €26,999/year vs. €3,561/year for typical patients
- **49x higher** genetic testing volume

**US Healthcare System:**
- Direct annual cost: **$966 billion**
- 30% spent on repeated testing
- 40% on hospitalizations (often unnecessary due to misdiagnosis)
- 20% on lost productivity

**What These Costs Represent:**
- Families driven into bankruptcy seeking answers
- Hospital beds occupied by patients who could be treated if diagnosed
- Insurance systems bearing preventable costs
- Economic productivity lost to caregiver burden

A diagnosis doesn't just end uncertainty—it **stops the financial hemorrhaging**. Project Baby Bear demonstrated that rapid genomic diagnosis saves $2.5M in avoided hospitalizations and unnecessary procedures per cohort of critically ill infants.

## 1.4 The Siloed Data Problem

A critical structural barrier compounds the medical challenge: genomic and phenotypic data resides in institutional silos—locked within hospitals, research centers, and private laboratories. This fragmentation is reinforced by valid privacy concerns and regulations (GDPR in Europe, HIPAA in the United States).

**The "n=2" Problem:**

Medical knowledge advances through pattern recognition. A clinician in Stockholm may identify a novel variant in a patient with a unique phenotype. Without access to global data, they cannot know that a clinician in San Diego has seen the exact same variant-phenotype correlation. The second case would confirm causality—but the cases never connect.

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE FRAGMENTATION PROBLEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Hospital A (Stockholm)           Hospital B (San Diego)        │
│   ┌─────────────────────┐         ┌─────────────────────┐       │
│   │ Patient with        │         │ Patient with        │       │
│   │ SCN4A:c.1234+5G>A   │    ?    │ SCN4A:c.1234+5G>A   │       │
│   │ + periodic paralysis │◄──?──►│ + periodic paralysis │       │
│   │                     │         │                     │       │
│   │ "Variant of Unknown │         │ "Novel finding,     │       │
│   │  Significance"      │         │  needs confirmation"│       │
│   └─────────────────────┘         └─────────────────────┘       │
│                                                                  │
│   Each case alone = uncertain                                    │
│   Both cases together = CONFIRMED CAUSALITY                      │
│                                                                  │
│   But they never connect.                                        │
└─────────────────────────────────────────────────────────────────┘
```

**Why the Silos Exist:**
- Patient privacy laws (legitimate)
- Institutional competition (problematic)
- Technical incompatibility (solvable)
- Lack of incentive structures (addressable)

The data to solve most undiagnosed cases exists somewhere in the world. The challenge is connecting it without compromising patient privacy.

## 1.5 The Mission: Beyond Individual Diagnosis

The Wilhelm Foundation's mission goes beyond diagnosing individual patients. It seeks to **transform the diagnostic paradigm itself** by demonstrating that the collective intelligence of global experts, working in parallel with the latest technologies, can solve cases that sequential, siloed medicine cannot.

**The Core Insight:**

> What if we could bring the world's best diagnosticians into the same room—not for one family, but for every family?

This question led to the creation of the **Undiagnosed Hackathon**: a 48-hour intensive where 100+ experts from 28 countries converge to tackle the hardest diagnostic cases.

## 1.6 The Hackathon as Answer: A Preview

The Undiagnosed Hackathon is the Wilhelm Foundation's empirical proof-of-concept. In Stockholm 2023:

- **10 families** with years of unsuccessful diagnostic workups
- **100+ experts** from 28 countries
- **48 hours** of parallel, coordinated analysis
- **Result: 4 diagnoses, 4 strong candidates** (80% actionable outcomes)

Cases that had stumped specialists for years were solved in hours. The hackathon didn't just help families—it **revealed a replicable pattern** for how diagnosis actually works when the barriers are removed.

**The Three Discoveries:**
1. **The workflow** that experts actually use (Planner-Executor dynamics)
2. **The technologies** that crack cases (multi-omics, not just WES)
3. **The feedback loop** that refines tools in real-time (human RLHF)

Section 2 details these discoveries. Sections 3-7 describe how we automate and scale them.

---

## 1.7 What Follows

The remainder of this paper traces the path from hackathon observation to scalable system:

| Section | Content | From Hackathon |
|---------|---------|----------------|
| **Section 2** | The Hackathon as Discovery Engine | The six principles we extracted |
| **Section 3** | The Diagnostic Workflow | Planner-Executor pattern |
| **Section 4** | Multi-Omics in Practice | Technologies that actually work |
| **Section 5** | Agentic AI Architecture | Digital replication of swarm dynamics |
| **Section 6** | The Federated Network | Scaling to every clinic, every day |
| **Section 7** | Reinforcement Learning | Formalizing the expert feedback |
| **Section 8** | Validation & Proof | Hackathon + external evidence |
| **Section 9** | Ethical Guardrails | Human oversight by design |
| **Section 10** | From Event to Network | The vision realized |

---

**The diagnostic odyssey ends when the hackathon effect reaches every clinic, every day.**

This is the mission. This paper describes the architecture.
