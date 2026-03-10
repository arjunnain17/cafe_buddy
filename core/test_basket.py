import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.basket import (
    set_budget, add_drink, add_cookie,
    view_basket, checkout, get_total
)

drink = {
    "id": "caramel_latte", "name": "Caramel Latte",
    "prices": {"medium": 4.50, "large": 5.25},
}
addon = {
    "id": "oat_milk_upgrade", "name": "Oat Milk Upgrade", "price": 0.60,
}
cookie = {
    "id": "choco_chunk_cookie", "name": "Choco Chunk Cookie", "price": 2.50,
}

set_budget(10.0)
add_drink(drink, "large", [addon])
add_cookie(cookie)

print(view_basket())
print("\n")
print(checkout())

# basket should be empty after checkout
print(get_total())    # 0.0
print(view_basket())  # "Your basket is empty."
