import time
import random
import subprocess
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from logger import logger
import sys
import base64
import os
import requests
from filelock import FileLock
import json
from imss import pdfExtractionScraper

EMAIL = "kizix_xupiz_81870@outlook.com"
PASSWORD = "6HnHL3#d!r3Cmj!"
CURP = "MASA020416HCHRNLA9"
DEVICE_ID = "RFCY2019MPN"
URL = "https://outlook.live.com/mail/0/?prompt=select_account"
UTILS_FOLDER = "utils"
DEVICE_PORT_FILE = os.path.join(UTILS_FOLDER, "device_port_map.json")
DEVICE_PORT_LOCK = DEVICE_PORT_FILE + ".lock"
BASE_PORT = 9222

def get_port_for_device(device_id):
    with FileLock(DEVICE_PORT_LOCK):
        if os.path.exists(DEVICE_PORT_FILE):
            with open(DEVICE_PORT_FILE, "r") as f:
                try:
                    device_port_map = json.load(f)
                except json.JSONDecodeError:
                    device_port_map = {}
        else:
            device_port_map = {}

        if device_id in device_port_map:
            return device_port_map[device_id]

        assigned_ports = set(device_port_map.values())
        next_port = BASE_PORT
        while next_port in assigned_ports:
            next_port += 1

        device_port_map[device_id] = next_port

        with open(DEVICE_PORT_FILE, "w") as f:
            json.dump(device_port_map, f, indent=2)

        return next_port

def random_delay():
    seconds = random.randint(8, 13)
    logger.info(f"\u23f3 Random delay: {seconds} seconds...", extra={"curp": CURP})
    time.sleep(seconds)

def connect_device_port(device_id, devtools_port, curp):
    subprocess.run(["adb", "-s", device_id, "forward", f"tcp:{devtools_port}", "localabstract:chrome_devtools_remote"])
    logger.info(f"🔌 Port {devtools_port} forwarded for device {device_id}", extra={"curp": curp})

def soft_reset_chrome(device_id, curp):
    try:
        logger.info("🚪 Closing all Chrome tabs without data wipe...", extra={"curp": curp})
        subprocess.run(["adb", "-s", device_id, "shell", "am", "force-stop", "com.android.chrome"], check=True)
        subprocess.run([
            "adb", "-s", device_id, "shell", "am", "start",
            "-n", "com.android.chrome/com.google.android.apps.chrome.Main",
            "-a", "android.intent.action.VIEW",
            "-d", "about:blank",
            "--ez", "create_new_tab", "true",
            "--ez", "incognito", "true"
        ], check=True)
        logger.info("✅ Chrome restarted with new incognito tab (no old tabs restored)", extra={"curp": curp})
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error during tab reset: {e}", extra={"curp": curp})

def wait_and_click(locator, label, curp, timeout=15000):
    async def inner():
        try:
            await locator.wait_for(timeout=timeout)
            await locator.click()
            logger.info(f"✅ Clicked: {label}", extra={"curp": curp})
            random_delay()
            return True
        except PlaywrightTimeoutError:
            logger.error(f"❌ Timeout waiting for {label}", extra={"curp": curp})
            return False
    return inner

# def pdfExtractionScraper(curp, url):
#     for i in range(6):
#         try:
#             logger.info(f"Attempt {i+1} to fetch PDF from: {url}", extra={"curp": curp})
#             response = requests.get(
#                 url,
#                proxies={
                   
#                    "http": "http://mngesieu-rotate:2npHQ41kMZpm@p.webshare.io:80",
#                     "https": "http://mngesieu-rotate:2npHQ41kMZpm@p.webshare.io:80"

#                     # "http" : "http://SProxy01:3w+rW0wSfQ8Tnrf8xd@mx.smartproxy.com:20000",
#                     # "https" : "http://SProxy01:3w+rW0wSfQ8Tnrf8xd@mx.smartproxy.com:20000"

