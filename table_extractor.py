import pdfplumber
import pandas as pd
import os
from typing import List, Dict, Optional

def get_title(words: List[Dict[str, str]]) -> Optional[str]:
    """
    Get the title of the table from the list of words.

    Parameters:
        words (List[Dict[str, str]]): List of words extracted from a PDF page.

    Returns:
        Optional[str]: The title of the table or None if no title is found.
    """
    top_pos = next((word['top'] for word in words if "eTable" in word['text']), None)
    if top_pos is not None:
        title = " ".join(word['text'] for word in words if word['top'] == top_pos)
        return title if title else None
    return None

def extract_table(pdf_path: str, pmid: str, csv_path: str, writer: pd.ExcelWriter):
    """
    Extract tables from a PDF file and save them into CSV files in the article directory
    Excel file is also saved for checking

    Parameters:
        pdf_path (str): The path to the PDF file.
        pmid (str): Article PMID
        csv_path (str): path for CSV
        writer (pd.ExcelWriter): The Excel writer object to save sheets.
    """
    keywords = ["quality", "risk of bias", "included"]
    with pdfplumber.open(pdf_path) as pdf:
        table_title = None
        result = pd.DataFrame()

        for page in pdf.pages:
            words = page.extract_words()
            for table in page.extract_tables():
                title = get_title(words)
                if title and any(keyword in title.lower() for keyword in keywords):
                    # print(f"Found title: {title}")
                    table = [[cell.replace('\n',' ') if cell else cell for cell in row] for row in table] # remove '\n' in all cells
                    table_title = title
                    result = pd.DataFrame(table[1:], columns=table[0])
                    break  # Assume we only need the first matching table per page

        filename = f"{pmid}_{table_title.split('.')[0].replace(' ', '_')}" if table_title else f"{pmid}"
        
        # Only create csv in path if table is successfully extracted
        if not result.empty:
            result.to_csv(f"{csv_path}/{filename}.csv", index=False, encoding="utf-8")
            result.to_excel(writer, sheet_name=filename, index=False)
            # print(f"Writing to {csv_path}/{filename}.csv with {len(result)} records")

def read_table(base_dir: str = "./data", output_file: str = "output.xlsx"):
    """
    Read the specified base directory and process each PDF file found in 'supp' subdirectories.

    Parameters:
        base_dir (str): The base directory to search for PDF files.
        output_file (str): The path to save the output Excel file.
    """
    with pd.ExcelWriter(f"{base_dir}/{output_file}") as writer:
        for root, dirs, files in os.walk(base_dir):
            if "supp" in dirs:
                pmid = os.path.basename(root)
                supp_path = os.path.join(root, "supp")
                pdf_files = [f for f in os.listdir(supp_path) if f.lower().endswith(".pdf")]
                for pdf in pdf_files:
                    pdf_path = os.path.join(supp_path, pdf)
                    print(f"Processing: {pdf_path}")
                    extract_table(pdf_path, pmid, root, writer)
    # print(f"Excel file saved to {output_file}")
