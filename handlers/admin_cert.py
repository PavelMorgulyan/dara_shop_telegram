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
from handlers.other import STATES, status_distribution, clients_status

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
            "❔ Какую команду по сертификатам выполнить?",
            reply_markup=kb_admin.kb_cert_item_commands,
        )


# ----------------------------------------CREATE CERT ORDER--------------------------------------
async def create_cert_order(data: dict, message: types.Message):
    with Session(engine) as session:
        new_cert_order = Orders(
            order_type="сертификат",
            user_id=message.from_id,
            order_state=data['state'],
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
            "❔ На какую цену сертификат? Выбери цену из списка", reply_markup=kb_admin.kb_price
        )
        await bot.send_message(
            message.from_id, 
            MSG_ADMIN_CAN_SET_ANOTHER_PRICE,
            reply_markup= kb_admin.kb_set_another_price_from_line
        )


# Возможность добавления цены через ввод, а не кб
async def process_callback_set_price_from_line(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 
        MSG_ADMIN_SET_ANOTHER_PRICE_FROM_LINE, reply_markup= kb_client.kb_cancel
    )


async def load_сert_price(message: types.Message, state: FSMContext):
    if message.text in kb_admin.price_lst or message.text.isdigit():
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
                f"❔ Пользователь оплатил сертфикат?", reply_markup=kb_client.kb_yes_no
            )
        else:
            await FSM_Admin_сert_item.next()
            await message.reply(
                f"❔ На какую сумму пользователь хочет сертификат? Введи сумму",
                reply_markup=kb_admin.kb_price,
            )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def load_сert_other_price(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        async with state.proxy() as data:
            data["price"] = int(message.text)
        await FSM_Admin_сert_item.next() #->admin_process_successful_cert_payment
        await message.reply(
            f"❔ Пользователь оплатил сертфикат?", reply_markup=kb_client.kb_yes_no
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def admin_process_successful_cert_payment(
    message: types.Message, state=FSMContext
):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:  # type: ignore
            code = data["code"]
            data["state"] = STATES["paid"]

            await bot.send_message(message.chat.id, f"Код на сертификат: {code}.")
            await FSM_Admin_сert_item.next()
            await message.reply(
                f"❔ Хочешь приложить чек перевода?", reply_markup=kb_client.kb_yes_no
            )

    elif (
        message.text == kb_client.no_str
    ):  # В таблице код уже будет, но выдадим мы его только после оплаты
        async with state.proxy() as data:  # type: ignore
            data["state"] = STATES["open"]
            data["check_document"] = []

            new_cert_order = {
                "price": data["price"],
                "state": data["state"],
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
            new_check = [
            CheckDocument(
                order_number= order_number,
                doc= check_document
                )
            ]       
            new_cert_order = {
                "price": data["price"],
                "state": STATES['paid'],
                "code": data["code"],
                "cert_order_number": data["cert_order_number"],
                "check_document": new_check,
            }
            await create_cert_order(new_cert_order, message)

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
        await message.reply(f"❌ Чек не подошел! {check_doc_result['report_msg']}")
        


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
        await message.reply(
            "Ответ принят, это другой пользователь. Введи его телеграм", reply_markup= kb_client.kb_cancel
        )

    else:
        await message.reply('Ответь на вопрос "Да" или "Нет"')


async def cert_load_telegram(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["telegram"] = message.from_user.id
    await FSM_Admin_cert_username_info.next()
    await bot.send_message(
        message.from_id, "❔ Добавить телефон клиента?", reply_markup= kb_client.kb_yes_no
    )


async def cert_load_phone(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        await message.reply("Введи его телефон")
        
    elif message.text == kb_client.no_str:
        await message.reply("Пользователь будет без телефона")
        
    else:
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
                    phone= message.text,
                    status = clients_status['active']
                )
                with Session(engine) as session:
                    session.add(new_client_info)
                    session.commit()
                username, telegram, phone = data["username"], data["telegram"], message.text
                order_number = data["cert_order_number"]

            await bot.send_message(
                message.from_user.id,
                f"Заказ под номером {order_number}"
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
            await bot.send_message(
                message.from_id, f"<pre>{table}</pre>", parse_mode=types.ParseMode.HTML
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


# TODO изменить статус сертификата, удалить сертификат
# --------------------------------CHANGE STATE CERT COMMANDS----------------------------------
class FSM_Admin_set_new_state_cert_order(StatesGroup):
    get_order_number = State()
    set_new_order_state = State()
    get_answer_check_document = State()
    get_price_for_check_document = State()
    get_check_document = State()


# изменить сертификат
async def command_set_new_cert_order_state(message: types.Message):
    if (
        message.text.lower() in ["изменить статус сертификата", "/изменить_статус_сертификата"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders).where(Orders.order_type == "сертификат")
            ).all()
            
        if orders == []:
            await bot.send_message(
                message.from_id,
                MSG_NO_ORDER_IN_TABLE,
                reply_markup=kb_admin.kb_cert_item_commands,
            )
        else:
            kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
            await FSM_Admin_set_new_state_cert_order.get_order_number.set() #-> get_cert_order_number

            for order in orders:
                kb_orders.add(
                    KeyboardButton(
                        f'{order.order_number} статус: {order.order_state}'
                    )
                )
            kb_orders.add(kb_client.back_btn)
            await bot.send_message(
                message.from_user.id,
                MSG_WHICH_ADMIN_ORDER_WANT_TO_CHANGE,
                reply_markup=kb_orders,
            )


async def get_cert_order_number(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders).where(Orders.order_type == "сертификат")
        ).all()
    kb_orders = []
    for order in orders:
        kb_orders.append(f'{order.order_number} статус: {order.order_state}')
    
    if message.text in kb_orders:
        await FSM_Admin_set_new_state_cert_order.next() # -> get_new_status_to_cert_order
        
        async with state.proxy() as data:
            data['order_number'] = int(message.text.split()[0])
            data['current_order_status'] = message.text.split()[2]
        
        kb_new_status = ReplyKeyboardMarkup(resize_keyboard=True)
        if message.text.split()[2] in list(STATES['closed'].values()):
            kb_new_status = kb_admin.kb_order_statuses
        else:
            for status in status_distribution["сертификат"][message.text.split()[2]] \
                + list(STATES['closed'].values()):
                kb_new_status.add(KeyboardButton(status))
        
        await bot.send_message(
            message.from_id, f"Какой статус выставляем?", reply_markup= kb_new_status,
        )


async def get_new_status_to_cert_order(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        order_number = data['order_number']
        current_order_status = data['current_order_status'] 
        
    if message.text in list(STATES.values()) + list(STATES['closed'].values()):
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == order_number)
            ).one()
            order.order_state = message.text
            async with state.proxy() as data:
                data['new_state'] = message.text
                data['user_id'] = order.user_id
                data['username'] = order.username
            new_state = message.text
            user_id = order.user_id
            username = order.username
            session.commit()
            
        if message.text not in [STATES["paid"]]:
            await message.reply(MSG_DO_CLIENT_WILL_GET_MSG_ABOUT_CHANGING_STATUS, 
                reply_markup=kb_client.kb_yes_no)
                
        elif message.text in [STATES["paid"]]:  # оплачен
            await FSM_Admin_set_new_state_cert_order.next() #-> get_answer_for_getting_check_document
            await message.reply(
                f"Хочешь добавить чек к сертификату?", reply_markup=kb_client.kb_yes_no
            )
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            new_state = data['new_state']
            user_id = data['user_id']
            username = data['username']
            
        await bot.send_message(user_id, 
            (
                f"❕ Уважаемый {username}!\n"
                f"❕ Статус сертификата {order_number} изменился с '{current_order_status}' на '{new_state}'.\n"
                f"За подробностями об изменении статуса заказа обращайтесь к "
                "@dara_redwan (https://t.me/dara_redwan)"
            )
        )
        await message.reply(
            f'❕ Готово! Обновлен статус сертификата {order_number} на "{new_state}"',
            reply_markup=kb_admin.kb_cert_item_commands,
        )
        await state.finish() 
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            new_state = data['new_state']
        await message.reply(
            f'❕ Готово! Обновлен статус сертификата {order_number} на "{new_state}"',
            reply_markup=kb_admin.kb_cert_item_commands,
        )
        await state.finish()  #  полностью очищает данные


async def get_answer_for_getting_check_document(
    message: types.Message, state: FSMContext
):
    if message.text == kb_client.yes_str:
        await FSM_Admin_set_new_state_cert_order.next()
        await message.reply(
            f"На какую сумму чек?", reply_markup=kb_admin.kb_price
        )

    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            order_number = data["order_number"]
            new_state = data["new_state"]

        await message.reply(
            f"Готово! Обновлен статусзаказа {order_number} на '{new_state}'",
            reply_markup=kb_admin.kb_cert_item_commands,
        )
        await state.finish()
    else:
        await message.reply(
            f"На этот вопрос можно ответит только 'Да' или 'Нет'. Выбери правильный ответ",
            reply_markup=kb_client.kb_yes_no,
        )


async def get_price_for_check_document(message: types.Message, state: FSMContext):
    if message.text in kb_admin.another_price_lst:
        await bot.send_message(
            message.from_id,
            MSG_ADMIN_SET_ANOTHER_PRICE,
            reply_markup=kb_admin.kb_another_price_full,
        )

    elif message.text.isdigit():
        async with state.proxy() as data:
            data["cert_price"] = message.text
        await FSM_Admin_set_new_state_cert_order.next() # -> get_check_document
        await message.reply(
            MSG_ADMIN_GET_CHECK_TO_ORDER,
            reply_markup=kb_client.kb_back_cancel,
        )

    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_cert_item_commands
        )

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_check_document(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        order_number = data["order_number"]
        price = data["cert_price"]

    if message.content_type == "document":
        check_doc_pdf = await check_pdf_document_payment(
            user_id=message.from_id,
            price=price,
            file_name=message.document.file_name,
            file_id=message.document.file_id,
        )

        if check_doc_pdf["result"]:
            with Session(engine) as session:
                order = session.scalars(select(Orders)
                    .where(Orders.order_number == order_number)).one()
                
                new_check_item = CheckDocument(
                    order_number=order_number, 
                    doc= message.document.file_id
                )
                if order.check_document in [[], None]:
                    order.check_document = [new_check_item]
                else:
                    order.check_document.append(new_check_item)
                session.commit()

            await bot.send_message(
                message.from_id,
                f"🌿 Чек подошел! Заказ № {order_number} обрел свой чек! "
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_cert_item_commands,
            )
            
            await message.reply(MSG_DO_CLIENT_WILL_GET_MSG_ABOUT_CHANGING_STATUS, 
                reply_markup=kb_client.kb_yes_no)
        else:
            await message.reply(f"❌ Чек не подошел! {check_doc_pdf['report_msg']}")

    if message.content_type == "text":
        if message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(
                MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_cert_item_commands
            )

        elif message.text in LIST_BACK_COMMANDS:
            await FSM_Admin_set_new_state_cert_order.previous()
            await message.reply(
                f"{MSG_CLIENT_GO_BACK}❔ На какую сумму чек?",
                reply_markup=kb_admin.kb_price,
            )
        if message.text == kb_client.yes_str:
            async with state.proxy() as data:
                new_state = data['new_state']
                user_id = data['user_id']
                username = data['username']
                
            await bot.send_message(user_id, 
                (
                    f"❕ Уважаемый {username}!\n"
                    f"❕ Статус сертификата {order_number} изменился на '{new_state}'.\n"
                    f"За подробностями об изменении статуса заказа обращайтесь к "
                    "@dara_redwan (https://t.me/dara_redwan)"
                )
            )
            await message.reply(
                f'❕ Готово! Обновлен статус сертификата {order_number} на "{new_state}"',
                reply_markup=kb_admin.kb_cert_item_commands,
            )
            await state.finish() 
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            new_state = data['new_state']
        await message.reply(
            f'❕ Готово! Обновлен статус сертификата {order_number} на "{new_state}"',
            reply_markup=kb_admin.kb_cert_item_commands,
        )
        await state.finish()  #  полностью очищает данные

    if message.content_type == "photo":
        message.photo[0].file_id
        check_photo = await check_photo_payment(
            message=message,
            user_id=message.from_id,
            price=price,
            file_name=message.document.file_name,
            file_id=message.photo[0].file_id,
        )

        if check_photo["result"]:
            with Session(engine) as session:
                order = session.scalars(select(Orders)
                    .where(Orders.order_number == order_number)).one()
                
                if order.check_document in [None, []]:
                    new_check_item = CheckDocument(
                        order_number=order_number, 
                        doc= message.photo[0].file_id
                    )
                    order.check_document = [new_check_item]
                else:
                    order.check_document.append(new_check_item)
                session.commit()
            await bot.send_message(
                message.from_id,
                f"🌿 Чек подошел! Заказ № {order_number} обрел свой чек!"
            )
            await bot.send_message(
                message.from_id, 
                MSG_DO_CLIENT_WILL_GET_MSG_ABOUT_CHANGING_STATUS, 
                reply_markup=kb_client.kb_yes_no
            )
        else:
            await message.reply(f"❌ Чек не подошел! {check_doc_pdf['report_msg']}")  # type: ignore


# -------------------------------------------- удалить сертификат---------------------------------
class FSM_Admin_delete_cert_order(StatesGroup):
    order_number = State()


# /удалить сертификат - полное удаление сертификата из таблицы
async def command_delete_info_cert_order(message: types.Message):
    if (
        message.text in ["удалить сертификат", "/удалить_сертификат"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders).where(Orders.order_type == "сертификат")
            ).all()

        if orders == []:
            await message.reply(MSG_NO_ORDER_IN_TABLE)
            await bot.send_message(
                message.from_id,
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_cert_item_commands,
            )
        else:
            await bot.send_message(message.from_id, MSG_DELETE_FUNCTION_NOTE)
            kb_cert_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
            for order in orders:
                # выводим наименования тату
                kb_cert_order_numbers.add(
                    KeyboardButton(
                        f'{order.id}) №{order.order_number} {order.order_state}'
                    )
                )

            kb_cert_order_numbers.add(KeyboardButton("Назад"))
            await FSM_Admin_delete_cert_order.order_number.set()
            await message.reply(
                "Какой заказ хотите удалить?", reply_markup=kb_cert_order_numbers
            )


async def delete_info_cert_orders(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders).where(Orders.order_type == "сертификат")
        ).all()
    order_kb_lst = []
    for order in orders:
        order_kb_lst.append(
            f'{order.id}) №{order.order_number} {order.order_state}'
        )

    if message.text in order_kb_lst:
        with Session(engine) as session:
            order = session.get(Orders, message.text.split(")")[0])
            session.delete(order)
            session.commit()

        await message.reply(f"Cертификат {message.text.split()[1][1:]} удален")
        await bot.send_message(
            message.from_user.id,
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_cert_item_commands,
        )
        await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_cert_item_commands
        )
        await state.finish()
    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


def register_handlers_admin_cert(dp: Dispatcher):
    # ---------------------------CREATE CERT ORDER-----------------------------
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
    dp.register_callback_query_handler(process_callback_set_price_from_line,
        state=FSM_Admin_сert_item.сert_price)
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
        get_check_document_cert_from_admin, content_types= ['document', 'photo', 'text'],
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
        commands="посмотреть_сертификаты",
        state=None,
    )
    dp.register_message_handler(
        command_get_info_сert_orders,
        Text(equals="посмотреть сертификаты", ignore_case=True),
        state=None,
    )
    # ---------------------------------CHANGE STATUS CERT ORDER----------------------------
    dp.register_message_handler(
        command_set_new_cert_order_state, commands=["изменить_статус_сертификата"]
    )
    dp.register_message_handler(
        command_set_new_cert_order_state,
        Text(equals="изменить статус сертификата", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_cert_order_number,
        state=FSM_Admin_set_new_state_cert_order.get_order_number,
    )
    dp.register_message_handler(
        get_new_status_to_cert_order,
        state=FSM_Admin_set_new_state_cert_order.set_new_order_state,
    )

    dp.register_message_handler(
        get_answer_for_getting_check_document,
        state=FSM_Admin_set_new_state_cert_order.get_answer_check_document,
    )
    dp.register_message_handler(
        get_price_for_check_document,
        state=FSM_Admin_set_new_state_cert_order.get_price_for_check_document,
    )

    dp.register_message_handler(
        get_check_document,
        content_types=["photo", "document"],
        state=FSM_Admin_set_new_state_cert_order.get_check_document,
    )
    
    # ---------------------------------DELETE STATUS CERT ORDER----------------------------
    dp.register_message_handler(
        command_delete_info_cert_order, commands=["удалить_сертификат"]
    )
    dp.register_message_handler(
        command_delete_info_cert_order,
        Text(equals="удалить сертификат", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        delete_info_cert_orders, state=FSM_Admin_delete_cert_order.order_number
    )