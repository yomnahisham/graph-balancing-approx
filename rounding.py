"""
rounding procedures for graph balancing

implements rotate (algorithm 1) and round (algorithm 2) from the paper
"""

from typing import Dict, Tuple, Optional, Any, List, Set
from core import Graph, get_big_edges, get_fractional_edges
import networkx as nx


def rotate(x: Dict[Tuple[int, Any], float], graph: Graph, cycle: List[Tuple[int, Any]]) -> Dict[Tuple[int, Any], float]:
    """
    rotate procedure (algorithm 1)
    
    takes a feasible solution x and a directed cycle C, and modifies x
    so that it is still feasible and the number of integral values increases
    
    args:
        x: fractional solution dict mapping (edge_idx, vertex) -> value
        graph: the graph
        cycle: list of (edge_idx, direction) tuples representing directed cycle
               where direction is (u, v) meaning edge goes from u to v
    
    returns:
        modified solution x
    """
    # compute delta_e = x_eu * p_e for each edge in cycle
    deltas = []
    for edge_idx, (u, v) in cycle:
        x_eu = x.get((edge_idx, u), 0.0)
        p_e = graph.get_edge_weight(edge_idx)
        delta_e = x_eu * p_e
        deltas.append((edge_idx, u, v, delta_e))
    
    # delta = min over e in C of delta_e
    if not deltas:
        return x
    
    min_delta = min(delta_e for _, _, _, delta_e in deltas)
    
    # for each edge e in C (directed u->v):
    #   x_eu := x_eu - delta/p_e
    #   x_ev := x_ev + delta/p_e
    for edge_idx, u, v, delta_e in deltas:
        p_e = graph.get_edge_weight(edge_idx)
        if p_e > 1e-9:  # Avoid division by zero
            delta = min_delta / p_e
            x[(edge_idx, u)] = max(0.0, x.get((edge_idx, u), 0.0) - delta)
            x[(edge_idx, v)] = min(1.0, x.get((edge_idx, v), 0.0) + delta)
            
            # normalize to ensure x_eu + x_ev = 1 (handle floating point)
            total = x[(edge_idx, u)] + x[(edge_idx, v)]
            if total > 1e-9:
                x[(edge_idx, u)] = x[(edge_idx, u)] / total
                x[(edge_idx, v)] = x[(edge_idx, v)] / total
            else:
                x[(edge_idx, u)] = 0.5
                x[(edge_idx, v)] = 0.5
    
    return x


def find_cycle(graph: Graph, x: Dict[Tuple[int, Any], float], 
               fractional_edges: Set[int], big_edges: Set[int]) -> Optional[List[Tuple[int, Any]]]:
    """
    find a directed cycle in G_x (findcycle step from algorithm 2)
    
    starts a walk in an arbitrary vertex, prefers big edges, continues until cycle found
    
    returns:
        list of (edge_idx, (u, v)) tuples representing directed cycle, or None if no cycle
    """
    if not fractional_edges:
        return None
    
    # build adjacency for fractional edges
    adj = {}  # vertex -> list of (edge_idx, other_vertex, is_big)
    for edge_idx in fractional_edges:
        u, v = graph.edges[edge_idx]
        is_big = edge_idx in big_edges
        if u not in adj:
            adj[u] = []
        if v not in adj:
            adj[v] = []
        adj[u].append((edge_idx, v, is_big))
        adj[v].append((edge_idx, u, is_big))
    
    if not adj:
        return None
    
    # start walk from arbitrary vertex
    start_vertex = next(iter(adj.keys()))
    visited_vertices = {}
    path = []  # list of (edge_idx, (u, v)) tuples
    
    def walk(vertex, depth=0):
        if vertex in visited_vertices:
            # found cycle! extract cycle from path
            cycle_start = visited_vertices[vertex]
            cycle_edges = path[cycle_start:]
            if len(cycle_edges) > 0:
                return cycle_edges
            return None
        
        visited_vertices[vertex] = len(path)
        
        # get incident edges, prefer big edges
        incident = adj.get(vertex, [])
        incident.sort(reverse=True, key=lambda t: (t[2], t[0]))  # big edges first
        
        for edge_idx, other_vertex, is_big in incident:
            # determine direction based on fractional values
            x_ev = x.get((edge_idx, vertex), 0.0)
            x_eother = x.get((edge_idx, other_vertex), 0.0)
            
            if x_ev > x_eother:
                direction = (vertex, other_vertex)
            else:
                direction = (other_vertex, vertex)
            
            path.append((edge_idx, direction))
            result = walk(other_vertex, depth + 1)
            if result is not None:
                return result
            path.pop()
        
        del visited_vertices[vertex]
        return None
    
    return walk(start_vertex)


