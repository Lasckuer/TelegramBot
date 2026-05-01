import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SPREADSHEET_ID, JSON_KEYFILE

class GoogleTable:
    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(SPREADSHEET_ID).sheet1

    def add_expense(self, category, name, price, shop="-"):
        # Проверяем, есть ли уже такой товар
        all_records = self.sheet.get_all_records()
        for record in all_records:
            if record['Название'].lower() == name.lower() and str(record['Стоимость']) == str(price):
                return "exists"
        
        self.sheet.append_row([category, name, price, shop])
        return "success"

    def get_all_data(self):
        records = self.sheet.get_all_records()
        if not records:
            return "Список пуст."
        
        report = ""
        for res in records:
            report += f"📦 {res['Категория']} | 🔹 {res['Название']} | 💰 {res['Стоимость']}р | 🏪 {res['Магазин']}\n"
        return report