import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
import base64
import logging
from datetime import datetime
from logger import logger
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from imss import pdfExtractionScraper
# Constants
URL = "https://outlook.live.com/mail/0/?prompt=select_account" 
MAX_WAIT = 30
MAX_RETRIES = 3

# EMAIL = ""
# PASSWORD = ""  # NOT your regular password

# # Setup Chrome
# options = Options()
# options.add_argument("--start-maximized")
# # options.add_argument("--headless")  # Optional: uncomment for headless
# driver = webdriver.Chrome(options=options)

def random_delay():
    seconds = random.randint(8, 13)
    print(f"⏳ Waiting for {seconds} seconds...")
    time.sleep(seconds)

def wait_for_element(xpath, driver, timeout=MAX_WAIT):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
    except:
        return None

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

def pdfExtractionUsingOutlookWeb(email, password, curp):
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # Optional
    driver = webdriver.Chrome(options=options)
    # options = Options()
    # profile_path = os.path.abspath("proxy-profile")
    # options.add_argument(f"--user-data-dir={profile_path}")
    # options.add_argument("--incognito")  # ✅ ONLY if extension is allowed in incognito
    # options.add_argument("--start-maximized")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")

    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        logger.info("Starting Outlook Web login flow...", extra={"curp": curp})
        driver.get(URL)
        time.sleep(10)

        # Step 1: Enter Email
        while True:
            logger.info("Waiting for email input...", extra={"curp": curp})
            email_input = wait_for_element('//*[@id="i0116"]', driver)
            if email_input:
                logger.info("Email input found. Entering email...", extra={"curp": curp})
                email_input.send_keys(email)
                next_btn_after_email = wait_for_element('//*[@id="idSIButton9"]', driver)
                if next_btn_after_email:
                    next_btn_after_email.click()
                    random_delay()
                else:
                    logger.error("Next button after email not found.", extra={"curp": curp})
                    return {"data": "Next button not found after email input", "status": False}
                break
            else:
                logger.warning("Email input not found. Refreshing page...", extra={"curp": curp})
                driver.refresh()

        # Step 2: Enter Password
        password_input = wait_for_element('//*[@id="passwordEntry"]', driver)
        if password_input:
            logger.info("Password input found. Entering password...", extra={"curp": curp})
            password_input.send_keys(password)
            random_delay()
        else:
            logger.error("Password input not found.", extra={"curp": curp})
            return {"data": "Password input not found", "status": False}
        
        

        # Step 3: Final Next
        final_next_btn = wait_for_element('//*[@id="view"]/div/div[5]/button', driver)
        if final_next_btn:
            final_next_btn.click()
            random_delay()
        else:
            return {"data": "Final 'Next' button not found", "status": False}
        
        # Step 3.5: Handle optional "Skip for now" screen
        # skip_button_xpath = '//*[@id="view"]/div/div[5]/button[2]'
        # skip_button = wait_for_element(skip_button_xpath, driver, timeout=5)
        # if skip_button:
        #     try:
        #         logger.info("'Skip for now' button found. Clicking...", extra={"curp": curp})
        #         skip_button.click()
        #         random_delay()
        #     except Exception as e:
        #         logger.warning(f"Could not click 'Skip for now' button: {e}", extra={"curp": curp})
        skip_xpath = '//*[@id="view"]/div/div[5]/button[2]'
        for attempt in range(3):
            skip_button = wait_for_element(skip_xpath, driver, timeout=5)
            if skip_button:
                try:
                    logger.info(f"Attempt {attempt+1}: Found 'Skip for now' button. Scrolling and clicking...", extra={"curp": curp})
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", skip_button)
                    time.sleep(1)
                    skip_button.click()
                    random_delay()

                    # Wait and check if it disappeared
                    time.sleep(2)
                    still_there = wait_for_element(skip_xpath, driver, timeout=3)
                    if not still_there:
                        logger.info("'Skip for now' popup handled successfully.", extra={"curp": curp})
                        break
                    else:
                        logger.warning("'Skip for now' button still visible. Retrying...", extra={"curp": curp})
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1}: Failed to click 'Skip for now': {e}", extra={"curp": curp})
            else:
                logger.info("No 'Skip for now' button found. Skipping this step.", extra={"curp": curp})
                break
        


        # # Step 4: Handle "Stay Signed In"
        # no_button = wait_for_element('//*[@id="view"]/div/div[5]/button[2]', driver)
        # if no_button:
        #     logger.info("'No' button found. Clicking...", extra={"curp": curp})
        #     no_button.click()
        #     random_delay()
        no_button_xpath = '//*[@id="view"]/div/div[5]/button[2]'
        for attempt in range(3):
            no_button = wait_for_element(no_button_xpath, driver, timeout=5)
            if no_button:
                try:
                    logger.info(f"Attempt {attempt+1}: Found 'No' button. Scrolling and clicking...", extra={"curp": curp})
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", no_button)
                    time.sleep(1)
                    no_button.click()
                    random_delay()

                    # Check if button is still there after click
                    time.sleep(2)
                    still_there = wait_for_element(no_button_xpath, driver, timeout=3)
                    if not still_there:
                        logger.info("'Stay Signed In' prompt handled successfully.", extra={"curp": curp})
                        break
                    else:
                        logger.warning("'No' button still visible. Retrying...", extra={"curp": curp})
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1}: Failed to click 'No' button: {e}", extra={"curp": curp})
            else:
                logger.info("No 'Stay Signed In' button found. Moving on.", extra={"curp": curp})
                break
            
        logger.info("Waiting 10 seconds for inbox to load...", extra={"curp": curp})
        time.sleep(10)
        # Step 5: Look for target email
        logger.info("Waiting for 'Servicio Digital:' email...", extra={"curp": curp})
        start_time = time.time()
        while time.time() - start_time < 300:
            try:
                element_with_text = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Servicio Digital:')]"))
                )
                logger.info("'Servicio Digital:' email found. Clicking...", extra={"curp": curp})
                element_with_text.click()
                break
            except:
                logger.warning("'Servicio Digital:' email not found. Refreshing...", extra={"curp": curp})
                driver.refresh()
                time.sleep(15)
        else:
            logger.error("Timeout waiting for 'Servicio Digital:' email.", extra={"curp": curp})
            return {"data": "'Servicio Digital:' email not found within timeout", "status": False}

        time.sleep(5)

        # Step 6: Extract link and download PDF
        try:
            logger.info("Looking for download link in email...", extra={"curp": curp})
            link_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(text(), 'Solicitud de Constancia de Semanas Cotizadas del Asegurado')]")
                )
            )
            raw_link = link_element.get_attribute("href")

            if raw_link:
                cleaned_link = (
                    raw_link.replace("detalle=true", "detalle=detalle")
                            .replace("detalle=false", "detalle=detalle")
                            .replace("&origen=MOVILES", "")
                            .replace("origen=MOVILES&", "")
                )
                if "detalle=detalle" not in cleaned_link:
                    cleaned_link += "&detalle=detalle" if "?" in cleaned_link else "?detalle=detalle"

                result = pdfExtractionScraper(curp, cleaned_link)
                if result.get("status"):
                    logger.info("PDF successfully downloaded and processed.", extra={"curp": curp})
                    return {"data": result["data"], "status": True}
                else:
                    logger.error(f"PDF download failed: {result}", extra={"curp": curp})
                    return {"data": result.get("data", "error"), "status": False}
            else:
                return {"data": "Link was empty or not extracted properly.", "status": False}

        except Exception as e:
            logger.error(f"Failed to locate link element: {str(e)}", extra={"curp": curp})
            return {"data": f"Failed to locate link: {str(e)}", "status": False}

    finally:
        logger.info("🧹 Cleaning up and quitting driver...", extra={"curp": curp})
        driver.quit()

