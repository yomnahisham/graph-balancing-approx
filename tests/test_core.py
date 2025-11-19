"""
Unit tests for core data structures.
"""

import pytest
from core import Graph, Orientation, get_big_edges, get_fractional_edges


def test_graph_creation():
    """Test basic graph creation."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.6, 1: 0.4}
    dedicated_loads = {0: 0.1, 1: 0.2, 2: 0.1}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    
    assert len(graph.vertices) == 3
    assert len(graph.edges) == 2
    assert graph.get_edge_weight(0) == 0.6
    assert graph.get_dedicated_load(0) == 0.1
    assert graph.get_dedicated_load(2) == 0.1


def test_graph_default_dedicated_loads():
    """Test that default dedicated loads are 0."""
    vertices = [0, 1]
    edges = [(0, 1)]
    edge_weights = {0: 0.5}
    
    graph = Graph(vertices, edges, edge_weights)
    
    assert graph.get_dedicated_load(0) == 0.0
    assert graph.get_dedicated_load(1) == 0.0


def test_graph_incident_edges():
    """Test getting incident edges."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2), (0, 2)]
    edge_weights = {0: 0.3, 1: 0.4, 2: 0.5}
    
    graph = Graph(vertices, edges, edge_weights)
    
    incident = graph.get_incident_edges(1)
    assert len(incident) == 2
    assert 0 in incident
    assert 1 in incident


def test_orientation_creation():
    """Test orientation creation."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.6, 1: 0.4}
    
    graph = Graph(vertices, edges, edge_weights)
    mapping = {0: 1, 1: 2}  # Edge 0 -> vertex 1, Edge 1 -> vertex 2
    
    orientation = Orientation(graph, mapping)
    
    assert orientation.get_target(0) == 1
    assert orientation.get_target(1) == 2


def test_orientation_load():
    """Test computing vertex load."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.6, 1: 0.4}
    dedicated_loads = {0: 0.1, 1: 0.2, 2: 0.1}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    mapping = {0: 1, 1: 2}  # Edge 0 -> vertex 1, Edge 1 -> vertex 2
    
    orientation = Orientation(graph, mapping)
    
    # Vertex 0: only dedicated load (0.1)
    assert abs(orientation.compute_load(0) - 0.1) < 1e-9
    
    # Vertex 1: dedicated load (0.2) + edge 0 (0.6) = 0.8
    assert abs(orientation.compute_load(1) - 0.8) < 1e-9
    
    # Vertex 2: dedicated load (0.1) + edge 1 (0.4) = 0.5
    assert abs(orientation.compute_load(2) - 0.5) < 1e-9


def test_orientation_makespan():
    """Test computing makespan."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.6, 1: 0.4}
    dedicated_loads = {0: 0.1, 1: 0.2, 2: 0.1}
    
    graph = Graph(vertices, edges, edge_weights, dedicated_loads)
    mapping = {0: 1, 1: 2}
    
    orientation = Orientation(graph, mapping)
    
    makespan = orientation.compute_makespan()
    assert abs(makespan - 0.8) < 1e-9  # Max load is 0.8 at vertex 1


def test_get_big_edges():
    """Test identifying big edges (p_e > 0.5)."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2), (0, 2)]
    edge_weights = {0: 0.3, 1: 0.6, 2: 0.5}  # Only edge 1 is big
    
    graph = Graph(vertices, edges, edge_weights)
    big_edges = get_big_edges(graph)
    
    assert big_edges == {1}


def test_get_fractional_edges():
    """Test identifying fractional edges."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.6, 1: 0.4}
    
    graph = Graph(vertices, edges, edge_weights)
    
    # All edges fractional
    x = {
        (0, 0): 0.3, (0, 1): 0.7,
        (1, 1): 0.5, (1, 2): 0.5
    }
    fractional = get_fractional_edges(graph, x)
    assert fractional == {0, 1}
    
    # Edge 0 integral, edge 1 fractional
    x = {
        (0, 0): 0.0, (0, 1): 1.0,
        (1, 1): 0.5, (1, 2): 0.5
    }
    fractional = get_fractional_edges(graph, x)
    assert fractional == {1}
    
    # All edges integral
    x = {
        (0, 0): 0.0, (0, 1): 1.0,
        (1, 1): 0.0, (1, 2): 1.0
    }
    fractional = get_fractional_edges(graph, x)
    assert fractional == set()

