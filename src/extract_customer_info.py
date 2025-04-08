import pandas as pd
import os
import sys
from typing import List, Dict

def resource_path(relative_path):
    """Get absolute path for PyInstaller compatibility."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

CSV_ORDERS_PATH = resource_path("data/orders.csv")

def extract_all_customer_orders() -> List[Dict]:
    """
    Extract all customer orders from a CSV file with SKU-based product lines.
    Returns a list of dictionaries with customer details and item list.
    """
    customer_orders = []

    df = pd.read_csv(CSV_ORDERS_PATH, quoting=1, on_bad_lines='skip', engine='python')

    grouped = df.groupby("Order ID")
    for order_id, group in grouped:
        first_row = group.iloc[0]
        name = f"{first_row['First name']} {first_row['Last name']}"
        address_parts = [
            str(first_row.get("Shipping address line1", "")),
            str(first_row.get("Shipping address line2", "")),
            str(first_row.get("Shipping address line3", "")),
            str(first_row.get("Shipping address city", "")),
            str(first_row.get("Shipping address region", "")),
            str(first_row.get("Shipping address post code", "")),
            str(first_row.get("Shipping address country", ""))
        ]
        address = "\n".join([part for part in address_parts if part and part.strip()])

        items = []
        for _, row in group.iterrows():
            product = str(row["Lineitem name"]).strip()
            sku = str(row["Lineitem SKU"]).strip()
            qty = int(row["Lineitem quantity"])
            items.append({"product": product, "sku": sku, "quantity": qty})

        customer_orders.append({"name": name, "address": address, "items": items})

    return customer_orders

if __name__ == "__main__":
    import json
    orders = extract_all_customer_orders()
    print(json.dumps(orders, indent=2))
