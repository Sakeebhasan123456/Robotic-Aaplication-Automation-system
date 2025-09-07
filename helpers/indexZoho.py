import random
from datetime import datetime, timedelta
from faker import Faker
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
from base64 import b64encode
import traceback

mongo_logger = MongoLogger()

fake = Faker("es_MX")

memory = {
    "df_locks": {},       # Per-device lock
    "task_tracker": {},    # Tracks if device is currently busy (optional but useful) 
    "last_used_index": 0
}

DOMAINS = [
    "notaria238cdmx.mx",
    # "notaria103.com",
    # "notaria110edomex.com",
    # "notaria117edomex.com.mx",
    # "notaria218.com.mx",
    # "notaria2cdmx.mx",
    # "notaria42mx.com.mx",
    # "notaria46cdmx.mx",
    # "notaria67toluca.com.mx",
    # "notaria80edomex.com",
    # "notariacdmx5.com.mx",
    # "notariaedomex123.com",
    # "notariaedomex141.com",
    # "notariaedomex144.com",
    # "notariaedomex17.com",
    # "notariaedomex19.com.mx"
   
]

def create_email(curp):
    random_number = random.randint(10000, 99999)
    username = f"{curp}{random_number}".lower()
    domain = random.choice(DOMAINS)
    return f"{username}@{domain}"

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

    async def imssAppAnydeskZoho(self, curp, device_name):

        logger.info("Scraping IMSS App with Android", extra={"curp": curp})
        process_id = mongo_logger.create_log(curp)
        
        email = create_email(curp)  #need to implement this function
        mongo_logger.update_log(process_id, "Zoho_email", email)

        async with aiohttp.ClientSession() as session:
            try:
                response = await session.post(
                    "http://127.0.0.1:5000/anydesk/imss",
                    json={
                        "curp": curp,
                        "email": email,  # dummy placeholder
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
                updateRW(curp=curp, condition=4, message=str(e), status="Failed")
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

            # --- Normalize & Check
            normalized_out = unidecode(out).strip().lower()
            fixed_out = fix_mojibake(normalized_out)

            # Patterns
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

            # Condition 2
            if regex_match(fixed_out, condition2_patterns):
                updateRW(curp=curp, condition=2, message=out, status="Complete")
                logger.info("Condition 2 matched and updated", extra={"curp": curp})
                return {"data": out, "status": True}

            # Condition 4
            if regex_match(fixed_out, condition4_patterns) or not status:
                updateRW(curp=curp, condition=4, message=out, status="Complete")
                logger.info("Condition 4 matched or API failure", extra={"curp": curp})
                return {"data": out, "status": False}

            # Expected Success
            expected_msg = "Para continuar con su trámite le hemos enviado una liga de confirmación a su correo electrónico"
            if normalized_out == unidecode(expected_msg).strip().lower():
                logger.info("Expected confirmation message received", extra={"curp": curp})
                return {"data": out, "status": True}

            # Default fallback
            logger.info("No condition matched, returning raw response", extra={"curp": curp})
            return {"data": out, "status": status}



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
    
# @app.route("/imss/anydesk/dfl/2.0", methods=["POST"])
# async def run_imss_anydesk():
#     data = request.get_json()
#     nbc_id = data.get("id")  # expecting MongoDB ObjectId

#     if not nbc_id:
#         logger.error("Missing 'id' in request body", extra={"id": "N/A"})
#         return jsonify({"error": "Missing 'id' in request body"}), 400

#     try:
#         # Extract CURP, RW ID, and Email
#         curp = getCurp(nbc_id)
#         rw_id = getRwID(nbc_id)
#        missing_fields = []
#         if not curp:
#             missing_fields.append("curp")
#         if not rw_id:
#             missing_fields.append("rw_id")
#         if missing_fields:
#             logger.warning(f"Missing required fields for nbc_id: {', '.join(missing_fields)}",extra={"nbc_id": nbc_id})
#             return jsonify({
#                 "message": f"Invalid nbc_id: missing {', '.join(missing_fields)}",
#                 "status": "error"
#             }), 400

#     except Exception as e:
#         logger.exception("Failed to parse or fetch data from MongoDB", extra={"nbc_id": nbc_id})
#         return jsonify({"message": str(e), "status": "error"}), 500

#     device_names = list(memory["df_locks"].keys())
#     num_devices = len(device_names)

#     # Try devices starting from last used (round-robin)
#     for i in range(num_devices):
#         index = (memory["last_used_index"] + i) % num_devices
#         device_name = device_names[index]
#         lock = memory["df_locks"][device_name]

#         if not lock.locked():
#             memory["last_used_index"] = (index + 1) % num_devices  # Move to next for next time
#             async with lock:
#                 try:
#                     memory["task_tracker"][device_name] = True
#                     result = await scraper.imssAppAnydeskZoho(curp, rw_id, device_name)
#                     memory["task_tracker"][device_name] = False
#                     return jsonify(result)
#                 except Exception as e:
#                     memory["task_tracker"][device_name] = False
#                     return jsonify({"error": str(e)}), 500

#     return jsonify({
#         "error": "All devices are currently busy. Please try again later.",
#         "status": 429
#     }), 429

if __name__ == "__main__":
    app.run(debug=True, port=3000)