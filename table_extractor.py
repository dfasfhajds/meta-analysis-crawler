import pdfplumber
import pandas as pd
import os
from typing import List, Dict, Optional
from ai_tool import get_quality_related_sections

def get_title(words: List[Dict[str, str]], top_pos_list: List[float]) -> Optional[tuple[str, float]]:
    """
    Get the title of the table from the list of words.

    Parameters:
        words (List[Dict[str, str]]): List of words extracted from a PDF page.
        top_pos_list (List[float]): List of top positions that have already been processed.

    Returns:
        Optional[Tuple[str, float]]: A tuple containing the title of the table and its top position,
                                     or None if no title is found.
    """
    for word in words:
        if "eTable" in word['text']:
            top_pos = word['top']
            if top_pos in top_pos_list:
                continue
            else:
                title = " ".join(w['text'] for w in words if w['top'] == top_pos)
                if title:
                    top_pos_list.append(top_pos)
                    return title, top_pos
    return None

def extract_table(pdf_path: str, pmid: str, csv_path: str):
    """
    Extract tables from a PDF file and save them into CSV files in the article directory.

    Parameters:
        pdf_path (str): The path to the PDF file.
        pmid (str): Article PMID.
        csv_path (str): Path for CSV.
    """
    keywords = get_quality_related_sections(read_all_titles(pdf_path))

    # print(f"the keywords for {pmid} are :{keywords}")

    with pdfplumber.open(pdf_path) as pdf:
        table_title = None
        all_tables = []  # Used to store all matching tables
        
        for page in pdf.pages:
            words = page.extract_words()
            top_pos_list = []  # Initialize an empty list for top positions
            for table in page.extract_tables():
                title_result = get_title(words, top_pos_list)
                if title_result:
                    current_title, top_pos = title_result
                    if top_pos not in top_pos_list:
                        top_pos_list.append(top_pos)  # Add the top position to the list
                else:
                    continue

                if any(keyword in current_title.lower() for keyword in keywords):
                    print(f"keyword found in title - {pmid}")
                    table = [[cell.replace('\n', ' ') if cell else cell for cell in row] for row in table]
                    table_title = current_title
                    df = pd.DataFrame(table[1:], columns=table[0])
                    all_tables.append((table_title, df))  # Add table and title to all_tables list

        # Write all tables to a single Excel file
        if all_tables:
            with pd.ExcelWriter(f"{csv_path}/{pmid}.xlsx") as writer:
                for title, df in all_tables:
                    sheet_name = title.split('.')[0].replace(' ', '_')
                    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1)
                    writer.sheets[sheet_name].cell(1, 1, title)
        else:
            # If no data, create an empty sheet
            empty_df = pd.DataFrame()
            empty_filename = f"{pmid}_empty"
            with pd.ExcelWriter(f"{csv_path}/{empty_filename}.xlsx") as writer:
                empty_df.to_excel(writer, sheet_name=empty_filename, index=False)

def read_table(base_dir: str = "./data"):
    """
    Read the specified base directory and process each PDF file found in 'supp' subdirectories.

    Parameters:
        base_dir (str): The base directory to search for PDF files.
    """
    for root, dirs, files in os.walk(base_dir):
        if "supp" in dirs:
            pmid = os.path.basename(root)
            supp_path = os.path.join(root, "supp")
            pdf_files = [f for f in os.listdir(supp_path) if f.lower().endswith(".pdf")]
            for pdf in pdf_files:
                pdf_path = os.path.join(supp_path, pdf)
                extract_table(pdf_path, pmid, root)

def read_all_titles(pdf_path: str):
    """
    Read all table titles in the PDF for AI analysis

    Parameters:
        pdf_path: The path to the PDF file

    Return:
        titles: A string containing all table titles, each separated by a newline character
    """
    with pdfplumber.open(pdf_path) as pdf:
        titles = []

        for page in pdf.pages:
            if page.page_number == 1:
                continue

            text = page.extract_text()
            lines = text.split('\n')

            for line in lines:
                if line.startswith("eTable"):
                    titles.append(line)

        return "\n".join(titles)
