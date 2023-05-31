from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from prettytable import PrettyTable
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import (
    generate_random_order_number,
    generate_random_code,
    CODE_LENTH,
    ORDER_CODE_LENTH,
    ADMIN_NAMES,
    CALENDAR_ID,
    DARA_ID,
)

from handlers.other import *

from validate import check_pdf_document_payment, check_photo_payment

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, date, time, timedelta
from aiogram.types.message import ContentType
from aiogram_calendar import (
    simple_cal_callback,
    SimpleCalendar,
    dialog_cal_callback,
    DialogCalendar,
)
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback
from aiogram_timepicker import result, carousel, clock


from handlers.calendar_client import obj
from msg.main_msg import *


# -----------------------------------  SKETCH COMMANDS LIST-----------------------------------
async def get_tattoo_sketch_order_and_item_command_list(message: types.Message):
    if (
        message.text.lower() in ["эскиз заказы", "/эскиз_заказы"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            "Какую команду заказов эскиз хочешь выполнить?",
            reply_markup=kb_admin.kb_tattoo_sketch_commands,
        )


# --------------------------------------  SKETCH COMMANDS -----------------------------------
async def send_to_view_sketch_order(
    message: types.Message, orders: ScalarResult["Orders"]
):
    if orders == []:
        await bot.send_message(
            message.from_id,
            MSG_NO_ORDER_IN_TABLE,
            reply_markup=kb_admin.kb_tattoo_sketch_commands,
        )
    else:
        headers = [
                "№",
                "Тип заказа",
                "Номер заказа",
                "Время заказа",
                "Описание",
                "Пользователь"
                "Статус",
            ]
        table = PrettyTable(
            headers, left_padding_width=1, right_padding_width=1
        )
        # TODO сделать нормальную pretty table
        # TODO сделать нормальный вывод изображений эскиза
        for order in orders:
            with Session(engine) as session:
                user = session.scalars(
                    select(User).where(User.telegram_id == order.user_id)
                ).one()
            # Определяем таблицу
            note = order.order_note if len(order.order_note) < 10 else order.order_note[:10]
            table.add_row(
                [
                    order.id,
                    order.order_type,
                    order.order_number,
                    order.creation_date.strftime('%H:%M %d/%m/%Y'),
                    note,
                    user.telegram_name,
                ]
            )
        await bot.send_message(
            message.from_id, f"<pre>{table}</pre>", parse_mode=types.ParseMode.HTML
        )
        """  message_to_send = (
            f"№ Заказа эскиза {order.order_number} от {order.creation_date.strftime('%H:%M %d/%m/%Y')}\n"
            f"- Описание эскиза: {order.order_note}\n"
            f"- Состояние заказа: {order.order_state}\n"
            f"- Имя пользователя: {username}\n"
            f"- Telegram пользователя: {username_telegram}\n"
            f"- Телефон пользователя: {username_phone}\n"
        )

        try:
            if "|" not in order[2]:
                await bot.send_photo(
                    message.from_user.id, order[2], message_to_send
                )
            else:
                media = []

                for i in range(len(order[2].split("|")) - 1):
                    media.append(
                        types.InputMediaPhoto(
                            order[2].split("|")[i], message_to_send
                        )
                    )
                # print(f'media: {media}\n\norder[2]:{order[2]}')
                await bot.send_chat_action(
                    message.chat.id, types.ChatActions.UPLOAD_DOCUMENT
                )
                await bot.send_media_group(message.chat.id, media=media)
                await bot.send_message(message.from_id, message_to_send)
        except:
                await bot.send_message(message.from_id, message_to_send) """
        await bot.send_message(
            message.from_user.id,
            f"Всего заказов: {len(orders)}",
            reply_markup=kb_admin.kb_tattoo_sketch_commands,
        )



class FSM_Admin_get_info_sketch_orders(StatesGroup):
    order_state = State()

# ---------------------------------- посмотреть_эскиз_заказы-----------------------------------
# /посмотреть_эскиз_заказы
async def command_get_info_sketch_orders(message: types.Message):
    # print("ищем заказы в таблице tattoo_sketch_orders")
    if (
        message.text in ["посмотреть эскиз заказы", "/посмотреть_эскиз_заказы"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_get_info_sketch_orders.order_state.set()
        await bot.send_message(
            message.from_id, 
            MSG_WHITH_ORDER_STATE_ADMIN_WANT_TO_SEE, 
            reply_markup=kb_admin.kb_order_statuses,
        )


async def get_sketch_order_state(message: types.Message, state: FSMContext):
    if message.text in kb_admin.statuses_order_lst:
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders)
                    .where(Orders.order_type == "эскиз")
                    .where(Orders.order_state == message.text)
            ).all()
        await send_to_view_sketch_order(message, orders)
        await state.finish()
        await bot.send_message(
            message.from_id, 
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_admin.kb_tattoo_sketch_commands)
        
    elif message.text in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.giftbox_order_commands,
        )

    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_TO_SEND)


