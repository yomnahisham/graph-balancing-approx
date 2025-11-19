"""
Reproducibility tests - verify deterministic results.
"""

import pytest
from core import Graph
from algorithm import lp_balance
from generators import generate_random_instance


def test_deterministic_results():
    """Test that algorithm produces deterministic results."""
    # use a known feasible instance instead of random
    from core import Graph
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.4, 1: 0.3}
    dedicated_loads = {0: 0.1, 1: 0.2, 2: 0.1}
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    
    # Run multiple times
    results = []
    for _ in range(5):
        orientation = lp_balance(graph)
        assert orientation is not None, "Instance should be feasible"
        makespan = orientation.compute_makespan()
        results.append(makespan)
    
    # All results should be the same (within floating point tolerance)
    assert len(results) == 5, "Should have 5 results"
    for i in range(1, len(results)):
        assert abs(results[0] - results[i]) < 1e-6, f"Results should be deterministic: {results[0]} vs {results[i]}"


def test_deterministic_orientation():
    """Test that orientation mapping is deterministic."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.4, 1: 0.3}
    dedicated_loads = {0: 0.1, 1: 0.2, 2: 0.1}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    
    # Run multiple times
    orientations = []
    for _ in range(3):
        orientation = lp_balance(graph)
        if orientation is not None:
            orientations.append(orientation.mapping)
    
    # All orientations should be the same
    if len(orientations) > 1:
        for i in range(1, len(orientations)):
            assert orientations[0] == orientations[i]


def test_numerical_stability():
    """Test numerical stability on edge cases."""
    # Very small weights - should still work
    vertices = [0, 1]
    edges = [(0, 1)]
    edge_weights = {0: 1e-6}
    dedicated_loads = {0: 0.0, 1: 0.0}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    orientation = lp_balance(graph)
    
    # Should handle small weights without crashing and produce valid result
    assert orientation is not None, "Should handle small weights"
    makespan = orientation.compute_makespan()
    assert makespan <= 1.75 + 1e-6, f"Makespan {makespan} should be <= 1.75"
    
    # Very large dedicated loads (but still feasible)
    vertices = [0, 1]
    edges = [(0, 1)]
    edge_weights = {0: 0.1}
    dedicated_loads = {0: 0.9, 1: 0.0}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    orientation = lp_balance(graph)
    
    # This should be feasible (edge goes to vertex 1: load = 0.0 + 0.1 = 0.1 <= 1.0)
    assert orientation is not None, "Should be feasible"
    makespan = orientation.compute_makespan()
    assert makespan <= 1.75 + 1e-6, f"Makespan {makespan} should be <= 1.75"

