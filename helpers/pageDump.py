import os
import sys
import time

# --------- Configuration ---------
device_id = "RZ8T80KSXYD"
base_dir = "outlookReopen"

#https://serviciosdigitales.imss.gob.mx/semanascotizadas-web/certificacionhttps://serviciosdigitales.imss.gob.mx/semanascotizadas-web/certificacion/vistaReporte?token=aPMK8tXIWOOWHsAkfRWE+g==&curp=/PKtWroJtZUt/XhjuXVYZG+7El2KPgri&nss=z8u5NGk+dr1CRUA2KSnW5A==&correo=jkYo70WGGG+2E2eH4BZBsoDengY4OLEJz5FaXk2M6lw=&detalle=true&origen=MOVILES
# 
page_number = "copy_link_address"

# --------- Directory Setup ---------
page_dir = os.path.join(base_dir, f"page{page_number}")
os.makedirs(page_dir, exist_ok=True)

print(f"\n📸 Capturing Outlook UI for Page {page_number}...")
os.system(f"adb -s {device_id} shell rm /sdcard/view.xml")

# --------- ADB Commands ---------
os.system(f"adb -s {device_id} shell uiautomator dump /sdcard/view.xml")
# os.system(f"adb -s {device_id} pull /sdcard/view.xml {page_dir}/view.xml")
os.system(f'adb -s {device_id} pull /sdcard/view.xml "{page_dir}/view.xml"')
os.system(f"adb -s {device_id} exec-out screencap -p > {page_dir}/screen.png")

print(f"✅ Saved to {page_dir}")
