"""
Instance generators for testing Graph Balancing algorithms.
"""

import random
from typing import List, Tuple, Dict, Optional
from core import Graph


def generate_simple_instance() -> Graph:
    """Generate a simple test instance."""
    vertices = [0, 1, 2]
    edges = [(0, 1), (1, 2)]
    edge_weights = {0: 0.6, 1: 0.4}
    dedicated_loads = {0: 0.1, 1: 0.2, 2: 0.1}
    return Graph(vertices, edges, edge_weights, dedicated_loads)


def generate_random_instance(num_vertices: int = 10, num_edges: int = 15, 
                            weight_range: Tuple[float, float] = (0.1, 1.0),
                            dedicated_load_range: Tuple[float, float] = (0.0, 0.5),
                            seed: Optional[int] = None) -> Graph:
    """
    Generate a random Graph Balancing instance.
    
    Args:
        num_vertices: Number of vertices
        num_edges: Number of edges
        weight_range: (min, max) for edge weights
        dedicated_load_range: (min, max) for dedicated loads
        seed: Random seed for reproducibility
    """
    if seed is not None:
        random.seed(seed)
    
    vertices = list(range(num_vertices))
    edges = []
    edge_weights = {}
    
    # Generate edges (ensuring each edge connects two distinct vertices)
    for i in range(num_edges):
        u = random.choice(vertices)
        v = random.choice(vertices)
        # Ensure u != v (no self-loops for simplicity, though paper allows them)
        while v == u:
            v = random.choice(vertices)
        edges.append((u, v))
        edge_weights[i] = random.uniform(weight_range[0], weight_range[1])
    
    # Generate dedicated loads
    dedicated_loads = {
        v: random.uniform(dedicated_load_range[0], dedicated_load_range[1])
        for v in vertices
    }
    
    return Graph(vertices, edges, edge_weights, dedicated_loads)


def generate_long_path_instance(path_length: int = 10, epsilon: float = 0.01) -> Graph:
    """
    Generate long path instance from Section 3.3.
    
    This instance demonstrates integrality gap of 2 for LP1.
    Path with edges of weight 1-ε, endpoints with dedicated load 1.
    
    Args:
        path_length: Number of edges in the path
        epsilon: Small value for edge weights (1-ε)
    """
    vertices = list(range(path_length + 1))
    edges = []
    edge_weights = {}
    
    # Create path: 0-1-2-...-path_length
    for i in range(path_length):
        edges.append((i, i + 1))
        edge_weights[i] = 1.0 - epsilon
    
    # Dedicated loads: 1 on endpoints, 0 elsewhere
    dedicated_loads = {0: 1.0, path_length: 1.0}
    for i in range(1, path_length):
        dedicated_loads[i] = 0.0
    
    return Graph(vertices, edges, edge_weights, dedicated_loads)


def generate_three_path_instance(path_length: int = 5, epsilon: float = 0.01) -> Graph:
    """
    Generate three-path instance from Section 3.3.
    
    This instance demonstrates integrality gap of 1.75 for LP2/LP3.
    Three long disjoint paths between u and v with alternating weights (1, 0.5-ε),
    dedicated load 0.25 on all vertices.
    
    Args:
        path_length: Number of edges in each path (should be odd)
        epsilon: Small value
    """
    # Create two main vertices
    u = 0
    v = 1
    
    # Create paths
    vertices = [u, v]
    edges = []
    edge_weights = {}
    edge_idx = 0
    
    # Add three paths
    for path_num in range(3):
        # Create intermediate vertices for this path
        path_vertices = [u]
        for i in range(path_length - 1):
            path_vertices.append(len(vertices))
            vertices.append(len(vertices))
        path_vertices.append(v)
        
        # Add edges with alternating weights
        for i in range(path_length):
            edges.append((path_vertices[i], path_vertices[i + 1]))
            # Alternating: 1, 0.5-ε, 1, 0.5-ε, ...
            if i % 2 == 0:
                edge_weights[edge_idx] = 1.0
            else:
                edge_weights[edge_idx] = 0.5 - epsilon
            edge_idx += 1
    
    # Dedicated loads: 0.25 on all vertices
    dedicated_loads = {v: 0.25 for v in vertices}
    
    return Graph(vertices, edges, edge_weights, dedicated_loads)

