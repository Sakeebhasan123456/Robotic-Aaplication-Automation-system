import asyncio
import aiohttp
import io
import re
from datetime import datetime
from bson import ObjectId
import os
import pdfplumber
from pymongo import MongoClient
import traceback
import time
import shutil
from utils.mongoLogger import MongoLogger

mongo_logger = MongoLogger()

#MONGO_PRINCIPAL='mongodb://main_user:fu6o0fsIPwZXJ7Qo2KMGXXY31UoVDe7p@172.31.7.161:27017/admin'
MONGO_PRINCIPAL='mongodb://carlos_readonly:p13CCTjtXUaqf1xQyyR6KpuRtYzrsw9R@principal.mongodb.searchlook.mx:27017/admin'
PDF_PATH = r"C:\Users\HOSTN1\Desktop\imssAppDfl\Scraper_IMSS_App_Priyansh\pdf"
DEVICE = "IMSS_App_DFL_Priyansh_01"

# ✅ ADD: Function to update queue document based on queue_id from RW
def update_queue_document_for_condition1(rw_id, curp, message):
    """
    Update queue document for condition 1 (success) using queue_id from RW document
    
    Args:
        rw_id: The RW document ID to get queue_id from
        curp: CURP value for logging
        message: Success message to store
    """
    try:
        print(f"=== UPDATING QUEUE DOCUMENT FOR CONDITION 1 ===")
        print(f"RW ID: {rw_id}, CURP: {curp}")
        
        client = MongoClient(MONGO_PRINCIPAL)
        
        # Get RW collection and find the document
        rw_collection = client['Main_User']['Registro_works']
        rw_doc = rw_collection.find_one({"ID": rw_id})
        
        if not rw_doc:
            print(f"⚠️ No RW document found for ID: {rw_id}")
            client.close()
            return
        
        # Get queue_id from RW document
        queue_id = rw_doc.get("queue_id")
        
        if not queue_id:
            print(f"⚠️ No queue_id found in RW document for ID: {rw_id}")
            client.close()
            return
        
        print(f"📄 Found queue_id: {queue_id}")
        
        # Get queue collection
        queue_collection = client['Mini_Base_Central']['imss_queue_iad']
        
        # Update queue document with success=true for condition 1
        result = queue_collection.update_one(
            {"_id": ObjectId(queue_id)},
            {
                "$set": {
                    "Status": "Complete",
                    "success": True,  # condition 1 = success
                    "Message": message,
                    "completed_at": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully updated queue document {queue_id} with success=true (condition 1)")
        else:
            print(f"⚠️ Queue document {queue_id} found but nothing was modified")
            
        client.close()
        
    except Exception as e:
        print(f"❌ Failed to update queue document for RW {rw_id}, CURP {curp}: {str(e)}")
        traceback.print_exc()

def removerAcentos(cadena):
    lista_cars = [['Á','A'], ['É','E'], ['Í','I'], ['Ó','O'], ['Ú','U'], ['á','a'], ['é','e'], ['í','i'], ['ó','o'], ['ú','u']]
    for cars in lista_cars:
        cadena = re.sub(cars[0], cars[1], cadena)
    return cadena

states1 = {
    "Aguascalientes":{
        "_id" : ObjectId("5ae5abb59060ed36e3ca7ba0"),
        "name" : "Aguascalientes"
    },
    "Baja California":{ 
        "_id" : ObjectId("5ae5abb79060ed36e3ca7ba1"),
        "name" : "Baja California"
    },
    "Baja California Sur":{
        "_id" : ObjectId("5ae5abb99060ed36e3ca7ba2"),
        "name" : "Baja California Sur"
    },
    "Campeche":{
        "_id" : ObjectId("5ae5abba9060ed36e3ca7ba3"),
        "name" : "Campeche"
    },
    "Coahuila de Zaragoza":{
        "_id" : ObjectId("5ae5abbb9060ed36e3ca7ba4"),
        "name" : "Coahuila de Zaragoza"
    },
    "Colima":{
        "_id" : ObjectId("5ae5abbe9060ed36e3ca7ba5"),
        "name" : "Colima"
    },
    "Chiapas":{
        "_id" : ObjectId("5ae5abbf9060ed36e3ca7ba6"),
        "name" : "Chiapas"
    },
    "CHIHUAHUA":{
        "_id" : ObjectId("5ae5abc69060ed36e3ca7ba7"),
        "name" : "Chihuahua"
    },
    "CIUDAD DE MÉXICO":{
        "_id" : ObjectId("5ae5abb39060ed36e3ca7b9f"),
        "name" : "Ciudad de México"
    },
    "DISTRITO FEDERAL":{
        "_id" : ObjectId("5ae5abb39060ed36e3ca7b9f"),
        "name" : "Ciudad de México"
    },
    "DURANGO":{ 
        "_id" : ObjectId("5ae5abce9060ed36e3ca7ba8"),
        "name" : "Durango"
    },
    "GUANAJUATO":{
        "_id" : ObjectId("5ae5abd49060ed36e3ca7ba9"),
        "name" : "Guanajuato"
    },
    "GUERRERO":{
        "_id" : ObjectId("5ae5abdc9060ed36e3ca7baa"),
        "name" : "Guerrero"
    },
    "HIDALGO":{
        "_id" : ObjectId("5ae5abdf9060ed36e3ca7bab"),
        "name" : "Hidalgo"
    },
    "JALISCO":{
        "_id" : ObjectId("5ae5abe49060ed36e3ca7bac"),
        "name" : "Jalisco"
    },
    "ESTADO DE MÉXICO":{
        "_id" : ObjectId("5ae5abe89060ed36e3ca7bad"),
        "name" : "Estado de México"
    },
    "México":{
        "_id" : ObjectId("5ae5abe89060ed36e3ca7bad"),
        "name" : "Estado de México"
    },
    "MICHOACÁN DE OCAMPO":{
        "_id" : ObjectId("5ae5abee9060ed36e3ca7bae"),
        "name" : "Michoacán de Ocampo"
    },
    "MICHOACÁN":{
        "_id" : ObjectId("5ae5abee9060ed36e3ca7bae"),
        "name" : "Michoacán de Ocampo"
    },
    "Morelos":{
        "_id" : ObjectId("5ae5abfb9060ed36e3ca7baf"),
        "name" : "Morelos"
    },
    "Nayarit":{
        "_id" : ObjectId("5ae5abfd9060ed36e3ca7bb0"),
        "name" : "Nayarit"
    },
    "Nuevo León":{
        "_id" : ObjectId("5ae5abfe9060ed36e3ca7bb1"),
        "name" : "Nuevo León"
    },
    "Oaxaca":{
        "_id" : ObjectId("5ae5ac039060ed36e3ca7bb2"),
        "name" : "Oaxaca"
    },
    "Puebla":{ 
        "_id" : ObjectId("5ae5ac099060ed36e3ca7bb3"),
        "name" : "Puebla"
    },
     "Querétaro":{
        "_id" : ObjectId("5ae5ac0e9060ed36e3ca7bb4"),
        "name" : "Querétaro"
    },
    "Quintana Roo":{ 
        "_id" : ObjectId("5ae5ac119060ed36e3ca7bb5"),
        "name" : "Quintana Roo"
    },
    "San Luis Potosí": {
        "_id": ObjectId("5ae5ac129060ed36e3ca7bb6"),
        "name": "San Luis Potosí"
    },
    "Sinaloa":{
        "_id": ObjectId("5ae5ac179060ed36e3ca7bb7"),
        "name": "Sinaloa"
    },
    "Sonora":{
        "_id": ObjectId("5ae5ac1a9060ed36e3ca7bb8"),
        "name": "Sonora"
    },
    "Tabasco":{
        "_id": ObjectId("5ae5ac219060ed36e3ca7bb9"),
        "name": "Tabasco"
    },
    "Tamaulipas": {
        "_id": ObjectId("5ae5ac249060ed36e3ca7bba"),
        "name": "Tamaulipas"
    },
    "Tlaxcala": {
        "_id": ObjectId("5ae5ac269060ed36e3ca7bbb"),
        "name": "Tlaxcala"
    },
    "VERACRUZ DE IGNACIO DE LA LLAVE": {
        "_id": ObjectId("5ae5ac279060ed36e3ca7bbc"),
        "name": "Veracruz de Ignacio de la Llave"
    },
    "VERACRUZ": {
        "_id": ObjectId("5ae5ac279060ed36e3ca7bbc"),
        "name": "Veracruz de Ignacio de la Llave"
    },
    "Yucatán": {
        "_id": ObjectId("5ae5ac2f9060ed36e3ca7bbd"),
        "name": "Yucatán"
    },
    "Zacatecas": {
        "_id": ObjectId("5ae5ac309060ed36e3ca7bbe"),
        "name": "Zacatecas"
    },
    "NE": {
        "_id": None,
        "name": "Nacido En El Extranjero"
    },
    "": {
        "_id": None,
        "name": ""
    }
}

states_nombre_completo = {
    '': {'_id': None, 'name': ''},
    'MEXICO': {'_id': ObjectId('5ae5abe89060ed36e3ca7bad'), 'name': 'Estado de México'},
    'AGUASCALIENTES': {'_id': ObjectId('5ae5abb59060ed36e3ca7ba0'), 'name': 'Aguascalientes'},
    'BAJA CALIFORNIA': {'_id': ObjectId('5ae5abb79060ed36e3ca7ba1'), 'name': 'Baja California'},
    'BAJA CALIFORNIA SUR': {'_id': ObjectId('5ae5abb99060ed36e3ca7ba2'), 'name': 'Baja California Sur'},
    'CAMPECHE': {'_id': ObjectId('5ae5abba9060ed36e3ca7ba3'), 'name': 'Campeche'},
    'CHIAPAS': {'_id': ObjectId('5ae5abbf9060ed36e3ca7ba6'), 'name': 'Chiapas'},
    'CHIHUAHUA': {'_id': ObjectId('5ae5abc69060ed36e3ca7ba7'), 'name': 'Chihuahua'},
    'CIUDAD DE MEXICO': {'_id': ObjectId('5ae5abb39060ed36e3ca7b9f'), 'name': 'Ciudad de México'},
    'COAHUILA': {'_id': ObjectId('5ae5abbb9060ed36e3ca7ba4'), 'name': 'Coahuila de Zaragoza'},
    'COAHUILA DE ZARAGOZA': {'_id': ObjectId('5ae5abbb9060ed36e3ca7ba4'), 'name': 'Coahuila de Zaragoza'},
    'COLIMA': {'_id': ObjectId('5ae5abbe9060ed36e3ca7ba5'), 'name': 'Colima'},
    'DISTRITO FEDERAL': {'_id': ObjectId('5ae5abb39060ed36e3ca7b9f'), 'name': 'Ciudad de México'},
    'DURANGO': {'_id': ObjectId('5ae5abce9060ed36e3ca7ba8'), 'name': 'Durango'},
    'ESTADO DE MEXICO': {'_id': ObjectId('5ae5abe89060ed36e3ca7bad'), 'name': 'Estado de México'},
    'GUANAJUATO': {'_id': ObjectId('5ae5abd49060ed36e3ca7ba9'), 'name': 'Guanajuato'},
    'GUERRERO': {'_id': ObjectId('5ae5abdc9060ed36e3ca7baa'), 'name': 'Guerrero'},
    'HIDALGO': {'_id': ObjectId('5ae5abdf9060ed36e3ca7bab'), 'name': 'Hidalgo'},
    'JALISCO': {'_id': ObjectId('5ae5abe49060ed36e3ca7bac'), 'name': 'Jalisco'},
    'MICHOACAN DE OCAMPO': {'_id': ObjectId('5ae5abee9060ed36e3ca7bae'), 'name': 'Michoacán de Ocampo'},
    'MICHOACAN': {'_id': ObjectId('5ae5abee9060ed36e3ca7bae'), 'name': 'Michoacán de Ocampo'},
    'MORELOS': {'_id': ObjectId('5ae5abfb9060ed36e3ca7baf'), 'name': 'Morelos'},
    'NAYARIT': {'_id': ObjectId('5ae5abfd9060ed36e3ca7bb0'), 'name': 'Nayarit'},
    'NE': {'_id': None, 'name': 'Nacido En El Extranjero'},
    'NUEVO LEON': {'_id': ObjectId('5ae5abfe9060ed36e3ca7bb1'), 'name': 'Nuevo León'},
    'OAXACA': {'_id': ObjectId('5ae5ac039060ed36e3ca7bb2'), 'name': 'Oaxaca'},
    'PUEBLA': {'_id': ObjectId('5ae5ac099060ed36e3ca7bb3'), 'name': 'Puebla'},
    'QUERETARO': {'_id': ObjectId('5ae5ac0e9060ed36e3ca7bb4'), 'name': 'Querétaro'},
    'QUINTANA ROO': {'_id': ObjectId('5ae5ac119060ed36e3ca7bb5'), 'name': 'Quintana Roo'},
    'SAN LUIS POTOSI': {'_id': ObjectId('5ae5ac129060ed36e3ca7bb6'), 'name': 'San Luis Potosí'},
    'SINALOA': {'_id': ObjectId('5ae5ac179060ed36e3ca7bb7'), 'name': 'Sinaloa'},
    'SONORA': {'_id': ObjectId('5ae5ac1a9060ed36e3ca7bb8'), 'name': 'Sonora'},
    'TABASCO': {'_id': ObjectId('5ae5ac219060ed36e3ca7bb9'), 'name': 'Tabasco'},
    'TAMAULIPAS': {'_id': ObjectId('5ae5ac249060ed36e3ca7bba'), 'name': 'Tamaulipas'},
    'TLAXCALA': {'_id': ObjectId('5ae5ac269060ed36e3ca7bbb'), 'name': 'Tlaxcala'},
    'VERACRUZ DE IGNACIO DE LA LLAVE': {'_id': ObjectId('5ae5ac279060ed36e3ca7bbc'), 'name': 'Veracruz de Ignacio de la Llave'},
    'VERACRUZ': {'_id': ObjectId('5ae5ac279060ed36e3ca7bbc'), 'name': 'Veracruz de Ignacio de la Llave'},
    'YUCATAN': {'_id': ObjectId('5ae5ac2f9060ed36e3ca7bbd'), 'name': 'Yucatán'},
    'ZACATECAS': {'_id': ObjectId('5ae5ac309060ed36e3ca7bbe'), 'name': 'Zacatecas'}
}

states_abreviaciones = {
    "AGS": {"_id": ObjectId("5ae5abb59060ed36e3ca7ba0"), "name": "Aguascalientes"},
    "BCN": {"_id": ObjectId("5ae5abb79060ed36e3ca7ba1"), "name": "Baja California"},
    "BC": {"_id": ObjectId("5ae5abb79060ed36e3ca7ba1"), "name": "Baja California"},
    "BCS": {"_id": ObjectId("5ae5abb99060ed36e3ca7ba2"), "name": "Baja California Sur"},
    "CAM": {"_id": ObjectId("5ae5abba9060ed36e3ca7ba3"), "name": "Campeche"},
    "COA": {"_id": ObjectId("5ae5abbb9060ed36e3ca7ba4"), "name": "Coahuila de Zaragoza"},
    "COAH": {"_id": ObjectId("5ae5abbb9060ed36e3ca7ba4"), "name": "Coahuila de Zaragoza"},
    "COL": {"_id": ObjectId("5ae5abbe9060ed36e3ca7ba5"), "name": "Colima"},
    "CHS": {"_id": ObjectId("5ae5abbf9060ed36e3ca7ba6"), "name": "Chiapas"},
    "CHIS": {"_id": ObjectId("5ae5abbf9060ed36e3ca7ba6"), "name": "Chiapas"},
    "CHI": {"_id": ObjectId("5ae5abc69060ed36e3ca7ba7"), "name": "Chihuahua"},
    "CHIH": {"_id": ObjectId("5ae5abc69060ed36e3ca7ba7"), "name": "Chihuahua"},
    "CDMX": {"_id": ObjectId("5ae5abb39060ed36e3ca7b9f"), "name": "Ciudad de México"},
    "DGO": {"_id": ObjectId("5ae5abce9060ed36e3ca7ba8"), "name": "Durango"},
    "GTO": {"_id": ObjectId("5ae5abd49060ed36e3ca7ba9"), "name": "Guanajuato"},
    "GRO": {"_id": ObjectId("5ae5abdc9060ed36e3ca7baa"), "name": "Guerrero"},
    "HGO": {"_id": ObjectId("5ae5abdf9060ed36e3ca7bab"), "name": "Hidalgo"},
    "JAL": {"_id": ObjectId("5ae5abe49060ed36e3ca7bac"), "name": "Jalisco"},
    "EM": {"_id": ObjectId("5ae5abe89060ed36e3ca7bad"), "name": "Estado de México"},
    "MEX": {"_id": ObjectId("5ae5abe89060ed36e3ca7bad"), "name": "Estado de México"},
    "MICH": {"_id": ObjectId("5ae5abee9060ed36e3ca7bae"), "name": "Michoacán de Ocampo"},
    "MOR": {"_id": ObjectId("5ae5abfb9060ed36e3ca7baf"), "name": "Morelos"},
    "NAY": {"_id": ObjectId("5ae5abfd9060ed36e3ca7bb0"), "name": "Nayarit"},
    "NL": {"_id": ObjectId("5ae5abfe9060ed36e3ca7bb1"), "name": "Nuevo León"},
    "OAX": {"_id": ObjectId("5ae5ac039060ed36e3ca7bb2"), "name": "Oaxaca"},
    "PUE": {"_id": ObjectId("5ae5ac099060ed36e3ca7bb3"), "name": "Puebla"},
    "QRO": {"_id": ObjectId("5ae5ac0e9060ed36e3ca7bb4"), "name": "Querétaro"},
    "QROO": {"_id": ObjectId("5ae5ac119060ed36e3ca7bb5"), "name": "Quintana Roo"},
    "QR": {"_id": ObjectId("5ae5ac119060ed36e3ca7bb5"), "name": "Quintana Roo"},
    "SLP": {"_id": ObjectId("5ae5ac129060ed36e3ca7bb6"), "name": "San Luis Potosí"},
    "SIN": {"_id": ObjectId("5ae5ac179060ed36e3ca7bb7"), "name": "Sinaloa"},
    "SON": {"_id": ObjectId("5ae5ac1a9060ed36e3ca7bb8"), "name": "Sonora"},
    "TAB": {"_id": ObjectId("5ae5ac219060ed36e3ca7bb9"), "name": "Tabasco"},
    "TAM": {"_id": ObjectId("5ae5ac249060ed36e3ca7bba"), "name": "Tamaulipas"},
    "TLA": {"_id": ObjectId("5ae5ac269060ed36e3ca7bbb"), "name": "Tlaxcala"},
    "TLAX": {"_id": ObjectId("5ae5ac269060ed36e3ca7bbb"), "name": "Tlaxcala"},
    "VER": {"_id": ObjectId("5ae5ac279060ed36e3ca7bbc"), "name": "Veracruz de Ignacio de la Llave"},
    "YUC": {"_id": ObjectId("5ae5ac2f9060ed36e3ca7bbd"), "name": "Yucatán"},
    "ZAC": {"_id": ObjectId("5ae5ac309060ed36e3ca7bbe"), "name": "Zacatecas"},
    "NE": {"_id": None, "name": "Nacido En El Extranjero"}
}

states = {**states_abreviaciones, **states_nombre_completo}
states1 = {removerAcentos(key).upper(): value for key, value in states1.items()}

def corregirBasura(estado0):
    estado = removerAcentos(estado0).upper()
    lista_estados = list(states_nombre_completo.keys())
    res = ''
    for s in lista_estados[:]:
        if estado.find(s) != -1:
            res = s
    if res == '':
        res = estado0
    return res

def fixState(estado):
    estado = corregirBasura(estado)
    estado = states.get(estado, states.get(''))
    return estado

def parsero(enter):
    if "/" in enter:
        enter = enter.replace(' ', '')
        enter = enter.split('/')
        y = datetime(int(enter[2]), int(enter[1]), int(enter[0]))
    else:
        y = enter
    return y

def extract_total_weeks(full_text):
    """Extrae el total de semanas cotizadas del encabezado - VERSIÓN DEFINITIVA"""
    try:
        print("=== EXTRAYENDO TOTAL DE SEMANAS (TSC) ===")
        
        # Extraer las primeras líneas donde está el encabezado
        lines = full_text.split('\n')
        
        # MÉTODO 1: Buscar el patrón exacto del encabezado
        # El formato es siempre: número grande en el encabezado después de "Total de semanas cotizadas"
        print("\n--- MÉTODO 1: Buscar patrón del encabezado ---")
        
        for i, line in enumerate(lines[:40]):  # Solo buscar en las primeras 40 líneas
            if "Total de semanas cotizadas" in line:
                print(f"Encontrado 'Total de semanas cotizadas' en línea {i}: {line}")
                
                # Buscar en las siguientes líneas el número
                for j in range(i+1, min(len(lines), i+8)):
                    next_line = lines[j].strip()
                    print(f"  Revisando línea {j}: '{next_line}'")
                    
                    # Buscar línea que solo contenga un número
                    if re.match(r'^\s*(\d{1,4})\s*$', next_line):
                        total = int(next_line)
                        # Validar que sea un total válido (no fecha)
                        if 1 <= total <= 5000 and total != 2025 and total != 2024:
                            print(f"✓ Total encontrado: {total}")
                            return total
        
        # MÉTODO 2: Buscar en la cadena original del pie de página que siempre contiene el total
        print("\n--- MÉTODO 2: Buscar en cadena original ---")
        
        # Buscar el patrón de la cadena original que siempre tiene el formato:
        # "Número total de semanas cotizadas:XX"
        cadena_pattern = re.search(r'Número total de semanas cotizadas:(\d{1,4})', full_text)
        if cadena_pattern:
            total = int(cadena_pattern.group(1))
            print(f"✓ Total encontrado en cadena original: {total}")
            return total
        
        # MÉTODO 3: Buscar el patrón específico en el NSS/CURP/Total
        print("\n--- MÉTODO 3: Buscar patrón NSS/CURP/Total ---")
        
        # Buscar después de encontrar NSS y CURP
        nss_found = -1
        curp_found = -1
        
        for i, line in enumerate(lines[:30]):
            if "NSS:" in line:
                nss_found = i
                print(f"NSS encontrado en línea {i}")
            elif "CURP:" in line and nss_found != -1:
                curp_found = i
                print(f"CURP encontrado en línea {i}")
                
                # Buscar el número en las siguientes líneas
                for j in range(i+1, min(len(lines), i+6)):
                    check_line = lines[j].strip()
                    if re.match(r'^\s*(\d{1,4})\s*$', check_line):
                        total = int(check_line)
                        if 1 <= total <= 5000:
                            print(f"✓ Total encontrado después de CURP: {total}")
                            return total
                break
        
        # MÉTODO 4: Buscar números aislados en el encabezado excluyendo fechas
        print("\n--- MÉTODO 4: Búsqueda de números aislados ---")
        
        for i, line in enumerate(lines[:25]):
            line_clean = line.strip()
            if re.match(r'^\s*(\d{1,4})\s*$', line_clean):
                total = int(line_clean)
                print(f"Candidato en línea {i}: {total}")
                
                # Verificar que no sea fecha
                context_valid = True
                for k in range(max(0, i-2), min(len(lines), i+3)):
                    context_line = lines[k].lower()
                    if any(word in context_line for word in ['fecha', 'dd', 'mm', 'yyyy', '/', '2024', '2025']):
                        context_valid = False
                        break
                
                if context_valid and 1 <= total <= 5000:
                    # Verificar que esté en el contexto correcto (después de datos personales)
                    found_personal_data = False
                    for k in range(max(0, i-10), i):
                        if any(word in lines[k] for word in ['NSS:', 'CURP:', 'Total de semanas']):
                            found_personal_data = True
                            break
                    
                    if found_personal_data:
                        print(f"✓ Total encontrado por contexto: {total}")
                        return total
        
        print("⚠️ No se encontró el total de semanas")
        return 0
        
    except Exception as e:
        print(f"Error extrayendo total de semanas: {e}")
        return 0

def extract_weeks_detail(full_text):
    """Extrae el detalle de semanas de la tabla específica"""
    try:
        print("=== EXTRAYENDO DETALLE DE SEMANAS ===")
        
        lines = full_text.split('\n')
        
        # Buscar en la sección de la tabla
        in_detail_section = False
        
        for i, line in enumerate(lines):
            if "Tu detalle de semanas cotizadas" in line:
                in_detail_section = True
                print(f"Inicio de sección detalle en línea {i}")
                continue
            elif "Tu historia laboral" in line:
                print(f"Fin de sección detalle en línea {i}")
                break
            elif in_detail_section:
                # Buscar línea con exactamente 3 números
                line_clean = line.strip()
                if re.match(r'^\s*\d+\s+\d+\s+\d+\s*$', line_clean):
                    numbers = re.findall(r'\d+', line_clean)
                    if len(numbers) == 3:
                        try:
                            cotizadas = int(numbers[0])
                            descontadas = int(numbers[1]) 
                            reintegradas = int(numbers[2])
                            
                            print(f"Candidato línea {i}: '{line_clean}' -> {cotizadas}, {descontadas}, {reintegradas}")
                            
                            # Validar que tiene sentido
                            if (cotizadas >= descontadas >= reintegradas >= 0 and 
                                cotizadas <= 10000 and 
                                not (cotizadas <= 31 and descontadas <= 12 and reintegradas >= 2020)):
                                
                                print(f"✓ Detalle encontrado: {cotizadas}, {descontadas}, {reintegradas}")
                                return [cotizadas, descontadas, reintegradas]
                                
                        except ValueError:
                            continue
        
        print("⚠️ No se encontró el detalle de semanas")
        return [0, 0, 0]
        
    except Exception as e:
        print(f"Error extrayendo detalle de semanas: {e}")
        return [0, 0, 0]

def extract_employers_from_text(full_text):
    """Extrae empleadores usando regex mejorado"""
    employers = []
    
    try:
        print("=== EXTRAYENDO EMPLEADORES ===")
        
        # Patrón mejorado para capturar empleadores
        pattern = r'Nombre del patrón\s+([^\n\r]+?)\s+Registro Patronal\s+([A-Z0-9]+)\s+Entidad federativa\s+([^\n\r]+?)\s+Fecha de alta\s+(\d{2}/\d{2}/\d{4})\s+Fecha de baja\s+(\d{2}/\d{2}/\d{4}|Vigente)\s+Salario Base de Cotización[^$]*\$\s*([\d,.]+)'
        
        matches = re.finditer(pattern, full_text, re.DOTALL)
        
        for match in matches:
            try:
                patron = match.group(1).strip()
                registro = match.group(2).strip()
                estado = match.group(3).strip()
                fecha_alta = match.group(4).strip()
                fecha_baja = match.group(5).strip()
                salario_str = match.group(6).strip()
                
                print(f"Procesando empleador: {patron}")
                
                # Procesar salario
                try:
                    salario = float(salario_str.replace(',', ''))
                except:
                    salario = 0.0
                
                # Procesar fechas
                try:
                    fa = parsero(fecha_alta)
                except:
                    fa = fecha_alta
                
                if fecha_baja == "Vigente":
                    fb = "Vigente"
                else:
                    try:
                        fb = parsero(fecha_baja)
                    except:
                        fb = fecha_baja
                
                employer = {
                    'p': patron,
                    'rp': registro,
                    'state': fixState(estado),
                    'fa': fa,
                    'fb': fb,
                    'sbc': salario,
                    'movimientos': []
                }
                
                employers.append(employer)
                print(f"✓ Empleador agregado: {patron}")
                
            except Exception as e:
                print(f"Error procesando empleador: {e}")
                continue
        
        print(f"Total empleadores extraídos: {len(employers)}")
        return employers
        
    except Exception as e:
        print(f"Error en extract_employers_from_text: {e}")
        return []

def extract_basic_info(full_text):
    """Extrae información básica del PDF"""
    try:
        print("=== EXTRAYENDO INFORMACIÓN BÁSICA ===")
        
        nss_real = ''
        curp_sc = ''
        nombre = ''
        
        # Buscar NSS
        nss_match = re.search(r"NSS:\s*([0-9]{10,11})", full_text)
        if nss_match:
            nss_real = nss_match.group(1).strip()
            print(f"NSS encontrado: {nss_real}")
        
        # Buscar CURP
        curp_match = re.search(r"CURP:\s*([A-Z0-9]{18})", full_text)
        if curp_match:
            curp_sc = curp_match.group(1).strip()
            print(f"CURP encontrado: {curp_sc}")
        
        # Buscar nombre
        nombre_patterns = [
            r"NSS:\s*[0-9]+\s*([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]+?)(?=\s*CURP)",
            r"([A-ZÁÉÍÓÚÑ]{2,}\s+[A-ZÁÉÍÓÚÑ]{2,}\s+[A-ZÁÉÍÓÚÑ]{2,}(?:\s+[A-ZÁÉÍÓÚÑ]{2,})?)"
        ]
        
        for pattern in nombre_patterns:
            nombre_matches = re.finditer(pattern, full_text)
            for nombre_match in nombre_matches:
                potential_name = nombre_match.group(1).strip()
                
                # Limpiar nombre
                unwanted_texts = [
                    "DD MM YYYY", "Tu detalle de semanas cotizadas", "NSS:", "CURP:", 
                    "Total de semanas cotizadas", "Instituto Mexicano del Seguro Social"
                ]
                
                for unwanted in unwanted_texts:
                    potential_name = potential_name.replace(unwanted, "")
                
                potential_name = re.sub(r'\s+', ' ', potential_name).strip()
                
                # Verificar que el nombre tiene sentido
                if (len(potential_name) > 5 and 
                    len(potential_name) < 100 and
                    not re.search(r'\d', potential_name) and
                    len(potential_name.split()) >= 2):
                    
                    nombre = potential_name
                    print(f"Nombre encontrado: {nombre}")
                    break
            
            if nombre:
                break
        
        return nss_real, curp_sc, nombre
        
    except Exception as e:
        print(f"Error extrayendo información básica: {e}")
        return '', '', ''

def process_simplified_format(pdf):
    """Procesa PDFs en formato simplificado - VERSIÓN FINAL"""
    try:
        print("\n=== INICIANDO PROCESAMIENTO SIMPLIFICADO ===")
        
        # Extraer todo el texto del PDF
        full_text = ""
        for page in pdf.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            except Exception as e:
                print(f"Error extrayendo página: {e}")
                continue
        
        print(f"Texto extraído: {len(full_text)} caracteres")
        
        # Extraer información básica
        nss_real, curp_sc, nombre = extract_basic_info(full_text)
        
        # Extraer detalle de semanas
        detalle_semanas = extract_weeks_detail(full_text)
        
        # Extraer total de semanas (TSC)
        total_semanas = extract_total_weeks(full_text)
        
        print(f"=== RESUMEN FINAL ===")
        print(f"NSS: {nss_real}")
        print(f"CURP: {curp_sc}")
        print(f"Nombre: {nombre}")
        print(f"TSC (Total): {total_semanas}")
        print(f"Detalle - Cotizadas: {detalle_semanas[0]}, Descontadas: {detalle_semanas[1]}, Reintegradas: {detalle_semanas[2]}")
        
        # Extraer empleadores
        employers = extract_employers_from_text(full_text)
        print(f"Empleadores: {len(employers)}")
        
        # Generar nombres alternativos
        nombres_field = nombre
        if nombre:
            partes = nombre.split()
            if len(partes) >= 3:
                nombres_field = f"{partes[-1]} {' '.join(partes[:-1])}"
        
        # Estructura final
        s_c = {
            "Nombre": nombre,
            "Nombres": nombres_field,
            "created_at": datetime.now(),
            "curp_sc": [curp_sc] if curp_sc else [],
            "detalle_semanas": {
                'semanas_cotizadas': detalle_semanas[0],
                'semanas_descontadas': detalle_semanas[1], 
                'semanas_reintegradas': detalle_semanas[2]
            },
            "device": "",
            "job_cotizations": employers,
            "nss_final": nss_real,
            "nss_real": [nss_real] if nss_real else [],
            "rw_data": {
                "browser-scraper": "Para continuar con su trámite le hemos enviado una liga de confirmación a su correo electrónico",
                "requests-scraper": "",
                "e-visor": "",
                "app-requests-scraper": ""
            },
            "source": "browser-web",
            "tsc": total_semanas
        }
        
        return s_c
        
    except Exception as e:
        print(f"Error en process_simplified_format: {e}")
        import traceback
        traceback.print_exc()
        return None

def leyendopdf(pdf):
    """Función principal que procesa el PDF"""
    try:
        print("=== INICIANDO PROCESAMIENTO PDF ===")
        
        result = process_simplified_format(pdf)
        
        if result:
            print("\n=== PROCESAMIENTO EXITOSO ===")
            print(f"Nombre: {result.get('Nombre', 'N/A')}")
            print(f"CURP: {result.get('curp_sc', ['N/A'])[0] if result.get('curp_sc') else 'N/A'}")
            print(f"NSS: {result.get('nss_final', 'N/A')}")
            print(f"TSC: {result.get('tsc', 'N/A')}")
            print(f"Empleadores: {len(result.get('job_cotizations', []))}")
            print(f"Detalle - Cotizadas: {result.get('detalle_semanas', {}).get('semanas_cotizadas', 'N/A')}")
            print(f"Detalle - Descontadas: {result.get('detalle_semanas', {}).get('semanas_descontadas', 'N/A')}")
            print(f"Detalle - Reintegradas: {result.get('detalle_semanas', {}).get('semanas_reintegradas', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"Error procesando PDF: {e}")
        import traceback
        traceback.print_exc()
        return None
    
class PDFProcessor:
    
    def __init__(self, path, mongo_url):
        
        self.path = path
        client = MongoClient(mongo_url)
        db = client["Main_User"]
        self.NBC = db["Nueva_Base_Central"]
        self.RW = db["Registro_works"]
        self.IMSS = db["imss"]
        self.slp = client["Mini_Base_Central"]['sl_pendiente']
        
    def process_pdf(self, pdf_path):
        
        curp = self.extract_curp(pdf_path)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                data = leyendopdf(pdf)
                print(f"Processed {pdf_path} for CURP: {curp} and found data")
                
            id = self.getID(curp.strip())
            # ✅ Pass CURP to updateDB for queue updates
            self.updateDB(id, data, curp)

            return data
        except Exception as e:
                print(f"Error processing {pdf_path}: {e}")
                traceback.print_exc()
                return None

    def extract_device_from_rw(self, rw_id):
        """Extract device_id from RW Device field"""
        try:
            rw_collection = self.RW
            rw_doc = rw_collection.find_one({"ID": rw_id})
            
            if rw_doc and rw_doc.get("Device"):
                return rw_doc["Device"]
                
            return None
        except Exception as e:
            print(f"Error extracting device_id from RW {rw_id}: {e}")
            return None

    def release_device_from_pdf_processor(self, device_id, task_id):
        """Release device after PDF processing"""
        try:
            # Connect to devices collection  
            client = MongoClient(MONGO_PRINCIPAL)
            devices_collection = client['Mini_Base_Central']['devices']
            
            result = devices_collection.update_one(
                {"device": device_id, "process": "IAD"},
                {
                    "$set": {"available": True, "updated_at": datetime.now()},
                    "$unset": {"current_task": "", "task_id": "", "task_start_time": ""}
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ [PDF-IAD] Device {device_id} released after PDF processing (task: {task_id})")
            else:
                print(f"⚠️ [PDF-IAD] Could not release device {device_id} (task: {task_id})")
                
            client.close()
                
        except Exception as e:
            print(f"❌ [PDF-IAD] Error releasing device {device_id}: {e}")

    def extract_curp(self, pdf_path):
        """
        Extracts the CURP from a filename like CURPXXXXXXX.pdf.
        """
        filename = os.path.basename(pdf_path)
        if filename.lower().endswith('.pdf'):
            curp = filename[:-4] 
        else:
            curp = filename
        return curp
    
    # ✅ UPDATED: Modified updateDB to include queue updates and accept curp parameter
    def updateDB(self, id, data, curp):
        
        nbc_collection = self.NBC
        rw_collection = self.RW
        imss_collection = self.IMSS
        slp_collection  = self.slp
        
        nbc_doc = nbc_collection.find_one({"_id": id})
        if nbc_doc: 
            id_rw = nbc_doc.get("Work_dic_imss", {}).get("ID")
            
            if id_rw:
                print(id_rw)
                rw_doc = rw_collection.find_one({"ID": id_rw})
                if rw_doc:
                    print(f"Condition: {rw_doc['Condition']}")
                
                    print("Would insert here")
                    
                    data["source"] = DEVICE
                    data["created_at"] = datetime.now()
                    success_message = f"APP-DFL-PRIYANSH {datetime.now()}"
                    data["message"] = success_message
                    
                    # Insert IMSS data
                    imss_collection.update_one(
                        {"_id": id},
                        {"$set": data}, 
                        upsert=True
                    )
                    
                    # Update NBC
                    nbc_collection.update_one(
                        {"_id": id},
                        {"$set": {
                            "searchlook.imss": datetime.now(),
                            "searchlook.dependientes_r": datetime.now(),
                            "nss.nss": data["nss_final"],
                            "nss.nss_final": data["nss_final"],
                            "nss.status": "s",
                            "imss": {"status": "s", "date": datetime.now()}
                        }}
                    )
                    
                    # Update RW with condition 1 (SUCCESS)
                    rw_collection.update_one(
                        {"ID": id_rw},
                        {"$set": {
                            "Name": "IMSS_App_DFL",
                            "Instance": DEVICE,
                            "Condition": 1,  # ✅ SUCCESS CONDITION
                            "Status": "Complete", 
                            "f_date": datetime.now(),
                            "Message": success_message
                        }}
                    )
                    
                    # ✅ NEW: Update queue document for condition 1 (success)
                    try:
                        update_queue_document_for_condition1(
                            rw_id=id_rw,
                            curp=curp, 
                            message=success_message
                        )
                        print(f"✅ Queue document updated for successful PDF processing: {curp}")
                    except Exception as queue_error:
                        print(f"❌ Failed to update queue document: {queue_error}")
                    
                    # ✅ ENHANCED: Release device after successful processing
                    try:
                        device_id = self.extract_device_from_rw(id_rw)
                        if device_id:
                            self.release_device_from_pdf_processor(device_id, id_rw)
                        else:
                            print(f"Could not extract device_id for RW: {id_rw}")
                    except Exception as e:
                        print(f"Error releasing device after PDF processing: {e}")
                    
                    print("Inserted IMSS: '_id':", id)
                    print("Inserted RW  : 'ID':", id_rw)
                    
                    # Update NSS job if exists
                    try:
                        id_rw_nss = nbc_doc.get("Work_dic_NSS", {}).get("ID")
                        if id_rw_nss:
                            rw_collection.update_one(
                                {"ID": id_rw_nss},
                                {"$set": {
                                    "Name" : "NSS_App_DFL",
                                    "Instance": DEVICE,
                                    "Condition": 1, 
                                    "Status": "Complete", 
                                    "f_date": datetime.now(),
                                    "Message": success_message
                                }}
                            )
                    except Exception as nss_error:
                        print(f"No NSS job or error updating: {nss_error}")

                    # Update NBC with additional fields
                    nbc_collection.update_one(
                        {"_id": id},
                        {"$set": {
                            "searchlook.pep": "p",
                            "searchlook.nlf": "p",
                            "searchlook.lname_bl": "p"
                        }}
                    )
                    
                    print("Updating slp")
                    last_slp = slp_collection.find_one(
                                                {"_id_NBC": id},
                                                sort=[("inserted", -1)]
                                            )
                    if last_slp:
                        slp_collection.update_one({
                                                "_id":last_slp["_id"]},
                                                    {"$set":{
                                                        "nlf":"p",
                                                        "pep":"p",
                                                        "lname_bl":"p"
                                                            }})
                    else:
                        print(f"No slp record found for _id_NBC: {id}")
                        
                    slp_collection.update_many(
                                        {"_id_NBC": id,
                                            "finished":False},
                                            {"$set":{
                                                "nlf":"p",
                                                "pep":"p",
                                                "lname_bl":"p"
                                                }}
                                            )
                    print("updated slp")
                else:
                    print("RW document not found")
            else:
                print(f"This one doesn't ok IMSS work")
        else:
            print(f"This one doesn't have NBC")
    
    def getID(self, curp):
        docs = list(self.NBC.find({'curp.curp': curp}))
        if not docs:
            return None

        for doc in docs:
            searchlook_imss = doc.get('searchlook', {}).get('imss')
            if searchlook_imss in ['p1', 'p']:
                return doc['_id']

        return docs[0]['_id']

    def getPdfsList(self):
        """Returns a list of all PDF file paths in self.path (recursive) that are not marked as readed."""
        pdfs = []
        for dirpath, _, filenames in os.walk(self.path):
            for f in filenames:
                if f.lower().endswith('.pdf') and not f.lower().endswith('_readed.pdf'):
                    pdfs.append(os.path.join(dirpath, f))
        return pdfs

# ✅ KEEP: All your existing processing functions (extract_total_weeks, extract_weeks_detail, etc.)
def extract_total_weeks(full_text):
    """Extrae el total de semanas cotizadas del encabezado - VERSIÓN DEFINITIVA"""
    try:
        print("=== EXTRAYENDO TOTAL DE SEMANAS (TSC) ===")
        
        # Extraer las primeras líneas donde está el encabezado
        lines = full_text.split('\n')
        
        # MÉTODO 1: Buscar el patrón exacto del encabezado
        # El formato es siempre: número grande en el encabezado después de "Total de semanas cotizadas"
        print("\n--- MÉTODO 1: Buscar patrón del encabezado ---")
        
        for i, line in enumerate(lines[:40]):  # Solo buscar en las primeras 40 líneas
            if "Total de semanas cotizadas" in line:
                print(f"Encontrado 'Total de semanas cotizadas' en línea {i}: {line}")
                
                # Buscar en las siguientes líneas el número
                for j in range(i+1, min(len(lines), i+8)):
                    next_line = lines[j].strip()
                    print(f"  Revisando línea {j}: '{next_line}'")
                    
                    # Buscar línea que solo contenga un número
                    if re.match(r'^\s*(\d{1,4})\s*$', next_line):
                        total = int(next_line)
                        # Validar que sea un total válido (no fecha)
                        if 1 <= total <= 5000 and total != 2025 and total != 2024:
                            print(f"✓ Total encontrado: {total}")
                            return total
        
        # MÉTODO 2: Buscar en la cadena original del pie de página que siempre contiene el total
        print("\n--- MÉTODO 2: Buscar en cadena original ---")
        
        # Buscar el patrón de la cadena original que siempre tiene el formato:
        # "Número total de semanas cotizadas:XX"
        cadena_pattern = re.search(r'Número total de semanas cotizadas:(\d{1,4})', full_text)
        if cadena_pattern:
            total = int(cadena_pattern.group(1))
            print(f"✓ Total encontrado en cadena original: {total}")
            return total
        
        # MÉTODO 3: Buscar el patrón específico en el NSS/CURP/Total
        print("\n--- MÉTODO 3: Buscar patrón NSS/CURP/Total ---")
        
        # Buscar después de encontrar NSS y CURP
        nss_found = -1
        curp_found = -1
        
        for i, line in enumerate(lines[:30]):
            if "NSS:" in line:
                nss_found = i
                print(f"NSS encontrado en línea {i}")
            elif "CURP:" in line and nss_found != -1:
                curp_found = i
                print(f"CURP encontrado en línea {i}")
                
                # Buscar el número en las siguientes líneas
                for j in range(i+1, min(len(lines), i+6)):
                    check_line = lines[j].strip()
                    if re.match(r'^\s*(\d{1,4})\s*$', check_line):
                        total = int(check_line)
                        if 1 <= total <= 5000:
                            print(f"✓ Total encontrado después de CURP: {total}")
                            return total
                break
        
        # MÉTODO 4: Buscar números aislados en el encabezado excluyendo fechas
        print("\n--- MÉTODO 4: Búsqueda de números aislados ---")
        
        for i, line in enumerate(lines[:25]):
            line_clean = line.strip()
            if re.match(r'^\s*(\d{1,4})\s*$', line_clean):
                total = int(line_clean)
                print(f"Candidato en línea {i}: {total}")
                
                # Verificar que no sea fecha
                context_valid = True
                for k in range(max(0, i-2), min(len(lines), i+3)):
                    context_line = lines[k].lower()
                    if any(word in context_line for word in ['fecha', 'dd', 'mm', 'yyyy', '/', '2024', '2025']):
                        context_valid = False
                        break
                
                if context_valid and 1 <= total <= 5000:
                    # Verificar que esté en el contexto correcto (después de datos personales)
                    found_personal_data = False
                    for k in range(max(0, i-10), i):
                        if any(word in lines[k] for word in ['NSS:', 'CURP:', 'Total de semanas']):
                            found_personal_data = True
                            break
                    
                    if found_personal_data:
                        print(f"✓ Total encontrado por contexto: {total}")
                        return total
        
        print("⚠️ No se encontró el total de semanas")
        return 0
        
    except Exception as e:
        print(f"Error extrayendo total de semanas: {e}")
        return 0

# ... (keep all other existing functions like extract_weeks_detail, extract_employers_from_text, etc.) ...

def process_simplified_format(pdf):
    """Procesa PDFs en formato simplificado - VERSIÓN FINAL"""
    try:
        print("\n=== INICIANDO PROCESAMIENTO SIMPLIFICADO ===")
        
        # Extraer todo el texto del PDF
        full_text = ""
        for page in pdf.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            except Exception as e:
                print(f"Error extrayendo página: {e}")
                continue
        
        print(f"Texto extraído: {len(full_text)} caracteres")
        
        # Extraer información básica
        nss_real, curp_sc, nombre = extract_basic_info(full_text)
        
        # Extraer detalle de semanas
        detalle_semanas = extract_weeks_detail(full_text)
        
        # Extraer total de semanas (TSC)
        total_semanas = extract_total_weeks(full_text)
        
        print(f"=== RESUMEN FINAL ===")
        print(f"NSS: {nss_real}")
        print(f"CURP: {curp_sc}")
        print(f"Nombre: {nombre}")
        print(f"TSC (Total): {total_semanas}")
        print(f"Detalle - Cotizadas: {detalle_semanas[0]}, Descontadas: {detalle_semanas[1]}, Reintegradas: {detalle_semanas[2]}")
        
        # Extraer empleadores
        employers = extract_employers_from_text(full_text)
        print(f"Empleadores: {len(employers)}")
        
        # Generar nombres alternativos
        nombres_field = nombre
        if nombre:
            partes = nombre.split()
            if len(partes) >= 3:
                nombres_field = f"{partes[-1]} {' '.join(partes[:-1])}"
        
        # Estructura final
        s_c = {
            "Nombre": nombre,
            "Nombres": nombres_field,
            "created_at": datetime.now(),
            "curp_sc": [curp_sc] if curp_sc else [],
            "detalle_semanas": {
                'semanas_cotizadas': detalle_semanas[0],
                'semanas_descontadas': detalle_semanas[1], 
                'semanas_reintegradas': detalle_semanas[2]
            },
            "device": "",
            "job_cotizations": employers,
            "nss_final": nss_real,
            "nss_real": [nss_real] if nss_real else [],
            "rw_data": {
                "browser-scraper": "Para continuar con su trámite le hemos enviado una liga de confirmación a su correo electrónico",
                "requests-scraper": "",
                "e-visor": "",
                "app-requests-scraper": ""
            },
            "source": "browser-web",
            "tsc": total_semanas
        }
        
        return s_c
        
    except Exception as e:
        print(f"Error en process_simplified_format: {e}")
        import traceback
        traceback.print_exc()
        return None

def leyendopdf(pdf):
    """Función principal que procesa el PDF"""
    try:
        print("=== INICIANDO PROCESAMIENTO PDF ===")
        
        result = process_simplified_format(pdf)
        
        if result:
            print("\n=== PROCESAMIENTO EXITOSO ===")
            print(f"Nombre: {result.get('Nombre', 'N/A')}")
            print(f"CURP: {result.get('curp_sc', ['N/A'])[0] if result.get('curp_sc') else 'N/A'}")
            print(f"NSS: {result.get('nss_final', 'N/A')}")
            print(f"TSC: {result.get('tsc', 'N/A')}")
            print(f"Empleadores: {len(result.get('job_cotizations', []))}")
            print(f"Detalle - Cotizadas: {result.get('detalle_semanas', {}).get('semanas_cotizadas', 'N/A')}")
            print(f"Detalle - Descontadas: {result.get('detalle_semanas', {}).get('semanas_descontadas', 'N/A')}")
            print(f"Detalle - Reintegradas: {result.get('detalle_semanas', {}).get('semanas_reintegradas', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"Error procesando PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    
    mongo_url = MONGO_PRINCIPAL
    path = PDF_PATH
    processor = PDFProcessor(path, mongo_url)

    processed_dir = os.path.abspath(os.path.join(path, "..", "pdf_processed"))
    os.makedirs(processed_dir, exist_ok=True)

    while True:
        pdfs = processor.getPdfsList()
        if not pdfs:
            print(f"[{str(datetime.now())}]No PDFs to process. Waiting...")

        for pdf_path in pdfs:
            data = processor.process_pdf(pdf_path)
            base, ext = os.path.splitext(os.path.basename(pdf_path))  
            dt_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{base}_{dt_str}_readed{ext}"
            dest_path = os.path.join(processed_dir, new_filename)

            shutil.move(pdf_path, dest_path)
            print(f"Movido y renombrado: {pdf_path} -> {dest_path}")
            curp = base     
            if data:
                print(f"Data extracted from {pdf_path}")
                mongo_logger.update_latest_log_by_curp_and_inbox(curp=curp, field_path="DB_insert Field_1", value=True)
                mongo_logger.update_latest_log_by_curp_and_inbox(curp=curp, field_path="DB_insert Field_2", value="PDF saved in database")
            else:
                print(f"Failed to extract data from {pdf_path}.")
            
        time.sleep(10)