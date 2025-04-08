import tkinter as tk
from tkinter import filedialog, Label, Button, Text
from PIL import Image, ImageTk
from utils.pdf_printing import extract_and_print_pdf_page
from utils.qr_scanner import read_qr_code_wechat
from src.extract_customer_info import extract_all_customer_orders
from src.fetch_shipping_label import fetch_shipping_label
import cv2
import os

class LogoRecognitionApp:
    def __init__(self, root):
        self.last_scanned_sku = None
        self.root = root
        self.root.title("Product SKU Scanner & Shipping Label System")
        self.root.geometry("1000x700")
        self.root.configure(bg="white")

        self.video_label = Label(root, text="Live Camera Feed", bg="gray")
        self.video_label.pack(pady=5)

        # self.upload_button = Button(root, text="Upload Product Image", command=self.upload_image, bg="blue", fg="white", font=("Arial", 12))
        # self.upload_button.pack(pady=10)

        # self.image_label = Label(root, text="Uploaded Image Will Appear Here", bg="white", font=("Arial", 10))
        # self.image_label.pack()

        self.qr_code_label = Label(root, text="", bg="white", font=("Arial", 12), fg="purple")
        self.qr_code_label.pack(pady=5)

        self.product_label = Label(root, text="", bg="white", font=("Arial", 14, "bold"), fg="green")
        self.product_label.pack(pady=10)

        # Scrollable Text Frame for Customer Details
        text_frame = tk.Frame(root)
        text_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        self.customer_details_text = Text(text_frame, width=90, height=15, bg="white", font=("Arial", 11), fg="black", wrap=tk.WORD)
        self.customer_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = tk.Scrollbar(text_frame, command=self.customer_details_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.customer_details_text.config(yscrollcommand=self.scrollbar.set)

        self.shipping_label = Label(root, text="", bg="white", font=("Arial", 10), fg="blue")
        self.shipping_label.pack(pady=10)

        self.process_button = Button(root, text="Start Webcam Scan", command=self.open_webcam_preview, bg="orange", fg="white", font=("Arial", 12))
        self.process_button.pack(pady=10)

        self.reset_button = Button(root, text="Reset", command=self.reset_fields, bg="red", fg="white", font=("Arial", 12))
        self.reset_button.pack(pady=10)

        self.image_path = None
        self.orders = extract_all_customer_orders()
        self.scan_counts = {}  # (customer_name, sku) -> scanned count
        self.completed_orders = set()
        self.cap = None
        self.detector = None

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.png;*.jpeg")])
        if file_path:
            self.display_image(file_path)
            self.image_path = file_path
            self.process_order()

    def open_webcam_preview(self):
        prototxt = "models/wechat_qr/detect.prototxt"
        model = "models/wechat_qr/detect.caffemodel"
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
                qr_codes, _ = self.detector.detectAndDecode(frame)
                if qr_codes:
                    sku = qr_codes[0]
                    self.qr_code_label.config(text=f"QR Detected: {sku}", fg="green")
                    cv2.imwrite("images/scanned_products/webcam_capture.jpg", frame)
                    self.image_path = "images/scanned_products/webcam_capture.jpg"
                    self.process_order(sku)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                imgtk = ImageTk.PhotoImage(image=img.resize((480, 320)))
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
        self.root.after(50, self.update_frame)

    def display_image(self, path):
        image = Image.open(path)
        image = image.resize((300, 300), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo

    def process_order(self, sku=None):
        if not sku and not self.image_path:
            self.product_label.config(text="No image selected or captured!", fg="red")
            return
        if not sku:
            sku = read_qr_code_wechat(self.image_path)
            if not sku:
                self.qr_code_label.config(text="QR code not detected!", fg="red")
                return

        display_lines = []

        for order in self.orders:
            customer_name = order["name"]
            normalized_name = customer_name.strip().lower()
            display_lines.append(f"{customer_name}")
            for item in order["items"]:
                key = (customer_name, item["sku"])
                scanned = self.scan_counts.get(key, 0)
                needed = item["quantity"]
                if scanned >= needed:
                    display_lines.append(f"  ✔ {item['product']} ({item['sku']}): {scanned}/{needed}")
                else:
                    display_lines.append(f"  ✖ {item['product']} ({item['sku']}): {scanned}/{needed}")

            for item in order["items"]:
                if item["sku"] == sku:
                    key = (customer_name, sku)
                    scanned = self.scan_counts.get(key, 0)
                    if scanned < item["quantity"]:
                      scanned += 1
                      self.scan_counts[key] = scanned
                      self.last_scanned_sku = sku

            all_scanned = all(
                self.scan_counts.get((customer_name, i["sku"]), 0) >= i["quantity"]
                for i in order["items"]
            )
            if all_scanned and normalized_name not in self.completed_orders:
                page = fetch_shipping_label(customer_name.strip().title())

                if page is not None:
                    extract_and_print_pdf_page(page_number=page, copies=1)
                    self.completed_orders.add(normalized_name)
                    display_lines.append(f"  ✅ Order complete for {customer_name}")
                else:
                    display_lines.append(f"  ⚠️ Could not fetch label for {customer_name}")
            elif all_scanned and normalized_name in self.completed_orders:
                display_lines.append(f"  ✅ Already printed label for {customer_name}")

            display_lines.append("")

        self.customer_details_text.config(state=tk.NORMAL)
        self.customer_details_text.delete("1.0", tk.END)
        self.customer_details_text.insert(tk.END, "\n".join(display_lines))
        self.product_label.config(text=f"Product/SKU: {sku}", fg="green")
        self.shipping_label.config(text="✅ Scan complete. Waiting for next...", fg="green")

    def reset_fields(self):
        self.image_path = None
        # self.image_label.config(image="", text="Uploaded Image Will Appear Here")
        self.product_label.config(text="")
        self.customer_details_text.delete("1.0", tk.END)
        self.shipping_label.config(text="")
        self.qr_code_label.config(text="")
        if self.cap:
            self.cap.release()
            self.cap = None
        self.video_label.config(image="")

if __name__ == "__main__":
    root = tk.Tk()
    app = LogoRecognitionApp(root)
    root.mainloop()
