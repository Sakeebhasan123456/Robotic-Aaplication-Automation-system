import subprocess
import time
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
IP_LOG_DIR = "logs/ipInfo"

def log_ip(device_id, ip_address, message):
    """Append IP log to a device-specific text file."""
    if not ip_address:
        ip_address = "N/A"

    os.makedirs(IP_LOG_DIR, exist_ok=True)
    file_path = os.path.join(IP_LOG_DIR, f"{device_id}.log")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}][{ip_address}] message: {message}\n"

    with open(file_path, "a") as f:
        f.write(log_entry)

    print(f"[{device_id}] Logged: {log_entry.strip()}")

# -------- ADB Command Runner --------
def run_adb_command(device_id, cmd):
    full_cmd = ["adb", "-s", device_id] + cmd
    result = subprocess.run(full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout.strip()

# -------- IP Address Functions --------
def get_device_ip(device_id: str) -> str:
    # logging.info(f"Getting IP address for device: {device_id}")

    try:
        # Run the ADB + netcat command
        cmd = [
            "adb", "-s", device_id, "shell",
            "echo -e 'GET /ip HTTP/1.1\\r\\nHost: ipinfo.io\\r\\n\\r\\n' | nc ipinfo.io 80"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            logging.error(f"Failed to run command: {result.stderr.strip()}")
            return ""

        # Parse the response
        lines = result.stdout.strip().splitlines()
        logging.debug(f"Raw response:\n{result.stdout}")

        # IP address will be the last non-empty line
        ip_address = ""
        for line in reversed(lines):
            if line.strip() and "." in line:
                ip_address = line.strip()
                break

        # if ip_address:
        #     logging.info(f"Got IP address")
        # else:
        #     logging.warning(f"No IP address found in response for device {device_id}")

        return ip_address

    except subprocess.TimeoutExpired:
        logging.error("Command timed out.")
        return ""
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return ""
    

# -------- Wi-Fi Functions --------
def is_wifi_enabled(device_id):
    output = run_adb_command(device_id, ["shell", "dumpsys", "wifi"])
    return "Wi-Fi is enabled" in output

def turn_on_wifi(device_id):
    if not is_wifi_enabled(device_id):
        print(f"[{device_id}] Turning ON Wi-Fi...")
        run_adb_command(device_id, ["shell", "svc", "wifi", "enable"])
    else:
        print(f"[{device_id}] Wi-Fi is already ON")

def turn_off_wifi(device_id):
    if is_wifi_enabled(device_id):
        print(f"[{device_id}] Turning OFF Wi-Fi...")
        run_adb_command(device_id, ["shell", "svc", "wifi", "disable"])
    else:
        print(f"[{device_id}] Wi-Fi is already OFF")

# -------- Mobile Data Functions --------
def is_mobile_data_enabled(device_id):
    output = run_adb_command(device_id, ["shell", "dumpsys", "telephony.registry"])
    return "mDataConnectionState=2" in output or "mDataConnectionState=CONNECTED" in output

def turn_on_mobile_data(device_id):
    if not is_mobile_data_enabled(device_id):
        print(f"[{device_id}] Turning ON Mobile Data...")
        run_adb_command(device_id, ["shell", "svc", "data", "enable"])
    else:
        print(f"[{device_id}] Mobile Data is already ON")

def turn_off_mobile_data(device_id):
    if is_mobile_data_enabled(device_id):
        print(f"[{device_id}] Turning OFF Mobile Data...")
        run_adb_command(device_id, ["shell", "svc", "data", "disable"])
    else:
        print(f"[{device_id}] Mobile Data is already OFF")

# -------- Airplane Mode Functions --------
def is_airplane_mode_enabled(device_id):
    output = run_adb_command(device_id, ["shell", "settings", "get", "global", "airplane_mode_on"])
    return output.strip() == "1"

def turn_on_airplane_mode(device_id):
    if not is_airplane_mode_enabled(device_id):
        print(f"[{device_id}] Turning ON Airplane Mode...")
        run_adb_command(device_id, ["shell", "settings", "put", "global", "airplane_mode_on", "1"])
        run_adb_command(device_id, ["shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", "true"])
    else:
        print(f"[{device_id}] Airplane Mode is already ON")

def turn_off_airplane_mode(device_id):
    if is_airplane_mode_enabled(device_id):
        print(f"[{device_id}] Turning OFF Airplane Mode...")
        run_adb_command(device_id, ["shell", "settings", "put", "global", "airplane_mode_on", "0"])
        run_adb_command(device_id, ["shell", "am", "broadcast", "-a", "android.intent.action.AIRPLANE_MODE", "--ez", "state", "false"])
    else:
        print(f"[{device_id}] Airplane Mode is already OFF")
        
def reset_airplane_mode(device_id):

    print(f"[{device_id}] Resetting Airplane Mode (Turning ON then OFF)...")
    before_ip = get_device_ip(device_id)
    log_ip(device_id, before_ip, "IP address before turning on airplane mode")
    print(f"[{device_id}] IP before turning on airplane mode: {before_ip}")
    turn_on_airplane_mode(device_id)
    time.sleep(180)
    turn_off_airplane_mode(device_id)
    time.sleep(40)
    after_ip = get_device_ip(device_id)
    log_ip(device_id, after_ip, "IP address after turning off airplane mode")
    print(f"[{device_id}] IP after turning off airplane mode: {after_ip}")

    print(f"[{device_id}] Airplane Mode Reset Complete")
    
#------------------------- restart mobilde device 
def restart_android_device(device_id: str, wait_timeout: int = 90):
    """
    Reboots an Android device, waits for it to come online, and swipes to unlock.
    
    Args:
        device_id (str): ADB device ID (e.g., ZE223FZQ6C)
        wait_timeout (int): Time to wait for device to come online (seconds)
    """
    before_ip = get_device_ip(device_id)
    log_ip(device_id, before_ip, "IP address before restart")
    logging.info(f"Rebooting device: {device_id}")
    try:
        subprocess.run(["adb", "-s", device_id, "reboot"], check=True)
    except subprocess.CalledProcessError:
        logging.error(f"Failed to reboot device {device_id}")
        return

    # Allow time for device to shut down
    time.sleep(5)

    logging.info("Waiting for device to come back online...")

    # Wait until device is back online
    start_time = time.time()
    while time.time() - start_time < wait_timeout:
        output = run_adb_command(device_id, ["devices"])

        if device_id in output and "device" in output:
            logging.info(f"Device {device_id} is back online.")
            break
        time.sleep(2)
    else:
        logging.warning(f"Device {device_id} did not come online in {wait_timeout} seconds.")
        return

    # Wait a little extra time for full boot
    logging.info("Waiting for UI to fully load...")
    time.sleep(10)
    

    # Swipe up to unlock the device
    logging.info("Swiping up to unlock the screen...")
    try:
        subprocess.run(["adb", "-s", device_id, "shell", "input", "swipe", "500", "1800", "500", "500"], check=True)
        logging.info("Swipe to unlock command sent successfully.")
    except subprocess.CalledProcessError:
        logging.error("Failed to swipe and unlock the device.")
        
def normal_reset_mobile_data(device_id):
    import time

    print(f"[{device_id}] Resetting Mobile Data (Turning OFF then ON)...")
    before_ip = get_device_ip(device_id)
    log_ip(device_id, before_ip, "IP address before turning off mobile data")
    
    turn_off_mobile_data(device_id)
    time.sleep(20)
    turn_on_mobile_data(device_id)
    time.sleep(10)  # Wait for mobile data to reconnect
    after_ip = get_device_ip(device_id)
    log_ip(device_id, before_ip, "IP address after turning on mobile data")
    

    print(f"[{device_id}] normal Mobile Data Reset Complete")
    


def reset_mobile_data(device_id):

    print(f"[{device_id}] Starting Mobile Data Reset Flow...")

    # Get IP before turning off data
    before_ip = get_device_ip(device_id)
    print(f"[{device_id}] Before IP: {before_ip}")
    log_ip(device_id, before_ip, "IP address before turning off mobile data")
    if not before_ip:
        print(f"[{device_id}] Could not fetch IP before turning off data.")
    
    print(f"[{device_id}] Turning OFF Mobile Data...")
    turn_off_mobile_data(device_id)
    time.sleep(20)

    print(f"[{device_id}] Turning ON Mobile Data...")
    turn_on_mobile_data(device_id)
    time.sleep(8)  # Give more time for reconnection

    # Get IP after turning back on
    after_ip = get_device_ip(device_id)
    log_ip(device_id, after_ip, "IP address after turning on mobile data")
    print(f"[{device_id}] After IP: {after_ip}")
    if not after_ip:
        print(f"[{device_id}] Could not fetch IP after turning on data.")

    print(f"[{device_id}] Before IP: {before_ip}, After IP: {after_ip}")

    # Compare IPs
    if before_ip and after_ip and before_ip == after_ip:
        print(f"[{device_id}] IP did not change after mobile data reset. Resetting Airplane Mode...")
        ##reset_airplane_mode(device_id)
        restart_android_device(device_id)
        after_ip = get_device_ip(device_id)
        log_ip(device_id, after_ip, "IP address after restart")
    else:
        print(f"[{device_id}] IP changed, no restart needed.")

    # print(f"[{device_id}] Clearing Chrome app data...")
    
    # Ensure Mobile Data is ON at the end
    if not is_mobile_data_enabled(device_id):
        print(f"[{device_id}] Mobile Data is OFF after reset. Turning it back ON...")
        turn_on_mobile_data(device_id)
        time.sleep(3)
    else:
        print(f"[{device_id}] Mobile Data is already ON.")
    
    
    # run_adb_command(device_id, ["shell", "pm", "clear", "com.android.chrome"])
    print(f"[{device_id}] Mobile Data Reset")





# if __name__ == "__main__":
#     example_device = "ZE223G8FX9"
#     # reset_airplane_mode(example_device)
#     reset_mobile_data(example_device)
#     # ip = get_device_ip(example_device)
#     # print(f"✅ Final IP: {ip}")



        
# -------------------

