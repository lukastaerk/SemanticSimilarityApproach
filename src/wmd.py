import numpy as np
from itertools import product
from collections import defaultdict
import pulp

class WordMoversSimilarity:

    def __init__(self, SimMatrix, concepts):
        self._SIM = SimMatrix
        self._concepts = concepts
        self._concept2index = dict(zip(concepts, range(len(concepts))))

    def concepts2sentenceSIM(self, bows):
        SM = np.zeros((len(self._concepts), len(bows)))
        for i in range(len(self._concepts)):
            for j in range(len(bows)):
                bow = list(set(bows[j]) & set(self._concepts))
                bows_sort  = sorted(bow, key=lambda w: self._SIM[i,self._concept2index[w]])
                best = bows_sort[:5]
                SM[i,j] = sum([self._SIM[i,self._concept2index[b]]/len(best) for b in best])
        self._ConSenSim = SM
        return SM 

    def sentenceSimilartyMatrix(self, bows):
        bows_len = len(bows)
        SM = np.eye(bows_len)
        for i in range(bows_len):
            for j in range(i+1, bows_len):
                SM[i,j] = self.word_mover_distance(bows[i], bows[j])
                SM[j,i] = SM[i,j]
        return SM

    def concepts_to_index(self, concepts):
        return [self._concept2index[c] for c in concepts]

    def tokens_to_fracdict(self,tokens):
        cntdict = defaultdict(lambda : 0)
        for token in tokens:
            cntdict[token] += 1
        totalcnt = sum(cntdict.values())
        return {token: float(cnt)/totalcnt for token, cnt in cntdict.items()}
    
    def max_match_similarity(self, bow1, bow2):
        if len(bow1)==0 or len(bow2)==0:
            return None
        index1 = dict(zip(bow1, range(len(bow1))))
        index2 = dict(zip(bow2, range(len(bow2))))
        con_index1, con_index2 = self.concepts_to_index(bow1), self.concepts_to_index(bow2)
        SIM = self._SIM[con_index1,:][:, con_index2]

    def word_mover_distance(self, bow1, bow2):
        bow1, bow2 = list(set(bow1) & set(self._concepts)), list(set(bow2) & set(self._concepts))
        if len(bow1)==0 or len(bow2)==0:
            return 0
        prob = self.word_mover_distance_probspec(bow1, bow2)
        return pulp.value(prob.objective)
        
    def word_mover_distance_probspec(self,first_sent_tokens, second_sent_tokens, lpFile=None): 
        index1 = dict(zip(first_sent_tokens, range(len(first_sent_tokens))))
        index2 = dict(zip(second_sent_tokens, range(len(second_sent_tokens))))

        con_index1, con_index2 = self.concepts_to_index(first_sent_tokens), self.concepts_to_index(second_sent_tokens)
        SIM = self._SIM[con_index1,:][:, con_index2]
        first_sent_buckets = self.tokens_to_fracdict(first_sent_tokens)
        second_sent_buckets = self.tokens_to_fracdict(second_sent_tokens)

        T = pulp.LpVariable.dicts('T_matrix', list(product(first_sent_tokens, second_sent_tokens)), lowBound=0)

        prob = pulp.LpProblem('WMD', sense=pulp.LpMaximize)
        prob += pulp.lpSum([T[token1, token2]*SIM[index1[token1], index2[token2]]
                            for token1, token2 in product(first_sent_tokens, second_sent_tokens)])
        for token2 in second_sent_buckets:
            prob += pulp.lpSum([T[token1, token2] for token1 in first_sent_buckets])==second_sent_buckets[token2]
        for token1 in first_sent_buckets:
            prob += pulp.lpSum([T[token1, token2] for token2 in second_sent_buckets])==first_sent_buckets[token1]

        if lpFile!=None:
            prob.writeLP(lpFile)

        prob.solve()
        return prob