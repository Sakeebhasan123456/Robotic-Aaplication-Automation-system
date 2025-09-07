# -*- coding: utf-8 -*-
import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="ignore")

from bson.objectid import ObjectId
from pymongo import MongoClient
from ReadPDF import leyendopdf
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path
import pandas as pd
import pdfplumber
import warnings
import time
import json
import glob
import logging
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pdf_processing.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

MONGO_URI = "mongodb://carlos_readonly:p13CCTjtXUaqf1xQyyR6KpuRtYzrsw9R@principal.mongodb.searchlook.mx:27017/admin"


def get_database_connection():
    """Establece la conexión con la base de datos MongoDB."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Probar la conexión
        client.admin.command("ping")
        return client.Main_User, client
    except Exception as e:
        logger.error(f"No se pudo conectar a la base de datos: {e}")
        return None, None


def flatten_dict(d, parent_key="", sep="."):
    """Flattens a dictionary to count total fields"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def select_best_document(documents):
    """
    Selects the best document based on priority criteria:
    1. The one with most fields (applies to ALL documents)
    2. If tied, the one with the most recent date in 'Work_dic_imss.last_i' (datetime)
    3. If tied, the one with 'searchlook.imss' = 'p1' or 'p'
    """
    if not documents:
        return None

    logger.info(f"Seleccionando el mejor documento entre {len(documents)} candidatos")

    # PRIORITY 1: Find documents with maximum number of fields
    docs_with_field_count = [(doc, len(flatten_dict(doc))) for doc in documents]
    max_fields = max(docs_with_field_count, key=lambda x: x[1])[1]

    logger.info(f"Máximo número de campos encontrado: {max_fields}")

    # Get all documents that have the maximum number of fields
    best_docs = [doc for doc, count in docs_with_field_count if count == max_fields]
    logger.info(f"Documentos con máximo número de campos: {len(best_docs)}")

    # If only one document has max fields, return it
    if len(best_docs) == 1:
        logger.info("Solo un documento tiene el máximo de campos, seleccionándolo")
        return best_docs[0]

    # PRIORITY 2: Among docs with max fields, prefer those with recent dates
    docs_with_dates = []
    for doc in best_docs:
        work_dic_imss = doc.get("Work_dic_imss", {}).get("last_i")
        if work_dic_imss and isinstance(work_dic_imss, datetime):
            docs_with_dates.append((doc, work_dic_imss))

    logger.info(
        f"Documentos con fechas válidas en Work_dic_imss.last_i: {len(docs_with_dates)}"
    )

    # If we have docs with dates, return the most recent one
    if docs_with_dates:
        best_doc = max(docs_with_dates, key=lambda x: x[1])[0]
        logger.info("Seleccionado documento con fecha más reciente")
        return best_doc

    # PRIORITY 3: Among remaining docs, prefer 'p1' or 'p'
    docs_with_priorities = []
    for doc in best_docs:
        searchlook_imss = doc.get("searchlook", {}).get("imss")
        if searchlook_imss in ["p1", "p"]:
            docs_with_priorities.append(doc)

    logger.info(
        f"Documentos con searchlook.imss 'p1' o 'p': {len(docs_with_priorities)}"
    )

    if docs_with_priorities:
        logger.info("Seleccionado documento con prioridad searchlook")
        return docs_with_priorities[0]  # Already filtered by max fields

    # Fallback: return first of the best docs
    logger.info("Seleccionado primer documento como fallback")
    return best_docs[0]


def find_best_document_by_curp(nbc, curp):
    """
    Busca todos los documentos con el CURP dado y selecciona el mejor según los criterios.
    Retorna el documento seleccionado o None si no encuentra ninguno.
    """
    try:
        logger.info(f"Buscando documentos en Nueva_Base_Central para CURP: {curp}")

        # Buscar todos los documentos con este CURP
        documents = list(nbc.find({"curp.curp": curp}))

        if not documents:
            logger.error(
                f"No se encontraron documentos en Nueva_Base_Central para curp.curp: {curp}"
            )
            documents = list(nbc.find({"curp.Curps_asociados": curp}))
            if not documents:
                logger.error(
                    f"No se encontraron documentos en Nueva_Base_Central para curp.Curps_asociados: {curp}"
                )
                return None

        logger.info(f"Se encontraron {len(documents)} documento(s) para CURP: {curp}")

        # Si solo hay uno, retornarlo directamente
        if len(documents) == 1:
            logger.info("Solo un documento encontrado, seleccionándolo")
            curp = documents[0].get("curp", {}).get("curp", curp)
            return documents[0], curp

        # Si hay múltiples, seleccionar el mejor
        logger.info(
            "Múltiples documentos encontrados, aplicando criterios de selección"
        )
        best_document = select_best_document(documents)

        if best_document:
            logger.info(f"Mejor documento seleccionado: {best_document['_id']}")
            curp = best_document.get("curp", {}).get("curp", curp)

        return best_document, curp

    except Exception as e:
        logger.error(f"Error buscando documento por CURP {curp}: {e}")
        import traceback

        traceback.print_exc()
        return None


