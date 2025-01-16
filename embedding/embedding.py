import requests
import os

Jina_api = "jina_d1f20ceaa138457c8f8fe46db436665b3xRYUXn_hqA5lUuHnlDF9xH5kpGZ"
 
embedding_api=Jina_api  
 
   
def embeddingprocess(text):
   
    headers = {
        "Authorization": f"Bearer {embedding_api}",
        "Content-Type": "application/json",
    }
    payload = {
    "model": "jina-clip-v2",
    "dimensions": 1024,
    "normalized": True,
    "embedding_type": "float",
    "input": [
        {
            "text": text
        }
    ]
}
    response = requests.post("https://api.jina.ai/v1/embeddings", json=payload, headers=headers)
   
    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        raise Exception(f"API Request Failed: {response.status_code}, {response.text}")
 