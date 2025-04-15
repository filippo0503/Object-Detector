import pandas as pd
import os
from PIL import Image
from datetime import datetime
import tkinter as tk
from tkinter import ttk

# --- CONFIGURATION ---
CSV_PATH = 'data.csv'
LOGO_FOLDER = 'logos/'
BASE_OUTPUT_FOLDER = 'output/'
BOTTOM_MARGIN_CM = 5
DPI = 300
BOTTOM_MARGIN_PX = int((BOTTOM_MARGIN_CM / 2.54) * DPI)  # ≈ 590 px
FULL_A4 = (2480, 3508)  # Full A4 at 300 DPI
A4_SIZE = (FULL_A4[0], FULL_A4[1] - BOTTOM_MARGIN_PX)
GRID = (3, 4)  # 3 columns × 4 rows = 12 slots

# SKU Prefix → layout block (width × height)
layout_rules = {
    'SCKPO3_': {'name': 'socks', 'block': (3, 2)},
    'SND_': {'name': 'hats', 'block': (3, 2)},
}

# Timestamped output folder
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
OUTPUT_FOLDER = os.path.join(BASE_OUTPUT_FOLDER, timestamp)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Pillow version compatibility
try:
    resample_filter = Image.Resampling.LANCZOS
except AttributeError:
    resample_filter = Image.ANTIALIAS

# --- UI for selecting logo subfolder ---
def choose_subfolder(folder_root):
    subfolders = [f.name for f in os.scandir(folder_root) if f.is_dir()]
    subfolders.sort()
    subfolders.insert(0, "All")  # Add "All" at top

    root = tk.Tk()
    root.title("Select Logo Subfolder")
    root.geometry("300x120")

    selected = tk.StringVar(root)
    selected.set(subfolders[0])

    ttk.Label(root, text="Choose logo subfolder:").pack(padx=10, pady=(10, 5))
    dropdown = ttk.Combobox(root, textvariable=selected, values=subfolders, state="readonly")
    dropdown.pack(padx=10, pady=5)

    def on_select():
        root.quit()
        root.destroy()

    ttk.Button(root, text="Confirm", command=on_select).pack(padx=10, pady=10)
    root.mainloop()

    return selected.get()

# Get folder selection from user
selected = choose_subfolder(LOGO_FOLDER)
if selected == "All":
    search_folders = [LOGO_FOLDER]
    search_folders += [os.path.join(LOGO_FOLDER, f.name) for f in os.scandir(LOGO_FOLDER) if f.is_dir()]
else:
    search_folders = [os.path.join(LOGO_FOLDER, selected)]

# Helper to find image across all search folders
def find_image(folders, filename):
    for folder in folders:
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            return path
    return None

# Load CSV
df = pd.read_csv(CSV_PATH)[['Lineitem SKU', 'Lineitem quantity']]

def get_layout_rule(sku):
    for prefix, rule in layout_rules.items():
        if sku.startswith(prefix):
            return rule
    return None

# Build logo pair list
logo_pairs = []
for _, row in df.iterrows():
    sku = row['Lineitem SKU']
    qty = int(row['Lineitem quantity'])
    rule = get_layout_rule(sku)
    if not rule:
        print(f"⚠️ Unknown SKU prefix: {sku}")
        continue

    base = os.path.splitext(sku)[0]
    qr_path = find_image(search_folders, f"QR{base}.png")
    plain_path = find_image(search_folders, f"{base}.png")

    if not qr_path or not plain_path:
        print(f"⚠️ Missing image(s) for: {sku}")
        continue

    for _ in range(qty):
        logo_pairs.append({
            'sku': sku,
            'qr': qr_path,
            'plain': plain_path,
            'rule': rule
        })

# Calculate slot size
grid_cols, grid_rows = GRID
slot_w = A4_SIZE[0] // grid_cols
slot_h = A4_SIZE[1] // grid_rows

# Determine how many blocks fit per sheet
first_block = layout_rules[next(iter(layout_rules))]
slots_per_block = first_block['block'][0] * first_block['block'][1]
blocks_per_sheet = (grid_cols * grid_rows) // slots_per_block

# Generate A4 sheets
for sheet_idx in range(0, len(logo_pairs), blocks_per_sheet):
    canvas = Image.new("RGBA", FULL_A4, (255, 255, 255, 0))  # Full A4 with transparent background
    current_pairs = logo_pairs[sheet_idx:sheet_idx + blocks_per_sheet]

    for block_idx, pair in enumerate(current_pairs):
        qr_img = Image.open(pair['qr']).convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
        plain_img = Image.open(pair['plain']).convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
        block_w, block_h = pair['rule']['block']

        y_block = block_idx * block_h
        if y_block + block_h > grid_rows:
            break  # prevent overflow

        placed = 0
        for row in range(block_h):
            for col in range(block_w):
                col_mirrored = (block_w - col - 1)
                x = col_mirrored * slot_w
                y = (y_block + row) * slot_h

                # QR first
                if row == 0 and col == 0:
                    resized_qr = qr_img.resize((slot_w, slot_h), resample=resample_filter)
                    canvas.paste(resized_qr, (x, y), mask=resized_qr)
                elif placed < 5:
                    resized_plain = plain_img.resize((slot_w, slot_h), resample=resample_filter)
                    canvas.paste(resized_plain, (x, y), mask=resized_plain)
                    placed += 1

    # Save final image
    out_path = os.path.join(OUTPUT_FOLDER, f"A4_sheet_{sheet_idx // blocks_per_sheet + 1}_MIRRORED_5cmMargin.png")
    canvas.save(out_path, format='PNG', dpi=(DPI, DPI))
    print(f"✅ Saved with 5cm margin: {out_path}")
