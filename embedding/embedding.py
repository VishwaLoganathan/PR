import requests
import os


 
embedding_api=os.getenv("JINA_API_KEY")
 
   
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
 