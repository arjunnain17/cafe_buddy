# core/menu_ingestion.py

import json
import tempfile
import os
import importlib
from pathlib import Path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# ── Step 1 — Extract structured Markdown from PDF ────────────────────────────

def extract_menu_markdown(pdf_path: str) -> str:
    """
    Uses OpenDataLoader to extract structured Markdown from any cafe menu PDF.
    """
    import opendataloader_pdf

    output_dir = tempfile.mkdtemp()

    opendataloader_pdf.convert(
        input_path=[pdf_path],
        output_dir=output_dir,
        format="markdown",
    )

    md_files = list(Path(output_dir).glob("*.md"))

    if not md_files:
        raise ValueError(
            "OpenDataLoader produced no output. "
            "Check that the PDF contains extractable text."
        )

    markdown = md_files[0].read_text(encoding="utf-8").strip()

    # cleanup
    for f in Path(output_dir).iterdir():
        f.unlink()
    Path(output_dir).rmdir()

    return markdown


# ── Step 2 — LLM structures Markdown into your schema ────────────────────────

EXTRACTION_PROMPT = """
You are a menu data extraction specialist for a cafe ordering system.

Extract ALL menu items from the text below and return a JSON object
with exactly three keys: "drinks", "cookies", "customizations".

If the menu has no customizations section, return "customizations": [].
If the menu has no food/snacks section, return "cookies": [].

═══════════════════════════════
DRINK SCHEMA:
{
  "id": "snake_case_name",
  "name": "Display Name",
  "prices": {"medium": 0, "large": 0},
  "default_size": "medium",
  "description": "natural language description",
  "tags": ["sweet", "coffee", "warm"],
  "allergens": ["milk"],
  "dietary_tags": ["vegetarian"],
  "base_milk": "whole_milk",
  "customisable": true,
  "compatible_addons": [],
  "category": "hot",
  "available": true
}

FOOD/COOKIE SCHEMA:
{
  "id": "snake_case_name",
  "name": "Display Name",
  "price": 0,
  "description": "natural language description",
  "tags": ["sweet", "baked"],
  "allergens": ["gluten", "milk"],
  "dietary_tags": ["vegetarian"],
  "pairs_well_with": [],
  "flavour_profile": ["sweet", "chocolatey"],
  "category": "baked",
  "available": true
}

CUSTOMIZATION SCHEMA:
{
  "id": "snake_case_name",
  "name": "Display Name",
  "price": 0,
  "description": "natural language description",
  "tags": ["dairy-free"],
  "allergens": [],
  "dietary_tags": ["vegan", "dairy-free"],
  "addon_type": "milk_swap",
  "replaces": "whole_milk",
  "compatible_with": [],
  "dietary_resolution": {"resolves": ["vegan", "dairy-free"], "introduces": []},
  "upsell_line": "short upsell phrase",
  "available": true
}

═══════════════════════════════
FIELD RULES:

category for drinks:
  "hot"     → espresso, latte, cappuccino, flat white, tea, hot chocolate
  "iced"    → iced latte, cold brew, iced tea, iced americano
  "blended" → frappuccino, smoothie, shake
  "tea"     → tea-only drinks with no espresso

base_milk:
  "whole_milk" → standard milk-based drinks
  "oat_milk"   → if oat milk is the default
  "none"       → black coffee, americano, espresso, tea with no milk

allergens — infer from drink type if not listed:
  milk-based drinks → ["milk"]
  oat milk default  → ["oats"]
  baked goods       → ["gluten", "milk", "eggs"] unless stated otherwise

dietary_tags — infer:
  no allergens       → ["vegan", "dairy-free", "gluten-free", "vegetarian"]
  only milk allergen → ["vegetarian"]

addon_type options:
  "milk_swap"     → oat milk, almond milk, soy milk
  "shot"          → extra espresso shot
  "flavour_syrup" → vanilla, caramel, hazelnut syrups
  "topping"       → whipped cream, sprinkles
  "size_upgrade"  → size upgrades

PRICE RULES:
  One price listed    → use for "medium", set "large" to 0
  Two prices listed   → first is "medium", second is "large"
  Format 100/130      → medium: 100, large: 130
  Price missing       → set to 0

RETURN ONLY valid JSON. No explanation. No markdown fences.
Start with { and end with }.

MENU TEXT:
{menu_text}
"""

