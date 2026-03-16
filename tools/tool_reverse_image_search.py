import os
import argparse
import requests
import json
from tqdm import tqdm
from io import BytesIO
import re
import random
import string
from pathlib import Path
from functools import wraps
import atexit
import logging
import subprocess
from urllib.parse import quote
import hashlib
import base64

SERPER_API_KEY = os.getenv('SERPER_API_KEY')



def search_by_image_url(download_url, img_save_path=None, byte=True, retry_attempt=10, timeout=30):

    url = "https://google.serper.dev/lens"

    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }

    data = json.dumps({
        "url": download_url
    })

    results = {}
    
    for attempt in range(retry_attempt):
        try:
            response = requests.request("POST", url, headers=headers, data=data)
            results = response.json()
            if response.status_code != 200:
                raise Exception(f"Error: {response.status_code} - {response.text}")
            if "organic" not in results:
                raise Exception(f"No results found. Use a less specific query.")
            
            search_data = [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "image_url": item.get("imageUrl", ""),
                    # "source": item.get("source", "")
                }
                for item in results['organic']
            ]
            return search_data[:3]
        except requests.exceptions.Timeout:
            print(f"Time out (try {attempt + 1}/{retry_attempt}): {download_url}")
        except Exception as e:
            print(f"Error searching image via URL: {str(e)}. Retrying...")
            
    
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

def reverse_image_search(params, messages=None, img_save_path=None, byte=False, **kwargs):
    try:
        assert isinstance(params, dict)
        image_url = params.get("image_url") or params.get("image")
    except:
        return "Invalid request format: Input must be a DICT containing 'image_urls' field"        


    search_result = search_by_image_url(image_url, img_save_path, byte)
    
    search_texts, search_urls, search_images = parse_image_search_result(search_result)
    

    if len(search_images) > 0:
        lines = []
        for img, txt, url in zip(search_images, search_texts, search_urls):
            entry = f"Image: {img}, Title: {txt}, Webpage Url: {url}"
            lines.append(entry)
        contents = "```\n" + '\n\n'.join(lines) + "\n```"

    elif len(search_images) == 0 and len(search_texts) > 0:
        lines = []
        for txt, url in zip(search_texts, search_urls):
            entry = f"Title: {txt}, Webpage Url: {url}"
            lines.append(entry)
        contents = "```\n" + '\n\n'.join(lines) + "\n```"
    
    else:
        contents = f"No image found: {search_images}, {search_texts}, {search_result}"
        
    return contents    
