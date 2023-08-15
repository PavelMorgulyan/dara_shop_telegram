from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from msg.main_msg import *
from msg.msg_client_payload import *
from keyboards import kb_client, kb_admin
from handlers.other import *

from validate import check_pdf_document_payment, check_photo_payment
from handlers.calendar_client import obj

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *
from datetime import datetime
from handlers.client import DARA_ID

# 📷 ⏱ 🛠 ⚙️ 📎 ❤️ ☎️ 🗓 💬 🕒 🔴 🟢 🟡 ⁉️‼️ ❓❕❌
# ⭕️ 🛑 ⛔️ 🌿 ☘️ 🍀 🌴 🍃 🕸 💳 🎉 🎁 📃 🎫 📏 📜 🏷


# -------------------------------------Pay order----------------------------------------
class FSM_Client_paid_order(StatesGroup):
    order_type = State()
    order_name = State()
    order_check_document = State()


async def command_get_payment_order_choice(message: types.Message):
    if message.text.lower() in ["оплатить заказ 💳", "/pay_for_the_order"]:
        await FSM_Client_paid_order.order_type.set() # -> command_send_to_view_orders_to_payloading
        await bot.send_message(
            message.from_id,
            MSG_WHICH_ORDER_CLIENT_WANT_TO_PAY,
            reply_markup=kb_client.kb_choice_order_type_to_payloading,
        )
        # await FSM_Client_paid_order.order_name.set()


async def send_to_view_orders(orders: ScalarResult["Orders"]) -> tuple:
    unpaid_order_lst = []
    kb_unpaid_orders = ReplyKeyboardMarkup(resize_keyboard=True)
    msg, orders_str = ("", "")
    
    for order in orders:
        creation_date = order.creation_date.strftime("%H:%M %d/%m/%Y")
        
        if order.order_type in kb_client.choice_order_type_to_payloading["Тату заказы 🕸"]:
            orders_str += (
                f"🕸 Тату заказ № {order.order_number} от {creation_date}\n"
                f"🕒 Дата и время встречи:\n"
            )
            
            # Если заказ на постоянное тату, то добавляем список встреч
            if order.order_type == kb_admin.price_lst_types['constant_tattoo']:
                with Session(engine) as session:
                    schedule_order_items = session.scalars(
                        select(ScheduleCalendarItems)
                            .where(ScheduleCalendarItems.order_number == order.order_number)
                        ).all()
                
                if schedule_order_items == []:
                    orders_str += ("⭕️ Без даты встречи\n")
                else:
                    for number, event in enumerate(schedule_order_items):
                        with Session(engine) as session:
                            schedule_event = session.scalars(
                                select(ScheduleCalendar).where(
                                    ScheduleCalendar.id == event.schedule_id
                                )
                            ).one()
                        
                        start_time = schedule_event.start_datetime.strftime("%d/%m/%Y c %H:%M")
                        end_time = schedule_event.end_datetime.strftime("%H:%M")
                        orders_str += f"    {number+1}) {start_time} по {end_time}\n"
                    
            orders_str += (
                f"📜 Наименования тату: {order.order_name}\n"
                f"📏 Размер: {order.tattoo_size}\n"
                f"🍃 Описание тату: {order.tattoo_note}\n"
                f"💬 Описание заказа: {order.order_note}\n"
                f"📃 Состояние заказа: {order.order_state}\n"
            )
            
            msg = (
                f"Тату заказ № {order.order_number} от {creation_date} 🕸"
            )

        elif order.order_type in kb_client.choice_order_type_to_payloading["Гифтбоксы 🎁"]:
            orders_str += (
                f"🎁 Гифтбокс заказ № {order.order_number}\n"
                f"💬 Описание заказа: {order.order_note}\n"
                f"🕒 Дата открытия заказа: {creation_date}\n"
                f"📃 Состояние заказа: {order.order_state}\n\n"
            )
            msg = f"Гифтбокс заказ № {order.order_number} от {creation_date} 🎁"

        elif (
            order.order_type in kb_client.choice_order_type_to_payloading["Заказы эскизов 🎨"]
        ):
            orders_str += (
                f"🕸 Эскиз заказ № {order.order_number} от {creation_date}\n"
                f"📜 Описание эскиза тату: {order.order_note}\n"
                f"🕒 Дата открытия заказа: {creation_date}\n"
                f"📃 Состояние заказа: {order.order_state}\n"
            )
            msg = f"Эскиз заказ № {order.order_number} от {creation_date} 🎨"

        elif order.order_type in kb_client.choice_order_type_to_payloading["Сертификаты 🎫"]:
            orders_str += (
                f"🎫 Заказ сертификата № {order.order_number}\n"
                f"💰 Цена сертификата: {order.price}\n"
            )

            msg = f"Сертификат {order.order_number} по цене {order.price} 🎫"
        unpaid_order_lst.append(msg)
        kb_unpaid_orders.add(KeyboardButton(msg))

    kb_unpaid_orders.add(KeyboardButton(kb_client.back_lst[0]))
    return kb_unpaid_orders, orders_str, unpaid_order_lst


