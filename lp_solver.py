"""
linear programming solver for graph balancing

implements LP3 formulation from section 3.2 of the paper
"""

from typing import Dict, Tuple, Optional, Any
import cvxpy as cp
import numpy as np
from core import Graph


def solve_lp3(graph: Graph) -> Optional[Dict[Tuple[int, Any], float]]:
    """
    solve LP3 linear program for graph balancing
    
    LP3 formulation (section 3.2):
    - variables: x_ev for each edge e and vertex v in e
    - edge constraints: x_eu + x_ev = 1 for each edge e={u,v}
    - load constraints: q_v + sum of x_ev * p_e over edges e with v in e <= 1 for each v
    - star constraints: sum of x_ev over big edges e in EB with v in e <= 1 for each v (where EB = big edges)
    
    returns:
        dictionary mapping (edge_idx, vertex) -> value, or None if infeasible
    """
    # get big edges: EB = {e | p_e > 0.5}
    big_edges = set()
    for edge_idx in graph.edge_weights.keys():
        if graph.get_edge_weight(edge_idx) > 0.5:
            big_edges.add(edge_idx)
    
    # create variables: x_ev for each edge e and vertex v incident to e
    variables = {}
    for edge_idx, (u, v) in enumerate(graph.edges):
        variables[(edge_idx, u)] = cp.Variable(nonneg=True)
        variables[(edge_idx, v)] = cp.Variable(nonneg=True)
    
    # build constraints
    constraints = []
    
    # edge constraints: x_eu + x_ev = 1 for each edge e={u,v}
    for edge_idx, (u, v) in enumerate(graph.edges):
        constraints.append(
            variables[(edge_idx, u)] + variables[(edge_idx, v)] == 1
        )
    
    # load constraints: q_v + sum of x_ev * p_e over edges e with v in e <= 1 for each vertex v
    for vertex in graph.vertices:
        load_expr = graph.get_dedicated_load(vertex)
        for edge_idx in graph.get_incident_edges(vertex):
            u, v = graph.edges[edge_idx]
            p_e = graph.get_edge_weight(edge_idx)
            # add x_ev * p_e to the load
            if vertex == u:
                load_expr += variables[(edge_idx, u)] * p_e
            else:  # vertex == v
                load_expr += variables[(edge_idx, v)] * p_e
        constraints.append(load_expr <= 1.0)
    
    # star constraints: sum of x_ev over big edges e in EB with v in e <= 1 for each vertex v
    for vertex in graph.vertices:
        star_expr = 0
        for edge_idx in graph.get_incident_edges(vertex):
            if edge_idx in big_edges:
                u, v = graph.edges[edge_idx]
                if vertex == u:
                    star_expr += variables[(edge_idx, u)]
                else:  # vertex == v
                    star_expr += variables[(edge_idx, v)]
        constraints.append(star_expr <= 1.0)
    
    # objective: minimize 0 (we're just checking feasibility)
    # in practice, we can use any objective since we're just checking feasibility
    objective = cp.Minimize(0)
    
    # solve
    problem = cp.Problem(objective, constraints)
    
    try:
        # try available solvers in order of preference
        solvers_to_try = [cp.CLARABEL, cp.OSQP, cp.SCIPY, cp.SCS]
        solved = False
        
        for solver in solvers_to_try:
            if solver in cp.installed_solvers():
                try:
                    problem.solve(solver=solver, verbose=False)
                    solved = True
                    break
                except:
                    continue
        
        if not solved:
            # fallback to default
            problem.solve(verbose=False)
        
        if problem.status in ["infeasible", "unbounded", "infeasible_inaccurate"]:
            return None
        
        # extract solution
        solution = {}
        for edge_idx, (u, v) in enumerate(graph.edges):
            val_u = variables[(edge_idx, u)].value
            val_v = variables[(edge_idx, v)].value
            
            # handle numerical issues: clamp to [0, 1]
            val_u = max(0.0, min(1.0, val_u if val_u is not None else 0.0))
            val_v = max(0.0, min(1.0, val_v if val_v is not None else 0.0))
            
            # normalize to ensure x_eu + x_ev = 1 (handle floating point errors)
            total = val_u + val_v
            if total > 1e-9:
                val_u = val_u / total
                val_v = val_v / total
            else:
                val_u = 0.5
                val_v = 0.5
            
            # convert to python float (from numpy types)
            solution[(edge_idx, u)] = float(val_u)
            solution[(edge_idx, v)] = float(val_v)
        
        return solution
        
    except Exception as e:
        # if solver fails, return None (infeasible)
        return None

