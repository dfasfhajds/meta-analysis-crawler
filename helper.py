from bs4 import BeautifulSoup
import requests

headers = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}
    
def get_pdf_url_from_scihub(doi: str) -> str:
    """
    Get the URL of the article pdf from Scihub given the article doi

    Parameters:
        doi (str): Article doi

    Returns:
        str: URL of the article pdf
    """
    full_text_response = requests.get(f"https://sci-hub.mksa.top/{doi}", headers=headers)
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
    full_text_response = requests.get(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}", headers=headers)
    soup = BeautifulSoup(full_text_response.content, "html.parser")
    try:
        pdf_url = soup.find("li", {'class': "pdf-link"}).find("a").get("href")
        return f"https://www.ncbi.nlm.nih.gov{pdf_url}"
    except Exception as e:
        return None