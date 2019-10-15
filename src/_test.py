from preprocessing import get_ac1_ideas_in_format, get_cscw19_gold_ideas_in_format
from visualize import get_graphic_G
from knowledge_graph import make_nx_KG, get_DiGraph_from_file
import os
import networkx as nx
import unittest


class TestsPreprocessing(unittest.TestCase):

    def test_ac1(self):
        (c, cc, tests) = get_ac1_ideas_in_format()
        print(c)
        self.assertTrue(not len(c) == 0)

    def test_gold(self):
        (c, cc, tests) = get_cscw19_gold_ideas_in_format()
        self.assertTrue(not len(c) == 0)

    def test_get_graph_from_file(self):
        DiGraph = get_DiGraph_from_file()
        self.assertTrue(DiGraph.is_directed())


class TestsDrawGraph(unittest.TestCase):
    def draw(self):
        concepts = [(1, "zwei"), (2, "drei")]
        g = make_nx_KG(concepts)
        G = get_graphic_G(g, concepts)
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
