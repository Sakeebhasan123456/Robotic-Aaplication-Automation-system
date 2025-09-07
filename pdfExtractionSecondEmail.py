from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.options.android import UiAutomator2Options
import time
import logging
import random
import string
import calendar
import os
import subprocess
import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
# from pdfViewer import downloadPdfFromChrome
# from appium.webdriver.common.touch_action import TouchAction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction
import re
from imss import pdfExtractionScraper
import numpy as np
import pytesseract
from unidecode import unidecode
import cv2
import subprocess
from PIL import Image
import os
import xml.etree.ElementTree as ET
from getPdf import pull_pdf_from_device
import difflib
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



def run_adb(*args):
    return subprocess.run(["adb"] + list(args), check=True)

#------------------------------- below function click on the Constancia_de_Semanas email in the inbox -------------------------------
def click_on_pdf_mail_present_in_inbox(device_id):
    try:
        print(f"📸 Taking screenshot from device {device_id}...")
        
        base_dir = os.path.join("screenshots", device_id)
        os.makedirs(base_dir, exist_ok=True)
        local_image_path = os.path.join(base_dir, "Constancia_de_Semanas.png")

        if os.path.exists(local_image_path):
            os.remove(local_image_path)
            print("🗑️ Existing screenshot removed.")

        subprocess.run(["adb", "-s", device_id, "shell", "screencap", "-p", "/sdcard/screen.png"], check=True)
        subprocess.run(["adb", "-s", device_id, "pull", "/sdcard/screen.png", local_image_path], check=True)

        print("🖼️ Loading screenshot...")
        img = cv2.imread(local_image_path)

        if img is None:
            return {"success": False, "message": "❌ Failed to load screenshot."}

        print("🔍 Performing OCR...")
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        target_text = "constancia de semanas"  # lowercase for comparison
        found = False

        for i, word in enumerate(data['text']):
            if target_text.startswith(word.lower()):
                # Check next few words to match the full phrase
                phrase = " ".join(data['text'][i:i+4]).lower()
                if target_text in phrase:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    center_x = x + w // 2
                    center_y = y + h // 2

                    print(f"✅ Found '{target_text}' at: ({center_x}, {center_y})")
                    subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(center_x), str(center_y)], check=True)

                    return {"success": True, "message": f"✅ Clicked on '{target_text}' successfully."}

        return {"success": False, "message": f"❌ '{target_text}' text not found on screen."}

    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"❌ ADB command failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"❌ Unexpected error: {e}"}

#-----------------------below function click on the pdf attachment present in the email-----------
def click_on_pdf_attachment(device_id):
    try:
        print(f"📸 Taking screenshot from device {device_id}...")

        base_dir = os.path.join("screenshots", device_id)
        os.makedirs(base_dir, exist_ok=True)
        local_image_path = os.path.join(base_dir, "pdf_attachment.png")

        if os.path.exists(local_image_path):
            os.remove(local_image_path)
            print("🗑️ Existing screenshot removed.")

        # Capture and pull screenshot
        subprocess.run(["adb", "-s", device_id, "shell", "screencap", "-p", "/sdcard/screen.png"], check=True)
        subprocess.run(["adb", "-s", device_id, "pull", "/sdcard/screen.png", local_image_path], check=True)

        print("🖼️ Loading screenshot...")
        img = cv2.imread(local_image_path)
        if img is None:
            return {"success": False, "message": "❌ Failed to load screenshot."}

        print("🔍 Performing OCR...")
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        target_pattern = re.compile(r"pdf", re.IGNORECASE)

        for i, word in enumerate(data['text']):
            if target_pattern.search(word):
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]

                # Tap further to the right to ensure clicking on the attachment area
                center_x = x + w // 2 + 150
                center_y = y + h // 2

                print(f"✅ Found '{word}' at ({center_x}, {center_y}) → tapping PDF attachment")
                subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(center_x), str(center_y)], check=True)

                return {"success": True, "message": f"✅ Clicked on PDF attachment '{word}' successfully."}

        return {"success": False, "message": "❌ No PDF text found in screenshot."}

    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"❌ ADB command failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"❌ Unexpected error: {e}"}
    
#------------------------ below function click on 3 dot persent on screen ---------------------
def get_screen_size(device_id):
    output = subprocess.check_output(["adb", "-s", device_id, "shell", "wm", "size"], text=True)
    match = re.search(r'Physical size: (\d+)x(\d+)', output)
    if match:
        return int(match.group(1)), int(match.group(2))
    else:
        raise ValueError("Could not detect screen size")

