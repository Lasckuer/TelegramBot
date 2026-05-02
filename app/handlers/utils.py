import os
import json
import app.keyboards.inline as kb_inline
from app.database.db_manager import DatabaseManager

db = DatabaseManager()

SUBS_FILE = "subs.json"
CAT_MAP_FILE = "cat_map.json"
DEBTS_FILE = "debts.json"

def load_json(filename):
    if not os.path.exists(filename):
        return [] if "map" not in filename else {}
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_debts(): return load_json(DEBTS_FILE)
def save_debts(data): save_json(DEBTS_FILE, data)
def load_subs(): return load_json(SUBS_FILE)
def save_subs(data): save_json(SUBS_FILE, data)
def load_cat_map(): return load_json(CAT_MAP_FILE)
def save_cat_map(data): save_json(CAT_MAP_FILE, data)

def generate_page_text(matches: list, query: str, page: int, per_page: int = 5):
    import math
    total_pages = math.ceil(len(matches) / per_page)
    start = page * per_page
    end = start + per_page
    page_items = matches[start:end]

    text = f"🔍 Результаты по запросу «{query}» (Стр. {page+1} из {total_pages}):\n\n"
    for row in page_items:
        date_str = row.get('date', '-')
        text += f"• <b>{row.get('name', '-')}</b> — {row.get('price', 0)}р <i>({date_str})</i>\n"

    markup = kb_inline.get_pagination_kb(page, total_pages)
    return text, markup