#                     #"http": "http://SProxy01:69+axtKowN5Ut2qphI@mx.smartproxy.com:20000",
#                     #"https": "http://SProxy01:69+axtKowN5Ut2qphI@mx.smartproxy.com:20000"
#                 })
#             if response.status_code == 200:
#                 pdf_bytes = response.content
#                 if b'PDF' in pdf_bytes:
#                     # Ensure the directory exists
#                     os.makedirs("pdf", exist_ok=True)

#                     # Create file path as pdf/curp_YYYYMMDD_HHMMSS.pdf
#                     # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                     file_path = f"pdf/{curp}.pdf"

#                     # Write PDF file
#                     with open(file_path, "wb") as f:
#                         f.write(pdf_bytes)
#                     logger.info(f"PDF saved successfully as: {file_path}", extra={"curp": curp})

#                     return {
#                         "status": True,
#                         "data": base64.b64encode(pdf_bytes).decode("utf-8"),
#                         # "file_path": file_path
#                     }
#             return {
#                 "status": False,
#                 "data": response.text,
#                 "error": f"Failed to fetch PDF: {response.status_code}"
#             }
#         except Exception as e:
#             logger.error(f"Error fetching PDF: {str(e)}", extra={"curp": curp})
#             return {
#                 "status": False,
#                 "error": str(e)
#             }
            
# def pdfExtractionScraper(curp, url):
#     last_error = None  # To capture the last error or response message

#     for i in range(6):
#         try:
#             logger.info(f"Attempt {i+1} to fetch PDF from: {url}", extra={"curp": curp})
#             response = requests.get(
#                 url,
#                 proxies={
#                     "http": "http://mngesieu-rotate:2npHQ41kMZpm@p.webshare.io:80",
#                     "https": "http://mngesieu-rotate:2npHQ41kMZpm@p.webshare.io:80"
#                 },
#                 timeout=30
#             )

#             if response.status_code == 200:
#                 pdf_bytes = response.content
#                 if b'PDF' in pdf_bytes:
#                     os.makedirs("pdf", exist_ok=True)
#                     file_path = f"pdf/{curp}.pdf"
#                     with open(file_path, "wb") as f:
#                         f.write(pdf_bytes)
#                     logger.info(f"PDF saved successfully as: {file_path}", extra={"curp": curp})
#                     return {
#                         "status": True,
#                         "data": base64.b64encode(pdf_bytes).decode("utf-8"),
#                     }
#                 else:
#                     last_error = "Response is 200 but content is not a valid PDF"
#                     logger.warning(last_error, extra={"curp": curp})
#             else:
#                 last_error = f"Non-200 response: {response.status_code}"
#                 logger.warning(last_error, extra={"curp": curp})

#         except Exception as e:
#             last_error = f"Exception: {str(e)}"
#             logger.error(last_error, extra={"curp": curp})

#         time.sleep(5)  # Delay before retry

#     # All attempts failed
#     return {
#         "status": False,
#         "error": last_error or "Unknown error"
#     }

