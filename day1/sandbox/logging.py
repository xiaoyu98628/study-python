import logging
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "storage" / "logs"
SANDBOX_LOG_FILE = LOG_DIR / "sandbox.log"

LOG_DIR.mkdir(parents=True, exist_ok=True)

sandbox_logger = logging.getLogger("day1.sandbox")
sandbox_logger.setLevel(logging.DEBUG)
sandbox_logger.propagate = False

if not sandbox_logger.handlers:
    sandbox_handler = logging.FileHandler(SANDBOX_LOG_FILE, encoding="utf-8")
    sandbox_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s"))
    sandbox_logger.addHandler(sandbox_handler)
