import os
from openai import OpenAI

PUBMED_API_KEY = "YOUR_OWN_KEY"
OPENAI_API_KEY = "YOUR_OWN_KEY"

def load_dotenv(text: str):
    """
    Connect to openai, and filter meta-analysis articles that meet the requirements
    Args:
        text (str): The caption of the file

    Returns:
        return VALUE1 if the article has quality assessment, otherwise return VALUE2 
    """
    try:
        client = OpenAI(api_key = OPENAI_API_KEY)
        prompt = "YOUR_OWN_PROMPT"
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "assistant",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": text,
                }
            ],
            model="gpt-3.5-turbo",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error when prompting gpt-3.5 to find quality related sections: {e}")
        return []