async def pdf_extraction_using_playwright(email, password, curp, device_id):
    # subprocess.run(["adb", "-s", device_id, "shell", "settings", "put", "global", "http_proxy", ""])
    devtools_port = get_port_for_device(device_id)
    soft_reset_chrome(device_id, curp)
    connect_device_port(device_id, devtools_port, curp)

    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{devtools_port}")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()

            logger.info("🪝 Clearing cookies and storage...", extra={"curp": curp})
            await context.clear_cookies()
            await context.clear_permissions()

            temp_page = await context.new_page()
            await temp_page.goto("about:blank", timeout=10000)
            try:
                await temp_page.evaluate("localStorage.clear(); sessionStorage.clear();")
                logger.info("🪜 Cleared localStorage and sessionStorage", extra={"curp": curp})
            except Exception as e:
                logger.warning(f"⚠️ Could not clear storage: {e}", extra={"curp": curp})
            await temp_page.close()

            page = await context.new_page()
            logger.info("🌐 Navigating to Outlook login page...", extra={"curp": curp})
            await page.goto(URL, timeout=60000)

            logger.info("🔍 Looking for email input...", extra={"curp": curp})
            email_input = page.locator('//*[@id="i0116"]')
            await email_input.wait_for(timeout=15000)
            await email_input.fill(email)
            logger.info("✅ Email entered", extra={"curp": curp})

            if not await wait_and_click(page.locator('//*[@id="idSIButton9"]'), "Next after email", curp)():
                return {"status": False, "data": "Next button after email not found"}

            logger.info("🔍 Looking for password input...", extra={"curp": curp})
            pwd_input = page.locator('//*[@name="passwd"]')
            await pwd_input.wait_for(timeout=15000)
            await pwd_input.fill(password)
            logger.info("✅ Password entered", extra={"curp": curp})

            if not await wait_and_click(page.locator('//*[@id="view"]/div/div[5]/button'), "Final Next", curp)():
                return {"status": False, "data": "Final Next button not found"}

            # Step 3: Optional "Skip for now"
            skip_xpath = '//*[@id="view"]/div/div[5]/button[2]'
            for attempt in range(3):
                try:
                    skip_button = page.locator(skip_xpath)
                    if await skip_button.is_visible():
                        logger.info(f"Attempt {attempt+1}: Clicking 'Skip for now'...", extra={"curp": curp})
                        await skip_button.scroll_into_view_if_needed()
                        await skip_button.click()
                        random_delay()
                        if not await skip_button.is_visible():
                            break
                except:
                    break

            # Step 4: Optional "Stay signed in"
            no_button_xpath = '//*[@id="view"]/div/div[5]/button[2]'
            for attempt in range(3):
                try:
                    no_button = page.locator(no_button_xpath)
                    if await no_button.is_visible():
                        logger.info(f"Attempt {attempt+1}: Clicking 'No' (Stay Signed In)...", extra={"curp": curp})
                        await no_button.scroll_into_view_if_needed()
                        await no_button.click()
                        random_delay()
                        if not await no_button.is_visible():
                            break
                except:
                    break

            # Step 5: Wait for inbox and look for email
            logger.info("📥 Waiting for inbox to load...", extra={"curp": curp})
            await page.wait_for_timeout(10000)

            # Check for Welcome popup
            try:
                welcome_popup_button = page.locator("//button[contains(., 'Continue to Inbox')]")
                if await welcome_popup_button.is_visible():
                    logger.info("📦 'Welcome to Outlook' popup detected. Clicking 'Continue to Inbox'...", extra={"curp": curp})
                    await welcome_popup_button.click()
                    await page.wait_for_timeout(3000)
                else:
                    logger.info("✅ No Welcome popup found", extra={"curp": curp})
            except Exception as e:
                logger.warning(f"⚠️ Could not handle Welcome popup: {e}", extra={"curp": curp})

            logger.info("🔍 Searching for 'Servicio Digital:' email...", extra={"curp": curp})
            found = False
            for attempt in range(10):
                try:
                    email_element = page.locator("//*[contains(text(), 'Servicio Digital:')]").first
                    if await email_element.count() > 0:
                        logger.info(f"🕵️ Attempt {attempt+1}: Found matching element(s)", extra={"curp": curp})
                        try:
                            await email_element.wait_for(timeout=5000)
                            logger.info("✅ Email element is ready. Clicking...", extra={"curp": curp})
                            await email_element.click(force=True)
                            found = True
                            break
                        except Exception as e:
                            logger.warning(f"⚠️ Click failed: {e}", extra={"curp": curp})
                    else:
                        logger.info("🚫 No matching email element found yet", extra={"curp": curp})
                except Exception as e:
                    logger.warning(f"❌ Error in attempt {attempt+1}: {e}", extra={"curp": curp})

                logger.warning("🔄 Refreshing page and retrying...", extra={"curp": curp})
                await page.reload()
                await page.wait_for_timeout(15000)

            if not found:
                return {"status": False, "data": "'Servicio Digital:' email not found in time"}

            # Step 6: Extract link and call PDF scraper
            try:
                logger.info("🔍 Looking for PDF download link in email...", extra={"curp": curp})
                await asyncio.sleep(5)

                link_locator = page.locator("//a[contains(text(), 'Solicitud de Constancia de Semanas Cotizadas del Asegurado')]")
                await link_locator.wait_for(timeout=20000)

                raw_link = await link_locator.first.get_attribute("href")

                if raw_link:
                    logger.info(f"🔗 Raw link found: {raw_link}", extra={"curp": curp})
                    cleaned_link = (
                        raw_link.replace("detalle=true", "detalle=detalle")
                                .replace("detalle=false", "detalle=detalle")
                                .replace("&origen=MOVILES", "")
                                .replace("origen=MOVILES&", "")
                    )
                    if "detalle=detalle" not in cleaned_link:
                        cleaned_link += "&detalle=detalle" if "?" in cleaned_link else "?detalle=detalle"

                    logger.info(f"🧼 Cleaned link: {cleaned_link}", extra={"curp": curp})

                    # Use the existing sync scraper for now (optional: make async later)
                    result = pdfExtractionScraper(curp, cleaned_link)

                    if result.get("status"):
                        logger.info("✅ PDF successfully downloaded and processed", extra={"curp": curp})
                        return {"data": result["data"], "status": True}
                    else:
                        logger.error(f"❌ PDF download failed: {result}", extra={"curp": curp})
                        return {"data": result.get("data", "error"), "status": False}
                else:
                    logger.error("❌ Link was empty or not extracted properly.", extra={"curp": curp})
                    return {"status": False, "data": "Link was empty or not extracted properly."}
            except Exception as e:
                logger.error(f"❌ Failed to locate or process PDF link: {str(e)}", extra={"curp": curp})
                return {"status": False, "data": f"Failed to locate or process PDF link: {str(e)}"}

        except Exception as e:
            logger.error(f"❌ Unexpected Error: {e}", extra={"curp": curp})
            return {"status": False, "data": str(e)}
        finally:
            if browser:
                await browser.close()
                logger.info("🪜 Cleaned up browser", extra={"curp": curp})