async def command_send_to_view_orders_to_payloading(
    message: types.Message, state=FSMContext
):
    if message.text in list(kb_client.choice_order_type_to_payloading.keys()):
        async with state.proxy() as data:
            data["order_type"] = kb_client.choice_order_type_to_payloading[message.text]
        
        with Session(engine) as session:
            unpaid_orders = session.scalars(
                select(Orders)
                .order_by(Orders.creation_date)
                .where(
                    Orders.order_type.in_(
                        kb_client.choice_order_type_to_payloading[message.text]
                    )
                )
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_state.in_([
                            STATES["open"], 
                            STATES["processed"]
                        ])
                    )
            ).all()
            
            paid_orders = session.scalars(
                select(Orders)
                .order_by(Orders.creation_date)
                .where(
                    Orders.order_type.in_(
                        kb_client.choice_order_type_to_payloading[message.text]
                    )
                )
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_state.not_in([STATES["open"], STATES["processed"]]))
            ).all()
            

        if paid_orders != [] and unpaid_orders == []:
            await bot.send_message(
                message.from_id,
                f"🍀 У тебя все тату заказы оплачены! {MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_client.kb_choice_order_type_to_payloading,
            )
        if unpaid_orders == []:
            await bot.send_message(
                message.from_id,
                MSG_CLIENT_DONT_HAVE_SKETCH_ORDERS,
                reply_markup=kb_client.kb_choice_order_type_to_payloading,
            )

        else:
            kb_unpaid_orders, orders_str, unpaid_order_lst = (
                await send_to_view_orders(orders=unpaid_orders)
            )
            
            async with state.proxy() as data:
                data["kb_unpaid_orders"] = kb_unpaid_orders
                data["orders_str"] = orders_str
                data["unpaid_orders_db"] = unpaid_orders
                data["unpaid_order_lst"] = unpaid_order_lst

            await bot.send_message(
                message.from_id,
                f"📃 Ваши заказы:\n {orders_str}",
                reply_markup=kb_unpaid_orders,
            )
            await FSM_Client_paid_order.next()
            await bot.send_message(
                message.from_id, MSG_WHICH_ORDER_DO_CLIENT_WANT_TO_PAY
            )

    elif any(
        text in message.text for text in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS
    ):
        await state.finish()  # type: ignore
        await bot.send_message(
            message.from_id, MSG_BACK_TO_HOME, reply_markup=kb_client.kb_client_main
        )


