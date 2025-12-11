# ML Dependency Network Analyzer

**INFO 202: Information Organization and Retrieval — Final Project**
UC Berkeley, Fall 2025

## Project Type: Implementation

## Summary

This project applies information organization principles to analyze the Python machine learning ecosystem's dependency network. Traditional package managers show flat dependency lists, but this obscures the rich semantic relationships between packages. I built a system that collects dependency data from 100 ML repositories on GitHub, classifies 769 packages using a multi-faceted taxonomy, and visualizes the resulting network through an interactive dashboard.

The core contribution is treating dependencies as an ontology rather than a simple graph. Instead of a single "depends_on" relationship, I defined four typed edges: `requires_core` (essential runtime), `requires_optional` (feature flags), `requires_dev` (development only), and `extends` (builds upon). This mirrors how biomedical ontologies like Gene Ontology use relationship types to capture richer semantics.

Each package is classified across three orthogonal facets: domain (deep learning, NLP, data processing, etc.), role (framework, library, tool, extension), and health status (active, stable, declining). This enables faceted navigation where users can filter by any combination, such as "active deep learning frameworks."

The dashboard provides three navigation paradigms: an entity view for examining individual packages, a network view for exploring structure visually, and a path explorer for finding connections between packages. Key findings include identifying "hidden pillars," infrastructure packages like `packaging` and `typing-extensions` that have high centrality but low visibility.

## The Problem

Python's ML ecosystem is a tangled web. Transformers depends on tokenizers, huggingface-hub, and numpy. Matplotlib pulls in numpy, pillow, and fonttools. Pandas requires numpy and python-dateutil. But what's _really_ holding everything together?

Traditional package managers show you a flat list of dependencies. That's like describing a city by listing its buildings. It's technically accurate, but it's missing the roads, the neighborhoods, the hidden infrastructure that makes it all work.

This project applies information organization principles to dependency networks, treating them as complex information systems that require ontologies, faceted classification, and multiple navigation paradigms to truly understand.

## Key Findings

### The Network at a Glance

| Metric                   | Value |
| ------------------------ | ----- |
| Repositories analyzed    | 100   |
| Unique packages          | 769   |
| Dependency relationships | 1,758 |
| Relationship types       | 4     |

### The Real Pillars of ML

PageRank reveals which packages the ecosystem actually depends on, and it's not always what you'd expect:

| Package   | PageRank | Dependents | Stars |
| --------- | -------- | ---------- | ----- |
| **numpy** | 0.0067   | 56         | 31K   |
| requests  | 0.0041   | 25         | 54K   |
| pytest    | 0.0036   | 38         | 13K   |
| scipy     | 0.0033   | 32         | 14K   |
| pandas    | 0.0025   | 37         | 47K   |

numpy dominates. With 56 direct dependents and the highest PageRank, it's the foundation everything else builds on. But notice `pytest` at #3 by PageRank despite having far fewer stars than pandas. Infrastructure packages don't make headlines but appear in nearly every project.

### Hidden Pillars

Some packages punch above their weight, with high centrality but low visibility:

- **typing-extensions** (22 dependents): Backporting type hints
- **colorama** (4 dependents but high PageRank): Terminal colors, used transitively
- **pytest-cov** (20 dependents): Test coverage, everywhere in CI

These are the quiet workhorses. They don't get conference talks, but break one and watch the ecosystem crumble.

### Framework Ecosystems

The "extends" relationship reveals how ecosystems form around major frameworks:

```
pytorch ecosystem
├── torchvision (extended by ultralytics, optuna, daft)
├── torchaudio (extended by fairseq, speechbrain)
├── torch-geometric (extended by lkpy, pytorch_geometric)
└── pytorch-lightning (extended by neptune_client, pytorch_geometric)

huggingface ecosystem
├── datasets (extended by evaluate, stanza, peft, vllm)
└── accelerate (extended by peft, kornia, sktime, pytorch_geometric)

tensorflow ecosystem
├── tensorflow-cpu (extended by keras, keras_tuner)
└── torch-xla (extended by keras)
```

### Dependency Appetites

Some packages are hungry:

| Package   | Dependencies |
| --------- | ------------ |
| sktime    | 89           |
| mlflow    | 62           |
| bentoml   | 59           |
| wandb     | 54           |
| optuna    | 53           |

