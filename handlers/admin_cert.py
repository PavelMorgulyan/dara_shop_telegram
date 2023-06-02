from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from prettytable import PrettyTable
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import CODE_LENTH, ORDER_CODE_LENTH, ADMIN_NAMES, CALENDAR_ID
from handlers.other import generate_random_code, generate_random_order_number

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from validate import check_pdf_document_payment, check_photo_payment
from db.db_setter import set_to_table
from db.db_updater import update_info
from db.db_getter import get_info_many_from_table

# from diffusers import StableDiffusionPipeline
# import torch
from datetime import datetime
from handlers.calendar_client import obj
from msg.main_msg import *
from handlers.other import STATES

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *
import re

# ------------------------------------ CERT COMMAND LIST-------------------------------------------
# 'Сертификат',
async def get_cert_command_list(message: types.Message):
    if (
        message.text.lower() == "сертификат"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            "Какую команду по сертификатам хочешь выполнить?",
            reply_markup=kb_admin.kb_cert_item_commands,
        )


# ----------------------------------------CREATE CERT ORDER--------------------------------------
async def create_cert_order(data: dict, message: types.Message):
    with Session(engine) as session:
        new_cert_order = Orders(
            order_type="сертификат",
            user_id=message.from_id,
            order_state=STATES["open"],
            order_number=data["cert_order_number"],
            creation_date=datetime.now(),
            price=data["price"],
            check_document=data["check_document"],
            username=message.from_user.full_name,
            code=data["code"],
        )
        session.add(new_cert_order)
        session.commit()


class FSM_Admin_сert_item(StatesGroup):
    сert_price = State()
    сert_other_price = State()
    сert_payment_choise = State()
    cert_get_check_answer = State()
    cert_get_check_document = State()
    # cert_payment_state_second = State()


class FSM_Admin_cert_username_info(StatesGroup):
    get_user_name = State()
    user_name_answer = State()
    telegram = State()
    phone = State()


PRICE_сert_1K = types.LabeledPrice(label="Сертификат на 1000 Р.", amount=100000)
PRICE_сert_2K = types.LabeledPrice(label="Сертификат на 2000 Р.", amount=200000)
PRICE_сert_3K = types.LabeledPrice(label="Сертификат на 3000 Р.", amount=300000)
PRICE_сert_4K = types.LabeledPrice(label="Сертификат на 4000 Р.", amount=400000)
PRICE_сert_5K = types.LabeledPrice(label="Сертификат на 5000 Р.", amount=500000)


