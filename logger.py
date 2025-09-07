import os
import logging
from datetime import datetime

# Create logs directory if not exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

class CustomFormatter(logging.Formatter):
    def format(self, record):
        timestamp = self.formatTime(record, self.datefmt)
        level = record.levelname
        module = record.module
        curp = getattr(record, "curp", "N/A")
        message = record.getMessage()
        return f"[{timestamp}] | {level} | [{module}] | [{curp}] | {message}"

class DailyFileHandler(logging.Handler):
    def __init__(self, log_dir=LOG_DIR):
        super().__init__()
        self.log_dir = log_dir
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self._open_file()

    def _open_file(self):
        log_path = os.path.join(self.log_dir, f"{self.current_date}.log")
        self.file = open(log_path, "a", encoding="utf-8")

    def emit(self, record):
        try:
            record_date = datetime.now().strftime("%Y-%m-%d")
            if record_date != self.current_date:
                self.file.close()
                self.current_date = record_date
                self._open_file()
            msg = self.format(record)
            self.file.write(msg + "\n")
            self.file.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        if hasattr(self, 'file') and not self.file.closed:
            self.file.close()
        super().close()

# Create the logger
logger = logging.getLogger("imssLogger")
logger.setLevel(logging.INFO)

# Add handlers only once
if not logger.handlers:
    file_handler = DailyFileHandler()
    file_handler.setFormatter(CustomFormatter(datefmt="%Y-%m-%d %H:%M:%S"))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomFormatter(datefmt="%Y-%m-%d %H:%M:%S"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
