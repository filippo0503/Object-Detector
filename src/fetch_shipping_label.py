import PyPDF2
import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller or dev."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

label_pdf = resource_path("data/shipping_labels.pdf")


PURCHASE_RECORDS_PATH = resource_path("data/shipping_labels.pdf")

def fetch_shipping_label(customer_name):
    with open(PURCHASE_RECORDS_PATH, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for  page_number, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            print(text)
            if customer_name in text:
                return page_number+1