from ai_tool import get_search_strategy_related_article, get_quality_related_articles

def judge_search_strategy(caption: str):
    """
    Judge weather the pdf file satisfies the requirements.

    Parameters:
        caption: The caption of the pdf file which is located at the first page.
    """
    result = get_search_strategy_related_article(caption)
    return result

def has_quality_assessment(caption: str):
    """
    Judge weather the pdf file satisfies the requirements.

    Parameters:
        caption: The caption of the pdf file which is located at the first page.
    """
    result = get_quality_related_articles(caption)
    return result

#base_dir = "./data"
#read_table(base_dir)

#path = "data/36194412/supp/jamanetwopen-e2234459-s002.pdf"
#print(read_caption(path))
