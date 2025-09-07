import random
from datetime import datetime, timedelta
from faker import Faker
#from mailTrapServer import create_inbox, get_inbox_messages, get_email_attachment, delete_inbox
import asyncio
from bs4 import BeautifulSoup
import aiohttp
import time
import pdfplumber
from io import BytesIO
from base64 import b64decode, b64encode 
import traceback
from ReadPDF import leyendopdf
import json 
from unidecode import unidecode
from flask import Flask, request, jsonify
from logger import logger
from utils.mongoLogger import MongoLogger, updateRW
import subprocess
import re
import uuid
from mailTm import (
    
    create_inbox,
    get_token,
    get_inbox_messages,
    wait_for_email,
    get_email_attachment,
    #delete_session
)
mongo_logger = MongoLogger()

fake = Faker("es_MX")

memory = {
    "df_locks": {},       # Per-device lock
    "task_tracker": {},    # Tracks if device is currently busy (optional but useful) 
    "last_used_index": 0
}

def get_connected_devices():
    try:
        output = subprocess.check_output(["adb", "devices"], stderr=subprocess.DEVNULL)
        lines = output.decode().strip().split('\n')[1:]  # Skip the first line
        devices = []
        for line in lines:
            parts = line.strip().split('\t')
            if len(parts) == 2 and parts[1] == 'device':
                devices.append(parts[0])  # e.g., 'emulator-5554'
        return devices
    except Exception as e:
        print(f"Error fetching devices: {e}")
        return []
    
connected_devices = get_connected_devices()
# connected_devices = ["RFCY202HHYB"]
print(f"Connected devices: {connected_devices}")

# DFL 11 - RFCY200LWYX     device
# DFL 10 - RFCY2019RXP     device
# DFL 9  - RFCY202HNHJ     device

def getLink(html):
    if html:
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a")

        if not links or len(links) < 2:
            return None

        link = links[1].get("href")
        if not link:
            return None

        # Clean up the link by removing or updating query parameters
        link = (
            link.replace("detalle=true", "detalle=detalle")
                .replace("detalle=false", "detalle=detalle")
                .replace("&origen=MOVILES", "")
                .replace("origen=MOVILES&", "")
        )

        if "detalle=detalle" not in link:
            if "?" in link:
                link += "&detalle=detalle"
            else:
                link += "?detalle=detalle"

        return link

    return None

from base64 import b64encode
import traceback

