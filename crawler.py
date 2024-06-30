import requests
from xml.etree import ElementTree
from bs4 import BeautifulSoup
from document import MetaAnalysis
from pathlib import Path
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
import json

class Crawler:
    """Wrapper of PubMed MetaAnalysis Crawler"""

    headers = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"}

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

            reference_list = []
            reference_list_element = xml_response.find(".//ReferenceList")
            for reference_element in reference_list_element:
                ref_doi = reference_element.find(".//ArticleId[@IdType='doi']")
                ref_pmid = reference_element.find(".//ArticleId[@IdType='pubmed']")
                reference_list.append({
                    'citation': reference_element.find(".//Citation").text,
                    'doi': ref_doi.text if ref_doi is not None else None,
                    'pmid': ref_pmid.text if ref_pmid is not None else None
                })

            doc = MetaAnalysis(
                pmid=pmid,
                pmcid=pmc,
                title=title,
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                abstract=abstract,
                publication_date=date,
                reference_list=reference_list
            )

            return doc
        except Exception as e:
            # print(f"Error extracting article with PMID={pmid}: {e}")
            return None
        
    def __extract_figures_from_article(self: object, pmid: str, pmcid: str) -> list:
        """
        Extract figures (src, caption) of a article with its PMID and PMCID
    
        Parameters:
            pmid (str): Article PMID
            pmcid (str): Article PMCID
    
        Returns:
            List: Figure list
        """
        try:
            results = []
            full_text_response = requests.get(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}", headers=self.headers)
            soup = BeautifulSoup(full_text_response.content, 'html.parser')

            links = soup.find_all('figure')
            for link in links:
                fig_id = link.find('a').get('data-figure-id')
                if fig_id:
                    fig_response = requests.get(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/figure/{fig_id}/", headers=self.headers)
                    soup = BeautifulSoup(fig_response.content, 'html.parser')
                    caption_div = soup.find('div', {'class': 'caption'})
                    caption = caption_div.find('strong').get_text() if caption_div else ""
                    src = link.find('a').get('href')
                    results.append({
                        'path': f'./data/{pmid}/figures/{src.split("/")[-1]}',
                        'src': src,
                        'caption': caption
                    })

            return results
        except Exception as e:
            # print(f"Error extracting figures for article with PMID={pmid}: {e}")
            return []
        
    def __extract_supplementary_materials_url(self: object, pmid: str, pmcid: str) -> list:
        """
        Extract supplementary materials (url) of an article with its PMCID
    
        Parameters:
            pmid (str): Article PMID
            pmcid (str): Article PMCID
    
        Returns:
            List: list of supplementary material urls
        """
        url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}"
        keywords = ['quality', 'assess', 'assessment', 'risk', 'bias', 'publication', 'search', 'funnel', 'forest', 'newcastle', 'ottawa', 'STROBE', 'PRISMA']
        try:
            results = []
            full_text_response = requests.get(url=url, headers=self.headers)
            soup = BeautifulSoup(full_text_response.content, 'html.parser')

            for suppmat in soup.find('dd', { 'id': 'data-suppmats' }).children:
                for caption in suppmat.find('div', { 'class': ['caption', 'half_rhythm'] }).children:
                    if any(word in caption.text.lower() for word in keywords):
                        src = 'https://www.ncbi.nlm.nih.gov' + suppmat.find('a', { 'data-ga-action': 'click_feat_suppl' }).get('href')
                        results.append({
                            'path': f'./data/{pmid}/supp/{src.split("/")[-1]}',
                            'src': src
                        })
                        break

            return results
        except Exception as e:
            # print(f"Error extracting supplementary materials URL from {url}: {e}")
            return []

    def query(self: object, 
              search_term: str, 
              max_results: int = 10, 
              max_year: int = 2023, 
              min_year: int =2012) -> list[MetaAnalysis]:
        """
        Query articles from PubMed
    
        Parameters:
            search_term (str): Search term on PubMed database
            max_results (int): Maximum number of articles to retrieve
    
        Returns:
            List[MetaAnalysis]: A list of article objects
        """
        print("Begin query")
        results = []
        start = 0
        while len(results) < max_results:
            id_list = self.__query_PMID(search_term, max_results - len(results), start, max_year, min_year)
            if not id_list:
                break  # No more articles to fetch

            for id in id_list:
                article = self.__query_article(id)
                if article is None:  # skip articles with missing data
                    continue
                if "meta-analysis" in article['title'].lower():
                    results.append(article)
                    print(f"Extracted article info for PMID={id}")

            start += len(id_list)

        # get article figures
        for article in results:
            figure_list = self.__extract_figures_from_article(article['pmid'], article['pmcid'])
            article.set_figures(figure_list)
            print(f"Extracted {len(figure_list)} figures for PMID={article['pmid']}")

        # get article supplementary material
        for article in results:
            supp_list = self.__extract_supplementary_materials_url(article['pmid'], article['pmcid'])
            article.set_supplementary_materials(supp_list)
            print(f"Extracted {len(supp_list)} supplementary materials for PMID={article['pmid']}")

        print(f"End query, extracted {len(results)} articles")
        return results

    def download(self: object, list: list[MetaAnalysis]):
        """
        Download all files associated with the list of meta-analysis and generate json file
    
        Parameters:
            list (List[MetaAnalysis]): list of meta-analysis objects
        """
        print("Begin downloading")
        # create directories
        Path("./data").mkdir(exist_ok=True)
        for article in list:
            Path(f"./data/{article['pmid']}").mkdir(exist_ok=True)
            Path(f"./data/{article['pmid']}/figures").mkdir(exist_ok=True)
            Path(f"./data/{article['pmid']}/supp").mkdir(exist_ok=True)
            Path(f"./data/{article['pmid']}/studies").mkdir(exist_ok=True)

        # export data to json file
        with open("./data/data.json", "w", encoding="utf-8") as f:
          json.dump({ 'data': list }, f, ensure_ascii=False, indent = 4)

        # generate list of urls and associated paths
        urls = []
        paths = []
        for article in list:
            for supp in article['supplementary_materials']:
                urls.append(supp['src'])
                paths.append(supp['path'])

            for figure in article['figures']:
                urls.append(figure['src'])
                paths.append(figure['path'])

        inputs = zip(urls, paths)

        def download_url(args): 
            url, fn = args[0], args[1] 
            try: 
                r = requests.get(url, headers=self.headers) 
                with open(fn, "wb") as f: 
                    f.write(r.content) 
                return url
            except Exception as e: 
                # print('Exception in download_url():', e)
                return None

        # download in parallel
        results = ThreadPool(cpu_count() - 1).imap_unordered(download_url, inputs)
        for result in results: 
            print("Downloaded: " + result)
        print("Download completed")