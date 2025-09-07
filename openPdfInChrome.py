
import os
import json
import time
import random
import asyncio
import logging
import subprocess
from pathlib import Path
from filelock import FileLock
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import aiohttp
import shutil
# from utils.deleteAndPull import delete_downloaded_pdfs, pull_pdf_from_device
# from utils.downloadPdf import downloadPdf
# from pdfProcess import extract_main_and_associated_curps
from datetime import datetime

# ------------------------- Logger Setup -------------------------
logger = logging.getLogger("curp_launcher")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# ------------------------- Configuration -------------------------
UTILS_FOLDER = "utils"
PORT_MAP_FILE = Path(UTILS_FOLDER) / "device_port_map.json"
PORT_MAP_LOCK = str(PORT_MAP_FILE) + ".lock"
BASE_PORT = 9222
GOB_CURP_URL = "https://www.gob.mx/curp/"


os.makedirs(UTILS_FOLDER, exist_ok=True)

# ------------------------- Utility Functions -------------------------

def get_devtools_port(device_id):
    """Assign or retrieve a unique port for a device."""
    with FileLock(PORT_MAP_LOCK):
        port_map = {}
        if PORT_MAP_FILE.exists():
            try:
                port_map = json.loads(PORT_MAP_FILE.read_text())
            except json.JSONDecodeError:
                logger.warning("⚠️ Failed to parse port map file. Starting fresh.")

        if device_id not in port_map:
            assigned_ports = set(port_map.values())
            port = BASE_PORT
            while port in assigned_ports:
                port += 1
            port_map[device_id] = port
            PORT_MAP_FILE.write_text(json.dumps(port_map, indent=2))
        return port_map[device_id]

def force_stop_chrome(device_id):
    logger.info(f"[{device_id}] 🚪 Force-stopping Chrome...")
    subprocess.run(["adb", "-s", device_id, "shell", "am", "force-stop", "com.android.chrome"])

def start_chrome_incognito(device_id):
    logger.info(f"[{device_id}] 🌀 Launching Chrome in incognito mode...")
    subprocess.run([
        "adb", "-s", device_id, "shell", "am", "start",
        "-n", "com.android.chrome/com.google.android.apps.chrome.IntentDispatcher",
        "-a", "android.intent.action.VIEW",
        "-d", "about:",
        "--ez", "create_new_tab", "true",
        "--ez", "incognito", "true"
    ])
    logger.info(f"[{device_id}] ✅ Chrome launched")

def forward_port(device_id, port):
    subprocess.run(["adb", "-s", device_id, "forward", f"tcp:{port}", "localabstract:chrome_devtools_remote"])
    logger.info(f"[{device_id}] 🔌 Port {port} forwarded")

async def wait_for_devtools(port, retries=10, delay=1):
    url = f"http://localhost:{port}/json/version"
    logger.info(f"⏳ Waiting for DevTools on port {port}...")
    async with aiohttp.ClientSession() as session:
        for _ in range(retries):
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        logger.info("✅ DevTools endpoint is ready")
                        return
            except Exception:
                pass
            await asyncio.sleep(delay)
    raise TimeoutError("❌ DevTools endpoint not available")


# ------------------------- Core Automation -------------------------

def run_adb(*args):
    try:
        subprocess.run(["adb"] + list(args), check=True)
    except subprocess.CalledProcessError as e:
        logger.warning(f"ADB command failed: {' '.join(args)} | {e}")