def round_procedure(graph: Graph, x: Dict[Tuple[int, Any], float]) -> Dict[int, Any]:
    """
    round procedure (algorithm 2)
    
    takes a feasible solution x of LP3 and produces an integral orientation
    
    returns:
        orientation mapping: dict[edge_idx] -> vertex
    """
    epsilon = 1e-9
    x = x.copy()  # work on a copy
    
    # get big edges and fractional edges
    big_edges = get_big_edges(graph)
    
    while True:
        # get current fractional edges
        fractional_edges = get_fractional_edges(graph, x, epsilon)
        
        if not fractional_edges:
            break
        
        # build G_x: subgraph of fractionally assigned edges
        G_x_edges = fractional_edges
        
        # check for leaf pair (v, e) in G_x
        leaf_pair = None
        for edge_idx in G_x_edges:
            u, v = graph.edges[edge_idx]
            x_eu = x.get((edge_idx, u), 0.0)
            x_ev = x.get((edge_idx, v), 0.0)
            
            # check if u is a leaf (degree 1 in G_x)
            u_degree = sum(1 for e_idx in G_x_edges 
                          if u in graph.edges[e_idx])
            if u_degree == 1 and x_eu > epsilon:
                p_e = graph.get_edge_weight(edge_idx)
                if x_eu * p_e <= 0.75:
                    leaf_pair = (v, edge_idx, u)  # (leaf_vertex, edge_idx, other_vertex)
                    break
            
            # check if v is a leaf
            v_degree = sum(1 for e_idx in G_x_edges 
                          if v in graph.edges[e_idx])
            if v_degree == 1 and x_ev > epsilon:
                p_e = graph.get_edge_weight(edge_idx)
                if x_ev * p_e <= 0.75:
                    leaf_pair = (u, edge_idx, v)  # (leaf_vertex, edge_idx, other_vertex)
                    break
        
        if leaf_pair is not None:
            # leaf assignment
            leaf_vertex, edge_idx, other_vertex = leaf_pair
            x[(edge_idx, leaf_vertex)] = 1.0
            x[(edge_idx, other_vertex)] = 0.0
        else:
            # check for tree assignment case
            # find a leaf in GB_x (big fractional edges)
            big_fractional = fractional_edges & big_edges
            tree_assigned = False
            
            for edge_idx in big_fractional:
                u, v = graph.edges[edge_idx]
                x_eu = x.get((edge_idx, u), 0.0)
                x_ev = x.get((edge_idx, v), 0.0)
                
                # check if this is a leaf in GB_x
                u_big_degree = sum(1 for e_idx in big_fractional 
                                  if u in graph.edges[e_idx])
                if u_big_degree == 1:
                    p_e = graph.get_edge_weight(edge_idx)
                    if x_eu * p_e > 0.75:
                        # tree assignment: orient entire tree T
                        # find component T of GB_x containing this edge
                        T_edges = _get_component_edges(graph, big_fractional, edge_idx)
                        T_vertices = set()
                        for e_idx in T_edges:
                            u_t, v_t = graph.edges[e_idx]
                            T_vertices.add(u_t)
                            T_vertices.add(v_t)
                        
                        # find leaf v in T
                        leaf_v = None
                        for v_t in T_vertices:
                            degree = sum(1 for e_idx in T_edges if v_t in graph.edges[e_idx])
                            if degree == 1:
                                leaf_v = v_t
                                break
                        
                        if leaf_v is not None:
                            # orient all edges in T away from leaf_v
                            _orient_tree_away_from_leaf(graph, x, T_edges, leaf_v)
                            tree_assigned = True
                            break
                
                v_big_degree = sum(1 for e_idx in big_fractional 
                                  if v in graph.edges[e_idx])
                if v_big_degree == 1:
                    p_e = graph.get_edge_weight(edge_idx)
                    if x_ev * p_e > 0.75:
                        # tree assignment
                        T_edges = _get_component_edges(graph, big_fractional, edge_idx)
                        T_vertices = set()
                        for e_idx in T_edges:
                            u_t, v_t = graph.edges[e_idx]
                            T_vertices.add(u_t)
                            T_vertices.add(v_t)
                        
                        leaf_v = None
                        for v_t in T_vertices:
                            degree = sum(1 for e_idx in T_edges if v_t in graph.edges[e_idx])
                            if degree == 1:
                                leaf_v = v_t
                                break
                        
                        if leaf_v is not None:
                            _orient_tree_away_from_leaf(graph, x, T_edges, leaf_v)
                            tree_assigned = True
                            break
            
            if not tree_assigned:
                # rotation: find cycle and rotate
                cycle = find_cycle(graph, x, fractional_edges, big_edges)
                if cycle is None:
                    # no cycle found, break (shouldn't happen if graph is connected)
                    break
                x = rotate(x, graph, cycle)
    
    # extract final orientation
    orientation = {}
    for edge_idx in range(len(graph.edges)):
        u, v = graph.edges[edge_idx]
        x_eu = x.get((edge_idx, u), 0.0)
        x_ev = x.get((edge_idx, v), 0.0)
        
        # determine orientation based on which is closer to 1
        if x_eu > x_ev:
            orientation[edge_idx] = u
        else:
            orientation[edge_idx] = v
    
    return orientation


