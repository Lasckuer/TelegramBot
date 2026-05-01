import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from config import SPREADSHEET_ID, JSON_KEYFILE
from datetime import datetime

class GoogleTable:
    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(SPREADSHEET_ID).sheet1

    def add_expense(self, category, name, price, shop="-"):
        date_now = datetime.now().strftime("%d.%m.%Y")
        self.sheet.append_row([category, name, price, shop, date_now])
        
    def get_all_df(self):
        records = self.sheet.get_all_records()
        return pd.DataFrame(records)

    def delete_last_record(self):
        all_values = self.sheet.get_all_values()
        if len(all_values) > 1: # Не удаляем заголовок
            self.sheet.delete_rows(len(all_values))
            return True
        return False

    def get_monthly_analytics(self):
        records = self.sheet.get_all_records()
        if not records: return "Данных пока нет."
        
        report = {}
        total = 0
        for r in records:
            # Используем get() с именами колонок. Проверь, что в таблице они такие же!
            cat = r.get('Категория', 'Другое')
            
            # Пробуем достать стоимость и превратить в число
            raw_price = r.get('Стоимость', 0)
            try:
                price = int(raw_price)
            except (ValueError, TypeError):
                price = 0
                
            report[cat] = report.get(cat, 0) + price
            total += price
        
        msg = "📊 Аналитика:\n"
        for cat, sum_val in report.items():
            msg += f"🔹 {cat}: {sum_val}р\n"
        msg += f"\n💰 Итого: {total}р"
        return msg
    
    def get_records_by_category(self, category):
        all_records = self.sheet.get_all_records()
        # Фильтруем записи и сохраняем их реальный номер строки (index + 2, т.к. заголовок и счет с 0)
        filtered = []
        for i, r in enumerate(all_records):
            if r.get('Категория') == category:
                r['row_idx'] = i + 2 
                filtered.append(r)
        return filtered[-10:] # Возвращаем последние 10

    def delete_by_row(self, row_number):
        self.sheet.delete_rows(row_number)
        return True