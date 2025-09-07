import unicodedata
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.options.android import UiAutomator2Options
from flask import Flask, request, jsonify
import traceback
import threading
import logging
import time
import subprocess
import random
from time import sleep
import os
from datetime import datetime
import requests
import base64
import json
import email
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from logger import logger

# logging.basicConfig(
#     level=logging.INFO,
#     format="[%(asctime)s] [%(name)s] [%(levelname)s] > %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     force=True,
# )
# logger = logging.getLogger(__name__)

app = Flask(__name__)

# ec2s = [
#     "RFCY202HNHJ"
# ]
# locks = [threading.Lock() for _ in range(len(ec2s))]
def handle_common_popup(driver, logger, context=""):
    """
    Handles a generic popup with message and 'ACEPTAR' button.
    Returns:
        None if no popup
        dict with {"data": message, "status": True/False}
    """
    try:
        popup_text_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("android:id/message")')
            )
        )
        popup_text = popup_text_element.get_attribute("text").strip()

        # Normalize the popup text to handle encoding issues
        normalized_text = unicodedata.normalize("NFKD", popup_text).lower()

        # List of known problematic substrings
        problematic_phrases = [
            "los datos registrados en el imss asociados a la curp presentan inconsistencias",
            "los datos registrados en el imss asociados a la curp, presentan alguna inconsistencia",
        ]

        aceptar_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("android:id/button2")')
            )
        )
        aceptar_button.click()

        # Check if the popup matches any known problematic case
        for phrase in problematic_phrases:
            if phrase in normalized_text:
                return {"data": popup_text, "status": True}

        return {"data": popup_text, "status": False}

    except TimeoutException:
        return None
       
def run_adb(*args):
    try:
        subprocess.run(["adb"] + list(args), check=True)
    except subprocess.CalledProcessError as e:
        logger.warning(f"ADB command failed: {' '.join(args)} | {e}")

# def pdfExtractionScraper(curp, url):
#     for i in range(6):
#         try:
#             logger.info(f"Attempt {i+1} to fetch PDF from: {url}", extra={"curp": curp})
#             response = requests.get(
#                 url,
#                proxies={
#                      "http" : "http://SProxy01:3w+rW0wSfQ8Tnrf8xd@mx.smartproxy.com:20000",
#                     "https" : "http://SProxy01:3w+rW0wSfQ8Tnrf8xd@mx.smartproxy.com:20000"
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

def pdfExtractionScraper(curp, url):
    last_error = None  # To capture the last error or response message

    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-MX,es-US;q=0.9,es;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://serviciosdigitales.imss.gob.mx/'
    }

    for i in range(6):
        try:
            logger.info(f"Attempt {i+1} to fetch PDF from: {url}", extra={"curp": curp})
            response = requests.get(
                url,
                headers=headers,
                proxies={

                    #new SP proxies
                    # "http": "http://spvyia7kot:i5Wyt0eRtgW=6pX4as@mx.smartproxy.com:20000",
                    # "https": "http://spvyia7kot:i5Wyt0eRtgW=6pX4as@mx.smartproxy.com:20000"
                    


                    #old sp proxies
                    "http" : "http://SProxy01:3w+rW0wSfQ8Tnrf8xd@mx.smartproxy.com:20000",
                    "https" : "http://SProxy01:3w+rW0wSfQ8Tnrf8xd@mx.smartproxy.com:20000"

                    # "http": "http://mngesieu-MX-rotate:2npHQ41kMZpm@p.webshare.io:80",
                    # "https": "http://mngesieu-MX-rotate:2npHQ41kMZpm@p.webshare.io:80"

                    # "http": "http://mngesieu-rotate:2npHQ41kMZpm@p.webshare.io:80",
                    # "https": "http://mngesieu-rotate:2npHQ41kMZpm@p.webshare.io:80"
                    
                    

                    #  "http":"http://knuqwqhhqqq-rotate:56u8953h76l11235@p.webshare.io:80",
                    # "https":"https://knuqwqhhqqq-rotate:56u8953h76l11235@p.webshare.io:80"


                    # #"http": "http://SProxy01:69+axtKowN5Ut2qphI@mx.smartproxy.com:20000",
                    # #"https": "http://SProxy01:69+axtKowN5Ut2qphI@mx.smartproxy.com:20000"
                },
                timeout=30
            )

            if response.status_code == 200:
                pdf_bytes = response.content
                if b'PDF' in pdf_bytes:
                    os.makedirs("pdf", exist_ok=True)
                    file_path = f"pdf/{curp}.pdf"
                    with open(file_path, "wb") as f:
                        f.write(pdf_bytes)
                    logger.info(f"PDF saved successfully as: {file_path}", extra={"curp": curp})
                    return {
                        "status": True,
                        "data": base64.b64encode(pdf_bytes).decode("utf-8"),
                    }
                else:
                    last_error = "Response is 200 but content is not a valid PDF"
                    logger.warning(last_error, extra={"curp": curp})
            else:
                last_error = f"Non-200 response: {response.status_code}"
                logger.warning(last_error, extra={"curp": curp})

        except Exception as e:
            last_error = f"Exception: {str(e)}"
            logger.error(last_error, extra={"curp": curp})

        time.sleep(5)  # Delay before retry

    # All attempts failed
    return {
        "status": False,
        "error": last_error or "Unknown error"
    }

