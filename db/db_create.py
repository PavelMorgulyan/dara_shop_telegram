import sqlite3
from db.db_getter import DB_NAME


def db_connect():
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        print("База данных создана и успешно подключена к SQLite")

        sqlite_select_query = "select sqlite_version();"
        cursor.execute(sqlite_select_query)
        record = cursor.fetchall()
        print("Версия базы данных SQLite: ", record)
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_tattoo_order_table():
    # tattoo_id - id того продукта, который будет в таблице самого продукта
    # CREATE TABLE
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE tattoo_orders (
                telegram TEXT,
                tattoo_name TEXT,
                tattoo_photo TEXT, 
                tattoo_size TEXT,
                date_meeting TEXT,
                date_time TEXT,
                tattoo_note TEXT,
                order_note TEXT,
                order_state TEXT NOT NULL,
                tattoo_order_number TEXT PRIMARY KEY,
                creation_date DATE,
                price TEXT,
                check_document TEXT,
                username TEXT NOT NULL,
                schedule_id TEXT, 
                colored TEXT,
                details_number INTEGER,
                bodyplace TEXT,
                tattoo_place_file TEXT, 
                tattoo_type TEXT,
                tattoo_place_video_note TEXT, 
                tattoo_place_video TEXT
                );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица заказов тату tattoo_orders создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_tattoo_sketch_order():
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE tattoo_sketch_orders (
                order_id INTEGER UNIQUE PRIMARY KEY,
                desc TEXT, 
                photo_list TEXT, 
                telegram TEXT,
                creation_time TEXT,
                order_state TEXT,
                check_document TEXT,
                price TEXT
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица заказов тату tattoo_sketch_orders создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_price_list_to_tattoo_order():
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE tattoo_order_price_list (
                id INTEGER UNIQUE PRIMARY KEY,
                min_size TEXT, 
                max_size TEXT, 
                price TEXT 
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица заказов тату tattoo_order_price_list создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_tattoo_themes_table():
    # tattoo_id - id того продукта, который будет в таблице самого продукта
    # CREATE TABLE
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE  tattoo_themes (
                tattoo_themes_name TEXT UNIQUE PRIMARY KEY
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица заказов тату tattoo_themes создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_clients_info_table():
    # tattoo_id - id того продукта, который будет в таблице самого продукта
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE clients (
                username TEXT ,
                telegram TEXT NOT NULL PRIMARY KEY,
                phone TEXT
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица клиентов clients создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_candle_items_table():
    # state - есть в наличии / нет в наличии
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE  candle_items (
            name TEXT PRIMARY KEY,
            photo TEXT, 
            price INTEGER,
            note TEXT,
            state TEXT NOT NULL,
            numbers INTEGER
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица свечей candle_items создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_giftbox_order_table():
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE  giftbox_orders (
                order_note TEXT NOT NULL,
                order_number TEXT PRIMARY KEY,
                creation_date TEXT ,
                username TEXT NOT NULL,
                check_document TEXT NOT NULL,
                order_state TEXT,
                price TEXT,
                telegram TEXT
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица заказов гифтбоксов giftbox_orders создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_tattoo_table():
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE tattoo_items (
                name TEXT,
                photo TEXT PRIMARY KEY, 
                price TEXT,
                colored TEXT,
                note TEXT,
                creator TEXT
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица татушек tattoo_items создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


"""
    giftbox_name = State()                  # назови гифтбокс
    giftbox_photo = State()                 # загрузи фото гифтбокс
    giftbox_price = State()                 # примерная цена на гифтбокс
    giftbox_note = State()                  # напиши описание гифтбокс
    giftbox_candle_choice = State()         # добавляем свечу в гифтбокс из готовых
    giftbox_candle_name = State()           # назови имя свечи
    giftbox_candle_photo = State()          # загрузи фото свечи
    giftbox_candle_price = State()          # если есть свеча, то какая цена свеча,если свеча нет, то цена 0
    giftbox_candle_note = State()           # описание свечи
    giftbox_candle_state = State()          # есть ли эти свечи сейчас в наличии или надо докупать      
    # giftbox_tattoo_state = State()        # есть ли тату в гифтбокс 
    giftbox_tattoo_theme = State()          # если есть тату, то какая тематика
    giftbox_tattoo_other_theme = State()    # если есть тату, то какая тематика
    giftbox_tattoo_note  = State()          # впиши описание тату
    giftbox_tattoo_state = State()          # есть ли эти тату сейчас в наличии или надо докупать
    giftbox_sequins_type = State()           # впиши тип блесток тату
    giftbox_sequins_state = State()          # есть ли эти блестки сейчас в наличии или надо докупать
"""


def db_create_giftbox_item_table():
    # candle - id свечи, сert - есть сертификат или нет, theme - ботаника, лес, абстракция
    # note - описание гифт-бокса
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE giftbox_items (
                name TEXT PRIMARY KEY,
                photo TEXT,
                price INTEGER,
                giftbox_note TEXT,
                candle_name TEXT,
                candle_photo TEXT,
                candle_price INTEGER,
                candle_note TEXT,
                candle_state TEXT,
                tattoo_theme TEXT,
                tattoo_note TEXT,
                tattoo_state TEXT,
                sequins_type TEXT,
                sequins_state TEXT
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица гифтобксов giftbox_items создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_sequins_table():
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE sequins_items (
                name TEXT PRIMARY KEY,
                photo TEXT
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица календаря sequins_items создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_schedule_table():
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE schedule_calendar (
                id INTEGER PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                date TEXT,
                month_name TEXT,
                month_number INTEGER,
                status TEXT,
                event_type TEXT
            );"""
        # status - Свободен, занят
        # event_type - тату заказ или консультация
        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица расписания schedule_calendar создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_schedule_photo_table():
    try:  # event_type - тату заказ или консультация
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE schedule_photo (
                name TEXT PRIMARY KEY,
                photo TEXT
            );"""
        # status - Свободен, занят
        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица фото расписания schedule_photo создана")
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_сert_table():
    try:
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE сert_orders (
                username TEXT NOT NULL,
                price TEXT,
                order_state TEXT NOT NULL,
                code TEXT PRIMARY KEY,  
                creation_date TEXT NOT NULL,
                cert_order_number TEXT,
                check_document TEXT,
                telegram TEXT
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица сертификатов сert_orders создана")
        cursor.close()
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")


def db_create_tattoo_img_from_ai_table():
    try:
        # state - удачный, неудачный
        sqlite_connection = sqlite3.connect(DB_NAME)
        sqlite_create_table_query = """CREATE TABLE tattoo_ai(
                id TEXT PRIMARY KEY,
                name TEXT,
                photo TEXT,
                state TEXT,
                author_name TEXT
            );"""

        cursor = sqlite_connection.cursor()
        cursor.execute(sqlite_create_table_query)
        sqlite_connection.commit()
        print("Таблица сертификатов сert_orders создана")
        cursor.close()
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
            print("Соединение с SQLite закрыто")
