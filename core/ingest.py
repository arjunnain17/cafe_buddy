import os
import json
import numpy as np 
import faiss    
import google.genai as genai
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
client = genai.Client()

from data.menu import menu

descriptions = [item["description"] for item in menu]

def embed(text: str) -> np.ndarray:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return np.array(result.embeddings[0].values, dtype="float32")
print("Embedding descriptions....")

embeddings = []
for i, desc in enumerate(descriptions):
    print(f"  Embedding {i+1}/{len(descriptions)}...")
    embeddings.append(embed(desc))

embeddings = np.array(embeddings, dtype="float32")
# Normalize
faiss.normalize_L2(embeddings)

# Build index
dimension = embeddings.shape[1]  # should be 768
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)
print(f"Index built with {index.ntotal} vectors.")

# Save FAISS index
faiss.write_index(index, "storage/menu.index")
print("FAISS index saved.")

# Save metadata
metadata = [
    {"id": item["id"], "name": item["name"], "price": item["price"]}
    for item in menu
]
with open("storage/menu.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("Metadata saved.")
print("Ingestion complete.")