from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from prettytable import PrettyTable
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES

from db.db_setter import set_to_table
from db.db_updater import update_info
from db.db_getter import get_info_many_from_table
from handlers.other import *

# from diffusers import StableDiffusionPipeline
# import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup

from handlers.calendar_client import obj
from msg.main_msg import *

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *


# ------------------------------------------------------- GIFTBOX ITEM COMMAND LIST------------------------------------------------------
async def get_giftbox_item_command_list(message: types.Message):
    if (
        message.text.lower() == "гифтбокс продукт"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            MSG_WHICH_COMMAND_TO_EXECUTE,
            reply_markup=kb_admin.kb_giftbox_item_commands,
        )


# -------------------------------------------------------SET GIFTBOX ITEM------------------------------------------------------
class FSM_Admin_giftbox_item(StatesGroup):
    giftbox_name = State()  # назови гифтбокс
    giftbox_photo = State()  # загрузи фото гифтбокс
    giftbox_price = State()  # примерная цена на гифтбокс
    giftbox_note = State()  # напиши описание гифтбокс
    # giftbox_candle_in_stock = State()       # добавить новую свечу или выбрать из готовых
    giftbox_candle_choice = State()  # добавляем свечу в гифтбокс из готовых

    giftbox_candle_name = State()  # назови имя свечи
    giftbox_candle_photo = State()  # загрузи фото свечи
    giftbox_candle_price = State()  # если есть свеча, то какая цена свеча,
    # если свеча нет, то цена 0
    giftbox_candle_note = State()  # описание свечи

    giftbox_candle_state = (
        State()
    )  # есть ли эти свечи сейчас в наличии или надо докупать

    giftbox_tattoo_theme = State()  # если есть тату, то какая тематика

    giftbox_tattoo_note = State()  # впиши описание тату
    giftbox_tattoo_state = (
        State()
    )  # есть ли эти тату сейчас в наличии или надо докупать
    giftbox_sequins_type = State()  # впиши тип блесток тату
    giftbox_sequins_state = (
        State()
    )  # есть ли эти блестки сейчас в наличии или надо докупать