TARGET_TEXT = "El token ya fue utilizado"
async def openPdfInChrome(device_id, url=GOB_CURP_URL):
    port = get_devtools_port(device_id)
    force_stop_chrome(device_id)
    start_chrome_incognito(device_id)
    await asyncio.sleep(1)
    forward_port(device_id, port)
    await asyncio.sleep(2)

    try:
        await wait_for_devtools(port)
    except Exception as e:
        logger.error(f"[{device_id}] ❌ DevTools not ready: {e}")
        return {"data": str(e), "status": False}

    pdf_folder = os.path.abspath("pdf")
    os.makedirs(pdf_folder, exist_ok=True)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await context.new_page()

            await page.goto(url, timeout=20000)
            logger.info(f"[{device_id}] 🌐 Navigated to {url}")

            # -------------------------
            # Initial check (wait 5s)
            # -------------------------
            logger.info(f"[{device_id}] ⏳ Waiting 5 seconds to check initial page content...")
            await asyncio.sleep(5)

            try:
                content = await page.content()
            except Exception as e:
                logger.warning(f"[{device_id}] ⚠️ Error reading page content initially: {e}")
                content = ""

            # If target text present right away -> perform 2 swipe refreshes (up -> down) and return success
            if TARGET_TEXT in content:
                logger.info(f"[{device_id}] ✅ Target text present on first load. Performing 2 swipe refreshes (up->down).")
                for i in range(2):
                    # swipe from near top (y=300) to near bottom (y=1300) to simulate pull-to-refresh
                    run_adb("-s", device_id, "shell", "input", "swipe", "500", "300", "500", "1300", "300")
                    logger.info(f"[{device_id}] 🔄 Swipe refresh {i + 1}/2")
                    # give the page some time to react to the swipe
                    await asyncio.sleep(3)

                # optional small wait to settle
                await asyncio.sleep(1)
                await browser.close()
                logger.info(f"[{device_id}] 🔒 Browser closed after initial-refresh flow.")
                return {"data": "Token found on first load, refreshed twice via swipe", "status": True}

            # -------------------------
            # If not found initially, fall back to swiping loop
            # -------------------------
            max_attempts = 6
            found = False
            for attempt in range(max_attempts):
                logger.info(f"[{device_id}] 🔄 Swipe attempt {attempt + 1}/{max_attempts}")
                # swipe down to trigger refresh
                run_adb("-s", device_id, "shell", "input", "swipe", "500", "300", "500", "1300", "300")
                await asyncio.sleep(4)

                try:
                    content = await page.content()
                    if TARGET_TEXT in content:
                        logger.info(f"[{device_id}] ✅ Target text found after swiping (attempt {attempt + 1}).")
                        found = True
                        break
                except Exception as e:
                    logger.warning(f"[{device_id}] ⚠️ Error reading page content: {e}")

            if not found:
                logger.warning(f"[{device_id}] ❌ Target text not found after {max_attempts} attempts")
                await browser.close()
                return {"data": "Element not found after swiping", "status": False}

            # One final swipe after detection (keeps same behavior as before)
            logger.info(f"[{device_id}] 🔁 Final swipe after detection")
            run_adb("-s", device_id, "shell", "input", "swipe", "500", "300", "500", "1300", "300")
            await asyncio.sleep(2)

            await browser.close()
            logger.info(f"[{device_id}] 🔒 Browser closed.")
            return {"data": "Successfully opened PDF in Chrome", "status": True}

    except PlaywrightTimeoutError as e:
        logger.error(f"[{device_id}] ❌ Playwright timeout: {e}")
        return {"data": str(e), "status": False}
    except Exception as e:
        logger.error(f"[{device_id}] ❌ Unexpected error: {e}")
        return {"data": str(e), "status": False}


           