# if __name__ == "__main__":
#     pdfExtractionUsingOutlookWeb("qeza_gojaci_50867@outlook.com","Z3CTgei!8K3Z1ay", "TEST1234")   # pas the email and password and the curp to the function





























# import time
# import random
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import os
# import requests
# import base64
# import logging
# from datetime import datetime
# from logger import logger
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# # Constants
# URL = "https://outlook.live.com/mail/0/?prompt=select_account" 
# MAX_WAIT = 30
# MAX_RETRIES = 3

# # EMAIL = ""
# # PASSWORD = ""  # NOT your regular password

# # # Setup Chrome
# # options = Options()
# # options.add_argument("--start-maximized")
# # # options.add_argument("--headless")  # Optional: uncomment for headless
# # driver = webdriver.Chrome(options=options)

# def random_delay():
#     seconds = random.randint(8, 13)
#     print(f"⏳ Waiting for {seconds} seconds...")
#     time.sleep(seconds)

# def wait_for_element(xpath, driver, timeout=MAX_WAIT):
#     try:
#         return WebDriverWait(driver, timeout).until(
#             EC.presence_of_element_located((By.XPATH, xpath))
#         )
#     except:
#         return None
    
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

# def pdfExtractionUsingOutlookWeb(email, password, curp):
#     # options = Options()
#     # options.add_argument("--start-maximized")
#     # # options.add_argument("--headless")  # Optional
#     # driver = webdriver.Chrome(options=options)
#     options = Options()
#     profile_path = os.path.abspath("proxy-profile")
#     options.add_argument(f"--user-data-dir={profile_path}")
#     options.add_argument("--incognito")  # ✅ ONLY if extension is allowed in incognito
#     options.add_argument("--start-maximized")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")

#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

#     try:
#         logger.info("Starting Outlook Web login flow...", extra={"curp": curp})
#         driver.get(URL)
#         time.sleep(10)