# /добавить_новый_гифтбокс, Команда для добавление гифтбокс итема
async def command_load_giftbox_item(message: types.Message):
    if (
        message.text.lower() in ["/добавить_новый_гифтбокс", "добавить новый гифтбокс"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_giftbox_item.giftbox_name.set()
        await message.reply(
            "Введи название гифтбокса", reply_markup=kb_client.kb_cancel
        )


# Отправляем название гифтбокса
async def load_giftbox_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["giftbox_name"] = message.text
    await FSM_Admin_giftbox_item.next()
    await message.reply(
        MSG_CLIENT_LOAD_PHOTO, reply_markup=kb_client.kb_cancel
    )


# Отправляем фото гифтбокса
async def load_giftbox_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["giftbox_photo"] = message.photo[0].file_id
    await FSM_Admin_giftbox_item.next()
    await message.reply(
        "Введи примерную цену на гифтбокс", reply_markup=kb_admin.kb_price
    )


# TODO добавить возможность вбить другую цену
# Отправляем стоимость гифтбокса
async def load_giftbox_price(message: types.Message, state: FSMContext):
    if message.text in kb_admin.price_lst:
        async with state.proxy() as data:
            data["giftbox_price"] = int(message.text)

        await FSM_Admin_giftbox_item.next()
        await message.reply(
            "Введи описание гифтбокса", reply_markup=kb_client.kb_cancel
        )
    else:
        await message.reply(
            MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


# Отправляем описание гифтбокса
async def load_giftbox_note(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["giftbox_note"] = message.text
    await FSM_Admin_giftbox_item.next()
    await message.reply(
        "Хорошо, теперь необходимо добавить свечу в гифтбокс. "
        f"❔ Добавить в этот гифтбокс новую свечу или выбрать из готовых?",
        reply_markup=kb_admin.kb_candle_choice,
    )


async def get_giftbox_candle_choice(message: types.Message, state: FSMContext):
    await FSM_Admin_giftbox_item.next() #-> get_giftbox_candle_name
    if message.text == kb_admin.candle_choice["new"]:
        await FSM_Admin_giftbox_item.next()
        await message.reply("Назови имя свечи", reply_markup=kb_client.kb_cancel)

    elif message.text == kb_admin.candle_choice["having"]:
        kb_candle_names = ReplyKeyboardMarkup(resize_keyboard=True)
        with Session(engine) as session:
            candle_items = session.scalars(select(CandleItems)).all()
        for item in candle_items:
            kb_candle_names.add(KeyboardButton(item.name))
        await message.reply("Выбери имя готовой свечи", reply_markup=kb_candle_names)


async def get_giftbox_candle_name(message: types.Message, state: FSMContext):

    with Session(engine) as session:
        candle_items = session.scalars(select(CandleItems.name)).all()
        
    if message in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_admin.kb_price_list_commands,
        )
    elif message.text in candle_items:
        async with state.proxy() as data:
            with Session(engine) as session:
                candle = session.scalars(select(CandleItems).where(CandleItems.name == message.text)).one()
            data['candle_id'] = candle.id
            data["candle_name"] = candle.name
            data["candle_photo"] = candle.photo
            data["candle_price"] = candle.price
            data["candle_note"] = candle.note
        for i in range(4):
            await FSM_Admin_giftbox_item.next() #-> giftbox_candle_state
        await message.reply(
            "❔ Есть ли эти свечи сейчас в наличии или надо докупать?",
            reply_markup=kb_admin.kb_in_stock,
        )

    else:
        with Session(engine) as session:
            candles_name = session.scalars(select(CandleItems.name)).all()
        if message.text not in candles_name:
            async with state.proxy() as data:
                data["giftbox_candle_name"] = message.text
            await FSM_Admin_giftbox_item.next() #-> load_giftbox_candle_photo
            await message.reply("Загрузи фото свечи")
        else:
            await bot.send_message(message.from_id, f'У тебя уже есть свеча с названием {message.text}. '
                'Введи другое название')


# Отправляем фото свечи в гифтбоксе
async def load_giftbox_candle_photo(message: types.Message, state: FSMContext):
    if message.content_type == 'photo':
        async with state.proxy() as data:
            data["candle_photo"] = message.photo[0].file_id
        await FSM_Admin_giftbox_item.next()
        await message.reply("Введи примерную цену свечи", reply_markup=kb_admin.kb_price)
        
    elif message.content_type == 'text':
        if message in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
            await state.finish()
            await message.reply(
                f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
                reply_markup=kb_admin.kb_giftbox_item_commands,
            )


# Отправляем стоимость свечи в гифтбоксе
async def load_giftbox_candle_price(message: types.Message, state: FSMContext):
    if message.text == kb_admin.another_price_lst[0]:
        await bot.send_message(
            message.from_id,
            MSG_ADMIN_SET_ANOTHER_PRICE,
            reply_markup=kb_admin.kb_another_price_full,
        )
    elif message.text in kb_admin.price_lst + kb_admin.another_price_full_lst:
        async with state.proxy() as data:
            data["candle_price"] = int(message.text)

            await FSM_Admin_giftbox_item.next() #-> giftbox_candle_note
            await message.reply("Введи описание свечи в гифтбоксе", reply_markup= kb_client.kb_cancel)
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def giftbox_candle_note(message: types.Message, state: FSMContext):
    if message in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_admin.kb_giftbox_item_commands,
        )
    else:
        async with state.proxy() as data:
            data["candle_note"] = message.text
        await message.reply(
            "❔ Есть ли эти свечи сейчас в наличии или надо докупать?",
            reply_markup=kb_admin.kb_in_stock,
        )


# есть ли эти свечи сейчас в наличии или надо докупать
async def giftbox_candle_state(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.in_stock_button.values()):
        async with state.proxy() as data:
            data["candle_quantity"] = 0 if message.text == kb_admin.in_stock_button["not_in_stock"] else 1
            with Session(engine) as session:
                new_candle_item = CandleItems(
                    name= data['candle_name'],
                    photo= data['candle_photo'],
                    price= data['candle_price'],
                    note= data['candle_note'],
                    quantity= int(data["candle_quantity"])
                )
                session.add(new_candle_item)
                session.commit()
                
            with Session(engine) as session:
                candle_id = session.scalars(select(CandleItems).where(CandleItems.name == data['candle_name'])).one().id
                data["candle_id"] = candle_id
        
        kb_tattoo_theme = ReplyKeyboardMarkup(resize_keyboard=True)
        for theme in TATTOO_THEMES:
            kb_tattoo_theme.add(KeyboardButton(theme))
        await FSM_Admin_giftbox_item.next() #-> load_tattoo_theme
        await message.reply(
            f"Хорошо, а теперь добавь тему тату в этом гифтбоксе."
            f" На данный момент у тебя есть эти темы: {', '.join(TATTOO_THEMES)}.\n"
            f"❔ Какую выбираешь?",
            reply_markup=kb_tattoo_theme,
        )
    elif message in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_admin.kb_giftbox_item_commands,
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# Отправляем тему тату в гифтбоксе
async def load_tattoo_theme(message: types.Message, state: FSMContext):
    if message.text != "Другая":
        async with state.proxy() as data:
            data["tattoo_theme"] = message.text
        await FSM_Admin_giftbox_item.next() #-> load_giftbox_tattoo_other_theme
        await message.reply(f"Выбрана тема: {message.text}. Введи описание тату")
        
    elif message.text == "Другая":
        await message.reply("❔ Какая тема будет у тату?", kb_client.kb_cancel)
        
    elif message in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_admin.kb_giftbox_item_commands,
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# Отправляем описание тату в гифтбоксе
async def load_giftbox_tattoo_note(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.in_stock_button.values()):
        async with state.proxy() as data:
            data["tattoo_note"] = message.text
        await FSM_Admin_giftbox_item.next()
        await message.reply(
            "❔ Есть ли эти тату сейчас в наличии или надо докупать?",
            reply_markup=kb_admin.kb_in_stock,
        )  # in_stock_button = ['Есть в наличии', 'Нет в наличии, нужно докупать']
        
    elif message in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_admin.kb_giftbox_item_commands,
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# есть ли эти тату сейчас в наличии или надо докупать
async def load_giftbox_tattoo_state(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.in_stock_button.values()):
        async with state.proxy() as data:
            data["tattoo_quantity"] = 0 if message.text == kb_admin.in_stock_button["not_in_stock"] else 1
        await FSM_Admin_giftbox_item.next() # -> load_giftbox_sequins_type
        
        kb_sequin_types = ReplyKeyboardMarkup(resize_keyboard=True)
        with Session(engine) as session:
            sequin_types = session.scalars(select(SequinsItems)).all()
            
        for type in sequin_types:
            kb_sequin_types.add(type.name)
        await message.reply("Выбери тип блесток в гифтбоксе", reply_markup= kb_sequin_types)
        
    elif message in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_admin.kb_giftbox_item_commands,
        )
        
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# впиши тип блесток
async def load_giftbox_sequins_type(message: types.Message, state: FSMContext):
    if message.text in kb_admin.sequin_types:
        async with state.proxy() as data:
            data["sequins_type"] = message.text
        
            with Session(engine) as session:
                data["sequins_id"] = session.scalars(select(SequinsItems)
                    .where(SequinsItems.name == message.text)).one().id
        
        await FSM_Admin_giftbox_item.next()
        await message.reply(
            "❔ Есть ли эти блестки сейчас в наличии или надо докупать?",
            reply_markup=kb_admin.kb_in_stock,
        )  # ['Есть в наличии', 'Нет в наличии']


# впиши статус блесток
async def load_giftbox_sequins_state(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.in_stock_button.values()):
        async with state.proxy() as data:
            data["sequins_state"] = message.text
            sequins_id = data["sequins_id"] 
        
        
        with Session(engine) as session:
            seq = session.get(SequinsItems, sequins_id)
            seq.state = message.text
            
            new_giftbox_item = GiftboxItems(
                name= data['giftbox_name'],
                photo= GiftboxItemsPhoto(photo= data['giftbox_photo']),
                price= data['giftbox_price'],
                giftbox_note= data["giftbox_note"],
                candle_id= data['candle_id'],
                tattoo_note= data['tattoo_note'],
                tattoo_quantity= int(data['tattoo_quantity']),
                sequins_id= sequins_id
            )
            session.add(new_giftbox_item)
            session.commit()
        
        await message.reply(
            f"Готово! Вы добавили гифтбокс {data['giftbox_name']} в таблицу!", reply_markup=kb_admin.kb_giftbox_item_commands
        )
        await state.finish()  #  полностью очищает данные
    elif message in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_admin.kb_giftbox_item_commands,
        )
        
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# ------------------------------------GIFTBOX ITEM COMMANDS--------------------------------
async def send_to_view_gifbox_item(message: types.Message, items: ScalarResult['GiftboxItems']) -> None:
    if items == []:
        await message.reply("Пока у вас нет гифтбоксов в таблице")
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
    else:
        headers = [
            "№",
            "Название",
            "Цена",
            "Описание",
            "Название свечи",
            "Цена свечи",
            "Статус свечи",
            "Тату тема",
            "Описание тату",
            "Статус тату",
            "Блестки",
            "Статус блесток"
        ]
        for item in items:
            table = PrettyTable(
                headers, left_padding_width=1, right_padding_width=1
            )  # Определяем таблицу
            

            with Session(engine) as session:
                candle = session.get(CandleItems, item.candle_id)
                sequins = session.get(SequinsItems, item.sequins_id)
                table.add_row(
                    [
                        item.id,
                        item.name,
                        item.price,
                        item.giftbox_note,
                        candle.name,
                        candle.price,
                        f"Нет в наличии" if candle.quantity == 0 else f"В наличии {candle.quantity} штук",
                        item.tattoo_theme,
                        item.tattoo_note,
                        f"Нет в наличии" if item.tattoo_quantity == 0 else f"В наличии {item.tattoo_quantity} штук",
                        sequins.name,
                        f"Нет в наличии" if sequins.quantity == 0 else f"В наличии {sequins.quantity} штук",
                        
                    ]
                )
            await bot.send_message(
                message.from_id, f"<pre>{table}</pre>", parse_mode=types.ParseMode.HTML
            )
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_clients_commands,
        )
    ''' for ret in items:
        await bot.send_photo(
            message.from_user.id,
            ret[1],
            f'- Гифтбокс {number_deleted_order} с названием "{ret[0]}"\n'
            f"- Цена гифтбокса: {ret[2]}\n"
            f"- Описание гифтбокса: {ret[3]}\n"
            f"- Название свечи в гитфбоксе: {ret[4]}\n"
            f"- Цена свечи в гитфбоксе: {ret[6]}\n"
            f"- Описание свечи в гитфбоксе: {ret[7]}\n"
            f"- Статус свечи в гитфбоксе: {ret[8]}\n"
            f"- Тату тема в гитфбоксе: {ret[9]}\n"
            f"- Описание тату в гитфбоксе: {ret[10]}\n"
            f"- Статус тату в гитфбоксе: {ret[11]}\n"
            f"- Блестки в гитфбоксе: {ret[12]}\n"
            f"- Статус блесток в гитфбоксе: {ret[13]}\n",
        )
    '''
        



