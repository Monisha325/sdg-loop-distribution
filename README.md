# SDG Loop Distribution — SCC Dependence Graph Construction for Loop Parallelization
> Component 2 of the Compiler Analysis Pipeline  
> Inspired by *"Reinforcement Learning Assisted Loop Distribution for Locality and Vectorization"* — IITH Compilers Lab, Dr. Ramakrishna Upadrasta

---

## What I Built

A full loop distribution pipeline that takes a pseudo-C loop body, detects all data dependences between statements, decomposes them into Strongly Connected Components via Kosaraju's algorithm, builds an SCC Dependence Graph (SDG), and emits either parallelized `#pragma omp parallel for` loops or reordered sequential loops — depending on what the dependence structure allows.

The SDG JSON produced here is the direct input to the RL Loop Distribution Agent (Component 3), which uses it to learn a SPLIT/KEEP policy per node. The topological walk in this component is exactly the hand-written heuristic that the RL agent is trained to replace.

---

## Pipeline Diagram

```
loop.txt
    │
    ▼
[Parser]           regex parse of A[i±k] expressions → reads/writes per statement
    │
    ▼
[RDG Builder]      pairwise stmt comparison → RAW / WAW / WAR edges
                   each edge carries: array, distance, direction (<, =, >), loop_carried flag
    │
    ▼
[SCC — Kosaraju]   strongly connected components → id, size, loop_carried_edges per SCC
    │
    ▼
[SDG Builder]      SCCs → nx.DiGraph nodes with parallelizable flag
                   parallelizable = (size == 1 and loop_carried_count == 0)
    │
    ▼
[Topological Walk] topological sort → SPLIT if parallelizable, KEEP otherwise
    │
    ▼
[Loop Generator]   walk → distributed C code with #pragma omp parallel for
[Export Graph]     SDG → JSON consumed by Component 3 RL agent
```

---

## Project Structure

```
sdg-loop-distribution/
├── src/
│   ├── parser.py               # regex parse of A[i±k] → reads/writes per statement
│   ├── rdg_builder.py          # pairwise RAW/WAW/WAR detection with distance + direction
│   ├── scc.py                  # Kosaraju SCC → id, size, loop_carried_edges
│   ├── sdg_builder.py          # SCCs → nx.DiGraph with parallelizable flag per node
│   ├── topological_walk.py     # topological sort → SPLIT/KEEP decision per SCC
│   ├── loop_generator.py       # walk → distributed C code with #pragma omp parallel for
│   └── export_graph.py         # SDG → JSON (consumed by Component 3 RL agent)
├── visualize/
│   ├── draw_rdg.py             # RDG visualization (networkx + matplotlib)
│   ├── draw_sdg.py             # SDG visualization
│   └── draw_sdg_paper_style.py # paper-style SDG layout
├── input/                      # 5 pseudo-C loop test cases
├── output/
│   ├── graphs/                 # SDG JSON + PNG per loop
│   └── loops/                  # distributed C output per loop
└── notebooks/
    └── SDG_Project_Setup.ipynb # full Colab walkthrough
```

---

## How Each Component Works

### Parser — `parser.py`

`parse_index()` uses the regex `([A-Za-z]+)\[i([+-]\d+)?\]` to extract the array name and integer offset from expressions like `A[i-1]`. `parse_statement()` splits each line on `:` and `=` to isolate the LHS write and all RHS reads. Each statement becomes a dict of `{label, writes: [(array, offset)], reads: [(array, offset)]}`.

### RDG Builder — `rdg_builder.py`

`build_rdg()` performs pairwise comparison across all statement pairs to detect three dependence types. A **RAW** (Read After Write) edge from S1→S2 is added when S1 writes array A and S2 reads array A. A **WAW** (Write After Write) edge is added when both statements write the same array. A **WAR** (Write After Read) edge is added when S1 reads array A and S2 writes it. Every edge carries the distance (`r_offset - w_offset`), direction (`<`, `=`, `>`), and a `loop_carried` boolean that is `True` when the distance is non-zero — meaning the dependence crosses loop iterations.

### SCC Decomposition — `scc.py`

`compute_scc()` calls `nx.strongly_connected_components()` (NetworkX's implementation of Kosaraju's algorithm) on the RDG. For each component it counts how many edges within the SCC are loop-carried. A single-statement SCC with no loop-carried edges is parallelizable; a multi-statement SCC or one with carried edges forms a cyclic dependence that must stay sequential.

