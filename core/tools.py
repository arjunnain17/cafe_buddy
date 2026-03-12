import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from langchain.tools import tool
from core.reccomend import _indexes,search_drinks, search_cookies, search_customizations
from core.basket import (
    add_drink, add_cookie, remove_item,
    view_basket, checkout, clear_basket,
    set_budget, get_budget, get_total, get_remaining,
    set_dietary, get_dietary
)


@tool
def tool_search_drinks(query: str) -> str:
    """
    Search the drinks menu using semantic vector search.
    Call this when the user describes what kind of drink they want —
    mood, flavour, temperature, caffeine level, or dietary need.
    Input:  natural language query e.g. "something warm and sweet"
    Output: top 3 matching drinks with name, prices, and dietary info.
    """
    results = search_drinks(query, k=3)

    if not results:
        return "No drinks found matching that description."

    lines = []
    for r in results:
        prices = r.get("prices", {})
        price_str = " / ".join(
            f"{size.capitalize()} ₹{price:.0f}"
            for size, price in prices.items()
        )
        dietary = ", ".join(r.get("dietary_tags", []))
        lines.append(
            f"- {r['name']} | {price_str} | {dietary} | score: {r['score']}"
        )

    return "\n".join(lines)


@tool
def tool_search_cookies(query: str) -> str:
    """
    Search the cookies menu using semantic vector search.
    Call this when the user asks for food, a snack, something to eat,
    or something to complement their drink.
    Input:  natural language query e.g. "something chocolatey"
    Output: top 3 matching cookies with name, price, dietary info.
    """
    results = search_cookies(query, k=3)

    if not results:
        return "No cookies found matching that description."

    lines = []
    for r in results:
        price = r.get("price", 0.0)
        dietary = ", ".join(r.get("dietary_tags", []))
        lines.append(
            f"- {r['name']} | ₹{price:.0f} | {dietary} | score: {r['score']}"
        )

    return "\n".join(lines)


@tool
def tool_search_customizations(query: str) -> str:
    """
    Search available drink customizations — milk swaps, syrups,
    extra shots, toppings.
    Call this when user wants to modify a drink, asks for dairy-free
    version, wants it stronger, or asks about upgrades.
    Input:  natural language query e.g. "dairy free milk option"
    Output: top matching customizations with name, price, dietary info.
    """
    results = search_customizations(query, k=3)

    if not results:
        return "No customizations found matching that description."

    lines = []
    for r in results:
        price = r.get("price", 0.0)
        dietary = ", ".join(r.get("dietary_tags", []))
        lines.append(
            f"- {r['name']} | ₹{price:.0f} | {dietary} | score: {r['score']}"
        )

    return "\n".join(lines)
@tool
def tool_view_basket(_: str = "") -> str:
    """
    Show the current contents of the order basket.
    Call this when the user asks what's in their order,
    wants to see their basket, or asks how much so far.
    Input:  ignored — pass empty string
    Output: formatted basket with items, prices, and total.
    """
    return view_basket()


@tool
def tool_checkout(_: str = "") -> str:
    """
    Finalise the order and print a receipt.
    Call this when the user says they're done, wants to
    place their order, or says checkout.
    Clears the basket after generating the receipt.
    Input:  ignored — pass empty string
    Output: formatted receipt string.
    """
    return checkout()


@tool
def tool_remove_from_basket(basket_id: str) -> str:
    """
    Remove a specific item from the basket by its basket_id.
    basket_id looks like "item_001" — get it from view_basket().
    Call this when user says remove, cancel, or don't want something.
    Input:  basket_id string e.g. "item_001"
    Output: confirmation with updated total.
    """
    return remove_item(basket_id.strip())


@tool
def tool_add_cookie_to_basket(cookie_json: str) -> str:
    """
    Add a cookie to the basket.
    Input must be a JSON string with these exact keys:
      id, name, price
    Example:
      '{"id": "choco_chunk_cookie", "name": "Choco Chunk Cookie", "price": 65}'
    Call this only after the user explicitly confirms they want the cookie.
    Never add without confirmation.
    Output: confirmation string with basket_id and price.
    """
    try:
        cookie = json.loads(cookie_json)
        return add_cookie(cookie)
    except json.JSONDecodeError as e:
        return f"Error parsing cookie data: {e}"
    except KeyError as e:
        return f"Missing required field: {e}"


