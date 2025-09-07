
# Robotic_Aaplication_Automation System

A Python-based automation and scraping tool designed to interact with Android devices using Appium. This project performs device-level automation to collect and serve data through a backend server.

---

## 🚀 Features

- Android device automation using Appium
- Data scraping from device interfaces
- Backend server for serving scraped data
- Modular scripts for scraping and server management

---

## 🛠 Requirements

- Python 3.x
- Appium (installed globally)
- Android Debug Bridge (ADB)
- Android device or emulator with USB debugging enabled
- Node.js (for Appium installation)

---

## 📦 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Searchlook/Scraper_IMSS_App_Priyansh.git
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run the Project

### Step 1: Activate Virtual Environment

```bash
venv\Scripts\activate
```

### Step 2: Start the Appium Server

```bash
appium --allow-insecure adb_shell
```

> Ensure your Android device is connected or emulator is running.

### Step 3: Start the Scraper

```bash


```

### Step 4: Start the Main Server

```bash
python indexOutlook.py
```

### Step 5: Start the ngrok server

```bash
cd "C:\Users\User\Downloads\ngrok-v3-stable-windows-amd64"
ngrok http  --url=priyansh.ngrok.app 3000
```
---

## 📁 Project Structure

```
IMSS_APP_DFL_Priyansh/
├── imss.py              # Scraper logic
├── index.py             # Main server entry point
├── venv/                # Virtual environment (excluded from Git)
├── requirements.txt     # Project dependencies
├── README.md            # Project documentation
```

---

## 🧪 Testing

Manual testing can be done by observing console logs while:
- Running the scraper
- Monitoring Appium logs
- Checking outputs from the backend server

---

---

## 📃 License

This project is intended for internal use and development learning. Licensing can be updated as needed.
