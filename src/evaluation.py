from dataset import Dataset, SentenceDataset
from similarity import ConceptSimilarity
from scipy.stats import pearsonr, spearmanr
from kg import build_nx_graph, show_progression
from analytics import DiGraph, DAC
from preprocessing import get_ideas_in_format
from wmd import WordMoversSimilarity
import numpy as np
from IPython.display import display
import pandas as pd
import os.path as path

class WordSimEvaluation:
    """
    contains the following datasets: "noun_rg", "noun_mc", "noun_ws353", "noun_ws353-sim", "noun_simlex" 
    kwargs: correlation_metric spearman or pearson, default is spearman
    """
    def __init__(self, correlation_metric = "spearman"):
        self._dataset = Dataset()
        self._correlation = spearmanr if correlation_metric == "spearman" else pearsonr
        self.simData = {}
        self.dataset_names = ["noun_rg", "noun_mc", "ws353", "noun_ws353-sim", "noun_simlex"]
        self.metic_names = ["path", "wpath_graph","res", "lin", "jcn"]

    def evaluate_all(self):
        cors_matrix = [[
            self._dataset.load_dataset_json("%s_%s"%(dataset, metric))["correlation"]
                if path.exists("dataset/wordsim/results/%s_%s.json"%(dataset, metric)) 
                else self.evaluate_metric(metric, dataset, True)
            for dataset in self.dataset_names] for metric in self.metic_names]
        
        df_wpath = pd.DataFrame(cors_matrix, index=self.metic_names, columns=self.dataset_names)
        return display(df_wpath)

    def evaluate_datasets_metrics(self, metrics , datasets, display_table=False, **kwargs):
        cors = []
        for d in datasets:
            cors.append(self.evaluate_multiple_metrics(metrics, d, **kwargs))

        if display_table:
            df_wpath = pd.DataFrame(np.array(cors).T, index=metrics, columns=datasets)
            
            return display(df_wpath)
        return cors

    def evaluate_multiple_metrics(self, metrics, dataset_name, display_table=False, **kwargs):
        cors = []
        for m in metrics:
            cors.append(self.evaluate_metric(m,dataset_name, **kwargs))
        
        if display_table:
            df_wpath = pd.DataFrame([cors], index=[dataset_name], columns=metrics)
            return display(df_wpath)
        return cors

    def evaluate_datasets_wpath_k(self, sim_name, datasets, range_k=[k/10 for k in range(1,11)],display_table=False, **kwargs):
        cors = []
        for d in datasets:
            cors.append(self.evaluate_wpath_k(sim_name,d,range_k=range_k, **kwargs))
        
        if display_table:
            k_index = ["k=%s"%k for k in range_k]
            df_wpath = pd.DataFrame(np.array(cors).T, index=k_index, columns=datasets)
            df_wpath.to_csv("dataset/wordsim/results-csv/wpath_k.csv")
            return display(df_wpath)
        return cors
        
    def evaluate_wpath_k(self, sim_name, dataset_name, display_table=False, range_k=[k/10 for k in range(1,11)] ,**kwargs):

        cors =[self.evaluate_metric(sim_name, dataset_name, k=k, **kwargs) for k in range_k]
        if display_table:
            df_wpath = pd.DataFrame([cors], index=[dataset_name], columns=range_k)
            return display(df_wpath)
        return cors

    def evaluate_metric(self, sim_name, dataset_name, lcs_pref_value = "shortest_path", icfqvalue="freq", save_results=False, relatedness=False, **kwargs):
        concepts, word_pairs, get_ids_from_noun = self._dataset.transform_dataset(dataset_name)
        human = [v[2] for v in word_pairs]
        dataset_name_re = dataset_name.replace("type", "noun")
        KG = DAC(concepts=concepts, dataset=dataset_name_re, relatedness=relatedness)
        if(KG.graph.__len__()==0):
            print("start building knowledge graph")
            KG.build_nx_graph()
        #KG.remove_nodes_with_hight_freq(1)
        #print("KG has now len:",KG.graph.__len__())
        consim_key = dataset_name_re+lcs_pref_value+str(relatedness)
        
        if not consim_key in self.simData:
            ConSim = ConceptSimilarity(KG)
            ConSim.all_shortest_paths_and_LCS(lcs_pref_value)
            self.simData[consim_key] = ConSim
        else : 
            ConSim = self.simData[consim_key]
        sim_values = []
        lcs_values = []
        for (w1,w2, h) in word_pairs: 
            a,b = get_ids_from_noun(w1), get_ids_from_noun(w2)
            temp_sim = np.ndarray((len(a), len(b)))
            for i,ai in enumerate(a):
                for j,bi in enumerate(b):
                    sim = ConSim.similarity(ai, bi, sim_name, **kwargs, noun1=w1, noun2=w2)
                    temp_sim[i,j] = sim
            i,j = np.unravel_index(temp_sim.argmax(), temp_sim.shape)
            c1, c2 = a[i], b[j]
            lcs = KG.get_value(KG.get_key(int(ConSim.get_LCS(c1,c2))))
            lcs_values.append(lcs)
            sim_values.append(temp_sim[i,j])
        
        sim_values = [round(x, 3) for x in sim_values]
        maxH = round(max(human), 0)
        human = [x/maxH for x in human]
        cor = self._correlation(sim_values, human)[0]
        cor = round(cor, 3)
        if save_results:
            results = list(zip(map(lambda wp: wp[0],word_pairs), map(lambda wp: wp[1], word_pairs), map(lambda wp: round(wp[2], 2), word_pairs), [round(s*maxH,2) for s in sim_values],lcs_values))
            csv = pd.DataFrame(columns=["wordone", "wordtwo", "mean", "sim", "LCS"], data=results)
            k=""
            if ("k" in kwargs): k=kwargs["k"]
            csv.to_csv("dataset/wordsim/results-csv/%s_%s_%s_%s.csv"% (dataset_name,sim_name,lcs_pref_value, k))
            #self._dataset.save_dataset(dict(zip(("correlation", "similarities"),(cor, results))), dataset_name+"_"+sim_name+"_"+lcs_pref_value)
        return cor

