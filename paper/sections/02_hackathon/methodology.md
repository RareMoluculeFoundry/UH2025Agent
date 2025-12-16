# The Undiagnosed Hackathon: A Case Study in Extreme Collaboration

## 2.1 The Genesis and Evolution of the Event

The Undiagnosed Hackathon serves as a living laboratory for the future of precision medicine. Initiated by the Wilhelm Foundation—established by Helene and Mikk Cederroth after the tragic loss of three of their children to an undiagnosed degenerative disease—the event was conceived to break the deadlock of the diagnostic odyssey.[3] Unlike traditional hackathons that focus on software development, this event is a high-intensity medical investigation, a "collaborative swarm" designed to solve the "cold cases" of medicine.

The inaugural international event took place in Stockholm, Sweden, in June 2023, hosted at the Karolinska Institutet. This pilot brought together nearly 100 experts from 28 countries to tackle 10 undiagnosed families.[11] The success of this event—resulting in four diagnoses and candidates for four others within just 48 hours—validated the model of "extreme collaboration".[11]

Building on this success, the event expanded significantly in 2024 and 2025, moving to the Mayo Clinic in Rochester, Minnesota. The 2024 event, and the subsequent 2025 iteration scheduled for September, gathered over 120 participants, including clinicians, bioinformaticians, AI specialists, and molecular biologists.[3] The sheer density of expertise—ranging from the Rare Care Centre in Australia to the NIH in the US—created a unique environment where the friction of traditional medical consultation was eliminated.

## 2.2 The "Swarm" Dynamics and the Sound of Discovery

The operational model of the Hackathon differs fundamentally from standard clinical care. In a typical hospital setting, a patient's file moves sequentially from specialist to specialist, a process that can take months. At the Hackathon, the process is parallelized. Diagnosticians from institutions like UCLA, Stanford, and Mayo work alongside tech giants like Google DeepMind, the Chan Zuckerberg Initiative (CZI), and Illumina in real-time.[3]

The atmosphere is one of intense, focused problem-solving. Participants describe a palpable energy, punctuated by the ringing of a bell—a ritual introduced to mark a breakthrough. "Each time the bell rang, scientists cheered and exchanged hugs," reported the Mayo Clinic News Network, symbolizing not just a technical success but the end of years of uncertainty for a family.[10] This "swarm intelligence" allows for rapid hypothesis generation and validation; a clinician can propose a theory, a bioinformatician can test it against the data immediately, and a geneticist can validate the biological plausibility, all within minutes.

## 2.3 Integration of Global Expertise and Technology

The participant list reads like a "Who's Who" of genomic medicine and AI. The 2024 and 2025 rosters included experts like Gareth Baynam from the Rare Care Centre in Australia, Zeynep Tumer from Copenhagen University Hospital, and teams from the Broad Institute and Radboudumc in the Netherlands.[15]

Crucially, the event also integrates the developers of the tools being used. Representatives from Illumina, Oxford Nanopore, and PacBio were present not just as sponsors but as active participants in the "tech teams," tweaking their algorithms and pipelines in real-time to meet the needs of the diagnosticians.[3] This tight feedback loop between tool users (clinicians) and tool makers (engineers) is a defining feature of the Hackathon and a key driver of its success. It represents a microcosm of the "Doctor-in-the-Loop" model, where clinical feedback directly informs technological optimization.

## 2.4 Operational Workflow

The Hackathon follows a structured methodology designed to maximize diagnostic yield within the 48-hour constraint:

### 2.4.1 Pre-Event Preparation (Weeks Before)

| Phase | Activities | Duration |
|-------|-----------|----------|
| **Case Selection** | Review submissions, assess diagnostic complexity, ensure data availability | 4-6 weeks |
| **Data Aggregation** | Collect WGS, WES, RNA-seq, methylation, clinical notes per family | 2-4 weeks |
| **Team Assignment** | Match clinician expertise to case phenotypes | 1-2 weeks |
| **Platform Setup** | Configure secure data access, analysis environments | 1 week |

### 2.4.2 Event Execution (48 Hours)

**Hour 0-4: Orientation and Case Distribution**
* Participant briefing and security protocols
* Case assignment to diagnostic teams (3-5 experts per case)
* Initial phenotype review and hypothesis formation

**Hour 4-24: Primary Analysis Cycle**
* Parallel bioinformatics pipelines execute (variant calling, SV detection, methylation analysis)
* Clinicians formulate candidate gene lists
* Tech teams provide real-time pipeline support
* Cross-team consultations for rare phenotypes

**Hour 24-44: Iterative Refinement**
* Validation of top candidates via orthogonal data (RNA-seq, long-read)
* Literature deep-dives for novel gene-disease associations
* Functional prediction using AlphaMissense, SpliceAI
* Clinical correlation with global case databases (Matchmaker Exchange)

**Hour 44-48: Synthesis and Presentation**
* Team consensus on diagnostic conclusions
* Report preparation with confidence levels
* Bell ceremony for confirmed diagnoses
* Handoff to referring clinicians

### 2.4.3 Team Structure

| Role | Count per Case | Responsibilities |
|------|----------------|------------------|
| **Lead Diagnostician** | 1 | Final diagnostic decision, clinical correlation |
| **Clinical Geneticist** | 1-2 | Phenotype analysis, inheritance patterns |
| **Bioinformatician** | 1-2 | Pipeline execution, variant prioritization |
| **Tech Liaison** | 1 | Tool integration, platform troubleshooting |
| **AI/ML Specialist** | 0-1 | Deep learning tool deployment (optional) |

## 2.5 Success Metrics

| Metric | 2023 Stockholm | 2024 Mayo | Definition |
|--------|---------------|-----------|------------|
| **Diagnostic Rate** | 40% (4/10) | ~35-40% | Confirmed molecular diagnoses |
| **Strong Candidates** | 40% (4/10) | ~30-35% | High-confidence candidates pending validation |
| **Time to Diagnosis** | <48 hours | <48 hours | From case presentation to diagnosis |
| **Novel Gene Discovery** | 1-2 | 1-2 | Previously unreported gene-disease associations |
