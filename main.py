from crawler import Crawler
import os
from table_extractor import read_table

crawler = Crawler()

list = crawler.query(search_term="Meta analysis JAMA eye disease", max_results=10, api_key=PUBMED_API_KEY)
crawler.download(list)

read_table("./data") # read table from the pdf files in supplementary file and output the tables as excel format
