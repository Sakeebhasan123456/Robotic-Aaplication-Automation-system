##################this below function able to click on the email present in the outlook inbox using ocr and adb commands##########################

# import pytesseract
# import cv2
# import subprocess
# from PIL import Image
# import os
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# device_name = "RZ8T80KSXYD"  # Replace with your actual device ID

# # STEP 1: Capture screenshot
# subprocess.run(["adb", "-s", device_name, "shell", "screencap", "-p", "/sdcard/screen.png"])
# subprocess.run(["adb", "-s", device_name, "pull", "/sdcard/screen.png", "./screen.png"])

# # STEP 2: Load image
# img = cv2.imread("screen.png")

# # STEP 3: OCR with bounding boxes
# data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

# # STEP 4: Find target text and coordinates
# target_text = "historia.laboral"
# found = False

# for i, word in enumerate(data['text']):
#     if target_text in word.lower():
#         x = data['left'][i]
#         y = data['top'][i]
#         w = data['width'][i]
#         h = data['height'][i]

#         center_x = x + w // 2
#         center_y = y + h // 2
#         print(f"✅ Found '{target_text}' at: ({center_x}, {center_y})")

#         # STEP 5: Tap on screen at that location
#         subprocess.run(["adb", "-s", device_name, "shell", "input", "tap", str(center_x), str(center_y)])
#         found = True
#         break

# if not found:
#     print("❌ Email not found via OCR.")












#######################this below function able to click on the email text present in the outlook imss email using ocr and adb commands##########################
# import cv2
# import pytesseract
# import numpy as np
# import subprocess
# from unidecode import unidecode

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# DEVICE_ID = "RZ8T80KSXYD"  # 👈 Your device ID
# SCREENSHOT_FILE = "link_screen.png"

# # These are the partial lines we're OK clicking
# PHRASE_OPTIONS = [
#     "Solicitud de Constancia de",
#     "Semanas Cotizadas del Asegurado"
# ]

# def adb_screencap(save_path=SCREENSHOT_FILE):
#     subprocess.run(f"adb -s {DEVICE_ID} shell screencap -p /sdcard/screen.png", shell=True)
#     subprocess.run(f"adb -s {DEVICE_ID} pull /sdcard/screen.png {save_path}", shell=True)

# def long_press(x, y, duration_ms=5000):
#     print(f"👉 Long pressing at ({x}, {y}) for {duration_ms} ms")
#     subprocess.run(f"adb -s {DEVICE_ID} shell input swipe {x} {y} {x} {y} {duration_ms}", shell=True)

# def extract_blue_regions(image):
#     hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
#     lower_blue = np.array([90, 50, 70])
#     upper_blue = np.array([130, 255, 255])
#     mask = cv2.inRange(hsv, lower_blue, upper_blue)
#     result = cv2.bitwise_and(image, image, mask=mask)
#     return result, mask

# def find_any_phrase(img, phrase_options):
#     data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
#     words = []
    
#     for i, text in enumerate(data['text']):
#         txt = unidecode(text.strip().lower())
#         if txt:
#             x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#             words.append({"text": txt, "x": x, "y": y, "w": w, "h": h})
    
#     # Try to find any one phrase
#     for phrase in phrase_options:
#         target = unidecode(phrase.lower())
#         target_parts = target.split()
#         parts_len = len(target_parts)

#         for i in range(len(words)):
#             combined = words[i]["text"]
#             box = [words[i]["x"], words[i]["y"], words[i]["x"] + words[i]["w"], words[i]["y"] + words[i]["h"]]

#             for j in range(1, parts_len):
#                 if i + j >= len(words):
#                     break
#                 # Ensure same line or nearby
#                 if abs(words[i + j]["y"] - words[i]["y"]) > 30:
#                     break
#                 combined += " " + words[i + j]["text"]
#                 box[2] = words[i + j]["x"] + words[i + j]["w"]
#                 box[3] = max(box[3], words[i + j]["y"] + words[i + j]["h"])

