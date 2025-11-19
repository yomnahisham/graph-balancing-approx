"""
main algorithm for graph balancing

implements LP-balance algorithm (algorithm 3) from the paper
"""

from typing import Optional, Tuple
from core import Graph, Orientation
from lp_solver import solve_lp3
from rounding import round_procedure


def lp_balance(graph: Graph) -> Optional[Orientation]:
    """
    LP-balance algorithm (algorithm 3)
    
    main 1.75-approximation algorithm for graph balancing
    
    steps:
    1. find feasible solution x of LP3
    2. if no solution exists, return None (FAIL)
    3. call round(G, x) to get orientation
    4. return orientation
    
    returns:
        orientation if feasible, None if infeasible
    """
    # step 1: solve LP3
    x = solve_lp3(graph)
    
    if x is None:
        # step 2: infeasible
        return None
    
    # step 3: round the solution
    orientation_mapping = round_procedure(graph, x)
    
    # step 4: create orientation object
    orientation = Orientation(graph, orientation_mapping)
    
    return orientation


def graph_balancing_approx(graph: Graph) -> Tuple[str, Optional[Orientation]]:
    """
    decision version (GBapx) of graph balancing
    
    returns:
        ("SUCCESS", orientation) if orientation with makespan <= 1.75 exists
        ("FAIL", None) if no such orientation exists
    """
    orientation = lp_balance(graph)
    
    if orientation is None:
        return ("FAIL", None)
    
    # check if makespan is within 1.75 (should always be true by algorithm design)
    makespan = orientation.compute_makespan()
    if makespan > 1.75 + 1e-6:  # small epsilon for floating point
        # this shouldn't happen if algorithm is correct
        return ("FAIL", None)
    
    return ("SUCCESS", orientation)


def graph_balancing_optimize(graph: Graph, tolerance: float = 1e-6) -> Optional[Orientation]:
    """
    optimization version: find orientation minimizing makespan
    
    uses binary search on the makespan value, scaling the instance
    
    args:
        graph: input graph
        tolerance: tolerance for binary search
    
    returns:
        orientation with approximately minimal makespan, or None if infeasible
    """
    # first, check if there's any feasible solution
    test_orientation = lp_balance(graph)
    if test_orientation is None:
        return None
    
    # get initial bounds
    # lower bound: maximum dedicated load or maximum edge weight
    lower_bound = max(
        max(graph.get_dedicated_load(v) for v in graph.vertices),
        max(graph.get_edge_weight(e) for e in graph.edge_weights.keys()) if graph.edge_weights else 0
    )
    
    # upper bound: sum of all loads (trivial solution)
    upper_bound = (
        sum(graph.get_dedicated_load(v) for v in graph.vertices) +
        sum(graph.get_edge_weight(e) for e in graph.edge_weights.keys())
    )
    
    # binary search
    best_orientation = None
    while upper_bound - lower_bound > tolerance:
        mid = (lower_bound + upper_bound) / 2
        
        # scale graph: divide all weights and dedicated loads by mid
        scaled_graph = _scale_graph(graph, 1.0 / mid)
        
        # test if scaled instance has solution with makespan <= 1
        scaled_orientation = lp_balance(scaled_graph)
        
        if scaled_orientation is not None:
            # feasible: can achieve makespan <= mid
            upper_bound = mid
            # unscale the orientation
            best_orientation = _unscale_orientation(scaled_orientation, graph, mid)
        else:
            # infeasible: need makespan > mid
            lower_bound = mid
    
    return best_orientation


def _scale_graph(graph: Graph, scale_factor: float) -> Graph:
    """scale all edge weights and dedicated loads by scale_factor"""
    scaled_edge_weights = {
        idx: weight * scale_factor
        for idx, weight in graph.edge_weights.items()
    }
    scaled_dedicated_loads = {
        v: load * scale_factor
        for v, load in graph.dedicated_loads.items()
    }
    
    return Graph(
        vertices=graph.vertices,
        edges=graph.edges,
        edge_weights=scaled_edge_weights,
        dedicated_loads=scaled_dedicated_loads
    )


def _unscale_orientation(scaled_orientation: Orientation, original_graph: Graph, 
                         scale_factor: float) -> Orientation:
    """create orientation for original graph from scaled orientation"""
    # the orientation mapping is the same (just edge indices)
    return Orientation(original_graph, scaled_orientation.mapping)