MLOps tools (mlflow, wandb, bentoml) and hyperparameter tuning frameworks (optuna) tend to have large dependency footprints because they integrate with everything.

### Relationship Type Distribution

| Type              | Count | %   |
| ----------------- | ----- | --- |
| requires_core     | 661   | 38% |
| requires_optional | 567   | 32% |
| requires_dev      | 502   | 29% |
| extends           | 28    | 2%  |

Nearly a third of dependencies are optional features. This matters for understanding what a package _actually_ needs versus what it _can_ use.

## How It Works

### Ontology-Based Graph Structure

Traditional dependency analysis uses a single relationship: "depends_on." This is taxonomic thinking. It tells you _that_ A depends on B, but not _how_ or _why_. Ontologies capture richer semantic relationships, similar to how biomedical ontologies like Gene Ontology use "is_a," "part_of," and "regulates" rather than generic links.

This system defines four relationship types:

| Relation            | Semantic Meaning             | Detection Method                 |
| ------------------- | ---------------------------- | -------------------------------- |
| `requires_core`     | Essential runtime dependency | In `install_requires`            |
| `requires_optional` | Feature flag dependency      | In `extras_require`              |
| `requires_dev`      | Development/testing only     | pytest, black, mypy, etc.        |
| `extends`           | Builds upon another package  | Name patterns, wrapper detection |

**`requires_core`** — These are non-negotiable dependencies. When you `pip install transformers`, you _must_ get tokenizers, numpy, and requests. The package cannot function without them. In Python packaging, these live in `install_requires` (setup.py) or `dependencies` (pyproject.toml). This is the strongest dependency signal.

**`requires_optional`** — Feature flags that unlock additional functionality. For example, `transformers[torch]` pulls in PyTorch, while `transformers[tf]` pulls in TensorFlow. The base package works without them. These appear in `extras_require` or `optional-dependencies`. They reveal which packages are designed to interoperate.

**`requires_dev`** — Dependencies only needed during development: testing (pytest, coverage), linting (black, ruff, mypy), documentation (sphinx). These never ship to end users. Detection uses a known list of dev tool packages plus heuristics around requirement file names (`requirements-dev.txt`, `[dev]` extras).

**`extends`** — The most semantically rich relationship. Package A extends package B when A is specifically designed to augment B's functionality. Examples: `keras` extends `tensorflow-cpu`, `peft` extends `accelerate`, `fairseq` extends `torchaudio`. Detection uses name pattern matching (one package name containing another) and explicit wrapper patterns. This relationship reveals ecosystem structure that flat dependency lists obscure.

### Dependency Extraction

Python packages declare dependencies in multiple file formats. The system parses each format and merges results:

| File | Format | What It Contains |
|------|--------|------------------|
| `pyproject.toml` | TOML (PEP 621 or Poetry) | `dependencies`, `optional-dependencies`, dev groups |
| `setup.py` | Python (setuptools) | `install_requires`, `extras_require`, `tests_require` |
| `requirements.txt` | Plain text (PEP 508) | Flat dependency list, often pinned versions |

The parser processes all available files and deduplicates, with earlier sources taking priority: `pyproject.toml` first (most modern and complete), then `setup.py`, then `requirements.txt`. For `setup.py`, the system uses AST parsing rather than executing the file—this is safer and avoids arbitrary code execution.

Each dependency's relationship type is inferred from where it was found:
- `dependencies` / `install_requires` → `requires_core`
- `optional-dependencies` / `extras_require` → `requires_optional` (unless the group name is `dev`, `test`, etc.)
- `setup_requires`, `tests_require`, or groups named `dev`/`test` → `requires_dev`
- `requirements.txt` → `requires_core` (unless filename contains "dev" or "test")

### Faceted Classification

Faceted classification avoids forcing packages into a single hierarchy. Instead, each package is classified across three orthogonal facets that can be combined freely.

Classification uses a hybrid approach: 55 well-known packages (torch, pandas, scikit-learn, etc.) are manually labeled, while the rest are classified through pattern matching on package names (e.g., names containing "torch" or "neural" map to deep_learning, names containing "plot" or "vis" map to visualization). Packages that don't match any pattern default to data_processing. Health status is fully automatic based on last commit date from GitHub.

