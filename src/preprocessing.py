import json
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS


def sort_concepts_by_freq(concepts, concepts_per_idea):
    num = []
    for i, c in enumerate(concepts):
        num += [sum([c in cc for cc in concepts_per_idea])]

    c_nr = list(zip(concepts, num))
    c_nr = sorted(c_nr, key=lambda o: o[1], reverse=True)
    print([(c[0].split("/")[-1], c[1]) for c in c_nr][:10])


def get_concept_set(file_array, text_prop, dbp_link_prop, c_value, *concept_props):
    if type(file_array) is not list:
        raise Exception(
            "file_array is not a list, its of type: {0}".format(type(file_array)))
    ideas = list(filter(
        lambda i:
        text_prop in i
        and
            all([
                c_prop not in i
                or
                (c_prop in i and type(i[c_prop]) is list)
                for c_prop in concept_props
            ]), file_array))
    text_of_ideas = [idea[text_prop] for idea in ideas]

    concept_per_idea = list(map(lambda idea:
                                [c[dbp_link_prop] for c in
                                 sum([idea[c_prop]
                                      for c_prop in concept_props if c_prop in idea], [])
                                 if c[c_value].lower() not in ENGLISH_STOP_WORDS
                                 ], ideas))
    concepts = list(set([y for x in concept_per_idea for y in x]))
    return (concepts, concept_per_idea, text_of_ideas)


def get_cscw19_gold_ideas_in_format():
    with open('data/cscw19-1-goldstandard.json', 'r') as f:
        return get_concept_set(json.load(f), "text", "resource", "text", "concepts", "not_wrong")


def get_ac1_ideas_in_format():
    with open('data/ac1-export-complete.json', 'r') as f:
        return get_concept_set(json.load(f)["@graph"], "content", "linkedConcept", "conceptSurface", "concept")
