import threading
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
from scraperOutlookApp import automate_outlook_create_account
from collections import defaultdict
import concurrent.futures
from outlookAppPdfExtractor import pdf_extraction_using_outlook_app
from deviceManager import normal_reset_mobile_data, reset_mobile_data, get_device_ip
from getPdf import pull_pdf_from_device, delete_downloaded_pdfs
from openPdfInChrome import openPdfInChrome
from pdfExtractionSecondEmail import pdf_extraction_from_second_email

# ✅ ADD: MongoDB imports for device management
from pymongo import MongoClient

import os
mongo_logger = MongoLogger()

fake = Faker("es_MX")

# ✅ ADD: Background task processing system
task_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10, thread_name_prefix="IAD-BG")

# ✅ ADD: Processing state management
class IADProcessingState:
    def __init__(self):
        self._processing_tasks = {}
        self._lock = threading.Lock()
    
    def add_task(self, task_id: str, curp: str, device_id: str):
        with self._lock:
            self._processing_tasks[task_id] = {
                "curp": curp,
                "device_id": device_id,
                "start_time": time.time(),
                "status": "processing"
            }
            
    def complete_task(self, task_id: str):
        with self._lock:
            if task_id in self._processing_tasks:
                del self._processing_tasks[task_id]
                
    def get_active_tasks(self):
        with self._lock:
            return self._processing_tasks.copy()

# Initialize processing state
iad_processing_state = IADProcessingState()

# ✅ REMOVED: DeviceLockManager class - Using MongoDB-only approach like iwd.py

# ✅ SIMPLIFIED: Background processing function following iwd.py approach
def process_imss_app_background(curp: str, device_id: str, taskid: str, queue_document_id: str):
    """
    Background processing function that runs the actual IMSS app scraping
    SIMPLIFIED: Using MongoDB-only device management like iwd.py
    """
    task_id = f"{taskid}_{curp}_{int(time.time())}"
    
    try:
        logger.info(f"🚀 [IAD-BG-START] CURP: {curp} | Device: {device_id} | Task: {taskid} | Queue: {queue_document_id}")
        
        # Add to processing state
        iad_processing_state.add_task(task_id, curp, device_id)
        
        # ✅ SIMPLIFIED: No internal device locks - MongoDB handles it all
        logger.info(f"📝 [IAD-BG] Device {device_id} already assigned in MongoDB for task {taskid}")
        
        # Use the global scraper instance
        global scraper
        
        # Run scraper in synchronous mode
        def run_scraper_sync():
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    logger.info(f"🎬 [IAD-BG-SCRAPER] Starting scraper for CURP: {curp} on device: {device_id}")
                    
                    # ✅ FIXED: Pass queue_document_id to scraper
                    result = loop.run_until_complete(
                        scraper.imssScraperOutlook(curp, device_id, queue_document_id)
                    )
                    
                    logger.info(f"🎯 [IAD-BG-SCRAPER] Scraper completed for CURP: {curp}")
                    logger.info(f"📊 [IAD-BG-SCRAPER] Result: {result}")
                    return result
                    
                except Exception as scraper_error:
                    logger.error(f"❌ [IAD-BG-SCRAPER-ERROR] CURP: {curp}: {str(scraper_error)}")
                    traceback.print_exc()
                    
                    # Update RW with scraper error
                    try:
                        updateRW(curp=curp, condition=4, message=f"Scraper error: {str(scraper_error)}", status="Complete", queue_document_id=queue_document_id)
                        logger.info(f"📝 [IAD-BG-SCRAPER] Updated RW with condition=4 for scraper error: {curp}")
                    except Exception as rw_error:
                        logger.error(f"❌ Failed to update RW for scraper error: {rw_error}")
                    
                    return {"status": False, "data": str(scraper_error)}
                    
                finally:
                    try:
                        loop.close()
                        logger.debug(f"🔄 [IAD-BG-SCRAPER] Event loop closed for CURP: {curp}")
                    except Exception as loop_error:
                        logger.warning(f"⚠️ Error closing event loop: {loop_error}")
                        
            except Exception as thread_error:
                logger.error(f"❌ [IAD-BG-THREAD-ERROR] CURP: {curp}: {str(thread_error)}")
                traceback.print_exc()
                
                # Update RW with thread error
                try:
                    updateRW(curp=curp, condition=4, message=f"Thread error: {str(thread_error)}", status="Complete", queue_document_id=queue_document_id)
                    logger.info(f"📝 [IAD-BG-THREAD] Updated RW with condition=4 for thread error: {curp}")
                except Exception as rw_error:
                    logger.error(f"❌ Failed to update RW for thread error: {rw_error}")
                
                return {"status": False, "data": str(thread_error)}
        
        # Execute the scraper
        logger.info(f"⚡ [IAD-BG-EXEC] Executing scraper for CURP: {curp}")
        result = run_scraper_sync()
        
        # Log final result
        if result and result.get("status"):
            logger.info(f"✅ [IAD-BG-SUCCESS] CURP: {curp} completed successfully")
        else:
            error_msg = result.get("data", "Unknown error") if result else "No result returned"
            logger.warning(f"⚠️ [IAD-BG-WARNING] CURP: {curp} completed with issues: {error_msg}")
            
    except Exception as e:
        logger.error(f"❌ [IAD-BG-ERROR] CURP: {curp}, Device: {device_id}: {str(e)}")
        traceback.print_exc()
        
        # Update RW with failure
        try:
            updateRW(curp=curp, condition=4, message=f"Background processing error: {str(e)}", status="Complete", queue_document_id=queue_document_id)
            logger.info(f"📝 [IAD-BG-GENERAL] Updated RW with condition=4 for background error: {curp}")
        except Exception as rw_error:
            logger.error(f"❌ Failed to update RW for background error: {rw_error}")
            
    finally:
        # Clean up processing state
        iad_processing_state.complete_task(task_id)
        
        # ✅ SIMPLIFIED: Only release MongoDB device (following iwd.py pattern)
        try:
            release_device(device_id, taskid)
            logger.info(f"🔓 [IAD-BG-CLEANUP] MongoDB device {device_id} released after background task {taskid}")
        except Exception as release_error:
            logger.error(f"❌ [IAD-BG-CLEANUP] Error releasing MongoDB device {device_id}: {release_error}")

