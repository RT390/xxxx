import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN","9278953855:AAH8sBJoIW3mLWfMUEBgfV_1bVv5Y3mhJVo")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7989584978"))
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin1234")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-please")
DATABASE_URL = os.getenv("DATABASE_URL", "")

BACKGROUND_IMAGE_URL = os.getenv(
    "BACKGROUND_IMAGE_URL",
    "https://i.imgur.com/8Q4YWvX.jpg"
)
VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1280"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "720"))
SEND_DELAY = int(os.getenv("SEND_DELAY", "3"))

SHEIKH_NAME = "الشيخ ابن عثيمين رحمه الله"
TMP_DIR = "/app/tmp"
LOG_DIR = "/app/logs"

os.makedirs(TMP_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)