def structure_with_llm(markdown: str) -> dict:
    """
    Sends extracted Markdown to Gemini for schema-aware structuring.
    Uses temperature 0 for deterministic extraction.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=EXTRACTION_PROMPT.replace("{menu_text}", markdown),
        config=types.GenerateContentConfig(temperature=0.0),
    )

    text = response.text.strip()

    # strip markdown fences if model adds them despite instructions
    if text.startswith("```"):
        lines = text.split("\n")
        text  = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        )

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM returned invalid JSON.\n"
            f"Error: {e}\n"
            f"Raw response (first 500 chars):\n{text[:500]}"
        )


# ── Step 3 — Validate and fill gaps ──────────────────────────────────────────

def validate(structured: dict) -> tuple[dict, list[str]]:
    """
    Validates extracted data. Fills safe defaults, flags missing prices.
    Returns (cleaned_data, issues_list).
    """
    issues  = []
    drinks  = structured.get("drinks", [])
    cookies = structured.get("cookies", [])
    customs = structured.get("customizations", [])

    for i, drink in enumerate(drinks):
        if not drink.get("id"):
            drink["id"] = drink.get(
                "name", f"drink_{i}"
            ).lower().replace(" ", "_")

        prices = drink.get("prices", {})
        if not prices or prices.get("medium", 0) == 0:
            issues.append(
                f"⚠ Missing medium price: '{drink.get('name')}'"
            )
        if prices.get("large", 0) == 0 and prices.get("medium", 0) != 0:
            issues.append(
                f"ℹ Single size only: '{drink.get('name')}'"
            )

        drink.setdefault("category",     "hot")
        drink.setdefault("dietary_tags", ["vegetarian"])
        drink.setdefault("tags",         [drink.get("category", "coffee")])
        drink.setdefault("customisable", drink.get("base_milk") != "none")
        drink.setdefault("available",    True)
        drink.setdefault("compatible_addons", [])
        drink.setdefault("base_milk",    "whole_milk")

    for i, item in enumerate(cookies):
        if not item.get("id"):
            item["id"] = item.get(
                "name", f"item_{i}"
            ).lower().replace(" ", "_")

        if not item.get("price") or item["price"] == 0:
            issues.append(
                f"⚠ Missing price: '{item.get('name')}'"
            )

        item.setdefault("category",      "baked")
        item.setdefault("dietary_tags",  ["vegetarian"])
        item.setdefault("tags",          ["baked"])
        item.setdefault("pairs_well_with", [])
        item.setdefault("flavour_profile", [])
        item.setdefault("available",     True)

    for i, addon in enumerate(customs):
        if not addon.get("id"):
            addon["id"] = addon.get(
                "name", f"addon_{i}"
            ).lower().replace(" ", "_")

        if addon.get("price") is None:
            issues.append(
                f"⚠ Missing price: '{addon.get('name')}'"
            )

        addon.setdefault("addon_type",          "other")
        addon.setdefault("replaces",            "none")
        addon.setdefault("compatible_with",     [])
        addon.setdefault("dietary_resolution",  {"resolves": [], "introduces": []})
        addon.setdefault("upsell_line",         "")
        addon.setdefault("available",           True)

    structured["drinks"]         = drinks
    structured["cookies"]        = cookies
    structured["customizations"] = customs

    return structured, issues


# ── Step 4 — Write data files ─────────────────────────────────────────────────

def write_data_files(structured: dict, output_dir: str = "data") -> None:
    import pprint
    Path(output_dir).mkdir(exist_ok=True)

    mapping = {
        "drinks":         ("drinks",         "drinks.py"),
        "cookies":        ("cookies",        "cookies.py"),
        "customizations": ("customizations", "customizations.py"),
    }

    for key, (var_name, filename) in mapping.items():
        items    = structured.get(key, [])
        filepath = Path(output_dir) / filename
        # pprint.pformat produces valid Python with True/False/None
        content  = f"{var_name} = {pprint.pformat(items, indent=4)}\n"
        filepath.write_text(content, encoding="utf-8")
        print(f"[ingest] Wrote {len(items)} items → {filepath}")

# ── Step 5 — Rebuild FAISS indexes ───────────────────────────────────────────

def rebuild_indexes() -> None:
    """
    Calls run_ingest() from ingest.py.
    Uses importlib.reload to ensure updated data files are picked up.
    """
    from core.ingest import run_ingest
    run_ingest()


# ── Master pipeline ───────────────────────────────────────────────────────────

def ingest_menu_from_pdf(pdf_path: str) -> dict:
    """
    Full pipeline:
    PDF → OpenDataLoader Markdown → LLM extraction
        → validation → data files → FAISS rebuild
    """
    print(f"\n[ingest] ── Starting menu ingestion ──────────────────────")
    print(f"[ingest] File: {pdf_path}")

    # step 1
    print(f"[ingest] Step 1: Parsing PDF with OpenDataLoader...")
    try:
        markdown = extract_menu_markdown(pdf_path)
        print(f"[ingest] Extracted {len(markdown)} characters.")
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}")

    if not markdown.strip():
        raise ValueError(
            "No content extracted. "
            "PDF may be a scanned image without OCR support."
        )

    # step 2
    print(f"[ingest] Step 2: Structuring with Gemini...")
    structured = structure_with_llm(markdown)

    # step 3
    print(f"[ingest] Step 3: Validating...")
    cleaned, issues = validate(structured)

    # step 4
    print(f"[ingest] Step 4: Writing data files...")
    write_data_files(cleaned)

    # step 5
    print(f"[ingest] Step 5: Rebuilding FAISS indexes...")
    rebuild_indexes()

    summary = {
        "drinks":         len(cleaned.get("drinks", [])),
        "cookies":        len(cleaned.get("cookies", [])),
        "customizations": len(cleaned.get("customizations", [])),
        "issues":         issues,
        "status":         "complete" if not issues else "complete_with_warnings",
    }

    print(f"\n[ingest] ── Done ─────────────────────────────────────────")
    print(f"[ingest] Drinks:         {summary['drinks']}")
    print(f"[ingest] Food items:     {summary['cookies']}")
    print(f"[ingest] Customizations: {summary['customizations']}")
    if issues:
        print(f"[ingest] Warnings ({len(issues)}):")
        for issue in issues:
            print(f"         {issue}")

    return summary