**Domain** (what problem space):
- data_processing (369 packages)
- deep_learning (186)
- infrastructure (85)
- visualization (48)
- nlp (43)
- traditional_ml (23)
- computer_vision (9)
- utilities (6)

**Role** (what function):
- framework: Primary ML framework
- library: Reusable functionality
- tool: CLI or developer tool
- extension: Extends a framework

**Health** (maintenance status):
- active: Commits within 90 days
- stable: Within 1 year
- declining: Over 1 year
- unknown: Cannot determine

Facets are mutually exclusive within each dimension but combine freely across dimensions. This enables queries like "show me active deep learning frameworks" or "find declining NLP libraries."

### Information Architecture

Different users have different mental models and information needs. Someone debugging a dependency issue needs different views than someone exploring the ecosystem. Good information architecture provides multiple navigation paradigms.

I chose Streamlit for the dashboard because it handles the data-to-UI pipeline well and integrates with Python data tools. PyVis renders the network graphs because it produces interactive HTML visualizations that support zooming, panning, and node dragging without needing a JavaScript frontend.

The UI offers three views:

1. **Network View**: The main visualization. Nodes are packages, edges are dependencies. Node size reflects PageRank score (bigger = more important). Node color indicates domain (e.g., blue for deep_learning, green for data_processing). Edge color shows relationship type. Users can zoom, pan, drag nodes, and click to see details. A sidebar provides faceted filtering: checkboxes for domain, role, health status, and relationship types, plus a slider for minimum in-degree. The graph updates live as filters change.

2. **Package Explorer**: A searchable list of all packages with sorting options (by PageRank, in-degree, name, or stars). Selecting a package shows its full details: classification badges, centrality metrics, GitHub info, and lists of dependencies and dependents grouped by relationship type. Each package card also shows a mini network graph of its immediate neighborhood.

3. **Path Explorer**: Two search boxes for source and target packages. The system finds shortest paths between them and displays each step with the package's domain, role, and the edge type connecting them. Useful for answering questions like "how does peft depend on numpy?" (answer: peft → transformers → numpy).

The faceted filter sidebar appears on all views, providing consistent navigation. Filter counts update dynamically (e.g., "deep_learning (186)") so users can see how many packages match before applying a filter.

### Controlled Vocabulary

Package names are notoriously inconsistent: is it `sklearn` or `scikit-learn`? Is `cv2` the same as `opencv-python`? This is the vocabulary problem, where users and systems use different terms for the same concept. The system addresses this through PEP 503 name normalization and a controlled vocabulary mapping well-known packages to their canonical names.

### Centrality-Based Ranking

The graph structure enables computing metrics that aren't available from package metadata alone:

- **Dependents (in-degree)**: Computed by inverting the dependency graph. If A depends on B, then B has A as a dependent. This reveals which packages are most relied upon.
- **PageRank**: Identifies important packages recursively—a package is "important" if important packages depend on it. Unlike raw dependent counts, PageRank weights connections by the importance of the depending package.
- **Betweenness centrality**: Measures how often a package lies on the shortest path between other packages. High betweenness indicates a "bridge" package connecting different parts of the ecosystem.

Combined, these metrics reveal infrastructure packages that don't make headlines but are critical to the ecosystem.

## Running the Project

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Environment

```bash
export GITHUB_TOKEN=your_token_here  # Required for API access
```

### Data Collection (optional, data already collected)

```bash
python scripts/collect_data.py  # Fetches from GitHub, slow due to rate limits
python scripts/build_graph.py   # Builds graph and computes metrics
```

### Launch Dashboard

```bash
streamlit run src/ui/app.py
```

Then open http://localhost:8501

### Live Demo

