import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
USER_ID = int(os.getenv("USER_ID"))
PROVERKA_CHEKA_TOKEN = os.getenv("PROVERKA_CHEKA_TOKEN")
JSON_KEYFILE = os.getenv("JSON_KEYFILE")