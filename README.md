# SDG Loop Distribution — Project 1: SCC Dependence Graph Builder

> **Component 1 of the Loop Parallelization Pipeline**
> Inspired by *"Reinforcement Learning Assisted Loop Distribution for Locality and Vectorization"* — IITH Compilers Lab, Dr. Ramakrishna Upadrasta

---

## What This Project Does

A loop program cannot always be parallelized directly. The reason is **data dependences** — when one statement reads a value written by another, the order of execution matters. This project implements the **first stage of a compiler's loop parallelization pipeline**: detecting those dependences, organizing them into a graph, and determining which parts of the loop can safely run in parallel.

The pipeline mirrors the system used in Dr. Upadrasta's lab at IIT Hyderabad, where the **SCC Dependence Graph (SDG)** is built from source code as input to an RL-based loop distribution model.

---

## The Pipeline

```
Input Loop (.txt)
       │
       ▼
  [ 1. Parser ]
  Extract statements → writes & reads with index offsets
       │
       ▼
  [ 2. RDG Builder ]
  Reduced Dependence Graph
  Nodes = statements, Edges = RAW / WAR / WAW with distance vectors
       │
       ▼
  [ 3. SCC Computation ]  ← Kosaraju's Algorithm  O(V + E)
  Find all Strongly Connected Components in the RDG
       │
       ▼
  [ 4. SDG Builder ]  ← THE CORE DELIVERABLE
  Collapse each SCC → one supernode
  Result: a DAG where each node = one group of dependent statements
       │
       ▼
  [ 5. Topological Walk ]
  Walk the SDG in topological order
  Label each node: SPLIT (parallel) or KEEP (sequential)
       │
       ▼
  [ 6. Loop Generator ]
  Emit distributed C loops
  Add  #pragma omp parallel for  where safe
       │
       ▼
  [ 7. Export ]
  Save SDG as JSON + PNG for downstream use (e.g. RL model input)
```

---

## Dependency Types Detected

| Type | Full Name | Meaning | Example |
|------|-----------|---------|---------|
| **RAW** | Read-After-Write | S1 writes X, S2 reads X — true dependence | `S1: A[i]=...` then `S2: ...=A[i]` |
| **WAR** | Write-After-Read | S1 reads X, S2 writes X — anti-dependence | `S1: ...=A[i]` then `S2: A[i]=...` |
| **WAW** | Write-After-Write | Both write to same array — output dependence | `S1: A[i]=...` and `S2: A[i]=...` |

Each edge in the RDG also carries:

- **Distance vector** `d = read_offset − write_offset`  
  e.g., `S1` writes `A[i]` (offset 0), `S2` reads `A[i-1]` (offset -1) → `d = -1`
- **Direction** `<` / `=` / `>` based on sign of d
- **loop_carried** flag — `True` when `d ≠ 0`, meaning the dependence spans iterations

---

## Project Structure

```
sdg-loop-distribution/
│
├── input/                          # Loop programs (one statement per line)
│   ├── example_loop.txt            # 4-statement loop with full cross-dependencies
│   ├── loop_parallel.txt           # 3 independent statements — fully parallelizable
│   ├── loop_carried.txt            # Loop-carried dependence (A[i] = A[i-1] + ...)
│   ├── loop_mixed.txt              # Mix: one cyclic SCC + one independent statement
│   └── loop_complex.txt            # Dense 4-statement loop (X,Y,Z,W cross-deps)
│
├── src/                            # Core pipeline modules
│   ├── parser.py                   # Parses loop text → list of {label, writes, reads}
│   ├── rdg_builder.py              # Builds RDG with RAW/WAR/WAW + distance vectors
│   ├── scc.py                      # Computes SCCs using NetworkX (Kosaraju's)
│   ├── sdg_builder.py              # Condenses RDG into SDG (DAG of SCC supernodes)
│   ├── topological_walk.py         # Topological sort → SPLIT/KEEP labels per node
│   ├── loop_generator.py           # Generates distributed C code with OpenMP pragmas
│   └── export_graph.py             # Exports SDG as JSON for RL model consumption
│
├── visualize/                      # Graph drawing modules
│   ├── draw_rdg.py                 # NetworkX plot of RDG (colored by dep type)
│   ├── draw_sdg.py                 # NetworkX plot of SDG (green=parallel, red=sequential)
│   └── draw_sdg_paper_style.py     # Graphviz paper-style layout (rectangles, LR flow)
│
├── output/
│   ├── graphs/                     # Saved PNG + JSON for every input loop
│   │   ├── *_rdg.png               # Full dependence graph visualization
│   │   ├── *_sdg.png               # SDG visualization
│   │   ├── *_sdg.json              # Machine-readable SDG (for RL model input)
│   │   └── sdg_paper.png           # Paper-style graphviz layout
│   └── loops/                      # Distributed C code output
│       ├── example_loop_distributed.c
│       ├── loop_parallel_distributed.c
│       ├── loop_carried_distributed.c
│       ├── loop_mixed_distributed.c
│       └── loop_complex_distributed.c
│
└── notebooks/
    └── SDG_Project_Setup.ipynb     # Full Colab notebook — setup to output
```

