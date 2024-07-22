import requests
import xml.etree.ElementTree as ET
import json
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ['PUBMED_API_KEY']

def search_pubmed(query, max_results=10, api_key=OPENAI_API_KEY, publish_year=None):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "xml",
        "api_key": api_key
    }
    if publish_year:
        params["mindate"] = publish_year
    response = requests.get(base_url, params=params)
    root = ET.fromstring(response.content)
    id_list = [id_elem.text for id_elem in root.findall(".//Id")]
    total_count = root.find(".//Count").text # Total number of search results
    return id_list, total_count

def fetch_pubmed_details(ids, api_key=OPENAI_API_KEY):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
        "api_key": api_key
    }
    response = requests.get(base_url, params=params)
    root = ET.fromstring(response.content)
    results = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.find(".//PMID").text
        title = article.find(".//ArticleTitle").text if article.find(".//ArticleTitle") is not None else None
        abstract = article.find(".//AbstractText").text if article.find(".//AbstractText") is not None else None
        doi = None
        article_ids = article.findall(".//ArticleId")
        for id_elem in article_ids:
            if id_elem.attrib.get("IdType") == "doi":
                doi = id_elem.text
                break
        results.append({"PMID": pmid, "Title": title, "DOI": doi, "Abstract": abstract})
    return results

def save_details_as_json(details, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, 'base_references.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(details, f, ensure_ascii=False, indent=4)

def get_base_references(query, related_pmid, max_results=10, publish_year=None):
    api_key = OPENAI_API_KEY
    ids, total_count = search_pubmed(query, max_results=max_results, api_key=api_key, publish_year=publish_year)
    details = fetch_pubmed_details(ids, api_key=api_key)

    print(f"Total search results: {total_count}")

    output_dir = os.path.join('./data', related_pmid)
    save_details_as_json(details, output_dir)

# Sample
query = "cancer research"
related_pmid = "32497510"  
max_results = 10  
publish_year = "2020"  

"""
The function's parameters are as follows:
query (str): Search Keywords
related_pmid (str): PMID of the meta-analysis article
publish_year (str): Filter articles by publish year

Usage:
The function fetches the base references for the meta-analysis article with the given PMID.
"""
get_base_references(query, related_pmid, max_results=max_results, publish_year=publish_year)
