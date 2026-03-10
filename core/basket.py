# core/basket.py

# ── State ─────────────────────────────────────────────────
_basket: list[dict] = []
_budget: float | None = None
_dietary: list[str] = []
_item_counter: int = 0

# ── Budget ────────────────────────────────────────────────
def set_budget(amount: float) -> str:
    """
    Sets the session budget.
    Persists for entire session — does not reset on clear_basket().
    """
    global _budget
    _budget = amount
    return f"Budget set to ₹{amount:.2f}"
def get_budget() -> float | None:
    """Returns the current budget, or None if not set."""
    return _budget
    

# ── Dietary ───────────────────────────────────────────────
def set_dietary(preferences: list[str]) -> str: 
    """
    Sets dietary preferences for the session.
    These are used to filter recommendations and check compatibility of items.
    Persists for entire session — does not reset on clear_basket().
    """
    global _dietary
    _dietary = preferences
    return f"Dietary preferences set: {', '.join(preferences)}"

def get_dietary() -> list[str]:
    """Returns the current dietary preferences."""
    return _dietary

# ── Basket operations ─────────────────────────────────────
def add_drink(drink: dict, size: str, customizations: list[dict]) -> str:
    """
    Adds a drink to the basket with size and customizations resolved.
    Size must be "medium" or "large".
    Customizations can be empty list if no addons selected.
    """
    global _item_counter

    # resolve prices
    base_price = drink["prices"][size]
    addon_total = sum(c["price"] for c in customizations)
    item_total  = round(base_price + addon_total, 2)

    # generate unique basket id
    _item_counter += 1
    basket_id = f"item_{_item_counter:03d}"

    # build basket item
    basket_item = {
        "basket_id":      basket_id,
        "type":           "drink",
        "id":             drink["id"],
        "name":           drink["name"],
        "size":           size,
        "base_price":     base_price,
        "customizations": [
            {
                "id":    c["id"],
                "name":  c["name"],
                "price": c["price"],
            }
            for c in customizations
        ],
        "item_total": item_total,
    }

    _basket.append(basket_item)

    # build confirmation string
    addon_names = ", ".join(c["name"] for c in customizations)
    addon_str   = f" + {addon_names}" if addon_names else ""
    return (
        f"Added {drink['name']} ({size.capitalize()})"
        f"{addon_str} → ${item_total:.2f} "
        f"[{basket_id}]"
    )

def add_cookie(cookie: dict) -> str:
    """
    Adds a cookie to the basket.
    Cookies have no size and no customizations.
    """
    global _item_counter

    _item_counter += 1
    basket_id = f"item_{_item_counter:03d}"

    basket_item = {
        "basket_id":      basket_id,
        "type":           "cookie",
        "id":             cookie["id"],
        "name":           cookie["name"],
        "size":           None,
        "base_price":     cookie["price"],
        "customizations": [],
        "item_total":     cookie["price"],
    }

    _basket.append(basket_item)

    return (
        f"Added {cookie['name']} → ${cookie['price']:.2f} "
        f"[{basket_id}]"
    )

def remove_item(basket_id: str) -> str:
    """
    Removes an item from the basket by basket_id.
    basket_id comes from the confirmation string when item was added
    e.g. "item_001"
    """
    global _basket

    # find the item
    match = next(
        (item for item in _basket if item["basket_id"] == basket_id),
        None
    )

    if match is None:
        return (
            f"Could not find '{basket_id}' in basket. "
            f"Use view_basket() to see current basket ids."
        )

    _basket = [item for item in _basket if item["basket_id"] != basket_id]

    return (
        f"Removed {match['name']} (${match['item_total']:.2f}). "
        f"New total: ${get_total():.2f}"
    )

def get_total() -> float:
    """
    Returns the current basket total.
    Sums item_total across all basket items.
    Returns 0.0 if basket is empty.
    """
    return round(sum(item["item_total"] for item in _basket), 2)

def get_remaining() -> float | None:
    """
    Returns remaining budget after current basket total is subtracted.
    If no budget set, returns None.
    """
    if _budget is None:
        return None
    return round(_budget - get_total(), 2)