# if __name__ == "__main__":
#     asyncio.run(pdf_extraction_using_playwright(EMAIL, PASSWORD, CURP, DEVICE_ID))





















# import time
# import random
# import subprocess
# from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
# from logger import logger  # ✅ Your custom logger
# import sys
# import base64
# import os
# import requests
# import subprocess
# from filelock import FileLock
# import json

# EMAIL = "kizix_xupiz_81870@outlook.com"
# PASSWORD = "6HnHL3#d!r3Cmj!"
# CURP = "MASA020416HCHRNLA9"
# DEVICE_ID = "RFCY20LK9FY"
# # DEVTOOLS_PORT = 9222

# URL = "https://outlook.live.com/mail/0/?prompt=select_account"
# UTILS_FOLDER = "utils"
# # os.makedirs(UTILS_FOLDER, exist_ok=True)

# DEVICE_PORT_FILE = os.path.join(UTILS_FOLDER, "device_port_map.json")
# DEVICE_PORT_LOCK = DEVICE_PORT_FILE + ".lock"
# BASE_PORT = 9222
# def get_port_for_device(device_id):
#     with FileLock(DEVICE_PORT_LOCK):
#         # Load or initialize the mapping
#         if os.path.exists(DEVICE_PORT_FILE):
#             with open(DEVICE_PORT_FILE, "r") as f:
#                 try:
#                     device_port_map = json.load(f)
#                 except json.JSONDecodeError:
#                     device_port_map = {}
#         else:
#             device_port_map = {}

#         # Return existing port if already assigned
#         if device_id in device_port_map:
#             return device_port_map[device_id]

#         # Assign the next available port
#         assigned_ports = set(device_port_map.values())
#         next_port = BASE_PORT
#         while next_port in assigned_ports:
#             next_port += 1

#         # Store and save the mapping
#         device_port_map[device_id] = next_port

