import tkinter as tk
from tkinter import Label, Button
from PIL import Image, ImageTk
from utils.pdf_printing import extract_and_print_pdf_page
from utils.qr_scanner import read_qr_code_wechat
from src.extract_customer_info import extract_all_customer_orders
from src.fetch_shipping_label import fetch_shipping_label
import cv2
import os
import time
import sys

class LogoRecognitionApp:
    def __init__(self, frame):
        self.root = frame
        self.root.configure(bg="white")
        self.last_scanned_sku = None
        self.last_scan_time = 0

        video_frame = tk.Frame(frame, bg="white")
        video_frame.pack(side=tk.TOP, padx=10, pady=10)
        self.video_label = Label(video_frame, text="Camera live preview", bg="gray")
        self.video_label.pack(padx=10, pady=5)

        self.qr_code_label = Label(frame, text="", bg="white", font=("Arial", 12), fg="purple")
        self.qr_code_label.pack(pady=5)

        self.product_label = Label(frame, text="", bg="white", font=("Arial", 14, "bold"), fg="green")
        self.product_label.pack(pady=10)

        scroll_container = tk.Frame(frame)
        scroll_container.pack(pady=10, fill=tk.BOTH, expand=True)

        self.log_scroll_canvas = tk.Canvas(scroll_container, bg="white")
        self.log_scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=self.log_scroll_canvas.yview)
        self.log_scrollable_frame = tk.Frame(self.log_scroll_canvas, bg="white")

        self.log_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.log_scroll_canvas.configure(scrollregion=self.log_scroll_canvas.bbox("all"))
        )

        self.log_scroll_window = self.log_scroll_canvas.create_window((0, 0), window=self.log_scrollable_frame, anchor="nw")
        self.log_scroll_canvas.configure(yscrollcommand=self.log_scrollbar.set)

        self.log_scroll_canvas.pack(side="left", fill="both", expand=True)
        self.log_scrollbar.pack(side="right", fill="y")

        self.summary_label = Label(frame, text="Total products: 0 Total labels: 0", bg="white", font=("Arial", 12, "bold"), fg="black", justify="right")
        self.summary_label.pack(pady=5, anchor="ne")

        self.shipping_label = Label(frame, text="", bg="white", font=("Arial", 10), fg="blue")
        self.shipping_label.pack(pady=10)

        self.process_button = Button(frame, text="Start Webcam Scan", command=self.open_webcam_preview, bg="orange", fg="white", font=("Arial", 12))
        self.process_button.pack(pady=10)

        self.reset_button = Button(frame, text="Reset", command=self.reset_fields, bg="red", fg="white", font=("Arial", 12))
        self.reset_button.pack(pady=10)

        self.orders = extract_all_customer_orders()
        self.scan_counts = {}
        self.completed_orders = set()
        self.cap = None
        self.detector = None

        self.render_all_customers()

    def resource_path(self, relative_path):
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        return os.path.join(base_path, relative_path)

    def open_webcam_preview(self):
        prototxt = self.resource_path("models/wechat_qr/detect.prototxt")
        model = self.resource_path("models/wechat_qr/detect.caffemodel")
        if not os.path.exists(prototxt) or not os.path.exists(model):
            self.qr_code_label.config(text="❌ QR model not found", fg="red")
            return

        self.detector = cv2.wechat_qrcode_WeChatQRCode(prototxt, model)
        self.cap = cv2.VideoCapture(0)
        self.update_frame()

    def update_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                imgtk = ImageTk.PhotoImage(image=img.resize((480, 320)))
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)

                qr_codes, _ = self.detector.detectAndDecode(frame)
                if qr_codes:
                    sku = qr_codes[0].strip().lower()
                    now = time.time()
                    if sku != self.last_scanned_sku or (now - self.last_scan_time) > 2:
                        self.last_scanned_sku = sku
                        self.last_scan_time = now
                        self.qr_code_label.config(text=f"QR Detected: {sku}", fg="green")
                        self.process_order(sku)
        self.root.after(50, self.update_frame)

    def process_order(self, sku):
        self.last_scanned_sku = sku.strip().lower()
        self.product_label.config(text=f"Product/SKU: {sku}", fg="green")
        for order in self.orders:
            for item in order["items"]:
                if item["sku"].strip().lower() == sku:
                    key = (order["name"], item["sku"])
                    scanned = self.scan_counts.get(key, 0)
                    if scanned < item["quantity"]:
                        self.scan_counts[key] = scanned + 1
        self.render_all_customers()
        self.log_scroll_canvas.update_idletasks()
        if self.focus_target:
            if self.focus_target:
                self.log_scroll_canvas.update_idletasks()
            self.log_scroll_canvas.yview_moveto(
                self.focus_target.winfo_y() / self.log_scrollable_frame.winfo_height()
            )

    def manual_print(self, customer_name):
        name_title = customer_name.strip().title()
        page = fetch_shipping_label(name_title)
        if page is not None:
            extract_and_print_pdf_page(page_number=page, copies=1)
            self.completed_orders.add(customer_name.strip().lower())
            self.shipping_label.config(text=f"✅ Printed manually for {customer_name}", fg="blue")
        else:
            self.shipping_label.config(text=f"⚠️ Could not fetch label for {customer_name}", fg="red")
        self.render_all_customers()

    def render_all_customers(self):
        self.focus_target = None
        for widget in self.log_scrollable_frame.winfo_children():
            widget.destroy()

        for order in self.orders:
            customer_name = order["name"]
            normalized_name = customer_name.strip().lower()
            frame = tk.Frame(self.log_scrollable_frame, bg="white")
            frame.pack(anchor="w", fill=tk.X, padx=10, pady=5)
            if any(item["sku"].strip().lower() == self.last_scanned_sku for item in order["items"]):
                self.focus_target = frame

            Label(frame, text=customer_name, font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
            all_scanned = True
            for item in order["items"]:
                key = (customer_name, item["sku"])
                scanned = self.scan_counts.get(key, 0)
                needed = item["quantity"]
                status = "✔" if scanned >= needed else "✖"
                line = f"    {status}  {item['product']} ({item['sku']}): {scanned}/{needed}"
                Label(frame, text=line, anchor="w", justify="left", font=("Arial", 9), bg="white").pack(anchor="w")
                if scanned < needed:
                    all_scanned = False

            if all_scanned:
                if normalized_name not in self.completed_orders:
                    page = fetch_shipping_label(customer_name.strip().title())
                    if page is not None:
                        extract_and_print_pdf_page(page_number=page, copies=1)
                        self.completed_orders.add(normalized_name)
                        Label(frame, text=f"✅ Auto-printed label for {customer_name}", fg="green", bg="white").pack(anchor="w")
                    else:
                        Label(frame, text=f"⚠️ Could not fetch label for {customer_name}", fg="orange", bg="white").pack(anchor="w")
                else:
                    Label(frame, text=f"✅ Already printed label for {customer_name}", fg="gray", bg="white").pack(anchor="w")

            btn = Button(frame, text="PRINT", fg="red", bg="white", relief="groove",
                         command=lambda name=customer_name: self.manual_print(name))
            btn.pack(anchor="w", padx=5)

        self.update_summary()

    def update_summary(self):
        scanned_products = 0
        scanned_labels = 0
        printed_customers = len(self.completed_orders)
        total_products = sum(len(order["items"]) for order in self.orders)
        total_labels = sum(item["quantity"] for order in self.orders for item in order["items"])

        for order in self.orders:
            for item in order["items"]:
                key = (order["name"], item["sku"])
                scanned = self.scan_counts.get(key, 0)
                if scanned > 0:
                    scanned_products += 1
                    scanned_labels += scanned

        self.summary_label.config(
            text=f"Scanned: {scanned_products}/{total_products} products, {printed_customers}/{len(self.orders)} labels"
        )

    def reset_fields(self):
        self.product_label.config(text="")
        self.qr_code_label.config(text="")
        self.shipping_label.config(text="")
        for widget in self.log_scrollable_frame.winfo_children():
            widget.destroy()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_label.config(image="")
        self.render_all_customers()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    root.configure(bg="white")

    canvas = tk.Canvas(root, borderwidth=0, background="white")
    frame = tk.Frame(canvas, background="white")
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((0, 0), window=frame, anchor="nw", width=1000)

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    frame.bind("<Configure>", on_frame_configure)

    app = LogoRecognitionApp(frame)
    root.mainloop()