# добавить заказ на сертификат, Отправляем цену сертификата
async def command_load_сert_item(message: types.Message):
    if (
        message.text.lower() == "добавить заказ на сертификат"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_сert_item.сert_price.set()
        await message.reply(
            "На какую цену хотите сертификат?", reply_markup=kb_admin.kb_price
        )


async def load_сert_price(message: types.Message, state: FSMContext):
    if message.text in kb_admin.price_lst:
        async with state.proxy() as data:
            data["username"] = message.from_user.username
            data["creation_date"] = datetime.now()
            data["code"] = await generate_random_code(CODE_LENTH)
            data["cert_order_number"] = await generate_random_order_number(
                ORDER_CODE_LENTH
            )

        if message.text != "Другая":
            async with state.proxy() as data:
                data["price"] = message.text.split()[0]

            for i in range(2):
                await FSM_Admin_сert_item.next()  # -> admin_process_successful_cert_payment
            await message.reply(
                f"Пользователь оплатил сертфикат?", reply_markup=kb_client.kb_yes_no
            )
        else:
            await FSM_Admin_сert_item.next()
            await message.reply(
                f"На какую сумму пользователь хочет сертификат? Введи сумму",
                reply_markup=kb_admin.kb_price,
            )
    else:
        await message.reply("Ответь на вопрос ответом из списка, пожалуйста")


async def load_сert_other_price(message: types.Message, state: FSMContext):
    if message.text in kb_admin.price_lst:
        async with state.proxy() as data:
            data["price"] = int(message.text)
        await FSM_Admin_сert_item.next() #->admin_process_successful_cert_payment
        await message.reply(
            f"Пользователь оплатил сертфикат?", reply_markup=kb_client.kb_yes_no
        )


async def admin_process_successful_cert_payment(
    message: types.Message, state=FSMContext
):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:  # type: ignore
            code = data["code"]
            data["state"] = STATES["paid"]

            await bot.send_message(message.chat.id, f"Вот код на сертификат: {code}.")
            await FSM_Admin_сert_item.next()
            await message.reply(
                f"Хочешь приложить чек перевода?", reply_markup=kb_client.kb_yes_no
            )

    elif (
        message.text == kb_client.no_str
    ):  # В таблице код уже будет, но выдадим мы его только после оплаты
        async with state.proxy() as data:  # type: ignore
            data["state"] = STATES["open"]
            data["check_document"] = []

            new_cert_order = {
                "price": data["price"],
                "status": data["state"],
                "code": data["code"],
                "cert_order_number": data["cert_order_number"],
                "check_document": data["check_document"],
            }
            await create_cert_order(new_cert_order, message)
        await state.finish()  # type: ignore

        await FSM_Admin_cert_username_info.get_user_name.set()
        async with state.proxy() as data:  # type: ignore
            cert_order_number = data["order_number"]

        await bot.send_message(
            message.chat.id,
            f"Админ, заказ под номером {cert_order_number} почти оформлен! "
            "Осталось только добавить имя, телеграм и телефон пользователя заказа. "
            "Напиши имя пользователя, пожалуйста.",
        )
    else:
        await message.reply('Ответь на вопрос "Да" или "Нет"')


async def get_check_answer_cert_from_admin(message: types.Message, state=FSMContext):
    if message.text == kb_client.yes_str:
        await FSM_Admin_сert_item.next()
        await message.reply(MSG_ADMIN_GET_CHECK_TO_ORDER, reply_markup= kb_client.kb_cancel)
        
    elif message.text == kb_client.no_str:
        cert_order_number = 0
        async with state.proxy() as data:  # type: ignore
            cert_order_number = data["cert_order_number"]
            data["check_document"] = None

            new_cert_order = {
                "username": data["username"],
                "price": data["price"],
                "state": data["state"],
                "code": data["code"],
                "creation_date": data["creation_date"],
                "cert_order_number": data["cert_order_number"],
                "check_document": data["check_document"],
            }

            await set_to_table(tuple(new_cert_order.values()), "сert_orders")

        await state.finish()  # type: ignore
        await FSM_Admin_cert_username_info.get_user_name.set()
        async with state.proxy() as data:  # type: ignore
            data["order_number"] = cert_order_number

        await bot.send_message(
            message.chat.id,
            f"Админ, заказ под номером {cert_order_number} почти оформлен! "
            "Осталось только добавить имя, телеграм и телефон пользователя заказа. "
            "Напиши имя пользователя.",
        )
    else:
        await message.reply('Ответь на вопрос "Да" или "Нет"')


# Получаем фотографию или документ чека
async def get_check_document_cert_from_admin(message: types.Message, state=FSMContext):
    async with state.proxy() as data:  # type: ignore
        price = str(data["price"])

    check_document = ""
    if message.content_type == "document":
        check_document = message.document.file_id  # .photo[0].file_id
        # Проверяем чек на корректность
        check_doc_result = await check_pdf_document_payment(
            message.from_id, price, message.document.file_name, check_document
        )

    elif message.content_type == "photo":
        check_document = message.photo[0].file_id
        # Проверяем чек на корректность
        check_doc_result = await check_photo_payment(
            message, message.from_id, price, data["cert_order_number"], check_document
        )

    if check_doc_result["result"]:
        async with state.proxy() as data:  # type: ignore
            order_number = data["cert_order_number"]

            new_cert_order = Orders(
                username=data["username"],
                price= data["price"],
                state= data["state"],
                code= data["code"],
                creation_date= data["creation_date"],
                order_number= data["cert_order_number"],
                check_document= check_document,
            )
            with Session(engine) as session:
                session.add(new_cert_order)
                session.commit()

            # await set_to_table(tuple(new_cert_order.values()), 'сert_orders')
        await bot.send_message(
            message.chat.id,
            f"Админ, заказ под номером {order_number} почти оформлен!"
            " Осталось только добавить имя, телеграм и телефон пользователя заказа."
            " Напиши имя пользователя.",
        )
        await state.finish()  # type: ignore
        await FSM_Admin_cert_username_info.get_user_name.set()
    else:
        await message.reply(
            await message.reply(f"❌ Чек не подошел! {check_doc_result['report_msg']}")
        )


async def cert_load_user_name(message: types.Message, state: FSMContext):
    
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.name == message.text)).all()
    
    user_telegram_name = "Без телеграма" if user == [] or user[0].telegram_name is None \
        else user[0].telegram_name
        
    phone = "Без телефона" if user == [] or user[0].phone is None else user[0].phone
    async with state.proxy() as data:
        data["username"] = message.text
        data["telegram"] = user_telegram_name
        data["phone"] = phone

    if user == []:
        for i in range(2): #-> cert_load_telegram
            await FSM_Admin_cert_username_info.next()

        await message.reply("Введи его телеграм")
    else:
        await FSM_Admin_cert_username_info.next()
        await message.reply(
            f"Это пользователь под ником {user_telegram_name}?",
            reply_markup=kb_client.kb_yes_no,
        )


