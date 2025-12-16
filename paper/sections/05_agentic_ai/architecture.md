# Agentic AI: The Rise of the Digital Bioinformatician

## 5.1 From Automation to Agency

Traditional bioinformatics relies on static workflows—rigid scripts that process data from step A to step Z (e.g., FASTQ → BAM → VCF). Agentic AI represents a paradigm shift. An AI agent is not just a script; it is a software system capable of perception, reasoning, and autonomous action to achieve a goal.[16] In the context of the Hackathon, an Agentic AI system is designed to mimic the "Planner-Executor" dynamic observed in human teams, automating the high-level reasoning usually performed by the senior clinician.

## 5.2 The Planner-Executor-Evaluator Architecture

Recent research in bioinformatics has formalized this into a multi-agent framework, with systems like CellAgent and BioMaster serving as prime examples.[16]

### The Planner (LLM-based)

This agent acts as the senior diagnostician. It utilizes a Large Language Model (LLM) to decompose the complex diagnostic question into a structured plan. For example, given a patient with "unexplained ataxia," the Planner might reason:

> "Step 1: Quality control the reads. Step 2: Call variants in ataxia-associated genes. Step 3: If negative, check for repeat expansions (common in ataxia). Step 4: If negative, analyze mitochondrial genome".[16]

The Planner does not write the code; it writes the strategy.

### The Executor

This specialized agent acts as the bioinformatician. It takes the step-by-step plan from the Planner and generates the specific code (Python, Bash, R) to execute it. It handles the API calls to tools like GATK or STAR, manages file paths, and executes the scripts. Crucially, if a tool fails (e.g., a memory error), the Executor can attempt to debug the code or request a new strategy.[16]

### The Evaluator

This agent acts as the quality control expert. It critiques the output of the Executor to ensure biological relevance. For instance, if the Executor returns 10,000 "pathogenic" variants, the Evaluator would flag this as biologically implausible and reject the result, prompting the Planner to refine the filtering criteria.[16]

## Table: The Planner-Executor AI Architecture

| Agent Role | Function | Analogous Human Role | Input | Output |
|:---|:---|:---|:---|:---|
| **Planner** | Decomposes complex query; Designs analysis workflow | Senior Diagnostician / Geneticist | Patient Phenotype + Clinical Question | Step-by-step Analysis Plan (The "Tool List") |
| **Executor** | Generates code; Calls APIs; Runs bioinformatic tools | Bioinformatician / Data Scientist | Analysis Plan | Raw Data / Processed Results (VCFs, Plots) |
| **Evaluator** | Inspects results for errors; Checks biological plausibility | Lab Director / Senior Reviewer | Processed Results | Quality Score + Feedback / Critique |
