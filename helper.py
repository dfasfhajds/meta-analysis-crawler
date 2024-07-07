from bs4 import BeautifulSoup
import requests
import random
from dotenv import load_dotenv
import os
from xml.etree import ElementTree
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()
PUBMED_API_KEY = os.environ['PUBMED_API_KEY']

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

user_agents = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
]

def get_headers():
    """
    Randomly choose a User-Agent for HTTP headers

    Returns:
        HTTP headers
    """
    return {'User-Agent': random.choice(user_agents)}    

def get_pdf_url_from_scihub(doi: str) -> str:
    """
    Get the URL of the article pdf from Scihub given the article doi

    Parameters:
        doi (str): Article doi

    Returns:
        str: URL of the article pdf
    """
    full_text_response = session.get(f"https://sci-hub.mksa.top/{doi}", headers=get_headers())
    soup = BeautifulSoup(full_text_response.content, "html.parser")
    
    try:
        pdf_url = soup.find("embed").get("src")
        return pdf_url
    except Exception as e:
        return None

def get_pdf_url_from_pmc(pmc: str) -> str:
    """
    Get the URL of the article pdf from PMC given the article PMC

    Parameters:
        pmc (str): Article PMC

    Returns:
        str: URL of the article pdf
    """
    full_text_response = session.get(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}", headers=get_headers())
    soup = BeautifulSoup(full_text_response.content, "html.parser")
    try:
        pdf_link = soup.find("li", {'class': "pdf-link"})
        if pdf_link:
            pdf_url = pdf_link.find("a").get("href")
            return f"https://www.ncbi.nlm.nih.gov{pdf_url}"
        else:
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/?report=printable"
    except Exception as e:
        return None
    
def get_pdf_url_from_doi_org(doi: str):
    """
    Get the URL of the article pdf from doi.org given doi
    Currently only JAMA is supported.

    Parameters:
        doi (str): Article doi

    Returns:
        str: URL of the article pdf
    """
    full_text_response = requests.get(f"https://doi.org/{doi}", headers=get_headers())
    soup = BeautifulSoup(full_text_response.content, "html.parser")
    
    for anchor in soup.find_all("a"):
        # JAMA
        if "jama" in doi and "pdf" in anchor.__str__():
            if anchor.has_attr("data-article-url"):
                return f"https://jamanetwork.com/{anchor.get('data-article-url')}"
    
def get_doi_from_pmid(pmid: str):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        'db': 'pubmed',
        'id': pmid,
        'retmode': 'xml',
        'api_key': PUBMED_API_KEY
    }
    response = session.get(url, params=params, headers=get_headers())
    xml_response = ElementTree.fromstring(response.content)
    
    try:
        return xml_response.find(".//ArticleId[@IdType='doi']").text
    except Exception as e:
        return None

def get_pdf_url(pmc: str, doi: str, pmid: str):
    """
    Get the URL of the article pdf given PMC and doi

    Parameters:
        pmc (str): Article PMC
        doi (str): Article doi

    Returns:
        str: URL of the article pdf
    """
    if pmc:
        url = get_pdf_url_from_pmc(pmc)
        if url:
            return url
    
    if not doi and pmid:
        doi = get_doi_from_pmid(pmid)

    if doi:
        url = get_pdf_url_from_scihub(doi)
        if url:
            return url
        
        url = get_pdf_url_from_doi_org(doi)
        if url:
            return url
    
    return None