def validate_curp(curp):
    """Valida que el CURP tenga el formato correcto"""
    if not curp or len(curp) != 18:
        return False

    # Patrón básico de CURP
    curp_pattern = r"^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$"
    return bool(re.match(curp_pattern, curp))


def validate_nss(nss):
    """Valida que el NSS tenga el formato correcto"""
    if not nss:
        return False

    # NSS debe tener 10 u 11 dígitos
    return bool(re.match(r"^[0-9]{10,11}$", nss))


def update_nueva_base_central(database, document_id, nss_real):
    """Actualiza el documento en Nueva_Base_Central usando el _id del documento seleccionado"""
    try:
        logger.info(f"Actualizando Nueva_Base_Central para documento ID: {document_id}")

        nbc = database["Nueva_Base_Central"]
        current_date = datetime.now()

        # Verificar que el documento existe
        document = nbc.find_one({"_id": document_id})
        if not document:
            logger.error(
                f"No se encontró documento en Nueva_Base_Central con ID: {document_id}"
            )
            return False

        logger.info(f"Documento encontrado en Nueva_Base_Central: {document_id}")

        # Verificar el estado actual de los campos
        existing_imss = document.get("imss")
        existing_nss = document.get("nss", {})
        existing_searchlook = document.get("searchlook", {})
        existing_work_dic_imss = document.get("Work_dic_imss", {})

        logger.info(f"Estado actual - imss: {existing_imss}")
        logger.info(f"Estado actual - nss: {existing_nss}")
        logger.info(
            f"Estado actual - searchlook.imss: {existing_searchlook.get('imss')}"
        )
        logger.info(f"Estado actual - Work_dic_imss: {existing_work_dic_imss}")

        # Preparar las actualizaciones base
        updates = {
            "$set": {
                "searchlook.imss": current_date,
                "Work_dic_imss.last_i": current_date,  # Actualizar last_i con la fecha de searchlook.imss
            }
        }

        # Actualizar NSS si existe la estructura
        if existing_nss:
            updates["$set"]["nss.nss"] = nss_real
            updates["$set"]["nss.status"] = "s"
        else:
            # Crear estructura NSS si no existe
            updates["$set"]["nss"] = {"nss": nss_real, "status": "s"}

        # Manejar el campo 'imss' según su estado actual
        if isinstance(existing_imss, str):
            # Si es string (como "p"), convertir a objeto
            updates["$set"]["imss"] = {"status": "s", "date": current_date}
            logger.info("Campo 'imss' convertido de string a objeto")
        elif isinstance(existing_imss, dict):
            # Si ya es objeto, solo actualizar campos
            updates["$set"]["imss.status"] = "s"
            updates["$set"]["imss.date"] = current_date
            logger.info("Campo 'imss' actualizado como objeto existente")
        else:
            # Si no existe, crear nuevo
            updates["$set"]["imss"] = {"status": "s", "date": current_date}
            logger.info("Campo 'imss' creado como nuevo objeto")

        logger.info(f"Actualizaciones a aplicar: {updates}")

        # Ejecutar la actualización usando el _id
        result = nbc.update_one({"_id": document_id}, updates)

        if result.modified_count > 0:
            logger.info(
                f"Nueva_Base_Central actualizada exitosamente para documento ID: {document_id}"
            )

            # Verificar la actualización
            updated_doc = nbc.find_one({"_id": document_id})
            logger.info(f"✓ Campo 'imss' después: {updated_doc.get('imss')}")
            logger.info(f"✓ Campo 'nss' después: {updated_doc.get('nss')}")
            logger.info(
                f"✓ Campo 'searchlook.imss' después: {updated_doc.get('searchlook', {}).get('imss')}"
            )
            logger.info(
                f"✓ Campo 'Work_dic_imss.last_i' después: {updated_doc.get('Work_dic_imss', {}).get('last_i')}"
            )

            return True
        else:
            logger.warning(
                f"No se modificó Nueva_Base_Central para documento ID: {document_id}"
            )
            return False

    except Exception as e:
        logger.error(f"Error actualizando Nueva_Base_Central: {e}")
        import traceback

        traceback.print_exc()
        return False


