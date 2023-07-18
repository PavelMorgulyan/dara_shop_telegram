from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text

from db.db_filling import dump_to_json, dump_to_json_from_db
from db.db_delete_info import delete_info, delete_table
from db.db_getter import (
    get_tables_name,
)

import os

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, date, time, timedelta
from aiogram.types.message import ContentType
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram_timepicker.panel import (
    FullTimePicker,
    full_timep_callback,
    full_timep_default,
    HourTimePicker,
    hour_timep_callback,
    MinuteTimePicker,
    minute_timep_callback,
    SecondTimePicker,
    second_timep_callback,
    MinSecTimePicker,
    minsec_timep_callback,
    minsec_timep_default,
)
from aiogram_timepicker import result, carousel, clock

from handlers.calendar_client import obj
import cv2
import pytesseract
from msg.main_msg import *

from handlers.client import CODE_LENTH, ORDER_CODE_LENTH, ADMIN_NAMES, CALENDAR_ID
from handlers.other import *

from sqlalchemy import inspect
from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *
import json
from db.db_filling import db_dump_from_json_tattoo_items


# /start_user
async def command_start_admin_as_user(message: types.Message):
    if str(message.from_user.username) in ADMIN_NAMES:
        await bot.send_message(
            message.from_user.id,
            "Привет админ (как пользователь)!",
            reply_markup=kb_client.kb_client_main,
        )
        # await message.delete()

#--------------------------CREATE JSON FILE FROM DB-------------------------------
# /создать_json_файл
class FSM_Admin_create_json_file(StatesGroup):
    table_name = State()


