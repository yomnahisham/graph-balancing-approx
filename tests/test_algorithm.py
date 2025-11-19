"""
Integration tests for the main algorithm.
"""

import pytest
from core import Graph, Orientation
from algorithm import lp_balance, graph_balancing_approx
from generators import generate_simple_instance


def test_lp_balance_simple():
    """Test LP-Balance on a simple instance."""
    graph = generate_simple_instance()
    orientation = lp_balance(graph)
    
    assert orientation is not None
    assert isinstance(orientation, Orientation)
    
    # Check makespan is reasonable
    makespan = orientation.compute_makespan()
    assert makespan > 0
    assert makespan <= 1.75 + 1e-6  # Should satisfy approximation guarantee


def test_lp_balance_feasible():
    """Test that algorithm produces valid orientation."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.4, 1: 0.3}
    dedicated_loads = {0: 0.1, 1: 0.2, 2: 0.1}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    orientation = lp_balance(graph)
    
    assert orientation is not None
    
    # Check all edges are oriented
    assert len(orientation.mapping) == len(graph.edges)
    
    # Check each edge is oriented to an incident vertex
    for edge_idx, target in orientation.mapping.items():
        u, v = graph.edges[edge_idx]
        assert target == u or target == v


def test_graph_balancing_approx():
    """Test decision version."""
    graph = generate_simple_instance()
    status, orientation = graph_balancing_approx(graph)
    
    assert status in ["SUCCESS", "FAIL"]
    if status == "SUCCESS":
        assert orientation is not None
        makespan = orientation.compute_makespan()
        assert makespan <= 1.75 + 1e-6

