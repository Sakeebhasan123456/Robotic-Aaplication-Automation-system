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
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



MAX_RETRIES = 10



def run_adb(*args):
    return subprocess.run(["adb"] + list(args), check=True)


######################### below function will click on the required email present in inbox    
def click_on_imss_mail_present_in_inbox(device_id):
    try:
        print(f"📸 Taking screenshot from device {device_id}...")
        
        # Define directory and file path
        base_dir = os.path.join("utils", device_id)
        os.makedirs(base_dir, exist_ok=True)  # Create the directory if it doesn't exist

        local_image_path = os.path.join(base_dir, "screen.png")

        # Remove the existing screen.png if it exists
        if os.path.exists(local_image_path):
            os.remove(local_image_path)
            print("🗑️ Existing screen.png removed.")
            
        subprocess.run(["adb", "-s", device_id, "shell", "screencap", "-p", "/sdcard/screen.png"], check=True)
        subprocess.run(["adb", "-s", device_id, "pull", "/sdcard/screen.png", local_image_path], check=True)

        print("🖼️ Loading screenshot...")
        img = cv2.imread(local_image_path)

        if img is None:
            return {"success": False, "message": "❌ Failed to load screenshot image."}

        print("🔍 Performing OCR...")
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        target_text = "historia.laboral"
        found = False

        for i, word in enumerate(data['text']):
            if target_text in word.lower():
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]

                center_x = x + w // 2
                center_y = y + h // 2
                print(f"✅ Found '{target_text}' at: ({center_x}, {center_y})")

                print("👉 Tapping on the location...")
                subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(center_x), str(center_y)], check=True)

                return {"success": True, "message": f"✅ Clicked on '{target_text}' successfully."}

        return {"success": False, "message": "❌ 'historia.laboral' text not found on screen."}

    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"❌ ADB command failed: {e}"}
    except Exception as e:
        return {"success": False, "message": f"❌ Unexpected error: {e}"}
    

########################## below function will long press on the pdflink present in the email    
PHRASE_OPTIONS = [
    "Solicitud de Constancia de",
    "Semanas Cotizadas del Asegurado"
]

def adb_screencap(device_name, save_path):
    subprocess.run(f"adb -s {device_name} shell screencap -p /sdcard/screen.png", shell=True)
    subprocess.run(f"adb -s {device_name} pull /sdcard/screen.png {save_path}", shell=True)

def long_press(device_name, x, y, duration_ms=5000):
    print(f"👉 Long pressing at ({x}, {y}) for {duration_ms} ms")
    subprocess.run(f"adb -s {device_name} shell input swipe {x} {y} {x} {y} {duration_ms}", shell=True)

