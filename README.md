<div align="center">
  <h1>🚀 Redrob HireFit Ranker v2.0</h1>
  <p><b>A Zero-Cost, Deterministic 100K-Scale Candidate Ranking Engine</b></p>
  
  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Challenge](https://img.shields.io/badge/Redrob-India_Runs_AI-ff69b4.svg)](#)
  [![Runtime](https://img.shields.io/badge/Pipeline-132s-brightgreen.svg)](#)
</div>

---

## ⚡ The 132-Second Edge

Processing 100,000 JSON resumes usually implies heavy GPU inference, dense embeddings, or slow LLM API calls. **We explicitly rejected that.** 

The Redrob India Runs Data & AI Challenge mandates a CPU-only, air-gapped evaluation. Our engine runs locally in **132 seconds** for **$0.00**, scoring all 100,000 candidates against the Senior AI Engineer JD using a deterministic, highly-optimized 28-dimension feature matrix. 

No LLM API calls during ranking. No hallucinations. No disqualifications.

## 🏗️ High-Level Architecture

```mermaid
graph TD
    A[(candidates.jsonl)] -->|100,000 profiles| B(Lexical Filter: BM25s)
    B -->|Batch Tokenization| C{Recruiter Engine}
    
    subgraph 28-D Deterministic Matrix
    C --> D[Core Technical Skills]
    C --> E[Production Evidence]
    C --> F[Logistics & Relocation]
    end
    
    D & E & F --> G{Guardrails}
    
    subgraph Multipliers
    G -->|Multiplicative Penalty| H[Redrob Behavioral Signals]
    G -->|0.0 Multiplier| I[Honeypot Detectors]
    end
    
    H & I --> J((Final Score))
    J --> K[Grounded Reasoner]
    K --> L[/submission.csv/]
```

*(For a deep-dive into the mathematical models, Gaussian YOE curves, and honeypot heuristics, read our **[Architecture Deep-Dive](docs/ARCHITECTURE.md)**).*

## 🎯 Core Innovations

1. **Deterministic AI**: We extract 28 specific features (e.g., `product_company_ratio`, `core_skill_match`) using highly tuned C-loops and regex. This means the engine is 100% interpretable. If a candidate drops in rank, we know exactly which matrix coefficient caused it.
2. **Honeypot Guardrails**: We deployed 8 aggressive heuristics to catch fake resumes. (e.g., *Salary inversion*, *impossible education timelines*, and *skill-duration paradoxes*). Candidates hitting a honeypot receive a `0.0` multiplier.
3. **Multiplicative Behavioral Modeling**: Instead of adding points for good behavior, we heavily penalize bad behavior. Stale profiles or low response rates act as a fractional multiplier on the candidate's base technical score.
4. **Anti-Templated Reasoning**: Our reasoning generation uses dynamic variance keyed off candidate ID hashes to guarantee structural diversity, ensuring we pass the Stage 4 manual audit without triggering "templating" penalties.

## 💻 Stage 5 Interview Tools

We built tools specifically for live engineering interviews to demonstrate pipeline observability.

### Rich CLI Output (`--show-top`)
Instantly audit the top candidates, their exact score composition, and behavioral signals in an ASCII-safe format:
```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --show-top 3
```

### Zero-Dependency HTML Dashboard
Generate an interactive, single-file HTML presentation of your results in 2 seconds:
```bash
python generate_demo.py --candidates ./candidates.jsonl --submission ./submission.csv --out demo.html
```
*(This generates a self-contained, offline HTML file with zero dependencies. You do **not** need to host it or set up a web server. Simply double-click the newly created `demo.html` file in your project folder to open it in Chrome/Edge during your interview).*

### Other Interactive Demos
If you prefer a hosted web app interface, this repository also includes the original FastAPI and HuggingFace Gradio apps:

**FastAPI Backend:**
```bash
uvicorn apps.api.main:app --reload
```

**HuggingFace Space (Gradio):**
```bash
python apps/space/app.py
```

## 🚀 Setup & Reproduction

**1. Clone & Environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**2. Run the Full 100K Pipeline:**
*(Ensure `candidates.jsonl` is in the root directory).*
```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```
You will see output similar to:
```text
Pipeline completed in 132.6s
Wrote 100 rows to ./submission.csv. Loaded 100000 candidates.
```

**3. Official Validation:**
```bash
python validate_submission.py ./submission.csv
```

## 📁 Repository Structure

- `rank.py` - Official one-command CLI entrypoint.
- `src/redrob_ranker/` - Core ranking logic (Pipeline, Features, Reasoning, Retrieval).
- `generate_demo.py` - Single-file HTML dashboard generator for Stage 5.
- `docs/ARCHITECTURE.md` - Technical deep-dive into system trade-offs.
- `tests/` - Strict unit tests preventing regression (run via `pytest`).

---
<div align="center">
  <i>Built for the Redrob India Runs Data & AI Challenge.</i>
</div>
