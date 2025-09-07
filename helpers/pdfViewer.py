from appium import webdriver
from appium.options.android import UiAutomator2Options
import time
import subprocess
import logging
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
logger = logging.getLogger(__name__)

def run_adb(*args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"ADB command failed: {' '.join(args)}\n{e.stderr}")
        return None
    
def delete_dummy_pdf_if_exists(device_name, file_path="/sdcard/Download/reporteSemanasCotizadas.pdf"):
    logger.info("🧹 Checking if reporteSemanasCotizadas.pdf exists on device")
    try:
        # List the file
        result = subprocess.run(
            ["adb", "-s", device_name, "shell", "ls", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if "No such file" in result.stderr:
            logger.info("✅ reporteSemanasCotizadas.pdf not found — no deletion needed.")
        else:
            # Delete the file
            subprocess.run(["adb", "-s", device_name, "shell", "rm", file_path])
            logger.info("🗑️ reporteSemanasCotizadas.pdf found and deleted.")
    except Exception as e:
        logger.warning(f"⚠️ Error while checking/deleting reporteSemanasCotizadas.pdf: {e}")
        
def pull_dummy_pdf_to_pc(device_name, curp, remote_path="/sdcard/Download/reporteSemanasCotizadas.pdf"):
    pdf_dir = "./pdf"
    os.makedirs(pdf_dir, exist_ok=True)
    local_path = os.path.join(pdf_dir, f"{curp}.pdf")

    try:
        result = subprocess.run(
            ["adb", "-s", device_name, "pull", remote_path, local_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            logger.info(f"✅ reporteSemanasCotizadas.pdf successfully pulled and saved as {curp}.pdf in 'pdf/'")
        else:
            logger.error(f"❌ Failed to pull reporteSemanasCotizadas.pdf: {result.stderr}")
    except Exception as e:
        logger.error(f"⚠️ Error during adb pull: {e}")

def savePdfFromChrome(driver, device_name,curp):
    try:
        logger.info("📄 Step 1: Tap 3-dot Chrome menu")
        # Tap the top-right corner (3 dots) - adjust coordinates if needed
        run_adb("adb", "-s", device_name, "shell", "input", "tap", "1000", "160")
        time.sleep(2)

        logger.info("📤 Step 2: Tap 'Open with' or 'Share'")
        try:
            # Try by text if available
            open_with_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Open with")')
                )
            )
            open_with_button.click()
        except:
            # If "Open with" not found, try coordinates or fallback to "Share"
            logger.warning("⚠️ Could not find 'Open with' by text — trying fallback tap.")
            run_adb("adb", "-s", device_name, "shell", "input", "tap", "900", "600")  # Approx for Open with
        time.sleep(2)
        
        logger.info("☁️ Step 3: Tap 'Drive' app")
        try:
            drive_option = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Drive")')
                )
            )
            drive_option.click()
        except Exception:
            logger.warning("⚠️ Could not find 'Drive' by text — using fallback tap.")
            run_adb("adb", "-s", device_name, "shell", "input", "tap", "400", "1850")  # Approx location for Drive

        time.sleep(2)

        logger.info("🕐 Step 4: Tap 'Just once'")
        try:
            just_once_button = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Just once")')
                )
            )
            just_once_button.click()
        except Exception:
            logger.warning("⚠️ Could not find 'Just once' — using fallback tap.")
            run_adb("adb", "-s", device_name, "shell", "input", "tap", "200", "2130")  # Approx location for Just once

        time.sleep(3)
        
        logger.info("📥 Step 5: Tap 3-dot menu in Drive PDF viewer")
        try:
            # Look for the "More options" ImageView (3-dot menu)
            menu_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (AppiumBy.ACCESSIBILITY_ID, "More options")
                )
            )
            menu_button.click()
        except Exception:
            logger.warning("⚠️ 'More options' not found — using fallback tap.")
            run_adb("adb", "-s", device_name, "shell", "input", "tap", "1050", "150")
        time.sleep(2)
        
        delete_dummy_pdf_if_exists(device_name)
        logger.info("⬇️ Step 6: Click on 'Download' in Google Drive options")
        try:
            # Locate and click on the "Download" option
            download_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Download")')
                )
            )
            download_btn.click()
            logger.info("✅ Download option clicked.")
        except Exception:
            logger.warning("⚠️ 'Download' option not found — using coordinate fallback.")
            run_adb("adb", "-s", device_name, "shell", "input", "tap", "800", "450")  # Adjust if needed
        time.sleep(3)
        # curp = "TEST1234"  # Replace with your actual CURP
        pull_dummy_pdf_to_pc(device_name,curp)
        logger.info(f"📂 PDF saved successfully in ./pdf/{curp}.pdf")
        
        

    

        # 👇 You can continue with "Step 4" once you give more instructions.

    except Exception as e:
        logger.error("❌ Failed in savePdfFromChrome()", exc_info=True)
def downloadPdfFromChrome(device_name, curp):
    # device_name = "RFCY20EKZMM"

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.platform_version = "14.0"
    options.udid = device_name
    options.device_name = device_name
    options.app_package = "com.android.chrome"
    options.app_activity = "com.google.android.apps.chrome.Main"
    options.automation_name = "UiAutomator2"
    options.no_reset = True
    options.auto_grant_permissions = True

    try:
        driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

        savePdfFromChrome(driver, device_name,curp)

        driver.quit()
    except Exception as e:
        print("❌ Failed to run Chrome automation", e)

if __name__ == "__main__":
    downloadPdfFromChrome("RFCY20EKZMM", "LUMS901008HPLCRR08")

