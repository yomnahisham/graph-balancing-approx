"""
Tests for rounding procedures (Rotate and Round).
"""

import pytest
from core import Graph
from rounding import rotate, round_procedure


def test_rotate_simple_cycle():
    """Test Rotate on a simple 2-cycle."""
    vertices = [0, 1]
    edges = [(0, 1), (1, 0)]  # 2-cycle
    edge_weights = {0: 0.6, 1: 0.4}
    
    graph = Graph(vertices, edges, edge_weights)
    
    # Initial fractional solution
    x = {
        (0, 0): 0.3, (0, 1): 0.7,
        (1, 0): 0.8, (1, 1): 0.2
    }
    
    # Cycle: edge 0 from 0->1, edge 1 from 1->0
    cycle = [(0, (0, 1)), (1, (1, 0))]
    
    x_new = rotate(x.copy(), graph, cycle)
    
    # Check that edge constraints are preserved
    assert abs(x_new[(0, 0)] + x_new[(0, 1)] - 1.0) < 1e-6
    assert abs(x_new[(1, 0)] + x_new[(1, 1)] - 1.0) < 1e-6
    
    # Check non-negativity
    assert x_new[(0, 0)] >= -1e-9
    assert x_new[(0, 1)] >= -1e-9
    assert x_new[(1, 0)] >= -1e-9
    assert x_new[(1, 1)] >= -1e-9


def test_round_procedure_simple():
    """Test Round procedure on a simple instance."""
    vertices = [0, 1]
    edges = [(0, 1)]
    edge_weights = {0: 0.5}
    dedicated_loads = {0: 0.3, 1: 0.2}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    
    # Fractional solution
    x = {
        (0, 0): 0.4, (0, 1): 0.6
    }
    
    orientation = round_procedure(graph, x)
    
    # Should produce valid orientation
    assert 0 in orientation
    assert orientation[0] in [0, 1]  # Must be one of the endpoints


def test_round_procedure_integral():
    """Test Round on already integral solution."""
    vertices = [0, 1]
    edges = [(0, 1)]
    edge_weights = {0: 0.5}
    
    graph = Graph(vertices, edges, edge_weights)
    
    # Already integral
    x = {
        (0, 0): 0.0, (0, 1): 1.0
    }
    
    orientation = round_procedure(graph, x)
    
    assert orientation[0] == 1