#         with open(DEVICE_PORT_FILE, "w") as f:
#             json.dump(device_port_map, f, indent=2)

#         return next_port
    

# def random_delay():
#     seconds = random.randint(8, 13)
#     logger.info(f"⏳ Random delay: {seconds} seconds...", extra={"curp": CURP})
#     time.sleep(seconds)

# def wait_and_click(page, xpath, label, timeout=15000):
#     try:
#         locator = page.locator(xpath)
#         locator.wait_for(timeout=timeout)
#         locator.click()
#         logger.info(f"✅ Clicked: {label}", extra={"curp": CURP})
#         random_delay()
#         return True
#     except PlaywrightTimeoutError:
#         logger.error(f"❌ Timeout waiting for {label}", extra={"curp": CURP})
#         return False


# def soft_reset_chrome(device_id, curp):
#     try:
#         logger.info("🚪 Closing all Chrome tabs without data wipe...", extra={"curp": curp})
        
#         # Step 1: Force stop Chrome
#         subprocess.run(["adb", "-s", device_id, "shell", "am", "force-stop", "com.android.chrome"], check=True)

#         # Step 2: Launch incognito tab (fresh session)
#         subprocess.run([
#             "adb", "-s", device_id, "shell", "am", "start",
#             "-n", "com.android.chrome/com.google.android.apps.chrome.Main",
#             "-a", "android.intent.action.VIEW",
#             "-d", "about:blank",
#             "--ez", "create_new_tab", "true",
#             "--ez", "incognito", "true"
#         ], check=True)

#         logger.info("✅ Chrome restarted with new incognito tab (no old tabs restored)", extra={"curp": curp})
#     except subprocess.CalledProcessError as e:
#         logger.error(f"❌ Error during tab reset: {e}", extra={"curp": curp})
            
# def pdfExtractionScraper(curp, url):
#     for i in range(6):
#         try:
#             logger.info(f"Attempt {i+1} to fetch PDF from: {url}", extra={"curp": curp})
#             response = requests.get(
#                 url,
#                proxies={
#                     "http" : "http://SProxy01:3w+rW0wSfQ8Tnrf8xd@mx.smartproxy.com:20000",
#                     "https" : "http://SProxy01:3w+rW0wSfQ8Tnrf8xd@mx.smartproxy.com:20000"

#                     #"http": "http://SProxy01:69+axtKowN5Ut2qphI@mx.smartproxy.com:20000",
#                     #"https": "http://SProxy01:69+axtKowN5Ut2qphI@mx.smartproxy.com:20000"
#                 })
#             if response.status_code == 200:
#                 pdf_bytes = response.content
#                 if b'PDF' in pdf_bytes:
#                     # Ensure the directory exists
#                     os.makedirs("pdf", exist_ok=True)

#                     # Create file path as pdf/curp_YYYYMMDD_HHMMSS.pdf
#                     # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                     file_path = f"pdf/{curp}.pdf"

#                     # Write PDF file
#                     with open(file_path, "wb") as f:
#                         f.write(pdf_bytes)
#                     logger.info(f"PDF saved successfully as: {file_path}", extra={"curp": curp})

#                     return {
#                         "status": True,
#                         "data": base64.b64encode(pdf_bytes).decode("utf-8"),
#                         # "file_path": file_path
#                     }
#             return {
#                 "status": False,
#                 "data": response.text,
#                 "error": f"Failed to fetch PDF: {response.status_code}"
#             }
#         except Exception as e:
#             logger.error(f"Error fetching PDF: {str(e)}", extra={"curp": curp})
#             return {
#                 "status": False,
#                 "error": str(e)
#             }
            

# def connect_device_port(device_id, devtools_port, curp):
#     subprocess.run(["adb", "-s", device_id, "forward", f"tcp:{devtools_port}", "localabstract:chrome_devtools_remote"])
#     logger.info(f"🔌 Port {devtools_port} forwarded for device {device_id}", extra={"curp": curp})

