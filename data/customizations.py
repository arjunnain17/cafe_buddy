customizations = [

{
"id": "oat_milk_upgrade",
"name": "Oat Milk Upgrade",

"price": 60.0,

"description": "Swap regular milk for creamy barista-grade oat milk. Makes lattes, cappuccinos, matcha lattes and hot chocolate fully dairy-free and vegan. Naturally slightly sweet and produces a smooth creamy foam.",

"tags": [
"dairy-free","vegan","creamy","milk-swap","oat"
],

"allergens": ["oats"],
"dietary_tags": ["vegan","dairy-free","vegetarian"],

"addon_type": "milk_swap",
"replaces": "whole_milk",

"compatible_with": [
"latte",
"cappuccino",
"flat_white",
"mocha",
"iced_latte",
"classic_cold_coffee",
"mocha_cookie_frappe",
"matcha_latte",
"belgian_hot_chocolate"
],

"dietary_resolution": {
"resolves": ["dairy-free","vegan"],
"introduces": ["oats"]
},

"upsell_line": "makes the drink creamier and naturally sweeter than regular milk",

"available": True
},

{
"id": "almond_milk_upgrade",
"name": "Almond Milk Upgrade",

"price": 60.0,

"description": "Replace regular milk with almond milk for a light nutty flavor and dairy-free alternative. Works beautifully in espresso drinks and matcha.",

"tags": [
"dairy-free","vegan","nutty","milk-swap","almond"
],

"allergens": ["nuts"],
"dietary_tags": ["vegan","dairy-free","vegetarian"],

"addon_type": "milk_swap",
"replaces": "whole_milk",

"compatible_with": [
"latte",
"cappuccino",
"flat_white",
"mocha",
"iced_latte",
"classic_cold_coffee",
"matcha_latte",
"belgian_hot_chocolate"
],

"dietary_resolution": {
"resolves": ["dairy-free","vegan"],
"introduces": ["nuts"]
},

"upsell_line": "adds a subtle nutty flavor while making the drink dairy-free",

"available": True
},

{
"id": "extra_espresso_shot",
"name": "Extra Espresso Shot",

"price": 50.0,

"description": "Add an extra espresso shot to boost caffeine and intensify coffee flavor. Perfect for stronger lattes, cappuccinos and iced coffees.",

"tags": [
"coffee","strong","extra-caffeine","espresso","upgrade"
],

"allergens": [],
"dietary_tags": ["vegan","dairy-free","vegetarian"],

"addon_type": "shot",
"replaces": None,

"compatible_with": [
"americano",
"latte",
"cappuccino",
"flat_white",
"mocha",
"iced_latte",
"cold_brew_black",
"classic_cold_coffee",
"mocha_cookie_frappe"
],

"dietary_resolution": {
"resolves": [],
"introduces": []
},

"upsell_line": "gives the drink a stronger coffee kick",

"available": True
},

{
"id": "vanilla_syrup",
"name": "Vanilla Syrup",

"price": 30.0,

"description": "Add smooth vanilla flavored syrup that enhances sweetness and aroma. Popular in lattes, cold coffee and frappes.",

"tags": [
"flavour","sweet","vanilla","syrup","upgrade"
],

"allergens": [],
"dietary_tags": ["vegan","dairy-free","vegetarian"],

"addon_type": "flavour_syrup",
"replaces": None,

"compatible_with": [
"latte",
"cappuccino",
"iced_latte",
"classic_cold_coffee",
"mocha_cookie_frappe",
"matcha_latte",
"cold_brew_black"
],

"dietary_resolution": {
"resolves": [],
"introduces": []
},

"upsell_line": "adds a smooth vanilla sweetness",

"available": True
},

{
"id": "caramel_syrup",
"name": "Caramel Syrup",

"price": 30.0,

"description": "Sweet buttery caramel syrup that turns any coffee into a dessert-style drink with rich caramel flavor.",

"tags": [
"flavour","sweet","caramel","syrup","dessert"
],

"allergens": [],
"dietary_tags": ["vegetarian","dairy-free","vegan"],

"addon_type": "flavour_syrup",
"replaces": None,

"compatible_with": [
"latte",
"cappuccino",
"mocha",
"iced_latte",
"classic_cold_coffee",
"mocha_cookie_frappe"
],

"dietary_resolution": {
"resolves": [],
"introduces": []
},

"upsell_line": "adds rich buttery caramel sweetness",

"available": True
},

{
"id": "hazelnut_syrup",
"name": "Hazelnut Syrup",

"price": 30.0,

"description": "Roasted hazelnut flavored syrup that adds nutty sweetness to coffee drinks like lattes, cappuccinos and cold coffee.",

"tags": [
"flavour","hazelnut","nutty","sweet","syrup"
],

"allergens": ["nuts"],
"dietary_tags": ["vegetarian", "dairy-free","vegan"],

"addon_type": "flavour_syrup",
"replaces": None,

"compatible_with": [
"latte",
"cappuccino",
"mocha",
"iced_latte",
"classic_cold_coffee"
],

"dietary_resolution": {
"resolves": [],
"introduces": ["nuts"]
},

"upsell_line": "adds a warm roasted hazelnut flavor",

"available": True
},

{
"id": "whipped_cream_topping",
"name": "Whipped Cream Topping",

"price": 40.0,

"description": "Light and airy whipped cream topping that makes drinks richer and more indulgent, especially chocolate drinks and frappes.",

"tags": [
"topping","cream","sweet","dessert"
],

"allergens": ["milk"],
"dietary_tags": ["vegetarian"],

"addon_type": "topping",
"replaces": None,

"compatible_with": [
"mocha",
"classic_cold_coffee",
"mocha_cookie_frappe",
"belgian_hot_chocolate"
],

"dietary_resolution": {
"resolves": [],
"introduces": ["milk"]
},

"upsell_line": "adds a rich creamy topping",

"available": True
},

{
"id": "marshmallow_topping",
"name": "Marshmallow Topping",

"price": 40.0,

"description": "Soft marshmallow topping that melts slightly into warm drinks and adds a sweet dessert-like finish.",

"tags": [
"topping","sweet","dessert","marshmallow"
],

"allergens": [],
"dietary_tags": ["vegetarian"],

"addon_type": "topping",
"replaces": None,

"compatible_with": [
"belgian_hot_chocolate",
"mocha",
"mocha_cookie_frappe"
],

"dietary_resolution": {
"resolves": [],
"introduces": []
},

"upsell_line": "adds a soft sweet marshmallow finish",

"available": True
}

]