async def cert_answer_user_name(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            username, telegram, phone = (
                data["username"],
                data["telegram"],
                data["phone"],
            )
            order_number = data["order_number"]
            await update_info(
                "cert_orders", "order_number", order_number, "username", username
            )

            await bot.send_message(
                message.from_user.id,
                f"Хорошо, твой заказ под номером {order_number} "
                f"оформлен на пользователя {username} c телеграмом {telegram}, телефон {phone}",
                reply_markup=kb_admin.kb_main,
            )
        await state.finish()
    elif message.text == kb_client.no_str:
        await FSM_Admin_cert_username_info.next()
        await message.reply("Хорошо, это другой пользователь, введи его телеграм")

    else:
        await message.reply('Ответь на вопрос "Да" или "Нет"')


async def cert_load_telegram(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["telegram"] = message.from_user.id
    await FSM_Admin_cert_username_info.next()
    await message.reply("Введи его телефон")


async def cert_load_phone(message: types.Message, state: FSMContext):
    number = message.text
    result = re.match(
        r"^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?"
        r"[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$",
        number,
    )

    if not result:
        await message.reply("Номер не корректен, пожалуйста, введи номер заново")
    else:
        async with state.proxy() as data:
            new_client_info = User(
                name=data["username"],
                telegram_name=data["telegram"],
                phone= message.text
            )
            with Session(engine) as session:
                session.add(new_client_info)
                session.commit()
            username, telegram, phone = data["username"], data["telegram"], message.text
            tattoo_order_number = data["tattoo_order_number"]

        await bot.send_message(
            message.from_user.id,
            f"Заказ под номером {tattoo_order_number}"
            f" оформлен на пользователя {username} под ником @{telegram}, телефон {phone}!",
            reply_markup=kb_admin.kb_main,
        )

        await state.finish()


async def view_cert_order(orders: ScalarResult["Orders"], message: types.Message):
    if orders == []:
            await message.reply("⭕️ Пока у вас нет заказов на сертификатов в таблице")
    else:
        headers = [
            "№",
            "Тип заказа",
            "Пользователь",
            "Номер заказа",
            "Статус",
            "Цена",
            "Код",
            "Дата открытия"
        ]
        for order in orders:
            table = PrettyTable(
                headers, left_padding_width=1, right_padding_width=1
            )  # Определяем таблицу
            table.add_row(
                [
                    order.id,
                    order.order_type,
                    order.username,
                    order.order_number,
                    order.order_state,
                    order.price,
                    order.code,
                    order.creation_date
                ]
            )
            
            # f" Чек на оплату: {}\n",
            with Session(engine) as session:
                checks = session.scalars(select(CheckDocument)
                    .where(CheckDocument.order_number == order.order_number)).all()
            
            for check in checks:
                try:
                    await bot.send_document(message.from_id, check.doc)
                except:
                    await bot.send_photo(message.from_id, check.doc)
                    
            
        await bot.send_message(
            message.from_user.id, f"Всего заказов: {len(orders)}"
        )

# --------------------------------GET TO VIEW CERT COMMANDS-------------------------------------
# /посмотреть_сертификаты
async def command_get_info_сert_orders(message: types.Message):
    if (
        message.text.lower()
        in ["посмотреть сертификаты", "/посмотреть_сертификаты"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(select(Orders)
                .where(Orders.order_type == "сертификат")).all()
            
        await view_cert_order(orders, message)
        
        await bot.send_message(message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_cert_item_commands,
        )


# TODO изменить сертификат, удалить сертификат
# --------------------------------CHANGE CERT COMMANDS-------------------------------------

# изменить сертификат
async def command_change_cert_order(message: types.Message):
    if (
        message.text.lower()
        in ["изменить сертификат", "/изменить_сертификат"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(select(Orders)
                .where(Orders.order_type == "сертификат")).all()
            
        await view_cert_order(orders, message)
        if orders != []:
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            for order in orders:
                kb.add(order.order_number)
            await bot.send_message(message.from_id,
                MSG_WHICH_ADMIN_ORDER_WANT_TO_CHANGE,
                reply_markup=kb
            )

def register_handlers_admin_cert(dp: Dispatcher):
    # -------------------------------------CREATE CERT ORDER-------------------------------------
    dp.register_message_handler(
        get_cert_command_list, commands="сертификат", state=None
    )
    dp.register_message_handler(
        get_cert_command_list, Text(equals="сертификат", ignore_case=True), state=None
    )

    dp.register_message_handler(
        command_load_сert_item, commands="добавить_заказ_на_сертификат", state=None
    )
    dp.register_message_handler(
        command_load_сert_item,
        Text(equals="добавить заказ на сертификат", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(load_сert_price, state=FSM_Admin_сert_item.сert_price)
    dp.register_message_handler(
        load_сert_other_price, state=FSM_Admin_сert_item.сert_other_price
    )

    dp.register_message_handler(
        admin_process_successful_cert_payment,
        state=FSM_Admin_сert_item.сert_payment_choise,
    )  # Пользователь оплатил сертфикат? Да / нет
    dp.register_message_handler(
        get_check_answer_cert_from_admin,
        state=FSM_Admin_сert_item.cert_get_check_answer,
    )  # Хочешь приложить чек перевода?  Да / нет
    dp.register_message_handler(
        get_check_document_cert_from_admin,
        state=FSM_Admin_сert_item.cert_get_check_document,
    )

    dp.register_message_handler(
        cert_load_user_name, state=FSM_Admin_cert_username_info.get_user_name
    )  # Приложи документ или фотографию чека
    dp.register_message_handler(
        cert_answer_user_name, state=FSM_Admin_cert_username_info.user_name_answer
    )
    dp.register_message_handler(
        cert_load_telegram, state=FSM_Admin_cert_username_info.telegram
    )  # добавляет всю инфу про пользователя
    dp.register_message_handler(
        cert_load_phone, state=FSM_Admin_cert_username_info.phone
    )  # добавляет всю инфу про пользователя

    # -----------------------COMMANDS CERT ORDER----------------------------------

    dp.register_message_handler(
        command_get_info_сert_orders,
        commands="посмотреть_заказанные_сертификаты",
        state=None,
    )
    dp.register_message_handler(
        command_get_info_сert_orders,
        Text(equals="посмотреть заказанные сертификаты", ignore_case=True),
        state=None,
    )
