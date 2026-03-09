# SDG Loop Distribution — SCC Dependence Graph Construction for Loop Parallelization
> Component 2 of the Compiler Analysis Pipeline
> Inspired by *"Reinforcement Learning Assisted Loop Distribution for Locality and Vectorization"* — IITH Compilers Lab, Dr. Ramakrishna Upadrasta

---

## What It Does

Takes a pseudo-C loop body as input, detects RAW/WAW/WAR data dependences between statements, computes Strongly Connected Components (SCCs) via Kosaraju's algorithm, and builds an SCC Dependence Graph (SDG) that encodes which statement groups can be parallelized and which carry loop-carried dependences. The SDG JSON is the direct input to the RL Loop Distribution Agent (Component 3), which uses it to decide SPLIT vs KEEP per node. This replaces the hand-written heuristic that the paper's RL agent is trained to outperform.

---

## Pipeline Diagram

```
loop.txt → [Parser] → [RDG Builder] → [SCC] → [SDG Builder] → [Topo Walk] → [Loop Generator] → distributed.c
            stmts→      RAW/WAW/WAR     Kosaraju  SCC nodes +    SPLIT/KEEP    #pragma omp        + SDG JSON
            reads/writes dependence      SCCs      parallel flag  per node      parallel for        → Component 3
                         graph
```

---

## Project Structure

```
sdg-loop-distribution/
├── src/
│   ├── parser.py            # regex parse of A[i±k] expressions → reads/writes per stmt
│   ├── rdg_builder.py       # pairwise stmt comparison → RAW, WAW, WAR edges with distance+direction
│   ├── scc.py               # Kosaraju SCC decomposition → id, size, loop_carried_edges
│   ├── sdg_builder.py       # SCCs → nx.DiGraph with parallelizable flag per node
│   ├── topological_walk.py  # topological sort → SPLIT/KEEP decision per SCC
│   ├── loop_generator.py    # walk → distributed C code with #pragma omp parallel for
│   └── export_graph.py      # SDG → JSON (consumed by Component 3 RL agent)
├── visualize/
│   ├── draw_rdg.py          # RDG visualization (networkx + matplotlib)
│   ├── draw_sdg.py          # SDG visualization
│   └── draw_sdg_paper_style.py  # paper-style SDG layout
├── input/                   # 5 pseudo-C loop test cases
├── output/
│   ├── graphs/              # SDG JSON + PNG per loop (5 loops)
│   └── loops/               # distributed C output per loop (5 loops)
└── notebooks/
    └── SDG_Project_Setup.ipynb  # full Colab walkthrough
```

---

## Results

| Loop | Input Stmts | SCCs | Parallelizable | Loop-Carried Edges | Output |
|---|---|---|---|---|---|
| `loop_parallel` | 3 (no deps) | 3 | ✓ all 3 | 0 | 3 × `#pragma omp parallel for` |
| `loop_mixed` | 3 (partial deps) | 1 | ✗ | 1 | 1 sequential loop (reordered) |
| `loop_carried` | 2 (self-dep) | 1 | ✗ | 0 | 1 sequential loop |
| `loop_complex` | 4 (cross-deps) | 1 | ✗ | 3 | 1 sequential loop (reordered) |
| `example_loop` | 4 (cross-deps) | 1 | ✗ | 3 | 1 sequential loop (reordered) |

**`loop_parallel` — full distribution:**
```
Input:  S1: A[i]=B[i]+C[i]   S2: D[i]=E[i]+F[i]   S3: G[i]=H[i]+I[i]
Output: 3 independent #pragma omp parallel for loops
```

**`loop_mixed` — partial dependence, reordered:**
```
Input:  S1: A[i]=B[i]+C[i]   S2: B[i]=A[i-1]+D[i]   S3: D[i]=E[i]+F[i]
Output: 1 sequential loop with topological order S3→S1→S2
```

---

## Connection to Dr. Upadrasta's Research

| This Project | Paper's System | Your Component | Their Equivalent |
|---|---|---|---|
| Regex parse of `A[i±k]` | LLVM IR memory access analysis | `parser.py` | MemorySSA / scalar evolution |
| RAW / WAW / WAR edge detection | Data dependence analysis pass | `rdg_builder.py` | LLVM DependenceInfo |
| Kosaraju SCC on RDG | SCC decomposition for loop distribution | `scc.py` | LLVM `LoopDistribute` SCC pass |
| SDG with parallelizable flag | SCC Dependence Graph in paper | `sdg_builder.py` | SDG construction (Figure 2 in paper) |
| Topological walk → SPLIT/KEEP | Distribution order heuristic | `topological_walk.py` | Heuristic the RL agent replaces |
| SDG JSON → Component 3 | Node features for RL agent | `export_graph.py` | IR2Vec node embeddings |

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

## Limitations

- Parser handles only single-array `A[i±k]` expressions — real LLVM dependence analysis handles multi-dimensional arrays, pointer aliasing, and symbolic bounds via scalar evolution
- `parallelizable = (size==1 and loop_carried==0)` is a simplified flag — the paper computes this from actual LLVM `DependenceInfo` with direction vectors
- Topological walk uses a greedy SPLIT/KEEP heuristic — this is exactly what Component 3's RL agent is trained to replace with a learned policy
- No actual compilation or runtime measurement — output is pseudo-C; a full system feeds into LLVM's `LoopDistribute` pass and measures vectorization speedup

---

Built for internship application to the **Scalable Compilers for Heterogeneous Architectures Lab**,
Dept. of Computer Science & Engineering, IIT Hyderabad — Dr. Ramakrishna Upadrasta
[compilers.cse.iith.ac.in](https://compilers.cse.iith.ac.in)
