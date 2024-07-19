from Bio import Entrez
import requests
from xml.etree import ElementTree
import os
from pathlib import Path
import shutil

"""
使用説明：
code 會先根據獲取的search_keys, 進行搜尋,
它會在給定的meta-analysis pmid所在的資料夾下建立base_references資料夾,
然後將搜尋到的文章下載到base_references資料夾下
之後會檢查key_references資料夾下的pdf是否有缺失, 並將缺失的pdf複製到base_references資料夾下

1. 需要準備search_keys,裡面包含了要搜尋的資料庫和搜尋的query
2. 需要準備meta-analysis pmid, 用於在./data/{pmid}下的合適位置建立資料夾
3. 需要準備meta-analysis年份, 晚於meta-analysis年份的文章將不會被下載
4. 需要準備key_references資料夾, 並創建於./data/{pmid}下, 用於存放meta-analysis的key references
* 注意: 請確保key_references資料夾下的pdf檔案名稱與meta-analysis的key references檔案名稱相同
* 因爲程序是透過檔案名稱來比對是否有缺失的pdf


database: 資料庫名稱
base_dir 默認為 "./data"
query: 也就是搜尋的關鍵字
pmid: meta-analysis的pmid
meta_analysis_year: meta-analysis的年份
retmax: 每次搜索返回的最大結果數量

主要是用到下面的這段code,可以在main.py 去call :

for database, query in search_keys.items():
    if database.lower() in ["medline/ovid", "embase/ovid"]:
        search_and_download(database, query, pmid, base_dir, meta_analysis_year, retmax)
"""

# Sample
Entrez.email = "736650366xu@gmail.com"
search_keys = {
    "Medline/OVID": """("diabetic retinopathy"[Title/Abstract] OR "diabetic retinopathy"[MeSH Terms]) AND ("pregnant"[Title/Abstract] OR "pregnancy"[MeSH Terms]) AND ("clinical trial"[Publication Type] OR "comparative study"[Publication Type] OR "controlled clinical trial"[Publication Type] OR "journal article"[Publication Type] OR "multicenter study"[Publication Type] OR "observational study"[Publication Type] OR "pragmatic clinical trial"[Publication Type] OR "randomized controlled trial"[Publication Type] OR "twin study"[Publication Type]) AND (english[Language]) AND (humans[MeSH Terms])""",
    "EMBASE/OVID": """("diabetic retinopathy"[Title/Abstract] OR "diabetic retinopathy"[MeSH Terms]) AND ("pregnant"[Title/Abstract] OR "pregnancy"[MeSH Terms]) AND ("article"[Publication Type] OR "journal"[Publication Type]) AND (english[Language]) AND (humans[MeSH Terms])""",
    "Scopus": """TITLE-ABS-KEY ("diabetic retinopathy") AND (TITLE-ABS-KEY (pregnant OR pregnancy)) AND (DOCTYPE(ar) AND SRCTYPE(j) AND LANGUAGE(English))"""
}
base_dir = Path("./data")
pmid = "35357410"
meta_analysis_year = "2020"
retmax = 100

# Define search function
def search_pubmed(query, max_year=None, retmax=100):
    params = {
        'db': 'pubmed',
        'term': query,
        'retmax': retmax
    }
    if max_year:
        params['maxdate'] = max_year
    
    handle = Entrez.esearch(**params)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]

# Define function to download full text
def download_full_text(pmid, base_references_dir):
    try:
        # Retrieve detailed information of the article using Entrez API
        handle = Entrez.efetch(db="pubmed", id=pmid, retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        
        article = records["PubmedArticle"][0]
        title = article["MedlineCitation"]["Article"]["ArticleTitle"]
        title = "".join(x for x in title if x.isalnum() or x.isspace()).strip()  # Clean title for use as filename

        # Retrieve PMCID
        pmc_id = None
        for id in article["PubmedData"]["ArticleIdList"]:
            if id.attributes["IdType"] == "pmc":
                pmc_id = id
                break
        
        if not pmc_id:
            return False

        # Construct full-text URL
        full_text_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
        
        # Save PDF
        response = requests.get(full_text_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
        if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
            pdf_path = base_references_dir / f"{title}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            return False
    except Exception as e:
        return False

# Define function to search and download full text
def search_and_download(database, query, pmid, base_dir, meta_analysis_year, retmax=100):
    results = search_pubmed(query, max_year=meta_analysis_year, retmax=retmax)

    # Check if directory matching the pmid exists
    pmid_dir = Path(base_dir) / str(pmid)
    if not pmid_dir.exists():
        return

    # Create base_references subdirectory
    base_references_dir = pmid_dir / "base_references"
    base_references_dir.mkdir(parents=True, exist_ok=True)

    for pmid in results:
        download_full_text(pmid, base_references_dir)

    # Check and copy missing PDFs from key_references to base_references
    check_and_copy_key_references(pmid_dir)

# Define function to check and copy PDFs from key_references to base_references
def check_and_copy_key_references(pmid_dir):
    key_references_dir = pmid_dir / "key_references"
    base_references_dir = pmid_dir / "base_references"

    if not key_references_dir.exists():
        return

    for pdf_file in key_references_dir.glob("*.pdf"):
        target_file = base_references_dir / pdf_file.name
        if not target_file.exists():
            shutil.copy2(pdf_file, target_file)

# Execute search and download full text for each database in search_keys
for database, query in search_keys.items():
    if database.lower() in ["medline/ovid", "embase/ovid"]:
        search_and_download(database, query, pmid, base_dir, meta_analysis_year, retmax)