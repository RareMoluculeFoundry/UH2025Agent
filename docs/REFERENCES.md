# Scientific References and Reading List

**Curated Bibliography for UH2025-CDS-Agent**

---

## How to Use This Document

This bibliography provides scientific foundations for the UH2025 Agent. References are organized by topic and include brief annotations explaining relevance.

---

## Rare Disease Background

### Foundational Reviews

**Boycott KM, et al. (2013). "Rare-disease genetics in the era of next-generation sequencing: discovery, diagnosis, and treatment." *Nature Reviews Genetics* 14(10):681-691.**
- Landmark review of how NGS transformed rare disease diagnosis
- Discusses 25-50% diagnostic yield expectations
- Framework for gene discovery vs. clinical diagnosis

**Nguengang Wakap S, et al. (2020). "Estimating cumulative point prevalence of rare diseases: analysis of the Orphanet database." *European Journal of Human Genetics* 28(2):165-173.**
- Systematic analysis estimating 300 million affected globally
- 6,172 unique rare diseases analyzed
- 71.9% of rare diseases are genetic

**Ferreira CR. (2019). "The burden of rare diseases." *American Journal of Medical Genetics Part A* 179(6):885-892.**
- Documents economic and social burden
- Healthcare utilization patterns
- Quality of life impacts

### Diagnostic Odyssey

**Splinter K, et al. (2018). "Effect of genetic diagnosis on patients with previously undiagnosed disease." *New England Journal of Medicine* 379(22):2131-2139.**
- Undiagnosed Diseases Network outcomes
- 35% diagnosis rate in highly selected patients
- Documents impact of diagnosis on patient care

**Shashi V, et al. (2014). "The utility of the traditional medical genetics diagnostic evaluation in the context of next-generation sequencing for undiagnosed genetic disorders." *Genetics in Medicine* 16(2):176-182.**
- Compares traditional vs. genomic approaches
- Cost-effectiveness considerations
- When to pursue advanced testing

**Gahl WA, et al. (2016). "The NIH Undiagnosed Diseases Program and Network." *Cold Spring Harbor Molecular Case Studies* 2(4):a001180.**
- Structure and outcomes of UDN
- Collaborative diagnosis model
- Novel disease discovery

### Rare Disease Resources

**OMIM (Online Mendelian Inheritance in Man)**
- URL: https://omim.org
- Comprehensive catalog of human genes and genetic disorders
- Updated continuously with new discoveries

**Orphanet**
- URL: https://www.orpha.net
- European reference portal for rare diseases
- Clinical descriptions, prevalence data, expert centers

**NORD (National Organization for Rare Disorders)**
- URL: https://rarediseases.org
- Patient advocacy and education
- Disease-specific information

---

## Variant Interpretation

### ACMG/AMP Guidelines

**Richards S, et al. (2015). "Standards and guidelines for the interpretation of sequence variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics and the Association for Molecular Pathology." *Genetics in Medicine* 17(5):405-424.**
- Foundational variant classification framework
- The "28 criteria" for pathogenicity assessment
- Required reading for variant interpretation

**Riggs ER, et al. (2020). "Technical standards for the interpretation and reporting of constitutional copy-number variants: a joint consensus recommendation of the American College of Medical Genetics and Genomics (ACMG) and the Clinical Genome Resource (ClinGen)." *Genetics in Medicine* 22(2):245-257.**
- Extension of ACMG guidelines to CNVs
- Dosage sensitivity considerations
- Reporting standards

**Tavtigian SV, et al. (2020). "Modeling the ACMG/AMP variant classification guidelines as a Bayesian classification framework." *Genetics in Medicine* 22(9):1564-1574.**
- Quantitative framework for classification
- Mathematical basis for evidence combination
- Points-based classification system

### Pathogenicity Prediction Tools

**Cheng J, et al. (2023). "Accurate proteome-wide missense variant effect prediction with AlphaMissense." *Science* 381(6664):eadg7492.**
- DeepMind's structure-based predictor
- 71 million missense variants scored
- >90% accuracy on known pathogenic/benign variants
- **Key tool integrated in UH2025 Agent**

**Jaganathan K, et al. (2019). "Predicting splicing from primary sequence with deep learning." *Cell* 176(3):535-548.e24.**
- SpliceAI: Deep learning for splice prediction
- 95% precision at 95% recall threshold
- Identifies cryptic splice sites
- **Key tool integrated in UH2025 Agent**

**Ioannidis NM, et al. (2016). "REVEL: an ensemble method for predicting the pathogenicity of rare missense variants." *American Journal of Human Genetics* 99(4):877-885.**
- Ensemble of 13 individual scores
- Optimized for rare variant interpretation
- **Key tool integrated in UH2025 Agent**