def extract_blue_regions(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([90, 50, 70])
    upper_blue = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(image, image, mask=mask)
    return result, mask

def find_any_phrase(img, phrase_options):
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    words = []

    for i, text in enumerate(data['text']):
        txt = unidecode(text.strip().lower())
        if txt:
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            words.append({"text": txt, "x": x, "y": y, "w": w, "h": h})

    for phrase in phrase_options:
        target = unidecode(phrase.lower())
        target_parts = target.split()
        parts_len = len(target_parts)

        for i in range(len(words)):
            combined = words[i]["text"]
            box = [words[i]["x"], words[i]["y"], words[i]["x"] + words[i]["w"], words[i]["y"] + words[i]["h"]]

            for j in range(1, parts_len):
                if i + j >= len(words):
                    break
                if abs(words[i + j]["y"] - words[i]["y"]) > 30:
                    break
                combined += " " + words[i + j]["text"]
                box[2] = words[i + j]["x"] + words[i + j]["w"]
                box[3] = max(box[3], words[i + j]["y"] + words[i + j]["h"])

                if target in combined:
                    x_center = (box[0] + box[2]) // 2
                    y_center = (box[1] + box[3]) // 2
                    print(f"✅ Found: '{phrase}' at ({x_center}, {y_center})")
                    return x_center, y_center
    return None

def long_click_on_the_pdflink_on_email(device_name):
    try:
        # Create directory: utils/{device_name}
        base_dir = os.path.join("utils", device_name)
        os.makedirs(base_dir, exist_ok=True)

        screenshot_path = os.path.join(base_dir, "link_screen.png")
        debug_path = os.path.join(base_dir, "debug_final_phrase_fail.png")

        print("📸 Taking screenshot...")
        adb_screencap(device_name, screenshot_path)

        if not os.path.exists(screenshot_path):
            return {"status": False, "data": "Screenshot failed."}

        img = cv2.imread(screenshot_path)
        blue_img, _ = extract_blue_regions(img)

        print("🔍 Searching for PDF link text...")
        coords = find_any_phrase(blue_img, PHRASE_OPTIONS)

        if coords:
            long_press(device_name, *coords)
            return {"status": True, "data": "Mail clicked, proceeding to next step"}
        else:
            cv2.imwrite(debug_path, blue_img)
            print(f"❌ No valid link phrase found. Saved debug image to {debug_path}")
            return {"status": False, "data": "No valid PDF link phrase found in email"}

    except Exception as e:
        return {"status": False, "data": f"Exception occurred: {str(e)}"}
    
######################below function used to copy link address 

KEYWORDS = ["address"]  # partial matching


def adb_screencap(device_name, save_path):
    subprocess.run(f"adb -s {device_name} shell screencap -p /sdcard/screen.png", shell=True)
    subprocess.run(f"adb -s {device_name} pull /sdcard/screen.png {save_path}", shell=True)

def tap(device_name, x, y):
    print(f"👉 Tapping at ({x}, {y})")
    subprocess.run(f"adb -s {device_name} shell input tap {x} {y}", shell=True)

def find_possible_buttons(img, keywords):
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    matches = []

    for i, word in enumerate(data["text"]):
        word_cleaned = unidecode(word.strip().lower())
        for key in keywords:
            if key in word_cleaned:
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                center_x, center_y = x + w // 2, y + h // 2
                matches.append((center_x, center_y, word_cleaned, x, y, w, h))
                break

    return matches

def copy_link_address(device_name):
    try:
        base_dir = os.path.join("utils", device_name)
        os.makedirs(base_dir, exist_ok=True)

        screenshot_path = os.path.join(base_dir, "screen.png")
        success_debug_path = os.path.join(base_dir, "debug_copy_link_success.png")
        fail_debug_path = os.path.join(base_dir, "debug_copy_link_fail_updated.png")

        # Step 1: Screenshot
        print("📸 Capturing screen...")
        adb_screencap(device_name, screenshot_path)

        if not os.path.exists(screenshot_path):
            return {"status": False, "data": "Screenshot capture failed."}

        img = cv2.imread(screenshot_path)

        # Step 2: OCR for keywords
        print("🔍 Searching for 'address' in screenshot...")
        matches = find_possible_buttons(img, KEYWORDS)

        if not matches:
            cv2.imwrite(fail_debug_path, img)
            print(f"❌ No matches found. Debug saved to {fail_debug_path}")
            return {"status": False, "data": "No copy address button found"}

        # Step 3: Choose best (lowest on screen)
        matches.sort(key=lambda x: x[1], reverse=True)
        cx, cy, label, x, y, w, h = matches[0]
        print(f"✅ Clicking on: '{label}' at ({cx}, {cy})")
        tap(device_name, cx, cy)

        # Optional: draw all boxes for debug
        for _, _, _, x1, y1, w1, h1 in matches:
            cv2.rectangle(img, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 2)
        cv2.imwrite(success_debug_path, img)
        print(f"✅ Debug image saved to {success_debug_path}")

        return {"status": True, "data": f"Clicked on '{label}'"}

    except Exception as e:
        return {"status": False, "data": f"Exception occurred: {str(e)}"}

#######################  ads popup page handler ################

def handle_ads_layout_popup(device_name):
    try:
        logger.info("🔍 Checking for ads layout popup...")

        # 1. Define local XML path
        local_dir = os.path.join("utils", device_name, "ads_layout")
        os.makedirs(local_dir, exist_ok=True)
        local_xml_path = os.path.join(local_dir, "window_dump.xml")

        # 2. Dump UI XML from device
        run_adb("-s", device_name, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml")
        run_adb("-s", device_name, "pull", "/sdcard/window_dump.xml", local_xml_path)

        # 3. Parse XML
        tree = ET.parse(local_xml_path)
        root = tree.getroot()

        for node in root.iter("node"):
            if node.attrib.get("resource-id") == "com.microsoft.office.outlook:id/eu_ruling_prompt_default" \
               and "MAILBOX" in node.attrib.get("text", "").upper():

                bounds = node.attrib["bounds"]
                logger.info(f"📌 Ad layout popup detected. Clicking MAILBOX button at {bounds}")

                # Extract coordinates
                x1, y1, x2, y2 = [int(x) for x in bounds.replace("[", "").replace("]", ",").split(",") if x]
                x = (x1 + x2) // 2
                y = (y1 + y2) // 2

                # 4. Click the MAILBOX button
                run_adb("-s", device_name, "shell", "input", "tap", str(x), str(y))
                logger.info("clicked on the add layout popup and handled properly")
                time.sleep(2)

                # 5. Tap center-top to refresh
                logger.info("🔄 Tapping top center after dismissing popup...")
                run_adb("-s", device_name, "shell", "input", "tap", "540", "150")
                time.sleep(2)

                return True

        logger.info("✅ No ads layout popup detected.")
        return False

    except Exception as e:
        logger.warning(f"⚠️ Failed to handle ads layout popup: {e}")
        return False
 

def open_latest_outlook_mail(driver, device_name, curp):
    try:
        logger.info("📨 Opening Outlook app")
        run_adb("-s", device_name, "shell", "am", "start", "-n", "com.microsoft.office.outlook/com.microsoft.office.outlook.MainActivity")
        time.sleep(10)
        handle_ads_layout_popup(device_name)
        # Tap on center top to refresh inbox
        run_adb("-s", device_name, "shell", "input", "tap", "540", "150")
        logger.info("🧹 Clicked on center top successfully")
        time.sleep(3)

        logger.info("🔄 Searching for 'historia.laboral' in inbox using OCR...")

        start_time = time.time()
        timeout = 90 #300  # 5 minutes
        interval = 7   # seconds between retries

        result = None
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.warning("⏳ Timeout: 'historia.laboral' not found after 5 minutes.")
                return {"status": False, "data": "Timeout: Mail not found"}

            result = click_on_imss_mail_present_in_inbox(device_name)

            if result.get("success"):  # Keep compatibility with existing result format
                logger.info(result.get("message", "✅ Mail clicked successfully."))
                break
            else:
                logger.info("📩 Mail not found, refreshing inbox and retrying...")
                handle_ads_layout_popup(device_name)
                run_adb("-s", device_name, "shell", "input", "swipe", "500", "500", "500", "1500")
                time.sleep(interval)

        logger.info("➡️ Proceeding to PDF link long click detection step...")
        time.sleep(4)
        handle_ads_layout_popup(device_name)
        # ✅ Retry long click on PDF link up to 3 times if needed
        for attempt in range(1, 4):
            logger.info(f"🔁 Attempt {attempt}: Trying to long click on PDF link...")
            link_result = long_click_on_the_pdflink_on_email(device_name)

            if link_result.get("status"):
                logger.info(f"✅ {link_result['data']}")
                break
                # return {"status": True, "data": "Successfully long-clicked on PDF link."}
            else:
                logger.warning(f"❌ {link_result['data']}")
                time.sleep(2)
                run_adb("-s", device_name, "shell", "input", "swipe", "500", "500", "500", "1500")
        else:
            # After 3 failed attempts
            logger.error("❌ Failed to long-click on PDF link after 3 attempts.")
            return {"status": False, "data": "Failed to long-click on PDF link after 3 retries."}
    
        # ✅ Proceed to copy the link address after successful long press
        logger.info("📋 Proceeding to copy link address...")

        for attempt in range(1, 3):
            logger.info(f"🔁 Attempt {attempt}: Trying to copy the link address...")
            copy_result = copy_link_address(device_name)

            if copy_result.get("status"):
                logger.info(f"✅ {copy_result['data']}")
                break
            else:
                logger.warning(f"❌ {copy_result['data']}")
                time.sleep(2)
        else:
            logger.error("❌ Failed to copy link address after 3 attempts.")
            return {"status": False, "data": "Failed to copy link address after 3 retries."}
        
        logger.info("📥 Extracting copied link from clipboard...")
        try:
            raw_clipboard_link = driver.get_clipboard_text()
            logger.info(f"📋 Raw clipboard content: {raw_clipboard_link}")
        except Exception as e:
            logger.error("❌ Failed to read clipboard text", exc_info=True)
            return {"status": False, "data": "Copied, but failed to read clipboard"}
        
        if raw_clipboard_link:
                cleaned_link = (
                    raw_clipboard_link.replace("detalle=true", "detalle=detalle")
                                      .replace("detalle=false", "detalle=detalle")
                                      .replace("&origen=MOVILES", "")
                                      .replace("origen=MOVILES&", "")
                )
                if "detalle=detalle" not in cleaned_link:
                    cleaned_link += "&detalle=detalle" if "?" in cleaned_link else "?detalle=detalle"
                    
                # ✅ Skip PDF extraction, just return the cleaned link
                return {
                        "status": True,
                        "pdf_link": cleaned_link,
                        "data": "PDF extracted successfully"
                    }

                # result = pdfExtractionScraper(curp, cleaned_link)
                # if result.get("status"):
                #     logger.info("PDF successfully downloaded and processed.", extra={"curp": curp})
                #     return {"data": result["data"], "status": True}
                # else:
                #     logger.error(f"PDF download failed: {result}", extra={"curp": curp})
                #     return {"data": result.get("data", "error"), "status": False}
        else:
            return {"data": "Link was empty or not extracted properly.", "status": False}
    
    

        # Optional: return a success status if needed at the end
        # return {"status": True, "data": "Mail clicked, proceeding to next step"}

    except Exception as e:
        logger.error(f"❌ Exception in open_latest_outlook_mail: {e}", exc_info=True)
        return {"status": False, "data": f"Exception: {e}"}
   

def pdf_extraction_using_outlook_app(device_name,curp):
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

    try:
        driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        logger.info("📱 Appium session started")

        # ✅ Call your function
        result = open_latest_outlook_mail(driver, device_name, curp)

        # You can quit the driver if needed
        driver.quit()
        return result

    except Exception as e:
        logger.error("❌ Error running open_latest_outlook_mail independently", exc_info=True)

# # ✅ Actually run it
# if __name__ == "__main__":
#     pdf_extraction_using_outlook_app("RFCY20LK9FY","BAGJ040124HMCNRSA6")  