@tool
def tool_add_drink_to_basket(drink_json: str) -> str:
    """
    Add a drink to the basket with size and customizations resolved.
    Input must be a JSON string with these exact keys:
      id, name, prices (dict), size, customizations (list)
    Example:
      '{
        "id": "caramel_latte",
        "name": "Caramel Latte",
        "prices": {"medium": 110, "large": 140},
        "size": "large",
        "customizations": [
          {"id": "oat_milk_upgrade", "name": "Oat Milk Upgrade", "price": 60}
        ]
      }'
    Size must be "medium" or "large".
    Customizations can be empty list [] if no addons selected.
    Call this only after user confirms drink AND size.
    Output: confirmation string with basket_id and total.
    """
    try:
        data = json.loads(drink_json)

        # extract fields
        drink = {
            "id":     data["id"],
            "name":   data["name"],
            "prices": data["prices"],
        }
        size            = data["size"]
        customizations  = data.get("customizations", [])

        # validate size
        if size not in drink["prices"]:
            return (
                f"Invalid size '{size}' for {drink['name']}. "
                f"Available sizes: {', '.join(drink['prices'].keys())}"
            )

        return add_drink(drink, size, customizations)

    except json.JSONDecodeError as e:
        return f"Error parsing drink data: {e}"
    except KeyError as e:
        return f"Missing required field: {e}"
@tool
def tool_set_session_budget(amount: str) -> str:
    """
    Set the customer's budget for this session.
    Call this the moment the user mentions a spending limit —
    "I have ₹500", "keep it under 300", "around ₹400".
    Input:  budget amount as string e.g. "500" or "300.00"
    Output: confirmation string.
    """
    try:
        set_budget(float(amount.replace("₹", "").strip()))
        return f"Budget set to ₹{float(amount):.0f} for this session."
    except ValueError:
        return f"Could not parse budget amount: '{amount}'"


@tool
def tool_check_budget_fit(price: str) -> str:
    """
    Check whether an item price fits within the remaining budget.
    Returns one of three zones:
      safe    — fits comfortably, recommend freely
      upsell  — slightly over (within 10%), may suggest with framing
      blocked — too far over, do not surface this item
    Call this before recommending any item when budget is set.
    Input:  price as string e.g. "140" or "60"
    Output: zone string with full context for reasoning.
    """
    budget = get_budget()

    if budget is None:
        return "zone:safe | no budget set — recommend freely"

    try:
        price_float  = float(price.replace("₹", "").strip())
        spent        = get_total()
        remaining    = budget - spent
        new_total    = spent + price_float
        overage      = new_total - budget
        tolerance    = budget * 0.10        # 10% overage allowed

        if price_float <= remaining:
            return (
                f"zone:safe | "
                f"₹{price_float:.0f} fits | "
                f"remaining after: ₹{remaining - price_float:.0f}"
            )
        elif overage <= tolerance:
            return (
                f"zone:upsell | "
                f"₹{price_float:.0f} is ₹{overage:.0f} over budget | "
                f"total would be ₹{new_total:.0f} vs budget ₹{budget:.0f} | "
                f"suggest with persuasive framing and cheaper alternative"
            )
        else:
            return (
                f"zone:blocked | "
                f"₹{price_float:.0f} is ₹{overage:.0f} over budget | "
                f"exceeds 10% tolerance — do not suggest this item"
            )

    except ValueError:
        return f"Could not parse price: '{price}'"


@tool
def tool_suggest_upsell(_: str = "") -> str:
    """
    After the main order is set, find the single best upsell item
    within the budget's upsell zone (up to 10% over budget).
    Searches customizations first, then cookies if no customization fits.
    Call this after user seems satisfied with main drink but before checkout.
    Input:  ignored — pass empty string
    Output: best upsell candidate with framing advice, or none.
    """
    budget = get_budget()
    spent  = get_total()

    if budget is None:
        return "upsell:free | no budget set — suggest freely from search results"

    remaining  = budget - spent
    tolerance  = budget * 0.10
    max_price  = remaining + tolerance

    # search both catalogs for popular upsell candidates
    customization_candidates = search_customizations("popular upgrade enhancement", k=5)
    cookie_candidates        = search_cookies("popular cookie complement", k=5)
    all_candidates           = customization_candidates + cookie_candidates

    # split into safe and upsell zone
    safe   = [i for i in all_candidates
              if i.get("price") and i["price"] <= remaining]
    upsell = [i for i in all_candidates
              if i.get("price") and remaining < i["price"] <= max_price]

    if safe:
        # pick highest priced safe item — best value upsell
        best = sorted(safe, key=lambda x: x["price"], reverse=True)[0]
        return (
            f"upsell:safe | {best['name']} ₹{best['price']:.0f} | "
            f"fits in budget | suggest naturally"
        )
    elif upsell:
        # pick cheapest over-budget item — smallest ask
        best    = sorted(upsell, key=lambda x: x["price"])[0]
        overage = (spent + best["price"]) - budget
        return (
            f"upsell:nudge | {best['name']} ₹{best['price']:.0f} | "
            f"₹{overage:.0f} over budget | "
            f"acknowledge overage, give value reason, offer cheaper alternative"
        )
    else:
        return "upsell:none | all remaining items exceed tolerance"