---

## Input Format

Each line is one loop statement in this form:

```
S1: A[i] = B[i] + C[i]
S2: B[i] = A[i-1] + D[i]
S3: C[i] = B[i] + E[i]
S4: D[i] = C[i-1] + A[i]
```

Rules:
- Label format: `S` followed by a number, then a colon
- Array accesses use only `i`, `i+k`, or `i-k` as subscripts (affine)
- One write per statement (LHS), multiple reads allowed (RHS)
- All loops are 1D with loop variable `i`

---

## Setup & Usage

### Requirements

```bash
pip install networkx matplotlib graphviz
apt-get install graphviz        # for paper-style visualization
```

### Run on a Single Loop

```python
from src.parser          import parse_file
from src.rdg_builder     import build_rdg
from src.scc             import compute_scc
from src.sdg_builder     import build_sdg
from src.topological_walk import topo_walk
from src.loop_generator  import generate_loops
from src.export_graph    import export_sdg_json
from visualize.draw_rdg  import draw_rdg
from visualize.draw_sdg  import draw_sdg

PROJECT_PATH = "/path/to/sdg-loop-distribution"

program = parse_file(f"{PROJECT_PATH}/input/example_loop.txt")
rdg     = build_rdg(program)
sccs    = compute_scc(rdg)
sdg     = build_sdg(rdg, sccs)
walk    = topo_walk(sdg)
code    = generate_loops(walk, PROJECT_PATH, name="example_loop")

draw_rdg(rdg, PROJECT_PATH, name="example_loop")
draw_sdg(sdg, PROJECT_PATH, name="example_loop")
export_sdg_json(sdg, f"{PROJECT_PATH}/output/graphs/example_loop_sdg.json")
```

### Run on All Test Loops

```python
import os

INPUT_FOLDER = f"{PROJECT_PATH}/input"

for filename in os.listdir(INPUT_FOLDER):
    if filename.endswith(".txt"):
        run_pipeline(filename)
```

### Google Colab

Open `notebooks/SDG_Project_Setup.ipynb`. Mount your Drive, set `PROJECT_PATH`, and run all cells top to bottom. All outputs go to `output/graphs/` and `output/loops/`.

---

## Test Cases & Results

### loop_parallel.txt — Fully Parallelizable
```
S1: A[i] = B[i] + C[i]
S2: D[i] = E[i] + F[i]
S3: G[i] = H[i] + I[i]
```
No shared arrays between any statements. Zero dependencies detected. Each statement forms its own SCC of size 1. The SDG has 3 independent nodes with no edges.

**Result:** 3 separate `#pragma omp parallel for` loops.

---

### loop_carried.txt — Loop-Carried Dependence
```
S1: A[i] = A[i-1] + B[i]
S2: B[i] = C[i] + D[i]
```
S1 reads `A[i-1]` which it wrote in the previous iteration → RAW with `d = -1`, loop-carried. S2 is independent but S1 depends on its own prior output.

**Result:** One sequential loop. Cannot be parallelized due to the self-carried RAW.

---

### loop_mixed.txt — Mixed: One Cyclic, One Independent
```
S1: A[i] = B[i] + C[i]
S2: B[i] = A[i-1] + D[i]
S3: D[i] = E[i] + F[i]
```
S1↔S2 form a cycle (S1 RAW→S2, S2 WAR→S1). S3 has no shared arrays with S1/S2 and no incoming dependencies.

**SDG:**
```
SCC1 = {S3}          → SPLIT  (parallelizable)
SCC2 = {S1, S2}      → KEEP   (cyclic, loop-carried RAW d=-1)
```

