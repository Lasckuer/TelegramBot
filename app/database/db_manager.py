import sqlite3
import pandas as pd
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="app/database/finance_bot.db"):
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER, 
                    category TEXT,
                    name TEXT,
                    price REAL,
                    shop TEXT,
                    date TEXT
                )
             """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS incomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    source TEXT,
                    name TEXT,
                    amount REAL,
                    date TEXT
                )
             """)

    # --- МЕТОДЫ ДЛЯ РАСХОДОВ ---

    def add_expense(self, user_id,category, name, price, shop="-"):
        """Добавление расхода."""
        date_now = datetime.now().strftime("%d.%m.%Y")
        with self.conn:
            self.conn.execute(
                "INSERT INTO expenses (user_id, category, name, price, shop, date) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, category, name, price, shop, date_now)
            )

    def get_all_df(self, user_id):
        """Получение всех расходов конкретного пользователя."""
        query = "SELECT * FROM expenses WHERE user_id = ?"
        return pd.read_sql_query(query, self.conn, params=(user_id,))

    def delete_last_record(self):
        """Удаление последней добавленной записи."""
        with self.conn:
            cursor = self.conn.execute("SELECT MAX(id) FROM expenses")
            max_id = cursor.fetchone()[0]
            if max_id:
                self.conn.execute("DELETE FROM expenses WHERE id = ?", (max_id,))
                return True
        return False

    def get_records_by_category(self, category, user_id):
        """Получает последние 10 записей конкретной категории."""
        query = "SELECT id, category, name, price, shop, date FROM expenses WHERE category = ? AND user_id = ? ORDER BY id DESC LIMIT 10"
        with self.conn:
            cursor = self.conn.execute(query, (category, user_id))
            # row_idx заменяет индекс строки Google Таблиц для совместимости с логикой удаления
            return [
                {"id": r[0], "Категория": r[1], "Название": r[2], "Стоимость": r[3], "Магазин": r[4], "Дата": r[5], "row_idx": r[0]}
                for r in cursor.fetchall()
            ]

    def delete_by_row(self, row_id, user_id):
        """Удаление записи по ID (вместо номера строки)."""
        with self.conn:
            self.conn.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (row_id, user_id))
            return True

    def update_cell(self, row_id, column_name, value, user_id):
        """Обновление конкретного поля записи."""
        # Безопасная подстановка имени колонки (внутренняя логика)
        allowed_columns = ["category", "name", "price", "shop", "date"]
        if column_name.lower() not in allowed_columns:
            return False
            
        query = f"UPDATE expenses SET {column_name} = ? WHERE id = ? AND user_id = ?"
        with self.conn:
            self.conn.execute(query, (value, row_id, user_id))
            return True

    # --- МЕТОДЫ ДЛЯ ДОХОДОВ ---

    def add_income(self, user_id, source, name, amount):
        """Добавление дохода."""
        date_now = datetime.now().strftime("%d.%m.%Y")
        with self.conn:
            self.conn.execute(
                "INSERT INTO incomes (user_id, source, name, amount, date) VALUES (?, ?, ?, ?, ?)",
                (user_id, source, name, amount, date_now)
            )

    def get_all_incomes(self, user_id):
        """Получение всех доходов как DataFrame."""
        return pd.read_sql_query("SELECT * FROM incomes WHERE user_id = ?", self.conn, params=(user_id,))

    # --- АНАЛИТИКА И ОТЧЕТЫ ---

    def get_monthly_analytics(self, user_id):
        """Генерация текстового отчета по категориям за все время."""
        df = self.get_all_df(user_id)
        if df.empty:
            return "Данных пока нет."
        
        report = df.groupby('category')['price'].sum().to_dict()
        total = df['price'].sum()
        
        msg = "📊 Аналитика:\n"
        for cat, sum_val in report.items():
            msg += f"🔹 {cat}: {sum_val}р\n"
        msg += f"\n💰 Итого: {total}р"
        return msg

    def get_balance_report(self, user_id):
        """Расчет баланса за текущий месяц."""
        now = datetime.now()
        month_str = now.strftime("%m.%Y")

        # Получаем расходы за текущий месяц через SQL
        exp_query = "SELECT SUM(price) FROM expenses WHERE date LIKE ? AND user_id = ?"
        inc_query = "SELECT SUM(amount) FROM incomes WHERE date LIKE ? AND user_id = ?"
        
        with self.conn:
            total_exp = self.conn.execute(exp_query, (f"%{month_str}", user_id)).fetchone()[0] or 0
            total_inc = self.conn.execute(inc_query, (f"%{month_str}", user_id)).fetchone()[0] or 0

        balance = total_inc - total_exp
        
        text = f"📊 <b>Финансовый итог за текущий месяц:</b>\n\n"
        text += f"🟢 Доходы: {total_inc}р\n"
        text += f"🔴 Расходы: {total_exp}р\n"
        text += f"➖➖➖➖➖➖➖➖\n"
        text += f"💰 Остаток: <b>{balance}р</b>\n\n"
        
        if balance > 0:
            text += f"👍 Вы в плюсе! Рекомендуем отложить: <b>{balance * 0.1:.0f}р</b> (10%)"
        elif balance < 0:
            text += f"⚠️ Внимание! Вы потратили больше, чем заработали."
        else:
            text += f"⚖️ Вы вышли в ноль."
            
        return text