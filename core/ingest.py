
import os
import json
import numpy as np 
import faiss    
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.drinks import drinks
from data.customizations import customizations
from data.cookies import cookies

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)
# ── Transformation mappings ───────────────────────────────────────────────────

ALLERGEN_PHRASES = {
    "milk":   "contains milk, contains dairy",
    "gluten": "contains gluten, contains wheat",
    "eggs":   "contains eggs",
    "nuts":   "contains nuts, contains tree nuts, nut allergy warning",
    "oats":   "contains oats",
    "soy":    "contains soy, contains soya",
    "sesame": "contains sesame",
}
ALL_DIETARY_OPTIONS = ["vegan", "dairy-free", "gluten-free", "vegetarian"]
DRINK_CATEGORY_PHRASES = {
    "hot":     "hot drink, warm drink, warm beverage, served hot, cozy",
    "iced":    "iced drink, cold drink, cold beverage, served over ice, refreshing, chilled",
    "blended": "blended drink, thick and creamy, frozen drink, smoothie style",
    "tea":     "tea based drink, non-coffee option, tea, lighter caffeine",
}

BASE_MILK_PHRASES = {
    "whole_milk": "made with whole milk, made with dairy milk, contains dairy",
    "oat_milk":   "made with oat milk, already dairy-free, already vegan milk base",
    "none":       "no milk, black, dairy-free as standard, no dairy added",
}
ADDON_TYPE_PHRASES = {
    "milk_swap":     "milk alternative, milk substitute, dairy-free swap, "
                     "change the milk, non-dairy option, swap out the milk",
    "flavour_syrup": "flavour shot, flavour add, syrup, sweetener, flavouring, "
                     "adds flavour, flavoured",
    "shot":          "extra espresso, extra caffeine, stronger coffee, "
                     "additional shot, more coffee, boost",
    "topping":       "topping, finishing touch, on top, garnish, added on top",
    "size_upgrade":  "size upgrade, bigger size, larger portion, more drink",
}

REPLACES_PHRASES = {
    "whole_milk":  "replaces regular milk, replaces dairy milk, "
                   "instead of whole milk, swap out dairy",
    "semi_milk":   "replaces semi skimmed milk, replaces dairy milk",
    "none":        "",    # addons with no replacement — shots, toppings etc
}
SNACK_CATEGORY_PHRASES = {
    "baked":   "baked good, freshly baked, pastry, bakery item, oven fresh",
    "savoury": "savoury snack, not sweet, savoury food, light meal",
    "healthy": "healthy snack, light snack, nutritious, wholesome, guilt free",
    "raw":     "raw snack, unprocessed, natural snack, no baking",
}
def build_text_drink(item: dict) -> str:
    """
    Converts a drink dictionary into a rich natural language string
    for embedding. Every field that carries semantic meaning a customer
    might search for is transformed and included.
    Fields that are operational (id, prices as numbers, available,
    compatible_addons) are skipped.
    """
    parts = []

    # ── Name ─────────────────────────────────────────────────────────────────
    # Always first — the exact name a customer might say
    parts.append(item["name"])

    # ── Description ──────────────────────────────────────────────────────────
    # Richest semantic field — embed as-is
    # If your description is thin, fix it in data/drinks.py first
    parts.append(item["description"])

    # ── Tags ─────────────────────────────────────────────────────────────────
    # Your hand-picked semantic anchors — join as space-separated
    # e.g. ["sweet", "coffee", "warm"] → "sweet coffee warm"
    if item.get("tags"):
        parts.append(" ".join(item["tags"]))

    # ── Category ─────────────────────────────────────────────────────────────
    # Transform single word into natural language phrases
    # "hot" → "hot drink, warm drink, warm beverage, served hot, cozy"
    category = item.get("category", "")
    if category:
        parts.append(
            DRINK_CATEGORY_PHRASES.get(category, f"{category} drink")
        )

    # ── Allergens ─────────────────────────────────────────────────────────────
    # Transform each allergen into customer-facing language with synonyms
    # ["milk"] → "contains milk, contains dairy, not dairy-free, not vegan"
    for allergen in item.get("allergens", []):
        phrase = ALLERGEN_PHRASES.get(allergen, f"contains {allergen}")
        parts.append(phrase)

    # ── Dietary tags ──────────────────────────────────────────────────────────
    # Explicitly state both presence AND absence
    # Absence of "vegan" → embed "not vegan" so vegan queries distance away
    # Unless the drink can be made vegan — handled by customisable block below
    dietary = item.get("dietary_tags", [])
    for option in ALL_DIETARY_OPTIONS:
        if option in dietary:
            parts.append(f"suitable for {option}, {option} friendly")
        else:
            # only skip vegan/dairy-free negation if drink is customisable
            # because customisable block below will say "can be made vegan"
            # gluten-free negation always fires regardless of customisable
            if option in ("vegan", "dairy-free") and item.get("customisable", False):
                pass   # customisable block handles this below
            else:
                parts.append(f"not {option}")
    # ── Base milk ─────────────────────────────────────────────────────────────
    # What milk the drink is made with by default
    # "whole_milk" → "made with whole milk, made with dairy milk, contains dairy"
    base_milk = item.get("base_milk", "")
    if base_milk:
        parts.append(
            BASE_MILK_PHRASES.get(base_milk, f"made with {base_milk}")
        )

    # ── Customisable ──────────────────────────────────────────────────────────
    # This is the critical signal for vegan conflict resolution
    # A customisable dairy drink should still surface for vegan queries
    # so the agent can pitch the milk swap
    if item.get("customisable", False):
        parts.append(
            "can be customised, modifications available, "
            "can swap the milk, dairy-free version available on request, "
            "can be made vegan with milk alternative"
        )

    # ── Size availability ─────────────────────────────────────────────────────
    # Don't embed prices as numbers — embed the concept of size choice
    if item.get("prices"):
        sizes = list(item["prices"].keys())
        size_str = " and ".join(sizes)
        parts.append(f"available in {size_str}")

    # ── Final join ────────────────────────────────────────────────────────────
    # Pipe separator gives embedder soft boundaries between concepts
    # Filter empty strings before joining
    return " | ".join(p for p in parts if p and p.strip())