def click_three_dots(device_id):
    try:
        time.sleep(2)

        width, height = get_screen_size(device_id)
        # 3 dots are usually at ~98% width, ~4% height
        tap_x = int(width * 0.97)  # slightly less than full right edge
        tap_y = int(height * 0.065)  # around 6.5% from top

        subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(tap_x), str(tap_y)], check=True)
        print(f"✅ Clicked 3-dot menu at ({tap_x}, {tap_y}) on screen {width}x{height}")
        return {"success": True}

    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"ADB failed: {e}"}
    
    
#-------------------------below function click on the Download button present on screen-------------------

# def normalize_text(text):
#     return text.strip().lower().replace("\n", "").replace("\r", "")

# def click_on_download(device_id):
#     try:
#         print(f"📸 Taking screenshot from device {device_id}...")
        
#         base_dir = os.path.join("screenshots", device_id)
#         os.makedirs(base_dir, exist_ok=True)
#         local_image_path = os.path.join(base_dir, "Constancia_de_Semanas.png")

#         if os.path.exists(local_image_path):
#             os.remove(local_image_path)
#             print("🗑️ Existing screenshot removed.")

#         subprocess.run(["adb", "-s", device_id, "shell", "screencap", "-p", "/sdcard/screen.png"], check=True)
#         subprocess.run(["adb", "-s", device_id, "pull", "/sdcard/screen.png", local_image_path], check=True)

#         print("🖼️ Loading screenshot...")
#         img = cv2.imread(local_image_path)

#         if img is None:
#             return {"success": False, "message": "❌ Failed to load screenshot."}

#         print("🔍 Performing OCR...")
#         data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

#         target_text = "download"
#         best_match = None
#         best_match_index = None

#         for i, word in enumerate(data['text']):
#             norm_word = normalize_text(word)
#             if not norm_word:
#                 continue

#             # Fuzzy match to handle OCR mistakes
#             match_ratio = difflib.SequenceMatcher(None, norm_word, target_text).ratio()
#             if target_text in norm_word or match_ratio > 0.8:
#                 best_match = norm_word
#                 best_match_index = i
#                 break

#         if best_match and best_match_index is not None:
#             x = data['left'][best_match_index]
#             y = data['top'][best_match_index]
#             w = data['width'][best_match_index]
#             h = data['height'][best_match_index]
#             center_x = x + w // 2
#             center_y = y + h // 2

#             print(f"✅ Found '{best_match}' (match ratio {match_ratio:.2f}) at: ({center_x}, {center_y})")
#             subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(center_x), str(center_y)], check=True)

#             return {"success": True, "message": f"✅ Clicked on '{best_match}' successfully."}

#         return {"success": False, "message": f"❌ '{target_text}' text not found on screen."}

#     except subprocess.CalledProcessError as e:
#         return {"success": False, "message": f"❌ ADB command failed: {e}"}
#     except Exception as e:
#         return {"success": False, "message": f"❌ Unexpected error: {e}"}
def normalize_text(text):
    return text.strip().lower()

def click_on_download(device_id):
    try:
        print(f"📸 Taking screenshot from device {device_id}...")
        base_dir = os.path.join("screenshots", device_id)
        os.makedirs(base_dir, exist_ok=True)
        local_image_path = os.path.join(base_dir, "screenshot.png")

        if os.path.exists(local_image_path):
            os.remove(local_image_path)
            print("🗑️ Existing screenshot removed.")

        # Capture screenshot
        subprocess.run(["adb", "-s", device_id, "shell", "screencap", "-p", "/sdcard/screen.png"], check=True)
        subprocess.run(["adb", "-s", device_id, "pull", "/sdcard/screen.png", local_image_path], check=True)

        print("🖼️ Loading screenshot...")
        img = cv2.imread(local_image_path)
        if img is None:
            return {"success": False, "message": "❌ Failed to load screenshot."}

        # Get image dimensions
        h, w, _ = img.shape

        # Crop top-right popup menu region
        crop_x1 = int(w * 0.55)  # start a bit left of center
        crop_y1 = int(h * 0.05)  # just below status bar
        crop_x2 = int(w * 0.98)  # almost to right edge
        crop_y2 = int(h * 0.35)  # cover menu height
        menu_crop = img[crop_y1:crop_y2, crop_x1:crop_x2]

        # Preprocess for OCR
        gray = cv2.cvtColor(menu_crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1]

        print("🔍 Performing OCR on menu area...")
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

        target_text = "download"
        best_match = None
        best_match_index = None
        best_match_ratio = 0

        for i, word in enumerate(data['text']):
            norm_word = normalize_text(word)
            if not norm_word:
                continue
            match_ratio = difflib.SequenceMatcher(None, norm_word, target_text).ratio()
            if match_ratio > best_match_ratio:
                best_match_ratio = match_ratio
                best_match = norm_word
                best_match_index = i

        print("📝 Detected words:", [normalize_text(w) for w in data['text'] if w.strip()])

        if best_match and best_match_ratio > 0.6:
            # Adjust coordinates relative to full screen
            x = crop_x1 + data['left'][best_match_index]
            y = crop_y1 + data['top'][best_match_index]
            w_box = data['width'][best_match_index]
            h_box = data['height'][best_match_index]
            center_x = x + w_box // 2
            center_y = y + h_box // 2

            print(f"✅ Found '{best_match}' (ratio {best_match_ratio:.2f}) at: ({center_x}, {center_y})")
            subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(center_x), str(center_y)], check=True)
            return {"success": True, "message": f"✅ Clicked on '{best_match}' successfully."}

        return {"success": False, "message": f"❌ '{target_text}' not found in menu area."}

    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"❌ ADB command failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"❌ Unexpected error: {e}"}
    