def view_basket() -> str:
    """
    Returns a formatted string of the current basket contents.
    Shows each item with its customizations nested underneath.
    Shows running total and remaining budget if set.
    """
    COL = 36  
    if not _basket:
        return "Your basket is empty."

    lines = []

    for item in _basket:
        # ── drink line ────────────────────────────────────────
        if item["type"] == "drink":
            size_str = f" ({item['size'].capitalize()})" if item["size"] else ""
            name_size = f"{item['name']}{size_str}"
            lines.append(f"  {name_size:<{COL}} ${item['base_price']:.2f}  [{item['basket_id']}]")
            for c in item["customizations"]:
                lines.append(f"    + {c['name']:<{COL - 2}} ${c['price']:.2f}")
                if item["customizations"]:
                    lines.append(f"    {'subtotal':<{COL - 2}} ${item['item_total']:.2f}")

                elif item["type"] == "cookie":
                    lines.append(f"  {item['name']:<{COL}} ${item['item_total']:.2f}  [{item['basket_id']}]")

        # ── cookie line ───────────────────────────────────────
        elif item["type"] == "cookie":
            lines.append(
                f"  {item['name']:<35} ${item['item_total']:.2f}"
                f"  [{item['basket_id']}]"
            )

    # ── total ─────────────────────────────────────────────────
    total = get_total()
    lines.append(f"\n  {'─' * 40}")
    lines.append(f"  {'TOTAL':<35} ${total:.2f}")

    # ── budget remaining ──────────────────────────────────────
    if _budget is not None:
        remaining = get_remaining()
        if remaining >= 0:
            lines.append(
                f"  {'Budget remaining':<35} ${remaining:.2f}"
            )
        else:
            lines.append(
                f"  {'Over budget by':<35} ${abs(remaining):.2f}"
            )

    return "\n".join(lines)
    
def clear_basket() -> None:
    """
    Clears basket and resets item counter.
    Does NOT clear budget or dietary preferences —
    those persist for the entire session.
    """
    global _basket, _item_counter
    _basket = []
    _item_counter = 0
def get_remaining() -> float | None:
    """
    Returns remaining budget after current basket total.
    Returns None if no budget set.
    Negative value means over budget.
    """
    if _budget is None:
        return None
    return round(_budget - get_total(), 2)
def checkout() -> str:
    """
    Formats and returns a receipt for the current basket.
    Clears the basket after generating the receipt.
    Returns an error string if basket is empty.
    """
    COL = 36
    if not _basket:
        return "Your basket is empty — nothing to checkout."

    lines = []

    # ── header ────────────────────────────────────────────────
    lines.append("╔══════════════════════════════════════════╗")
    lines.append("║        ☕  CAFE BUDDY RECEIPT             ║")
    lines.append("╠══════════════════════════════════════════╣")

    # ── items ─────────────────────────────────────────────────
    for item in _basket:

        if item["type"] == "drink":
            size_str = f" ({item['size'].capitalize()})" if item["size"] else ""
            name_size = f"{item['name']}{size_str}"
            lines.append(f"  {name_size:<{COL}} ${item['base_price']:.2f}  [{item['basket_id']}]")
            for c in item["customizations"]:
                lines.append(f"    + {c['name']:<{COL - 2}} ${c['price']:.2f}")
                if item["customizations"]:
                    lines.append(f"    {'subtotal':<{COL - 2}} ${item['item_total']:.2f}")

                elif item["type"] == "cookie":
                    lines.append(f"  {item['name']:<{COL}} ${item['item_total']:.2f}  [{item['basket_id']}]")
                elif item["type"] == "cookie":
                    lines.append(
                    f"  {item['name']:<35} ${item['item_total']:.2f}"
            )

        # blank line between items
        lines.append("")

    # ── total ─────────────────────────────────────────────────
    total = get_total()
    lines.append(f"  {'─' * 42}")
    lines.append(f"  {'TOTAL':<35} ${total:.2f}")

    # ── budget summary ────────────────────────────────────────
    if _budget is not None:
        remaining = get_remaining()
        if remaining >= 0:
            lines.append(f"  {'Budget remaining':<35} ${remaining:.2f}")
        else:
            lines.append(f"  {'Over budget by':<35} ${abs(remaining):.2f}")

    # ── footer ────────────────────────────────────────────────
    lines.append("╚══════════════════════════════════════════╝")
    lines.append("  Thanks for your order! Enjoy ☀️")

    receipt = "\n".join(lines)

    # clear basket after receipt generated
    clear_basket()

    return receipt