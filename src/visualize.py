import pydot
import networkx as nx
from IPython.display import Image, display
from sparql import relation_prop
"""
- Is-A herachic relation:
wdt:P279: subclass of,
wdt:P31: instance of,
wdt:P171: parent taxon,
wdt:P460: said to be the same as

- some relation:
wdt:P361: part of,
wdt:P527, has part,
wdt:P1542, has effect, 
wdt:P1889: different from,
wdt:P366: use, 
wdt:P2283: uses,
wdt:P1535: used by
"""
prefix = "http://www.wikidata.org/prop/direct/"
color_map = {
    "P279": "blue",
    "P31": "red",
    "P361": "green",
    "P171": "yellow",
    "P460": "orange"
}
for r in relation_prop:
    color_map[r.split(":")[-1]]="pink"

def draw_graph(name, graph, concepts=[]):
    concepts_in_graph = [n for n in concepts if n in graph.nodes()]
    g = get_graphic_G(graph, concepts_in_graph)
    im = Image(g.create_png())
    g.write_png("pic"+name+".png")
    return display(im)


def get_legend(G=None):
    legend = pydot.Cluster(graph_type="digraph",
                           graph_name="Legend", label="Legend", rankdir="LR")
    colors = ["blue", "red", "black"]
    labels = ["subclass of", "instance of", "traversal"]
    for i in range(2, -1, -1):
        legend.add_node(pydot.Node(
            labels[i], shape="underline", color=colors[i]))
        # legend.add_node(pydot.Node(i, shape="point", color="white"))
        # legend.add_edge(pydot.Edge(labels[i], i, label = labels[i], color = colors[i]))
    legend.add_node(pydot.Node("concept", shape="ellipse",
                               fillcolor="white", style="filled"))
    legend.add_node(pydot.Node("idea \n concept", shape="ellipse",
                               fillcolor="yellow", style="filled"))
    if not G: G = pydot.Dot()
    G.add_subgraph(legend)
    return G


def get_graphic_G(graph, concepts=[], name="Knowledge Graph"):
    G = pydot.Cluster(graph_type="digraph",
                  graph_name="Knowledge Graph", label=name)

    for (k, v) in concepts:
        if(type(v)) != str:
            v = "UNKONWN"
        G.add_node(pydot.Node(
            k, label=v, style="filled", fillcolor="yellow"))
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