#                 if target in combined:
#                     x_center = (box[0] + box[2]) // 2
#                     y_center = (box[1] + box[3]) // 2
#                     print(f"✅ Found: '{phrase}' at ({x_center}, {y_center})")
#                     return x_center, y_center
#     return None

# # Step 1: Capture screen
# adb_screencap()
# img = cv2.imread(SCREENSHOT_FILE)

# # Step 2: Isolate blue-colored text
# blue_img, _ = extract_blue_regions(img)

# # Step 3: Try finding either of the split phrases
# coords = find_any_phrase(blue_img, PHRASE_OPTIONS)

# if coords:
#     long_press(*coords)
# else:
#     print("❌ No valid link phrase found.")
#     cv2.imwrite("debug_final_phrase_fail.png", blue_img)
#     print("🧪 Debug saved as debug_final_phrase_fail.png")
    
    
    
    
    
####################below function able to copy the link address present in the mail body of the outlook imss email using adb commands##########################

# import cv2
# import pytesseract
# import numpy as np
# import subprocess
# from unidecode import unidecode

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# DEVICE_ID = "RZ8T80KSXYD"
# SCREENSHOT_FILE = "screen.png"
# KEYWORDS = ["address"]  # partial matching

# def adb_screencap(save_path=SCREENSHOT_FILE):
#     subprocess.run(f"adb -s {DEVICE_ID} shell screencap -p /sdcard/screen.png", shell=True)
#     subprocess.run(f"adb -s {DEVICE_ID} pull /sdcard/screen.png {save_path}", shell=True)

# def tap(x, y):
#     print(f"👉 Tapping at ({x}, {y})")
#     subprocess.run(f"adb -s {DEVICE_ID} shell input tap {x} {y}", shell=True)

# def find_possible_buttons(img, keywords):
#     data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
#     matches = []

#     for i, word in enumerate(data["text"]):
#         word_cleaned = unidecode(word.strip().lower())
#         for key in keywords:
#             if key in word_cleaned:
#                 x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
#                 center_x, center_y = x + w // 2, y + h // 2
#                 matches.append((center_x, center_y, word_cleaned, x, y, w, h))
#                 break

#     return matches

# # Step 1: Screenshot
# adb_screencap()
# img = cv2.imread(SCREENSHOT_FILE)

# # Step 2: Find potential button keywords
# matches = find_possible_buttons(img, KEYWORDS)

# if not matches:
#     print("❌ No partial matches found.")
#     cv2.imwrite("debug_copy_link_fail_updated.png", img)
#     print("🧪 Debug image saved as debug_copy_link_fail_updated.png")
# else:
#     # Pick the one closest to the bottom (highest Y value)
#     matches.sort(key=lambda x: x[1], reverse=True)
#     cx, cy, label, x, y, w, h = matches[0]
#     print(f"✅ Clicking on: '{label}' at ({cx}, {cy})")
#     tap(cx, cy)

#     # Optional: draw rectangle for visual debug
#     for _, _, _, x1, y1, w1, h1 in matches:
#         cv2.rectangle(img, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 2)
#     cv2.imwrite("debug_copy_link_success.png", img)
#     print("✅ Debug image saved as debug_copy_link_success.png")


import hashlib

def get_device_specific_port(device_id: str) -> int:
    """Generate device-specific port to avoid conflicts"""
    hash_obj = hashlib.md5(device_id.encode())
    port_offset = int(hash_obj.hexdigest()[:4], 16) % 100
    return 9222 + port_offset

print(get_device_specific_port("RFCY202HNHJ"))



# INFO: ADB device found:
# INFO:           (usb)  RFCY2019RXP                     device  SM_M156B
# INFO:           (usb)  RFCY2019S0N                     device  SM_M156B
# INFO:     -->   (usb)  RFCY202HNHJ                     device  SM_M156B
# INFO:           (usb)  RFCY20PLWDN                     device  SM_M156B