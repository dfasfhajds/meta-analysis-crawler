from crawler import Crawler

crawler = Crawler()

list = crawler.query(search_term="Meta analysis JAMA eye disease", max_results=10)
crawler.download(list)