#-------------- click on device button-------
def click_device_button(device_id):
    try:
        print(f"📸 Taking screenshot from device {device_id}...")
        base_dir = os.path.join("screenshots", device_id)
        os.makedirs(base_dir, exist_ok=True)
        local_image_path = os.path.join(base_dir, "screenshot.png")

        if os.path.exists(local_image_path):
            os.remove(local_image_path)

        # Capture screenshot
        subprocess.run(["adb", "-s", device_id, "shell", "screencap", "-p", "/sdcard/screen.png"], check=True)
        subprocess.run(["adb", "-s", device_id, "pull", "/sdcard/screen.png", local_image_path], check=True)

        img = cv2.imread(local_image_path)
        if img is None:
            return {"success": False, "message": "❌ Failed to load screenshot."}

        h, w, _ = img.shape

        # Tap position: horizontally centered, vertically ~85% down (above nav bar)
        tap_x = int(w * 0.5)
        tap_y = int(h * 0.91)

        print(f"📌 Clicking at fixed coordinates: ({tap_x}, {tap_y})")
        subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(tap_x), str(tap_y)], check=True)

        return {"success": True, "message": f"✅ Clicked on 'Device' at fixed position ({tap_x}, {tap_y})."}

    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"❌ ADB command failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"❌ Unexpected error: {e}"}
    
    #------------------------------------
    