def create_registro_works(database, document_id, curp):
    """Crea un nuevo registro en Registro_works usando el documento seleccionado"""
    try:
        logger.info(
            f"Creando nuevo registro en Registro_works para documento ID: {document_id}"
        )

        registro_works = database["Registro_works"]
        nbc = database["Nueva_Base_Central"]
        current_date = datetime.now()

        # Buscar el documento específico por ID
        nbc_document = nbc.find_one({"_id": document_id})
        if not nbc_document:
            logger.error(
                f"No se encontró documento en Nueva_Base_Central con ID: {document_id}"
            )
            return False

        # Extraer información necesaria
        nbc_id = nbc_document["_id"]
        work_dic_imss = nbc_document.get("Work_dic_imss", {})
        imss_id = work_dic_imss.get("ID", "")

        logger.info(f"Información extraída de Nueva_Base_Central:")
        logger.info(f"  - NBC_id: {nbc_id}")
        logger.info(f"  - Work_dic_imss actual: {work_dic_imss}")

        logger.info("Work_dic_imss.ID no existe, creando uno nuevo...")

        # Convertir fecha a formato número: YYYYMMDDHHMMSS
        fecha_formato_numero = current_date.strftime("%Y%m%d%H%M%S")

        # Crear el ID en el formato: IMSS_{_id}_{fecha_numero}
        imss_id = f"IMSS_{nbc_id}_{fecha_formato_numero}"

        logger.info(f"Nuevo ID generado: {imss_id}")

        # Actualizar Nueva_Base_Central con el nuevo ID
        update_result = nbc.update_one(
            {"_id": document_id}, {"$set": {"Work_dic_imss.ID": imss_id}}
        )

        if update_result.modified_count > 0:
            logger.info("✓ Work_dic_imss.ID actualizado en Nueva_Base_Central")
        else:
            logger.warning(
                "⚠️ No se pudo actualizar Work_dic_imss.ID en Nueva_Base_Central"
            )

        # Crear las fechas con 1 segundo de diferencia
        i_date = current_date
        f_date = current_date + timedelta(seconds=1)

        # Crear el nuevo registro
        new_record = {
            "Name": "IMSS_MANUAL",
            "Instance": "IMSS_MANUAL_IL",
            "ID": imss_id,
            "Curp": curp,
            "NBC_id": nbc_id,
            "Condition": 1,
            "Status": "Complete",
            "i_date": i_date,
            "f_date": f_date,
            "Message": "Manual",
        }

        logger.info(f"Nuevo registro a insertar en Registro_works:")
        for key, value in new_record.items():
            logger.info(f"  - {key}: {value}")

        # Insertar el nuevo registro
        result = registro_works.insert_one(new_record)

        if result.inserted_id:
            logger.info(f"✓ Nuevo registro creado exitosamente en Registro_works")
            logger.info(f"  - ID insertado: {result.inserted_id}")
            logger.info(f"  - CURP: {curp}")
            logger.info(f"  - NBC_id: {nbc_id}")
            logger.info(f"  - IMSS ID: {imss_id}")
            logger.info(f"  - i_date: {i_date}")
            logger.info(f"  - f_date: {f_date}")
            return True
        else:
            logger.error(
                f"No se pudo insertar el registro en Registro_works para documento ID: {document_id}"
            )
            return False

    except Exception as e:
        logger.error(f"Error creando registro en Registro_works: {e}")
        import traceback

        traceback.print_exc()
        return False


