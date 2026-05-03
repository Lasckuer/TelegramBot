import os
import json

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