#         # Step 1: Enter Email
#         while True:
#             logger.info("Waiting for email input...", extra={"curp": curp})
#             email_input = wait_for_element('//*[@id="i0116"]', driver)
#             if email_input:
#                 logger.info("Email input found. Entering email...", extra={"curp": curp})
#                 email_input.send_keys(email)
#                 next_btn_after_email = wait_for_element('//*[@id="idSIButton9"]', driver)
#                 if next_btn_after_email:
#                     next_btn_after_email.click()
#                     random_delay()
#                 else:
#                     logger.error("Next button after email not found.", extra={"curp": curp})
#                     return {"data": "Next button not found after email input", "status": False}
#                 break
#             else:
#                 logger.warning("Email input not found. Refreshing page...", extra={"curp": curp})
#                 driver.refresh()

#         # Step 2: Enter Password
#         password_input = wait_for_element('//*[@id="passwordEntry"]', driver)
#         if password_input:
#             logger.info("Password input found. Entering password...", extra={"curp": curp})
#             password_input.send_keys(password)
#             random_delay()
#         else:
#             logger.error("Password input not found.", extra={"curp": curp})
#             return {"data": "Password input not found", "status": False}
        
        

#         # Step 3: Final Next
#         final_next_btn = wait_for_element('//*[@id="view"]/div/div[5]/button', driver)
#         if final_next_btn:
#             final_next_btn.click()
#             random_delay()
#         else:
#             return {"data": "Final 'Next' button not found", "status": False}
        
#         # Step 3.5: Handle optional "Skip for now" screen
#         skip_button_xpath = '//*[@id="view"]/div/div[5]/button[2]'
#         skip_button = wait_for_element(skip_button_xpath, driver, timeout=5)
#         if skip_button:
#             try:
#                 logger.info("'Skip for now' button found. Clicking...", extra={"curp": curp})
#                 skip_button.click()
#                 random_delay()
#             except Exception as e:
#                 logger.warning(f"Could not click 'Skip for now' button: {e}", extra={"curp": curp})


#         # Step 4: Handle "Stay Signed In"
#         no_button = wait_for_element('//*[@id="view"]/div/div[5]/button[2]', driver)
#         if no_button:
#             logger.info("'No' button found. Clicking...", extra={"curp": curp})
#             no_button.click()
#             random_delay()
            
#         logger.info("Waiting 10 seconds for inbox to load...", extra={"curp": curp})
#         time.sleep(10)
#         # Step 5: Look for target email
#         logger.info("Waiting for 'Servicio Digital:' email...", extra={"curp": curp})
#         start_time = time.time()
#         while time.time() - start_time < 300:
#             try:
#                 element_with_text = WebDriverWait(driver, 10).until(
#                     EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Servicio Digital:')]"))
#                 )
#                 logger.info("'Servicio Digital:' email found. Clicking...", extra={"curp": curp})
#                 element_with_text.click()
#                 break
#             except:
#                 logger.warning("'Servicio Digital:' email not found. Refreshing...", extra={"curp": curp})
#                 driver.refresh()
#                 time.sleep(15)
#         else:
#             logger.error("Timeout waiting for 'Servicio Digital:' email.", extra={"curp": curp})
#             return {"data": "'Servicio Digital:' email not found within timeout", "status": False}

#         time.sleep(5)

#         # Step 6: Extract link and download PDF
#         try:
#             logger.info("Looking for download link in email...", extra={"curp": curp})
#             link_element = WebDriverWait(driver, 20).until(
#                 EC.presence_of_element_located(
#                     (By.XPATH, "//a[contains(text(), 'Solicitud de Constancia de Semanas Cotizadas del Asegurado')]")
#                 )
#             )
#             raw_link = link_element.get_attribute("href")

#             if raw_link:
#                 cleaned_link = (
#                     raw_link.replace("detalle=true", "detalle=detalle")
#                             .replace("detalle=false", "detalle=detalle")
#                             .replace("&origen=MOVILES", "")
#                             .replace("origen=MOVILES&", "")
#                 )
#                 if "detalle=detalle" not in cleaned_link:
#                     cleaned_link += "&detalle=detalle" if "?" in cleaned_link else "?detalle=detalle"

#                 result = pdfExtractionScraper(curp, cleaned_link)
#                 if result.get("status"):
#                     logger.info("PDF successfully downloaded and processed.", extra={"curp": curp})
#                     return {"data": result["data"], "status": True}
#                 else:
#                     logger.error(f"PDF download failed: {result}", extra={"curp": curp})
#                     return {"data": result.get("data", "error"), "status": False}
#             else:
#                 return {"data": "Link was empty or not extracted properly.", "status": False}

#         except Exception as e:
#             logger.error(f"Failed to locate link element: {str(e)}", extra={"curp": curp})
#             return {"data": f"Failed to locate link: {str(e)}", "status": False}

#     finally:
#         logger.info("🧹 Cleaning up and quitting driver...", extra={"curp": curp})
#         driver.quit()

# if __name__ == "__main__":
#     pdfExtractionUsingOutlookWeb("priyanshjain1203@outlook.com","PJoutlook@1203", "TEST1234")   # pas the email and password and the curp to the function