@tool
def tool_set_dietary_preferences(preferences: str) -> str:
    """
    Store the customer's dietary preferences for this session.
    Call this the moment any dietary signal appears in conversation —
    "I'm vegan", "no dairy", "I have a nut allergy", "gluten free please".
    Persists for entire session like budget does.
    Input:  comma separated string e.g. "vegan, dairy-free"
            or single value e.g. "vegan"
    Output: confirmation string.
    """
    prefs = [p.strip().lower() for p in preferences.split(",")]
    set_dietary(prefs)
    return f"Dietary preferences set: {', '.join(prefs)}"
@tool
def tool_check_dietary_conflict(item_json: str) -> str:
    """
    Check whether a specific item conflicts with the customer's
    dietary preferences stored in this session.
    Call this after search returns results that might conflict —
    especially before recommending any item to a customer who has
    stated dietary preferences.
    Input:  JSON string of item dict with allergens and dietary_tags
    Output: one of three results:
              clear    — no conflict, safe to recommend
              conflict — states exactly what conflicts and why
              unknown  — no dietary data recorded for this item
    """
    try:
        item     = json.loads(item_json)
        dietary  = get_dietary()

        if not dietary:
            return "clear | no dietary preferences set this session"

        allergens    = item.get("allergens", [])
        dietary_tags = item.get("dietary_tags", [])

        if not allergens and not dietary_tags:
            return f"unknown | no dietary data recorded for {item.get('name', 'this item')}"

        conflicts = []

        # check each dietary preference against item data
        if "vegan" in dietary:
            if "vegan" not in dietary_tags:
                # find which allergen is causing the conflict
                non_vegan = [a for a in allergens if a in ("milk", "eggs")]
                if non_vegan:
                    conflicts.append(
                        f"not vegan — contains {', '.join(non_vegan)}"
                    )
                else:
                    conflicts.append("not vegan")

        if "dairy-free" in dietary:
            if "dairy-free" not in dietary_tags:
                if "milk" in allergens:
                    conflicts.append("contains dairy — not dairy-free")

        if "gluten-free" in dietary:
            if "gluten-free" not in dietary_tags:
                if "gluten" in allergens or "oats" in allergens:
                    conflicts.append(
                        f"contains gluten — not gluten-free"
                    )

        if "vegetarian" in dietary:
            if "vegetarian" not in dietary_tags:
                conflicts.append("not vegetarian")

        if conflicts:
            return (
                f"conflict | {item.get('name', 'item')} | "
                f"{' | '.join(conflicts)}"
            )

        return f"clear | {item.get('name', 'item')} is compatible with your dietary preferences"

    except json.JSONDecodeError as e:
        return f"Error parsing item data: {e}"
