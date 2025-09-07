from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime, timezone
import pytz
import random

MONGO_URL = "mongodb://@principal.mongodb.searchlook.mx:27017/admin"
MONGO_DB = "Main_User"


client = MongoClient(MONGO_URL)
db = client[MONGO_DB]

Nueva_Base_Central = db["Nueva_Base_Central"]
Registro_works = db["Registro_works"]

def getCurp(nbc_id: str):
    """
    Retrieve the CURP string from a document in the 'Nueva_Base_Central' collection by its _id.

    Args:
        nbc_id (str): The string representation of the document's ObjectId.

    Returns:
        str or None: The CURP value if found, otherwise None.
    """
    doc = Nueva_Base_Central.find_one({"_id": ObjectId(nbc_id)})
    if doc and "curp" in doc and isinstance(doc["curp"], dict) and "curp" in doc["curp"]:
        return doc["curp"]["curp"]
    
    # Return None if not found or structure does not match
    return None

def getRwID(nbc_id : str):
    """
    Retrieve the 'ID' field from the 'Work_dic_imss' object in a document
    in the 'Nueva_Base_Central' collection by its _id.

    Args:
        nbc_id (str): The string representation of the document's ObjectId.

    Returns:
        str or None: The 'ID' value if found, otherwise None.
    """
    doc = Nueva_Base_Central.find_one({"_id": ObjectId(nbc_id)}, {"Work_dic_imss.ID": 1})

    return doc.get("Work_dic_imss", {}).get("ID") if doc else None

def updateRW(ID : str, condition : int, message : str, status : str):
    """
    Update the document with the given 'ID' field in 'Registro_works' with the provided fields.
    Returns True if a document was updated, False otherwise.

    Args:
        ID (str): The value of the document's 'ID' field.
        condition (int): Value to set in 'Condition'.
        message (str): Value to set in 'Message'.
        status (str): Value to set in 'Status'.

    Returns:
        bool: True if updated, False otherwise.
    """
    update_fields = {
        "Condition": condition,
        "Message": message,
        "Status": status,
        "f_date": datetime.now(mexico_tz)
    }

    mexico_tz = pytz.timezone("America/Mexico_City")
    result = Registro_works.update_one(
        {"ID": ID},
        {"$set": update_fields}
    )

    return result.modified_count > 0

def getNSS(nbc_id : str):
    """
    Retrieve the NSS string from a document in the 'Nueva_Base_Central' collection by its _id.

    Args:
        nbc_id (str): The string representation of the document's ObjectId.

    Returns:
        str or None: The NSS value if found, otherwise None.
    """
    doc = Nueva_Base_Central.find_one({"_id": ObjectId(nbc_id)})
    return doc.get("nss", {}).get("nss") if doc else None

def getRFC(nbc_id: str):
    """
    Retrieve the RFC string from a document in the 'Nueva_Base_Central' collection by its _id.

    Args:
        nbc_id (str): The string representation of the document's ObjectId.
        Nueva_Base_Central (Collection): The PyMongo Collection instance.

    Returns:
        str or None: The RFC value if found, otherwise None.
    """
    doc = Nueva_Base_Central.find_one({"_id": ObjectId(nbc_id)})
    return doc.get("rfc", {}).get("rfc") if doc else None


def getEmail(nbc_id : str):

    """
    Pending
    """
    
    return None





if __name__ == "__main__":
    
    # Test purposes 
    obj_id = "5c4918a7e358da090a05817e"
    
    print(getCurp(obj_id))
    print(getRwID(obj_id))
    print(getNSS(obj_id))
    print(getRFC(obj_id))