import pandas as pd
from PIL import Image, ImageOps
import os
import math
import tkinter as tk
from tkinter import ttk

from datetime import datetime

# === Config ===
CSV_FILE = 'data.csv'
QR_PREFIX = ''
IMG_EXT = '.png'
LOGO_FOLDER = 'logos'
DPI = 300

# === Output with datetime folder ===
base_output = 'a4_output'
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_FOLDER = os.path.join(base_output, timestamp)


# === A4 size in pixels (21cm × 29.7cm at 300 DPI) ===
A4_WIDTH = int(21 / 2.54 * DPI)     # ≈ 2480 px
A4_HEIGHT = int(29.7 / 2.54 * DPI)  # ≈ 3508 px

# === Grid and Layout ===
GRID_COLS, GRID_ROWS = 2, 3
LOGOS_PER_PAGE = GRID_COLS * GRID_ROWS

# === Bottom Margin ===
BOTTOM_MARGIN_CM = 5
BOTTOM_MARGIN_PX = int((BOTTOM_MARGIN_CM / 2.54) * DPI)
DRAW_HEIGHT = A4_HEIGHT - BOTTOM_MARGIN_PX

# === GUI: Select a logo subfolder via dropdown ===
def choose_subfolder(folder):
    subfolders = [f.name for f in os.scandir(folder) if f.is_dir()]
    if not subfolders:
        raise Exception("❌ No subfolders found inside 'logos/'")

    subfolders.insert(0, "All")  # Add "All" option

    root = tk.Tk()
    root.title("Select Logo Subfolder")

    selected = tk.StringVar(root)
    selected.set(subfolders[0])

    ttk.Label(root, text="Select a subfolder with logos:").pack(padx=20, pady=10)
    dropdown = ttk.Combobox(root, textvariable=selected, values=subfolders, state="readonly")
    dropdown.pack(padx=20, pady=10)

    def confirm_selection():
        root.quit()
        root.destroy()

    ttk.Button(root, text="OK", command=confirm_selection).pack(padx=20, pady=10)
    root.mainloop()

    return selected.get()

# === Image Finder (search recursively in given root folder) ===
def find_logo_file(root_folder, target_filename):
    for root, _, files in os.walk(root_folder):
        if target_filename in files:
            return os.path.join(root, target_filename)
    return None

# === Prepare Output Folder ===
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Get folder to search ===
selection = choose_subfolder(LOGO_FOLDER)
if selection == "All":
    search_folder = LOGO_FOLDER  # search all subfolders
else:
    search_folder = os.path.join(LOGO_FOLDER, selection)

# === Load CSV and Expand Image List ===
df = pd.read_csv(CSV_FILE)
images = []
missing = []

for _, row in df.iterrows():
    sku = str(row['Lineitem SKU']).strip()
    qty = int(row['Lineitem quantity'])

    filename = f"{QR_PREFIX}QR{sku}{IMG_EXT}"
    filepath = find_logo_file(search_folder, filename)

    if filepath:
        images.extend([filepath] * qty)
    else:
        print(f"⚠️ File not found: {filename}")
        missing.append(filename)

# === Generate A4 Pages ===
total_pages = math.ceil(len(images) / LOGOS_PER_PAGE)

for page_num in range(total_pages):
    canvas = Image.new('RGBA', (A4_WIDTH, A4_HEIGHT), (255, 255, 255, 0))  # white A4 background

    # Grid slot size
    slot_w = A4_WIDTH // GRID_COLS
    slot_h = DRAW_HEIGHT // GRID_ROWS

    for i in range(LOGOS_PER_PAGE):
        idx = page_num * LOGOS_PER_PAGE + i
        if idx >= len(images):
            break

        img_path = images[idx]
        logo = Image.open(img_path).convert("RGBA")
        logo = ImageOps.mirror(logo)  # Mirror horizontally

        # Resize while maintaining aspect ratio
        logo_ratio = logo.width / logo.height
        slot_ratio = slot_w / slot_h

        if logo_ratio > slot_ratio:
            new_w = slot_w
            new_h = int(slot_w / logo_ratio)
        else:
            new_h = slot_h
            new_w = int(slot_h * logo_ratio)

        logo = logo.resize((new_w, new_h), Image.LANCZOS)

        # Center in slot
        col = i % GRID_COLS
        row = i // GRID_COLS
        x = col * slot_w + (slot_w - new_w) // 2
        y = row * slot_h + (slot_h - new_h) // 2

        canvas.paste(logo, (x, y), logo if logo.mode == 'RGBA' else None)

    out_path = os.path.join(OUTPUT_FOLDER, f"A4_Page_{page_num + 1}.png")
    canvas.save(out_path, dpi=(DPI, DPI))  # Set DPI metadata

# === Save missing log ===
if missing:
    with open(os.path.join(OUTPUT_FOLDER, "missing_logos.txt"), "w") as f:
        f.write("\n".join(missing))

print(f"✅ Done. Created {total_pages} A4 page(s) in '{OUTPUT_FOLDER}' folder.")
if missing:
    print(f"⚠️ Missing {len(missing)} logo(s). See 'missing_logos.txt' for details.")
