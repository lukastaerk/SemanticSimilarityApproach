import json
from connection import sparql_request, wsd_request
import sparql
from helpers import flatten_array

class Dataset:
    """
    This class is used to prepare and separate word similarity datasets.
    """
    def __init__(self):
        self.dbp_uri = "http://dbpedia.org/resource/"

    def load_dataset(self, dataset_name):
        """
        prefix path: "dataset/wordsim"
        this function loads the word similarity dataset, for human judgement
        :param dataset_name: the name of the file in the folder dataset
        :return word pairs and human ratings 
        """
        with open('dataset/wordsim/%s.txt' % dataset_name, "r") as data:
            word_pairs = list(map(lambda x: (x.split()[0], x.split()[1], float(x.split()[2])), data))
            return word_pairs
    
    def load_dataset_json(self, dataset_name, path="dataset/wordsim/results"):
        """
        prefix path: "dataset/wordsim/results"
        """
        with open('%s/%s.json' % (path,dataset_name), "r") as f:
            return json.load(f)

    def load_idea_dataset(self, dataset_name):
        dataset = self.load_dataset_json(dataset_name, path="data/wikidata")
        concepts = list(set(flatten_array([[c["id"] for c in idea["concepts"]] for idea in dataset])))
        return concepts, dataset

    def save_dataset(self,data, name, path="dataset/wordsim/results"):
        with open("%s/%s.json" % (path,name), "w+") as f:
            f.write(json.dumps(data, indent=2))

    def transform_dataset(self,name):
        pairs = self.load_dataset(name)
        name_re = name.replace("type", "noun")
        try: 
            concept_maping = self.load_dataset_json("%s_concept_map" % name_re)
        except:
            concept_maping = self.match_noun_wikidata(name_re)
        concepts = [[r["item"]["value"].split("/")[-1] for r in results] for results in concept_maping.values()]
        concepts = list(set(flatten_array(concepts)))
        return concepts, pairs, self.get_concepts_from_noun(concept_maping)

    def get_concepts_from_noun(self,maping):
        def get_concepts(noun):
            return list(map(lambda c: c["item"]["value"].split("/")[-1], maping[noun]))
        return get_concepts

    def concepts_of_dataset(self, pairs):
        concepts = []
        for a in pairs:
            concepts += [a[0],a[1]]
        return list(set(concepts))

    def match_noun_wikidata(self,name, limit = 10):
        nouns = self.concepts_of_dataset(self.load_dataset(name))
        d = dict(zip(nouns, [[] for i in nouns]))
        for n in nouns:
            data = sparql_request(sparql.query_search_wikidata(n, limit))
            results = list(filter(lambda x: self.f_r(n, x), data))
            if len(results)==0: 
                results = list(filter(lambda x: self.f_r(n, x, str.lower), data))
            if len(results)==0:
                results = [data[0]]
            d[n]= results
        self.save_dataset(d, "%s_concept_map" % name)
        return d

    def f_r(self, noun, result, func = lambda x: x):
        if "itemAltLabel" in result:
            labels = func(result["itemLabel"]["value"])+","+func(result["itemAltLabel"]["value"])
        else:
            labels = func(result["itemLabel"]["value"])
        return (noun in [l.strip() for l in labels.split(",")])

class SentenceDataset(Dataset):
        
    def load_sentence_pairs(self, name="STS.input.MSRvid"):
        with open('dataset/test-gold/%s.txt' % name, "r") as data:
            sentence_pairs = [(x.split('\t')[0].strip(), x.split('\t')[1].strip()) for x in data]
            return sentence_pairs
    
    def load_sentence_similarities(self, name="STS.gs.MSRvid"): 
        with open("dataset/test-gold/%s.txt" % name, "r") as data:
            return [float(s.split()[0]) for s in data]

    def sentence_concept_annotation(self, name="STS.input.MSRvid"):
        s_pairs = self.load_sentence_pairs()
        sentences = list(set(flatten_array(s_pairs)))
        dataset_sen = []
        for s1 in sentences[:1000]:
            c1 = [{"DBpediaURL":c["DBpediaURL"], "babelSynsetID":c["babelSynsetID"], "value":s1[c["charFragment"]["start"]:c["charFragment"]["end"]+1]} for c in wsd_request(s1)]
            dataset_sen.append({"text": s1, "concepts":c1})
        self.save_dataset(dataset_sen, name+".2" ,path="data/dbpedia")
        return dataset_sen
    