async def getPdfFromLastMail_TM(curp, process_id, session, timeout=900):
    logger.info("Started checking Mail.tm inbox for PDF", extra={"curp": curp})
    start_time = time.time()

    async with aiohttp.ClientSession() as aio_session:
        while (time.time() - start_time) < timeout:
            try:
                msgs = await get_inbox_messages(session)
                logger.info(f"Fetched {len(msgs)} message(s) from Mail.tm", extra={"curp": curp})

                for msg in (msgs if isinstance(msgs, list) else []):
                    try:
                        message_id = msg["id"]
                        msg_data = await get_email_attachment(session, curp, message_id)
                        subject = msg.get("subject", "")

                        logger.info(f"Checking subject: {subject}", extra={"curp": curp})

                        # ✅ Case 1: Direct PDF attachment
                        if subject == "Constancia de Semanas Cotizadas del Asegurado":
                            if msg_data.get("attachment"):
                                with open(msg_data["attachment"], "rb") as f:
                                    encoded_pdf = b64encode(f.read()).decode("utf-8")

                                logger.info("PDF attachment found and encoded", extra={"curp": curp})
                                mongo_logger.update_log_by_process_id(process_id, "PDF_download_Field_1", True)
                                mongo_logger.update_log_by_process_id(process_id, "PDF_download_Field_2", "PDF saved successfully")
                                return {"data": encoded_pdf, "status": True}

                        # ✅ Case 2: Link-based email
                        if subject == "Servicio Digital: Solicitud de Constancia de Semanas Cotizadas del Asegurado":
                            url = getLink(msg_data.get("html", ""))
                            mongo_logger.update_log_by_process_id(process_id, "Email_Field_1", bool(url))
                            mongo_logger.update_log_by_process_id(process_id, "Email_Field_2", f"Extracted URL: {url}" if url else "URL extraction failed")
                            logger.info(f"Extracted PDF link from email: {url}", extra={"curp": curp})

                            if url:
                                response = await aio_session.post(
                                    "http://127.0.0.1:5000/anydesk/pdfextraction",
                                    json={"curp": curp, "url": url},
                                    timeout=600,
                                    ssl=False
                                )
                                response_json = await response.json()
                                success = response_json.get("status") in ["ok", True]

                                mongo_logger.update_log_by_process_id(
                                    process_id,
                                    "PDF_download_Field_1",
                                    success
                                )
                                mongo_logger.update_log_by_process_id(
                                    process_id,
                                    "PDF_download_Field_2",
                                    "PDF extracted from link" if success else str(response_json)
                                )

                                if success:
                                    logger.info("Successfully extracted PDF via link", extra={"curp": curp})
                                    return response_json
                                else:
                                    logger.error(f"Failed to extract PDF: {response_json}", extra={"curp": curp})

                    except Exception as e_inner:
                        logger.error(f"Error processing individual message: {str(e_inner)}", extra={"curp": curp})
                        logger.error(traceback.format_exc(), extra={"curp": curp})
                        mongo_logger.update_log_by_process_id(process_id, "PDF_download_Field_1", False)
                        mongo_logger.update_log_by_process_id(process_id, "PDF_download_Field_2", f"Exception: {str(e_inner)}")

            except Exception as e:
                logger.error(f"Exception while fetching inbox: {e}", extra={"curp": curp})
                logger.error(traceback.format_exc(), extra={"curp": curp})
                mongo_logger.update_log_by_process_id(process_id, "PDF_download_Field_1", False)
                mongo_logger.update_log_by_process_id(process_id, "PDF_download_Field_2", f"Exception: {str(e)}")

            await asyncio.sleep(10)

    logger.warning("Timeout reached while waiting for PDF in Mail.tm inbox", extra={"curp": curp})
    mongo_logger.update_log_by_process_id(process_id, "PDF_download_Field_1", False)
    mongo_logger.update_log_by_process_id(process_id, "PDF_download_Field_2", "Timeout waiting for PDF")
    return {"data": None, "status": False}


def fix_mojibake(text):
    try:
        return text.encode("cp1252").decode("utf-8")
    except Exception:
        return text
            
def regex_match(text, patterns):
    return any(re.search(p, text) for p in patterns)

def check_and_update_conditions(curp, message):
    """
    Checks the message against known patterns (condition 2 and 4),
    updates Registro_works, and returns True if handled.
    Returns False if no condition matched.
    """
    normalized_out = unidecode(message).strip().lower()
    fixed_out = fix_mojibake(normalized_out)

    condition2_patterns = [
        r"datos.*imss.*curp.*inconsistencia",
        r"acude a tu subdelegacion",
        r"persona no cuenta con nss",
        r"curp proporcionado.*no.*localizado.*renapo",
        r"no se encuentra\s*informaci[oó]n",
         r"no se (localizo|encontr[oó]).*informaci[oó]n.*renapo.*subdelegaci[oó]n"
    ]

    condition4_patterns = [
        r"servicio no se encuentra disponible",
        r"no se puede generar el reporte",
        r"favor de intentar(lo)? mas tarde"
    ]

    if regex_match(fixed_out, condition2_patterns):
        logger.info("Matched known issue pattern — updating Registro_works with condition=2", extra={"curp": curp})
        try:
            updateRW(curp=curp, condition=2, message=message, status="Complete")
        except Exception as e:
            logger.warning(f"Failed to update Registro_works (condition 2): {e}", extra={"curp": curp})
        return True

    elif regex_match(fixed_out, condition4_patterns):
        logger.info("Matched service unavailable pattern — updating Registro_works with condition=4", extra={"curp": curp})
        try:
            updateRW(curp=curp, condition=4, message=message, status="Complete")
        except Exception as e:
            logger.warning(f"Failed to update Registro_works (condition 4): {e}", extra={"curp": curp})
        return True

    return False  # No match found