**Rentzsch P, et al. (2019). "CADD: predicting the deleteriousness of variants throughout the human genome." *Nucleic Acids Research* 47(D1):D886-D894.**
- Combined Annotation Dependent Depletion
- Integrates diverse annotations
- Phred-scaled scores

### Population Databases

**Karczewski KJ, et al. (2020). "The mutational constraint spectrum quantified from variation in 141,456 humans." *Nature* 581(7809):434-443.**
- gnomAD v2.1 flagship paper
- Constraint metrics (pLI, LOEUF)
- Population-specific frequencies
- **Essential resource for variant filtering**

**Chen S, et al. (2024). "A genomic mutational constraint map using variation in 76,156 human genomes." *Nature* 625(7993):92-100.**
- gnomAD v4 update
- Expanded ancestry representation
- Improved constraint metrics

### Databases

**Landrum MJ, et al. (2018). "ClinVar: improving access to variant interpretations and supporting evidence." *Nucleic Acids Research* 46(D1):D1062-D1067.**
- Public archive of variant interpretations
- Star rating system explained
- Aggregation across laboratories
- **Primary source for clinical variant data**

**Amberger JS, et al. (2019). "OMIM.org: leveraging knowledge across phenotype-gene relationships." *Nucleic Acids Research* 47(D1):D1038-D1043.**
- Gene-disease relationship database
- Phenotype descriptions
- Allelic variants catalog
- **Primary source for gene-disease links**

**Köhler S, et al. (2021). "The Human Phenotype Ontology in 2021." *Nucleic Acids Research* 49(D1):D1207-D1217.**
- Standardized phenotype vocabulary
- 16,000+ phenotype terms
- Cross-references to genes and diseases
- **Used for phenotype encoding in UH2025 Agent**

---

## Clinical Decision Support

### Foundational Works

**Osheroff JA, et al. (2007). "A roadmap for national action on clinical decision support." *Journal of the American Medical Informatics Association* 14(2):141-145.**
- The "five rights" of CDS
- Implementation framework
- Success factors

**Sutton RT, et al. (2020). "An overview of clinical decision support systems: benefits, risks, and strategies for success." *NPJ Digital Medicine* 3(1):17.**
- Contemporary CDS landscape
- AI/ML integration challenges
- Implementation lessons

**Shortliffe EH, Sepúlveda MJ. (2018). "Clinical decision support in the era of artificial intelligence." *JAMA* 320(21):2199-2200.**
- AI implications for CDS
- Trust and transparency needs
- Regulatory considerations

### AI in Medicine

**Topol EJ. (2019). "High-performance medicine: the convergence of human and artificial intelligence." *Nature Medicine* 25(1):44-56.**
- Vision for AI-augmented medicine
- Capabilities and limitations
- Clinician-AI collaboration

**Rajpurkar P, et al. (2022). "AI in health and medicine." *Nature Medicine* 28(1):31-38.**
- State of the art review
- Clinical deployment challenges
- Future directions

**Yu KH, et al. (2018). "Artificial intelligence in healthcare." *Nature Biomedical Engineering* 2(10):719-731.**
- Technical foundations
- Application domains
- Implementation challenges

### LLMs in Clinical Applications

**Singhal K, et al. (2023). "Large language models encode clinical knowledge." *Nature* 620(7972):172-180.**
- Med-PaLM evaluation
- Medical question answering
- Clinical knowledge encoding

**Nori H, et al. (2023). "Capabilities of GPT-4 on medical competency examinations." *arXiv preprint arXiv:2303.13375.**
- USMLE performance analysis
- Clinical reasoning capabilities
- Limitations identified

**Lee P, et al. (2023). "Benefits, limits, and risks of GPT-4 as an AI chatbot for medicine." *New England Journal of Medicine* 388(13):1233-1239.**
- Practical clinical applications
- Safety considerations
- Appropriate use cases

### Human-in-the-Loop Design

**Cai CJ, et al. (2019). "Human-centered tools for coping with imperfect algorithms during medical decision-making." *Proceedings of CHI 2019*.**
- HITL interface design
- Trust calibration
- Error handling

**Amershi S, et al. (2019). "Guidelines for human-AI interaction." *Proceedings of CHI 2019*.**
- 18 guidelines for AI interfaces
- Applicable to clinical AI
- Design patterns

---

## Privacy and Security

### Healthcare Privacy

**McGraw D, Mandl KD. (2021). "Privacy protections to encourage use of health-relevant digital data in a learning health system." *NPJ Digital Medicine* 4(1):2.**
- Contemporary privacy challenges
- Data sharing frameworks
- Trust mechanisms