# ✅ Retry loop in open_latest_outlook_mail
def open_latest_outlook_mail(driver, device_name, curp):
    try:
        logger.info("📨 Opening Outlook app")
        subprocess.run(
            ["adb", "-s", device_name, "shell", "am", "start", "-n",
             "com.microsoft.office.outlook/com.microsoft.office.outlook.MainActivity"],
            check=True
        )
        time.sleep(10)  # Allow app to load fully

        # Tap top center to refresh inbox
        subprocess.run(["adb", "-s", device_name, "shell", "input", "tap", "540", "150"], check=True)
        time.sleep(3)

        logger.info("🔄 Searching for 'Constancia de Semanas Cotizadas' in inbox using OCR...")
        start_time = time.time()
        timeout = 90  # 90 seconds
        interval = 7

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                return {"status": False, "data": "Timeout: Mail not found"}

            result = click_on_pdf_mail_present_in_inbox(device_name)
            if result.get("success"):
                logger.info(result.get("message", "✅ Mail clicked successfully."))
                break
            else:
                logger.info("📩 Mail not found, refreshing inbox...")
                subprocess.run(
                    ["adb", "-s", device_name, "shell", "input", "swipe", "500", "500", "500", "1500"],
                    check=True
                )
                time.sleep(interval)

        logger.info("➡️ Proceeding to click on PDF present in email...")
        time.sleep(4)  # Let email content load
        
        # Step 2: Click on PDF
        pdf_result = click_on_pdf_attachment(device_name)
        if not pdf_result.get("success"):
            logger.error(pdf_result.get("message"))
            return {"status": False, "data": pdf_result.get("message")}
        logger.info(pdf_result.get("message"))
        
        # ✅ NEW: Handle "Open with" page with Device button
        logger.info("🔍 Checking if 'Device' button is present...")
        try:
            device_button_found = click_device_button(device_name)
            if device_button_found:
                logger.info("📌 'Device' button found and clicked.")
                time.sleep(5)  # Wait for PDF to save

                # Verify PDF is downloaded
                pull_result = pull_pdf_from_device(device_name, curp)
                if pull_result.get("status"):
                    logger.info(pull_result.get("data"))
                    return {"status": True, "data": "Successfully saved pdf in the pdf folder"}
                else:
                    logger.error(pull_result.get("data"))
                    # ⬇️ Don't return — let normal process handle it
            else:
                logger.info("ℹ️ 'Device' button not found → continuing normal process.")
        except Exception as e:
            logger.error(f"❌ Error checking/clicking 'Device' button: {e}", exc_info=True)
            logger.info("Continuing with normal process...")

        # Step 3: Click on 3-dot menu
        logger.info("📌 Clicking 3-dot menu...")
        three_dot_result = click_three_dots(device_name)
        if not three_dot_result.get("success"):
            logger.error(three_dot_result.get("message", "❌ Failed to click 3-dot menu"))
            return {"status": False, "data": three_dot_result.get("message")}
        logger.info("✅ 3-dot menu clicked successfully.")

        # Step 4: Click on Download
        logger.info("⬇️ Clicking Download button...")
        download_result = click_on_download(device_name)
        if not download_result.get("success"):
            logger.error(download_result.get("message"))
            return {"status": False, "data": download_result.get("message")}
        logger.info(download_result.get("message"))
        time.sleep(15)

        # Step 5: Pull PDF from device
        logger.info("💾 Pulling PDF from device...")
        pull_result = pull_pdf_from_device(device_name, curp)
        if not pull_result.get("status"):
            logger.error(pull_result.get("data"))
            return {"status": False, "data": pull_result.get("data")}
        logger.info(pull_result.get("data"))

        # ✅ Success
        return {"status": True, "data": "Successfully saved pdf in the pdf folder"}

        # # Step 3: Click on 3-dot menu
        # logger.info("📌 Clicking 3-dot menu...")
        # three_dot_result = click_three_dots(device_name)
        # if not three_dot_result.get("success"):
        #     logger.error(three_dot_result.get("message", "❌ Failed to click 3-dot menu"))
        #     return {"status": False, "data": three_dot_result.get("message")}
        # logger.info("✅ 3-dot menu clicked successfully.")

        # # Step 4: Click on Download
        # logger.info("⬇️ Clicking Download button...")
        # download_result = click_on_download(device_name)
        # if not download_result.get("success"):
        #     logger.error(download_result.get("message"))
        #     return {"status": False, "data": download_result.get("message")}
        # logger.info(download_result.get("message"))
        # time.sleep(15)
        # # Step 5: Pull PDF from device
        # logger.info("💾 Pulling PDF from device...")
        # pull_result = pull_pdf_from_device(device_name, curp)
        # if not pull_result.get("status"):
        #     logger.error(pull_result.get("data"))
        #     return {"status": False, "data": pull_result.get("data")}
        # logger.info(pull_result.get("data"))

        # # ✅ Success
        # return {"status": True, "data": "Successfully saved pdf in the pdf folder"}


    except Exception as e:
        logger.error(f"❌ Exception in open_latest_outlook_mail: {e}", exc_info=True)
        return {"status": False, "data": f"Exception: {e}"}
   

def pdf_extraction_from_second_email(device_name,curp):
    # curp = "MOMD001230HJCRRHA4"
    # device_name = "RZ8T80KSXYD"
    # App package and activity
    app_package = "com.microsoft.office.outlook"
    app_activity = "com.microsoft.office.outlook.MainActivity"

    # 🛑 Step 1: Close the app if it's already running
    try:
        subprocess.run(["adb", "-s", device_name, "shell", "am", "force-stop", app_package], check=True)
        logger.info("🛑 Outlook app force-stopped successfully before starting Appium session")
    except subprocess.CalledProcessError as e:
        logger.warning(f"⚠️ Failed to force-stop app: {e}")

    # Set desired capabilities / options
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.platform_version = "14.0"
    options.udid = device_name
    options.device_name = device_name
    # options.app_package = "com.microsoft.office.outlook"
    # options.app_activity = "com.microsoft.office.outlook.MainActivity"
    options.automation_name = "UiAutomator2"
    options.auto_grant_permissions = True
    options.no_reset = True

    driver = None

    try:
        driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        logger.info("📱 Appium session started")

        # ✅ Call your function
        result = open_latest_outlook_mail(driver, device_name, curp)

        try:
            logger.info(f"🔌 Attempting to quit driver for {device_name}")
            driver.quit()
            logger.info(f"✅ Driver closed successfully for {device_name}")
        except Exception as quit_error:
            logger.warning(f"⚠️ Driver quit failed for {device_name}: {type(quit_error).__name__}: {quit_error}")
        return result

    except Exception as e:
        logger.error("❌ Error running open_latest_outlook_mail independently", exc_info=True)

# # ✅ Actually run it
# if __name__ == "__main__":
#     pdf_extraction_from_second_email("RFCY20EKZMM","MASA040111MNLRLNA2")  


