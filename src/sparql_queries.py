def query_freq_dbpedia(item):
    return """
    SELECT (count(?e) as ?e) WHERE {
        ?e rdf:type owl:Thing .
        ?e rdf:type wd:""" + item + """.
        }
    """


def query_freq_wikidata(item, number_of_pre=3):
    return """
    SELECT DISTINCT (COUNT(?item) AS ?count)
    WHERE   { 
      ?item (""" + " | ".join(("wdt:P279", "wdt:P31", "wdt:P361")[:number_of_pre])+""")* wd:"""+item+""".
    }"""


def paths_to_entity(item, predicates):
    return """
    SELECT ?item ?itemLabel ?pre ?superItem ?superItemLabel
    WHERE { 
      VALUES ?pre {
        """ + "\n".join(predicates) + """
      }
      wd:""" + item + """  (""" + " | ".join(predicates) + """)* ?item.
      ?item ?pre ?superItem.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """


def query_paths_to_entity(item):
    return paths_to_entity(item, ("wdt:P279", "wdt:P31", "wdt:P361"))


def query_paths_to_entity_subclasses(item):
    return paths_to_entity(item, ("wdt:P279"))


def select_query(item, pre):
    return """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    
    SELECT ?item ?label
    WHERE 
    {
        wd:""" + item + """ wdt:""" + pre + """ ?item.
        ?item rdfs:label ?label.
        FILTER (lang(?label) = "en")
    }
    """


def query_wikidata_from_dbpedia(dbpediaConcept):
    return """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dbpedia: <http://dbpedia.org/resource/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    
    SELECT ?obj
    WHERE {
    { 
        <""" + dbpediaConcept + """> (owl:sameAs|^owl:sameAs) ?obj
        FILTER(CONTAINS(str(?obj), "http://www.wikidata.org")) 
    }
    UNION
    {
        ?alt ^dbo:wikiPageRedirects <""" + dbpediaConcept + """> .
        ?alt (owl:sameAs|^owl:sameAs) ?obj.
        FILTER(CONTAINS(str(?obj), "http://www.wikidata.org")) 
    }
    }
    """
