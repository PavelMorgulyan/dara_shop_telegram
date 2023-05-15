from db.db_setter import set_to_table
import json
from sqlite3 import connect
import datetime
from db.db_create import DB_NAME
from db.db_getter import get_info_many_from_table
from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

# Заполняем таблицу candle со свечами из списка 
"""
    CREATE TABLE giftbox_items (
    id INTEGER PRIMARY KEY,
    name TEXT,
    price TEXT,
    note TEXT
"""

async def db_dump_from_json_tattoo_items():
    with open(f'./db/json/tattoo_items.json', encoding='cp1251') as json_file:
        data = json.load(json_file)
    new_items_lst = []
    with Session(engine) as session:
        for index in range(1, len(data)+1):
            
            new_item = TattooItems(
                name=data[str(index)]["tattoo_name"],
                photos=[TattooItemPhoto(tattoo_item_name=data[str(index)]['tattoo_name'], photo=data[str(index)]["tattoo_photo"])],
                price=data[str(index)]["tattoo_price"],
                colored=data[str(index)]["tattoo_colored"],
                note=data[str(index)]["tattoo_note"],
                creator=data[str(index)]["creator"],
            )
            new_items_lst.append(new_item)
            
        session.add_all(new_items_lst)
        session.commit()
        
    return print(f"База данных в таблице tattoo_items обновлена")


async def dump_to_json(new_data: dict, json_name: str):
    with open(f'./db/{json_name}.json', encoding='cp1251') as json_file:
        data = json.load(json_file)
    data[str(len(data) + 1)] = new_data
    with open(f'./db/{json_name}.json', "w", encoding='cp1251') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


async def dump_to_json_from_db(table_name: str):
    table_info = await get_info_many_from_table(table_name)
    """ sqlite_connection = connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    cursor.execute(f'PRAGMA table_info({table_name})')
    column_names = [i[1] for i in cursor.fetchall()]
    sqlite_connection.close() """
    
    json_name = f".\\db\\db_{table_name}_{datetime.datetime.now().strftime('%H_%M_%d_%m_%Y')}.json"
    data = {}
    for id in range(len(table_info)):
        data[id] = table_info[id] # dict.fromkeys(column_names, table_info[id]) # TODO Доделать правильное формирование словаря
        id += 1
    try:
        with open(json_name, "w", encoding='cp1251') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return "Succsess"
    except Exception as ex:
        return ex