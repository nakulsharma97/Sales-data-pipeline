"""
Script to generate a synthetic sales dataset for the retail sales demo.
Creates a CSV file with 4000 records within the bounded dates (date, product, quantity, price).
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

def generate_dataset(output_path="data/input.csv", n_rows=4000, seed=42):
    np.random.seed(seed)

    # Product catalog (name and base price in €)
    products = [
        ("Bread", 1.20),
        ("Milk", 0.95),
        ("Cheese", 2.60),
        ("Yogurt", 0.55),
        ("Apple", 0.70),
        ("Banana", 0.50),
        ("Tomato", 1.10),
        ("Lettuce", 0.90),
        ("Olive Oil", 6.50),
        ("Rice", 1.30),
        ("Pasta", 1.10),
        ("Chicken", 5.20),
        ("Canned Tuna", 1.40),
        ("Mineral Water", 0.35),
        ("Beer", 0.85),
        ("Red Wine", 5.90),
        ("Sugar", 1.00),
        ("Salt", 0.40),
        ("Eggs", 0.25),
        ("Coffee", 3.80),
        ("Tea", 2.10),
        ("Chocolate", 1.80),
        ("Cookies", 1.50),
        ("Toilet Paper", 0.45),
    ]

    # Dates (January - June 2025)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 6, 30)
    days = (end_date - start_date).days + 1

    # Sample generation
    dates = [
        start_date + timedelta(days=int(x))
        for x in np.random.randint(0, days, size=n_rows)
    ]
    prod_idx = np.random.randint(0, len(products), size=n_rows)

    rows = []
    for i in range(n_rows):
        name, base_price = products[prod_idx[i]]
        price = round(float(base_price * (1 + np.random.uniform(-0.1, 0.1))), 2)
        quantity = int(np.clip(np.random.poisson(4) + 1, 1, 20))
        rows.append((dates[i].strftime("%Y-%m-%d"), name, quantity, price))

    df = pd.DataFrame(rows, columns=["date", "product", "quantity", "price"])

    # Ensure the data/ folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Dataset generated: {output_path} ({len(df)} rows)")

if __name__ == "__main__":
    generate_dataset()