def build_text_customization(item: dict) -> str:
    """
    Converts a customization (addon) dictionary into a rich natural language string
    for embedding. Every field that carries semantic meaning a customer might search for
    is transformed and included.
    Fields that are operational (id, price, compatible_with, available) are skipped.
    """
    parts = []

    # ── Name ──────────────────────────────────────────────────────────────────
    # Always first — the exact name/addon a customer might request
    parts.append(item["name"])

    # ── Description ───────────────────────────────────────────────────────────
    # Richest semantic field — embed as-is
    parts.append(item["description"])

    # ── Tags ───────────────────────────────────────────────────────────────────
    # Hand-picked semantic anchors — join as space-separated
    if item.get("tags"):
        parts.append(" ".join(item["tags"]))

    # ── Allergens ──────────────────────────────────────────────────────────────
    # Transform each allergen into customer-facing language with synonyms
    # This addon might INTRODUCE allergens (e.g. oat milk introduces oats)
    for allergen in item.get("allergens", []):
        phrase = ALLERGEN_PHRASES.get(allergen, f"contains {allergen}")
        parts.append(phrase)

    # ── Dietary tags ───────────────────────────────────────────────────────────
    # What dietary needs this addon fulfills
    dietary = item.get("dietary_tags", [])
    for option in ALL_DIETARY_OPTIONS:
        if option in dietary:
            parts.append(f"suitable for {option}, {option} friendly")
        else:
            parts.append(f"not {option}")

    # ── Addon type ─────────────────────────────────────────────────────────────
    # Transform addon category into natural language phrases
    # "milk_swap" → "milk alternative, milk substitute, dairy-free swap, ..."
    addon_type = item.get("addon_type", "")
    if addon_type:
        parts.append(
            ADDON_TYPE_PHRASES.get(addon_type, f"{addon_type} addon")
        )

    # ── Replaces ───────────────────────────────────────────────────────────────
    # What this addon replaces (if anything) — context for the swap
    # "whole_milk" → "replaces regular milk, replaces dairy milk, instead of whole milk, swap out dairy"
    replaces = item.get("replaces", "")
    if replaces:
        phrase = REPLACES_PHRASES.get(replaces, f"replaces {replaces}")
        if phrase:
            parts.append(phrase)

    # ── Dietary resolution ─────────────────────────────────────────────────────
    # What conflicts this addon RESOLVES (e.g. oat milk resolves dairy-free conflict)
    # AND what new allergens/restrictions it INTRODUCES
    dietary_resolution = item.get("dietary_resolution", {})
    resolves = dietary_resolution.get("resolves", [])
    introduces = dietary_resolution.get("introduces", [])
    
    if resolves:
        for tag in resolves:
            parts.append(
                f"makes drink {tag}, suitable for {tag} customers, "
                f"{tag} option, good for {tag} diet"
            )

    if introduces:
        for allergen in introduces:
            phrase = ALLERGEN_PHRASES.get(allergen, f"contains {allergen}")
            parts.append(phrase)
    # ── Upsell line ────────────────────────────────────────────────────────────
    # The pitch — why a customer should add this addon
    if item.get("upsell_line"):
        parts.append(item["upsell_line"])

    # ── Final join ─────────────────────────────────────────────────────────────
    # Pipe separator gives embedder soft boundaries between concepts
    # Filter empty strings before joining
    return " | ".join(p for p in parts if p and p.strip())


