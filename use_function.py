import pdfplumber
from typing import List, Dict, Optional, Tuple

def get_title(words: List[Dict[str, str]]) -> Optional[str]:
    """
    Get the title of the table from the list of words.

    Parameters:
        words (List[Dict[str, str]]): List of words extracted from a PDF page.
        top_pos_list (List[float]): List of top positions that have already been processed.

    Returns:
        Optional[Tuple[str, float]]: A tuple containing the title of the table and its top position,
                                     or None if no title is found.
    """
    top_pos = next((word['top'] for word in words if "Table" in word['text']), None)
    if top_pos is not None:
        title = " ".join(word['text'] for word in words if word['top'] == top_pos)
        return title if title else None
    return None


def merge_tables(tables: list[list]):
    """
    Merge the tables into one table
    
    Parameters:
        tables: one table is divided into several tables by page
    """

    if len(tables) == 1:
        return tables
    else:
        column_titles = tables[0][0]
        result = [column_titles]
        for table in tables:  
                for row in table:
                    if row == column_titles:
                        continue
                    else:
                        result.append(row)       
    return result

def merge_tables_in_txt(tables: list[list]):
    """
    Merge the tables into one table in txt format
    
    Parameters:
        tables: one table is divided into several tables by page
    """

    text = ''
    for table in tables:  
            for row in table:
                for content in row:
                    if content:
                        text = text + content + ' '
                    else:
                        text = text + '^ '
                text += '\n'      
    return text

def read_caption(pdf_path: str):
    """
        Read the caption in supplementary for AI analysis
        
        Parameters:
            pdf_path: The path to the PDF file
        
        Return:
            caption: The caption of supplementary
    """
    with pdfplumber.open(pdf_path) as pdf:
        caption = ''
        page_num = 0
        # Get the caption of the file which is located in the first page 
        for page in pdf.pages:
            page_num += 1
            if page_num == 1:
                caption = caption + page.extract_text()
        return caption