# ------------------------------------- посмотреть_эскиз_заказ-----------------------------------
class FSM_Admin_command_get_info_sketch_order(StatesGroup):
    order_name = State()


# /посмотреть_эскиз_заказ
async def command_get_info_sketch_order(message: types.Message):
    if (
        message.text in ["посмотреть эскиз заказ", "/посмотреть_эскиз_заказ"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders).where(Orders.order_type == "эскиз")
            ).all()

        kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
        await FSM_Admin_command_get_info_sketch_order.order_name.set()

        for order in orders:
            kb_orders.add(
                KeyboardButton(
                    f'№{order.order_number} {order.order_state}'
                )
            )
        kb_orders.add(kb_client.back_btn)
        await bot.send_message(
            message.from_user.id,
            f"Какой заказ хочешь посмотреть?",
            reply_markup=kb_orders,
        )


async def get_name_for_view_sketch_order(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders).where(Orders.order_type == "эскиз")
        ).all()
    order_list = []
    for order in orders:
        order_list.append(
            f'№{order.order_number} {order.order_state}'
        )

    if message.text in order_list:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == message.text.split()[0][1:])
            ).all()
        await send_to_view_sketch_order(message, order)
        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_tattoo_sketch_commands,
        )
        await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_COMMANDS:
        await message.reply(
            f"{MSG_BACK_TO_HOME}", reply_markup=kb_admin.kb_tattoo_sketch_commands
        )
        await state.finish()

    else:
        await message.reply('Пожалуйста, выбери заказ из списка или нажми "Назад"')


# -------------------------------------------- удалить_эскиз_заказ---------------------------------
class FSM_Admin_delete_sketch_order(StatesGroup):
    order_number = State()


# /удалить_эскиз_заказ - полное удаление заказа из таблицы
async def command_delete_info_sketch_order(message: types.Message):
    if (
        message.text in ["удалить эскиз заказ", "/удалить_эскиз_заказ"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders).where(Orders.order_type == "эскиз")
            ).all()

        if orders == []:
            await message.reply(MSG_NO_ORDER_IN_TABLE)
            await bot.send_message(
                message.from_id,
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_tattoo_sketch_commands,
            )
        else:
            await bot.send_message(message.from_id, MSG_DELETE_FUNCTION_NOTE)
            kb_sketch_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
            for order in orders:
                # выводим наименования тату
                kb_sketch_order_numbers.add(
                    KeyboardButton(
                        f'{order.id}) №{order.order_number} "{order.order_name}" {order.order_state}'
                    )
                )

            kb_sketch_order_numbers.add(KeyboardButton("Назад"))
            await FSM_Admin_delete_sketch_order.order_number.set()
            await message.reply(
                "Какой заказ хотите удалить?", reply_markup=kb_sketch_order_numbers
            )


