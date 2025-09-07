import os
import time
import asyncio
import logging
from datetime import datetime
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] > %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)
logger = logging.getLogger(__name__)

# PDF folder
pdf_folder = os.path.abspath("pdf")
os.makedirs(pdf_folder, exist_ok=True)

# Chrome user profile
user_data_dir = os.path.abspath("zoho")
os.makedirs(user_data_dir, exist_ok=True)

# Proxy setup
proxy_user = "SProxy01"
proxy_pass = "3w+rW0wSfQ8Tnrf8xd"
proxy_host = "mx.smartproxy.com"
proxy_port = "20000"
seleniumwire_options = {
    'proxy': {
        'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
        'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
        'no_proxy': 'localhost,127.0.0.1'
    }
}

# Chrome options
options = webdriver.ChromeOptions()
options.add_argument(f"--user-data-dir={user_data_dir}")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
prefs = {
    "download.default_directory": pdf_folder,
    "download.prompt_for_download": False,
    "plugins.always_open_pdf_externally": True,
}
options.add_experimental_option("prefs", prefs)
service = Service(ChromeDriverManager().install())

# Store processed email subjects
seen_subjects = set()

async def zoho_scraper():
    global seen_subjects
    while True:
        try:
            logger.info("🚀 Launching Zoho Webmail")
            driver = webdriver.Chrome(
                service=service,
                options=options,
                seleniumwire_options=seleniumwire_options,
            )
            driver.get("https://mail.zoho.com/zm/#search")

            # Wait for inbox
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".js-searchbox")))
            time.sleep(2)

            # Login check (only first time)
            try:
                login_box = driver.find_elements(By.CSS_SELECTOR, "#login_id")
                if login_box:
                    logger.info("🔐 Logging in...")
                    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#login_id'))).send_keys('contacto.principal@notariaedomex17.com')
                    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#nextbtn'))).click()
                    WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#password'))).send_keys('!9a#cMoei')
                    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#nextbtn'))).click()
                    logger.info("✅ Logged in")
            except:
                pass  # already logged in

            # Start refresh loop
            while True:
                driver.refresh()
                logger.info("🔄 Refreshed inbox")

                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".js-searchbox")))
                time.sleep(2)
                search_box = driver.find_element(By.CSS_SELECTOR, ".js-searchbox")
                search_box.clear()
                search_box.send_keys('Servicio Digital: Solicitud de Constancia de Semanas Cotizadas del Asegurado')
                search_box.send_keys(Keys.RETURN)

                time.sleep(5)
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".secTabs"))).click()

                emails = driver.find_elements(By.CSS_SELECTOR, '#jstab-zm_srch1 .zmLUrd')
                if not emails:
                    logger.info("📭 No matching emails found")
                for mail in emails[:5]:  # check only latest 5 to avoid loop spam
                    mail.click()
                    time.sleep(3)

                    subject_elem = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".zmMTitle"))
                    )
                    subject_text = subject_elem.text.strip()

                    if subject_text in seen_subjects:
                        logger.info(f"⏩ Already processed: {subject_text}")
                        continue
                    seen_subjects.add(subject_text)

                    for link in driver.find_elements(By.CSS_SELECTOR, '.zmMailWrapper a'):
                        if 'Solicitud de Constancia de Semanas Cotizadas del Asegurado' in link.text:
                            pdf_path = os.path.join("reporteSemanasCotizadas.pdf")
                            if os.path.exists(pdf_path):
                                os.remove(pdf_path)

                            if len(driver.window_handles) > 1:
                                for h in driver.window_handles[1:]:
                                    driver.switch_to.window(h)
                                    driver.close()
                            driver.switch_to.window(driver.window_handles[0])

                            to_email = driver.find_elements(By.CSS_SELECTOR, '.zmMHdrAddMail')[-1].text
                            curp = to_email.split('@')[0].split('_')[0].upper()

                            logger.info(f"📧 New Email → {to_email} | CURP: {curp}")

                            link.click()
                            for _ in range(10):
                                if os.path.exists(pdf_path):
                                    final_path = os.path.join(pdf_folder, f"{curp}.pdf")
                                    os.rename(pdf_path, final_path)
                                    logger.info(f"✅ PDF saved: {final_path}")
                                    break
                                time.sleep(2)
                logger.info("⏳ Waiting 15 seconds before next refresh...")
                time.sleep(15)

        except Exception as e:
            logger.error(f"🔥 Exception occurred: {e}")
            time.sleep(30)
        finally:
            try:
                driver.quit()
            except:
                pass
            logger.info("🔁 Restarting browser in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    asyncio.run(zoho_scraper())









# import os
# import time
# import logging
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# # Setup logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="[%(asctime)s] [%(levelname)s] > %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     force=True,
# )
# logger = logging.getLogger(__name__)

# pdf_folder = os.path.abspath("pdf")
# os.makedirs(pdf_folder, exist_ok=True)

# user_data_dir = os.path.abspath("zoho")
# os.makedirs(user_data_dir, exist_ok=True)

# # Keep track of already processed email subjects
# processed_subjects = set()


# def create_driver():
#     options = webdriver.ChromeOptions()
#     options.add_argument(f"--user-data-dir={user_data_dir}")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-gpu")

#     prefs = {
#         "download.default_directory": pdf_folder,
#         "download.prompt_for_download": False,
#         "plugins.always_open_pdf_externally": True,
#     }
#     options.add_experimental_option("prefs", prefs)

#     service = Service(ChromeDriverManager().install())
#     return webdriver.Chrome(service=service, options=options)


# def login_if_required(driver):
#     try:
#         WebDriverWait(driver, 15).until(
#             EC.any_of(
#                 EC.visibility_of_element_located((By.CSS_SELECTOR, '.js-searchbox')),
#                 EC.visibility_of_element_located((By.CSS_SELECTOR, '#login_id'))
#             )
#         )
#         if "login" in driver.current_url.lower():
#             logger.warning("Login screen detected — attempting login")
#             WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#login_id'))).send_keys('contacto.principal@notariaedomex17.com')
#             driver.find_element(By.CSS_SELECTOR, '#nextbtn').click()
#             WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#password'))).send_keys('!9a#cMoei')
#             driver.find_element(By.CSS_SELECTOR, '#nextbtn').click()
#     except Exception as e:
#         logger.error(f"Login failed: {e}")
#         raise RuntimeError("Login failed")


# def process_latest_email(driver):
#     try:
#         latest_email = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, '#jstab0 .zmLUrd'))
#         )
#         subject_line = latest_email.find_element(By.CSS_SELECTOR, '.zmLSu').text.strip()
#         if subject_line in processed_subjects:
#             return False

#         if "Solicitud de Constancia de Semanas Cotizadas del Asegurado" not in subject_line:
#             return False

#         logger.info(f"📨 New Matching Email: {subject_line}")
#         processed_subjects.add(subject_line)
#         latest_email.click()

#         WebDriverWait(driver, 30).until(
#             EC.invisibility_of_element_located((By.CSS_SELECTOR, '[role="progressbar"]'))
#         )
#         time.sleep(2)

#         to_email = driver.find_elements(By.CSS_SELECTOR, '.zmMHdrAddMail')[-1].text
#         curp = to_email.split('@')[0].split('_')[0].upper()
#         logger.info(f"📧 To: {to_email} | CURP: {curp}")

#         for link in driver.find_elements(By.CSS_SELECTOR, '.zmMailWrapper a'):
#             if 'Solicitud de Constancia de Semanas Cotizadas del Asegurado' in link.text:
#                 temp_pdf = os.path.join("reporteSemanasCotizadas.pdf")
#                 final_pdf = os.path.join(pdf_folder, f"{curp}.pdf")

#                 if os.path.exists(final_pdf):
#                     logger.info(f"⏩ Already exists: {final_pdf}")
#                     break

#                 if os.path.exists(temp_pdf):
#                     os.remove(temp_pdf)

#                 # Close extra tabs
#                 while len(driver.window_handles) > 1:
#                     driver.switch_to.window(driver.window_handles[-1])
#                     driver.close()
#                 driver.switch_to.window(driver.window_handles[0])

#                 link.click()

#                 for _ in range(15):
#                     if os.path.exists(temp_pdf):
#                         os.rename(temp_pdf, final_pdf)
#                         logger.info(f"✅ PDF saved as: {final_pdf}")
#                         break
#                     time.sleep(2)
#                 break

#         # Go back to inbox
#         driver.get("https://mail.zoho.com/zm/#mail/inbox")
#         WebDriverWait(driver, 30).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, '#jstab0 .zmLUrd'))
#         )
#         return True

#     except Exception as e:
#         logger.warning(f"❌ Error while processing email: {e}")
#         return False


# def run_scraper_forever():
#     while True:
#         try:
#             logger.info("🚀 Starting new Chrome session")
#             driver = create_driver()
#             driver.get("https://mail.zoho.com/zm/#mail/inbox")

#             login_if_required(driver)
#             WebDriverWait(driver, 60).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '#ms_load')))
#             logger.info("✅ Inbox loaded. Monitoring...")

#             while True:
#                 driver.refresh()
#                 time.sleep(5)
#                 processed = process_latest_email(driver)
#                 if not processed:
#                     logger.info("🔄 No new matching email. Waiting...")
#                 time.sleep(10)

#         except Exception as e:
#             logger.error(f"💥 Critical Error: {e}")
#             try:
#                 driver.quit()
#             except:
#                 pass
#             logger.info("♻️ Restarting in 5 seconds...")
#             time.sleep(5)


# if __name__ == "__main__":
#     run_scraper_forever()
