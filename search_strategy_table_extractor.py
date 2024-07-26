import pdfplumber
import pandas as pd
import os
import codecs
import shutil
import xmltodict
import time
from typing import List, Dict, Optional, Tuple
from judge_validation import judge_search_strategy
from Bio import Entrez
from use_function import get_title, merge_tables_in_txt, read_caption
from ai_tool import judge_strategy, generate_search_strategy
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.environ['EMAIL_ADDRESS']
Entrez.email = EMAIL_ADDRESS

def search(query):
    handle = Entrez.esearch(db="pubmed", term=query, retmax=10)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]

def fetch_details(id_list):
    ids = ",".join(id_list)
    handle = Entrez.efetch(db="pubmed", id=ids, retmode="xml")
    records = Entrez.read(handle)
    handle.close()
    return records

def is_search_strategy_table(title: str, table_type: str) -> str:
    if title == None:
        return '0'
    input_value = f"{table_type} : {title}"
    result = judge_strategy(input_value)    # Use ai to judge whether the title is related to search_strategy
    return result

def get_search_strategy(content: str):
    strategy = generate_search_strategy(content)
    return strategy

def extract_search_strategy_tables(pdf_path: str, pmid: str, table_type: str = "Search Strategy") -> str:
    """
    Extract search strategy tables from a PDF file.

    Parameters:
        pdf_path (str): The path to the PDF file.
        pmid (str): Article PMID.
        
    Return:
        query: The search strategy
    """

    print(f"Reading file: {pmid}")
    final_table = []
    is_find = 0
    finish = 0
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            for table in page.extract_tables():
                title = get_title(words)
                if title and is_search_strategy_table(title, table_type) == '1':
                    is_find = 1
                    final_table.append(table)
                elif is_find == 1:
                    if title == None:
                        final_table.append(table)
                    else:
                        is_find = 0
                        finish = 1
            
            if finish == 1:
                break
        
        content = merge_tables_in_txt(final_table)
        query = get_search_strategy(content)
        return query

def write_to_txt(content: str, path: str):
    """Write content in txt file"""

    if not os.path.exists(f"{path}/search_strategy"):  
        os.makedirs(f"{path}/search_strategy")
    full_path = path + "/search_strategy/search_strategy.txt"
    with open(full_path, 'w', encoding='gbk', errors='replace') as file:
        file.write(content)

def do_query(query: str):
    article_ids = search(query)
    print(f"Found {len(article_ids)} articles.")

    batch_size = 10
    result = ""
    for i in range(0, len(article_ids), batch_size):
        batch_ids = article_ids[i:i + batch_size]
        articles = fetch_details(batch_ids)
        for article in articles["PubmedArticle"]:
            article_dict = xmltodict.parse(Entrez.efetch(db="pubmed", id=article['MedlineCitation']['PMID'], retmode="xml").read())
            article_info = article_dict['PubmedArticleSet']['PubmedArticle']['MedlineCitation']['Article']
            title = article_info['ArticleTitle']
            abstract = article_info.get('Abstract', {}).get('AbstractText', 'No abstract available')
            #print(f"Title: {title}\nAbstract: {abstract}\n")
            result = result + f"Title: {title}\nAbstract: {abstract}\n\n"
            time.sleep(0.5)

    return result

def read_search_strategy_tables(base_dir: str):
    """
    Read the specified base directory and process each PDF file found in 'supp' subdirectories.

    Parameters:
        base_dir (str): The base directory to search for PDF files.
    
    Return:
        total: The number of total read articles
        count: The number of articles that have a search strategy table
    """
    total = 0   #Total number of articles read
    count = 0   #Total number of articles that have search strategy table
    for root, dirs, files in os.walk(base_dir):
        if "supp" in dirs:
            pmid = os.path.basename(root)
            supp_path = os.path.join(root, "supp")
            pdf_files = [f for f in os.listdir(supp_path) if f.lower().endswith(".pdf")]
            for pdf in pdf_files:
                pdf_path = os.path.join(supp_path, pdf)
                print(f"Search Strategy\nroot: {root}, pmid: {pmid}, pdf: {pdf}")
                total += 1
                if judge_search_strategy(read_caption(pdf_path)) == '1':
                    count += 1
                    query = extract_search_strategy_tables(pdf_path, pmid)
                    result = do_query(query)
                    write_to_txt(result, supp_path)
                    output_path = os.path.join(base_dir, 'selected_articles')
                    if not os.path.exists(output_path):  
                        os.makedirs(output_path)
                    if not os.path.exists(os.path.join(output_path, pdf)):
                        shutil.copyfile(pdf_path, os.path.join(output_path, pdf))
    return total, count

# Example usage
#path = "data/jama_eye_disease/31750861/supp/jamaophthalmol-138-50-s001.pdf"
#query = extract_search_strategy_tables(path, "31750861")
#print(query)
#result = do_query(query)
#write_to_txt(result, "data/jama_eye_disease/31750861/supp")
#read_search_strategy_table("./data")
