from crawler import Crawler
import os
from dotenv import load_dotenv

load_dotenv()
PUBMED_API_KEY = os.environ['PUBMED_API_KEY']

crawler = Crawler()

list = crawler.query(search_term="Meta analysis JAMA eye disease", max_results=10, api_key=PUBMED_API_KEY)
crawler.download(list)