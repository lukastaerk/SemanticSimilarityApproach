import networkx as nx
import numpy as np

entity = "Q35120"


def get_subgraph_from(graph, node_id, depth=5):
    return nx.subgraph(graph, set(recursively_get_child_nodes(graph, node_id, depth)))


def get_subgraph_from_dac(graph, node_id):
    return nx.subgraph(graph, {*nx.descendants(graph, node_id), node_id})


def recursively_get_child_nodes(di_graph, idv, depth):
    if(len(list(di_graph.successors(idv))) == 0 or depth < 0):
        return [idv]
    else:
        depth = depth - 1
        ll = [recursively_get_child_nodes(
            di_graph, v, depth) for v in di_graph.successors(idv)]
        return [l for sub in ll for l in sub] + [idv]


def remove_backward_edges(di_graph, root_id):
    dac = nx.DiGraph()
    dac.add_nodes_from(di_graph.nodes(data=True))

    for (n1, n2) in list(nx.edge_dfs(di_graph, root_id)):
        if(not n1 in nx.descendants(dac, n2) and n1 != n2):
            dac.add_edge(n1, n2, value=di_graph[n1][n2]["value"])
    return dac


def all_shortest_paths(di_g):
    sim_m = nx.floyd_warshall_numpy(di_g)

    return
