from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES, CALENDAR_ID, DARA_ID

from db.db_setter import set_to_table
from db.db_updater import update_info, update_info_in_json
from db.db_filling import dump_to_json
from db.db_delete_info import delete_info
from db.db_getter import get_info_many_from_table

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult, Sequence
from db.sqlalchemy_base.db_classes import *

from handlers.other import *

# from diffusers import StableDiffusionPipeline
# import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup

from msg.main_msg import *
import json


async def get_tattoo_items_and_item_command_list(message: types.Message):
    if (
        message.text.lower() in ["татуировки", "/татуировки"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            "Какую команду хочешь выполнить?",
            reply_markup=kb_admin.kb_tattoo_items_commands,
        )


# -------------------------------------------------------CHANGE TATTOO ITEM-----------------------------------------
class FSM_Admin_tattoo_item_change(StatesGroup):
    tattoo_name = State()
    new_state = State()
    new_value = State()
    new_photo = State()


# изменить_тату
async def command_change_tattoo_item(message: types.Message):
    if (
        message.text.lower() in ["изменить тату", "/изменить_тату"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            tattoo_items = session.scalars(select(TattooItems)).all()

        if tattoo_items == []:
            await message.reply(MSG_NO_TATTOO_IN_TABLE)
        else:
            kb_tattoo_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in tattoo_items:
                kb_tattoo_names.add(item.name)
            await FSM_Admin_tattoo_item_change.tattoo_name.set()

            kb_tattoo_names.add(LIST_BACK_TO_HOME[0])

            await FSM_Admin_tattoo_item_change.tattoo_name.set()
            await message.reply(
                "Какое тату хочешь изменить?", reply_markup=kb_tattoo_names
            )


async def get_tattoo_name_for_changing(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        tattoo_items = session.scalars(select(TattooItems)).all()
    tattoo_names_list = []
    for item in tattoo_items:
        tattoo_names_list.append(item.name)

    if message.text in tattoo_names_list:
        async with state.proxy() as data:
            data["tattoo_name"] = message.text
        await FSM_Admin_tattoo_item_change.next()
        await message.reply(
            f'Хорошо, вы выбрали тату под названием "{message.text}".\n'
            "❔ Что хотите изменить?",
            reply_markup=kb_admin.kb_new_tattoo_item_state,
        )

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_items_commands
        )


async def get_new_tattoo_item_state(message: types.Message, state: FSMContext):
    if message.text in kb_admin.new_tattoo_item_state.keys():
        await FSM_Admin_tattoo_item_change.next()
        async with state.proxy() as data:
            data["new_state"] = message.text

        kb_new_state_tattoo_item = {
            "name": kb_client.kb_back,
            "photo": kb_client.kb_back,
            "price": kb_admin.kb_price_list_commands,
            "size": kb_admin.kb_sizes,
            "colored": kb_client.kb_colored_tattoo_choice,
            "details_number": kb_client.kb_number_tattoo_details,
            "note": kb_client.kb_back,
            "creator": kb_admin.kb_creator_lst,
        }
        if message.text != "Фотография":
            await message.reply(
                "❔ На какое значение хотите изменить?",
                reply_markup=kb_new_state_tattoo_item[
                    kb_admin.new_tattoo_item_state[message.text]
                ],
            )
        else:
            await FSM_Admin_tattoo_item_change.next()
            await message.reply(
                "📎 Загрузи новую фотографию тату, пожалуйста",
                reply_markup=kb_new_state_tattoo_item[
                    kb_admin.new_tattoo_item_state[message.text]
                ],
            )
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_items_commands
        )
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def set_new_tattoo_item_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        new_state = kb_admin.new_tattoo_item_state[data["new_state"]]
        tattoo_name = data["tattoo_name"]

    new_state_value = message.text
    await update_info("tattoo_items", "name", tattoo_name, new_state, new_state_value)
    await message.reply(
        f"Отлично, ты поменяла значение {new_state} у {tattoo_name}",
        reply_markup=kb_admin.kb_tattoo_items_commands,
    )
    await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
    await state.finish()


async def set_new_tattoo_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        tattoo_name = data["tattoo_name"]
        new_state = data["new_state"]
    await update_info("tattoo_items", "name", tattoo_name, "photo", message.text)
    await update_info_in_json(
        "tattoo_items", "name", tattoo_name, "photo", message.text
    )

    await message.reply(
        f"Отлично, ты поменяла значение {new_state} у {tattoo_name}",
        reply_markup=kb_admin.kb_tattoo_items_commands,
    )
    await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
    await state.finish()


# -----------------------------------------SET TATTOO ITEM-----------------------------------------


class FSM_Admin_tattoo_item(StatesGroup):
    tattoo_name = State()  # назови тату
    tattoo_photo = State()  # загрузи фото тату
    tattoo_price = State()  # примерная цена на тату
    tattoo_colored = State()
    # tattoo_number_of_details = State()
    tattoo_note = State()  # напиши описание тату


# /добавить_тату

"""# TODO
    1) command_load_tattoo_item:
        a) 'Введи название тату' - Complete
        b) LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME  -  Complete
    2) load_tattoo_name
        a) 'А теперь загрузи фотографию тату' -  Complete
        b) LIST_CANCEL_COMMANDS + LIST_BACK_COMMANDS + LIST_BACK_TO_HOME  -  Complete
    3) load_tattoo_photo
        a) 'Введи примерную цену тату' -  Complete
        b) MSG_PLS_SEND_TATTOO_PHOTO_OR_CANCEL_ACTION - NO
    4) load_tattoo_price -
"""


async def command_load_tattoo_item(message: types.Message):
    if (
        message.text.lower() in ["добавить тату", "/добавить_тату"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_tattoo_item.tattoo_name.set()
        await message.reply("Введи название тату", reply_markup=kb_client.kb_cancel)


# Отправляем название тату
async def load_tattoo_name(message: types.Message, state: FSMContext):
    if message.text in LIST_CANCEL_COMMANDS + LIST_BACK_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_items_commands
        )
    else:
        async with state.proxy() as data:
            data["tattoo_name"] = message.text
        await FSM_Admin_tattoo_item.next()
        await message.reply(
            "А теперь загрузи фотографию тату", reply_markup=kb_client.kb_back_cancel
        )


# Отправляем фото тату
async def load_tattoo_item_photo(message: types.Message, state: FSMContext):
    # try:
    if message.content_type == "photo":
        async with state.proxy() as data:
            data["tattoo_photo"] = message.photo[0].file_id
        await FSM_Admin_tattoo_item.next()
        await message.reply("Введи примерную цену тату", reply_markup=kb_admin.kb_price)
    else:
        if message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
            await state.finish()
            await message.reply(
                MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST,
                reply_markup=kb_admin.kb_price,
            )
        elif message.text in LIST_BACK_COMMANDS:
            await message.reply(
                "Вы вернулись назад к выбору имени для тату."
                " Какое имя для тату хочешь поставить?",
                reply_markup=kb_admin.kb_back_home,
            )
            await FSM_Admin_tattoo_item.previous()


# Отправляем стоимость тату
async def load_tattoo_price(message: types.Message, state: FSMContext):
    if message.text == "Другая цена":
        await message.reply(
            "Хорошо, введи другую цену тату",
            reply_markup=kb_admin.kb_another_price_full,
        )

    elif message.text in kb_admin.price_lst + kb_admin.another_price_full_lst:
        async with state.proxy() as data:
            data["tattoo_price"] = message.text
        await FSM_Admin_tattoo_item.next()
        await message.reply(
            f"Тату будет ч/б или цветная?",
            reply_markup=kb_client.kb_colored_tattoo_choice,
        )

    elif message.text in LIST_CANCEL_COMMANDS:  #
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)

    elif message.text in LIST_BACK_COMMANDS:
        await message.reply(
            "Вы вернулись назад к выбору фото для тату."
            " Какое фото для тату хочешь поставить?",
            reply_markup=kb_client.kb_back_cancel,
        )
        await FSM_Admin_tattoo_item.previous()
    else:
        await message.reply(
            MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST, reply_markup=kb_admin.kb_price
        )


# Отправляем цвет тату
async def load_tattoo_colored(message: types.Message, state: FSMContext):
    if message.text in kb_client.colored_tattoo_choice:
        async with state.proxy() as data:
            data["tattoo_colored"] = message.text.split()[0]
        await FSM_Admin_tattoo_item.next()
        await message.reply(
            f"Хорошо, тату будет {message.text}.\n" "Опиши тату, пожалуйста",
            reply_markup=kb_client.kb_number_tattoo_details,
        )
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_items_commands
        )

    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Admin_tattoo_item.previous()
        await message.reply(
            "Вы вернулись назад к выбору цены. Какая примерная цена тату?",
            reply_markup=kb_admin.kb_price,
        )

    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


""" # Отправляем количество деталей тату
async def load_tattoo_number_of_details(message: types.Message, state: FSMContext):
    
    if message.text == kb_client.number_tattoo_details['more_details']:
        await message.reply('Хорошо, укажи количество деталей',
            reply_markup = kb_client.kb_another_number_details)
        
    elif message.text in list(kb_client.number_tattoo_details.values())[:5] + \
        kb_client.list_other_number_details():
        async with state.proxy() as data:
            data['tattoo_details_number'] = message.text
        await FSM_Admin_tattoo_item.next()
        await message.reply('Введи описание тату', 
            reply_markup = kb_admin.kb_no_note)
        
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Admin_tattoo_item.previous()
        await message.reply('Вы вернулись назад к выбору цвета. Какой будет цвет?',
            reply_markup = kb_client.kb_colored_tattoo_choice)
    
    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_main)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST,
            reply_markup= kb_client.kb_number_tattoo_details) """


# Отправляем описание тату
async def load_tattoo_note(message: types.Message, state: FSMContext):
    if message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Admin_tattoo_item.previous()
        await message.reply(
            "Хорошо, укажи цвет тату", reply_markup=kb_client.kb_colored_tattoo_choice
        )

    elif (
        message.text
        not in LIST_CANCEL_COMMANDS + LIST_BACK_COMMANDS + LIST_BACK_TO_HOME
    ):
        async with state.proxy() as data:
            data["tattoo_note"] = message.text

            new_tattoo_info = {
                "tattoo_name": data["tattoo_name"],
                "tattoo_photo": data["tattoo_photo"],
                "tattoo_price": data["tattoo_price"],
                # "tattoo_size":              data['tattoo_size'],
                "tattoo_colored": data["tattoo_colored"],
                # "tattoo_details_number":    data['tattoo_details_number'],
                "tattoo_note": data["tattoo_note"],
                "creator": "admin",
            }
        await set_to_table(tuple(new_tattoo_info.values()), "tattoo_items")
        await dump_to_json(new_tattoo_info, "tattoo_items")
        await message.reply(
            "Готово! Вы добавили тату в таблицу tattoo_items.\n\n"
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_items_commands,
        )
        await state.finish()  #  полностью очищает данные

    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)


