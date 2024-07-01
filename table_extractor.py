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
        title = ' '.join(word['text'] for word in words if word['top'] == top_pos)
        return title if title else None
    return None

def extract_table(pdf_path: str, writer: pd.ExcelWriter, count: int):
    """
    Extract tables from a PDF file and save them into an Excel sheet.

    Parameters:
    pdf_path (str): The path to the PDF file.
    writer (pd.ExcelWriter): The Excel writer object to save sheets.
    count (int): The count for naming the output sheet.
    """
    key_words = ['quality', 'risk of bias', 'included']
    with pdfplumber.open(pdf_path) as pdf:
        is_find = False
        result = pd.DataFrame()

        for page in pdf.pages:
            words = page.extract_words()
            for table in page.extract_tables():
                title = get_title(words)
                if title and any(keyword in title.lower() for keyword in key_words):
                    # print(f"Found title: {title}")
                    is_find = True
                    result = pd.DataFrame(table[1:], columns=table[0])
                    break  # Assume we only need the first matching table per page

        sheet_name = f"paper_{count}" if is_find else f"paper_{count}(None)"
        
        # Ensure at least one worksheet is created
        if result.empty:
            result = pd.DataFrame({"Message": ["No relevant tables found"]})

        # print(f"Writing to sheet: {sheet_name} with {len(result)} records")
        result.to_excel(writer, sheet_name=sheet_name, index=False)

def read_dir(base_dir: str = './data', output_file: str = 'output.xlsx'):
    """
    Read the specified base directory and process each PDF file found in 'supp' subdirectories.

    Parameters:
    base_dir (str): The base directory to search for PDF files.
    output_file (str): The path to save the output Excel file.
    """
    count = 1
    with pd.ExcelWriter(output_file) as writer:
        for root, dirs, files in os.walk(base_dir):
            if 'supp' in dirs:
                supp_path = os.path.join(root, 'supp')
                pdf_files = [f for f in os.listdir(supp_path) if f.lower().endswith('.pdf')]
                for pdf in pdf_files:
                    pdf_path = os.path.join(supp_path, pdf)
                    # print(f"Processing: {pdf_path}")
                    extract_table(pdf_path, writer, count)
                    count += 1
    # print(f"Excel file saved to {output_file}")