class IMSSAppScraper:

    async def imssAppAnydesk(self, curp, device_name):
        logger.info("Scraping IMSS App with Android", extra={"curp": curp})
        process_id = mongo_logger.create_log(curp)

        async with aiohttp.ClientSession() as session:
            try:
                email_address, password = await create_inbox(session=session)
                await get_token(session, email_address, password)
            except Exception as e:
                logger.info(f"Failed to create email: {str(e)}", extra={"curp": curp})
                mongo_logger.update_log(process_id, "Email_Creation_1", False)
                mongo_logger.update_log(process_id, "Email_Creation_2", "FAILED TO CREATE EMAIL ON MAIL.TM")
                return {"data": str(e), "status": False}

            mongo_logger.update_log(process_id, "inbox_id", email_address)
            mongo_logger.update_log(process_id, "device_id", device_name)
            logger.info(f"Created and using email: {email_address}", extra={"curp": curp})

            try:
                response = await session.post(
                    "http://127.0.0.1:5000/anydesk/imss",
                    json={
                        "curp": curp,
                        "email": email_address,
                        "deviceName": device_name
                    },
                    headers={"User-Agent": "IMSS_Generator"},
                    timeout=1800,
                    ssl=False
                )
                response_text = await response.text()
                logger.info(f"API Response: {response_text}", extra={"curp": curp})
            except Exception as e:
                logger.error(f"Request failed: {e}", extra={"curp": curp})
                return {"data": str(e), "status": False}

            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON from IMSS APP: {str(e)}"
                logger.error(error_msg, extra={"curp": curp})
                mongo_logger.update_log(process_id, "App_request_Field_1", False)
                mongo_logger.update_log(process_id, "App_request_Field_2", response_text[:500])
                try:
                    updateRW(curp=curp, condition=4, message=error_msg, status="Complete")
                except Exception as update_err:
                    logger.warning(f"Registro_works update failed: {update_err}", extra={"curp": curp})
                return {"data": error_msg, "status": False}

            status = response_json.get("status", False)
            out = response_json.get("data", "")
            mongo_logger.update_log(process_id, "App_request_Field_1", status)
            mongo_logger.update_log(process_id, "App_request_Field_2", out)

            handled_condition = check_and_update_conditions(curp, out)

            if not status:
                logger.info(f"IMSS API returned failure - {out}", extra={"curp": curp})
                if not handled_condition:
                    try:
                        logger.info("No known error matched. Defaulting to condition 4.", extra={"curp": curp})
                        updateRW(curp=curp, condition=4, message=out, status="Complete")
                    except Exception as e:
                        logger.warning(f"updateRW failed: {e}", extra={"curp": curp})
                return {"data": out, "status": False}

            expected_msg = "Para continuar con su trámite le hemos enviado una liga de confirmación a su correo electrónico"
            if unidecode(out).strip().lower() == unidecode(expected_msg).strip().lower():
                logger.info("Expected confirmation message received, fetching PDF", extra={"curp": curp})
                data = await getPdfFromLastMail_TM(curp, process_id=process_id, session=session)
                logger.info("Mail.tm inbox processed", extra={"curp": curp})
                return data

            logger.info("No PDF expected, returning API response", extra={"curp": curp})
            return response_json


def initialize_device_locks():
    connected_devices = get_connected_devices()
    for device in connected_devices:
        if device not in memory["df_locks"]:
            memory["df_locks"][device] = asyncio.Lock()
            memory["task_tracker"][device] = False  # Initially all are free

initialize_device_locks()

app = Flask(__name__)
scraper = IMSSAppScraper()


@app.route("/imss/anydesk/dfl", methods=["POST"])
async def run_imss_anydesk():
    data = request.get_json()
    curp = data.get("curp")

    if not curp:
        logger.error("Missing 'curp' in request body", extra={"curp": "N/A"})
        return jsonify({"error": "Missing 'curp' in request body"}), 400

    device_names = list(memory["df_locks"].keys())
    num_devices = len(device_names)

    # Try devices starting from last used (round-robin)
    for i in range(num_devices):
        index = (memory["last_used_index"] + i) % num_devices
        device_name = device_names[index]
        lock = memory["df_locks"][device_name]

        if not lock.locked():
            memory["last_used_index"] = (index + 1) % num_devices  # Move to next for next time
            async with lock:
                try:
                    memory["task_tracker"][device_name] = True
                    result = await scraper.imssAppAnydesk(curp, device_name)
                    memory["task_tracker"][device_name] = False
                    return jsonify(result)
                except Exception as e:
                    memory["task_tracker"][device_name] = False
                    return jsonify({"error": str(e)}), 500

    return jsonify({
        "error": "All devices are currently busy. Please try again later.",
        "status": 429
    }), 429

if __name__ == "__main__":
    app.run(debug=True, port=3000)