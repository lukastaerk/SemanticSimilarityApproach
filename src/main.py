import sys
from dataset import Dataset
from analytics import DiGraph, DAC

def process_wordsim_dataset(dataset):
    ds = Dataset()
    match = ds.match_noun_wikidata(dataset)
    concepts, _, _ = ds.transform_dataset(dataset)
    graph = DiGraph(concepts=concepts, dataset=dataset, relatedness=True)
    graph.build_nx_graph()
    graph.global_secondorder_freq()

if __name__ == "__main__":
    if sys.argv[1]:
        process_wordsim_dataset(sys.argv[1])
