from datetime import datetime
from pymongo import MongoClient, DESCENDING
from collections import OrderedDict
import pytz
import os
from logger import logger
from bson import ObjectId
from pymongo import MongoClient, DESCENDING

def updateRW(curp, condition, message, status, queue_document_id=None):
    """
    Update Registro_works and optionally update queue document
    
    Args:
        curp: CURP value
        condition: RW condition (1,2,3,4, or "Except")
        message: Message to store
        status: Status value
        queue_document_id: Optional ObjectId string for queue document update
    """
    mongo_uri = "mongodb://carlos_readonly:p13CCTjtXUaqf1xQyyR6KpuRtYzrsw9R@principal.mongodb.searchlook.mx:27017/admin"  
    db_name = "Main_User"
    collection_name = "Registro_works"

    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    collection = client[db_name][collection_name]

    # Find the latest document by 'f_date'
    query = {
        "Name": "IMSS_App_DFL",
        "Instance": "IMSS_App_DFL_Priyansh_01",
        "Curp": curp
    }

    latest_doc = collection.find_one(query, sort=[("i_date", DESCENDING)])
    if not latest_doc:
        raise ValueError(f"No document found for CURP: {curp} with given Name and Instance.")

    if condition == 2:
        nbc_id = latest_doc.get("NBC_id")
        if not nbc_id:
            print("NBC_id not found in latest Registro_works document.")

        nbc_collection = client[db_name]["Nueva_Base_Central"]
        nbc_collection.update_one(
            {"_id": nbc_id},
            {
                "$set": {
                    "imss": {"status": "subdelegacion", "date": datetime.now()},
                    "searchlook.imss": datetime.now()
                }
            }
        ) 

    if condition == 4:
        nbc_id = latest_doc.get("NBC_id")
        if not nbc_id:
            print("NBC_id not found in latest Registro_works document.")

        nbc_collection = client[db_name]["Nueva_Base_Central"]
        nbc_collection.update_one(
            {"_id": nbc_id},
            {
                "$set": {
                    "imss": {"status": "nf", "date": datetime.now()},
                    "searchlook.imss": datetime.now()
                }
            }
        ) 
    # Perform the Registro_works update
    update_fields = {
        "Condition": condition,
        "Message": message,
        "Status": status,
        "f_date": datetime.now()
    }

    result = collection.update_one(
        {"_id": latest_doc["_id"]},
        {"$set": update_fields}
    )

    if result.modified_count > 0:
        print(f"[✔] Successfully updated Registro_works for CURP: {curp}")
        logger.info(f"[RW-UPDATE] Updated Registro_works for CURP: {curp} with {update_fields}")
    else:
        print(f"[!] Registro_works found, but nothing was modified for CURP: {curp}")
        logger.info(f"[RW-UPDATE] Registro_works found, but nothing was modified for CURP: {curp}")

    queue_id_to_use = queue_document_id or latest_doc.get("queue_id")

    if queue_id_to_use:
        try:
            # Determine success based on condition
            success = condition in [1, 2, 3]  # success=true for conditions 1,2,3 | false for 4 or "Except"
            
            # Get queue collection (Mini_Base_Central database)
            queue_collection = client['Mini_Base_Central']['imss_queue_iad']
            
            queue_result = queue_collection.update_one(
                {"_id": ObjectId(queue_id_to_use)},
                {
                    "$set": {
                        "Status": "Complete",
                        "success": success,
                        "Message": message,  # Same message as RW
                        "completed_at": datetime.now()
                    }
                }
            )
            
            if queue_result.modified_count > 0:
                print(f"[✔] Successfully updated queue document {queue_id_to_use} with success={success}")
                logger.info(f"[QUEUE-UPDATE] Updated queue document {queue_id_to_use} for CURP {curp} with success={success}")
            else:
                print(f"[!] Queue document {queue_id_to_use} found but nothing was modified")
                logger.warning(f"[QUEUE-UPDATE] Queue document {queue_id_to_use} found but not modified for CURP {curp}")
                
        except Exception as queue_error:
            logger.error(f"❌ Failed to update queue document {queue_id_to_use} for CURP {curp}: {str(queue_error)}")
            print(f"[!] Warning: Queue document update failed: {str(queue_error)}")

    # Close the connection
    client.close()

class MongoLogger:
    def __init__(self, db_name="Scrapers", collection_name="IMSS_App_DFL",
                 mongo_uri="mongodb://main-user:Vk2M7KQBL9fGhjheh4jF4SqlRzAlf0c4@172.31.19.83:27017/admin"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        # self.tz = pytz.timezone("America/Mexico_City")

    def _generate_process_id(self):
        now = datetime.now()
        return f"IMSS-APP-DFL-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"

    def create_log(self, curp, scraper="IMSS_APP_Priyansh_01", dev="IMSS_App_Priyansh"):
        process_id = self._generate_process_id()
        now = datetime.now()

        log_doc = OrderedDict({
            "process_id": process_id,
            "Dev": dev,
            "Scraper": scraper,
            "Curp": curp,
            "start_date": now,
            "last_update": now
        })

        self.collection.insert_one(log_doc)
        return process_id

    def update_log(self, process_id, field_path, value):
        now = datetime.now()
        update_data = {
            field_path: value,
            "last_update": now
        }

        self.collection.update_one(
            {"process_id": process_id},
            {"$set": update_data}
        )
        
    def update_log_by_process_id(self, process_id, field_path, value):
        if not process_id:
           raise ValueError("'process_id' is required")

        now = datetime.now()
        update_data = {
            field_path: value,
            "last_update": now
        }

        result = self.collection.update_one(
            {"process_id": process_id},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ValueError(f"No document found with process_id: {process_id}")
        
    def update_latest_log_by_curp_and_inbox(self, curp, inbox_id=None, field_path=None, value=None, scraper="IMSS_APP_Priyansh_01"):
       
            if not curp:
               raise ValueError("'curp' is required")

        # if not isinstance(field_path, str) or '.' not in field_path:
        #     raise ValueError("Field path must be in the format 'Section.FieldName' (e.g., 'App_request.Field_1')")

        # Find the most recent log by curp, inbox_id and scraper
            query = {
            "Curp": curp,
            "Scraper": scraper
            }
            if inbox_id:
              query["inbox_id"] = inbox_id

            latest_log = self.collection.find_one(query, sort=[("start_date", -1)])
            if not latest_log:
                raise ValueError(f"No log entry found for CURP: {curp}, inbox_id: {inbox_id or 'N/A'}, and Scraper: {scraper}")

            process_id = latest_log["process_id"]

            # Update the field
            update_data = {
                field_path: value,
                "last_update": datetime.now()
            }

            self.collection.update_one(
                {"process_id": process_id},
                {"$set": update_data}
            )
