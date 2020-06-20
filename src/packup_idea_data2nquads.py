from dataset import Dataset
from pyld import jsonld
import uuid, json

dataset2contest =  {
    "ac1":"TCO_AC1",
    "gold":"TCO_Gold"
}

context = {
    "applicationCase": "oid:applicationCase",
    "concepts": {
        "@id": "inov:concept",
        "@type": "@id"
      },
    "hasIdeaContest" : {
      "@id" : "http://purl.org/gi2mo/ns#hasIdeaContest",
      "@type" : "@id"
    },
    "wd": "https://www.wikidata.org/wiki/",
    "description": "dcterms:description",
    "title": "dcterms:title",
    "content": "gi2mo:content",
    "created": "dcterms:created",
    "value": "concept:Surface",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "wikidata_id": "inov:linkedConcept",
    "challenge": "inov:challenge",
    "idea" : "http://purl.org/innovonto/ontoideaLegacy/ideas/",
    "gi2mo" : "http://purl.org/gi2mo/ns#",
    "dcterms" : "http://purl.org/dc/terms/",
    "inov" : "http://purl.org/innovonto/types/#"
  }

def pack_idea(idea, ideaContest):
    ideald = {
        "@id": "idea:%s"%uuid.uuid1(),
        "@type": "gi2mo:Idea",
        "content": idea["text"],
        "hasIdeaContest": "http://purl.org/innovonto/ideaContests/%s"%ideaContest,
        "concepts": [pack_concept(c) for c in idea["concepts"]]
          } 
    return ideald     

def pack_concept(concept):
    concept = {
        "@id": "http://purl.org/innovonto/ontoideaLegacy/concepts/%s"%uuid.uuid1(),
        "wikidata_id": "wd:%s"%concept["wikidata_id"],
        "value":concept["value"]
    } 
    return concept

def packup_dataset(dataset_name):
    contest = dataset2contest[dataset_name]
    DS = Dataset()
    ideas = DS.load_dataset_json(dataset_name, "data/wikidata")
    packed_ideas = [pack_idea(idea, contest) for idea in ideas]
    newfile = {
        "@context": context,
       "@graph": packed_ideas
       }
    nquads = jsonld.to_rdf(newfile,{"format":'application/n-quads'})
    DS.save_dataset_nq(nquads, dataset_name, "data/core_data")

def update_contest_db():
    DS = Dataset()
    contest_data = DS.load_dataset_json("contest_data", "data/core_data")
    nquads = jsonld.to_rdf(contest_data,{"format":'application/n-quads'})
    DS.save_dataset_nq(nquads, "contest_data", "data/core_data")
