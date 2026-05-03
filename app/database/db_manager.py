import os
import sqlite3
import logging
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="app/database/finance_bot.db"):
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        try:
            with self.conn:
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER, 
                        category TEXT,
                        name TEXT,
                        price REAL,
                        shop TEXT,
                        currency TEXT DEFAULT 'RUB',
                        date TEXT
                    )
                 """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS incomes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        category TEXT,
                        name TEXT,
                        price REAL,
                        currency TEXT DEFAULT 'RUB',
                        date TEXT
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_settings (
                        user_id INTEGER PRIMARY KEY,
                        monthly_limit REAL DEFAULT 50000
                    )
                """)
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")

    def add_expense(self, user_id, category, name, price, shop="-", currency="RUB"):
        date_now = datetime.now().strftime("%d.%m.%Y %H:%M")
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO expenses (user_id, category, name, price, shop, currency, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (user_id, category, name, price, shop, currency, date_now)
                )
        except Exception as e:
            logger.error(f"Ошибка при добавлении расхода: {e}")

    def add_income(self, user_id, category, name, price, currency="RUB"):
        date_now = datetime.now().strftime("%d.%m.%Y")
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO incomes (user_id, category, name, price, currency, date) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, category, name, price, currency, date_now)
                )
        except Exception as e:
            logger.error(f"Ошибка при добавлении дохода: {e}")

    def get_records_by_category(self, category, user_id, table="expenses"):
        cols = "id, category, name, price, shop, date" if table == "expenses" else "id, category, name, price, date"
        query = f"SELECT {cols} FROM {table} WHERE category = ? AND user_id = ? ORDER BY id DESC LIMIT 10"
        try:
            cursor = self.conn.execute(query, (category, user_id))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = {"id": r[0], "Название": r[2], "Стоимость": r[3], "Дата": r[-1], "row_idx": r[0]}
                if table == "expenses":
                    item["Магазин"] = r[4]
                result.append(item)
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении записей категории {category}: {e}")
            return []

    def delete_by_row(self, row_id, user_id, table="expenses"):
        query = f"DELETE FROM {table} WHERE id = ? AND user_id = ?"
        try:
            with self.conn:
                self.conn.execute(query, (row_id, user_id))
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении записи {row_id} из {table}: {e}")
            return False

    def update_cell(self, row_id, column_name, value, user_id, table="expenses"):
        query = f"UPDATE {table} SET {column_name} = ? WHERE id = ? AND user_id = ?"
        try:
           with self.conn:
                self.conn.execute(query, (value, row_id, user_id))
           return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении ячейки {column_name} в {table}: {e}")
            return False

    def get_all_df(self, user_id=None, table="expenses"):
        try:
            if user_id:
                query = f"SELECT * FROM {table} WHERE user_id = ?"
                return pd.read_sql_query(query, self.conn, params=(user_id,))
            else:
                query = f"SELECT * FROM {table}"
                return pd.read_sql_query(query, self.conn)
        except Exception as e:
            logger.error(f"Ошибка при получении DataFrame из {table}: {e}")
            return pd.DataFrame()

    def get_user_limit(self, user_id):
        query = "SELECT monthly_limit FROM user_settings WHERE user_id = ?"
        try:
            cursor = self.conn.execute(query, (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 50000
        except Exception as e:
            logger.error(f"Ошибка при получении лимита пользователя {user_id}: {e}")
            return 50000

    def set_user_limit(self, user_id, limit):
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT OR REPLACE INTO user_settings (user_id, monthly_limit) VALUES (?, ?)",
                    (user_id, limit)
                )
        except Exception as e:
            logger.error(f"Ошибка при установке лимита пользователю {user_id}: {e}")