# Globals
connected_devices = []
lock = threading.Lock()

JSON_FILE = "connected_devices.json"

# ✅ ADD: MongoDB connection for device management (same as iwd.py approach)
MONGO_PRINCIPAL = 'mongodb://carlos_readonly:p13CCTjtXUaqf1xQyyR6KpuRtYzrsw9R@principal.mongodb.searchlook.mx:27017/admin'

# ✅ SIMPLIFIED: Device management functions following iwd.py approach
def get_devices_collection():
    """Get MongoDB devices collection with error handling"""
    try:
        client = MongoClient(MONGO_PRINCIPAL)
        return client['Mini_Base_Central']['devices']
    except Exception as e:
        logger.error(f"[IAD] Failed to connect to MongoDB: {e}")
        raise
    
def get_device_name(device_id):
    # Mapping of device_id to device_name
    device_map = {
        "RFCY20EL58W": "DFL-4",
        "RFCY2019MPN": "DFL-15",
        "ZE223G283Z": "DFL-25",
        "RFCY20EKZMM": "DFL-3",
        "RFCY20LK9FY": "DFL-17",
        "ZE223G2669": "DFL-18",
        "ZE223G4GQP": "DFL-22",
        "ZE223FTL58": "DFL-23"
    }
    return device_map.get(device_id, device_id)

