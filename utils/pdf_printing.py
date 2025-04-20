from PyPDF2 import PdfReader, PdfWriter
import os
import tempfile
import win32print
import win32api
import threading
import time
import sys
import os

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller or dev."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def extract_and_print_pdf_page(page_number, copies=1, printer_name=None):
    """
    Extract a specific page from shipping_labels.pdf and send it to printer.
    :param page_number: 1-based page number to extract.
    :param copies: Number of copies to print.
    :param printer_name: Specific printer name or None to use default.
    """
    try:
        # Load shipping labels PDF
        pdf_path = resource_path("data/shipping_labels.pdf")
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        if page_number < 1 or page_number > len(reader.pages):
            print("❌ Invalid page number!")
            return

        # Extract specified page
        writer.add_page(reader.pages[page_number - 1])

        # Save temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_pdf_path = temp_file.name
            writer.write(temp_file)

        print(f"✅ Extracted label page: {temp_pdf_path}")

        # Print file using system's default or specified printer
        for _ in range(copies):
            print_file(temp_pdf_path, printer_name)

        # Auto-delete temporary file
        delete_after_delay(temp_pdf_path, delay=60)

    except Exception as e:
        print(f"❌ Error extracting or printing label: {e}")


def print_file(filepath, printer_name=None):
    """
    Send a PDF file directly to printer using Windows native print.
    :param filepath: Path to the PDF file.
    :param printer_name: Optional printer name (None for default printer).
    """
    try:
        if printer_name:
            win32print.SetDefaultPrinter(printer_name)

        # Use default PDF viewer's silent print mode
        win32api.ShellExecute(
            0,
            "print",
            filepath,
            None,
            ".",
            0
        )

        print(f"✅ Sent to printer: {filepath}")

    except Exception as e:
        print(f"❌ Printing failed: {e}")


def delete_after_delay(filepath, delay=60):
    """
    Deletes a file after a delay.
    :param filepath: Path to file to delete.
    :param delay: Seconds to wait before deleting.
    """
    def delayed_delete():
        time.sleep(delay)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"🗑️ Deleted temporary file: {filepath}")

    threading.Thread(target=delayed_delete, daemon=True).start()
