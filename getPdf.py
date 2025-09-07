import subprocess
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

def delete_downloaded_pdfs(device_id):
    print("➡️ Deleting downloaded PDFs from /sdcard/Download...")
    try:
        subprocess.run(["adb", "-s", device_id, "shell", "rm", "/sdcard/Download/*.pdf"], check=True)
        print("✅ Deleted downloaded PDFs successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        
def pull_pdf_from_device(device_id: str, curp: str, target_folder: str = "pdf") -> dict:
    """
    Pulls either `reporteSemanasCotizadas.pdf` or 
    `Constancia de Semanas Cotizadas del Asegurado.pdf` from the device,
    saves it locally as <curp>.pdf, and deletes it from the device after.
    """
    try:
        script_dir = Path(__file__).resolve().parent
        pdf_dir = script_dir / target_folder
        pdf_dir.mkdir(parents=True, exist_ok=True)

        possible_files = [
            "/sdcard/Download/reporteSemanasCotizadas.pdf",
            "/sdcard/Download/Constancia de Semanas Cotizadas del Asegurado.pdf"
        ]

        local_path = pdf_dir / f"{curp}.pdf"

        # Try each possible file
        for remote_path in possible_files:
            logger.info(f"[{device_id}] 📥 Trying to pull: {remote_path}")
            result = subprocess.run(
                ["adb", "-s", device_id, "pull", remote_path, str(local_path)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and local_path.exists() and local_path.stat().st_size > 0:
                logger.info(f"[{device_id}] ✅ PDF pulled successfully to {local_path}")
                
                # Delete all downloaded PDFs from the device
                delete_downloaded_pdfs(device_id)

                return {"status": True, "data": f"pdf saved successfully at {local_path}"}
            else:
                logger.info(f"[{device_id}] ❌ {remote_path} not found or empty.")

        return {"status": False, "data": "No matching PDF found on device."}

    except Exception as e:
        logger.exception(f"[{device_id}] ❌ Unexpected error occurred while pulling PDF.")
        return {"status": False, "data": str(e)}
    
# response = pull_pdf_from_device(device_id="ZE223G8FX9", curp="test123")
# print("✅", response)