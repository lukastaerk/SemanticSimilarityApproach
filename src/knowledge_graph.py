import networkx as nx
import sys
import json
from connection import wikidata_sparql_request, convert_dbp_wikid_ids
from sparql_queries import query_paths_to_entity
from preprocessing import get_cscw19_gold_ideas_in_format, get_ac1_ideas_in_format


def goldstandard_Graph():
    concepts = read_concepts_from_file("data/gold_wiki_concepts.json")
    DiGraph = build_nx_graph(concepts, query_paths_to_entity)
    nx.write_gml(DiGraph, "data/DiGraph_gold")
    return DiGraph


def ac1_Graph():
    (c, cc, texts) = get_ac1_ideas_in_format()
    concepts = convert_dbp_wikid_ids(c)
    with open("ac1_wiki_concepts.json", "w+") as f:
        f.write(json.dumps(concepts, indent=2))
    DiGraph = build_nx_graph(concepts, query_paths_to_entity)
    nx.write_gml(DiGraph, "data/DiGraph_ac1")
    return DiGraph


def get_DiGraph_from_file():
    return nx.read_gml("data/DiGraph_gold")


def get_AC1_Graph_from_file():
    return nx.read_gml("data/DiGraph_ac1")


def read_concepts_from_file(name):
    with open(name, "r") as f:
        return json.load(f)


def get_gold_aswikidata():
    (gold_concepts, gold_concepts_per_idea,
     texts) = get_cscw19_gold_ideas_in_format()
    return convert_dbp_wikid_ids(gold_concepts)


def make_nx_KG(concepts):
    KG = nx.DiGraph()
    KG.add_nodes_from([(k, dict(value=v)) for (k, v) in concepts])
    return KG


def build_nx_graph(concepts, query_func=query_paths_to_entity):
    nxKG = make_nx_KG(concepts)
    concepts_len = len(concepts)
    for i, (key, v) in enumerate(concepts):
        text = "\rPercent: {0}%".format(int(i/concepts_len * 100))
        sys.stdout.write(text)
        sys.stdout.flush()
        for s in wikidata_sparql_request(query_func(key)):
            (k1, v1, k2, v2, pre) = (s["item"]["value"].split("/")[-1],
                                     s["itemLabel"]["value"],
                                     s["superItem"]["value"].split("/")[-1],
                                     s["superItemLabel"]["value"],
                                     s["pre"]["value"])
            nxKG.add_node(k1, value=v1)
            nxKG.add_node(k2, value=v2)
            nxKG.add_edge(k2, k1, value=pre)
    return nxKG