@tool
def tool_find_vegan_alternative(drink_name: str) -> str:
    """
    Find a dairy-free milk swap for a specific drink that conflicts
    with the customer's vegan or dairy-free dietary preference.
    Call this when:
      - customer requests a specific drink by name
      - that drink has a dietary conflict with their stated preferences
      - the drink has customisable: True and base_milk is not "none"
    Input:  drink name string e.g. "Caramel Latte"
    Output: JSON string with original drink info + compatible swap options
            or a message if no swap is available.
    """
    try:
       
        drinks_meta = _indexes["drinks"]["meta"]

        drink = next(
            (d for d in drinks_meta
             if d["name"].lower() == drink_name.lower().strip()),
            None
        )

        if drink is None:
            return f"Could not find '{drink_name}' in drinks catalog."

        # check if drink is customisable
        if not drink.get("customisable", False):
            return (
                f"{drink['name']} is not customisable — "
                f"no milk swap available. "
                f"Suggest a naturally dairy-free alternative instead."
            )

        # check base milk
        base_milk = drink.get("base_milk", "none")
        if base_milk == "none":
            return f"{drink['name']} contains no milk — already dairy-free."

        # search customizations for compatible milk swaps
        swap_results = search_customizations(
            f"dairy-free milk alternative vegan swap {base_milk}", k=5
        )

        # filter by dietary resolution and compatibility
        compatible = [
            c for c in swap_results
            if "vegan" in c.get("dietary_tags", [])
            and c.get("replaces") == base_milk
            and drink.get("id") in c.get("compatible_with", [])
        ]

        if not compatible:
            # relax compatibility filter — check replaces field only
            compatible = [
                c for c in swap_results
                if "vegan" in c.get("dietary_tags", [])
                and c.get("replaces") == base_milk
            ]

        if not compatible:
            return (
                f"No compatible milk swap found for {drink['name']}. "
                f"Suggest a naturally dairy-free drink instead."
            )

        result = {
            "drink":            drink["name"],
            "drink_id":         drink["id"],
            "conflict":         f"contains {base_milk.replace('_', ' ')}",
            "swaps":            [
                {
                    "id":    c["id"],
                    "name":  c["name"],
                    "price": c["price"],
                    "upsell_line": c.get("upsell_line", ""),
                }
                for c in compatible
            ],
            "prices_with_swap": {
                size: round(price + compatible[0]["price"], 0)
                for size, price in drink["prices"].items()
            }
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error finding alternative: {e}"
@tool
def tool_build_vegan_combo(query: str) -> str:
    """
    Build the best drink recommendation for a customer with dietary
    preferences who has described a vague craving.
    Searches drinks, checks each result for dietary conflicts,
    finds milk swaps where needed, and returns two options:
      option_1 — safest pick (already compatible, no swap needed)
      option_2 — best flavour match (may need a swap to be compatible)
    Call this when:
      - customer has stated dietary preferences (vegan, dairy-free)
      - customer describes what they want without naming a specific drink
      e.g. "something creamy and sweet but vegan"
    Input:  natural language query string
    Output: JSON with two candidate pitches for agent to present.
    """
    try:
        dietary = get_dietary()

        if not dietary:
            return (
                "No dietary preferences set — "
                "use tool_search_drinks for general recommendations."
            )

        # search drinks
        results = search_drinks(query, k=5)

        if not results:
            return "No drinks found matching that description."

        direct_options = []    # already compatible
        combo_options  = []    # compatible with swap

        for drink in results:
            # check dietary conflict
            conflict_check = tool_check_dietary_conflict.invoke(json.dumps(drink)
            if not tool_check_dietary_conflict.invoke(
                    json.dumps(drink)
                ).startswith("Error")
                else '{"allergens": [], "dietary_tags": []}'
            ) if False else tool_check_dietary_conflict.invoke(
                json.dumps(drink)
            )

            if conflict_check.startswith("clear"):
                direct_options.append({
                    "drink":  drink,
                    "type":   "direct",
                    "pitch":  f"{drink['name']} is already {', '.join(dietary)}"
                })

            elif conflict_check.startswith("conflict"):
                # try to find a swap
                if drink.get("customisable", False):
                    swap_result = tool_find_vegan_alternative.invoke(
                        drink["name"]
                    )
                    if not swap_result.startswith("No compatible") \
                       and not swap_result.startswith("Could not"):
                        swap_data = json.loads(swap_result)
                        combo_options.append({
                            "drink":     drink,
                            "swap_data": swap_data,
                            "type":      "combo",
                            "pitch":     (
                                f"{drink['name']} with "
                                f"{swap_data['swaps'][0]['name']} swap"
                            )
                        })

        # build response — one direct + one combo if available
        output = {}

        if direct_options:
            best_direct = direct_options[0]
            d = best_direct["drink"]
            output["option_1"] = {
                "type":        "direct",
                "name":        d["name"],
                "prices":      d["prices"],
                "dietary":     d["dietary_tags"],
                "pitch":       best_direct["pitch"],
                "score":       d["score"],
            }

        if combo_options:
            best_combo = combo_options[0]
            d          = best_combo["drink"]
            swap       = best_combo["swap_data"]
            output["option_2"] = {
                "type":             "combo",
                "name":             d["name"],
                "base_prices":      d["prices"],
                "swap":             swap["swaps"][0],
                "prices_with_swap": swap["prices_with_swap"],
                "pitch":            best_combo["pitch"],
                "score":            d["score"],
            }

        if not output:
            return (
                "No compatible drinks found for your dietary preferences. "
                "Try a different description."
            )

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"Error building combo: {e}"
# ── Export all tools ──────────────────────────────────────────────────────────
ALL_TOOLS = [
    tool_search_drinks,
    tool_search_cookies,
    tool_search_customizations,
    tool_add_drink_to_basket,
    tool_add_cookie_to_basket,
    tool_remove_from_basket,
    tool_view_basket,
    tool_checkout,
    tool_set_session_budget,
    tool_check_budget_fit,
    tool_suggest_upsell,
    tool_set_dietary_preferences,
    tool_check_dietary_conflict,
    tool_find_vegan_alternative,
    tool_build_vegan_combo,
]