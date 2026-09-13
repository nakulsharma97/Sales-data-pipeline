"""
Product catalog: maps each product to a category.

Single source of truth for the ETL (adds the category column) and the
dashboard (category filter). Keep names in sync with generate_data.py.
"""

PRODUCT_CATEGORIES = {
    "Bread": "Bakery",
    "Cookies": "Bakery",
    "Milk": "Dairy",
    "Cheese": "Dairy",
    "Yogurt": "Dairy",
    "Eggs": "Dairy",
    "Apple": "Produce",
    "Banana": "Produce",
    "Tomato": "Produce",
    "Lettuce": "Produce",
    "Olive Oil": "Pantry",
    "Rice": "Pantry",
    "Pasta": "Pantry",
    "Sugar": "Pantry",
    "Salt": "Pantry",
    "Chicken": "Meat & Fish",
    "Canned Tuna": "Meat & Fish",
    "Mineral Water": "Beverages",
    "Beer": "Beverages",
    "Red Wine": "Beverages",
    "Coffee": "Beverages",
    "Tea": "Beverages",
    "Chocolate": "Snacks",
    "Toilet Paper": "Household",
}

CATEGORIES = sorted(set(PRODUCT_CATEGORIES.values()))