# def pdf_extraction_using_playwright(email, password, curp,device_id):
#     devtools_port = get_port_for_device(device_id)
#     soft_reset_chrome(device_id, curp)
#     connect_device_port(device_id, devtools_port, curp)
#     browser = None
#     with sync_playwright() as p:
#         try:
#             browser = p.chromium.connect_over_cdp(f"http://localhost:{devtools_port}")
#             context = browser.contexts[0] if browser.contexts else browser.new_context()
            
#             # ✅ Clear cookies and storage before creating the new page
#             logger.info("🧹 Clearing cookies and storage before starting new session...", extra={"curp": curp})
#             context.clear_cookies()
#             context.clear_permissions()
            
#             # ✅ Clear localStorage and sessionStorage
#             temp_page = context.new_page()
#             temp_page.goto("about:blank", timeout=10000)
#             try:
#                 temp_page.evaluate("localStorage.clear(); sessionStorage.clear();")
#                 logger.info("🧼 Cleared localStorage and sessionStorage", extra={"curp": curp})
#             except Exception as e:
#                 logger.warning(f"⚠️ Could not clear local/session storage: {e}", extra={"curp": curp})
#             temp_page.close()
            
            
#             page = context.new_page()

#             logger.info("🌐 Navigating to Outlook login page...", extra={"curp": curp})
#             page.goto(URL, timeout=60000)

#             # Step 1: Email input
#             logger.info("🔍 Looking for email input...", extra={"curp": curp})
#             page.locator('//*[@id="i0116"]').wait_for(timeout=15000)
#             page.locator('//*[@id="i0116"]').fill(email)
#             logger.info("✅ Email entered", extra={"curp": curp})

#             if not wait_and_click(page, '//*[@id="idSIButton9"]', "Next after email"):
#                 return {"status": False, "data": "Next button after email not found"}

#             # Step 2: Password input
#             logger.info("🔍 Looking for password input...", extra={"curp": curp})
#             page.locator('//*[@name="passwd"]').wait_for(timeout=15000)
#             page.locator('//*[@name="passwd"]').fill(password)
#             logger.info("✅ Password entered", extra={"curp": curp})

#             if not wait_and_click(page, '//*[@id="view"]/div/div[5]/button', "Final Next"):
#                 return {"status": False, "data": "Final Next button not found"}

#             # Step 3: Optional "Skip for now"
#             skip_xpath = '//*[@id="view"]/div/div[5]/button[2]'
#             for attempt in range(3):
#                 try:
#                     skip_button = page.locator(skip_xpath)
#                     if skip_button.is_visible():
#                         logger.info(f"Attempt {attempt+1}: Clicking 'Skip for now'...", extra={"curp": curp})
#                         skip_button.scroll_into_view_if_needed()
#                         skip_button.click()
#                         random_delay()
#                         if not skip_button.is_visible():
#                             break
#                 except:
#                     break

#             # Step 4: Optional "Stay signed in"
#             no_button_xpath = '//*[@id="view"]/div/div[5]/button[2]'
#             for attempt in range(3):
#                 try:
#                     no_button = page.locator(no_button_xpath)
#                     if no_button.is_visible():
#                         logger.info(f"Attempt {attempt+1}: Clicking 'No' (Stay Signed In)...", extra={"curp": curp})
#                         no_button.scroll_into_view_if_needed()
#                         no_button.click()
#                         random_delay()
#                         if not no_button.is_visible():
#                             break
#                 except:
#                     break

#             # Step 5: Wait for inbox and look for email
#             logger.info("📥 Waiting for inbox to load...", extra={"curp": curp})
#             page.wait_for_timeout(10000)
            
#             # Check for Welcome popup
#             try:
#                 welcome_popup_button = page.locator("//button[contains(., 'Continue to Inbox')]")
#                 if welcome_popup_button.is_visible():
#                     logger.info("📦 'Welcome to Outlook' popup detected. Clicking 'Continue to Inbox'...", extra={"curp": curp})
#                     welcome_popup_button.click()
#                     page.wait_for_timeout(3000)
#                 else:
#                     logger.info("✅ No Welcome popup found", extra={"curp": curp})
#             except Exception as e:
#                 logger.warning(f"⚠️ Could not handle Welcome popup: {e}", extra={"curp": curp})

