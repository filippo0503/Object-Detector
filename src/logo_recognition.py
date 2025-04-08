import cv2
import os
import sys

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

def recognize_qr_code(image_path):
    """Scans the QR code in the image and returns its decoded data."""
    img = cv2.imread(image_path)
    if img is None:
        print("❌ Error reading image!")
        return None

    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)

    if bbox is not None and data:
        print(f"✅ QR Code detected: {data}")
        return data
    else:
        print("❌ No QR code found.")
        return None