async def command_create_json_file(message: types.Message):
    if (
        message.text in ["Создать json файл", "/создать_json_файл"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        tables_names = await get_tables_name()
        kb_tables_names = ReplyKeyboardMarkup(resize_keyboard=True)
        for ret in tables_names:
            kb_tables_names.add(KeyboardButton(ret[0]))  # выводим наименования таблиц
        kb_tables_names.add(kb_admin.home_btn)
        await FSM_Admin_create_json_file.table_name.set()
        await bot.send_message(
            message.from_id,
            "Какую таблицу хочешь выгрузить в json?",
            reply_markup=kb_tables_names,
        )


async def get_name_json_file(message: types.Message, state: FSMContext):
    tables_names = await get_tables_name()
    tables_names_lst = []
    for name in tables_names:
        tables_names_lst.append(name)

    if (message.text,) in tables_names_lst:
        result = await dump_to_json_from_db(table_name=message.text)
        if result == "Succsess":
            await state.finish()
            await message.reply(
                f"Готово! Вы выгрузили таблицу {message.text}! {MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_main,
            )
        else:
            await message.reply(f"Возникла ошибка: {result}")

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# ------------------------------------------DELETE TABLE---------------------------------------------
class FSM_Admin_delete_table(StatesGroup):
    yes_no_delete_choice = State()
    table_name = State()


# /удалить_таблицу
async def delete_table_command(message: types.Message):
    if (
        message.text.lower() in ["удалить таблицу", "/удалить_таблицу"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for schema in schemas:
            for table_name in inspector.get_table_names(schema=schema):
                kb.add(KeyboardButton(table_name))

        kb.add(KeyboardButton("Все таблицы")).add(kb_admin.home_btn)
        await FSM_Admin_delete_table.yes_no_delete_choice.set()
        await message.reply("Какую таблицу хочешь удалить?", reply_markup=kb)


async def yes_no_delete_choice(message: types.Message, state: FSMContext):
    if message.text not in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        async with state.proxy() as data:
            data["table_name"] = message.text
        await message.reply(
            f"Вы точно хотите удалить таблицу?", reply_markup=kb_client.kb_yes_no
        )
        await FSM_Admin_delete_table.next()
    else:
        await message.reply(
            f"Хорошо, удаление таблицы будет позже. Хотите сделать что-то еще?",
            reply_markup=kb_admin.kb_main,
        )


async def delete_table_with_name(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            table_name = data["table_name"]
        if table_name == "Все таблицы":
            inspector = inspect(engine)
            schemas = inspector.get_schema_names()
            for schema in schemas:
                for table_name in inspector.get_table_names(schema=schema):
                    await delete_table(table_name)
            await message.reply(
                f"Готово! Вы удалили все таблицы", reply_markup=kb_admin.kb_main
            )
        else:
            await delete_table(table_name)

            await message.reply(
                f"Готово! Вы удалили таблицу {table_name}",
                reply_markup=kb_admin.kb_main,
            )

        await state.finish()

    elif message.text == kb_client.no_str:
        await message.reply(
            f"Хорошо, удаление таблицы будет позже. Хотите сделать что-то еще?",
            reply_markup=kb_admin.kb_main,
        )

        await state.finish()


# TODO доделать загрузку базы
# ----------------------------------------------GET DATA FROM JSON--------------------------------
class FSM_Admin_get_data_from_json(StatesGroup):
    table_name = State()
    json_name = State()


# получить данные из json, получить_данные_из_json
async def command_get_data_from_json(message: types.Message):
    if (
        message.text.lower() in ["получить данные из json", "получить_данные_из_json"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        print(f"schemas:{schemas}")
        for schema in schemas:
            for table_name in inspector.get_table_names(schema=schema):
                print(f"table_name:{table_name}")
                kb.add(KeyboardButton(table_name))
                """ for column in inspector.get_columns(table_name, schema=schema):
                        kb.add(KeyboardButton(column)) """
        kb.add(kb_client.cancel_btn)
        await FSM_Admin_get_data_from_json.table_name.set()
        await message.reply("В какую таблицу хочешь поместить данные?", reply_markup=kb)


async def get_table_name_filling(message: types.Message, state: FSMContext):
    inspector = inspect(engine)
    schemas = inspector.get_schema_names()
    table_names_lst = []
    for schema in schemas:
        for table_name in inspector.get_table_names(schema=schema):
            table_names_lst.append(table_name)

    if message.text in table_names_lst:
        async with state.proxy() as data:
            data["table_name"] = message.text

        os.system("dir .\\db\\json\\*.json /b /d > .\\db\\json\\json_name_lst")

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        with open(".\\db\\json\\json_name_lst", "r") as json_name_lst:
            full_line_str = ""
            for line in json_name_lst:
                full_line_str += line
                kb.add(KeyboardButton(line[:-1]))
            json_name_lst = full_line_str.split("\n")
            async with state.proxy() as data:
                data["json_name_lst"] = json_name_lst
            await FSM_Admin_get_data_from_json.next()
            kb.add(LIST_BACK_TO_HOME[0])
            await message.reply("Какой json хочешь использовать?", reply_markup=kb)

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_json_name_filling(message: types.Message, state: FSMContext):
    full_line_str = ""
    full_json_name_lst = []
    with open(".\\db\\json\\json_name_lst", "r") as json_name_lst:
        for line in json_name_lst:
            full_line_str += line
        full_json_name_lst = full_line_str.split("\n")

    if message.text in full_json_name_lst:
        async with state.proxy() as data:
            table_name = data["table_name"]
        data = {}
        with open(f"./db/json/{message.text}", encoding="cp1251") as json_file:
            data = json.load(json_file)

        with Session(engine) as session:
            new_item_lst = []
            for i in range(len(data)):  # TODO нужно из if-else превратить в 1 строку
                if table_name == "price_list":
                    new_item_lst.append(
                        OrderPriceList(
                            type=data[str(i)][1],
                            min_size=data[str(i)][2],
                            max_size=data[str(i)][3],
                            price=data[str(i)][4],
                        )
                    )

                elif table_name == "candle_items":
                    if message.text == "candle_items.json":
                        new_item_lst.append(
                            CandleItems(
                                name=data[str(i + 1)][0]["name"],
                                photo=data[str(i + 1)][0]["photo"],
                                price=data[str(i + 1)][0]["price"],
                                note=data[str(i + 1)][0]["note"],
                                quantity=0,
                            )
                        )
                    else:
                        new_item_lst.append(
                            CandleItems(
                                name=data[str(i)][0],
                                photo=data[str(i)][1],
                                price=int(data[str(i)][2]),
                                note=data[str(i)][3],
                                quantity=int(data[str(i)][4])
                            )
                        )

            session.add_all(new_item_lst)
            session.commit()

        await message.reply(
            f"🎉 Готово! Вы загрузили данные в таблицу {table_name}!\n"
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_main,
        )
        await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# ----------------------------------------------BASIC COMMANDS--------------------------------
# /commands , /команды
async def command_see_list(message: types.Message):
    if (
        message.text.lower() in ["команды", "/команды", "/commands", "commands"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        command_str_message = ""
        i = 0
        for command in (
            list(kb_admin.commands_button.values())
            + kb_admin.schedule_commands
            + kb_admin.candle_item_commands
            + kb_admin.clients_commands
            + kb_admin.giftbox_item_commands
            + kb_admin.giftbox_order_commands
            + kb_admin.cert_item_commands
            + kb_admin.tattoo_order_commands
            + kb_admin.tattoo_items_commands
        ) + [
            'Создать json файл',
            'Удалить таблицу', 
            "Получить данные из json"
            ]:
            i += 1
            if command not in LIST_BACK_COMMANDS:
                command_str_message += f"{i}) {command}\n"

        await bot.send_message(
            message.from_user.id,
            f"На данный момент есть следующие команды:\n{command_str_message}",
            reply_markup=kb_admin.kb_main,
        )


# -------------------------------------------CLOSED COMMAND-------------------------------------------

""" # закончить
async def close_command(message: types.Message, state: FSMContext):
    # await state.finish()
    await bot.send_message(message.from_user.id, 'Удачи и добра тебе, друг,'\
        ' но знай - я всегда к твоим услугам!')
"""

#-----------------------------------------ORDER COMMANDS --------------------------------------

async def get_order_command_list(message: types.Message):
    if (
        message.text.lower() == "заказы"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            "❔ Какую команду по заказам выполнить?",
            reply_markup=kb_admin.kb_order_commands,
        )


# ----------------------------------------------CANCEL COMMAND-------------------------------
# @dp.message_handler(state="*", commands='отмена')
async def cancel_handler(message: types.Message, state: FSMContext):
    if (
        message.text in LIST_CANCEL_COMMANDS
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.finish()
        await message.reply(MSG_CANCEL_ACTION, reply_markup=kb_admin.kb_main)


# -----------------------------------------------BACK COMMAND-------------------------------------
async def back_to_home_command(message: types.Message, state: FSMContext):
    if (
        message.text in LIST_BACK_TO_HOME
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)

# -----------------------------------------------HELP COMMAND-------------------------------------
# help

class FSM_Admin_help(StatesGroup):
    info_type = State()


async def help_command(message: types.Message):
    if (
        message.text in ['/help', 'help']
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await bot.send_message(
            message.from_id, 
            "Какая информация тебя интересует?",
            reply_markup= kb_admin.kb_help_command
        )


async def get_help_type(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.help.values()):
        key = await get_key(kb_admin.help, message.text)
        await bot.send_message(
            message.from_id, kb_admin.help_info_msgs[key]
        )
        await bot.send_message(
            message.from_id, 
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}", 
            reply_markup=kb_admin.kb_main
        )
    

def register_handlers_admin(dp: Dispatcher):
    # ----------------------------------------COMMANDS------------------------------------------------
    dp.register_message_handler(
        get_order_command_list,
        Text(equals=["Заказы"], ignore_case=True),
        state=None,
    )
    
    dp.register_message_handler(command_start_admin_as_user, commands=["start_user"])
    dp.register_message_handler(
        command_start_admin_as_user,
        Text(equals="начать как пользователь", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(command_see_list, commands=["команды", "commands"])
    dp.register_message_handler(
        command_see_list,
        Text(equals=["команды", "commands"], ignore_case=True),
        state=None,
    )
    # dp.register_message_handler(back_command, commands=['назад'])
    # dp.register_message_handler(back_command, Text(equals=['назад'], ignore_case=True), state=None)

    # выгрузка таблицы в \db\db_{tablename}_%H_%M_%d_%m_%Y.json
    dp.register_message_handler(
        command_create_json_file,
        Text(equals="Создать json файл", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        command_create_json_file, commands=["создать_json_файл"], state=None
    )
    dp.register_message_handler(
        get_name_json_file, state=FSM_Admin_create_json_file.table_name
    )
    # --------------------------------------------TABLES-------------------------------------------------
    dp.register_message_handler(delete_table_command, commands=["удалить_таблицу"])
    dp.register_message_handler(
        delete_table_command,
        Text(equals="удалить таблицу", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        yes_no_delete_choice, state=FSM_Admin_delete_table.yes_no_delete_choice
    )
    dp.register_message_handler(
        delete_table_with_name, state=FSM_Admin_delete_table.table_name
    )

    # -------------------------------------------All Commands-------------------------------------------
    dp.register_message_handler(cancel_handler, state="*", commands="отмена")
    dp.register_message_handler(
        cancel_handler, Text(equals=LIST_CANCEL_COMMANDS, ignore_case=True), state="*"
    )

    dp.register_message_handler(
        back_to_home_command, commands=LIST_BACK_TO_HOME, state="*"
    )
    # dp.register_message_handler(back_to_home_command, commands=LIST_BACK_TO_HOME, state='*')
    dp.register_message_handler(
        back_to_home_command,
        Text(equals=LIST_BACK_TO_HOME, ignore_case=True),
        state="*",
    )

    # ----------------------------------------------GET DATA FROM JSON--------------------------------
    dp.register_message_handler(
        command_get_data_from_json,
        Text(equals="получить данные из json", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        command_get_data_from_json, commands="получить_данные_из_json", state=None
    )
    dp.register_message_handler(
        get_table_name_filling, state=FSM_Admin_get_data_from_json.table_name
    )
    dp.register_message_handler(
        get_json_name_filling, state=FSM_Admin_get_data_from_json.json_name
    )