#             logger.info("🔍 Searching for 'Servicio Digital:' email...", extra={"curp": curp})
#             found = False
#             for attempt in range(20):
#                 try:
#                     email_element = page.locator("//*[contains(text(), 'Servicio Digital:')]").first

#                     if email_element.count() > 0:
#                         logger.info(f"🕵️ Attempt {attempt+1}: Found matching element(s)", extra={"curp": curp})

#                         try:
#                             email_element.wait_for(timeout=5000)
#                             logger.info("✅ Email element is ready. Clicking...", extra={"curp": curp})

#                             # Try force click to overcome invisibility or overlay issues
#                             email_element.click(force=True)
#                             found = True
#                             break
#                         except Exception as e:
#                             logger.warning(f"⚠️ Click failed: {e}", extra={"curp": curp})
#                     else:
#                         logger.info("🚫 No matching email element found yet", extra={"curp": curp})

#                 except Exception as e:
#                     logger.warning(f"❌ Error in attempt {attempt+1}: {e}", extra={"curp": curp})

#                 logger.warning("🔄 Refreshing page and retrying...", extra={"curp": curp})
#                 page.reload()
#                 page.wait_for_timeout(15000)
                
#             if not found:
#                 return {"status": False, "data": "'Servicio Digital:' email not found in time"}

#             # Step 6: Extract link and call PDF scraper
#             try:
#                 logger.info("🔍 Looking for PDF download link in email...", extra={"curp": curp})
#                 time.sleep(5)

#                 link_locator = page.locator("//a[contains(text(), 'Solicitud de Constancia de Semanas Cotizadas del Asegurado')]")
#                 link_locator.wait_for(timeout=20000)

#                 raw_link = link_locator.first.get_attribute("href")

#                 if raw_link:
#                     logger.info(f"🔗 Raw link found: {raw_link}", extra={"curp": curp})

#                     # Clean up the link (as per your original logic)
#                     cleaned_link = (
#                         raw_link.replace("detalle=true", "detalle=detalle")
#                                 .replace("detalle=false", "detalle=detalle")
#                                 .replace("&origen=MOVILES", "")
#                                 .replace("origen=MOVILES&", "")
#                     )
#                     if "detalle=detalle" not in cleaned_link:
#                         cleaned_link += "&detalle=detalle" if "?" in cleaned_link else "?detalle=detalle"

#                     logger.info(f"🧼 Cleaned link: {cleaned_link}", extra={"curp": curp})

#                     # 🧾 Call your existing scraper function
#                     result = pdfExtractionScraper(curp, cleaned_link)

#                     if result.get("status"):
#                         logger.info("✅ PDF successfully downloaded and processed", extra={"curp": curp})
#                         return {"data": result["data"], "status": True}
#                     else:
#                         logger.error(f"❌ PDF download failed: {result}", extra={"curp": curp})
#                         return {"data": result.get("data", "error"), "status": False}
#                 else:
#                     logger.error("❌ Link was empty or not extracted properly.", extra={"curp": curp})
#                     return {"status": False, "data": "Link was empty or not extracted properly."}
#             except Exception as e:
#                 logger.error(f"❌ Failed to locate or process PDF link: {str(e)}", extra={"curp": curp})
#                 return {"status": False, "data": f"Failed to locate or process PDF link: {str(e)}"}


#         except Exception as e:
#             logger.error(f"❌ Unexpected Error: {e}", extra={"curp": curp})
#             return {"status": False, "data": str(e)}
#         finally:
#             if browser:
#                browser.close()
#                logger.info("🧹 Cleaned up browser", extra={"curp": curp})

# if __name__ == "__main__":
#     pdf_extraction_using_playwright(EMAIL, PASSWORD, CURP,DEVICE_ID)
