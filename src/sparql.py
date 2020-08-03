"""
- Is-A herachic relation:
wdt:P279: subclass of,
wdt:P31: instance of,
wdt:P171: parent taxon,
wdt:P460: said to be the same as

- some relation:
wdt:P361: part of,
wdt:P527, has part,
wdt:P1542, has effect, 
wdt:P1889: different from,
wdt:P366: use, 
wdt:P2283: uses,
wdt:P1535: used by
"""
rel = {
    "part_of":"wdt:P361",
    "has_part":"wdt:P527", 
    "has_effect":"wdt:P1542",
    "different_from":"wdt:P1889",
    "use":"wdt:P366",
    "uses":"wdt:P2283",
    "used_by":"wdt:P1535"
}
is_a_prop_2 = ["wdt:P279", "wdt:P460" ]
is_a_prop = ["wdt:P460","wdt:P279", "wdt:P171", "wdt:P31"]
relation_prop = rel.values()

dbp_is_a = {"skos:broader", "rdf:type", "rdfs:subclassOf", "dcterms:subject"}


def query_search_wikidata(item, limit=10):
    return """
    SELECT DISTINCT ?item ?itemLabel ?itemAltLabel WHERE {
        SERVICE wikibase:mwapi {
            bd:serviceParam wikibase:api "EntitySearch" .
            bd:serviceParam wikibase:endpoint "www.wikidata.org" .
            bd:serviceParam mwapi:search "%s" .
            bd:serviceParam mwapi:language "en" .
            ?item wikibase:apiOutputItem mwapi:item .
            ?num wikibase:apiOrdinal true .
        }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        ?item (%s) ?superItem.
    } ORDER BY ASC(?num) LIMIT %s
    """ % (item, "|".join(is_a_prop) ,limit)

def query_freq_dbpedia(item):
    return """
    SELECT (COUNT(DISTINCT ?e) AS ?e) WHERE {
        ?e rdf:type owl:Thing .
        ?e rdf:type wd:""" + item + """.
        }
    """

dbp_thing = "<http://www.w3.org/2002/07/owl#Thing>"

def query_ancestors_dbpedia(item, prop = dbp_is_a): 
    return """
    SELECT ?item ?itemLabel ?pre ?superItem ?superItemLabel
    WHERE { 
    VALUES ?item {
         <%s>
    }
    VALUES ?pre {
        %s
    }
        ?item ?pre ?superItem.
    }
    """ % (item, "\n".join(prop))

def query_number_of(item, pre): 
    query = """
    SELECT (COUNT(*) AS ?count)
    WHERE   {?item %s wd:%s.}
    """ % (pre, item)
    return query

def query_num_of_instance_of(item):
    return query_number_of(item, "wdt:P31")

def query_num_of_subclasses_of(item):
    return query_number_of(item, "wdt:P279")

def query_freq_wikidata_with_depth(item, depth=10, prop=is_a_prop_2):
    query = """select (count(*) as ?count) { 
        select distinct * where 
        {%s}
        }"""
    first = """{%s}"""
    union = """ union {%s}"""
    triple = """?item %s wd:%s."""
    pre = "(%s)" % ("|".join(prop))
    body = first % (triple % (pre, item))
    for i in range(1,depth+1):
        body += union % (triple % ("/".join([pre]*i), item))
    return query % body



def query_freq_wikidata(item, number_of_pre=3):
    return """
    
    SELECT DISTINCT (COUNT(*) AS ?count)
    WHERE   { 
        ?item (""" + " | ".join(("wdt:P279", "wdt:P31", "wdt:P361")[:number_of_pre])+""")* wd:"""+item+""".
    }"""


def query_ancestors(item, prop=is_a_prop):
    return """
    SELECT ?item ?itemLabel ?pre ?superItem ?superItemLabel
    WHERE { 
    VALUES ?item {
         wd:%s
    }
    VALUES ?pre {
            %s
    }
    ?item ?pre ?superItem.
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """ % (item, "\n".join(prop))
    


def query_paths_to_entity(item, prop=is_a_prop):
    return """
    SELECT ?item ?itemLabel ?pre ?superItem ?superItemLabel
    WHERE { 
    VALUES ?pre {
            %s
    }
    wd:%s  (%s)* ?item.
    ?item ?pre ?superItem.
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    }
    """ %("\n".join(prop), item, " | ".join(prop))


def query_paths_to_entity_subclasses(item):
    return query_paths_to_entity(item, ("wdt:P279"))

def query_wikidata2wordnet(item):
    return """
    SELECT DISTINCT ?item
    WHERE   { 
        wd:%s (wdt:P2888|wdt:P2581) ?item
    }
    """ % (item)


def select_query(item, pre):
    return """
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
    
    SELECT ?item
    WHERE {
    { 
        <""" + dbpediaConcept + """> (owl:sameAs|^owl:sameAs) ?item
        FILTER(CONTAINS(str(?item), "http://www.wikidata.org")) 
    }
    UNION
    {
        ?alt ^dbo:wikiPageRedirects <""" + dbpediaConcept + """> .
        ?alt (owl:sameAs|^owl:sameAs) ?item.
        FILTER(CONTAINS(str(?item), "http://www.wikidata.org")) 
    }
    }
    """

def query_dbpedia2babelnet(dbpediaConcept):
    return """
    PREFIX bn: <http://babelnet.org/rdf/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT DISTINCT ?item
    WHERE   { 
        ?item  skos:exactMatch <%s>
    }
    """ % (dbpediaConcept)

def babelnet_paths2top(item): 
    return """
    prefix bn: <http://babelnet.org/rdf/s>
    SELECT ?item ?superItem ?itemLabel ?superItemLabel WHERE {
    VALUES ?item {
         %s
    }
        ?item a skos:Concept.
        ?item skos:broader ?superItem.
        ?superItem a skos:Concept .
    OPTIONAL {
        ?item bn-lemon:definition ?d1 .
        ?d1 lemon:language "EN" .
        ?d1 bn-lemon:gloss ?itemLabel .
    }
    OPTIONAL {
        ?superItem bn-lemon:definition ?d2 .
        ?d2 lemon:language "EN" .
        ?d2 bn-lemon:gloss ?superItemLabel.
    }
    }""" % (item)   

def query_babelnet_number_of(item, pre="skos:broader"): 
    query = """
    prefix bn: <http://babelnet.org/rdf/s>
    SELECT (COUNT(*) AS ?count) 
    WHERE   {?item %s %s.}
    """ % (pre, item)
    return query

def query_innovonto_contests():
    return """
    PREFIX gi2mo:<http://purl.org/gi2mo/ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX inov:<http://purl.org/innovonto/types/#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT * WHERE {
        ?project a gi2mo:IdeaContest;
            dcterms:title ?titel;
            dcterms:description ?description;
            dcterms:created	?created;
            gi2mo:endDate ?endDate;
            gi2mo:startDate ?startDate;
    }
    """

def query_find_all_contest_ideas(contestURI):
    return """
    PREFIX idea: <https://innovonto-core.imp.fu-berlin.de/entities/ideas/>  
    PREFIX gi2mo: <http://purl.org/gi2mo/ns#>  
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX inov:<http://purl.org/innovonto/types/#>
    
    DESCRIBE ?idea ?concept WHERE {
        ?idea a gi2mo:Idea.
        ?idea gi2mo:hasIdeaContest <%s>.
        ?idea inov:concept ?concept
    }""" % contestURI