import PyPDF2
import re
import os
import sys

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller package.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

PURCHASE_RECORDS_PATH = resource_path("data/shipping_labels.pdf")

def fetch_shipping_label(customer_name):
    with open(PURCHASE_RECORDS_PATH, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for  page_number, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            if customer_name in text:
                return page_number+1