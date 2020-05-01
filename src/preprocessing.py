import json
from connection import convert_dbp_wikid_ids
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

def save_dataset(data, name, database="wikidata"):
        with open("data/%s/%s.json" % (database, name), "w+") as f:
            f.write(json.dumps(data, indent=2))


def convert_dataset_dbp2wikidata(dataset_name):
    con, cc, text = get_ideas_in_format(dataset_name, database="dbpedia")
    con_wiki = convert_dbp_wikid_ids(con)
    dbp2wiki = dict(zip(con, con_wiki))
    #cc_wiki = [[] for arr in cc]
    new_dataset = []
    for i in range(len(text)):
        new_dataset.append({
            "text":text[i],
            "concepts": [{"value":c["value"], "wikidata_id": dbp2wiki[c["id"]]} for c in cc[i]]
            })
    save_dataset(new_dataset, dataset_name, database="wikidata")
    return (con_wiki, new_dataset)

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
                                [{"value":c[c_value],"id":c[dbp_link_prop]} for c in
                                 sum([idea[c_prop]
                                      for c_prop in concept_props if c_prop in idea], [])
                                 if c[c_value].lower() not in ENGLISH_STOP_WORDS and c[dbp_link_prop]!=""
                                 ], ideas))

    concepts = list(set([y["id"] for x in concept_per_idea for y in x]))
    return concepts, concept_per_idea, text_of_ideas


def get_ideas_in_format(dataset="gold", database="wikidata"):
    """ 
    args:
    dataset: gold, ac1, noun_rg, noun_mc, noun_ws353, noun_ws353_sim, noun_simlex, SmartTextile, MTurk, environment
    kwargs:
    database: wikidata, dbpedia, babelnet 
    """
    if(database == "wikidata"): 
        with open('data/%s/%s.json' % (database, dataset), 'r') as f:
            return get_concept_set(json.load(f), "text", "wikidata_id", "value", "concepts")
    elif(database == "babelnet"):
        with open('data/%s.json'% dataset, 'r') as f:
            return get_concept_set(json.load(f), "text", "babelSynsetID", "value", "concepts")
    elif(dataset=="gold"):
        with open('data/cscw19-1-goldstandard.json', 'r') as f:
            return get_concept_set(json.load(f), "text", "resource", "text", "concepts", "not_wrong")
    elif(dataset=="ac1"):
        with open('data/ac1-export-complete.json', 'r') as f:
            return get_concept_set(json.load(f)["@graph"], "content", "linkedConcept", "conceptSurface", "concept")
    elif(dataset=="MSRvid"):
        with open('data/STS.input.MSRvid.json', 'r') as f:
            return get_concept_set(json.load(f), "text", "DBpediaURL", "value", "concepts")
    elif(database== "dbpedia"):
        with open('data/%s.json' % dataset, 'r') as f:
            return get_concept_set(json.load(f), "text", "DBpediaURL", "value", "concepts")