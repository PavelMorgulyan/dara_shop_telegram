import sqlite3
import traceback
import sys
from db.db_getter import DB_NAME
import json

async def update_info(table_name: str, column_name_condition: str, condition_value: 
    str, column_name_value: str, value: str):
    # try:
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    print("База данных подключена к SQLite")# order_state
    
    sqlite_select_query = f"""UPDATE {table_name} set {column_name_value} = \'{value}\'\
        WHERE {column_name_condition} = \'{condition_value}\'"""
    
    print(sqlite_select_query)
    cursor.execute(sqlite_select_query)
    
    sqlite_connection.commit()
    cursor.close()

    ''' except sqlite3.Error as error:
        print(f"Не удалось найти данные в таблице {table_name}")
        print("Класс исключения: ", error.__class__)
        print("Исключение", error.args)
        print("Печать подробноcтей исключения SQLite: ")
        exc_type, exc_value, exc_tb = sys.exc_info()
        print(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    finally:
        if (sqlite_connection):
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
        return f"Соединение с SQLite закрыто, данные из таблицы {table_name} \
        с значением \'{name}\' успешно удалены" '''



async def update_info_in_json(table_name: str, column_name_condition: str, condition_value: 
    str, column_name_value: str, value: str):
    
    with open(f'./db/{table_name}.json', encoding='cp1251') as json_file:
        data = json.load(json_file)
    
    for i in range(1, len(data)):
        if data[i][column_name_condition] == condition_value:
            data[i][column_name_value] = value
    
    with open(f'./db/{table_name}.json', "w", encoding='cp1251') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)