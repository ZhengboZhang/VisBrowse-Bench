import argparse
import json
import jsonlines
import re
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from transformers import AutoProcessor
from tool_util import tools, tools_map
from prompt import SYSTEM_PROMPT, INPUT_PROMPT
import requests
import base64
from PIL import Image
from io import BytesIO

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

class VisBrowse:
    def __init__(self, 
                base_url='http://0.0.0.0:8001/v1', 
                api_key='EMPTY'):

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.max_steps = 15
    
    def run_main(self, sample):

        images = sample['image']
        str_url = ""
        for image in images:
            str_url += "your_repository" + image + ', '

        messages = [dict(
                        role="system",
                        content=[
                            {
                                "type": "text",
                                "text": SYSTEM_PROMPT,
                            }
                        ]
                    ),
                    dict(
                        role="user",
                        content=[
                            {
                                "type": "text",
                                "text": INPUT_PROMPT.replace("{Image_url}", str_url).replace("{Question}", sample['question']),
                            },
                        ]
                    )]
        for image in images:
            messages[1]['content'].append({
                'type': 'image_url',
                'image_url': {
                    'url': "your_repository" + image
                }
            })

        max_steps = self.max_steps
        while True:
            ## assistant
            gen_times = 10
            while True:
                if gen_times < 0:
                    return 'time_out', messages, 'No answer'
                try:
                    response = self.client.chat.completions.create(
                        model=os.getenv('MODEL_NAME', ''),
                        messages=messages,
                        stream=False,
                        temperature=1,
                        tools=tools,
                        tool_choice="auto",
                    )
                    response_message = response.choices[0].message
                    response_content = response_message.content
                    tool_calls = response_message.tool_calls

                    # break
                    if response_content or tool_calls:
                        break
                    else:
                        raise Exception('model failed, retrying...')
                except Exception as e:
                    print(e)
                    gen_times -= 1

            messages.append(response_message.model_dump())

            pattern = r'<answer>(.*?)</answer>'
            match = re.search(pattern, response_content, re.DOTALL)
            if match:
                answer = match.group(1)
                return 'answer', messages, answer
            if max_steps==0:
                return 'time_out', messages, 'No answer'
            
            flag = True
            if tool_calls:
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    if function_name == '':
                        messages.append(
                            {
                                "role": "user",
                                "content": [{"type": "text", "text": "Please use the correct tool call format"}],
                            }
                        )
                        flag = False
                        break
                    function_to_call = tools_map[function_name]
                    
                    function_args = json.loads(tool_call.function.arguments)

                    function_response = function_to_call(
                        params=function_args
                    )
                    print("#"*20)
                    print("tool_name: ", function_name)
                    print("tool_response: ", function_response)
                    print("#"*20)
                    
                    if function_name in ['image_search', 'reverse_image_search']:
                        user_content = []

                        ## content
                        images_urls = re.findall(r"Image: (.*?), Title:", function_response)
                        web_titles = re.findall(r"Title: (.*?), Webpage Url:", function_response)
                        web_urls = re.findall(r"Webpage Url: (.+?)(?:\n|$)", function_response, re.MULTILINE)
                        
                        if len(images_urls)>0:
                            for title, image_url, web_url in zip(web_titles, images_urls, web_urls):

                                data_url = self.url_to_base64(image_url)
                                if data_url == None:
                                    continue

                                user_content.append({
                                    'type': 'text',
                                    'text': f"The title of webpage: {title} \n Image:"
                                })
                                user_content.append({
                                    'type': 'image_url',
                                    'image_url': {
                                        'url': data_url
                                    }
                                })
                                user_content.append({
                                    'type': 'text',
                                    'text': f"The url of image: {image_url} \n"
                                })
                                user_content.append({
                                    'type': 'text',
                                    'text': f"The url of webpage: {web_url}"
                                })
                        if len(user_content) == 0:
                            user_content.append({
                                'type': 'text',
                                'text': function_response
                            })
                        
                    elif function_name in ['text_search','visit']:
                        user_content=[{
                            'type': 'text',
                            'text': function_response
                        }]

                    elif function_name in ['image_crop']:
                        user_content = []
                        user_content.append({
                            'type': 'image_url',
                            'image_url': {
                                'url': function_response
                            }
                        })
                        user_content.append({
                            'type': 'text',
                            'text': f"The url of cropped image: {function_response}"
                        })

                    else:
                        user_content = [{
                            'type': 'text',
                            'text': 'Please use valid tool or answer the question.'
                        }]
                    

            if flag:
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": user_content,
                    }
                )
            max_steps -= 1
            if max_steps == 0:
                messages.append(
                    {
                        "role": "user",
                        "content": [{
                            'type': 'text',
                            'text': 'You must answer now based on the information gathered, and put answer in <answer> ... </answer> tags' 
                        }],
                    }
                )

    def url_to_base64(self, url, mime_type=None):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            image_content = response.content

            if mime_type is None:
                img = Image.open(BytesIO(image_content))
                mime_type = f"image/{img.format.lower()}" if img.format else "image/jpeg"

            base64_str = base64.b64encode(image_content).decode('utf-8')

            data_url = f"data:{mime_type};base64,{base64_str}"
            
            return data_url
        except Exception as e:
            return None
    
    def infer(self, sample):
        try:
            status, messages, content = self.run_main(sample)
        except Exception as e:
            sample["response"] = e
            sample["gen"] = 'No Answer'
            print(e)
            return sample

        sample["response"] = messages
    
        sample["gen"] = content

        return sample

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--output_path", type=str, required=True)
    parser.add_argument("--data_path", type=str, required=True)
    args = parser.parse_args()
        
    output_path = args.output_path
    data_path = args.data_path

    agent = VisBrowse(base_url=BASE_URL, api_key=API_KEY)

    data = []
    with jsonlines.open(data_path) as reader:
        for item in reader:
            data.append(item)
    
    with open(os.path.join(output_path, f"result_{os.getenv('MODEL_NAME', '')}.jsonl"), 'a', encoding='utf-8') as f:
        for sample in tqdm(data):
            answer = agent.infer(sample)
            json_line = json.dumps(answer, ensure_ascii=False)
            f.write(json_line + '\n')