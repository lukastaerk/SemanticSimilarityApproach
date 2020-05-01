import requests
import time
import functools
from sparql import query_wikidata_from_dbpedia
from json import JSONDecodeError

headers = {
            "User-Agent": "Concept-Similarity/1.0 (https://github.com/luka1220/Bachelor_Thesis) requests/2.22.0"
        }
babelfy_key = "e1a705de-b894-46f9-92c8-87b15eae25d6"
wikifier_key = "eududrphpqcrvrsxtzjwtpsndxcyqb"
endpoints = {
    "wikidata": 'https://query.wikidata.org/sparql',
    "dbpedia":'http://dbpedia.org/sparql', 
    "babelnet":'https://babelnet.org/sparql/',
    "babelfy": "https://babelfy.io/v1/disambiguate",
    "innovonto-core": "https://innovonto-core.imp.fu-berlin.de/management/orchard/query"
    }

@functools.lru_cache(10500)
def wsd_request(text):
    res = requests.get(endpoints["babelfy"], headers=headers, params={
            'text': text, "lang":"EN", 'key':babelfy_key})
    if res.status_code is 200:
        result = res.json()
        return result
    else:
        raise Exception("Status code is " + str(res.status_code), res)
    

def convert_dbp_wikid_ids(dbp_concepts):
    return [sparql_request(query_wikidata_from_dbpedia(c), "dbpedia")[0]["item"]["value"].split("/")[-1] for c in dbp_concepts]

@functools.lru_cache(105000)
def sparql_request(query, database="wikidata"):
    if(database in endpoints):
        url = endpoints[database]
    else:
        url = database
    
    try:
        res = requests.get(url, headers=headers, params={
            'query': query, 'format': 'json', 'key':babelfy_key})
    except JSONDecodeError:
        raise Exception("Status code is JSONDecodeError", res, query)  
    except:
        return None

    if res.status_code is 200:
        result = res.json()
        if not "results" in result or not "bindings" in result["results"]:
            return result
        else:
            return result["results"]["bindings"]
    else:
        raise Exception("Status code is " + str(res.status_code), res, query)
    

if __name__ == "__main__":
    pass
