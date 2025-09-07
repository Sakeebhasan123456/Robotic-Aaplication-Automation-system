from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import NoSuchElementException

from utils.names import first_names,last_names

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
from logger import logger
# from appium.webdriver.common.touch_action import TouchAction
import cv2
import pytesseract
import numpy as np
import subprocess
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

PHRASE_OPTIONS = ["PRESS & HOLD", "PRESS AND HOLD","Press and hold","Press & hold","press & hold","press and hold"]  # Exact case-sensitive match





def generate_outlook_email():
    first = random.choice(first_names)
    last = random.choice(last_names)
    digits = random.randint(10000000, 99999999)
    email_name = f"{first.lower()}_{last.lower()}_{digits}"
    return first, last, email_name

def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%"
    password = ''.join(random.choices(chars, k=15))
    return password

######################################################
# OCR / press-and-hold helpers (unchanged)
def press_and_hold_button(device_id, duration_ms=10000):
    # 📁 Define and create screenshot folder path
    base_dir = os.path.join("screenshots", device_id)
    os.makedirs(base_dir, exist_ok=True)

    screenshot_file = os.path.join(base_dir, "press_and_hold_screen.png")
    debug_file = os.path.join(base_dir, "debug_press_and_hold_fail.png")

    def adb_screencap():
        subprocess.run(f"adb -s {device_id} shell screencap -p /sdcard/screen.png", shell=True)
        subprocess.run(f"adb -s {device_id} pull /sdcard/screen.png {screenshot_file}", shell=True)

    def long_press(x, y):
        print(f"👉 Long pressing at ({x}, {y}) for {duration_ms} ms")
        subprocess.run(f"adb -s {device_id} shell input swipe {x} {y} {x} {y} {duration_ms}", shell=True)

    def extract_blue_regions(image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([90, 50, 70])
        upper_blue = np.array([130, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        result = cv2.bitwise_and(image, image, mask=mask)
        return result

    def find_exact_phrase(img, exact_phrases):
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        words = []

        for i, text in enumerate(data['text']):
            if text.strip():
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                words.append({"text": text.strip(), "x": x, "y": y, "w": w, "h": h})

        for phrase in exact_phrases:
            target_parts = phrase.split()
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

                    if combined == phrase:
                        x_center = (box[0] + box[2]) // 2
                        y_center = (box[1] + box[3]) // 2
                        print(f"✅ Found exact match: '{phrase}' at ({x_center}, {y_center})")
                        return x_center, y_center
        return None

    # 🧪 Main execution
    print(f"📱 Processing device: {device_id}")
    adb_screencap()

    if not os.path.exists(screenshot_file):
        print("❌ Screenshot failed or file not found.")
        return

    img = cv2.imread(screenshot_file)
    blue_img = extract_blue_regions(img)
    coords = find_exact_phrase(blue_img, PHRASE_OPTIONS)

    if coords:
        long_press(*coords)
    else:
        print("❌ Exact phrase 'PRESS & HOLD' not found.")
        cv2.imwrite(debug_file, blue_img)
        print(f"🧪 Debug image saved at {debug_file}")
        
############################################################

def select_month_via_ocr(device_name):
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    
    # Step 1: Randomly pick a month
    target_month = random.choice(months)
    print(f"🎯 Target month: {target_month}")

    # Step 2: Take screenshot from device
    subprocess.run(["adb", "-s", device_name, "shell", "screencap", "-p", "/sdcard/screen.png"])
    # Create folder for storing
    save_dir = os.path.join("screenshots", device_name)
    os.makedirs(save_dir, exist_ok=True)
    
    # Save as month.png
    save_path = os.path.join(save_dir, "month.png")
    
    # Pull the screenshot
    subprocess.run(["adb", "-s", device_name, "pull", "/sdcard/screen.png", save_path])

    # Load screenshot
    img = cv2.imread(save_path)

    # Step 4: Perform OCR
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    found = False

    # Step 5: Search for the selected month and tap it
    for i, word in enumerate(data['text']):
        if target_month.lower() in word.lower():
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]

            center_x = x + w // 2
            center_y = y + h // 2

            print(f"✅ Found '{target_month}' at: ({center_x}, {center_y})")

            # Tap on screen
            subprocess.run(["adb", "-s", device_name, "shell", "input", "tap", str(center_x), str(center_y)])
            found = True
            break

    if not found:
        print(f"❌ Month '{target_month}' not found via OCR.")
        
        
########################################################

def select_day_via_ocr(device_name):
    # Step 1: Pick a random day between 1 and 20
    target_day = str(random.randint(10, 20))
    
    print(f"🎯 Target day: {target_day}")

    # Optional: tap on "Day" dropdown if needed (fill x,y based on actual location)
    # subprocess.run(["adb", "-s", device_name, "shell", "input", "tap", "x", "y"])
    # time.sleep(1)

    # Step 2: Capture screenshot
    subprocess.run(["adb", "-s", device_name, "shell", "screencap", "-p", "/sdcard/screen.png"])
    # subprocess.run(["adb", "-s", device_name, "pull", "/sdcard/screen.png", "./screen.png"])

    # # Step 3: Load screenshot
    # img = cv2.imread("screen.png")

    # Create folder for storing
    save_dir = os.path.join("screenshots", device_name)
    os.makedirs(save_dir, exist_ok=True)
    
    # Save as day.png (e.g., "15.png")
    save_path = os.path.join(save_dir, "day.png")
    
    # Pull the screenshot to custom path
    subprocess.run(["adb", "-s", device_name, "pull", "/sdcard/screen.png", save_path])

    # Step 3: Load screenshot
    img = cv2.imread(save_path)

    # Step 4: OCR to get text and coordinates
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    found = False

    # Step 5: Search for target day and tap
    for i, word in enumerate(data['text']):
        if word.strip() == target_day:
            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]
            h = data['height'][i]

            center_x = x + w // 2
            center_y = y + h // 2

            print(f"✅ Found day '{target_day}' at: ({center_x}, {center_y})")

            # Tap at the center of the day
            subprocess.run(["adb", "-s", device_name, "shell", "input", "tap", str(center_x), str(center_y)])
            found = True
            break

    if not found:
        print(f"❌ Day '{target_day}' not found via OCR.")

###########################################################################

# ------------------ ADD DETECTION HELPER ------------------
def detect_email_page(driver, device_name=None, logger=None, curp=None, ocr_enabled=True):
    """
    Detect whether current screen is the 'email' page.
    Checks (in order):
      1) page_source text
      2) visible element attributes (text/hint/contentDescription/resourceId)
      3) UiSelector textContains checks
      4) optional OCR on screenshot (if device_name and ocr_enabled True)
    Returns: (True, matched_phrase) or (False, None)
    Logs "Yes — this is the email page" when True (uses logger if provided).
    """
    phrases = [
        "create your microsoft account",
        "enter your new email address.",
        "enter your new email",
        "new email",
        "email"
    ]
    def _log(msg, level="info"):
        if logger:
            getattr(logger, level)(msg, extra={"curp": curp} if curp else {})
        else:
            print(msg)

    try:
        # Phase 1: page_source
        try:
            page_src = (driver.page_source or "").lower()
            for p in phrases:
                if p in page_src:
                    _log(f"Yes — this is the email page (matched page_source: '{p}')")
                    return True, p
        except Exception:
            pass

        # Phase 2: element attributes
        classes = ["android.view.View", "android.widget.TextView", "android.widget.EditText", "android.widget.Button"]
        elements = []
        for cls in classes:
            try:
                elements += driver.find_elements(AppiumBy.CLASS_NAME, cls)
            except Exception:
                pass
        for el in elements:
            try:
                txt = (el.get_attribute("text") or "") or ""
                hint = (el.get_attribute("hint") or "") or ""
                desc = (el.get_attribute("contentDescription") or "") or ""
                rid = (el.get_attribute("resourceId") or "") or ""
                combined = " ".join([txt, hint, desc, rid]).lower()
                for p in phrases:
                    if p in combined:
                        _log(f"Yes — this is the email page (matched element attribute: '{p}')")
                        return True, p
            except Exception:
                continue

        # Phase 3: UiSelector.textContains fallback (try common casings)
        ui_checks = ["Create your Microsoft account", "Enter your new email address.", "New email", "Email"]
        for p in ui_checks:
            try:
                found = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().textContains("{p}")')
                if found:
                    _log(f"Yes — this is the email page (matched UiSelector: '{p}')")
                    return True, p
            except Exception:
                pass

        # Phase 4: OCR fallback (optional)
        if device_name and ocr_enabled:
            try:
                tmp_dir = os.path.join("screenshots", device_name)
                os.makedirs(tmp_dir, exist_ok=True)
                tmp_path = os.path.join(tmp_dir, "email_detect.png")
                # take screenshot and pull
                adb = "adb"
                subprocess.run([adb, "-s", device_name, "shell", "screencap", "-p", "/sdcard/screen.png"], check=False)
                subprocess.run([adb, "-s", device_name, "pull", "/sdcard/screen.png", tmp_path], check=False)
                img = cv2.imread(tmp_path)
                if img is not None:
                    text = (pytesseract.image_to_string(img) or "").lower()
                    for p in phrases:
                        if p in text:
                            _log(f"Yes — this is the email page (matched OCR: '{p}')")
                            return True, p
            except Exception:
                pass

        # no match
        _log("No — email phrases not detected on this page.", level="warning")
        return False, None

    except Exception as e:
        _log(f"detect_email_page() exception: {e}", level="error")
        return False, None

###########################################################################

def automate_outlook_create_account(curp,device_name):
    def log_info(msg):
        logger.info(msg, extra={"curp": curp})
    def log_error(msg):
        logger.error(msg, extra={"curp": curp})
    # Optional: For warnings/debug too
    def log_warning(msg):
        logger.warning(msg, extra={"curp": curp})
    def log_debug(msg):
        logger.debug(msg, extra={"curp": curp})
        
    # curp = "ZAAH950926HSPVLC08"
    # device_name = "RFCY20EKZMM"
    #outlookEmail = email_name + "@outlook.com"
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.platform_version = "14.0"
    options.udid = device_name
    options.device_name = device_name
    options.app_package = "com.microsoft.office.outlook"
    options.app_activity = "com.microsoft.office.outlook.MainActivity"
    options.automation_name = "UiAutomator2"
    options.auto_grant_permissions = True
    
    email = None
    password = None
    driver = None

    try:
        # subprocess.run(["adb", "-s", device_name,"shell", "settings", "put", "global", "http_proxy", "p.webshare.io:9999"])
        driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        log_info("📱 Outlook app launched")

        # Step 1: Click "CREATE NEW ACCOUNT"
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("CREATE NEW ACCOUNT")'))
        ).click()
        log_info("✅ Clicked on 'CREATE NEW ACCOUNT'")

        # --------------------------
        # NEW: detect email page with retries (2s wait between retries)
        # --------------------------
        max_attempts = 3
        is_email = False
        matched_phrase = None

        for attempt in range(1, max_attempts + 1):
            is_email, matched_phrase = detect_email_page(driver, device_name=device_name, logger=logger, curp=curp, ocr_enabled=True)
            if is_email:
                log_info(f"Yes — this is the email page (matched: {matched_phrase})")
                break
            else:
                if attempt < max_attempts:
                    log_info(f"Email page not detected (attempt {attempt}/{max_attempts}). Waiting 2s before retry...")
                    time.sleep(0.5)
                else:
                    log_warning(f"Email page not detected after {max_attempts} attempts. Aborting to avoid wrong input.")
                    return {"data": "Email page not detected", "status": False}

        # Step 2: Enter name (EditText field)  -- unchanged behavior (fills username)
        input_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
        )

        first, last, email_name = generate_outlook_email()
        log_info(f"✍️ Generated name: {email_name}")
        email = email_name + "@outlook.com"
        input_field.send_keys(email_name)
        log_info("✅ Entered name in input field")

        # Step 3: Click Next
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Next")'))
        ).click()
        log_info("➡️ Clicked on 'Next' button")
        time.sleep(7)

        # Step 4: Wait for Password field (next screen)
        log_info("⏳ Waiting for password field")
        password_input = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
        )

        password = generate_password()
        log_info(f"🔐 Generated password: {password}")
        password_input.send_keys(password)
        log_info("✅ Entered password")

        # Step 5: Click "Next" again
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Next")'))
        ).click()
        log_info("➡️ Clicked on 'Next' after entering password")

        time.sleep(5)
        
        # Step 6: Wait for DOB spinners to appear
        log_info("⏳ Waiting for DOB fields (Month, Day, Year)")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Month")'))
        )
        

        # Select Month
        month_spinner = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("BirthMonthDropdown")')
        month_spinner.click()
        log_info("📅 Clicked Month spinner")
        time.sleep(1)

        # Pick a random month (e.g., May)
        try:
            random_month = random.randint(1, 12)
            month_text = calendar.month_name[random_month]
            driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{month_text}")').click()
            log_info(f"✅ Selected month: {month_text}")
        except NoSuchElementException:
            log_info(f"⚠️ Month '{month_text}' not found via Appium, falling back to OCR.")
            # select_month_via_ocr(device_name)  # Pass month_text to OCR version
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                log_info(f"🔁 OCR Attempt {attempt}")
                success = select_month_via_ocr(device_name)
                if success:
                    log_info(f"✅ Successfully selected month via OCR on attempt {attempt}")
                    break
                else:
                    log_info(f"❌ Attempt {attempt} failed. Retrying..." if attempt < max_retries else f"❌ All attempts failed.")
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Month")'))
                    )
                    time.sleep(1)  # Optional delay between retries
        # Select Day
        day_spinner = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("BirthDayDropdown")')
        day_spinner.click()
        log_info("📅 Clicked Day spinner")
        time.sleep(1)
        
        try:
            random_day = random.randint(5, 18)
            driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{random_day}")').click()
            log_info(f"✅ Selected day: {random_day}")
        except NoSuchElementException:
            log_info(f"⚠️ Day not found via Appium, falling back to OCR.")
            # select_month_via_ocr(device_name)  # Pass month_text to OCR version
            max_retries = 3
            for attempt in range(1, max_retries + 1):
                log_info(f"🔁 OCR Attempt {attempt}")
                success = select_day_via_ocr(device_name)
                if success:
                    log_info(f"✅ Successfully selected day via OCR on attempt {attempt}")
                    break
                else:
                    log_info(f"❌ Attempt {attempt} failed. Retrying..." if attempt < max_retries else f"❌ All attempts failed.")
                    month_spinner = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("BirthMonthDropdown")')
                    month_spinner.click()
                    time.sleep(1)  # Optional delay between retries

        
        # Enter Year (just like password input)
        log_info("⏳ Waiting for Year EditText field")
        year_input = WebDriverWait(driver, 20).until(
            #EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("floatingLabelInput29")'))
            EC.presence_of_element_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
        )
        year_input.click()
        time.sleep(0.3)

        year = str(random.randint(1980, 2010))
        #year_input.send_keys(year)
        subprocess.run(["adb", "-s", device_name, "shell", "input", "text", year])
        log_info(f"📆 Entered year: {year}")

        driver.hide_keyboard()
        # year_label = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Year")'))
        # )
        # year_label.click()
        # log_info("🖱️ Clicked on 'Year' label")

        # # Step 2: Now find the EditText and send the year
        # year_input = WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
        # )

        # year = str(random.randint(1980, 2010))
        # year_input.click()  # tap to focus
        # time.sleep(0.3)
        # year_input.send_keys(year)
        # log_info(f"📆 Entered year: {year}")

        # Click Next
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Next")'))
        ).click()
        log_info("➡️ Clicked 'Next' after DOB")
        time.sleep(10)
        
        # Step 7: Wait for the First and Last name EditText fields
        log_info("⏳ Waiting for First and Last name fields")

        # Wait until at least 2 EditText fields appear (First Name and Last Name)
        WebDriverWait(driver, 30).until(
            lambda d: len(d.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")) >= 2
        )

        name_fields = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")

        # Safely enter first and last names
        if len(name_fields) >= 2:
            name_fields[0].send_keys(first)
            name_fields[1].send_keys(last)
            log_info(f"✅ Entered First Name: {first}, Last Name: {last}")
        else:
            log_error("❌ First and Last name fields not found")

        driver.hide_keyboard()
        time.sleep(2)

        # Step 8: Click Next after entering names
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Next").clickable(true).enabled(true)')) #'new UiSelector().textContains("Next")'))
        ).click()
        log_info("➡️ Clicked 'Next' after entering First and Last name")
        time.sleep(10)

        log_info("🤖 Performing long press via ADB on CAPTCHA button")
        subprocess.run([
            "adb", "-s", device_name,
            "shell", "input", "touchscreen", "swipe",
            "540", "1376", "540", "1376", "10000"  # 10 seconds
        ])
        log_info("✅ ADB long press complete")
        # press_and_hold_button(device_name)

        time.sleep(30)

        # Step: Wait for and click the OK button
        log_info("⏳ Waiting for 'OK' button to be clickable")

        try:
            ok_button = WebDriverWait(driver, 20).until(
              EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("OK")'))
            )
            ok_button.click()
            log_info("✅ Clicked on 'OK' button")
        except Exception as e:
            log_error(f"❌ Failed to click 'OK' button: {e}")
            return {"data": f"Failed to click 'OK' button: {e}", "status": False}

        # Wait for next screen to process
        log_info("⏳ Waiting 30 seconds after clicking OK")
        time.sleep(30)
        
        # Step: Click "MAYBE LATER"
        log_info("⏳ Waiting for 'MAYBE LATER' button to appear")

        try:
            maybe_later_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("MAYBE LATER")'))
            )
            maybe_later_button.click()
            log_info("✅ Clicked on 'MAYBE LATER' button")
        except Exception as e:
            log_error(f"❌ Failed to click 'MAYBE LATER' : {e}")
            return {"data": f"Failed to click 'MAYBE LATER' button: {e}", "status": False}

        time.sleep(20)    
        # # Wait until the "NEXT" button is clickable
        # next_btn = WebDriverWait(driver, 20).until(
        #      EC.element_to_be_clickable((AppiumBy.ID, "com.microsoft.office.outlook:id/bottom_flow_navigation_end_button"))
        # )

        # # Click the "NEXT" button
        # next_btn.click()
        # log_info("✅ Clicked on NEXT button after 'Maybe Later' screen.")
        log_info("⏳ Waiting for 'NEXT' button after 'Maybe Later'")
        try:
            next_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((AppiumBy.ID, "com.microsoft.office.outlook:id/bottom_flow_navigation_end_button"))
            )
            next_btn.click()
            log_info("✅ Clicked on NEXT button after 'Maybe Later' screen.")
        except Exception as e:
            log_error(f"❌ Failed to click 'NEXT' button after 'Maybe Later' :{e}")
            return {"data": f"Failed to click 'NEXT' after 'Maybe Later': {e} ", "status": False}

        
        try:
           log_info("🔎 Waiting for 'ACCEPT' button to appear...")
           accept_button = WebDriverWait(driver, 20).until(
           EC.element_to_be_clickable((AppiumBy.ID, "com.microsoft.office.outlook:id/btn_primary_button"))
           )
           accept_button.click()
           log_info("✅ 'ACCEPT' button clicked successfully.")
        except Exception as e:
            log_error(f"❌ Failed to click ACCEPT button: {e}")
            return {"data": f"Failed to click 'ACCEPT' button: {e}", "status": False}
            
        try:
            log_info("🔎 Waiting for 'CONTINUE TO OUTLOOK' button...")
            continue_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((AppiumBy.ID, "com.microsoft.office.outlook:id/bottom_flow_navigation_end_button"))
            )
            continue_button.click()
            log_info("✅ 'CONTINUE TO OUTLOOK' button clicked.")
        except Exception as e:
            log_error(f"❌ Failed to click CONTINUE TO OUTLOOK: {e}")
            return {"data": f"Failed to click 'CONTINUE TO OUTLOOK' button: {e}", "status": False}
        
        time.sleep(25)
        log_info("🎉 Account successfully created.")
        return {
            "data": {
                "message": "Account created successfully",
                "email": email,
                "password": password
            },
            "status": True
        }
                            

    except Exception as e:
        log_error(f"❌ Automation failed: {e}")
        return {"data": f"Mail Creation failed: {e}", "status": False}
    finally:
        try:
            if driver:
                driver.quit()
                log_info("📴 Driver closed")
        except Exception as e:
            log_error(f"❌ Failed to quit driver: {e}")

# Run the function
# if __name__ == "__main__":
#     automate_outlook_create_account("VIFD960313MPLLLL03","ZE223FZQ6C")