def build_text_snack(item: dict) -> str:
    """
    Converts a snack dictionary into a rich natural language string
    for embedding. Every field that carries semantic meaning a customer
    might search for is transformed and included.
    Fields that are operational (id, price, pairs_well_with, available)
    are skipped.
    """
    parts = []

    # ── Name ──────────────────────────────────────────────────────────────────
    # Always first — the exact name a customer might order or search for
    parts.append(item["name"])

    # ── Description ───────────────────────────────────────────────────────────
    # Richest semantic field — embed as-is
    parts.append(item["description"])

    # ── Tags ───────────────────────────────────────────────────────────────────
    # Hand-picked semantic anchors — join as space-separated
    # e.g. ["sweet", "chocolate", "baked"] → "sweet chocolate baked"
    if item.get("tags"):
        parts.append(" ".join(item["tags"]))

    # ── Category ───────────────────────────────────────────────────────────────
    # Transform category into natural language phrases
    # "baked" → "baked good, freshly baked, pastry, bakery item, oven fresh"
    category = item.get("category", "")
    if category:
        parts.append(
            SNACK_CATEGORY_PHRASES.get(category, f"{category} snack")
        )

    # ── Allergens ──────────────────────────────────────────────────────────────
    # Transform each allergen into customer-facing language with synonyms
    # ["gluten","milk","eggs"] → multiple phrases for each
    for allergen in item.get("allergens", []):
        phrase = ALLERGEN_PHRASES.get(allergen, f"contains {allergen}")
        parts.append(phrase)

    # ── Dietary tags ───────────────────────────────────────────────────────────
    # Explicitly state both presence AND absence
    # No customisable gate here — snacks can't be modified like drinks
    # Every absent tag becomes a flat negation
    dietary = item.get("dietary_tags", [])
    for option in ALL_DIETARY_OPTIONS:
        if option in dietary:
            parts.append(f"suitable for {option}, {option} friendly")
        else:
            parts.append(f"not {option}")

    # ── Flavour profile ────────────────────────────────────────────────────────
    # Your most useful field for vague queries like "something indulgent"
    # or "rich and chocolatey" — join as space-separated semantic anchors
    if item.get("flavour_profile"):
        parts.append(" ".join(item["flavour_profile"]))

    # ── Final join ─────────────────────────────────────────────────────────────
    # Pipe separator gives embedder soft boundaries between concepts
    # Filter empty strings before joining
    return " | ".join(p for p in parts if p and p.strip())


def embed_text(text: str) -> list[float]:
    """
    Embeds a single string using Gemini embedding model.
    Uses task_type RETRIEVAL_DOCUMENT at ingest time for optimal
    semantic representations in retrieval scenarios.
    Returns a list of 768 floats representing the embedding vector.
    """
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=768
        )
    )
    # Extract the embedding vector from ContentEmbedding object
    embedding_obj = result.embeddings[0]
    return embedding_obj.values


def ingest_catalog(name: str, items: list[dict], build_fn) -> None:
    """
    Builds and saves a FAISS index for one catalog (drinks, customizations, or snacks).
    
    Args:
        name     — used for filenames e.g. "drinks", "customizations", "snacks"
        items    — list of dicts from your data files
        build_fn — the right build_text function for this catalog
                   (build_text_drink, build_text_customization, build_text_snack)
    """
    print(f"\nIngesting {name} ({len(items)} items)...")
    
    embeddings = []
    metadata = []

    for item in items:
        # 1. Skip unavailable items
        if not item.get("available", True):
            continue

        # 2. Build the text string
        text = build_fn(item)

        # 3. Embed the text
        vector = embed_text(text)

        # 4. Append vector to embeddings list
        embeddings.append(vector)
        
        # 5. Store metadata in same order as embeddings
        metadata.append(item)

        # 6. Sleep to avoid rate limiting
        time.sleep(0.1)

        # 7. Print progress
        print(f"  embedded: {item['name']}")

    # 8. Convert embeddings list to numpy matrix
    # Shape must be (len(embeddings), 768)
    matrix = np.array(embeddings, dtype=np.float32)

    # 9. Create FAISS index and add matrix
    index = faiss.IndexFlatL2(768)
    index.add(matrix)

    # 10. Save FAISS index to storage/
    faiss.write_index(index, f"{STORAGE_DIR}/{name}.index")

    # 11. Save metadata JSON to storage/ in same order as matrix rows
    metadata_path = f"{STORAGE_DIR}/{name}_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  saved {index.ntotal} vectors → {STORAGE_DIR}/{name}.index")
    print(f"  saved metadata → {STORAGE_DIR}/{name}_metadata.json")


def main():
    """
    Main ingestion pipeline — builds FAISS indexes for all catalogs.
    Embeds drinks, customizations (addons), and snacks for semantic search.
    """
    ingest_catalog("drinks", drinks, build_text_drink)
    ingest_catalog("customizations", customizations, build_text_customization)
    ingest_catalog("cookies", cookies, build_text_snack)

    print("\nAll indexes built successfully.")
    print("Run python app.py to start the CLI.")


if __name__ == "__main__":
    main()