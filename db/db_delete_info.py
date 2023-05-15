import sqlite3
import traceback
import sys
from db.db_getter import DB_NAME

async def delete_info(table: str, condition_column_name: str, condition_value: str):
    # try:
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    print("База данных подключена к SQLite")
    
    sqlite_select_query = f"""DELETE from {table} WHERE {condition_column_name} = \'{condition_value}\'"""

    print(sqlite_select_query)
    cursor.execute(sqlite_select_query)
    
    sqlite_connection.commit()
    cursor.close()

    ''' except sqlite3.Error as error:
        print(f"Не удалось найти данные в таблице {table}")
        print("Класс исключения: ", error.__class__)
        print("Исключение", error.args)
        print("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    finally:
        if (sqlite_connection):
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
        return f"Соединение с SQLite закрыто, данные из таблицы {table} с значением \'{name}\' \
            успешно удалены" '''


async def delete_table(table):
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    print("База данных подключена к SQLite")

    sqlite_select_query = f"""DROP TABLE IF EXISTS {table} """
    print(sqlite_select_query)
    cursor.execute(sqlite_select_query)
    
    sqlite_connection.commit()
    cursor.close()