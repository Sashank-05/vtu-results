import os
import sqlite3

from functools import wraps


def reset_cursor(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            # Execute the original function
            return func(self, *args, **kwargs)
        finally:
            # Close the cursor after the function execution
            self.cursor.close()
            # Reopen a new cursor
            self.cursor = self.connection.cursor()

    return wrapper


class DBHandler:
    def __init__(self, db_path='../database.db' if os.getcwd().endswith('helpers') else 'database.db'):
        self.db_path = db_path
        self.connection = self.connect()
        self.cursor = self.connection.cursor()

    def connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    @reset_cursor
    def create_table_columns(self, table_name: str, sub_columns: list):
        print(table_name)
        sql_create_table = f"""CREATE TABLE IF NOT EXISTS {table_name} (
                    USN VARCHAR(12),
                    NAME VARCHAR(25)
            );"""
        self.cursor.execute(sql_create_table)

        for sub in sub_columns:
            print(sub)
            sql = f"ALTER TABLE {table_name} ADD COLUMN {sub} VARCHAR(100);"
            self.cursor.execute(sql)

        self.connection.commit()

    @reset_cursor
    def push_data_into_table(self, table_name: str, inte: list, ext: list, other: list):
        try:
            placeholders = ', '.join(['?'] * (len(inte) + len(ext) + len(other)))
            sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
            values = [other[0].strip(), other[1].strip()] + inte + ext + other[2:]
            print(values)
            self.cursor.execute(sql, values)

        except Exception as e:
            pass
        self.connection.commit()

    @reset_cursor
    def get_student_marks(self, id, sem, usn):
        try:
            sql = f"SELECT * FROM {id}_SEM_{sem} WHERE USN LIKE ?"
            self.cursor.execute(sql, (usn,))
            result = self.cursor.fetchall()
            return result
        except sqlite3.OperationalError as e:
            pass

    @reset_cursor
    def get_semester_marks(self, id, sem):
        sql = "SELECT * FROM {id}_SEM_{sem}"
        print(sql.format(id=id, sem=sem))
        self.cursor.execute(sql.format(id=id, sem=sem))
        result = self.cursor.fetchall()
        return result

    @reset_cursor
    def max(self, table_name: str, column_name: str):
        sql = f"SELECT MAX({column_name}) FROM {table_name}"

        self.cursor.execute(sql)
        result = self.cursor.fetchone()
        return result[0] if result else None

    @reset_cursor
    def get_columns(self, table_name: str):
        cols = []
        data = self.cursor.execute(f'''SELECT * FROM {table_name}''')
        for column in data.description:
            cols.append(column[0])

        return cols

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
