import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import List

load_dotenv()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

def get_quality_related_sections(text: str) -> str:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        messages = [
            {
                'role': "system",
                'content': """
                You are particularly good at conducting meta-analysis on medicine articles.
                Based on the provided caption of supplementary materials of a meta-analysis,
                find sections that are related to quality assessment of the included studies.
                Output the captions in a JSON object. 
                Only consider the parts that start with "eTable (this is a number e.g eTable 1.)."
                "eTable." Should not be considered as a quality related section.
                The JSON object must include "qa" field.

                Example:
                {"qa": ["eTable 4. (name_of_the_table)", "eTable 5. (name_of_the_table)"]}
                """
            },
            {
                "role": "user",
                "content": text,
            }
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0
        )

        return json.loads(chat_completion.choices[0].message.content)['qa']

    except Exception as e:
        print(f"Error when prompting gpt-3.5 to find quality related sections: {e}")
        return []
    
def get_key_references_index(text: str) -> List[int]:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        messages = [
            {
                'role': "system",
                'content': """
                You are particularly good at conducting meta-analysis on medicine articles.
                Based on the provided passage of a meta-analysis,
                find the citation numbers of the all included studies.
                Output the captions in a JSON object. 
                The JSON object must include "index" field.

                Example:
                {"index": [1, 2, 3, 4]}
                """
            },
            {
                "role": "user",
                "content": text,
            }
        ]

        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0
        )

        return json.loads(chat_completion.choices[0].message.content)['index']

    except Exception as e:
        print(f"Error when prompting gpt-3.5 to key references: {e}")
        return []