### SDG Builder — `sdg_builder.py`

`build_sdg()` lifts the SCC list into a higher-level DiGraph. Each SCC becomes a node carrying its statement list, size, `parallelizable` flag, and `loop_carried_count`. Cross-SCC edges from the original RDG become edges in the SDG, preserving the dependence ordering between groups.

### Topological Walk & Code Generation — `topological_walk.py`, `loop_generator.py`

`topo_walk()` sorts the SDG topologically and assigns each node a SPLIT or KEEP action based on the `parallelizable` flag. `generate_loops()` converts this walk into C code — SPLIT nodes become `#pragma omp parallel for` loops, KEEP nodes become plain sequential loops. The reordering in `loop_mixed` (S3→S1→S2 instead of S1→S2→S3) comes directly from the topological sort respecting dependence edges.

### Export — `export_graph.py`

`export_sdg_json()` serializes the SDG to JSON with each node's `id`, `statements`, `size`, `parallelizable`, and `loop_carried_count`. This is the exact schema consumed by `LoopDistributionEnv` in Component 3.

---

## Results

| Loop | Input Stmts | SCCs | Parallelizable | Loop-Carried Edges | Output |
|---|---|---|---|---|---|
| `loop_parallel` | 3 (no deps) | 3 | ✓ all 3 | 0 | 3 × `#pragma omp parallel for` |
| `loop_mixed` | 3 (partial deps) | 1 | ✗ | 1 | 1 sequential loop (reordered S3→S1→S2) |
| `loop_carried` | 2 (self-dep) | 1 | ✗ | 0 | 1 sequential loop |
| `loop_complex` | 4 (cross-deps) | 1 | ✗ | 3 | 1 sequential loop (reordered) |
| `example_loop` | 4 (cross-deps) | 1 | ✗ | 3 | 1 sequential loop (reordered) |

**`loop_parallel` — full distribution:**
```c
// Input:  S1: A[i]=B[i]+C[i]   S2: D[i]=E[i]+F[i]   S3: G[i]=H[i]+I[i]
// No shared arrays → 3 independent SCCs → all parallelized

#pragma omp parallel for
for(int i=0;i<N;i++){ S1; }

#pragma omp parallel for
for(int i=0;i<N;i++){ S2; }

#pragma omp parallel for
for(int i=0;i<N;i++){ S3; }
```

**`loop_mixed` — RAW dependence forces reorder:**
```c
// Input:  S1: A[i]=B[i]+C[i]   S2: B[i]=A[i-1]+D[i]   S3: D[i]=E[i]+F[i]
// S2 reads A[i-1] written by S1 → loop-carried RAW → single cyclic SCC
// Topological sort resolves ordering: S3 → S1 → S2

for(int i=0;i<N;i++){ S3; S1; S2; }
```

---

## Connection to Dr. Upadrasta's Research

| This Project | Paper's System |
|---|---|
| Regex parse of `A[i±k]` (`parser.py`) | LLVM MemorySSA / scalar evolution for array access analysis |
| RAW / WAW / WAR edge detection (`rdg_builder.py`) | LLVM `DependenceInfo` pass with direction vectors |
| Kosaraju SCC on RDG (`scc.py`) | LLVM `LoopDistribute` SCC decomposition |
| SDG with parallelizable flag (`sdg_builder.py`) | SCC Dependence Graph — Figure 2 in the paper |
| Topological walk → SPLIT/KEEP (`topological_walk.py`) | Hand-written heuristic the RL agent is trained to replace |
| SDG JSON → Component 3 (`export_graph.py`) | Node feature input to the RL environment |

---

## How to Run

```bash
pip install networkx matplotlib

python -c "
from src.parser import parse_file
from src.rdg_builder import build_rdg
from src.scc import compute_scc
from src.sdg_builder import build_sdg
from src.export_graph import export_sdg_json
from src.topological_walk import topo_walk
from src.loop_generator import generate_loops

program = parse_file('input/loop_parallel.txt')
rdg = build_rdg(program)
sccs = compute_scc(rdg)
sdg = build_sdg(rdg, sccs)
export_sdg_json(sdg, 'output/graphs/loop_parallel_sdg.json')
generate_loops(topo_walk(sdg), '.', 'loop_parallel')
"
```

---