# if __name__ == "__main__":
#     url = "https://u46177290.ct.sendgrid.net/ls/click?upn=u001.Fs0JxkLJ-2F4omq8KyT-2Fcb7VOlKFdO3O3IcrTksIQA-2BX97n9GXn4Mm29JSeK4xa80R4qixbhM4nnMhXzRYwWjQcALMOHDFqMDc9K-2BSySA9CrV3Bx0JDCyirW-2Bd716PAE2hBnUBWb9jKHpIQSTNFmjzaXUBrRUysBe2otf8fngpnillr1-2BP216G7-2FPh8hdndZ6foG6oP8Yc1fYIPRQYL0tVTVvIOEDttJeirdqbSeYXClzwOiyD7-2FuuJg58Tvh2Z9CpfyiJMbqV925gAjSeyYiwq3mRSAkmOLhGIsq-2FQAIh1hF2VoUAVje0CHn5qD81jOKz0ecHwFGMw1CLvLAKbPV1HNW3cLo2Te-2FFIQ2omE8BQueDnPYa7ltwcmZ9h0ysfbeBbTo6_7oTzVuVQCDsmGavHWgBia-2FUeVFCRdNchKgtgH8YAN6ayVfAHXwVbOH79V-2BNqlPwNZK6067YLlpJWMNqB7HX4Rv8GzNFzYRoRuOD54zpWW82YLPFcJpvLyXyOmpvkfyCnvl1OHj9lEhBev-2FOzorDqvCoef1DpqFxy80iR2I2YWWmp8r24oxdz2bn4wY0L8IIfi6PnwaFTu-2BVIUOSEfY-2BDTKPWj35xUWv4u-2BNmrKv0Kuc-3D&detalle=detalle"
#     device_id = "ZE223G8FX9"
#     asyncio.run(openPdfInChrome(device_id, url=url))
    




# async def openPdfInChrome(device_id, url=GOB_CURP_URL):
#     port = get_devtools_port(device_id)
#     force_stop_chrome(device_id)
#     start_chrome_incognito(device_id)
#     await asyncio.sleep(1)
#     forward_port(device_id, port)
#     await asyncio.sleep(2)

#     try:
#         await wait_for_devtools(port)
#     except Exception as e:
#         logger.error(f"[{device_id}] ❌ DevTools not ready: {e}")
#         return {"data": str(e), "status": False}

#     pdf_folder = os.path.abspath("pdf")
#     os.makedirs(pdf_folder, exist_ok=True)

#     try:
#         async with async_playwright() as p:
#             browser = await p.chromium.connect_over_cdp(f"http://localhost:{port}")
#             context = browser.contexts[0] if browser.contexts else await browser.new_context()
#             page = await context.new_page()

#             await page.goto(url, timeout=20000)
#             logger.info(f"[{device_id}] 🌐 Navigated to {url}")

#             max_attempts = 20
#             found = False
#             for attempt in range(max_attempts):
#                 logger.info(f"[{device_id}] 🔄 Swipe attempt {attempt + 1}")
                
#                 # Swipe down to refresh
#                 run_adb("-s", device_id, "shell", "input", "swipe", "500", "300", "500", "1300", "300")
#                 await asyncio.sleep(4)

#                 try:
#                     content = await page.content()
#                     if 'El token ya fue utilizado' in content:
#                         logger.info(f"[{device_id}] ✅ Target element found.")
#                         found = True
#                         break
#                 except Exception as e:
#                     logger.warning(f"[{device_id}] ⚠️ Error reading page content: {e}")

#             if not found:
#                 logger.warning(f"[{device_id}] ❌ Element not found after {max_attempts} attempts")
#                 return {"data": "Element not found after swiping", "status": False}

#             # One final swipe after finding the element
#             logger.info(f"[{device_id}] 🔁 Final swipe after detection")
#             run_adb("-s", device_id, "shell", "input", "swipe", "500", "300", "500", "1300", "300")
#             await asyncio.sleep(2)

#             await browser.close()
#             logger.info(f"[{device_id}] 🔒 Browser closed.")
#             return {"data": "Successfully open pdf in chrome browser", "status": True}

#     except PlaywrightTimeoutError as e:
#         logger.error(f"[{device_id}] ❌ Playwright timeout: {e}")
#         return {"data": str(e), "status": False}
#     except Exception as e:
#         logger.error(f"[{device_id}] ❌ Unexpected error: {e}")
#         return {"data": str(e), "status": False}

