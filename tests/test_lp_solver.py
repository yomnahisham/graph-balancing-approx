"""
Tests for LP3 solver.
"""

import pytest
from core import Graph
from lp_solver import solve_lp3


def test_lp3_feasible_simple():
    """Test LP3 on a simple feasible instance."""
    vertices = [0, 1]
    edges = [(0, 1)]
    edge_weights = {0: 0.5}
    dedicated_loads = {0: 0.3, 1: 0.2}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    x = solve_lp3(graph)
    
    assert x is not None
    
    # Check edge constraint: x_0u + x_0v = 1
    total = x[(0, 0)] + x[(0, 1)]
    assert abs(total - 1.0) < 1e-6
    
    # Check load constraints
    load_0 = 0.3 + x[(0, 0)] * 0.5
    load_1 = 0.2 + x[(0, 1)] * 0.5
    assert load_0 <= 1.0 + 1e-6
    assert load_1 <= 1.0 + 1e-6


def test_lp3_infeasible():
    """Test LP3 on an infeasible instance."""
    # Create a truly infeasible instance: both vertices need the edge
    # but edge weight is too large
    vertices = [0, 1]
    edges = [(0, 1)]
    edge_weights = {0: 1.5}  # Edge weight > 1
    dedicated_loads = {0: 0.6, 1: 0.6}  # Both have dedicated load
    
    # This is infeasible because:
    # - If edge goes to vertex 0: load = 0.6 + 1.5 = 2.1 > 1.0
    # - If edge goes to vertex 1: load = 0.6 + 1.5 = 2.1 > 1.0
    # - Fractional: at best we can get load = 0.6 + 0.5*1.5 = 1.35 > 1.0
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    x = solve_lp3(graph)
    
    # Should be infeasible
    assert x is None


def test_lp3_star_constraints():
    """Test that star constraints are enforced for big edges."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (0, 2)]
    edge_weights = {0: 0.6, 1: 0.6}  # Both are big edges (> 0.5)
    dedicated_loads = {0: 0.0, 1: 0.0, 2: 0.0}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    x = solve_lp3(graph)
    
    if x is not None:
        # Star constraint: x_0u + x_1u <= 1 for vertex 0
        star_sum = x[(0, 0)] + x[(1, 0)]
        assert star_sum <= 1.0 + 1e-6


def test_lp3_edge_constraints():
    """Test that edge constraints are satisfied."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.4, 1: 0.3}
    dedicated_loads = {0: 0.1, 1: 0.2, 2: 0.1}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    x = solve_lp3(graph)
    
    assert x is not None
    
    # Check each edge constraint
    for edge_idx, (u, v) in enumerate(graph.edges):
        total = x[(edge_idx, u)] + x[(edge_idx, v)]
        assert abs(total - 1.0) < 1e-6

