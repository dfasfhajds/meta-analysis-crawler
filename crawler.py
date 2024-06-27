import requests
from xml.etree import ElementTree
from bs4 import BeautifulSoup
from document import MetaAnalysis

class Crawler:
    """Wrapper of PubMed MetaAnalysis Crawler"""

    def __init__(self):
        pass

    def __query_PMID(self: object, 
                     search_term: str, 
                     max_results: int = 10, 
                     start: int = 0, 
                     max_year: int = 2023, 
                     min_year: int =2012) -> list:
        """
        Retrieve the article PMIDs for a query
    
        Parameters:
            search_term (str): Search term on PubMed database
            max_results (int): Maximum number of PMIDs to retrieve
            start (int): Starting index for the results
    
        Returns:
            list: A list of PMIDs
        """
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={search_term}&retmax={max_results}&retstart={start}&retmode=xml&maxdate={max_year}&mindate={min_year}"
        search_response = requests.get(search_url)
        search_tree = ElementTree.fromstring(search_response.content)

        return [e.text for e in search_tree.find("IdList").findall("Id")]

    def __query_article(self: object, pmid: str) -> MetaAnalysis:
        """
        Retrieve the article information with its PMID
    
        Parameters:
            pmid (str): Article PMID
    
        Returns:
            MetaAnalysis: Article object
        """
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
        response = requests.get(url)
        xml_response = ElementTree.fromstring(response.content)

        try:
            title = xml_response.find(".//ArticleTitle").text
            doi = xml_response.find(".//ArticleId[@IdType='doi']").text
            journal = xml_response.find(".//Journal/Title").text
            pmc = xml_response.find(".//ArticleId[@IdType='pmc']").text
            full_text_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}"

            abstract_elements = xml_response.findall(".//AbstractText")
            abstract = ''.join([f"""## {a.attrib['Label']}\n{a.text}\n""" for a in abstract_elements])
            
            date_element = xml_response.find(".//PubMedPubDate[@PubStatus='pubmed']")
            date = f"{date_element.find('.//Year').text}/{date_element.find('.//Month').text}/{date_element.find('.//Day').text}"

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
                full_text_url=full_text_url,
                authors=authors,
                doi=doi,
                journal=journal,
                abstract=abstract,
                publication_date=date
            )

            return doc
        except Exception as e:
            print(f"Error extracting article with PMID={pmid}: {e}")
            return None
        
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
                fig_id = link.find('a').get('data-figure-id')
                if fig_id:
                    fig_response = requests.get(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/figure/{fig_id}/", headers=headers)
                    soup = BeautifulSoup(fig_response.content, 'html.parser')
                    caption_div = soup.find('div', {'class': 'caption'})
                    caption = caption_div.find('strong').get_text() if caption_div else ""
                    results.append({
                        'src': link.find('a').get('href'),
                        'caption': caption
                    })

            return results
        except Exception as e:
            print(f"Error extracting figures for article with PMID={pmid}: {e}")
            return []
        
    def __extract_supplementary_materials_url(self: object, url: str) -> list:
        keywords = ['quality', 'assess', 'assessment', 'risk', 'bias', 'publication', 'search', 'funnel', 'forest', 'newcastle', 'ottawa', 'STROBE', 'PRISMA']
        try:
            results = []
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
            full_text_response = requests.get(url=url, headers=headers)
            soup = BeautifulSoup(full_text_response.content, 'html.parser')

            for suppmat in soup.find('dd', { 'id': 'data-suppmats'}).children:
                for caption in suppmat.find('div', { 'class': ['caption', 'half_rhythm'] }).children:
                    if any(word in caption.text.lower() for word in keywords):
                        results.append('https://www.ncbi.nlm.nih.gov' + suppmat.find('a', { 'data-ga-action': 'click_feat_suppl' }).get('href'))
                        break

            return results
        except Exception as e:
            print(f"Error extracting supplementary materials URL from {url}: {e}")
            return []
    
    def query(self: object, search_term: str, max_results: int = 10) -> list[MetaAnalysis]:
        """
        Query articles from PubMed
    
        Parameters:
            search_term (str): Search term on PubMed database
            max_results (int): Maximum number of articles to retrieve
    
        Returns:
            List[MetaAnalysis]: A list of article objects
        """
        results = []
        start = 0
        while len(results) < max_results:
            id_list = self.__query_PMID(search_term, max_results - len(results), start)
            if not id_list:
                break  # No more articles to fetch

            for id in id_list:
                article = self.__query_article(id)
                if article is None:  # skip articles with missing data
                    continue
                if 'meta-analysis' in article['title'].lower():
                    results.append(article)

            start += len(id_list)

        for article in results:
            article.set_figures(self.__extract_figures_from_article(article))

        # get article supplementary material
        for article in results:
            article.set_supplementary_materials(self.__extract_supplementary_materials_url(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{article['pmcid']}"))

        return results