# -------------------------------TATTOO COMMANDS------------------------------------------------------
async def send_to_view_tattoo_item(id, tattoo_items):
    if tattoo_items == []:
        await bot.send_message(id, MSG_NO_TATTOO_IN_TABLE)
    else:
        for tattoo in tattoo_items:
            msg = (
                f"- Название: {tattoo.name}\n"
                f"- Цена: {tattoo.price}\n"
                f"- Цвет: {tattoo.colored}\n"
                f"- Описание: {tattoo.note}\n"
                f"- Создатель: {tattoo.creator}"
            )

            if tattoo != None:
                with Session(engine) as session:
                    photos = session.scalars(
                        select(TattooItemPhoto).where(
                            TattooItemPhoto.tattoo_item_name == tattoo.name
                        )
                    ).all()
                for photo in photos:
                    await bot.send_photo(id, photo.photo, msg)
            else:
                await bot.send_message(id, msg)


# ----------------------------------/посмотреть_тату---------------------------------- COMPLETE
class FSM_Admin_get_info_tattoo_item(StatesGroup):
    tattoo_name = State()  # назови тату для просмотра


# /посмотреть_тату
async def command_get_info_tattoo(message: types.Message):
    if (
        message.text.lower() in ["посмотреть тату", "/посмотреть_тату"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            tattoo_items = session.scalars(select(TattooItems)).all()

        if tattoo_items == []:
            await message.reply(MSG_NO_TATTOO_IN_TABLE)
        else:
            kb_tattoo_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in tattoo_items:
                kb_tattoo_names.add(item.name)
            await FSM_Admin_get_info_tattoo_item.tattoo_name.set()

            kb_tattoo_names.add(KeyboardButton(LIST_BACK_TO_HOME[0]))
            await message.reply(
                "Какое тату хочешь посмотреть?", reply_markup=kb_tattoo_names
            )


async def get_tattoo_name_for_info(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        tattoo_items = session.scalars(select(TattooItems.name)).all()

    if message.text in tattoo_items:
        with Session(engine) as session:
            tattoo_items = session.scalars(
                select(TattooItems).where(TattooItems.name == message.text)
            ).all()

        await send_to_view_tattoo_item(message.from_user.id, tattoo_items)
        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_tattoo_items_commands,
        )

        await state.finish()
    elif message.text in LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_items_commands
        )


# -----------------------------------/посмотреть_все_тату-------------------------------- COMPLETE
# /посмотреть_все_тату
async def command_get_info_all_tattoo(message: types.Message):
    if (
        message.text.lower() in ["посмотреть все тату", "/посмотреть_все_тату"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            tattoo_items = session.scalars(select(TattooItems)).all()
        await send_to_view_tattoo_item(message.from_user.id, tattoo_items)
        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_tattoo_items_commands,
        )


# /посмотреть_все_мои_тату
async def command_get_info_all_admin_tattoo(message: types.Message):
    if (
        message.text.lower() in ["посмотреть все мои тату", "/посмотреть_все_мои_тату"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            tattoo_items = session.scalars(
                select(TattooItems).where(TattooItems.creator == "admin")
            ).all()

        await send_to_view_tattoo_item(message.from_user.id, tattoo_items)
        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_tattoo_items_commands,
        )


# /посмотреть_мои_тату
async def command_get_info_admin_tattoo(message: types.Message):
    if (
        message.text.lower() in ["посмотреть мои тату", "/посмотреть_мои_тату"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            tattoo_items = session.scalars(
                select(TattooItems).where(TattooItems.creator == "admin")
            ).all()

        if tattoo_items == []:
            await message.reply(
                "Прости, но у тебя пока нет своих тату в таблице. "
                'Данную таблицу можно заполнить через кнопку "добавить тату"'
            )
        else:
            kb_tattoo_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in tattoo_items:
                kb_tattoo_names.add(item.name)
            kb_tattoo_names.add(LIST_BACK_TO_HOME[0])
            await FSM_Admin_get_info_tattoo_item.tattoo_name.set()
            await message.reply(
                "Какое тату хочешь посмотреть?", reply_markup=kb_tattoo_names
            )


# /посмотреть_пользовательские_тату
async def command_get_info_client_tattoo(message: types.Message):
    if (
        message.text.lower()
        in ["посмотреть пользовательские тату", "/посмотреть_пользовательские_тату"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            tattoo_items = session.scalars(
                select(TattooItems).where(TattooItems.creator == "client")
            ).all()
        if tattoo_items == []:
            await message.reply(MSG_NO_TATTOO_IN_TABLE)
            await bot.send_message(
                message.from_id,
                MSG_DO_CLIENT_WANT_TO_DO_MORE,
                reply_markup=kb_admin.kb_tattoo_items_commands,
            )

        else:
            kb_tattoo_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in tattoo_items:
                kb_tattoo_names.add(item.name)
            kb_tattoo_names.add(kb_client.cancel_lst[0])
            await FSM_Admin_get_info_tattoo_item.tattoo_name.set()
            await message.reply(
                "Какое тату хочешь посмотреть?", reply_markup=kb_tattoo_names
            )


async def get_tattoo_name_for_tattoo_info(message: types.Message, state: FSMContext):
    if message.text not in LIST_CANCEL_COMMANDS:
        with Session(engine) as session:
            tattoo_items = session.scalars(
                select(TattooItems).where(TattooItems.name == message.text)
            ).all()
        if tattoo_items == []:
            await message.reply(
                "Таких тату нет. Выбери тату из списка или вернись домой."
            )
        else:
            await send_to_view_tattoo_item(message.from_user.id, tattoo_items)
            await bot.send_message(
                message.from_user.id,
                MSG_DO_CLIENT_WANT_TO_DO_MORE,
                reply_markup=kb_admin.kb_tattoo_items_commands,
            )
            await state.finish()  #  полностью очищает данные
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_tattoo_items_commands,
        )
    else:
        await message.reply("Таких тату нет. Выбери тату из списка или вернись домой.")


# /посмотреть_все_пользовательские_тату
async def command_get_info_all_client_tattoo(message: types.Message):
    if (
        message.text.lower()
        in [
            "посмотреть все пользовательские тату",
            "/посмотреть_все_пользовательские_тату",
        ]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        tattoo_items = await get_info_many_from_table(
            "tattoo_items", "creator", "client"
        )
        await send_to_view_tattoo_item(message.from_user.id, tattoo_items)
        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_tattoo_items_commands,
        )


# ------------------------------------/удалить_тату------------------------------------ COMPLETE


class FSM_Admin_delete_tattoo_item(StatesGroup):
    delete_tattoo_name = State()  # назови тату для удаления


# /удалить_тату
async def delete_info_tattoo_in_table(message: types.Message):
    if (
        message.text.lower() in ["удалить тату", "/удалить_тату"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        tattoo_items = await get_info_many_from_table("tattoo_items")
        if tattoo_items == []:
            await bot.send_message(
                message.from_user.id,
                "Увы, в базе пока нет тату, а значит и удалять нечего",
            )
        else:
            await send_to_view_tattoo_item(message.from_user.id, tattoo_items)
            kb_tattoo_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in tattoo_items:
                kb_tattoo_names.add(item[0])
            kb_tattoo_names.add(KeyboardButton(LIST_BACK_TO_HOME[0]))
            await FSM_Admin_delete_tattoo_item.delete_tattoo_name.set()
            await bot.send_message(
                message.from_user.id,
                "Какую тату хотите удалить?",
                reply_markup=kb_tattoo_names,
            )


async def delete_info_tattoo_in_table_next(message: types.Message, state: FSMContext):
    await delete_info("tattoo_items", "name", message.text)
    await message.reply(
        f"Готово! Вы удалили тату {message.text}. \n"
        f"{MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET}",
        reply_markup=kb_admin.kb_tattoo_items_commands,
    )

    update_data_to_json = {}
    json_name = "tattoo_items"
    with open(f"./db/{json_name}.json", encoding="cp1251") as json_file:
        data = json.load(json_file)

    """ delete_data_to_json = {}    
    with open(f'./db/{json_name}_deleted.json', encoding='cp1251') as json_file:
        data_deleted = json.load(json_file) """

    for i in range(1, len(data)):
        update_data_to_json[str(i)] = data[str(i)]
        if data[str(i)]["tattoo_name"] == message.text:
            # delete_data_to_json[str(i)] = data[str(i)]
            pass

    with open(f"./db/{json_name}.json", "w", encoding="cp1251") as outfile:
        json.dump(update_data_to_json, outfile, ensure_ascii=False, indent=2)

    """ for i in range(1, len(data_deleted)):
        delete_data_to_json[str(i)] = data_deleted[str(i)]
    with open(f'./db/{json_name}_deleted.json', 'w', encoding='cp1251') as outfile:
        json.dump(delete_data_to_json, outfile, ensure_ascii=False, indent=2) """

    await state.finish()


def register_handlers_admin_tattoo_item(dp: Dispatcher):
    # ---------------------------------- TATTOO ITEM COMMAND-------------------------
    dp.register_message_handler(
        get_tattoo_items_and_item_command_list, commands=["татуировки"]
    )
    dp.register_message_handler(
        get_tattoo_items_and_item_command_list,
        Text(equals="Татуировки", ignore_case=True),
        state=None,
    )

    # ---------------------------------------CHANGE TATTOO------------------------------------
    dp.register_message_handler(command_change_tattoo_item, commands=["изменить_тату"])
    dp.register_message_handler(
        command_change_tattoo_item,
        Text(equals="изменить тату", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_tattoo_name_for_changing, state=FSM_Admin_tattoo_item_change.tattoo_name
    )
    dp.register_message_handler(
        get_new_tattoo_item_state, state=FSM_Admin_tattoo_item_change.new_state
    )
    dp.register_message_handler(
        set_new_tattoo_item_state, state=FSM_Admin_tattoo_item_change.new_value
    )
    dp.register_message_handler(
        set_new_tattoo_photo,
        content_types=["photo"],
        state=FSM_Admin_tattoo_item_change.new_photo,
    )

    # ----------------------------------------ADD TATTOO-----------------------------------------
    dp.register_message_handler(
        command_load_tattoo_item, commands=["добавить_тату"], state=None
    )
    dp.register_message_handler(
        command_load_tattoo_item,
        Text(equals="добавить тату", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        load_tattoo_name, state=FSM_Admin_tattoo_item.tattoo_name
    )
    dp.register_message_handler(
        load_tattoo_item_photo,
        content_types=["photo", "text"],
        #  types.ContentType.all(),
        state=FSM_Admin_tattoo_item.tattoo_photo,
    )
    dp.register_message_handler(
        load_tattoo_price, state=FSM_Admin_tattoo_item.tattoo_price
    )
    dp.register_message_handler(
        load_tattoo_colored, state=FSM_Admin_tattoo_item.tattoo_colored
    )
    # dp.register_message_handler(load_tattoo_number_of_details,
    # state=FSM_Admin_tattoo_item.tattoo_number_of_details)
    dp.register_message_handler(
        load_tattoo_note, state=FSM_Admin_tattoo_item.tattoo_note
    )

    dp.register_message_handler(
        command_get_info_all_tattoo, commands=["посмотреть_все_тату"]
    )
    dp.register_message_handler(
        command_get_info_all_tattoo,
        Text(equals="посмотреть все тату", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_all_admin_tattoo, commands=["посмотреть_все_мои_тату"]
    )
    dp.register_message_handler(
        command_get_info_all_admin_tattoo,
        Text(equals="посмотреть все мои тату", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_admin_tattoo, commands=["посмотреть_мои_тату"]
    )
    dp.register_message_handler(
        command_get_info_admin_tattoo,
        Text(equals="посмотреть мои тату", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_all_client_tattoo,
        commands=["посмотреть_все_пользовательские_тату"],
    )
    dp.register_message_handler(
        command_get_info_all_client_tattoo,
        Text(equals="посмотреть все пользовательские тату", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_client_tattoo, commands=["посмотреть_пользовательские_тату"]
    )
    dp.register_message_handler(
        command_get_info_client_tattoo,
        Text(equals="посмотреть пользовательские тату", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_tattoo_name_for_tattoo_info,
        state=FSM_Admin_get_info_tattoo_item.tattoo_name,
    )

    dp.register_message_handler(command_get_info_tattoo, commands=["посмотреть_тату"])
    dp.register_message_handler(
        command_get_info_tattoo,
        Text(equals="посмотреть тату", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_tattoo_name_for_info, state=FSM_Admin_get_info_tattoo_item.tattoo_name
    )

    dp.register_message_handler(delete_info_tattoo_in_table, commands=["удалить_тату"])
    dp.register_message_handler(
        delete_info_tattoo_in_table,
        Text(equals="удалить тату", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        delete_info_tattoo_in_table_next,
        state=FSM_Admin_delete_tattoo_item.delete_tattoo_name,
    )
