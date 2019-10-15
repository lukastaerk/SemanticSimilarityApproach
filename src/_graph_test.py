from knowledge_graph import get_DiGraph_from_file
from analytics import get_subgraph_from, remove_backward_edges, all_shortest_paths_and_LCS
import networkx as nx
import unittest
import numpy as np
import os


class TestsKnowledgeGraph(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        filepath = "data/DiGraph_gold"
        if os.path.isfile(filepath):
            cls.graph = get_DiGraph_from_file()
            cls.dac_vehicle = remove_backward_edges(
                cls.graph, "Q42889")  # vehicle
        else:
            raise IOError("Clound not load graph from " + filepath)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_cycle_free_graph(self):
        self.assertTrue(nx.is_directed_acyclic_graph(self.dac_vehicle))

    def test_all_shortest_paths(self):
        M, LCS, Dir = all_shortest_paths_and_LCS(self.dac_vehicle)
        for i in np.random.randint(0, M.shape[0], size=10):
            for j in np.random.randint(0, M.shape[0], size=10):
                self.assertEqual(
                    M[i, j], Dir[int(LCS[i, j]), i] + Dir[int(LCS[i, j]), j])


if __name__ == '__main__':
    unittest.main()
