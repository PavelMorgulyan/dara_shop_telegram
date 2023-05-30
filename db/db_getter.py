import sqlite3
import traceback
import sys
from create_bot import bot

DB_NAME = "db_dara_store_telegram.db"


async def get_info(table: str, column_name: str, name: str):
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        print("База данных подключена к SQLite")

        sqlite_select_query = (
            f"""SELECT {column_name} from {table} WHERE {column_name} = {name}"""
        )
        cursor.execute(sqlite_select_query)
        info = cursor.fetchone()

    except sqlite3.Error as error:
        print(f"Не удалось найти данные в таблице {table}")
        print("Класс исключения: ", error.__class__)
        print("Исключение", error.args)
        print("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))

    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
        return info


async def get_tables_name():
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        print("База данных подключена к SQLite")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        # print(cursor.fetchall())
        info = cursor.fetchall()

    except sqlite3.Error as error:
        print("Не удалось найти данные о таблицах")
        print("Класс исключения: ", error.__class__)
        print("Исключение", error.args)
        print("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))

    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
        return info


async def get_info_many_from_table(table: str, column_name="", condition=""):
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        print(column_name, condition)
        print("База данных подключена к SQLite")
        sqlite_select_query = ""
        if condition == "":
            sqlite_select_query = f"""SELECT * from {table}"""
        else:
            sqlite_select_query = (
                f"""SELECT * from {table} WHERE {column_name} = \'{condition}\'"""
            )
        cursor.execute(sqlite_select_query)

        many = cursor.fetchall()
        print(many)

    except sqlite3.Error as error:
        print(f"Не удалось найти данные в таблице {table}")
        print("Класс исключения: ", error.__class__)
        print("Исключение", error.args)
        print("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))

    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
        return many


""" async def get_info_tattoo_orders(message):
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    for ret in cursor.execute('SELECT * FROM tattoo_orders').fetchall():
        await bot.send_message(message.from_user.id, ret[0] + ret[1] + ret[2])

"""
