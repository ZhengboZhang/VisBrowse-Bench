import os
import re
import json
import time
import random
import requests
import datetime
from typing import Union, List
from functools import wraps


SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def google_search(query: str):
    url = 'https://google.serper.dev/search'
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json',
    }
    data = {
        "q": query,
        "num": 5,
        "extendParams": {
            "country": "en",
            "page": 1,
        },
    }

    for i in range(5):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            results = response.json()
            break
        except Exception as e:
            print(e)
            if i == 4:
                return f"Google search Timeout, return None, Please try again later."
        
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} - {response.text}")

    try:
        if "organic" not in results:
            raise Exception(f"No results found for query: '{query}'. Use a less specific query.")

        web_snippets = list()
        idx = 0
        if "organic" in results:
            for page in results["organic"]:
                idx += 1
                date_published = ""
                if "date" in page:
                    date_published = "\nDate published: " + page["date"]

                source = ""
                if "source" in page:
                    source = "\nSource: " + page["source"]

                snippet = ""
                if "snippet" in page:
                    snippet = "\n" + page["snippet"]

                redacted_version = f"{idx}. [{page['title']}]({page['link']}){date_published}{source}\n{snippet}"

                redacted_version = redacted_version.replace("Your browser can't play this video.", "")
                web_snippets.append(redacted_version)

        content = f"A Google search for '{query}' found {len(web_snippets)} results:\n\n## Web Results\n" + "\n\n".join(web_snippets)
        return content
    except:
        return f"No results found for '{query}'. Try with a more general query, or remove the year filter."

def text_search(params: Union[str, dict], **kwargs) -> str:
    
    try:
        query = params["query"]
    except:
        return "[Search] Invalid request format: Input must be a JSON object containing 'queries' field"
    
    assert isinstance(query, str)

    response = google_search(query)

    return response