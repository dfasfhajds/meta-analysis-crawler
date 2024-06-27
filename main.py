from crawler import Crawler
from document import MetaAnalysis
import json

crawler = Crawler()

list = crawler.query(search_term="Meta analysis JAMA eye disease", max_results=2)

# export data to json file
with open('data.json', 'w') as f:
  json.dump({ 'data': list }, f, ensure_ascii=False, indent = 4)