def _get_component_edges(graph: Graph, edge_set: Set[int], start_edge: int) -> Set[int]:
    """get all edges in the same connected component as start_edge"""
    component = {start_edge}
    queue = [start_edge]
    
    while queue:
        edge_idx = queue.pop(0)
        u, v = graph.edges[edge_idx]
        
        # find adjacent edges
        for other_edge in edge_set:
            if other_edge in component:
                continue
            u_other, v_other = graph.edges[other_edge]
            if u_other == u or u_other == v or v_other == u or v_other == v:
                component.add(other_edge)
                queue.append(other_edge)
    
    return component


def _orient_tree_away_from_leaf(graph: Graph, x: Dict[Tuple[int, Any], float], 
                                tree_edges: Set[int], leaf: Any):
    """orient all edges in tree away from the leaf vertex"""
    # build tree structure
    tree_graph = nx.Graph()
    for edge_idx in tree_edges:
        u, v = graph.edges[edge_idx]
        tree_graph.add_edge(u, v, key=edge_idx)
    
    # bfs from leaf to orient edges
    queue = [(leaf, None)]
    visited = {leaf}
    
    while queue:
        current, parent = queue.pop(0)
        
        for neighbor in tree_graph.neighbors(current):
            if neighbor in visited:
                continue
            
            # find edge between current and neighbor
            edge_idx = None
            for e_idx in tree_edges:
                u, v = graph.edges[e_idx]
                if (u == current and v == neighbor) or (u == neighbor and v == current):
                    edge_idx = e_idx
                    break
            
            if edge_idx is not None:
                # orient edge from current to neighbor
                x[(edge_idx, neighbor)] = 1.0
                x[(edge_idx, current)] = 0.0
                visited.add(neighbor)
                queue.append((neighbor, current))