class SentenceSimEvaluation(WordSimEvaluation):

    def __init__(self):
        self._dataset = SentenceDataset()
        self.sentence_dataset_names = ["MSRvid", "SmartTextile", "MTurk", "environment"]

    def evaluate_all_sentence_datasets(self, display_table=True, **kwargs):
        cors = [self.evaluate_sentence_similarity(name, **kwargs) for name in self.sentence_dataset_names]
        if display_table:
            df_wpath = pd.DataFrame([cors], index=["wpath"], columns=self.sentence_dataset_names)
            return display(df_wpath)
        return cors

    def evaluate_sentence_similarity(self, dataset_name="MSRvid", metric = "wpath_graph", relatedness=True, save_results = False, database="wikidata"):
        concepts, cc, texts = get_ideas_in_format(dataset_name, database=database)
        KG = DAC(concepts=concepts, dataset=dataset_name, relatedness=relatedness, database=database)
        if(KG.graph.__len__()==0):
            print("start building knowledge graph")
            KG.build_nx_graph()

        ConSim = ConceptSimilarity(KG)
        sim_M = ConSim.similarityMatrix(lcs_pref_value="freq1", metric=metric)
        WMD = WordMoversSimilarity(sim_M, KG._concepts)

        sen_pairs, human_sim = self._dataset.load_sentence_pairs_and_similarities(dataset_name)
        sim_values = []
        map_sen2bow = dict(zip(texts, [[c["id"] for c in bow] for bow in cc]))
        pg, total_len = 0 , len(sen_pairs)
        remove_index = []
        for sen1, sen2 in sen_pairs:
            show_progression(pg, total_len)
            bow1, bow2 = list(set(map_sen2bow[sen1]) & set(KG._concepts)), list(set(map_sen2bow[sen2]) & set(KG._concepts))
            sim_value = WMD.word_mover_distance(bow1, bow2)
            if sim_value is None:
                print(sen1, sen2)
                remove_index.append(pg)
            else:
                sim_values.append(sim_value)
            pg = pg+1
        
        human_sim = np.delete(human_sim, remove_index)
        cor = pearsonr(sim_values, human_sim)[0]
        if save_results:
            results = list(zip([round(x, 3) for x in sim_values], sen_pairs))
            self._dataset.save_dataset(dict(zip(("correlation", "similarities"),(cor, results))), dataset_name+"_"+metric)
        return cor

    def compute_concept_sentence_M(self, dataset_name="gold", database="wikidata",metric="wpath", lcs_pref_value="freq1", relatedness=True):
        concepts, cc, texts = get_ideas_in_format(dataset_name, database=database)
        bows = [[c["id"] for c in bow] for bow in cc]
        KG = DAC(concepts=concepts, dataset=dataset_name, relatedness=relatedness, database=database)
        if(KG.graph.__len__()==0): 
            print("start building knowledge graph")
            KG.build_nx_graph()

        ConSim = ConceptSimilarity(KG)
        sim_M = ConSim.similarityMatrix(lcs_pref_value="freq1", metric=metric)
        WMD = WordMoversSimilarity(sim_M, KG._concepts)
        ideaM = WMD.sentenceSimilarityMatrix(bows)
        con2ideaM = WMD.concepts2sentenceSIM(bows)
        SIM_data = {
            "concepts":KG._concepts, 
            "ideas":texts,
            "conceptSIM":sim_M.tolist(),
            "ideaSIM":ideaM.tolist(),
            "concept2ideaSIM":con2ideaM.tolist()
        }
        print(SIM_data["concepts"].__len__() == SIM_data["conceptSIM"].__len__())
        self._dataset.save_dataset(SIM_data, dataset_name)
        return SIM_data
