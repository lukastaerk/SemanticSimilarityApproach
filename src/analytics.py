import networkx as nx
from networkx import NetworkXError
import numpy as np
import time, functools
from igraph import Graph
from connection import sparql_request
import sparql as sql
from kg import show_progression, get_query_for_database_to_build_KG

entity = "Q35120"
class DiGraph: 
    def __init__(self, concepts = [], dataset="gold", database = "wikidata", relatedness=False, **kwargs):
        self._dataset= dataset
        self._database = database
        self._key2pos = dict()
        self._entity = "Q35120"
        self._init_concepts = concepts
        self._concepts = []
        self._relatedness = relatedness
        if "graph" in kwargs:
            self.graph = kwargs["graph"]
            self.init_key2pos()
        else: 
            try:
                self.read_DiGraph()
            except FileNotFoundError as error:
                print(error)
                self.graph = nx.DiGraph()
        #print("init with: %s nodes, with %s concepts for dataset %s and database %s" % (self.graph.__len__(), len(self._concepts), dataset, database))

    def init_key2pos(self):
        self._concepts = list(self._init_concepts & self.graph.nodes)
        self._key2pos = dict(zip(self.graph.nodes(), range(self.graph.number_of_nodes())))

    def read_DiGraph(self):
        if self._relatedness:
            path = "data/%s/DiGraph_rel_%s.gml"
        else:
            path = "data/%s/DiGraph_%s.gml"
        self.graph = nx.read_gml(path % (self._database, self._dataset))
        self.init_key2pos()
        return self.graph

    def write_to_file(self):
        if self._relatedness: 
            path = "data/%s/DiGraph_rel_%s.gml"%(self._database, self._dataset)
        else: 
            path = "data/%s/DiGraph_%s.gml" %(self._database, self._dataset)
        nx.write_gml(self.graph, path)
        print(" Worte to file: %s" %(path))
        return "done"
        
    def get_position(self, key):
        return self._key2pos[key]

    def get_key(self, pos):
        return list(self.graph.nodes())[pos]

    def get_value(self, key):
        return self.graph.nodes()[key]["value"]
    
    def get_subgraph_from(self, node_id, depth=5):
        return nx.subgraph(self.graph, set(self.recursively_get_child_nodes(node_id, depth)))

    def decendants_of(self, id):
        queue = [id]
        decendants = []
        while len(queue) > 0:
            q = queue.pop()
            succ = [v for v in self.graph.successors(q) if not v in decendants and v != id]
            decendants.extend(succ)
            queue.extend(succ)
        return decendants

    def remove_nodes_with_hight_freq(self, include=0.6):
        limit = self.graph.__len__() * include
        remove_nodes = [x[0] for x in self.sort_nodes_by_freq() if x[1] > limit and x[0] not in self._concepts]
        self.graph.remove_nodes_from(remove_nodes)
        self.init_key2pos()

    def sort_nodes_by_freq(self):
        for n in self.graph.nodes:
            self.decendants_freq(n)
        return sorted(self.graph.nodes("freq"), key=lambda x: x[1], reverse=True)

    def decendants_freq(self, id):
        if id == self._entity:
           return self.graph.__len__()
        if not "freq" in self.graph.nodes[id] or self.graph.nodes[id]["freq"] == 0:
            self.graph.nodes[id]["freq"] = len(self.decendants_of(id)) + 1
        return self.graph.nodes[id]["freq"]

    @functools.lru_cache(1050000)
    def freq_by_value(self, id, value):
        if value == "freq":
            if id == self._entity:
                return self.graph.__len__()
            return self.decendants_freq(id)
        if id == self._entity:
            return sum([freq[1] for freq in self.graph.nodes(value)])
        freq = self.graph.nodes[id][value] +1.0
        for n in self.decendants_of(id):
            freq += self.graph.nodes[n][value] + 1.0
        return freq

    def global_secondorder_freq(self, write_value="freq1"):
        i, num_nodes = 0, self.graph.__len__()
        for n in self.graph.nodes:
            i = i+1
            show_progression(i, num_nodes )
            try:
                num1 = sparql_request(sql.query_number_of(n, "wdt:P31"))[0]["count"]["value"]
                num2 = sparql_request(sql.query_number_of(n, "wdt:P279"))[0]["count"]["value"]
                self.graph.nodes[n][write_value] = int(num1) + int(num2)
            except:
                print("timeout", n)
                self.graph.nodes[n][write_value] = 6000000
        self.write_to_file()

    def recursively_get_child_nodes(self, idv, depth):
        if(len(list(self.graph.successors(idv))) == 0 or depth < 0):
            return [idv]
        else:
            depth = depth - 1
            ll = [self.recursively_get_child_nodes(v, depth) for v in self.graph.successors(idv)]
            return [l for sub in ll for l in sub] + [idv]

    def add_edges_for_concept(self, query_str, nxKG, split_delimiter="/", prefix=""):
        concept_keys = []
        pre = "is-a"
        v1, v2 = "no label", "no label"
        response = sparql_request(query_str, self._database)
        if type(response) is not type([]):
            response = sparql_request(query_str+" ", self._database)
        for r in response:
            (k1,k2) = (prefix + r["item"]["value"].split(split_delimiter)[-1],
                                prefix + r["superItem"]["value"].split(split_delimiter)[-1])
            if "itemLabel" in r: 
                v1 = r["itemLabel"]["value"]
            if "superItemLabel" in r:
                v2 = r["superItemLabel"]["value"]
            if "pre" in r: 
                pre = r["pre"]["value"].split("/")[-1]
            if not nxKG.has_node(k1):
                nxKG.add_node(k1, value=v1)
            if not nxKG.has_node(k2): 
                nxKG.add_node(k2, value=v2)
                concept_keys.append(k2)
            if not nxKG.has_edge(k2, k1):
                nxKG.add_edge(k2, k1, value=pre)
        return concept_keys

    def build_nx_graph(self, query = sql.query_ancestors):
        start_t = time.time()
        concepts=self._init_concepts
        
        nxKG = nx.DiGraph()
        i,concepts_len = 0,len(concepts)
        for con in concepts:
            keys = [con]
            i=i+1
            show_progression(i, concepts_len)
            if self._relatedness:
                keys += self.add_edges_for_concept(query(con, sql.relation_prop), nxKG)
            while len(keys) > 0: 
                key = keys.pop()
                keys += self.add_edges_for_concept(query(key), nxKG)
        self.graph = nxKG
        self.init_key2pos()
        self.write_to_file()
        return print("building the Graph from %s took: %s seconds." % (self._database,(time.time()-start_t)))