# ------------------------------GIFTBOX ITEM COMMANDS посмотреть_все_гифтбоксы---------------------COMPLETE
# /посмотреть_все_гифтбоксы
async def command_get_info_giftboxes_item(message: types.Message):
    if (
        message.text.lower()
        in ["/посмотреть_все_гифтбоксы", "посмотреть все гифтбоксы"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(select(GiftboxItems)).all()

        await send_to_view_gifbox_item(message, orders)


# ------------------------------GIFTBOX ITEM COMMANDS посмотреть_гифтбокс---------------------COMPLETE
# /посмотреть_гифтбокс
class FSM_Admin_get_info_giftbox_items(StatesGroup):
    giftbox_item_name = State()


# /посмотреть_гифтбокс
async def command_get_info_giftbox_item(message: types.Message):
    if (
        message.text.lower() in ["/посмотреть_гифтбокс", "посмотреть гифтбокс"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(select(GiftboxItems)).all()
        
        if orders == []:
            await message.reply("Пока у вас нет гифтбоксов в таблице")
            await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        else:
            kb_giftbox_names = ReplyKeyboardMarkup(resize_keyboard=True)
            await FSM_Admin_get_info_giftbox_items.giftbox_item_name.set()
            for order in orders:
                kb_giftbox_names.add(KeyboardButton(order.name))
                await bot.send_message(
                    message.from_user.id,
                    f"❔ Какой гифтбокс хочешь посмотреть?",
                    reply_markup=kb_giftbox_names,
                )


async def get_name_for_info_giftbox_item(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(select(GiftboxItems)).all()
    giftbox_names_lst = []
    for order in orders:
        giftbox_names_lst.append(order.name)
    
    if message.text in giftbox_names_lst:
        with Session(engine) as session:
            orders = session.scalars(select(GiftboxItems).where(GiftboxItems.name == message.text)).one()
            
        await send_to_view_gifbox_item(message, orders)
        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_main,
        )
        await state.finish()
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# -------------------------------------------------------GIFTBOX ITEM COMMANDS поменять_цену_гифтбокса---------------------COMPLETE
# /посмотреть_гифтбокс
class FSM_Admin_change_price_giftbox_items(StatesGroup):
    giftbox_item_number = State()
    giftbox_item_price = State()
    giftbox_item_other_price = State()


# /поменять_цену_гифтбокса
async def command_change_price_giftbox_item(message: types.Message):
    if (
        message.text.lower() in ["/поменять_цену_гифтбокса", "поменять цену гифтбокса"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        orders_into_table = await get_info_many_from_table("giftbox_items")
        kb_giftbox_numbers = ReplyKeyboardMarkup(resize_keyboard=True)

        if orders_into_table is None:
            await message.reply("Пока у вас нет гифтбоксов в таблице(")
        else:
            await FSM_Admin_change_price_giftbox_items.giftbox_item_number.set()

            for ret in orders_into_table:
                kb_giftbox_numbers.add(KeyboardButton(ret[0]))
            await send_to_view_gifbox_item(message, orders_into_table)
            await bot.send_message(
                message.from_user.id,
                f"❔ У какого гифтбокса хочешь поменять цену?",
                reply_markup=kb_giftbox_numbers,
            )


# Определяем имя гифтбокса для изменения цены
async def get_new_price_giftbox_item(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["giftbox_item_name"] = message.text
    await FSM_Admin_change_price_giftbox_items.next()
    await message.reply(
        "❔ На какую цену хочешь поменять?", reply_markup=kb_admin.kb_price
    )


# Определяем новую цену гифтбокса
async def set_new_price_giftbox_item(message: types.Message, state: FSMContext):
    if message.text.lower() != "другая":
        async with state.proxy() as data:
            giftbox_item_name = data["giftbox_item_name"]

        await update_info(
            "giftbox_items", "name", giftbox_item_name, "price", message.text
        )
        await message.reply(
            f"Готово! Вы обновили цену  {giftbox_item_name} на {message.text}",
            reply_markup=kb_admin.kb_main,
        )
        await state.finish()  #  полностью очищает данные
    else:
        await FSM_Admin_change_price_giftbox_items.next()
        await message.reply(MSG_ADMIN_SET_ANOTHER_PRICE)


# Определяем новую цену гифтбокса
async def set_new_other_price_giftbox_item(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        giftbox_item_name = data["giftbox_item_name"]

    await update_info("giftbox_items", "name", giftbox_item_name, "price", message.text)
    await message.reply(
        f"Готово! Вы обновили цену  {giftbox_item_name} на {message.text}",
        reply_markup=kb_admin.kb_main,
    )
    await state.finish()  #  полностью очищает данные


def register_handlers_admin_giftbox_item(dp: Dispatcher):
    # -------------------------------------------------------CREATE GIFTBOX ITEM------------------------------------------------------
    dp.register_message_handler(
        get_giftbox_item_command_list, commands="гифтбокс_продукт", state=None
    )
    dp.register_message_handler(
        get_giftbox_item_command_list,
        Text(equals="гифтбокс продукт", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_load_giftbox_item, commands="добавить_новый_гифтбокс", state=None
    )
    dp.register_message_handler(
        command_load_giftbox_item,
        Text(equals="добавить новый гифтбокс", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        load_giftbox_name, state=FSM_Admin_giftbox_item.giftbox_name
    )
    dp.register_message_handler(
        load_giftbox_photo,
        content_types=["photo"],
        state=FSM_Admin_giftbox_item.giftbox_photo,
    )
    dp.register_message_handler(
        load_giftbox_price, state=FSM_Admin_giftbox_item.giftbox_price
    )
    dp.register_message_handler(
        load_giftbox_note, state=FSM_Admin_giftbox_item.giftbox_note
    )
    dp.register_message_handler(
        get_giftbox_candle_choice, state=FSM_Admin_giftbox_item.giftbox_candle_choice
    )
    dp.register_message_handler(
        get_giftbox_candle_name, state=FSM_Admin_giftbox_item.giftbox_candle_name
    )
    dp.register_message_handler(
        load_giftbox_candle_photo,
        content_types=["photo"],
        state=FSM_Admin_giftbox_item.giftbox_candle_photo,
    )
    dp.register_message_handler(
        load_giftbox_candle_price, state=FSM_Admin_giftbox_item.giftbox_candle_price
    )
    dp.register_message_handler(
        giftbox_candle_note, state=FSM_Admin_giftbox_item.giftbox_candle_note
    )
    dp.register_message_handler(
        giftbox_candle_state, state=FSM_Admin_giftbox_item.giftbox_candle_state
    )
    dp.register_message_handler(
        load_tattoo_theme, state=FSM_Admin_giftbox_item.giftbox_tattoo_theme
    )
    dp.register_message_handler(
        load_giftbox_tattoo_note, state=FSM_Admin_giftbox_item.giftbox_tattoo_note
    )
    dp.register_message_handler(
        load_giftbox_tattoo_state, state=FSM_Admin_giftbox_item.giftbox_tattoo_state
    )
    dp.register_message_handler(
        load_giftbox_sequins_type, state=FSM_Admin_giftbox_item.giftbox_sequins_type
    )
    dp.register_message_handler(
        load_giftbox_sequins_state, state=FSM_Admin_giftbox_item.giftbox_sequins_state
    )
    # -------------------------------------------------------COMMANDS GIFTBOX ITEM------------------------------------------------------

    dp.register_message_handler(
        command_change_price_giftbox_item,
        commands="поменять_цену_гифтбокса",
        state=None,
    )
    dp.register_message_handler(
        command_change_price_giftbox_item,
        Text(equals="поменять цену гифтбокса", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_new_price_giftbox_item,
        state=FSM_Admin_change_price_giftbox_items.giftbox_item_number,
    )
    dp.register_message_handler(
        set_new_price_giftbox_item,
        state=FSM_Admin_change_price_giftbox_items.giftbox_item_price,
    )
    dp.register_message_handler(
        set_new_other_price_giftbox_item,
        state=FSM_Admin_change_price_giftbox_items.giftbox_item_other_price,
    )

    dp.register_message_handler(
        command_get_info_giftboxes_item, commands="посмотреть_все_гифтбоксы", state=None
    )
    dp.register_message_handler(
        command_get_info_giftboxes_item,
        Text(equals="посмотреть все гифтбоксы", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_giftbox_item, commands="посмотреть_гифтбокс", state=None
    )
    dp.register_message_handler(
        command_get_info_giftbox_item,
        Text(equals="посмотреть гифтбокс", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_name_for_info_giftbox_item,
        state=FSM_Admin_get_info_giftbox_items.giftbox_item_name,
    )
