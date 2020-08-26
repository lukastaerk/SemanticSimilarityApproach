import pydot
import networkx as nx
from IPython.display import Image, display
from sparql import relation_prop
from similarity import ConceptSimilarity
from analytics import DAC
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

label_map= {
    "P279": "subclass of",
    "P31" : "instance of",
    "P460": "said to be the same as",
    "P361": "part of",
    "P171": "parent taxon",
    "P366": "use"
}

color_map = {
    "P279": "gray10",
    "P31": "gray40",
    "default": "gray60",
    "P361": "gray70",
    "P171": "yellow",
    "P460": "orange"
}
edge_grey = "gray20"
edge_map = {
    "P279": "solid",
    "P366": "dashed",
    "P460": "bold",
    "default": "dotted",
}
concept_color = "gold1" #"cornsilk"
normal_color = "cornsilk"#"floralwhite"
boarder_color = "moccasin"
concept_style = "filled, none"

for r in relation_prop:
    color_map[r.split(":")[-1]]="pink"

def draw_graph(name, graph, concepts, **kwargs):
    concepts_in_graph = [(n, graph.nodes()[n]["value"]) for n in concepts if n in graph.nodes()]
    g = pydot.Dot()
    g1 = get_graphic_G(graph, concepts_in_graph,concepts=concepts, **kwargs)
    get_legend(graph, name, **kwargs)
    g.add_subgraph(g1)
    im = Image(g.create_png())
    display(im)
    g.write_png("pic/%s.png"%name)

def get_legend(subgraph, name, show_ic=False, **kwargs):
    legend = pydot.Cluster(graph_type="digraph",
                           graph_name="Legend", label="Legend", rankdir="LR", color="white")
    colors = list(color_map.values())
    ic_label = ""
    if show_ic : ic_label = "\nIC"
    edge_types = set(map(lambda e: e[2]["value"], subgraph.edges(data=True)))
    for k in filter(lambda k: k in edge_types, reversed(edge_map.keys())):# count down
        legend.add_node(pydot.Node(
            label_map[k], shape="underline", color=edge_grey, style=edge_map[k]))
        # legend.add_node(pydot.Node(i, shape="point", color="white"))
        # legend.add_edge(pydot.Edge(labels[i], i, label = labels[i], color = colors[i]))
    legend.add_node(pydot.Node("concept"+ic_label, shape="ellipse",
                               color=normal_color,style=concept_style))
    legend.add_node(pydot.Node("idea \n concept"+ic_label, shape="ellipse",
                               color=concept_color, style=concept_style))
    G = pydot.Dot()
    G.add_subgraph(legend)
    G.write_png("pic/%s_legend.png"%name)
    return G


def get_graphic_G(graph, concepts_in_graph ,concepts=[], name="Knowledge Graph", all_edge_colors=True, show_ic = False, dataset="gold", relatedness=True):
    KG = DAC(concepts=concepts, dataset=dataset, relatedness=relatedness)
    cs = ConceptSimilarity(KG)
    G = pydot.Cluster(graph_type="digraph",
                  graph_name="Knowledge Graph", label="", color="white")
    ic_label = ""
    for (k, v) in concepts_in_graph:
        if(type(v)) != str:
            v = "UNKONWN"
        elif show_ic:
            ic_label = "\n%s"%round(cs.ic_graph_global(k),2)
        G.add_node(pydot.Node(
            k, label=v+ic_label, style=concept_style, color=concept_color))
    # init Nodes
    for (cid, data) in graph.nodes(data=True):
        if G.get_node(cid) == []:
            if(type(data["value"])) != str:
                data["value"] = "UNKONWN"
            elif show_ic:
                ic_label = "\n%s"%round(cs.ic_graph_global(cid),2)
            v = pydot.Node(cid, label=data["value"]+ic_label, style=concept_style, color=normal_color)
            G.add_node(v)
        for n in graph[cid]:
            if(G.get_edge(cid, n) == []):
                edge_label = graph[cid][n]["value"].split("/").pop()
                if not edge_label in edge_map:
                    edge_label = "default"
                e = pydot.Edge(
                    cid, n, color=edge_grey, style=edge_map[edge_label])
                G.add_edge(e)
    # if has Entity set color
    if G.get_node("Q35120") != []:
        G.add_node(pydot.Node("Q35120", label="Entity",
                              style=concept_style, fillcolor="green"))
    return G
