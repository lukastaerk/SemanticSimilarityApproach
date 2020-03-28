import networkx as nx
from igraph import Graph
import sys
import json
import os.path
import re
from connection import sparql_request, convert_dbp_wikid_ids
import sparql
from preprocessing import get_ideas_in_format


def build_Graph(database="wikidata", dataset="gold"):
    path = "data/{}/{}_concepts.json".format(database, dataset)
    if not os.path.isfile(path):
        (concepts, cc, texts) = get_ideas_in_format(dataset)
        if(database=="wikidata"):
            concepts = convert_dbp_wikid_ids(concepts)
            with open(path, "w+") as f:
                f.write(json.dumps(concepts, indent=2))
        elif(database=="dbpedia"):
            with open(path, "w+") as f:
                f.write(json.dumps(concepts,indent=2))
        else:
            return 0
    else: 
        concepts = read_concepts_from_file(path)
    DiGraph = build_igraph_KG(concepts, database)
    DiGraph.write_gml("data/{}/DiGraph_{}.gml".format(database, dataset))
    return DiGraph


def read_concepts_from_file(name):
    with open(name, "r") as f:
        return json.load(f)


def build_nx_graph(concepts, database="wikidata"):
    query = get_query_for_database_to_build_KG(database)
    nxKG = nx.DiGraph()
    concepts_len = len(concepts)
    for i, key in enumerate(concepts):
        show_progression(i, concepts_len)
        for s in sparql_request(query(key), database):
            (k1, v1, k2, v2, pre) = (s["item"]["value"].split("/")[-1],
                                     s["itemLabel"]["value"],
                                     s["superItem"]["value"].split("/")[-1],
                                     s["superItemLabel"]["value"],
                                     s["pre"]["value"])
            if not nxKG.has_node(k1):
                 nxKG.add_node(k1, value=v1)
            if not nxKG.has_node(k2):
                nxKG.add_node(k2, value=v2)
            if not nxKG.has_edge(k2, k1):
                nxKG.add_edge(k2, k1, value=pre)
    return nxKG

def get_query_for_database_to_build_KG(database):
    if(database=="wikidata"):
        return sparql.query_paths_to_entity
    elif(database=="dbpedia"): 
        return sparql.query_ancestors_dbpedia
    else:
        return 0

def show_progression(i, total):
    text = "\rPercent: {0}%".format(round(i/total * 100,2))
    sys.stdout.write(text)
    sys.stdout.flush()
    

def build_igraph_KG(concepts, database="wikidata"):
    query = get_query_for_database_to_build_KG(database)
    concepts_len = len(concepts)
    g = Graph(directed=True)
    g.vs["name"]=""
    g.vs["label"]=""
    for i, c in enumerate(concepts):
        show_progression(i,concepts_len)
        for s in sparql_request(query(c), database):
            (k1, k2, pre) = (s["item"]["value"],s["superItem"]["value"],s["pre"]["value"])
            if("itemLabel" in s and "superItemLabel" in s):
                (v1, v2) = (s["itemLabel"]["value"],s["superItemLabel"]["value"])
            else: 
                (v1, v2) = (re.split('[/#]',k1)[-1], re.split('[/#]',k2)[-1])
            if len(g.vs.select(name=k1))==0:
                g.add_vertex(k1, label=v1)
            if len(g.vs.select(name=k2))==0:
                g.add_vertex(k2, label=v2)
            if g[k1,k2]==0:
                g.add_edge(k1, k2, label=pre)
    return g