async def delete_info_sketch_orders(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders).where(Orders.order_type == "эскиз")
        ).all()
    order_kb_lst = []
    for order in orders:
        order_kb_lst.append(
            f'{order.id}) №{order.order_number} "{order.order_name}" {order.order_state}'
        )

    if message.text in order_kb_lst:
        with Session(engine) as session:
            order = session.get(Orders, message.text.split(")")[0])
            session.delete(order)
            session.commit()

        await message.reply(f"Заказ эскиза {message.text.split()[1][1:]} удален")
        await bot.send_message(
            message.from_user.id,
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_sketch_commands,
        )
        await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_sketch_commands
        )
        await state.finish()
    else:
        await bot.send_message(
            message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


# ------------------------------ посмотреть активные эскиз заказы-----------------------------------
# 'посмотреть активные эскиз заказы',
async def command_get_info_opened_sketch_orders(message: types.Message):
    if (
        message.text
        in ["посмотреть активные эскиз заказы", "/посмотреть_активные_эскиз_заказы"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders)
                .where(Orders.order_type == "эскиз")
                .where(
                    Orders.order_state.in_(
                        [STATES["open"], STATES["processed"], STATES["paid"]]
                    )
                )
            ).all()
        await send_to_view_sketch_order(message, orders)
        await bot.send_message(
            message.from_user.id,
            f"Всего активных заказов: {len(orders)}",
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )


# --------------------------- посмотреть активные эскиз заказы-----------------------------------
# /посмотреть_закрытые_эскиз_заказы
async def command_get_info_closed_sketch_orders(message: types.Message):
    if (
        message.text
        in ["посмотреть закрытые эскиз заказы", "/посмотреть_закрытые_эскиз_заказы"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders)
                .where(Orders.order_type == "эскиз")
                .where(Orders.order_state.in_(list(STATES["closed"].values())))
            ).all()
        await send_to_view_sketch_order(message, orders)


class FSM_Admin_command_create_new_sketch_order(StatesGroup):
    get_description = State()
    get_photo_sketch = State()
    get_username_telegram = State()
    get_price = State()
    get_state = State()
    get_check = State()


# добавить эскиз заказ
async def command_create_new_sketch_order(message: types.Message):
    if (
        message.text.lower() in ["добавить эскиз заказ", "/добавить_эскиз_заказ"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_command_create_new_sketch_order.get_description.set()  # -> get_new_sketch_description
        await bot.send_message(
            message.from_id,
            "Ты ввела команду по созданию нового заказа эскиза переводного тату. \n\n"
            "Данный заказ состоит из:\n"
            "1) Добавление описания нового эскиза, \n"
            "2) Добавление фотографий нового эскиза\n"
            "3) Добавление телеграма клиента\n"
            "4) Добавление состояния заказа - оплачен или нет\n"
            "5) Возможность добавления чека, если заказ оплачен",
        )
        await bot.send_message(
            message.from_id,
            "Введи описание для нового эскиза",
            reply_markup=kb_client.kb_cancel,
        )


async def fill_sketch_order_table(data: dict, message: types.Message):
    with Session(engine) as session:
        new_sketch = Orders(
            order_type="эскиз",
            order_photo=data["sketch_photo_lst"],
            order_note=data["sketch_description"],
            order_state=data["state"],
            order_number=data["tattoo_sketch_order_number"],
            creation_date=data["creation_date"],
            price=data["price"],
            check_document=data["check_document"],
            username=data["telegram"],
        )
        session.add(new_sketch)
        session.commit()

    date = data["creation_time"]

    event = await obj.add_event(
        CALENDAR_ID,
        f"Новый эскиз заказ № {data['id']}",
        "Описание эскиза: "
        + data["sketch_description"]
        + " \n"
        + "Имя клиента:"
        + data["telegram"],
        f'{date.strftime("%Y-%m-%dT%H:%M:%S")}',  # '2023-02-02T09:07:00',
        f'{date.strftime("%Y-%m-%dT%H:%M:%S")}',  # '2023-02-03T17:07:00'
    )

    await message.reply(
        "🎉 Отлично, заказ на эскиз оформлен!\n"
        f"Номер твоего заказа эскиза {data['id']}\n\n"
        f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
        reply_markup=kb_admin.kb_tattoo_sketch_commands,
    )


async def fill_client_table(data: dict, message: types.Message):
    with Session(engine) as session:
        client = session.scalars(
            select(User).where(User.telegram_name == data["telegram"])
        ).one()

    if client == []:
        with Session(engine) as session:
            new_user = User(
                name=data["username"],
                telegram_id=None,
                telegram_name=data["telegram"],
                phone=data["phone"],
            )
            session.add(new_user)
            session.commit()
        await message.reply(
            f"Ты успешно добавила нового клиента! {MSG_DO_CLIENT_WANT_TO_DO_MORE}"
        )
    await message.reply(
        f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
        reply_markup=kb_admin.kb_tattoo_sketch_commands,
    )


async def get_new_sketch_description(message: types.Message, state: FSMContext):
    tattoo_sketch_order_number = await generate_random_order_number(CODE_LENTH)
    async with state.proxy() as data:
        data["first_photo"] = False
        data["tattoo_sketch_order_number"] = tattoo_sketch_order_number
        data["sketch_photo_lst"] = []
        data["state"] = STATES["open"]
        data["check_document"] = None

    if message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_sketch_commands
        )

        """ elif message.text == kb_client.yes_str:
        await FSM_Admin_command_create_new_sketch_order.next()
        await bot.send_message(message.from_id, 'Хорошо, добавь фото эскиза',
            reply_markup=kb_client.kb_cancel)
        
        elif message.text == kb_client.no_str:
            for i in range(2):
                await FSM_Admin_command_create_new_sketch_order.next()
            await bot.send_message(message.from_id,
                'Хорошо, закончим с добавлением фотографий для нового эскиза.\n\n'\
                'Для какого пользователя заказ?\n'\
                'Введи его имя или телеграм (с символом \"@\") или ссылку с \"https://t.me/\".\n\n',
                reply_markup= kb_admin.kb_admin_add_name_or_telegram_for_new_order
            ) 
        """
    else:
        await FSM_Admin_command_create_new_sketch_order.next()  # -> get_photo_sketch
        async with state.proxy() as data:
            data["sketch_description"] = message.text
        await bot.send_message(
            message.from_id,
            "Пожалуйста, добавь фото для нового эскиза",
            reply_markup=kb_client.kb_cancel,
        )


async def get_photo_sketch(message: types.Message, state: FSMContext):
    if message.content_type == "text":
        if message.text in LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(
                MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_sketch_commands
            )
        elif message.text == kb_client.yes_str:
            async with state.proxy() as data:
                data["first_photo"] = True
            await bot.send_message(
                message.from_id,
                "Добавь еще одно фото через файлы",
                reply_markup=kb_client.kb_cancel,
            )

        elif message.text == kb_client.no_str:
            await FSM_Admin_command_create_new_sketch_order.next()  # -> get_username_telegram
            await bot.send_message(
                message.from_id,
                "Хорошо, закончим с добавлением фотографий для нового эскиза.\n\n"
                "Для какого пользователя заказ?\n"
                'Введи его имя или телеграм (с символом "@") или ссылку с "https://t.me/".\n\n',
                #'P.s. Нажимая на пользователя в ТГ сверху будет его имя. '\
                #'А имя с символом \"@\" - ссылка на телеграм',
                reply_markup=kb_client.kb_cancel,
            )
        else:
            await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)

    if message.content_type == "photo":
        async with state.proxy() as data:
            data["sketch_photo_lst"].append(
                OrderPhoto(
                    photo=message.photo[0].file_id,
                    order_number=None,
                    telegram_user_id=None,
                )
            )

        await bot.send_message(
            message.from_id,
            "Хочешь добавить еще фото?",
            reply_markup=kb_client.kb_yes_no,
        )


async def get_username_telegram(message: types.Message, state: FSMContext):
    if "@" in message.text or "https://t.me/" in message.text:
        async with state.proxy() as data:
            if "@" in message.text:
                data["username"] = message.text.split("@")[1]
                data["telegram"] = message.text

            else:
                data["username"] = message.text.split("/")[3]
                data["telegram"] = "@" + message.text.split("/")[3]
            with Session(engine) as session:
                client = session.scalars(
                    select(User).where(User.telegram_name == data["telegram"])
                ).all()

            if client == []:
                await bot.send_message(
                    message.from_id,
                    "Хочешь добавить телефон пользователя?",
                    reply_markup=kb_client.kb_yes_no,
                )
            else:
                await FSM_Admin_command_create_new_sketch_order.next()  # -> get_sketch_price
                await bot.send_message(
                    message.from_id,
                    "Добавь цену эскиза переводного тату",
                    reply_markup=kb_admin.kb_price,
                )

    elif message.text == kb_client.yes_str:
        await bot.send_message(
            message.from_id,
            "Отправь телефон пользователя",
            reply_markup=kb_client.kb_cancel,
        )

    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            data["phone"] = "Нет номера"
            new_client_data = {
                "username": data["username"],
                "telegram": data["telegram"],
                "phone": data["phone"],
            }
            await fill_client_table(new_client_data, message)

    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_sketch_price(message: types.Message, state: FSMContext):
    if message.text in kb_admin.price_lst + kb_admin.another_price_full_lst:
        async with state.proxy() as data:
            data["price"] = message.text
        await bot.send_message(
            message.from_id, "Данный заказ оплачен?", reply_markup=kb_client.kb_yes_no
        )
        await FSM_Admin_command_create_new_sketch_order.next()  # -> get_sketch_state

    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_sketch_commands
        )

    elif message.text == "Другая цена":
        await bot.send_message(
            message.from_id,
            MSG_ADMIN_SET_ANOTHER_PRICE,
            reply_markup=kb_admin.kb_another_price_full,
        )

    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Admin_command_create_new_sketch_order.previous()  # -> get_username_telegram
        await bot.send_message(
            message.from_id,
            "Для какого пользователя заказ?\n"
            'Введи его имя или телеграм (с символом "@") или ссылку с "https://t.me/".\n\n',
            #'P.s. Нажимая на пользователя в ТГ сверху будет его имя. '\
            #'А имя с символом \"@\" - ссылка на телеграм',
            reply_markup=kb_client.kb_cancel,
        )

    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_sketch_state(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            data["state"] = STATES["paid"]

        await bot.send_message(
            message.from_id,
            "Хочешь добавить чек заказа?",
            reply_markup=kb_client.kb_yes_no,
        )
        await FSM_Admin_command_create_new_sketch_order.next()  # -> get_sketch_check

    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            new_sketch_order = {
                "order_id": data["tattoo_sketch_order"],
                "sketch_description": data["sketch_description"],
                "photo_lst": data["sketch_photo_lst"],
                "telegram": data["telegram"],
                "creation_time": datetime.now(),
                "state": data["state"],
                "check_document": data["check_document"],
                "price": data["price"],
            }
        await fill_sketch_order_table(new_sketch_order, message)
        await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_sketch_commands
        )

    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Admin_command_create_new_sketch_order.previous()  # -> get_sketch_price
        await bot.send_message(
            message.from_id,
            "Добавь цену эскиза переводного тату",
            reply_markup=kb_admin.kb_price,
        )

    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_sketch_check(message: types.Message, state: FSMContext):
    if message.content_type == "text":
        if message.text == kb_client.yes_str:
            await bot.send_message(
                message.from_id,
                "Хорошо, добавь фотографию или документ чека",
                reply_markup=kb_client.kb_cancel,
            )

        elif message.text == kb_client.no_str:
            async with state.proxy() as data:
                new_sketch_order = {
                    "order_id": data["tattoo_sketch_order"],
                    "sketch_description": data["sketch_description"],
                    "photo_lst": data["sketch_photo_lst"],
                    "telegram": data["telegram"],
                    "creation_time": datetime.now(),
                    "state": data["state"],
                    "check_document": data["check_document"],
                    "price": data["price"],
                }
            await fill_sketch_order_table(new_sketch_order, message)
            await state.finish()

        elif message.text in LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(
                MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_sketch_commands
            )

        elif message.text in LIST_BACK_COMMANDS:
            await FSM_Admin_command_create_new_sketch_order.previous()  # -> get_sketch_state
            await bot.send_message(
                message.from_id,
                f"{MSG_CLIENT_GO_BACK} Заказ оплачен?",
                reply_markup=kb_client.kb_yes_no,
            )

        else:
            await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)

    elif message.content_type == "document":
        async with state.proxy() as data:
            check_doc_pdf = await check_pdf_document_payment(
                user_id=message.from_id,
                price=str(data["price"]),
                file_name=data["tattoo_sketch_order"] + ".pdf",
                file_id=message.document.file_id,
            )

            if check_doc_pdf["result"]:
                data["check_document"] = CheckDocument(
                    order_number=data["tattoo_sketch_order"],
                    telegram_user_id=None,
                    doc=message.document.file_id,
                )
                new_sketch_order = {
                    "order_id": data["tattoo_sketch_order"],
                    "sketch_description": data["sketch_description"],
                    "photo_lst": data["sketch_photo_lst"],
                    "telegram": data["telegram"],
                    "creation_time": datetime.now(),
                    "state": data["state"],
                    "check_document": data["check_document"],
                    "price": data["price"],
                }
                await fill_sketch_order_table(new_sketch_order, message)
                await state.finish()
            else:
                await message.reply(
                    f"Чек не подошел! Попробуй другой документ или изображение."
                )

    elif message.content_type == "photo":
        async with state.proxy() as data:
            check_doc_photo = await check_photo_payment(
                message,
                message.from_id,
                str(data["price"]),
                data["tattoo_sketch_order"],
                message.photo[0].file_id,
            )

            if check_doc_photo["result"]:
                data["check_document"] = CheckDocument(
                    order_number=data["tattoo_sketch_order"],
                    telegram_user_id=None,
                    doc=message.photo[0].file_id,
                )
                new_sketch_order = {
                    "order_id": data["tattoo_sketch_order"],
                    "sketch_description": data["sketch_description"],
                    "photo_lst": data["sketch_photo_lst"],
                    "telegram": data["telegram"],
                    "creation_time": datetime.now(),
                    "state": data["state"],
                    "check_document": data["check_document"],
                    "price": data["price"],
                }
                await fill_sketch_order_table(new_sketch_order, message)
                await state.finish()
            else:
                await message.reply(
                    f"Чек не подошел! Попробуй другой документ или изображение."
                )


