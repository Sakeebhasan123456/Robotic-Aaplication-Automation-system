import os
import time
import pymongo
import asyncio
import aiohttp
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import re
# import email
from email import message_from_bytes
from logger import logger


# Mailtrap API credentials (you can move these to env vars if needed)
API_TOKEN =  ""   
ACCOUNT_ID = ""                                   
PROJECT_ID = ""


# Main function to create inbox
async def create_inbox(name):
    
    url = f"https://mailtrap.io/api/accounts/{ACCOUNT_ID}/projects/{PROJECT_ID}/inboxes"
    payload = {"inbox": {"name": name}}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Api-Token": API_TOKEN
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                logger.info(f"Created inbox '{name}' successfully.", extra={"curp": name})
                return data
    except Exception as e:
        logger.error(f"Failed to create inbox '{name}': {e}", extra={"curp": name})
        return {"error": str(e)}
    
    
async def delete_inbox(inbox_id):
    url = f"https://mailtrap.io/api/accounts/{ACCOUNT_ID}/inboxes/{inbox_id}"
    headers = {
        "Accept": "application/json",
        "Api-Token": API_TOKEN,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                return data
    except Exception as e:
        # logger.error(f"Failed to delete inbox {inbox_id}: {e}")
        return {"error": str(e)}


async def delete_all_inbox():
    url = f"https://mailtrap.io/api/accounts/{ACCOUNT_ID}/projects/{PROJECT_ID}/inboxes"
    headers = {
        "Accept": "application/json",
        "Api-Token": API_TOKEN,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                # data is expected to be a list of inboxes for this project
                for inbox in data:
                    inbox_id = inbox.get("id")
                    if inbox_id:
                        await delete_inbox(inbox_id)
    except Exception as e:
        logger.error(f"Failed to delete all inboxes: {e}")
        
async def get_inbox_messages(inbox_id):
    url = f"https://mailtrap.io/api/accounts/{ACCOUNT_ID}/inboxes/{inbox_id}/messages"

    headers = {
        "Accept": "application/json",
        "Api-Token": API_TOKEN
    }

    async with aiohttp.ClientSession() as session:
        # logger.info("Fetching inbox messages from: %s", url)
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                # logger.error("Failed to fetch inbox messages: %s", await response.text())
                return []
            return await response.json()


async def get_email_attachment(eml_link):
    async with aiohttp.ClientSession() as session:
        async with session.get(eml_link) as response:
            raw_email = await response.read()
            msg = message_from_bytes(await response.read())  #message_from_bytes(raw_email)

            subject = msg.get('Subject')
            html = None
            attachment = None

            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    html = part.get_payload(decode=True).decode('utf-8', errors='ignore')

                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename and filename.lower().endswith('.pdf'):
                        attachment = part.get_payload(decode=True)

            return {
                "subject": subject,
                "html": html,
                "attachment": attachment
            }