The dashboard is also deployed on Streamlit Cloud: [ml-dependency-analyzer.streamlit.app](https://ml-dependency-analyzer.streamlit.app)

## Technical Architecture

```
GitHub API → Parsing → Classification → Graph → UI
     │                      │              │
     └──────── SQLite ──────┴──────────────┘
```

- **Collection**: PyGithub with rate limiting and exponential backoff
- **Parsing**: AST-based setup.py parsing (safe, no exec), tomli for pyproject.toml
- **Graph**: NetworkX MultiDiGraph for typed edges
- **Metrics**: PageRank (damping=0.85), betweenness centrality (sampled for scale)
- **UI**: Streamlit with PyVis for interactive graph visualization
- **Storage**: SQLite with indexed lookups

## Limitations and Future Work

**Current limitations:**

- Only analyzes Python packages (no conda, no system dependencies)
- Seed set biased toward popular/well-maintained repos
- Health status based solely on commit recency
- No version conflict detection

**Potential extensions:**

- Temporal analysis: How has the network evolved?
- Vulnerability propagation: If package X has a CVE, what's the blast radius?
- Ecosystem comparison: How does Python ML compare to R or Julia?
- Community detection: Are there natural clusters beyond the domain facet?

## AI Transparency Statement

This project used AI assistance (Claude) as a coding tool. Per the rubric requirements, I provide detailed documentation of what I did versus what AI contributed.

### What I Did (Original Work)

1. **Project conception and design**: The idea to apply INFO 202 concepts to dependency networks, the ontology structure (four relationship types), and the faceted classification schema were my original design decisions. I mapped course concepts like ontologies, faceted classification, and information architecture to concrete implementation choices.

2. **Ontology relationship definitions**: The four relationship types (`requires_core`, `requires_optional`, `requires_dev`, `extends`) and their detection heuristics were my design, informed by how Python packaging actually works.

3. **Classification rules**: I defined the domain/role/health classification criteria and created the mapping of well-known packages to their correct categories (`src/ontology/package_taxonomy.py:KNOWN_PACKAGES`).

4. **Seed repository validation**: After getting initial repository suggestions from AI, I manually verified each repository had parseable dependency files and ensured coverage across domains (deep learning, traditional ML, NLP, computer vision, etc.).

5. **Architecture decisions**: I chose the three-view navigation paradigm (network, entity, path) based on different user mental models for exploring information spaces.

6. **Technology stack selection**: I evaluated and selected the libraries used (NetworkX for graphs, PyVis for visualization, Streamlit for the dashboard) based on project requirements.

7. **Data pipeline design**: I designed the flow from GitHub API → parsing → classification → graph construction → metrics computation.

8. **Analysis and interpretation**: All findings in this README (hidden pillars, ecosystem structure, dependency patterns) are my analysis of the data the system produced.

9. **All writing**: The content and analysis in this README is entirely my own. AI assisted only with markdown formatting (e.g., converting my data into markdown table syntax).

### What AI Assisted With

1. **Seed repository identification**: I used Claude's Deep Research feature to identify the top 100 ML repositories to analyze, which provided a starting list that I then validated and refined.

2. **Boilerplate code**: AI helped generate repetitive patterns like SQLite CRUD operations, Streamlit page layouts, and dataclass definitions.

3. **Parsing logic**: The AST-based `setup.py` parser (`src/parsing/setup_parser.py`) was developed iteratively with AI assistance. I specified what information to extract; AI helped handle edge cases in Python's AST module.

4. **UI components**: AI helped structure the Streamlit components, particularly the PyVis graph rendering and faceted filter sidebar.

### Assessment of AI Effectiveness

**What worked well:**
- Boilerplate generation saved significant time on repetitive code
- AI was helpful for learning unfamiliar libraries (PyVis, Streamlit multipage apps)
- Debugging assistance for tricky issues (e.g., NetworkX MultiDiGraph edge iteration)

**What did not work well:**
- AI-generated classification logic initially had poor accuracy; I rewrote most of `package_taxonomy.py` manually after testing showed ~60% accuracy on known packages
- AI tended to over-engineer solutions; I frequently simplified generated code

### Code Attribution

All code was reviewed, tested, and modified. Key files and their provenance:

| File | My Contribution | AI Contribution |
|------|-----------------|-----------------|
| `src/ontology/relation_types.py` | Relationship definitions, detection rules | Initial code structure |
| `src/ontology/package_taxonomy.py` | All known package mappings, domain patterns | Dataclass boilerplate |
| `src/parsing/setup_parser.py` | Specification of what to extract | AST visitor implementation |
| `src/graph/metrics.py` | Choice of metrics, interpretation | NetworkX API calls |
| `src/ui/pages/*.py` | Layout decisions, what to display | Streamlit boilerplate |

---

_Built for INFO 202: Information Organization and Retrieval, UC Berkeley, Fall 2025_
