import faiss, json

for name in ["drinks", "cookies", "customizations"]:
    try:
        index = faiss.read_index(f"storage/{name}.index")
        with open(f"storage/{name}_metadata.json") as f:
            meta = json.load(f)
        print(f"{name}: {index.ntotal} vectors, {len(meta)} metadata items")
        # both numbers must match for every catalog
    except FileNotFoundError as e:
        print(f"Error loading {name}: {e}")
    except Exception as e:
        print(f"Error processing {name}: {e}")