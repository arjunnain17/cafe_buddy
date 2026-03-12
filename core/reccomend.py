"""
core/recommend.py

Runtime recommendation engine for Cafe Buddy.
Loads FAISS indexes into memory at startup and exposes
a single search_index() function for all three catalogs.

Usage:
    from core.recommend import load_indexes, search_index

    load_indexes()   # call once at app startup

    results = search_index("drinks", "something warm and sweet", k=3)
"""

import os
import json
import time
from unittest import result
import numpy as np
import faiss
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# ── Constants ─────────────────────────────────────────────────────────────────

# Use absolute path relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(SCRIPT_DIR, "storage")
CATALOG_NAMES = ["drinks", "cookies", "customizations"]

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── In-memory index registry ──────────────────────────────────────────────────
# Populated once by load_indexes() at startup.
# Structure:
#   _indexes["drinks"] = {
#       "index": faiss.IndexFlatL2,   ← the FAISS binary
#       "meta":  list[dict],          ← original item dicts, same order as vectors
#   }

_indexes: dict = {}


# ── Load ──────────────────────────────────────────────────────────────────────

def load_indexes() -> None:
    """
    Loads all three FAISS indexes and their metadata into memory.
    Call this once at app startup before any search_index() calls.
    Raises FileNotFoundError if indexes haven't been built yet.
    """
    for name in CATALOG_NAMES:
        index_path = os.path.join(STORAGE_DIR, f"{name}.index")
        meta_path  = os.path.join(STORAGE_DIR, f"{name}_metadata.json")

        # clear error if ingest hasn't been run yet
        if not os.path.exists(index_path):
            raise FileNotFoundError(
                f"Index not found: {index_path}\n"
                f"Run `python core/ingest.py` first to build indexes."
            )

        index = faiss.read_index(index_path)

        with open(meta_path, "r") as f:
            meta = json.load(f)

        # sanity check — vectors and metadata must be in perfect sync
        if index.ntotal != len(meta):
            raise ValueError(
                f"Index/metadata mismatch for '{name}': "
                f"{index.ntotal} vectors but {len(meta)} metadata items. "
                f"Re-run `python core/ingest.py` to rebuild."
            )

        _indexes[name] = {"index": index, "meta": meta}
        print(f"[recommend] loaded '{name}' — {index.ntotal} vectors")


def _require_loaded(catalog: str) -> None:
    """Raises a clear error if load_indexes() hasn't been called yet."""
    if catalog not in _indexes:
        raise RuntimeError(
            f"Catalog '{catalog}' not loaded. "
            f"Call load_indexes() before searching."
        )


# ── Embed ─────────────────────────────────────────────────────────────────────

def embed_query(text: str) -> np.ndarray:
    """
    Embeds a user query using Gemini's retrieval_query task type.
    This is the runtime counterpart to embed_text() in ingest.py.

    IMPORTANT: must use retrieval_query here (not retrieval_document).
    The two task types are optimised as a matched pair —
    documents embedded with retrieval_document are designed to be
    searched by queries embedded with retrieval_query.

    Returns numpy array of shape (1, 768) — ready for faiss.search().
    """
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768   
        )
    )
    vector = np.array(result.embeddings[0].values, dtype=np.float32)
    return vector.reshape(1, -1)       # FAISS requires (1, 768) not (768,)


# ── Search ────────────────────────────────────────────────────────────────────

def search_index(catalog: str, query: str, k: int = 3) -> list[dict]:
    """
    Searches a named catalog with a natural language query.
    Returns top-k matching items sorted by similarity.

    Args:
        catalog  — "drinks", "cookies", or "customizations"
        query    — natural language e.g. "something sweet and cold"
        k        — number of results to return (default 3)

    Returns:
        List of item dicts from the catalog metadata,
        each with a "score" key added (L2 distance — lower = closer match).

    Example:
        results = search_index("drinks", "warm and comforting", k=3)
        # [
        #   {"name": "Caramel Latte", "score": 0.18, ...},
        #   {"name": "Chai Latte",    "score": 0.24, ...},
        #   {"name": "Hot Chocolate", "score": 0.31, ...},
        # ]
    """
    _require_loaded(catalog)

    # embed the query — retrieval_query task type, shape (1, 768)
    query_vec = embed_query(query)

    # search — returns two arrays each of shape (1, k)
    # distances[0] — L2 distances, lower means more similar
    # positions[0] — index positions mapping back to metadata
    distances, positions = _indexes[catalog]["index"].search(query_vec, k)
    meta = _indexes[catalog]["meta"]   

    results = []
    for distance, position in zip(distances[0], positions[0]):
        if position == -1:
            continue
        if float(distance) > 0.25:   # ← filter poor matches
            continue
        item = dict(meta[position])
        item["score"] = round(float(distance), 4)
        results.append(item)
    return results


# ── Convenience wrappers ──────────────────────────────────────────────────────
# These are what the LangChain tools call — cleaner than passing catalog name.

def search_drinks(query: str, k: int = 3) -> list[dict]:
    """Search the drinks catalog. Wrapper around search_index()."""
    return search_index("drinks", query, k)


def search_cookies(query: str, k: int = 3) -> list[dict]:
    """Search the cookies catalog. Wrapper around search_index()."""
    return search_index("cookies", query, k)


def search_customizations(query: str, k: int = 3) -> list[dict]:
    """Search the customizations catalog. Wrapper around search_index()."""
    return search_index("customizations", query, k)


