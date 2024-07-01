import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

def get_quality_related_sections(html: str) -> list[int]:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        messages=[
            {
                'role': "system",
                'content': """
                Based on the provided caption of supplementary materials of a meta-analysis,
                find sections that are related to quality assessment of the included studies.
                Output the captions in a JSON object.
                The JSON object must include "qa" field.

                Example:
                {"qa": ["eTable 4", "eTable 5"]}
                """
            },
            {
                "role": "user",
                "content": html,
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