**Result:** S3 distributed into its own parallel loop. S1+S2 stay sequential.

---

### example_loop.txt — Full Cross-Dependency
```
S1: A[i] = B[i] + C[i]
S2: B[i] = A[i-1] + D[i]
S3: C[i] = B[i] + E[i]
S4: D[i] = C[i-1] + A[i]
```
S1↔S2↔S3↔S4 all share arrays with loop-carried distances. All 4 land in one SCC.

**SDG:** Single node `SCC1 = {S1, S2, S3, S4}` → KEEP.

**Result:** One sequential loop — no distribution possible without advanced transformation.

---

### loop_complex.txt — Dense 4-Statement (X/Y/Z/W)
```
S1: X[i] = Y[i] + Z[i]
S2: Y[i] = X[i-1] + W[i]
S3: Z[i] = Y[i] + V[i]
S4: W[i] = Z[i-1] + X[i]
```
Structurally identical to `example_loop.txt`. Cross-array loop-carried deps force all statements into one SCC.

**Result:** One sequential loop.

---

## SDG Node Schema (JSON Export)

Each node in the exported JSON represents one SCC supernode:

```json
{
  "nodes": [
    {
      "id": "SCC1",
      "statements": ["S1", "S2", "S3"],
      "size": 3,
      "parallelizable": false,
      "loop_carried_count": 2
    }
  ],
  "edges": [
    { "from": "SCC1", "to": "SCC2" }
  ]
}
```

| Field | Type | Meaning |
|-------|------|---------|
| `id` | string | SCC identifier (SCC1, SCC2, ...) |
| `statements` | list | Original statement labels inside this SCC |
| `size` | int | Number of statements — 1 means potentially parallel |
| `parallelizable` | bool | True when size=1 AND loop_carried_count=0 |
| `loop_carried_count` | int | Number of loop-carried edges within this SCC |

---

## Connection to Dr. Upadrasta's Research

This project implements **Component 1** of the system described in:

> *"Reinforcement Learning Assisted Loop Distribution for Locality and Vectorization"*
> S. VenkataKeerthy et al., IITH Compilers Lab, LLVM-HPC 2022

| This Project | Paper's System |
|---|---|
| RDG Builder | Reduced Dependence Graph construction |
| SCC Computation | SCC identification on RDG |
| SDG Builder | SCC Dependence Graph (the RL model's input) |
| Topological Walk | RL model's action space traversal |
| Loop Generator | Distributed loop output with OpenMP pragmas |
| JSON Export | Feature representation for RL training |

The SDG JSON output is structured to serve as direct input to an RL model that learns to predict the optimal distribution order — the exact next component in Dr. Upadrasta's pipeline.

The project also aligns with his lab's **LLOV** (LLVM OpenMP Verifier) tool, which verifies correctness of the `#pragma omp parallel for` annotations this system generates.

All input loops in this project are valid **SCoPs (Static Control Parts)** — affine array subscripts, affine loop bounds — making them compatible with **Pluto** and **Polly**, the polyhedral compilation tools central to Dr. Upadrasta's work.

---

## Limitations & Future Work

- **1D loops only** — supports single loop variable `i`. Nested loops with 2D iteration vectors `(i, j)` are not yet handled.
- **Affine subscripts only** — indirect accesses like `A[B[i]]` are not parsed.
- **No GCD / Banerjee test** — dependency test assumes any same-named array access is dependent. A GCD test would eliminate false positives (e.g., `A[2i]` vs `A[2i+1]`).
- **No control dependences** — only data dependences are detected. `if` statements inside loops are not modeled.
- **RL model not included** — this project produces the SDG input; the RL distribution model is Component 2.

---

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `networkx` | ≥ 2.8 | Graph construction, SCC computation, topological sort |
| `matplotlib` | ≥ 3.5 | RDG and SDG visualization |
| `graphviz` (Python) | ≥ 0.20 | Paper-style SDG layout |
| `graphviz` (system) | any | Required by Python graphviz package |

---

## Author

Built as **Component 1 — SDG Builder** of the Loop Parallelization System.
Targeting internship application to the **Scalable Compilers for Heterogeneous Architectures Lab**,
Dept. of Computer Science & Engineering, IIT Hyderabad.
Supervisor: **Dr. Ramakrishna Upadrasta**
Lab: [compilers.cse.iith.ac.in](https://compilers.cse.iith.ac.in)
