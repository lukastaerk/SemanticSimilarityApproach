import requests
import time
from sparql_queries import query_paths_to_entity, query_wikidata_from_dbpedia, query_freq_wikidata

headers = {
    "User-Agent": "Topic-Extraction/1.0 (https://github.com/luka1220/Bachelor_Thesis) requests/2.22.0"
}


def convert_dbp_wikid_ids(dbp_concepts):
    return [(map_dbp_wikid(c).split("/")[-1], c.split("/")[-1]) for c in dbp_concepts]


def map_dbp_wikid(dbpediaConcept):
    url = "http://dbpedia.org/sparql"
    results = requests.get(url, headers=headers, params={
                           'query': query_wikidata_from_dbpedia(dbpediaConcept), 'format': 'json'})
    if results.status_code is not 200:
        raise Exception(results.status_code, results.test)

    results = results.json()["results"]["bindings"]
    if len(results) == 0:
        print("No results in dbpedia found for " + dbpediaConcept)
        raise Exception("No results in dbpedia found for " + dbpediaConcept)
    if len(results) > 1:
        print("Multiple results in dbpedia found for " + dbpediaConcept)
        raise Exception(
            "Multiple results in dbpedia found for " + dbpediaConcept)
    return results[0]["obj"]["value"]


def wikidata_sparql_request(query):
    url = 'https://query.wikidata.org/sparql'
    try:
        res = requests.get(url, headers=headers, params={
            'query': query, 'format': 'json'})
    except:
        return None
    if res.status_code is 200:
        return res.json()["results"]["bindings"]
    if res.status_code == 500:
        return None
    else:
        raise Exception("Status code is " + str(res.status_code))


if __name__ == "__main__":
    pass
