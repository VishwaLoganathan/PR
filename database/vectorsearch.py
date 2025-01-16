from pinecone import Pinecone
from embedding.embedding import embeddingprocess
from flask import jsonify
import os
import json
from dotenv import load_dotenv
load_dotenv()
 
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_host = "https://material-master-x2jalxr.svc.aped-4627-b74a.pinecone.io"
 
 
 
def search_products(query):
    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index("material-master")
    query1 = query
    query_embedding = embeddingprocess(query1)
    results = index.query(
    vector=query_embedding,
    top_k=1,
    include_metadata=True
    )
    id = results.get('matches')[0].get('id')
    print(id[10:-2])
    print(f'id: {id}')
    genre = results.get('matches')[0]['metadata'].get('materialDescription')
    print(f'description: {genre}') 
    json_format={"materialid":id,"materialDescription":genre} 
    return json_format
 
