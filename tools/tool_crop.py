import requests
import uuid
import os
from io import BytesIO
from PIL import Image
from typing import Union, List
from huggingface_hub import HfApi
from modelscope.hub.api import HubApi


HF_TOKEN = os.environ.get('HF_TOKEN')
HF_REPO_ID = os.environ.get('HF_REPO_ID')
HF_REPO_TYPE = "dataset"  

def crop_and_upload_to_hf(image_url: str, box: list, padding: float = 0.1):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(image_url, headers=headers, timeout=15)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")

        w, h = img.size
        xmin, ymin, xmax, ymax = box

        pad_w = (xmax - xmin) * w * padding
        pad_h = (ymax - ymin) * h * padding
        
        left = max(0, int(xmin * w - pad_w))
        top = max(0, int(ymin * h - pad_h))
        right = min(w, int(xmax * w + pad_w))
        bottom = min(h, int(ymax * h + pad_h))
        
        cropped_img = img.crop((left, top, right, bottom))

        img_buffer = BytesIO()
        cropped_img.save(img_buffer, format="JPEG", quality=95)
        img_buffer.seek(0) 
        
        api = HubApi()
        api.login(access_token=HF_TOKEN)
        
        filename = f"crops/{uuid.uuid4().hex}.jpg"
        
        api.upload_file(
            path_or_fileobj=img_buffer,
            path_in_repo=filename,
            repo_id=HF_REPO_ID,
            repo_type=HF_REPO_TYPE,
            commit_message=f"Agent auto-crop: {filename}"
        )
        
        final_url = f"https://huggingface.co/datasets/{HF_REPO_ID}/resolve/main/{filename}"
        
        return final_url

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def image_crop(params: Union[str, dict], **kwargs):

    try:
        image_url = params["image_url"]
        bbox = params["bbox"]

    except:
        return "[Crop] Invalid request format: Input must be a JSON object containing 'image_url' and 'bbox'"

    search_url = crop_and_upload_to_hf(image_url, bbox)

    return search_url