**Gostin LO, et al. (2009). "Privacy and security of personal information in a new health care system." *JAMA* 302(20):2263-2264.**
- HIPAA foundations
- Protected health information
- Security requirements

### AI-Specific Privacy

**Kaissis GA, et al. (2020). "Secure, privacy-preserving and federated machine learning in medical imaging." *Nature Machine Intelligence* 2(6):305-311.**
- Privacy-preserving ML
- Federated learning approaches
- Medical imaging applications

---

## Regulatory Guidance

### FDA Documents

**FDA. (2021). "Artificial Intelligence/Machine Learning (AI/ML)-Based Software as a Medical Device (SaMD) Action Plan."**
- Regulatory framework for AI
- Pre-certification pilot
- Real-world performance monitoring

**FDA. (2019). "Proposed Regulatory Framework for Modifications to Artificial Intelligence/Machine Learning (AI/ML)-Based Software as a Medical Device (SaMD)."**
- Update/modification handling
- Continuous learning systems
- Good Machine Learning Practice

### International Guidance

**WHO. (2021). "Ethics and governance of artificial intelligence for health."**
- Global ethical framework
- Key principles for health AI
- Governance recommendations

**European Commission. (2021). "Proposal for a Regulation laying down harmonised rules on artificial intelligence (AI Act)."**
- EU regulatory approach
- Risk categorization
- High-risk AI requirements

---

## Technical Foundations

### Genome Sequencing

**Goodwin S, et al. (2016). "Coming of age: ten years of next-generation sequencing technologies." *Nature Reviews Genetics* 17(6):333-351.**
- NGS technology overview
- Platform comparisons
- Application areas

**Shendure J, et al. (2017). "DNA sequencing at 40: past, present and future." *Nature* 550(7676):345-353.**
- Historical perspective
- Technology evolution
- Future directions

### LLM Foundations

**Vaswani A, et al. (2017). "Attention is all you need." *Advances in Neural Information Processing Systems* 30.**
- Transformer architecture
- Foundation of modern LLMs
- Attention mechanism

**Brown T, et al. (2020). "Language models are few-shot learners." *Advances in Neural Information Processing Systems* 33:1877-1901.**
- GPT-3 capabilities
- Few-shot learning
- In-context learning

**Touvron H, et al. (2023). "LLaMA: Open and efficient foundation language models." *arXiv preprint arXiv:2302.13971.**
- Open-source LLM foundation
- Efficient training and inference
- **Basis for UH2025 Agent models**

---

## Additional Resources

### Online Courses and Training

- **ClinGen**: Variant interpretation education (https://clinicalgenome.org/tools/education-and-training/)
- **ACMG/AMP Webinars**: Guideline training (https://www.acmg.net/ACMG/Medical-Genetics-Practice-Resources/Practice_Guidelines.aspx)
- **gnomAD Browser Documentation**: Tutorial and guides (https://gnomad.broadinstitute.org/help)

### Professional Organizations

- **ACMG**: American College of Medical Genetics and Genomics
- **ASHG**: American Society of Human Genetics
- **ESHG**: European Society of Human Genetics
- **AMIA**: American Medical Informatics Association

### Data Resources

| Resource | URL | Use Case |
|----------|-----|----------|
| ClinVar | https://www.ncbi.nlm.nih.gov/clinvar/ | Variant interpretations |
| gnomAD | https://gnomad.broadinstitute.org/ | Population frequencies |
| OMIM | https://omim.org/ | Gene-disease relationships |
| HPO | https://hpo.jax.org/ | Phenotype vocabulary |
| Orphanet | https://www.orpha.net/ | Rare disease information |
| UniProt | https://www.uniprot.org/ | Protein information |
| PubMed | https://pubmed.ncbi.nlm.nih.gov/ | Literature search |

---

## Citation for This System

If you use UH2025-CDS-Agent in research, please cite:

```bibtex
@software{uh2025_cds_agent_2025,
  title = {UH2025-CDS-Agent: Privacy-First Clinical Decision Support
           for Rare Disease Diagnosis},
  author = {RareResearch Consortium and Wilhelm Foundation},
  year = {2025},
  version = {2.0.0},
  note = {Inspired by the Wilhelm Foundation Undiagnosed Rare Disease
          Hackathon at Mayo Clinic, September 2025}
}
```

---

## Reference Updates

This bibliography is maintained alongside the UH2025 Agent codebase. Key references are selected for:

1. **Foundational importance**: Seminal works in the field
2. **Practical relevance**: Directly applicable to system design
3. **Currency**: Recent advances where applicable
4. **Accessibility**: Available to researchers and clinicians

For additions or corrections, please contribute through the project repository.

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Total References**: 50+
**Part of**: UH2025-CDS-Agent Documentation