def process_pdf_file(pdf_path, database, nbc, imss):
    """Procesa un archivo PDF individual y actualiza todas las colecciones necesarias"""
    try:
        logger.info(f"Procesando: {pdf_path}")

        # Validar que el archivo existe
        if not os.path.exists(pdf_path):
            logger.error(f"Archivo no encontrado: {pdf_path}")
            return False

        pdf = pdfplumber.open(pdf_path)
        data = leyendopdf(pdf)
        pdf.close()

        if data is None:
            logger.error(f"No se pudieron extraer datos de {pdf_path}")
            return False

        logger.info("Datos extraidos:")
        logger.info(data)

        # Validar estructura de datos
        if not isinstance(data.get("curp_sc"), list) or not data["curp_sc"]:
            logger.error(f"CURP no válida en la estructura de datos de {pdf_path}")
            return False

        # Extraer CURP del array para la búsqueda
        curp_for_search = (
            data["curp_sc"][0] if data["curp_sc"] and len(data["curp_sc"]) > 0 else ""
        )
        logger.info(f"CURP para búsqueda: {curp_for_search}")

        if not curp_for_search:
            logger.error(f"No se encontró CURP válida en {pdf_path}")
            return False

        # Extraer NSS para las actualizaciones posteriores
        nss_real = data.get("nss_real", [""])[0] if data.get("nss_real") else ""
        if not nss_real:
            nss_real = data.get("nss_final", "")

        logger.info(f"NSS extraído: {nss_real}")

        # PASO 0: Buscar y seleccionar el mejor documento
        logger.info("=== PASO 0: Buscando y seleccionando el mejor documento ===")
        best_document, curp_for_search = find_best_document_by_curp(
            nbc, curp_for_search
        )

        if not best_document:
            logger.error(
                f"No se encontró documento válido para CURP: {curp_for_search}"
            )
            return False

        document_id = best_document["_id"]
        logger.info(f"✓ Documento seleccionado: {document_id}")

        # PASO 1: Actualizar en la colección imss usando el _id del documento seleccionado
        logger.info("=== PASO 1: Actualizando colección IMSS ===")
        result = imss.update_one(
            {"_id": ObjectId(document_id)}, {"$set": data}, upsert=True
        )

        if result.modified_count > 0:
            logger.info(f"✓ Documento actualizado en colección 'imss' para {pdf_path}")
        elif result.upserted_id:
            logger.info(f"✓ Documento insertado en colección 'imss' para {pdf_path}")
        else:
            logger.info(
                f"✓ No se realizaron cambios en colección 'imss' para {pdf_path}"
            )

        # PASO 2: Actualizar Nueva_Base_Central usando el _id del documento seleccionado
        logger.info("=== PASO 2: Actualizando Nueva_Base_Central ===")
        success_nbc = update_nueva_base_central(database, document_id, nss_real)

        # PASO 3: Crear nuevo registro en Registro_works usando el _id del documento seleccionado
        logger.info("=== PASO 3: Creando nuevo registro en Registro_works ===")
        success_rw = create_registro_works(database, document_id, curp_for_search)

        # Verificar que todas las actualizaciones fueron exitosas
        logger.info("=== RESUMEN DE ACTUALIZACIONES ===")
        logger.info(f"Documento seleccionado: {document_id}")
        logger.info(f"Colección IMSS: ✓ EXITOSO")
        logger.info(f"Nueva_Base_Central: {'✓ EXITOSO' if success_nbc else '✗ FALLO'}")
        logger.info(
            f"Registro_works (NUEVO): {'✓ EXITOSO' if success_rw else '✗ FALLO'}"
        )

        if success_nbc and success_rw:
            logger.info(f"[PROCESAMIENTO COMPLETO EXITOSO] {pdf_path}")
            return True
        else:
            logger.warning(f"[PROCESAMIENTO PARCIALMENTE EXITOSO] {pdf_path}")
            return True  # Consideramos exitoso si al menos se insertó en 'imss'

    # except pdfplumber.PDFSyntaxError as e:
    #     logger.error(f"PDF corrupto o no válido {pdf_path}: {str(e)}")
    #     return False
    except Exception as e:
        logger.error(f"Error procesando {pdf_path}: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Función principal"""
    # Conectar a la base de datos
    database, client = get_database_connection()
    if database is None:
        logger.error("No se pudo establecer conexión con la base de datos")
        return

    try:
        imss = database["imss"]
        nbc = database["Nueva_Base_Central"]

        # Buscar todos los archivos PDF en la carpeta actual
        pdf_files = glob.glob("*.pdf")

        if not pdf_files:
            logger.info("No se encontraron archivos PDF en la carpeta actual")
            return

        logger.info(f"Se encontraron {len(pdf_files)} archivos PDF:")
        for pdf_file in pdf_files:
            logger.info(f"  - {pdf_file}")

        logger.info("Iniciando procesamiento...")

        # Procesar cada PDF secuencialmente
        successful = 0
        failed = 0

        for pdf_file in pdf_files:
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"PROCESANDO ARCHIVO: {pdf_file}")
                logger.info(f"{'='*80}")

                result = process_pdf_file(pdf_file, database, nbc, imss)
                if result:
                    successful += 1
                    logger.info(f"[ARCHIVO EXITOSO] {pdf_file}")
                else:
                    failed += 1
                    logger.error(f"[ARCHIVO FALLIDO] {pdf_file}")
            except Exception as e:
                failed += 1
                logger.error(f"[ERROR CRITICO] Procesando {pdf_file}: {e}")
                import traceback

                traceback.print_exc()

            logger.info("-" * 80)

        logger.info(f"\n{'='*80}")
        logger.info(f"RESUMEN FINAL DEL PROCESAMIENTO:")
        logger.info(f"{'='*80}")
        logger.info(f"[EXITOSOS] {successful} archivos procesados correctamente")
        logger.info(f"[FALLIDOS] {failed} archivos con errores")
        logger.info(f"[TOTAL] {len(pdf_files)} archivos procesados")
        logger.info(f"[TASA DE EXITO] {(successful/len(pdf_files)*100):.1f}%")
        logger.info(f"{'='*80}")

    finally:
        # Cerrar la conexión
        if client:
            client.close()
            logger.info("Conexión a base de datos cerrada correctamente")


if __name__ == "__main__":
    main()