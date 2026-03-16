import os
import re
import json
import time
import random
import requests
import datetime
from typing import Union, List


SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def search_image_query(query: str, retry_attempt=10, timeout=30):

    url = "https://google.serper.dev/images"

    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    data = json.dumps({
        "q": query
    })
    
    for attempt in range(retry_attempt):
        try:
            response = requests.request("POST", url, headers=headers, data=data)
            results = response.json()
            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code} - {response.text}")
            if "images" not in results:
                raise Exception(f"No results found. Use a less specific query.")
            
            search_data = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "image_url": item.get("imageUrl", ""),
                } 
                for item in results['images']
            ]
            return search_data[:3]
        except requests.exceptions.Timeout:
            print(f"Time out (try {attempt + 1}/{retry_attempt}): {query}")
        except Exception as e:
            print(f"Error searching image via query: {str(e)}. Retrying...")

    return []

def parse_image_search_result(search_result):
    search_images = [item.get('image_url', '') for item in search_result]
    search_texts = [item.get('title', '') for item in search_result]
    search_urls = [item.get('url', '') for item in search_result]

    if all(img == '' for img in search_images) or search_images[0] == None:
        if all(text == '' for text in search_texts) or search_texts[0] == None:
            return ([],[],[])
        return ([], search_texts, search_urls)

    return (
        search_texts,
        search_urls,
        search_images,
    )

def image_search(params: Union[str, dict], **kwargs) -> str:
    
    try:
        query = params["query"]
    except:
        return "[Search] Invalid request format: Input must be a JSON object containing 'queries' field"
    
    assert isinstance(query, str)
    search_result = search_image_query(query)

    search_texts, search_urls, search_images = parse_image_search_result(search_result)

    if len(search_images) > 0:
        lines = []
        for img, txt, url in zip(search_images, search_texts, search_urls):
            entry = f"Image: {img}, Title: {txt}, Webpage Url: {url}"
            lines.append(entry)
        contents = "```\n" + '\n\n'.join(lines) + "\n```"
    
    else:
        contents = f"[SearchImage] No image found: {query}"

    return contents 