async def get_order_name_to_paid(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        unpaid_order_lst = data["unpaid_order_lst"]

    if message.text in unpaid_order_lst:
        price, order_number = 0, ""
        async with state.proxy() as data:  # type: ignore
            order_type = data["order_type"]
            if order_type in kb_client.choice_order_type_to_payloading["Сертификаты 🎫"]:
                order_number = message.text.split()[1]
            else:
                order_number = message.text.split()[3]
                
            data["order_number"] = order_number
            
            with Session(engine) as session:
                price = session.scalars(
                    select(Orders.price)
                        .where(Orders.order_number == order_number)
                ).one()
                
            data["price"] = price
        await FSM_Client_paid_order.next() #-> get_order_check_document_to_paid
        await bot.send_message(
            message.from_id,
            MSG_CLIENT_CHOOSE_ORDER % (order_number, price),
            reply_markup=kb_client.kb_back_cancel,
        )

    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Client_paid_order.previous() # -> command_send_to_view_orders_to_payloading
        await bot.send_message(
            message.from_id,
            MSG_WHICH_ORDER_CLIENT_WANT_TO_PAY,
            reply_markup=kb_client.kb_choice_order_type_to_payloading,
        )

    elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()  # type: ignore
        await bot.send_message(
            message.from_id, MSG_BACK_TO_HOME, reply_markup=kb_client.kb_client_main
        )


async def get_order_check_document_to_paid(message: types.Message, state=FSMContext):
    if message.content_type == "text":
        if message.text in LIST_BACK_COMMANDS:
            await FSM_Client_paid_order.previous()
            async with state.proxy() as data:  # type: ignore
                kb_unpaid_orders = data["kb_unpaid_orders"]
                unpaid_order_lst = data["unpaid_order_lst"]

            await bot.send_message(
                message.from_id,
                f"📃 Заказы:\n" + "".join([f"{number+1}) {order}\n" 
                        for number, order in enumerate(unpaid_order_lst)
                    ]),
                reply_markup=kb_unpaid_orders,
            )

            await bot.send_message(
                message.from_id, MSG_WHICH_ORDER_DO_CLIENT_WANT_TO_PAY
            )

        elif message.text in LIST_CANCEL_COMMANDS:
            await state.finish()  # type: ignore
            await bot.send_message(
                message.from_id,
                f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
                reply_markup=kb_client.kb_client_main,
            )
        else:
            await bot.send_message(message.from_id, MSG_NOT_CORRECT_CHECK_FROM_USER)

    elif message.content_type in ["document", "photo"]:
        async with state.proxy() as data:  # type: ignore
            order_number = data["order_number"]
            price = data["price"]

        check_doc = {}
        doc_name = order_number
        if message.content_type == "document":
            # print("message.document.file_name: ", message.document.file_name)
            check_doc = await check_pdf_document_payment(
                user_id=message.from_id,
                price=str(price),
                file_name=doc_name,
                file_id=message.document.file_id,
            )
        elif message.content_type == "photo":
            # print("message.photo img:", message.photo[0])

            doc_name += ".jpg"
            check_doc = await check_photo_payment(
                message=message,
                user_id=message.from_id,
                price=str(price),
                file_name=doc_name,
                file_id=message.photo[0].file_id,
            )

        if check_doc["result"]:
            check_document_successful_download = ""
            if ".jpg" not in doc_name:
                check_document_successful_download = message.document.file_id
            else:
                check_document_successful_download = message.photo[0].file_id
            with Session(engine) as session:
                new_check_document = CheckDocument(
                    order_number=order_number,
                    doc=check_document_successful_download,
                )
                # session.add(new_check_document)
                order = session.scalars(
                    select(Orders).where(Orders.order_number == order_number)
                ).one()
                order.check_document.append(new_check_document)
                old_state = order.order_state
                order.order_state = STATES["paid"]
                current_order_type = order.order_type
                code = order.code
                session.commit()

            await bot.send_message(
                message.from_id,
                f"🎉 Заказ № {order_number} оплачен! "
                f"Статус заказа сменился с {old_state} на {STATES['paid']}",
            )

            if (
                current_order_type
                in kb_client.choice_order_type_to_payloading["сертификат"]
            ):
                await bot.send_message(message.from_id, f"🎫 Код сертификата: {code}")
                
            if DARA_ID != 0:
                await bot.send_message(
                        DARA_ID,
                        f"🔆 Дорогая Тату-мастерица!\n"
                        f"❕ Заказ на {current_order_type} под номером {order_number} "
                        "имеет новый статус заказа!\n"
                        f"📃 Статус заказа: {STATES['paid']}.\n"
                        f"💬 Имя клиента: {message.from_user.full_name}\n"
                        f"💬 Телеграм клиента: @{message.from_user.username}",
                    )

            elif current_order_type == kb_admin.price_lst_types["constant_tattoo"]:
                await bot.send_message(message.from_id, f"🎉 Жду сеанса!")

            await bot.send_message(
                message.from_id,
                MSG_DO_CLIENT_WANT_TO_DO_MORE,
                reply_markup=kb_client.kb_client_main,
            )
            await state.finish()

        else:
            await bot.send_message(
                message.from_id, 
                f"❌ Чек не подошел! {check_doc['report_msg']}"
            )


def register_handlers_client_payload(dp: Dispatcher):
    # --------------------------Pay order-------------------------
    dp.register_message_handler(
        command_get_payment_order_choice,
        Text(equals=kb_client.client_main["payload_order"], ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        command_get_payment_order_choice, commands="pay_for_the_order", state=None
    )

    dp.register_message_handler(
        command_send_to_view_orders_to_payloading,
        state=FSM_Client_paid_order.order_type,
    )

    dp.register_message_handler(
        get_order_name_to_paid, state=FSM_Client_paid_order.order_name
    )
    dp.register_message_handler(
        get_order_check_document_to_paid,
        Text(equals=[kb_client.cancel_lst[0], kb_client.back_lst[0]], ignore_case=True),
        state=FSM_Client_paid_order.order_check_document,
    )

    dp.register_message_handler(
        get_order_check_document_to_paid,
        content_types=["photo", "document", "message"],
        state=FSM_Client_paid_order.order_check_document,
    )
