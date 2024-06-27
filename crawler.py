import requests
import datetime
from xml.etree import ElementTree
from bs4 import BeautifulSoup
from document import MetaAnalysis

class Crawler:
    """Wrapper of PubMed MetaAnalysis Crawler"""

    def __init__(self):
        pass


    def __query_PMID(self: object, search_term: str, max_results: int = 10) -> list:
        """
        Retrieve the article PMIDs for a query
    
        Parameters:
            search_term (str): Search term on PubMed database
            max_results (int): Maximum number of PMIDs to retrieve
    
        Returns:
            list: A list of PMIDs
        """

        # Search for the article
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={search_term}&retmax={max_results}&retmode=xml"
        search_response = requests.get(search_url)
        search_tree = ElementTree.fromstring(search_response.content)

        # Extract PubMed ID (PMID)
        return [e.text for e in search_tree.find("IdList").findall("Id")]

    def __query_article(self: object, pmid: str) -> MetaAnalysis:
        """
        Retrieve the article information with its PMID
    
        Parameters:
            pmid (str): Article PMID
    
        Returns:
            MetaAnalysis: Article object
        """

        # Fetch article details using the PMID
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
        response = requests.get(url)
        xml_response = ElementTree.fromstring(response.content)

        # get article data
        title = xml_response.find(".//ArticleTitle").text
        doi = xml_response.find(".//ArticleId[@IdType='doi']").text
        journal = xml_response.find(".//Journal/Title").text
        pmc = xml_response.find(".//ArticleId[@IdType='pmc']").text

        # get abstract
        abstract_elements = xml_response.findall(".//AbstractText")
        abstract = ''.join([f"""## {a.attrib['Label']}\n{a.text}\n""" for a in abstract_elements])
        
        # get article date
        date_element = xml_response.find(".//PubMedPubDate[@PubStatus='pubmed']")
        date = f"{date_element.find('.//Year').text}/{date_element.find('.//Month').text}/{date_element.find('.//Day').text}"

        # get article authors
        authors_element = xml_response.findall(".//Author")
        authors = []
        for element in authors_element:
            lastname = element.find('.//LastName')
            forename = element.find('.//ForeName')
            if lastname is not None and forename is not None:
                authors.append(f"{lastname.text} {forename.text}")

        doc = MetaAnalysis(
            pmid=pmid,
            pmcid=pmc,
            title=title,
            authors=authors,
            doi=doi,
            journal=journal,
            abstract=abstract,
            publication_date=date
        )

        return doc
        
    def __extract_figures_from_article(self: object, article: MetaAnalysis) -> list:
        """
        Extract figures (src, caption) of a article
    
        Parameters:
            article (MetaAnalysis): Article object
    
        Returns:
            List: Figure list
        """
        pmid = getattr(article, 'pmid')
        pmcid = getattr(article, 'pmcid')
        try:
            results = []
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
            full_text_response = requests.get(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}", headers=headers)
            soup = BeautifulSoup(full_text_response.content, 'html.parser')

            links = soup.find_all('figure')
            for link in links:
                fig_response= requests.get(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/figure/{link.find('a').get('data-figure-id')}/", headers=headers)
                soup = BeautifulSoup(fig_response.content, 'html.parser')
                results.append({
                    'src': link.find('a').get('href'),
                    'caption': soup.find('div', {'class': 'caption'}).find('strong').get_text()
                })

            return results
        except Exception as e:
            print(f"Error extracting figures for article with PMID={pmid}: {e}")
            return []
    
    def query(self: object, search_term: str, max_results: int = 10) -> list[MetaAnalysis]:
        """
        Qurey articles from PubMed
    
        Parameters:
            search_term (str): Search term on PubMed database
            max_results (int): Maximum number of PMIDs to retrieve
    
        Returns:
            List[MetaAnalysis]: A list of article objects
        """
        results = []

        id_list = self.__query_PMID(search_term, max_results)

        # get article data
        for id in id_list:
            results.append(self.__query_article(id))

        # get article figures
        for article in results:
            article.setFigures(self.__extract_figures_from_article(article))

        # get article supplementary material
        
        return results