def imssScraper(options, curp, email):
    logger.info(f"Starting IMSS App scraping using anydesk | CURP: {curp} | Email: {email}", extra={"curp": curp})
    st = time.time()

    run_adb("-s", options.device_name, "shell", "pm", "clear", "st.android.imsspublico")
    run_adb("-s", options.device_name, "shell", "am", "force-stop", "st.android.imsspublico")
    # run_adb("-s", options.device_name, "shell", "settings", "put", "global", "http_proxy", "p.webshare.io:9999")

    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

    out = None
    status = False
    
    try:
        driver.execute_script("mobile: shell", { "command": "pm", "args": ["grant", "st.android.imsspublico", "android.permission.ACTIVITY_RECOGNITION"] })
        driver.execute_script("mobile: shell", { "command": "pm", "args": ["grant", "st.android.imsspublico", "android.permission.READ_EXTERNAL_STORAGE"] })
        time.sleep(5)

        # #original one
        # logger.info("Scrolling to 'Constancia de semanas cotizadas'", extra={"curp": curp})
        # driver.find_element(
        #     AppiumBy.ANDROID_UIAUTOMATOR,
        #     'new UiScrollable(new UiSelector().scrollable(true).instance(0))'
        #     '.scrollIntoView(new UiSelector().text("Constancia de semanas cotizadas").instance(0));'
        # ).click()
        
        for retry_attempt in range(3):
            try:
                logger.info(f"Scrolling to 'Constancia de semanas cotizadas' (attempt {retry_attempt + 1})", extra={"curp": curp})
                driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiScrollable(new UiSelector().scrollable(true).instance(0))'
                    '.scrollIntoView(new UiSelector().text("Constancia de semanas cotizadas").instance(0));'
                ).click()
                logger.info("Successfully clicked on 'Constancia de semanas cotizadas'", extra={"curp": curp})
                break
            except Exception as e:
                logger.warning(f"Attempt {retry_attempt + 1} failed: {str(e)}", extra={"curp": curp})
                if retry_attempt == 2:  # Last attempt failed
                    logger.error("All retry attempts failed for 'Constancia de semanas cotizadas'", extra={"curp": curp})
                    return {"data": "Could not find 'Constancia de semanas cotizadas' element", "status": False}
                time.sleep(2)  # Wait before next retry
        

        time.sleep(random.randint(1000, 5000) / 1000)
        logger.info(f"Entering CURP: {curp}", extra={"curp": curp})
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Ingresa CURP")'))
        ).send_keys(curp)
        time.sleep(random.randint(1000, 5000) / 1000)
        logger.info(f"Entering Email: {email}", extra={"curp": curp})
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Correo electrónico")'))
        ).send_keys(email)
        time.sleep(random.randint(1000, 5000) / 1000)
        logger.info("Clicking on 'INICIAR SESIÓN'", extra={"curp": curp})
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("INICIAR SESIÓN")'))
        ).click()
        popup_result = handle_common_popup(driver, logger, context="after login")
        if popup_result:
            logger.warning(f"Popup after login: {popup_result['data']}", extra={"curp": curp})
            return popup_result
        
        time.sleep(random.randint(1000, 5000) / 1000)
        WebDriverWait(driver, 120).until(
            EC.invisibility_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Esta consulta puede demorar algunos segundos.")'))
        )
        time.sleep(random.randint(1000, 5000) / 1000)
        if "subdelegaci" in driver.page_source.lower():
            logger.info("CURP inconsistency message found", extra={"curp": curp})
            out = "ï¿½Los datos registrados en el IMSS asociados a la CURP, presentan alguna inconsistencia, por favor acude a tu Subdelegaciï¿½n para obtener tu Nï¿½mero de Seguridad Social; presentando: CURP, Acta de Nacimiento e Identificaciï¿½n Oficial."
            status = True
        else:
            logger.info("Clicking 'CONTINUAR' before captcha", extra={"curp": curp})
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("CONTINUAR")'))
            ).click()
            time.sleep(random.randint(1000, 5000) / 1000)
            logger.info("Clicking checkbox", extra={"curp": curp})
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.CheckBox")'))
            ).click()
            for i in range(5):
                captcha_text_view_xpath = "//android.view.ViewGroup[@index='7']/android.widget.TextView[@index='0']"
                logger.info(f"Captcha attempt {i+1}", extra={"curp": curp})
                time.sleep(random.randint(1000, 5000) / 1000)
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText")'))
                ).clear()
                time.sleep(random.randint(1000, 5000) / 1000)
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText")'))
                ).send_keys(
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((AppiumBy.XPATH, captcha_text_view_xpath))
                    ).get_attribute("text")
                )
                #logger.info(f"Captcha text: {captcha_text}", extra={"curp": curp})
                time.sleep(random.randint(1000, 5000) / 1000)
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("CONTINUAR")'))
                ).click()
                time.sleep(random.randint(1000, 5000) / 1000)
                WebDriverWait(driver, 120).until(
                    EC.invisibility_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.ProgressBar")'))
                )
                time.sleep(random.randint(1000, 5000) / 1000)
                
                if "subdelegaci" in driver.page_source.lower():
                    out = "ï¿½Los datos registrados en el IMSS asociados a la CURP, presentan alguna inconsistencia, por favor acude a tu Subdelegaciï¿½n para obtener tu Nï¿½mero de Seguridad Social; presentando: CURP, Acta de Nacimiento e Identificaciï¿½n Oficial."
                    status = True
                    logger.warning(f"Inconsistency after captcha: {out}", extra={"curp": curp})
                    break
                elif "servicio no se encuentra disponible" in driver.page_source.lower():
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("ACEPTAR")'))
                    ).click()
                    out = "El servicio no se encuentra disponible, favor de intentar más tarde."
                    status = False
                    logger.warning(f"Service not available: {out}", extra={"curp": curp})
                    
                elif "el momento no se puede generar el reporte" in driver.page_source.lower():
                    logger.warning("Report generation unavailable", extra={"curp": curp})
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("ACEPTAR")'))
                    ).click()
                    out = "Por el momento no se puede generar el reporte, favor de intentarlo más tarde."
                    status = False
                    logger.warning(f"Report generation unavailable: {out}", extra={"curp": curp})
                elif "full authentication is required to access this resource" in driver.page_source.lower():
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("ACEPTAR")'))
                    ).click()
                    out = "No autorizado: se requiere autenticación completa para acceder a este recurso."
                    status = False
                    logger.warning(f"Full authentication required on the inbox : {out}", extra={"curp": curp})
                
                else:
                    try:
                        WebDriverWait(driver, 90).until(
                            EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("CONTINUAR")'))
                        ).click()
                        out = "Para continuar con su trámite le hemos enviado una liga de confirmación a su correo electrónico"
                        status = True
                        logger.info(f"Success: {out}", extra={"curp": curp})
                        break
                    except TimeoutException:
                        logger.warning("CONTINUAR button not found in time — checking for popup", extra={"curp": curp})
                        popup_result = handle_common_popup(driver, logger, context="post-captcha-final")
                        if popup_result:
                            out = popup_result["data"]
                            status = popup_result["status"]
                            logger.warning(f"Handled popup instead of CONTINUAR: {out}", extra={"curp": curp})
                        else:
                            out = "Timeout waiting for final CONTINUAR button and no popup appeared"
                            status = False
                            logger.error(out, extra={"curp": curp})
                        break
                
                # else:
                #     WebDriverWait(driver, 60).until(
                #         EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("CONTINUAR")'))
                #     ).click()
                #     out = "Para continuar con su trámite le hemos enviado una liga de confirmación a su correo electrónico"
                #     status = True
                #     logger.info(f"Success: {out}", extra={"curp": curp})
                #     break
    except Exception as e:
        logger.error(f"Error during scraping: {e}", extra={"curp": curp})
        logger.error(traceback.format_exc(), extra={"curp": curp})
        out = traceback.format_exc()
    finally:
        driver.quit()
        logger.info("Driver quit", extra={"curp": curp})
    
    logger.info("Execution time: %.2f seconds", time.time() - st, extra={"curp": curp})
    return {"data": out, "status": status}

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": True, "message": "Server is running"})


