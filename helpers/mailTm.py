# # mailTm.py

# mailTm.py
import os
import uuid
import time
import aiohttp
import asyncio
from logger import logger

BASE_URL = "https://api.mail.tm"


async def create_inbox(session, name=None):
    async with session.get(f"{BASE_URL}/domains") as resp:
        data = await resp.json()
        domain = data['hydra:member'][0]['domain']
    username = name or f"user{uuid.uuid4().hex[:8]}"
    email = f"{username}@{domain}"
    password = "Test@123456"

    async with session.post(f"{BASE_URL}/accounts", json={"address": email, "password": password}) as resp:
        if resp.status >= 400:
            logger.warning("Account may already exist, continuing.")
        else:
            await resp.json()

    logger.info(f"✅ Mail account created: {email}", extra={"curp": name or username})
    return email, password


async def get_token(session, email, password):
    async with session.post(f"{BASE_URL}/token", json={"address": email, "password": password}) as resp:
        resp.raise_for_status()
        data = await resp.json()
        token = data["token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info(f"✅ Authenticated to Mail.tm for {email}")
        return token


async def get_inbox_messages(session):
    async with session.get(f"{BASE_URL}/messages") as resp:
        resp.raise_for_status()
        data = await resp.json()
        return data.get("hydra:member", [])


async def wait_for_email(session, timeout=300, poll_interval=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        logger.info("⏳ Waiting for email...")
        messages = await get_inbox_messages(session)
        if messages:
            logger.info("📩 Email received.")
            return messages[0]['id']
        await asyncio.sleep(poll_interval)
    raise TimeoutError("❌ No email received within timeout")


async def get_email_attachment(session, curp, message_id):
    url = f"{BASE_URL}/messages/{message_id}"
    async with session.get(url) as resp:
        resp.raise_for_status()
        msg = await resp.json()

    subject = msg.get("subject", "(No Subject)")
    html = msg.get("html", "")
    if isinstance(html, list):
        html = "".join(html)

    attachments = msg.get("attachments", [])
    downloaded_files = []

    for att in attachments:
        att_id = att["id"]
        filename = att["filename"]
        download_url = f"{BASE_URL}/messages/{message_id}/attachments/{att_id}"
        async with session.get(download_url) as att_resp:
            att_resp.raise_for_status()
            content = await att_resp.read()
            downloaded_files.append({
                "filename": filename,
                "content": content
            })

    return {
        "subject": subject,
        "html": html,
        "attachment": downloaded_files[0] if downloaded_files else None  # Contains `content` in memory
    }
