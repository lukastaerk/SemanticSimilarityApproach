import pydot
import networkx as nx
from IPython.display import Image, display
prefix = "http://www.wikidata.org/prop/direct/"
color_map = {
    "P279": "blue",
    "P31": "red",
    "P361": "green"
}


def get_graphic_G(graph, concepts=[]):
    G = pydot.Dot(graph_type="digraph",
                  graph_name="Knowledge Graph", label="label:" + str(color_map))

    for (k, v) in concepts:
        if(type(v)) != str:
            v = "UNKONWN"
        G.add_node(pydot.Node(k, label=v, style="filled", fillcolor="yellow"))
    # init Nodes
    for (id, data) in graph.nodes(data=True):
        if G.get_node(id) == []:
            if(type(data["value"])) != str:
                data["value"] = "UNKONWN"
            v = pydot.Node(id, label=data["value"])
            G.add_node(v)
        for n in graph[id]:
            if(G.get_edge(id, n) == []):
                e = pydot.Edge(
                    id, n, color=color_map[graph[id][n]["value"].split("/").pop()])
                G.add_edge(e)
    # if has Entity set color
    if G.get_node("Q35120") != []:
        G.add_node(pydot.Node("Q35120", label="Entity",
                              style="filled", fillcolor="green"))
    return G
