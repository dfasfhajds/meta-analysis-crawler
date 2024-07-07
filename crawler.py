import requests
from xml.etree import ElementTree
from bs4 import BeautifulSoup
from document import MetaAnalysis
from pathlib import Path
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
import json
import re
import random
from helper import get_pdf_url
from ai_tool import get_key_references_index
import pdfkit
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class Crawler:
    """Wrapper of PubMed MetaAnalysis Crawler"""

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

    def __init__(self):
        pass

    def get_headers(self: object):
        """
        Randomly choose a User-Agent for HTTP headers
    
        Returns:
            HTTP headers
        """
        return {'User-Agent': random.choice(self.user_agents)}

    def __query_PMID(self: object, 
                     search_term: str, 
                     max_results: int = 10, 
                     start: int = 0, 
                     max_year: int = 2023, 
                     min_year: int = 2012,
                     api_key: str = None) -> list[str]:
        """
        Retrieve the article PMIDs for a query
    
        Parameters:
            search_term (str): Search term on PubMed database
            max_results (int): Maximum number of PMIDs to retrieve
            start (int): Starting index for the results
    
        Returns:
            list: A list of PMIDs
        """
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            'db': "pubmed",
            'term': search_term,
            'retmax': max_results,
            'retstart': start,
            'retmode': 'xml',
            'maxdate': max_year,
            'mindate': min_year
        }
        if api_key:
            params['api_key'] = api_key

        response = requests.get(url, params=params, headers=self.get_headers())
        xml_response = ElementTree.fromstring(response.content)

        return [e.text for e in xml_response.find("IdList").findall("Id")]

    def __query_article(self: object, pmid: str, api_key: str = None) -> MetaAnalysis:
        """
        Retrieve the article information with its PMID
    
        Parameters:
            pmid (str): Article PMID
    
        Returns:
            MetaAnalysis: Article object
        """
        try:
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'xml',
            }
            if api_key:
                params['api_key'] = api_key
            response = requests.get(url, params=params, headers=self.get_headers())
            xml_response = ElementTree.fromstring(response.content)

            title = xml_response.find(".//ArticleTitle").text
            doi = xml_response.find(".//ArticleId[@IdType='doi']").text
            journal = xml_response.find(".//Journal/Title").text
            pmc = xml_response.find(".//ArticleId[@IdType='pmc']").text
            full_text_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}"

            abstract_elements = xml_response.findall(".//AbstractText")
            abstract = ''.join([f"""## {a.attrib['Label']}\n{a.text}\n""" for a in abstract_elements])
            
            date_element = xml_response.find(".//PubMedPubDate[@PubStatus='pubmed']")
            date = f"{date_element.find('.//Year').text}/{date_element.find('.//Month').text}/{date_element.find('.//Day').text}"

            studies_index = self.__extract_studies_index(pmc)
            key_references = []
            reference_list_element = xml_response.find(".//ReferenceList")
            for i in studies_index:
                ref_doi = reference_list_element[i-1].find(".//ArticleId[@IdType='doi']")
                ref_pmid = reference_list_element[i-1].find(".//ArticleId[@IdType='pubmed']")
                ref_pmc = reference_list_element[i-1].find(".//ArticleId[@IdType='pmc']")
                key_references.append({
                    'citation': reference_list_element[i-1].find(".//Citation").text,
                    'doi': ref_doi.text if ref_doi is not None else None,
                    'pmid': ref_pmid.text if ref_pmid is not None else None,
                    'pmc': ref_pmc.text if ref_pmc is not None else None
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
                key_references=key_references
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
            full_text_response = requests.get(f"https://pubmed.ncbi.nlm.nih.gov/{pmid}", headers=self.get_headers())
            soup = BeautifulSoup(full_text_response.content, 'html.parser')

            links = soup.find_all('figure')
            for link in links:
                fig_id = link.find('a').get('data-figure-id')
                if fig_id:
                    fig_response = requests.get(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/figure/{fig_id}/", headers=self.get_headers())
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
            full_text_response = requests.get(url=url, headers=self.get_headers())
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

    def __extract_studies_index_from_pmc_table(self: object, pmcid: str) -> list[int]:
        """
        Extract the reference index of the key references from table in full text articles on PMC
    
        Parameters:
            article (MetaAnalysis): Article object
    
        Returns:
            List: list of reference index
        """
        url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}"
        keywords = ["characteristics", "study", "studies", "included", "selection", "selected"]
        try:
            results = []
            full_text_response = requests.get(url, headers=self.get_headers())
            soup = BeautifulSoup(full_text_response.content, "html.parser")

            table_wrappers = soup.find_all("div", { 'class': "table-wrap" })
            for table_wrapper in table_wrappers:
                caption = table_wrapper.find("div", { 'class': "caption" }).find("strong")

                if caption and not any(word in caption.text.lower() for word in keywords):
                    continue

                table = table_wrapper.find("div", { 'class': "xtable" }).find("table")
                for tr in table.find("tbody").find_all("tr"):
                    for td in tr.find_all("td"):
                        try:
                            anchors = td.find_all("a", {'class': "bibr"})
                            for anchor in anchors:
                                rid = anchor.get("rid")
                                if rid:
                                    results.append(int(rid.split("r")[-1]))
                        except Exception as e:
                            continue

            return list(dict.fromkeys(results)) # remove duplicate
        except Exception as e:
            return []

    def __extract_studies_index_from_text(self: object, pmcid: str) -> list[int]:
        """
        Extract the reference index of the key references from the "Results" section
        in the full text articles on PMC using gpt
    
        Parameters:
            article (MetaAnalysis): Article object
    
        Returns:
            List: list of reference index
        """
        url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}"
        keywords = ["characteristics", "study", "studies", "included", "selection", "selected"]
        try:
            full_text_response = requests.get(url, headers=self.get_headers())
            soup = BeautifulSoup(full_text_response.content, "html.parser")

            sections = soup.find_all("div", {'class': "tsec"})
            
            for section in sections:
                subheader = section.find("h2", {'class': "head"})
                if subheader and subheader.text.lower() == "results":
                    for subsection in section.find_all("div", {'class': "sec"}):
                        title = subsection.find("h3")
                        if title and not any(word in title.text.lower() for word in keywords):
                            continue
                        
                        for paragraph in subsection.find_all("p"):
                            anchors = paragraph.find_all("a", {'class': "bibr"})
                            if not anchors:
                                continue
                            return get_key_references_index(paragraph.text)
        except Exception as e:
            return []

    def __extract_studies_index(self: object, pmcid: str) -> list[int]:
        """
        Extract the reference index of the key reference from table in full text articles on PMC
    
        Parameters:
            article (MetaAnalysis): Article object
    
        Returns:
            List: list of reference index
        """
        studies_index = self.__extract_studies_index_from_pmc_table(pmcid)
        if studies_index:
            return studies_index
        
        studies_index = self.__extract_studies_index_from_text(pmcid)
        if studies_index:
            return studies_index
        
        return []

    def query(self: object, 
              search_term: str, 
              max_results: int = 10, 
              max_year: int = 2023, 
              min_year: int = 2012,
              api_key: str = None) -> list[MetaAnalysis]:
        """
        Query articles from PubMed
    
        Parameters:
            search_term (str): Search term on PubMed database
            max_results (int): Maximum number of articles to retrieve
    
        Returns:
            List[MetaAnalysis]: A list of article objects
        """
        print(f"Begin query for '{search_term}'")
        results = []
        start = 0
        while len(results) < max_results:
            id_list = self.__query_PMID(
                search_term=search_term,
                max_results=max_results - len(results),
                start=start,
                max_year=max_year,
                min_year=min_year,
                api_key=api_key
            )
            if not id_list:
                break  # No more articles to fetch

            for id in id_list:
                article = self.__query_article(pmid=id, api_key=api_key)
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
            Path(f"./data/{article['pmid']}/key_references").mkdir(exist_ok=True)

        # export data to json file
        with open("./data/data.json", "w", encoding="utf-8") as f:
            json.dump({ 'data': list }, f, ensure_ascii=False, indent = 4)

        # generate list of urls and associated paths
        urls = []
        paths = []
        for article in list:
            # get supplementary material urls
            for supp in article['supplementary_materials']:
                urls.append(supp['src'])
                paths.append(supp['path'])

            # get figure urls
            for figure in article['figures']:
                urls.append(figure['src'])
                paths.append(figure['path'])

            # get key reference urls
            for ref in article['key_references']:
                dir = f"./data/{article['pmid']}/key_references/"
                url = get_pdf_url(ref['pmc'], ref['doi'], ref['pmid'])
                if url:
                    urls.append(url)

                    if ref['pmc']:
                        paths.append(f"{dir}{ref['pmc']}.pdf")
                    elif ref['doi']:
                        # sanitize doi so that it can be used as filename
                        sanitized_doi = re.sub(r'[/:]', '_', ref['doi'])
                        paths.append(f"{dir}{sanitized_doi}.pdf")
                    elif ref['pmid']:
                        paths.append(f"{dir}PMID{ref['pmid']}.pdf")

        inputs = zip(urls, paths)

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        def download_url(args): 
            url, fn = args[0], args[1] 
            try: 
                if "?report=printable" in url:
                    options = {
                        'margin-top': '0.5in',
                        'margin-right': '0.5in',
                        'margin-bottom': '0.5in',
                        'margin-left': '0.5in',
                        'encoding': "UTF-8",
                        'no-outline': None,
                        'custom-header': [
                            ('User-Agent', self.get_headers()['User-Agent'])
                        ],
                        'no-background': None
                    }
                    pdfkit.from_url(url, fn, options=options)
                else:
                    r = session.get(url, headers=self.get_headers())
                    
                    if not (r.headers.get("content-type") == "application/pdf") and "pdf" in url:
                        return None
                    
                    with open(fn, "wb") as f: 
                        f.write(r.content)
                return url
            except Exception as e: 
                # print('Exception in download_url():', e)
                return None

        # download in parallel
        results = ThreadPool(cpu_count() - 1).imap_unordered(download_url, inputs)
        for result in results: 
            if result:
                print("Downloaded: " + result)
            else:
                print("Download failed")
        print("Download completed")