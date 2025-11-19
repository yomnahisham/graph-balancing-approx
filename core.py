"""
core data structures for graph balancing

implements graph and orientation classes as described in the paper
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
import networkx as nx


class Graph:
    """
    weighted multigraph representation for graph balancing
    
    represents G = (V, E, p, q) where:
    - V: vertices (machines)
    - E: edges (jobs) with weights p_e
    - q: dedicated loads q_v for each vertex v
    
    as per paper section 2.1
    """
    
    def __init__(self, vertices: List[Any], edges: List[Tuple[Any, Any]], 
                 edge_weights: Dict[int, float], 
                 dedicated_loads: Optional[Dict[Any, float]] = None):
        """
        initialize a graph
        
        args:
            vertices: list of vertex identifiers
            edges: list of (u, v) tuples representing edges (can have duplicates for multigraph)
            edge_weights: dict mapping edge index to weight p_e
            dedicated_loads: dict mapping vertex to dedicated load q_v (default: 0 for all)
        """
        self.vertices = list(vertices)
        self.edges = list(edges)  # list of (u, v) tuples, can have duplicates
        self.edge_weights = edge_weights  # dict[int, float]: edge_index -> weight
        self.dedicated_loads = dedicated_loads if dedicated_loads else {}
        
        # validate: all vertices in edges must be in vertices list
        all_edge_vertices = set()
        for u, v in self.edges:
            all_edge_vertices.add(u)
            all_edge_vertices.add(v)
        if not all_edge_vertices.issubset(set(self.vertices)):
            raise ValueError("All vertices in edges must be in vertices list")
        
        # validate: all edge indices in edge_weights must be valid
        if not all(0 <= idx < len(self.edges) for idx in self.edge_weights.keys()):
            raise ValueError("Edge indices in edge_weights must be valid")
        
        # set default dedicated loads to 0
        for v in self.vertices:
            if v not in self.dedicated_loads:
                self.dedicated_loads[v] = 0.0
    
    def get_edge_weight(self, edge_idx: int) -> float:
        """get weight p_e for edge at index edge_idx"""
        return self.edge_weights.get(edge_idx, 0.0)
    
    def get_dedicated_load(self, vertex: Any) -> float:
        """get dedicated load q_v for vertex v"""
        return self.dedicated_loads.get(vertex, 0.0)
    
    def get_incident_edges(self, vertex: Any) -> List[int]:
        """get list of edge indices incident to vertex v"""
        incident = []
        for idx, (u, v) in enumerate(self.edges):
            if u == vertex or v == vertex:
                incident.append(idx)
        return incident
    
    def __repr__(self) -> str:
        return f"Graph(vertices={len(self.vertices)}, edges={len(self.edges)})"


class Orientation:
    """
    edge orientation mapping gamma: E -> V
    
    represents an orientation of edges, where gamma(e) = v means edge e is oriented
    towards vertex v. as per paper section 2.1
    """
    
    def __init__(self, graph: Graph, mapping: Dict[int, Any]):
        """
        initialize an orientation
        
        args:
            graph: the graph being oriented
            mapping: dict mapping edge index to target vertex
        """
        self.graph = graph
        self.mapping = mapping  # dict[int, any]: edge_idx -> vertex
        
        # validate: all edges must be oriented to an incident vertex
        for edge_idx, target_vertex in self.mapping.items():
            if edge_idx < 0 or edge_idx >= len(graph.edges):
                raise ValueError(f"Invalid edge index: {edge_idx}")
            u, v = graph.edges[edge_idx]
            if target_vertex != u and target_vertex != v:
                raise ValueError(
                    f"Edge {edge_idx} oriented to {target_vertex}, "
                    f"but edge connects {u} and {v}"
                )
    
    def get_target(self, edge_idx: int) -> Any:
        """get the target vertex for edge e"""
        return self.mapping[edge_idx]
    
    def compute_load(self, vertex: Any) -> float:
        """
        compute load of vertex v: q_v + sum of p_e for edges e with gamma(e) = v
        
        as per paper section 2.1
        """
        load = self.graph.get_dedicated_load(vertex)
        for edge_idx, target_vertex in self.mapping.items():
            if target_vertex == vertex:
                load += self.graph.get_edge_weight(edge_idx)
        return load
    
    def compute_makespan(self) -> float:
        """
        compute makespan: maximum load over all vertices
        
        this is the objective we minimize
        """
        if not self.graph.vertices:
            return 0.0
        return max(self.compute_load(v) for v in self.graph.vertices)
    
    def __repr__(self) -> str:
        return f"Orientation({len(self.mapping)} edges oriented)"


# helper functions as per paper section 2.3

def get_big_edges(graph: Graph) -> Set[int]:
    """
    get set of big edges: EB = {e in E | p_e > 0.5}
    
    as per paper section 2.3
    """
    big_edges = set()
    for edge_idx in graph.edge_weights.keys():
        if graph.get_edge_weight(edge_idx) > 0.5:
            big_edges.add(edge_idx)
    return big_edges


def get_fractional_edges(graph: Graph, x: Dict[Tuple[int, Any], float], 
                         epsilon: float = 1e-9) -> Set[int]:
    """
    get set of fractionally assigned edges: Ex = {e | 0 < x_eu < 1 for some u}
    
    as per paper section 2.3
    
    args:
        graph: the graph
        x: fractional solution dict mapping (edge_idx, vertex) -> value
        epsilon: tolerance for checking if value is fractional
    """
    fractional_edges = set()
    for edge_idx, (u, v) in enumerate(graph.edges):
        x_eu = x.get((edge_idx, u), 0.0)
        x_ev = x.get((edge_idx, v), 0.0)
        # edge is fractional if neither value is 0 or 1 (within epsilon)
        if (epsilon < x_eu < 1.0 - epsilon) or (epsilon < x_ev < 1.0 - epsilon):
            fractional_edges.add(edge_idx)
    return fractional_edges


def get_components(graph: Graph, edge_subset: Optional[Set[int]] = None) -> List[Set[int]]:
    """
    get connected components of graph restricted to edge_subset
    
    if edge_subset is None, uses all edges
    
    returns list of sets of vertex indices (by position in graph.vertices)
    """
    if edge_subset is None:
        edge_subset = set(range(len(graph.edges)))
    
    # build networkx graph for component finding
    G = nx.Graph()
    G.add_nodes_from(range(len(graph.vertices)))
    
    for edge_idx in edge_subset:
        u, v = graph.edges[edge_idx]
        u_idx = graph.vertices.index(u)
        v_idx = graph.vertices.index(v)
        G.add_edge(u_idx, v_idx)
    
    # get connected components
    components = []
    for comp in nx.connected_components(G):
        # convert back to vertex objects
        vertex_set = {graph.vertices[i] for i in comp}
        components.append(vertex_set)
    
    return components


def compute_load(vertex: Any, graph: Graph, orientation: Orientation) -> float:
    """
    compute load of vertex v given orientation gamma
    
    equivalent to orientation.compute_load(vertex), but provided as helper function
    """
    return orientation.compute_load(vertex)

