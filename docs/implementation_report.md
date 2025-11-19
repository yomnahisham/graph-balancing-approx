# Implementation Report: Graph Balancing 1.75-Approximation Algorithm

## Overview

This report documents the implementation of the 1.75-approximation algorithm for Graph Balancing from the paper:
"Graph Balancing: A Special Case of Scheduling Unrelated Parallel Machines" by Ebenlendr, Krčál, and Sgall.

## File Structure

```
core.py          - graph and orientation data structures
lp_solver.py     - LP3 linear programming formulation
rounding.py      - rotate and round procedures
algorithm.py     - main LP-balance algorithm
generators.py    - instance generators for testing
tests/           - comprehensive test suite
```

## Implementation Mapping to Paper

### Core Data Structures (core.py)

**Graph Class** (Paper Section 2.1)
- Represents G = (V, E, p, q) where:
  - V: vertices (machines)
  - E: edges (jobs) with weights p_e
  - q: dedicated loads q_v for each vertex v
- Implementation: `Graph` class with vertices, edges, edge_weights, dedicated_loads

**Orientation Class** (Paper Section 2.1)
- Represents edge orientation mapping gamma: E -> V
- Implementation: `Orientation` class with mapping from edge indices to target vertices
- `compute_load(v)`: computes q_v + sum of p_e for edges e with gamma(e) = v
- `compute_makespan()`: returns maximum load over all vertices

**Helper Functions** (Paper Section 2.3)
- `get_big_edges(G)`: returns EB = {e in E | p_e > 0.5}
- `get_fractional_edges(G, x)`: returns Ex = {e | 0 < x_eu < 1 for some u}
- `get_components(G, edge_subset)`: returns connected components

### Linear Programming Solver (lp_solver.py)

**LP3 Formulation** (Paper Section 3.2)

Variables: x_ev for each edge e and vertex v in e

Constraints:
1. Edge constraints: x_eu + x_ev = 1 for each edge e={u,v}
   - Implementation: lines 42-45 in lp_solver.py

2. Load constraints: q_v + sum of x_ev * p_e over edges e with v in e <= 1 for each v
   - Implementation: lines 47-58 in lp_solver.py

3. Star constraints: sum of x_ev over big edges e in EB with v in e <= 1 for each v
   - Implementation: lines 60-70 in lp_solver.py
   - Big edges: EB = {e | p_e > 0.5}

**Solver Implementation**
- Uses cvxpy with fallback to available solvers (CLARABEL, OSQP, SCIPY, SCS)
- Handles numerical issues by clamping values to [0, 1] and normalizing
- Returns None if infeasible

### Rounding Procedures (rounding.py)

**Rotate Procedure** (Paper Algorithm 1)

Input: fractional solution x, directed cycle C

Steps:
1. Compute delta_e = x_eu * p_e for each edge in cycle
2. delta = min over e in C of delta_e
3. For each edge e in C (directed u->v):
   - x_eu := x_eu - delta/p_e
   - x_ev := x_ev + delta/p_e

Implementation: `rotate()` function (lines 12-61)
- Preserves edge constraints (x_eu + x_ev = 1)
- Maintains non-negativity
- At least one variable becomes 0 (integral)

**Round Procedure** (Paper Algorithm 2)

Input: graph G, fractional solution x of LP3
Output: integral orientation mapping

Main loop while G_x has edges:
1. If leaf pair (v, e) exists in G_x:
   - If x_eu * p_e <= 0.75: **Leaf Assignment**
     - Set x_ev = 1, x_eu = 0
   - Else: **Tree Assignment**
     - Find tree T in GB_x containing e
     - Orient all edges in T away from leaf v
2. Else: **Rotation**
   - Find cycle C (preferring big edges)
   - Call Rotate(x, C)

Implementation: `round_procedure()` function (lines 134-275)
- Maintains invariants from Theorem 3.1:
  - (a) Load of v <= 1.75
  - (b) If v incident to edge in G_x, load <= 1.25
  - (c) If v incident to big edge in G_x, load <= 1.0
  - (d) Tree constraints preserved

**FindCycle** (Part of Algorithm 2)
- Starts walk from arbitrary vertex
- Prefers big edges when choosing next edge
- Continues until cycle found
- Implementation: `find_cycle()` function (lines 64-131)

### Main Algorithm (algorithm.py)

**LP-Balance Algorithm** (Paper Algorithm 3)

Steps:
1. Find feasible solution x of LP3
2. If no solution exists, return None (FAIL)
3. Call Round(G, x) to get orientation
4. Return orientation

Implementation: `lp_balance()` function (lines 13-41)

**Decision Version (GBapx)**
- Tests if orientation with makespan <= 1.75 exists
- Returns ("SUCCESS", orientation) or ("FAIL", None)
- Implementation: `graph_balancing_approx()` function (lines 44-63)

**Optimization Version**
- Uses binary search on makespan value
- Scales instance and calls decision version
- Implementation: `graph_balancing_optimize()` function (lines 66-117)

## Key Design Decisions

1. **LP Solver Fallback**: Instead of requiring ECOS, we try multiple available solvers (CLARABEL, OSQP, SCIPY, SCS) for better compatibility.

2. **Numerical Stability**: All floating-point comparisons use epsilon tolerance (1e-9). Values are clamped to [0, 1] and normalized to ensure constraints are satisfied.

3. **Graph Representation**: Uses simple lists and dictionaries rather than complex graph libraries for core operations, with NetworkX only for component finding.

4. **Error Handling**: LP solver returns None for infeasible instances rather than raising exceptions, allowing graceful handling.

## Deviations from Paper

1. **Cycle Finding**: The paper's FindCycle procedure is simplified - we use a DFS walk that prefers big edges, which achieves the same goal.

2. **Tree Assignment**: The tree orientation logic uses BFS from the leaf, which is equivalent to the paper's description but more straightforward to implement.

3. **Preprocessing**: The paper mentions preprocessing to ensure GB is a disjoint union of trees and cycles, but LP3 guarantees this structure, so we skip explicit preprocessing.

## Testing

All components are tested:
- Core data structures: 8 tests
- LP solver: 4 tests
- Rounding procedures: 3 tests
- Main algorithm: 3 tests
- Paper examples: 3 tests
- Reproducibility: 3 tests

Total: 24 tests, all passing.

## Verification

The implementation maintains all invariants from Theorem 3.1:
- Maximum load is at most 1.75
- Load constraints are preserved during rounding
- Tree constraints are maintained
- Output is always a valid orientation

