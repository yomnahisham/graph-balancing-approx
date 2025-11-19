# Graph Balancing Research Framework

Implementation of the 1.75-approximation algorithm for Graph Balancing from:
Ebenlendr, Krčál, Sgall. "Graph Balancing: A Special Case of Scheduling Unrelated Parallel Machines"

## Problem

Graph Balancing: Given a weighted multigraph, orient edges to minimize the maximum vertex load, where the load of a vertex is the sum of weights of incoming edges plus its dedicated load.

## Algorithm

This implementation includes:
- LP3 linear programming formulation (Section 3.2)
- Round procedure with Rotate (Algorithms 1 & 2)
- Main LP-Balance algorithm (Algorithm 3)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from core import Graph
from algorithm import lp_balance

# Create a graph
G = Graph(vertices=[0, 1, 2], edges=[(0, 1), (1, 2)], 
          edge_weights={0: 0.6, 1: 0.4}, 
          dedicated_loads={0: 0.1, 1: 0.2, 2: 0.1})

# Find orientation
orientation = lp_balance(G)
```

## Testing

```bash
pytest tests/
```

## Project Structure

- `core.py`: Graph and Orientation data structures
- `lp_solver.py`: LP3 linear programming formulation
- `rounding.py`: Rotate and Round procedures
- `algorithm.py`: Main LP-Balance algorithm
- `tests/`: Comprehensive test suite
- `notebooks/`: Explanation and demonstration notebooks
- `docs/`: Implementation and validation reports