class DAC(DiGraph):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph = make_DAC(self.graph, self._concepts)#remove_backward_edges(self.graph, entity)
    def build_nx_graph(self, **kwargs):
        return print("Function not available")
    def write_to_file(self): 
        return print("Function not available")

    def get_subgraph_from(self, node_id):
        return nx.subgraph(self.graph, {*nx.descendants(self.graph, node_id), node_id})

    def decendants_freq(self, node_id):
        if (not "freq" in self.graph.nodes[node_id]) or self.graph.nodes[node_id]["freq"] == 0:
            self.graph.nodes[node_id]["freq"]= len([*nx.descendants(self.graph, node_id), node_id])
        return self.graph.nodes[node_id]["freq"]

    def decendants_of(self, node_id):
        return list(nx.descendants(self.graph, node_id))

class BabelNet_DiGraph(DiGraph):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def global_secondorder_freq(self, write_value="freq1"):
        i, num_nodes = 0, self.graph.__len__()
        for n in self.graph.nodes:
            i = i+1
            show_progression(i, num_nodes )
            try:
                num1 = sparql_request(sql.query_babelnet_number_of(n))[0]["count"]["value"]
                self.graph.nodes[n][write_value] = int(num1)
            except:
                print("timeout babelnet", n)
                self.graph.nodes[n][write_value] = 6000000
        self.write_to_file()

    def build_nx_graph(self):
        if self._database != "babelnet":
            return print("Function only for babelnet")
        start_t = time.time()
        concepts=self._init_concepts
        nxKG = nx.DiGraph()
        i,concepts_len = 0,len(concepts)
        for con in concepts:
            keys = [con]
            i=i+1
            show_progression(i, concepts_len)
            while len(keys) > 0: 
                key = keys.pop()
                keys += self.add_edges_for_concept(sql.babelnet_paths2top(key), nxKG, split_delimiter="/s", prefix="bn:")
        self.graph = nxKG
        self.init_key2pos()
        self.write_to_file()
        return print("building the Graph from %s took: %s seconds." % (self._database,(time.time()-start_t)))


def remove_backward_edges(di_graph, root_id=entity):
    dac = nx.DiGraph()
    dac.add_nodes_from(di_graph.nodes(data=True))

    for (n1, n2) in list(nx.edge_dfs(di_graph, root_id)):
        if( n1 in nx.descendants(dac, n2) or n1 == n2):
            di_graph.remove_edge(n1,n2)
            #dac.add_edge(n1, n2, value=di_graph[n1][n2]["value"])
    
    return di_graph

def make_DAC(di_graph, concepts, root_id=entity):
    edge_herachy = sql.is_a_prop + ["all_other"]
    dac = nx.DiGraph()
    dac.add_nodes_from(di_graph.nodes(data=True))
    concepts = sorted(concepts, key=lambda c: di_graph.in_degree(c))
    #dac.add_edges_from(di_graph.out_edges(root_id, data=True))
    for edgeType in edge_herachy:
        queue = list(concepts)
        #queue.remove(root_id)
        past = []
        while len(queue) != 0:
            n2 = queue.pop(0)
            past.append(n2)
            for n1,n2, value in sorted(di_graph.in_edges(n2, data=True), key=lambda x: x[0]):
                if(value["value"] != edgeType and edgeType != "all_other"):
                    continue
                if(edgeType=="all_other" and value["value"] in edge_herachy):
                    continue
                if(not n1 in nx.descendants(dac, n2) and n1 != n2):
                    dac.add_edge(n1, n2, value=value["value"])
                    if not n1 in past and not n1 in queue:
                        queue.append(n1)

    return dac


def get_distance_LCS(g, M, LCS, id1, id2):
    nodes = list(g.nodes(data=True))
    n1 = nodes[id1]
    n2 = nodes[id2]
    print("C1:", n1[1]["value"], "--", M[id1, id2], "-- C2:", n2[1]["value"])
    print("LCS:", nodes[int(LCS[id1, id2])][1]["value"])


def information_content(concepts):
    IC = []
    for c, i in concepts:
        show_progression(i, len(concepts))
        IC.append(sparql_request(sql.query_freq_wikidata(c, 2),"wikidata"))
    return [c[0]["count"]["value"] if c != None else None for c in IC]
