import json 
import os
import sys
import numpy as np
import faiss
from dotenv import load_dotenv
import google.genai as genai
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()
client = genai.Client()
def embed(text: str) -> np.ndarray:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return np.array(result.embeddings[0].values, dtype="float32")

with open("storage/menu.json", "r") as f:
    menu = json.load(f)

index = faiss.read_index("storage/menu.index")

def recommend(query: str, k: int = 3):
    query_embedding = embed(query)
    
    query_vector = np.array([query_embedding], dtype="float32")
    faiss.normalize_L2(query_vector)
    
    distances, indices = index.search(query_vector, k)
    results = []
    for i, (idx, score) in enumerate(zip(indices[0], distances[0])):
        results.append({
            "rank": i + 1,
            "name": menu[idx]["name"],
            "price": menu[idx]["price"],
            "match": f"{score * 100:.0f}%"
        })
    return results