def register_device_in_mongodb(device_id):
    """Register device in MongoDB with process: IAD"""
    try:
        devices_collection = get_devices_collection()
        device_doc = {
            "device": device_id,
            "online": True,
            "available": True,
            "device_name": get_device_name(device_id),
            "process": "IAD",
            "instance":"IAD1",
            "last_heartbeat": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        devices_collection.update_one(
            {"device": device_id},
            {"$set": device_doc},
            upsert=True
        )
        logger.info(f"[IAD] Device registered: {device_id}")
        
    except Exception as e:
        logger.error(f"[IAD] Error registering device {device_id}: {e}")



def release_device(device_id, taskid):
    """Release device and clear task info (same as iwd.py)"""
    try:
        devices_collection = get_devices_collection()
        result = devices_collection.update_one(
            {"device": device_id, "process": "IAD"},
            {
                "$set": {"available": True, "online": True, "updated_at": datetime.now()},
                "$unset": {"current_task": "", "task_id": "", "task_start_time": ""}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ [IAD] Device {device_id} released for task {taskid}")
        else:
            logger.warning(f"⚠️ [IAD] Could not release device {device_id} for task {taskid}")
            
    except Exception as e:
        logger.error(f"❌ [IAD] Error releasing device {device_id}: {e}")

def update_device_heartbeat(device_id):
    """Update device heartbeat"""
    try:
        devices_collection = get_devices_collection()
        devices_collection.update_one(
            {"device": device_id, "process": "IAD"},
            {"$set": {
                "last_heartbeat": datetime.now(),
                "online": True,
                "updated_at": datetime.now()
            }}
        )
    except Exception as e:
        logger.error(f"[IAD] Error updating heartbeat for {device_id}: {e}")

def register_all_devices_on_startup():
    """Register all connected Android devices on service startup"""
    try:
        current_devices = get_connected_devices()
        for device_id in current_devices:
            register_device_in_mongodb(device_id)
        
        logger.info(f"[IAD] Registered {len(current_devices)} devices on startup")
        
    except Exception as e:
        logger.error(f"[IAD] Error registering devices on startup: {e}")

def cleanup_offline_devices():
    """Remove devices that have been offline for more than 5 minutes"""
    try:
        devices_collection = get_devices_collection()
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        result = devices_collection.delete_many({
            "process": "IAD",
            "online": False,
            "last_heartbeat": {"$lt": cutoff_time}
        })
        
        if result.deleted_count > 0:
            logger.info(f"[IAD] Cleaned up {result.deleted_count} offline devices")
            
    except Exception as e:
        logger.error(f"[IAD] Error cleaning up offline devices: {e}")

def cleanup_stuck_devices():
    """Clean up devices stuck in processing for too long (like iwd.py)"""
    try:
        devices_collection = get_devices_collection()
        timeout_threshold = datetime.now() - timedelta(minutes=20)
        
        stuck_devices = list(devices_collection.find({
            "process": "IAD",
            "available": False,
            "task_start_time": {"$lt": timeout_threshold}
        }))
        
        for device in stuck_devices:
            device_id = device["device"]
            stuck_taskid = device.get("task_id", "unknown")
            logger.warning(f'🧹 [IAD] Releasing stuck device: {device_id} (task {stuck_taskid})')
            release_device(device_id, stuck_taskid)
            
        if len(stuck_devices) > 0:
            logger.info(f"🧹 [IAD] Cleaned up {len(stuck_devices)} stuck devices")
            
    except Exception as e:
        logger.error(f"[IAD] Error cleaning up stuck devices: {e}")

def start_device_heartbeat_monitoring():
    """Monitor device connectivity and heartbeat every 30 seconds"""
    while True:
        try:
            current_devices = get_connected_devices()
            
            # Update heartbeat for online devices
            for device_id in current_devices:
                update_device_heartbeat(device_id)
            
            # Mark offline devices
            devices_collection = get_devices_collection()
            registered_devices = []
            for doc in devices_collection.find({"process": "IAD"}):
                registered_devices.append(doc['device'])
            
            for device_id in registered_devices:
                if device_id not in current_devices:
                    devices_collection.update_one(
                        {"device": device_id, "process": "IAD"},
                        {"$set": {
                            "online": False,
                            "available": False,
                            "updated_at": datetime.now()
                        }}
                    )
                    logger.info(f"[IAD] Device {device_id} marked offline")
            
            # Clean up offline and stuck devices every 5 minutes
            if datetime.now().minute % 5 == 0:
                cleanup_offline_devices()
                cleanup_stuck_devices()
                    
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"[IAD] Device monitoring error: {e}")
            time.sleep(60)

# ---------------- Device Monitoring Functions (ORIGINAL) ---------------- #

def get_connected_devices():
    try:
        result = subprocess.check_output(["adb", "devices"], encoding="utf-8")
        lines = result.strip().split("\n")[1:]
        devices = [
            line.strip().split()[0]
            for line in lines
            if "device" in line and not ("unauthorized" in line or "offline" in line)
        ]
        return devices
    except subprocess.CalledProcessError as e:
        logger.error(f"[Error] ADB command failed: {e}")
        return []
    
def save_devices(devices):
    with open(JSON_FILE, "w") as f:
        json.dump(devices, f, indent=4)

def load_previous_devices():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    return []

def monitor_devices(interval=5):
    global connected_devices
    previous_devices = []

    while True:
        current_devices = get_connected_devices()

        with lock:
            connected_devices = current_devices.copy()

        if set(current_devices) != set(previous_devices):
            added = list(set(current_devices) - set(previous_devices))
            removed = list(set(previous_devices) - set(current_devices))

            if added:
                logger.info(f"[Monitor] New device(s) connected: {added}")
                # Register new devices in MongoDB
                for device_id in added:
                    register_device_in_mongodb(device_id)
                    
            if removed:
                logger.info(f"[Monitor] Device(s) disconnected: {removed}")

            save_devices(current_devices)
            previous_devices = current_devices

        time.sleep(interval)

def fix_mojibake(text):
    try:
        return text.encode("cp1252").decode("utf-8")
    except Exception:
        return text
            
def regex_match(text, patterns):
    return any(re.search(p, text) for p in patterns)

class IMSSAppScraper:
    curp_counts = {}  # {device_name: count}
    lock = threading.Lock()
    
    # ✅ FIXED: Added queue_document_id parameter
    async def imssScraperOutlook(self, curp, device_name, queue_document_id=None):
        
        logger.info(f"🎬 [IAD-SCRAPER] Starting IMSS App scraping for CURP: {curp} on device: {device_name}")
        process_id = mongo_logger.create_log(curp)
        mongo_logger.update_log(process_id, "device_id", device_name)
        
        # ✅ Log queue_document_id if provided
        if queue_document_id:
            mongo_logger.update_log(process_id, "queue_document_id", queue_document_id)

        with IMSSAppScraper.lock:
            # Increment count for this device
            current_count = IMSSAppScraper.curp_counts.get(device_name, 0) + 1
            IMSSAppScraper.curp_counts[device_name] = current_count

            logger.info(f"📊 [IAD-SCRAPER] CURP count for {device_name}: {current_count}", extra={"curp": curp})

            # If count reaches 5 → reset network
            if current_count >= 4:
                logger.info(f"🔄 [IAD-SCRAPER] Reached 5 CURPs on {device_name}. Resetting mobile data...", extra={"curp": curp})
                reset_mobile_data(device_name)
                IMSSAppScraper.curp_counts[device_name] = 0
                # register device in MongoDB
                # register_device_in_mongodb(device_name)
                time.sleep(6)  # Allow network to stabilize
        
        logger.info(f"⏳ [IAD-SCRAPER] Waiting for network to stabilize (10 seconds)...", extra={"curp": curp})
        time.sleep(10) #wait untill network is idle
        
        # Retry Logic: Attempt to create outlook account up to 2 times
        logger.info(f"📧 [IAD-SCRAPER] Starting Outlook account creation attempts...", extra={"curp": curp})
        account_response = None
        last_outlook_error = None
        for attempt in range(3):
            logger.info(f"🧪 [IAD-SCRAPER] Attempt {attempt + 1}/3 to create Outlook account", extra={"curp": curp})
            try:
                account_response = automate_outlook_create_account(curp, device_name)
                logger.info(f"📝 [IAD-SCRAPER] Outlook creation attempt {attempt + 1} response: {account_response}", extra={"curp": curp})
            except Exception as outlook_error:
                logger.error(f"❌ [IAD-SCRAPER] Exception in Outlook creation attempt {attempt + 1}: {outlook_error}", extra={"curp": curp})
                account_response = {"status": False, "data": str(outlook_error)}
                last_outlook_error = outlook_error
                
            if account_response and account_response.get("status") is True:
                logger.info(f"✅ [IAD-SCRAPER] Outlook account created successfully on attempt {attempt + 1}", extra={"curp": curp})
                break
            logger.warning(f"⚠️ [IAD-SCRAPER] Attempt {attempt + 1} failed to create inbox. Resetting mobile data...", extra={"curp": curp})
            # normal_reset_mobile_data(device_name)
            time.sleep(5)  # Optional backoff between retries

        if not account_response or account_response.get("status") is not True:
            logger.error(f"❌ [IAD-SCRAPER] Failed to create inbox after 3 retries", extra={"curp": curp})
            mongo_logger.update_log(process_id, "Outlook_email", "failes to create inbox")
            mongo_logger.update_log(process_id, "Outlook_error", account_response.get("data", "Unknown error"))
            
            # Update RW once after all attempts failed
            try:
                error_message = f"Error: {account_response.get('data', 'Unknown error')}"
                if account_response and "data" in account_response:
                    error_message = f"Error: {account_response['data']}"
                elif last_outlook_error:
                    error_message = f"Error: {str(last_outlook_error)}"
                else:
                    error_message = "Error: failed to create outlook email"
                    
                updateRW(curp=curp, condition=4, message=error_message, status="Complete", queue_document_id=queue_document_id)
            except Exception as rw_error:
                logger.error(f"❌ Failed to update RW for outlook creation error: {rw_error}")
            updateRW(curp=curp, condition=4, message="failed to create outlook email", status="Complete", queue_document_id=queue_document_id)
            return {"data": "Inbox creation failed", "status": False}

        email = account_response["data"]["email"]
        password = account_response["data"]["password"]

        logger.info(f"✅ [IAD-SCRAPER] Outlook account created: {email}", extra={"curp": curp})
        mongo_logger.update_log(process_id, "Outlook_email", email)
        mongo_logger.update_log(process_id, "Outlook_password", password)
        
        logger.info(f"🌐 [IAD-SCRAPER] Starting IMSS API request...", extra={"curp": curp})

        async with aiohttp.ClientSession() as session:
            try:
                logger.info(f"📡 [IAD-SCRAPER] Sending POST request to IMSS API...", extra={"curp": curp})
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
                logger.info(f"📨 [IAD-SCRAPER] IMSS API Response received (length: {len(response_text)})", extra={"curp": curp})
                logger.debug(f"📄 [IAD-SCRAPER] API Response content: {response_text[:500]}...", extra={"curp": curp})
            except Exception as e:
                logger.error(f"❌ [IAD-SCRAPER] IMSS API Request failed: {e}", extra={"curp": curp})
                updateRW(curp=curp, condition=4, message=str(e), status="Failed", queue_document_id=queue_document_id)
                return {"data": str(e), "status": False}

            try:
                response_json = json.loads(response_text)
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON from IMSS APP: {str(e)}"
                logger.error(error_msg, extra={"curp": curp})
                mongo_logger.update_log(process_id, "App_request_Field_1", False)
                mongo_logger.update_log(process_id, "App_request_Field_2", response_text[:500])
                try:
                    updateRW(curp=curp, condition=4, message=error_msg, status="Complete", queue_document_id=queue_document_id)
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
                r"favor de intentar(lo)? mas tarde",
                r"no corresponde la informacion del dispositivo",
                r"el servicio no se encuentra disponible,? favor de intentar mas tarde"
            ]

            # Condition 2
            if regex_match(fixed_out, condition2_patterns):
                updateRW(curp=curp, condition=2, message=out, status="Complete", queue_document_id=queue_document_id)
                logger.info("Condition 2 matched and updated", extra={"curp": curp})
                return {"data": out, "status": True}

            # Condition 4
            if regex_match(fixed_out, condition4_patterns) or not status:
                updateRW(curp=curp, condition=4, message=out, status="Complete", queue_document_id=queue_document_id)
                logger.info("Condition 4 matched or API failure", extra={"curp": curp})
                return {"data": out, "status": False}
            
            expected_msg = "Para continuar con su trámite le hemos enviado una liga de confirmación a su correo electrónico"
            if normalized_out == unidecode(expected_msg).strip().lower():
                logger.info(f"📩 [IAD-SCRAPER] Expected confirmation message received from IMSS app", extra={"curp": curp})
                logger.info(f"🔄 [IAD-SCRAPER] Starting PDF extraction process...", extra={"curp": curp})
    
                pdf_response = None
                chrome_result = None
                pdf_link = None
                last_pdf_error = None
                for attempt in range(5):
                    logger.info(f"📄 [IAD-SCRAPER] Attempt {attempt + 1}/5 to extract PDF from Outlook app", extra={"curp": curp})
                    try:
                        pdf_response = pdf_extraction_using_outlook_app(device_name, curp)
                        logger.info(f"📝 [IAD-SCRAPER] PDF extraction attempt {attempt + 1} response: {pdf_response}", extra={"curp": curp})
                    except Exception as e:
                        logger.error(f"❌ [IAD-SCRAPER] Exception in outlook attempt {attempt + 1}: {e}", extra={"curp": curp})
                        pdf_response = {"data": str(e), "status": False}
                        last_pdf_error = e

                    if pdf_response and pdf_response.get("status") is True:
                        logger.info(f"✅ [IAD-SCRAPER] PDF extraction successful via outlook app on attempt {attempt + 1}", extra={"curp": curp})
                        pdf_link = pdf_response.get("pdf_link")
                        logger.info(f"🔗 [IAD-SCRAPER] PDF link extracted: {pdf_link}", extra={"curp": curp})
                        break  # ✅ Break immediately on successful extraction
        
                    else:
                        logger.warning(f"⚠️ [IAD-SCRAPER] Outlook app attempt {attempt + 1} failed: {pdf_response.get('data', 'No error data')}", extra={"curp": curp})
                        time.sleep(5)
                mongo_logger.update_log(process_id, "Outlook_first_email_1", pdf_response.get("status", False))
                if pdf_response.get("status"):
                    message = f"Link extracted successfully: {pdf_link}"
                else:
                    message = pdf_response.get("data", "No data")
                    # Update RW once after all PDF extraction attempts failed
                    if last_pdf_error:
                        try:
                            updateRW(curp=curp, condition=4, message=f"Pdf link extraction failed from first email: {str(last_pdf_error)}", status="Complete", queue_document_id=queue_document_id)
                        except Exception as rw_error:
                            logger.error(f"❌ Failed to update RW for outlook PDF link extraction error: {rw_error}")
                mongo_logger.update_log(process_id, "Outlook_first_email_2", message)
                
                # After loop — if we got a valid link, open it in Chrome
                if pdf_link:
                    last_chrome_error = None
                    for chrome_attempt in range(3):  # ✅ Try up to 2 times
                        logger.info(f"🌐 Opening PDF in Chrome (Attempt {chrome_attempt + 1}/2): {pdf_link}", extra={"curp": curp})
                        try:
                            chrome_result = await openPdfInChrome(device_name, url=pdf_link)
                            if chrome_result.get("status"):
                                logger.info(f"✅ Chrome successfully opened and verified PDF", extra={"curp": curp})
                                break  # ✅ Stop retrying if success
                            else:
                                logger.warning(f"⚠️ Chrome failed to open PDF: {chrome_result.get('data')}", extra={"curp": curp})
                        except Exception as e:
                            logger.error(f"❌ Failed to open PDF in Chrome: {e}", extra={"curp": curp})
                            last_chrome_error = e

                        if chrome_attempt < 1:  # only wait before retry if not last attempt
                            logger.info("⏳ Retrying Chrome open after 5 seconds...")
                            await asyncio.sleep(5)
                    
                    # Update RW once after all Chrome attempts failed
                    if last_chrome_error:
                        try:
                            updateRW(curp=curp, condition=4, message=f"failed to open pdf link in chrome after 3 attempts: {str(last_chrome_error)}", status="Complete", queue_document_id=queue_document_id)
                        except Exception as rw_error:
                            logger.error(f"❌ Failed to update RW for Chrome PDF open error: {rw_error}")
                            
                mongo_logger.update_log(process_id, "Url_status_in_Chrome_1", chrome_result.get("status", False))
                mongo_logger.update_log(process_id, "Url_status_in_Chrome_2", chrome_result.get("data", "No data"))

                        
                # After loop — if Chrome succeeded, try pulling the PDF
                pull_result = pull_pdf_from_device(device_name, curp)
                if pull_result.get("status"):
                        logger.info(f"✅ PDF pulled successfully after Chrome view", extra={"curp": curp})
                        mongo_logger.update_log(process_id, "Pdf_pull_after_opening_url_in_chrome_1", pull_result.get("status", False))
                        mongo_logger.update_log(process_id, "Pdf_pull_after_opening_url_in_chrome_2", pull_result.get("data", "No data"))
                        
                        return pull_result  # Return the success response from pull_pdf_from_device
                else:
                    logger.warning(f"⚠️ PDF not found on device after Chrome view: {pull_result.get('data')}", extra={"curp": curp})
                        

                    # Second attempt: directly from second email
                    second_response = {"status": False, "data": "No data"}
                    last_second_email_error = None
                    for attempt in range(5):
                        logger.info(f"📩 Attempt {attempt + 1} to extract PDF from second email", extra={"curp": curp})
                        try:
                            second_response = pdf_extraction_from_second_email(device_name, curp)
                        except Exception as e:
                            logger.error(f"❌ Exception in second email attempt {attempt + 1}: {e}", extra={"curp": curp})
                            second_response = {"data": str(e), "status": False}
                            last_second_email_error = e

                        if second_response and second_response.get("status") is True:
                            logger.info("✅ PDF extraction successful via second email", extra={"curp": curp})
                            break
                        else:
                            logger.warning(f"⚠️ Second email attempt {attempt + 1} failed", extra={"curp": curp})
                            time.sleep(5)
                    mongo_logger.update_log(process_id, "Pdf_extraction_from_second_email_1", second_response.get("status", False))
                    mongo_logger.update_log(process_id, "Pdf_extraction_from_second_email_2", second_response.get("data", "No data"))
                    
                    # ✅ UPDATE: Handle second email result for RW update
                    if not second_response.get("status"):
                        try:
                            error_message = f"PDF extraction failed from both Chrome and second email: {second_response.get('data', 'Unknown error')}"
                            if last_second_email_error:
                                error_message = f"PDF extraction failed after 5 attempts: {str(last_second_email_error)}"
                            updateRW(curp=curp, condition=4, message=error_message, status="Complete", queue_document_id=queue_document_id)
                            logger.info(f"✅ [RW-UPDATE] Updated Registro_works with condition=4 (PDF extraction failed) for CURP {curp}")
                        except Exception as rw_error:
                            logger.error(f"❌ Failed to update Registro_works for failed PDF extraction: {rw_error}", extra={"curp": curp})
                    
                    return second_response
                        
             
                ipAddress = get_device_ip(device_name)
                mongo_logger.update_log(process_id, "ip_address", ipAddress)


            # Default fallback
            logger.info("No condition matched, returning raw response", extra={"curp": curp})
            
            # ✅ UPDATE: Handle unknown responses appropriately
            try:
                if status:
                    # If status is true but no pattern matched, treat as condition 4 (unknown success)
                    updateRW(curp=curp, condition=4, message=f"Unknown successful response: {out}", status="Complete", queue_document_id=queue_document_id)
                    logger.info(f"✅ [RW-UPDATE] Updated Registro_works with condition=4 (unknown success) for CURP {curp}")
                else:
                    # If status is false, treat as condition 4 (failure)
                    updateRW(curp=curp, condition=4, message=f"Unknown failure response: {out}", status="Complete", queue_document_id=queue_document_id)
                    logger.info(f"✅ [RW-UPDATE] Updated Registro_works with condition=4 (failure) for CURP {curp}")
            except Exception as rw_error:
                logger.error(f"❌ Failed to update Registro_works for fallback case: {rw_error}", extra={"curp": curp})
            
            return {"data": out, "status": status}

# # # ---------------- Flask Routes ---------------- #
app = Flask(__name__)
scraper = IMSSAppScraper()

# ✅ SIMPLIFIED: Constants following iwd.py approach
HEARTBEAT_STALE_SECONDS = 60

def _now():
    """Return server's local datetime (not UTC)."""
    return datetime.now()

@app.route("/device-check", methods=["GET"])
def device_check():
    try:
        # Get local devices
        with lock:
            local_devices = connected_devices.copy()
        
        # Get MongoDB devices
        devices_collection = get_devices_collection()
        mongo_devices = list(devices_collection.find(
            {"process": "IAD"}, 
            {
                "device": 1, 
                "online": 1, 
                "available": 1, 
                "current_task": 1, 
                "task_id": 1,
                "task_start_time": 1,
                "last_heartbeat": 1, 
                "_id": 0
            }
        ))
        
        # Add calculated fields for better debugging
        current_time = datetime.now()
        for device in mongo_devices:
            if device.get("task_start_time"):
                processing_time = (current_time - device["task_start_time"]).total_seconds()
                device["processing_time_minutes"] = round(processing_time / 60, 2)
            
            if device.get("last_heartbeat"):
                heartbeat_age = (current_time - device["last_heartbeat"]).total_seconds()
                device["heartbeat_age_seconds"] = round(heartbeat_age, 2)
        
        # Get active tasks
        active_tasks = iad_processing_state.get_active_tasks()
        
        return jsonify({
            "connected_devices": local_devices,
            "count": len(local_devices),
            "mongodb_devices": mongo_devices,
            "mongodb_count": len(mongo_devices),
            "background_tasks": active_tasks,
            "background_tasks_count": len(active_tasks),
            "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({
            "connected_devices": connected_devices,
            "count": len(connected_devices),
            "mongodb_error": str(e),
            "background_tasks": {},
            "background_tasks_count": 0
        })

@app.route("/task-status", methods=["GET"])
def task_status():
    """Get current background task processing status"""
    try:
        active_tasks = iad_processing_state.get_active_tasks()
        
        # Calculate processing times
        for task_id, task_info in active_tasks.items():
            processing_time = time.time() - task_info['start_time']
            task_info['processing_time_seconds'] = round(processing_time, 2)
            
        # Get device status
        devices_collection = get_devices_collection()
        total_devices = devices_collection.count_documents({"process": "IAD"})
        busy_devices = devices_collection.count_documents({"process": "IAD", "available": False})
        
        return jsonify({
            "status": "success",
            "active_background_tasks": len(active_tasks),
            "background_tasks": active_tasks,
            "device_summary": {
                "total_devices": total_devices,
                "busy_devices": busy_devices,
                "free_devices": total_devices - busy_devices
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "active_background_tasks": 0,
            "background_tasks": {}
        }), 500

@app.route("/imss/anydesk/dfl", methods=["POST"])
def run_imss_anydesk():
    data = request.get_json()
    curp = data.get("curp")
    device_id = data.get("device_id")
    taskid = data.get("taskid")
    queue_document_id = data.get("queue_document_id")

    # -------- Validation --------
    if not curp:
        updateRW(curp=None, condition=4, message="Missing 'curp'", status="Complete", queue_document_id=queue_document_id)
        return jsonify({"status": "error", "message": "Missing 'curp'", "app_dfl_completed": False}), 400
    if not device_id:
        updateRW(curp=curp, condition=4, message="Missing 'device_id'", status="Complete", queue_document_id=queue_document_id)
        return jsonify({"status": "error", "message": "Missing 'device_id'", "app_dfl_completed": False}), 400
    if not taskid:
        updateRW(curp=curp, condition=4, message="Missing 'taskid'", status="Complete", queue_document_id=queue_document_id)
        return jsonify({"status": "error", "message": "Missing 'taskid'", "app_dfl_completed": False}), 400
    if not queue_document_id:  # ✅ NEW validation
        updateRW(curp=curp, condition=4, message="Missing 'queue_document_id'", status="Complete", queue_document_id=queue_document_id)
        return jsonify({"status": "error", "message": "Missing 'queue_document_id'", "app_dfl_completed": False}), 400

    logger.info(f"🔍 [IAD-REQUEST] CURP={curp} | Device={device_id} | Task={taskid} | Queue={queue_document_id}")

    try:
        devices_collection = get_devices_collection()

        device_doc = devices_collection.find_one({
                "device": device_id,
                "process": "IAD",
                "online": True,
                "available": False,  # Debe estar ocupado
                "task_id": taskid    # Con mi tarea específica
            })

        if not device_doc:
            logger.warning(f"❌ [IAD] Device {device_id} assignment failed for task {taskid}")
            updateRW(curp=curp, condition=4, message=f"Device {device_id} not available", status="Complete", queue_document_id=queue_document_id)
            return jsonify({
                "status": "error",
                "message": f"Device {device_id} not available",
                "app_dfl_completed": False
            }), 400

        # ✅ FOLLOWING iwd.py: Ensure no other device is processing same CURP
        busy_device = devices_collection.find_one({
            "process": "IAD",
            "available": False,
            "current_task": curp,
            "device": {"$ne": device_id}
        })
        if busy_device:
            logger.warning(f"⚠️ CURP {curp} already in use by {busy_device['device']}")
            # Release the device we just assigned
            release_device(device_id, taskid)
            updateRW(curp=curp, condition=4, message=f"CURP {curp} is already being processed", status="Complete", queue_document_id=queue_document_id)
            return jsonify({
                "status": "error",
                "message": f"CURP {curp} is already being processed",
                "app_dfl_completed": False
            }), 429

        # ✅ FOLLOWING iwd.py: Submit to background processing
        logger.info(f"🔒 [IAD] Submitting CURP {curp} to background processing on {device_id}")
        
        # Get device count for response (like iwd.py)
        try:
            total_devices = devices_collection.count_documents({"process": "IAD", "online": True})
            available_devices = devices_collection.count_documents({"process": "IAD", "online": True, "available": True})
        except Exception as device_count_error:
            logger.warning(f"❌ Could not get device counts: {device_count_error}")
            updateRW(curp=curp, condition=4, message=f"Could not get device counts: {device_count_error}", status="Complete", queue_document_id=queue_document_id)
            total_devices = 1
            available_devices = 0
        
        # Submit background task
        future = task_executor.submit(process_imss_app_background, curp, device_id, taskid, queue_document_id)

        # Return immediately with success (match iwd.py format)
        response = {
            "status": "success",
            "message": "CURP accepted for background processing",
            "app_dfl_completed": False,  # Like web_scraper_completed in iwd.py
            "available_devices": available_devices,
            "background_processing": True
        }
        
        logger.info(f"✅ [IAD] Accepted CURP {curp} on {device_id} for background processing")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"❌ Error processing CURP {curp} on {device_id}: {e}")
        traceback.print_exc()
        
        # Add updateRW call for Flask endpoint errors
        try:
            updateRW(curp=curp, condition=4, message=f"Flask endpoint error: {str(e)}", status="Complete", queue_document_id=queue_document_id)
        except Exception as rw_error:
            logger.error(f"❌ Failed to update RW for Flask endpoint error: {rw_error}")
        
        return jsonify({
            "status": "error",
            "message": "Server error occurred",
            "app_dfl_completed": False
        }), 500

@app.route("/force-release-device", methods=["POST"])
def force_release_device():
    """Force release a stuck device (emergency use only) - FOLLOWING iwd.py pattern"""
    data = request.get_json()
    device_id = data.get("device_id")
    
    if not device_id:
        return jsonify({"status": "error", "message": "Missing 'device_id'"}), 400
    
    logger.warning(f"⚠️ [FORCE-RELEASE] Force releasing device {device_id}")
    
    try:
        # Get device status before release
        devices_collection = get_devices_collection()
        device_status_before = devices_collection.find_one(
            {"device": device_id, "process": "IAD"}, 
            {"device": 1, "available": 1, "current_task": 1, "task_id": 1, "_id": 0}
        )
        
        # Force release MongoDB device (following iwd.py pattern)
        result = devices_collection.update_one(
            {"device": device_id, "process": "IAD"},
            {
                "$set": {"available": True, "updated_at": datetime.now()},
                "$unset": {"current_task": "", "task_id": "", "task_start_time": ""}
            }
        )
        
        mongodb_released = result.modified_count > 0
        
        # Get device status after release
        device_status_after = devices_collection.find_one(
            {"device": device_id, "process": "IAD"}, 
            {"device": 1, "available": 1, "current_task": 1, "task_id": 1, "_id": 0}
        )
        
        logger.info(f"🔓 [FORCE-RELEASE] Device {device_id} status after release: {device_status_after}")
        
        return jsonify({
            "status": "success",
            "message": f"Force released device {device_id}",
            "mongodb_released": mongodb_released,
            "device_status_before": device_status_before,
            "device_status_after": device_status_after
        })
        
    except Exception as e:
        logger.error(f"❌ Error force releasing device {device_id}: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error force releasing device: {str(e)}"
        }), 500

# ✅ SIMPLIFIED: Cleanup functions following iwd.py approach
def cleanup_background_tasks():
    """Cleanup background task executor on shutdown"""
    logger.info("[Server] Shutting down background task executor...")
    task_executor.shutdown(wait=True)
    logger.info("[Server] Background task executor shut down complete")

# ✅ SIMPLIFIED: Startup following iwd.py pattern
if __name__ == "__main__":
    logger.info("[Server] Starting device monitor thread...")
    monitor_thread = threading.Thread(target=monitor_devices, daemon=True)
    monitor_thread.start()

    logger.info("[Server] Registering devices in MongoDB...")
    register_all_devices_on_startup()
    
    # logger.info("[Server] Starting device heartbeat monitoring...")
    # heartbeat_thread = threading.Thread(target=start_device_heartbeat_monitoring, daemon=True)
    # heartbeat_thread.start()

    logger.info("[Server] Starting Flask app on port 3000 with MongoDB-only device locking...")
    
    try:
        app.run(host="0.0.0.0", port=3000, debug=True)
    except KeyboardInterrupt:
        logger.info("[Server] Received shutdown signal...")
        cleanup_background_tasks()
    finally:
        cleanup_background_tasks()