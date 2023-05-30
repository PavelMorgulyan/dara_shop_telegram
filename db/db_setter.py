import sqlite3
import traceback
import sys
from db.db_getter import DB_NAME


async def set_to_table(state: tuple, table: str):
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        print("База данных подключена к SQLite")
        values_str = ""
        for i in range(len(state)):
            values_str += "?,"

        # Вставляем новый заказ в таблицу
        values_str = values_str[: len(values_str) - 1]
        line = f"INSERT INTO {table} VALUES ({values_str})"
        cursor.execute(line, state)

        sqlite_connection.commit()
        print(f"Запись успешно вставлена ​​в таблицу {table} ", cursor.rowcount)
        cursor.close()

    except sqlite3.Error as error:
        print(f"Не удалось вставить данные в таблицу {table}")
        print("Класс исключения: ", error.__class__)
        print("Исключение", error.args)
        print("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
        return 0