@app.route("/anydesk/pdfextraction", methods=["POST"])
def scrape_pdflink():
    data = request.get_json()
    curp = data.get("curp")
    url = data.get("url")
    
    out = pdfExtractionScraper(curp, url)
    # put_json_to_s3(f"{curp}.json", json.dumps(out))
    return jsonify(out)


@app.route("/anydesk/imss", methods=["POST"])
def scrape_imss():
    data = request.get_json()
    device_name = data.get("deviceName")  # ✅ New dynamic key
    curp = data.get("curp")
    email = data.get("email")

    logger.info(f"curp: {curp}; email: {email}; device: {device_name}", extra={"curp": curp})

    if not curp or not email or not device_name:
        return jsonify({"status": False, "message": "CURP, email, and deviceName are required"}), 400

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.platform_version = "14.0"
    options.udid = device_name
    options.device_name = device_name
    options.app_package = "st.android.imsspublico"
    options.app_activity = "crc642176304cdb761b92.Splash"
    options.automation_name = "UiAutomator2"
    options.auto_grant_permissions = True
    options.uiautomator2_server_launch_timeout = 300000
    options.adb_exec_timeout = 300000
    options.skip_device_initialization = True
    options.skip_server_installation = True

    # You may optionally use threading.Lock per-device here if needed,
    # but it's already managed by the asyncio.Lock upstream.

    result = imssScraper(options, curp, email)

    return jsonify(result)




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
