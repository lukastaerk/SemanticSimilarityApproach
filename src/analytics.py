import networkx as nx
import numpy as np
from igraph import Graph
from connection import wikidata_sparql_request, query_freq_wikidata

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


def remove_backward_edges(di_graph, root_id=entity):
    dac = nx.DiGraph()
    dac.add_nodes_from(di_graph.nodes(data=True))

    for (n1, n2) in list(nx.edge_dfs(di_graph, root_id)):
        if(not n1 in nx.descendants(dac, n2) and n1 != n2):
            dac.add_edge(n1, n2, value=di_graph[n1][n2]["value"])
    return dac


def all_shortest_paths_and_LCS(di_g):
    nx.write_gml(di_g, "data/temp_graph")
    ig = Graph.Read_GML("data/temp_graph")
    sim_m = np.array(ig.shortest_paths())
    l = di_g.number_of_nodes()
    M = np.zeros((l, l))
    LCS = np.zeros((l, l))
    for i in range(l):
        M_i_j = sim_m + sim_m[:, i][np.newaxis].T
        arg_min_j = np.argmin(M_i_j, axis=0)
        M[i, :] = M_i_j[arg_min_j, np.arange(l)]
        LCS[i, :] = arg_min_j
    return M, LCS, sim_m


def get_distance_LCS(g, M, LCS, id1, id2):
    nodes = list(g.nodes(data=True))
    n1 = nodes[id1]
    n2 = nodes[id2]
    print("C1:", n1[1]["value"], "--", M[id1, id2], "-- C2:", n2[1]["value"])
    print("LCS:", nodes[int(LCS[id1, id2])][1]["value"])


def position_from_key(g, key):
    maped = map_key_pos(g)
    return maped[key]


def map_key_pos(g, inv=False):
    if(inv):
        return dict(zip(range(g.number_of_nodes()), g.nodes()))
    else:
        return dict(zip(g.nodes(), range(g.number_of_nodes())))


def information_content(concepts):
    IC = []
    for c, i in concepts:
        IC.append(wikidata_sparql_request(query_freq_wikidata(c, 2)))
    return [c[0]["count"]["value"] if c != None else None for c in IC]
