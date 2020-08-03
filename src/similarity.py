from nltk.corpus import wordnet_ic
from nltk.corpus.reader.wordnet import information_content
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn
import networkx as nx
import numpy as np
from igraph import Graph
import sparql
from connection import sparql_request
import functools


class ConceptSimilarity:

    def __init__(self, KG, ic_corpus='brown'):
        self.G = KG
        self.size = KG.graph.__len__()
        self.entity = "Q35120"
        self._wn_lemma = WordNetLemmatizer()
        self._ic_corpus = wordnet_ic.ic('ic-brown.dat') if ic_corpus == 'brown' else wordnet_ic.ic('ic-semcor.dat')
        l = len(KG._concepts)
        self._SIM = np.zeros((l,l))
        self._LCS = np.zeros((l,l))
        self._similarities = None
        self._concepts_pos = dict(zip(self.G._concepts,range(l)))


    def similarityMatrix(self, metric="wpath_graph", lcs_pref_value="freq",icfqvalue="freq", k=0.8, **kwargs):
        SIM, LCS =self.all_shortest_paths_and_LCS(lcs_pref_value)
        for e in self.G.graph.nodes:
            self.G.freq_by_value(e, icfqvalue)

        total = self.G.freq_by_value(self.entity, icfqvalue)
        vec_func = np.vectorize(lambda x: self.ic(self.G.freq_by_value(self.G.get_key(int(x)),icfqvalue), total))
        IC = vec_func(LCS)
        similarities = 1/(1+SIM * (0.9 ** IC))
        self._similarities = similarities
        return similarities
    
    @functools.lru_cache(maxsize=128)
    def all_shortest_paths_and_LCS(self, lcs_pref_value="shortest_path"):
        nx.write_gml(self.G.graph, "data/temp_graph.gml")
        ig = Graph.Read_GML("data/temp_graph.gml")
        dist = np.array(ig.shortest_paths())
        self._dist_top_down = dist
        concept_pos = [self.G.get_position(key) for key in self.G._concepts]
        sim_m= dist[:,concept_pos]
        s = sim_m.shape
        if lcs_pref_value != "shortest_path":
            return self.sim_leastCommonSubsummer(sim_m, lcs_pref_value)
        l = s[1]
        M = np.zeros((l,l))
        LCS = np.zeros((l,l))
        for i in range(l):
            M_i_j = sim_m + sim_m[:, i][np.newaxis].T
            arg_min_j = np.argmin(M_i_j, axis=0)
            M[i, :] = M_i_j[arg_min_j, np.arange(l)]
            LCS[i, :] = arg_min_j
        self._SIM = M
        self._LCS = LCS
        print("done calculation all shortest distance")
        return M, LCS, 

    def sim_leastCommonSubsummer(self, dist, lcs_pref_value):
        lcs = (dist < float("inf")).astype(int)
        freq = np.array([self.G.freq_by_value(n, lcs_pref_value) for n in self.G.graph.nodes])
        max_freq = max(freq)
        castfreq = lcs * freq[np.newaxis].T
        inf = (dist == float("inf")).astype(int) * max_freq*2
        castfreq = castfreq + inf
        l = dist.shape[1] 
        M = np.zeros((l,l))
        LCS = np.zeros((l,l))
        for i in range(l):
            M_i_j = castfreq + castfreq[:, i][np.newaxis].T
            SIM_i_j = dist + dist[:, i][np.newaxis].T
            arg_min_j = np.argmin(M_i_j, axis=0)
            M[i, :] = SIM_i_j[arg_min_j, np.arange(l)]
            LCS[i, :] = arg_min_j
        self._SIM = M
        self._LCS = LCS
        print("done calculation all shortest distance for: %s"%(lcs_pref_value))
        return M, LCS

    def get_LCS(self, c1, c2):
        return self._LCS[self._concepts_pos[c1], self._concepts_pos[c2]]

    def method(self, name):
        return getattr(self, name)

    def ic_corpus(self, word):
        c = self.word2synset(word)
        if len(c)==0 and " " in word:
            return self.ic_corpus(word.split(" ")[0])
        elif len(c)==0:
            return 0.0
        return sum([information_content(ci, self._ic_corpus) for ci in c])/len(c)

    def ic_corpus_synset(self, syn):
        return information_content(syn, self._ic_corpus)

    def ic_graph(self, id):
        try:
            num = sparql_request(sparql.query_freq_wikidata(id, 2))
        except:
            return 0
        if len(num)>0 and "count" in num[0]: 
            num = int(num[0]["count"]["value"])
        else:
            return 0
        return -np.log(num/6900000)
            
    def ic_graph_local(self, id, **kwargs):
        freq = self.G.decendants_freq(id)
        return -np.log(freq/self.size)

    def ic_graph_global(self, id, icfqvalue="freq1", **kwargs):
        freq = self.G.freq_by_value(id, icfqvalue)
        return -np.log(freq/self.G.freq_by_value(self.entity, icfqvalue))

    def ic(self, freq, total):
        return -np.log(freq/total)

    @functools.lru_cache(maxsize=1050)
    def similarity(self, c1, c2, name='wpath_corpus', **kwargs):
        """
        Compute semantic similarity between two concepts
        :param c1:
        :param c2:
        :param name:
        :return:
        """
        return self.method(name)(c1, c2, **kwargs)
    
    def word2synset(self,word, pos=wn.NOUN):
        word = self._wn_lemma.lemmatize(word.split(" ")[0])
        ws = wn.synsets(word, pos)
        if len(ws)==0:
            print(word)
        return ws

    def wordnet_lcs_ic(self, syn1, syn2):
        return information_content(syn1.lowest_common_hypernyms(syn2)[0], self._ic_corpus)

    def lcs_form_cid(self, c1, c2):
        #w1, w2 = self.word2synset(self.G.get_value(c1)), self.word2synset(self.G.get_value(c1))
        w1, w2 = self.word2synset(c1), self.word2synset(c1)
        if len(w1)==0 or len(w2) == 0:
            return 0
        return sum([self.wordnet_lcs_ic(c1,c2) for c1 in w1 for c2 in w2])/(len(w1)*len(w2))

    def wpath_corpus(self, c1, c2, k=0.8, noun1="", noun2=""):
        i,j = self._concepts_pos[c1], self._concepts_pos[c2]
        dist = self._SIM[i,j]
        #lcs_pos = int(self._LCS[i,j])
        #lcs = self.G.get_key(lcs_pos)
        lcs_ic = self.lcs_form_cid(noun1, noun2)
        weight = k ** lcs_ic #self.ic_corpus(self.G.get_value(lcs))
        return 1.0 / (1 + dist * weight)

    def wpath(self, c1, c2, **kwargs):
        return self.wpath_graph(c1, c2, **kwargs)

    def wpath_graph(self, c1, c2, k=0.8, ic_func="ic_graph", **kwargs):
        i,j = self._concepts_pos[c1], self._concepts_pos[c2]
        dist = self._SIM[i,j]
        lcs_pos = int(self._LCS[i,j])
        lcs = self.G.get_key(lcs_pos)
        weight = k ** getattr(self,ic_func)(lcs, **kwargs)
        return 1.0 / (1 + dist * weight)

    def path(self,c1, c2, **kwargs):
        i,j = self._concepts_pos[c1], self._concepts_pos[c2]
        dist = self._SIM[i,j]
        return 1/(1+dist)

    def res(self, c1, c2, ic_func="ic_graph_local", **kwargs):
        i,j = self._concepts_pos[c1], self._concepts_pos[c2]
        lcs_pos = int(self._LCS[i,j])
        lcs = self.G.get_key(lcs_pos)
        return getattr(self,ic_func)(lcs, **kwargs)

    def lin(self, c1, c2, ic_func="ic_graph_local", **kwargs):
        ic = getattr(self,ic_func)
        return (2*self.res(c1, c2, ic_func, **kwargs))/(ic(c1, **kwargs) + ic(c2, **kwargs))

    def jcn(self, c1, c2, ic_func="ic_graph_local", **kwargs):
        ic = getattr(self,ic_func)
        return 1/(1+ic(c1, **kwargs) + ic(c2, **kwargs) - 2*self.res(c1, c2, ic_func, **kwargs))

    def wn_wpath(self, c1, c2, k=0.8, **kwargs):
        syn1,syn2 = self.word2synset(kwargs["noun1"]), self.word2synset(kwargs["noun2"])
        if len(syn1) == 0 or len(syn2) == 0: 
            return 0.0
        #print(syn1, syn2)
        dist = np.array([[s1.shortest_path_distance(s2) for s2 in syn2] for s1 in syn1])
        i,j = np.unravel_index(dist.argmin(), dist.shape)
        weight = k**self.wordnet_lcs_ic(syn1[i], syn2[j])
        return 1.0/(1+dist[i,j]*weight)