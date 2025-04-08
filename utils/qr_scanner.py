import cv2
import os
def read_qr_code_wechat(image_path):
    """Reads QR codes using WeChat's advanced detector."""
    detect_prototxt = "models/wechat_qr/detect.prototxt"
    detect_model = "models/wechat_qr/detect.caffemodel"

    if not os.path.exists(detect_prototxt): 
        print("❌ WeChat detect_prototxt files not found.")
        return None
    if not os.path.exists(detect_model):
        print("❌ WeChat Qdetect_model files not found.")
        return None
    detector = cv2.wechat_qrcode_WeChatQRCode(detect_prototxt, detect_model)
    img = cv2.imread(image_path)

    if img is None:
        print(f"❌ Cannot load image: {image_path}")
        return None

    qr_codes, points = detector.detectAndDecode(img)
    if qr_codes:
        print(f"✅ QR Code Detected: {qr_codes[0]}")
        return qr_codes[0]
    else:
        print("❌ No QR code found using WeChat detector.")
        return None

