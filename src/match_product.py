import pandas as pd
import os
import sys
import re

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller package.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

PRODUCT_DB_PATH = resource_path("data/product_database.csv")

def match_product(logo_name):
    """Matches the recognized logo with the product in the database."""
    df = pd.read_csv(PRODUCT_DB_PATH)
    print(df)
    product_row = df[df['product_image'].str.contains(re.escape(logo_name), na=False)]
    print("Product_row",product_row)
    return product_row.iloc[0]['product_name'] if not product_row.empty else None

if __name__ == "__main__":
    print(match_product("crown"))