# ------------------------------------SKETCH ORDER-------------------------------------------
def register_handlers_admin_sketch(dp: Dispatcher):
    dp.register_message_handler(
        get_tattoo_sketch_order_and_item_command_list, commands=["эскиз_заказы"]
    )
    dp.register_message_handler(
        get_tattoo_sketch_order_and_item_command_list,
        Text(equals="Эскиз заказы", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_sketch_orders, commands=["посмотреть_эскиз_заказы"]
    )
    dp.register_message_handler(
        command_get_info_sketch_orders,
        Text(equals="посмотреть эскиз заказы", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_sketch_order_state,
        state= FSM_Admin_get_info_sketch_orders.order_state
    )

    dp.register_message_handler(
        command_get_info_sketch_order, commands=["посмотреть_эскиз_заказ"]
    )
    dp.register_message_handler(
        command_get_info_sketch_order,
        Text(equals="посмотреть эскиз заказ", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_name_for_view_sketch_order,
        state=FSM_Admin_command_get_info_sketch_order.order_name,
    )

    dp.register_message_handler(
        command_delete_info_sketch_order, commands=["удалить_эскиз_заказ"]
    )
    dp.register_message_handler(
        command_delete_info_sketch_order,
        Text(equals="удалить эскиз заказ", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        delete_info_sketch_orders, state=FSM_Admin_delete_sketch_order.order_number
    )

    dp.register_message_handler(
        command_get_info_opened_sketch_orders,
        Text(equals="посмотреть активные эскиз заказы", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_closed_sketch_orders,
        Text(equals="посмотреть закрытые эскиз заказы", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_create_new_sketch_order, commands=["добавить_эскиз_заказ"]
    )
    dp.register_message_handler(
        command_create_new_sketch_order,
        Text(equals="добавить эскиз заказ", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        get_new_sketch_description,
        state=FSM_Admin_command_create_new_sketch_order.get_description,
    )
    dp.register_message_handler(
        get_photo_sketch,
        content_types=["photo", "text"],
        state=FSM_Admin_command_create_new_sketch_order.get_photo_sketch,
    )
    dp.register_message_handler(
        get_username_telegram,
        state=FSM_Admin_command_create_new_sketch_order.get_username_telegram,
    )
    dp.register_message_handler(
        get_sketch_price, state=FSM_Admin_command_create_new_sketch_order.get_price
    )
    dp.register_message_handler(
        get_sketch_state, state=FSM_Admin_command_create_new_sketch_order.get_state
    )
    dp.register_message_handler(
        get_sketch_check,
        content_types=["photo", "document", "text"],
        state=FSM_Admin_command_create_new_sketch_order.get_check,
    )
