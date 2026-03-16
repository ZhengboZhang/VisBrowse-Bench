from tools.tool_text_search import text_search
from tools.tool_reverse_image_search import reverse_image_search
from tools.tool_visit import visit
from tools.tool_image_search import image_search
from tools.tool_crop import image_crop

tools = [
    {
        "type": "function",
        "function": {
            "name": "text_search",
            "description": "Performs batched web searches: supply a 'query'; the tool retrieves the top 5 results for the query in one call.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reverse_image_search",
            "description": "Utilize the image search engine to retrieve relevant information based on the input image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "The url of the image to be searched.",
                    }
                },
                "required": ["image_url"],   
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "visit",
            "description": "visit a webpage and return the summary of webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The url of webpage you want to explore."
                    },
                    "goal": {
                        "type": "string",
                        "description": "The goal of the visit for the webpage."
                    }
                },
                "required": ["url", "goal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "image_search",
            "description": "Performs image search: supply a 'query'; the tool retrieves relevant images and web pages based on the input query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "image_crop",
            "description": "Zoom in on a specific region of an image by cropping it based on a bounding box (bbox) and return the url of cropped image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url": {
                            "type": "string",
                            "description": "The url of origin image."
                    },
                    "bbox": {
                            'type':
                                'array',
                            'items': {
                                'type': 'number'
                            },
                            'minItems':
                                4,
                            'maxItems':
                                4,
                            'description':
                                'The bounding box of the region to zoom in, in the form of a text array of coordinates [xmin, ymin, xmax, ymax], where (xmin, ymin) is the top-left corner and (xmax, ymax) is the bottom-right corner. \
                                These coordinates must be relative position coordinates, ranging from 0 to 1, and rounded to three decimal places.'
                    },
                },
                "required": ["image_url", "bbox"]
            }
        }
    }
]

tools_map = {
    'text_search': text_search,
    'reverse_image_search': reverse_image_search,
    'visit': visit,
    'image_search': image_search,
    'image_crop': image_crop,
}