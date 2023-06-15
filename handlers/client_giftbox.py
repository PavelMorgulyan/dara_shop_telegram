from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from msg.main_msg import *
from keyboards import kb_client
from handlers.other import *
from handlers.client import (
    ORDER_CODE_LENTH,
    DARA_ID,
    FSM_Client_username_info,
    CALENDAR_ID,
)
from validate import check_pdf_document_payment, check_photo_payment
from handlers.calendar_client import obj

from sqlalchemy.orm import Session
from sqlalchemy import select
from db.sqlalchemy_base.db_classes import *

from datetime import datetime


# -----------------------------------------GIFTBOX NEW ORDER----------------------------------
class FSM_Client_giftbox_having(StatesGroup):
    giftbox_note_choice = State()
    giftbox_get_note = State()
    giftbox_choice_pay_method = State()
    # giftbox_pay_func = State()
    get_check_photo = State()


class FMS_Client_get_info_from_user(StatesGroup):
    get_phone = State()


async def giftbox_command(message: types.Message):
    if message.text.lower() in ["гифтбокс 🎁", "/get_giftbox", "get_giftbox"]:
        # защита от спама множества заказов. Клиент может заказать только по одному типу товара
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders)
                .where(Orders.order_type == "гифтбокс")
                .where(Orders.order_state.in_([STATES["open"]]))
                .where(Orders.user_id == message.from_id)
            ).all()
            user = session.scalars(select(User).where(User.telegram_id == message.from_id)).all()
        
        if user == []:
            await bot.send_message(message.from_id, MSG_INFO_START_ORDER) 
            await bot.send_message(message.from_id, MSG_INFO_GIFTBOX_ORDER)

        if orders == []:
            await FSM_Client_giftbox_having.giftbox_note_choice.set()  # -> giftbox_order_giftbox_note_choice
            await bot.send_photo(
                message.chat.id, open("giftbox_title.jpg", "rb"), GIFTBOX_DESCRIPTION
            )
            # await bot.send_message(message.from_id, 'Какой гифтбокс ты хочешь?',
            # reply_markup=kb_client_giftbox_names)
            await bot.send_message(
                message.from_id,
                f"Хотите что-нибудь добавить к своему заказу?",
                reply_markup=kb_client.kb_giftbox_note,
            )
        else:
            await bot.send_message(message.from_id, MSG_CLIENT_ALREADY_HAVE_OPEN_ORDER)


async def giftbox_order_giftbox_note_choice(message: types.Message, state: FSMContext):
    if message.text == kb_client.giftbox_note_dict["client_want_to_add_something"]:
        await FSM_Client_giftbox_having.next()  # -> giftbox_order_add_giftbox_note
        await bot.send_message(
            message.from_id,
            f"🌿 Оставьте свой комментарий к заказу",
            reply_markup=kb_client.kb_back_cancel,
        )

    elif message.text == kb_client.giftbox_note_dict["client_dont_add_something"]:
        async with state.proxy() as data:
            data["giftbox_note"] = None  # 'Без описания'

        for i in range(2):
            await FSM_Client_giftbox_having.next()  # -> giftbox_order_pay_method
        await bot.send_message(
            message.from_id,
            f"❔ Каким способом оплатить?",
            reply_markup=kb_client.kb_pay_now_later,
        )

    elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_main,
        )

    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


async def set_giftbox_order(data: dict, message: types.Message):
    with Session(engine) as session:
        new_cert_order = Orders(
            order_type="гифтбокс",
            user_id=message.from_id,
            order_note=data["order_note"],
            order_state=STATES["open"],
            order_number=data["order_number"],
            creation_date=datetime.now(),
            price=data["price"],
            check_document=data["check_document"],
            username=message.from_user.full_name,
        )
        session.add(new_cert_order)
        session.commit()


async def giftbox_order_add_giftbox_note(message: types.Message, state: FSMContext):
    if any(text in message.text for text in LIST_BACK_COMMANDS):
        await FSM_Client_giftbox_having.previous()  # -> giftbox_order_giftbox_note_choice
        await bot.send_message(
            message.from_id,
            f"❔ Что-нибудь добавить к своему заказу? "
            "Ответь на вопрос, а потом напишите, что какой комментарий хотите оставить к заказу.",
            reply_markup=kb_client.kb_giftbox_note,
        )
        #'Да, мне есть чего добавить! 🌿, Нет, мне нечего добавить ➡️'

    elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_main,
        )

    else:
        async with state.proxy() as data:
            data["giftbox_note"] = message.text

        await bot.send_message(
            message.chat.id, "💬 Отлично, в заказ был добавлен комментарий!"
        )

        await FSM_Client_giftbox_having.next()  # -> giftbox_order_pay_method
        await bot.send_message(
            message.from_id,
            "❔ Хотите оплатить заказ сейчас? ",
            reply_markup=kb_client.kb_yes_no,
        )


async def giftbox_order_pay_method(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["giftbox_order_number"] = await generate_random_order_number(
            ORDER_CODE_LENTH
        )
        data["creation_date"] = datetime.now()
        with Session(engine) as session:
            price = (
                session.scalars(
                    select(OrderPriceList).where(OrderPriceList.type == "гифтбокс")
                )
                .one()
                .price
            )

        data["price"] = price  # тип int
        giftbox_order_number = await generate_random_order_number(ORDER_CODE_LENTH)

        if message.text in [kb_client.later_str, kb_client.no_str]:
            new_giftbox_order = {
                "order_note": data["giftbox_note"],
                "order_number": giftbox_order_number,
                "order_state": STATES["open"],
                "check_document": [],
                "price": price,
            }
            await set_giftbox_order(new_giftbox_order, message)

            with Session(engine) as session:
                user = session.scalars(
                    select(User).where(User.telegram_id == message.from_id)
                ).all()

            await state.finish()
            if user == []:
                await bot.send_message(
                    message.chat.id,
                    f"🎉 Ваш заказ гифтбокса под номером {giftbox_order_number} почти оформлен!",
                )

                await bot.send_message(
                    message.chat.id,
                    MSG_TO_CHOICE_CLIENT_PHONE,
                    reply_markup=kb_client.kb_phone_number,
                )

                await FSM_Client_username_info.phone.set()
            else:
                await bot.send_message(
                    message.chat.id,
                    f"🍀 Ваш заказ гифтбокса под номером {giftbox_order_number} оформлен!\n\n"
                    f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                    reply_markup=kb_client.kb_client_main,
                )

        elif message.text in [kb_client.now_str, kb_client.yes_str]:
            """  
            if PAYMENTS_PROVIDER_TOKEN.split(':')[1] == 'TEST':
                await bot.send_message(message.chat.id, 'Т.к. это тестовый режим, можно'\
            '  провести оплату следующими способами:\n'\
            '1) VISA 4111 1111 1111 1111, Дата истечения срока действия 2024/12,'\
            '  код 123, Проверочный код 3-D Secure: 12345678\n'\
            '2) MasterCard 5555 5555 5555 5599, Дата истечения срока действия: '\
            ' 2024/12, Проверочный код на обратной стороне: 123\n'\
            '3) MasterCard 5479 2700 0000 0000, Дата истечения срока действия: '\
            ' 2022/03, Проверочный код на обратной стороне: 123, Проверочный код 3-D Secure: 12345678\n'\
            '4) МИР 2200 0000 0000 0053, Дата истечения срока действия: '\
            ' 2024/12, Проверочный код на обратной стороне: 123, Проверочный код 3-D Secure: 12345678')
            await bot.send_invoice(
                message.chat.id,
                title=f'Гифтбокс на {price}',
                description='Этот Гифтбокс будет прекрасным подарком! ✨',
                provider_token=PAYMENTS_PROVIDER_TOKEN,
                currency='rub',
                is_flexible=False,  # True если конечная цена зависит от способа доставки
                prices=[types.LabeledPrice(label=f"Гифтбокс на {price}", amount = price)],
                start_parameter='giftbox',
                payload='some-invoice-payload-for-our-internal-use',
                photo_url = data['giftbox_photo']
                ,photo_height=512, photo_width=512, photo_size=512
            )#  ,photo_height=512, photo_width=512, photo_size=512,# !=0/None, иначе изображение не покажется
            await FSM_Client_giftbox_having.next()"""
            await FSM_Client_giftbox_having.next()  # -> process_successful_giftbox_payment_by_photo
            await bot.send_message(
                message.chat.id,
                "🌿 Хорошо! Давай оплатим сейчас.\n\n"
                f"❕ Пожалуйста, приложи снимок или PDF документ чека о "
                f"переводе средств на сумму {price} по "
                "номеру телефона +7-925-885-07-87",
            )


#! Перехода в эту функцию нет, сохранена на случай, если нужна будет оплата через Сбер-виджет
# @dp.message_handler(content_types=[ContentType.SUCCESSFUL_PAYMENT],
# state=FSM_Client_giftbox_having.giftbox_payment_state_second)
async def process_successful_giftbox_payment(message: types.Message, state=FSMContext):
    pmnt = message.successful_payment.to_python()
    """ 
    for key, val in pmnt.items():
        print(f'{key} = {val}') 
    """
    async with state.proxy() as data:  # type: ignore
        giftbox_order_number = data["giftbox_order_number"]

    await bot.send_message(
        message.chat.id, f"🎉 Заказ оплачен! Номер заказа: {giftbox_order_number}"
    )

    async with state.proxy() as data:  # type: ignore
        # если человек оплатил, то выставляем статус Обработан
        data["order_state"] = STATES["paid"]
        data["check_document"] = [
            CheckDocument(
                order_number=giftbox_order_number,
                doc="Заказ оплачен",
            )
        ]
        new_giftbox_order = {
            "order_note": data["giftbox_note"],
            "order_number": data["giftbox_order_number"],
            "check_document": data["check_document"],
            "order_state": data["order_state"],
            "price": data["price"],
        }

        await set_giftbox_order(new_giftbox_order, message)
        with Session(engine) as session:
            user = session.scalars(
                select(User).where(User.telegram_id == message.from_id)
            ).all()
    await state.finish()  # type: ignore

    if user == []:
        await bot.send_message(
            message.chat.id,
            f"🎉 Ваш заказ гифтбокса под номером {giftbox_order_number} почти оформлен!",
        )

        await bot.send_message(
            message.chat.id,
            MSG_TO_CHOICE_CLIENT_PHONE,
            reply_markup=kb_client.kb_phone_number,
        )

        await FSM_Client_username_info.phone.set()
    else:
        await bot.send_message(
            message.chat.id,
            f"🍀 Ваш заказ гифтбокса под номером {giftbox_order_number} оформлен!\n\n"
            f"{MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET}",
            reply_markup=kb_client.kb_client_main,
        )


# Ждем документ или фотографию чека от пользователя
async def process_successful_giftbox_payment_by_photo(
    message: types.Message, state=FSMContext
):
    async with state.proxy() as data:  # type: ignore
        # Проверяем чек на корректность
        doc_name = data["giftbox_order_number"]
        user_id = message.from_id
        check_doc = {}
        if message.content_type == "document":
            doc_name += ".pdf"
            check_doc = await check_pdf_document_payment(
                user_id, str(data["price"]), doc_name, message.document.file_id
            )

        elif message.content_type == "photo":
            doc_name = doc_name[:-4] + ".jpg"
            check_doc = await check_photo_payment(
                message, user_id, str(data["price"]), doc_name, message.photo[0].file_id
            )

        if check_doc["result"]:
            if ".pdf" in doc_name:
                check_document = message.document.file_id
            else:
                check_document = message.photo[0].file_id

            giftbox_order_number = data["giftbox_order_number"]
            data["order_state"] = STATES[
                "paid"
            ]  # если человек оплатил, то выставляем статус Обработан
            status = data["order_state"]
            data["check_document"] = [
                CheckDocument(
                    order_number=giftbox_order_number,
                    doc=check_document,
                )
            ]

            new_giftbox_order = {
                "order_note": data["giftbox_note"],
                "order_number": data["giftbox_order_number"],
                "check_document": data["check_document"],
                "order_state": data["order_state"],
                "price": data["price"],
            }

            await set_giftbox_order(new_giftbox_order, message)
            with Session(engine) as session:
                user = session.scalars(
                    select(User).where(User.telegram_id == message.from_id)
                ).all()

            await bot.send_message(
                message.chat.id,
                f"🎉 Заказ оплачен! Вот номер вашего заказа: {giftbox_order_number}",
            )
            await state.finish()  # type: ignore

            if user == []:
                await bot.send_message(
                    message.chat.id,
                    f"🎉 Ваш заказ гифтбокса под номером {giftbox_order_number} почти оформлен! "
                    "Осталось только добавить свой телефон.",
                )
                await bot.send_message(
                    message.chat.id,
                    MSG_TO_CHOICE_CLIENT_PHONE,
                    reply_markup=kb_client.kb_phone_number,
                )
                await FSM_Client_username_info.phone.set()
            else:
                await bot.send_message(
                    message.chat.id,
                    f"🍀 Ваш заказ гифтбокса под номером {giftbox_order_number} оформлен!\n\n"
                    f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                    reply_markup=kb_client.kb_client_main,
                )

                # TODO дополнить id Шуны
                if DARA_ID != 0:
                    await bot.send_message(
                        DARA_ID,
                        f"Дорогая Тату-мастерица! "
                        f"Поступил новый заказ на гифтбокс под номером {giftbox_order_number}!\n"
                        f"Статус заказа: {status}\n"
                        f"Имя клиента: {message.from_user.full_name}",
                    )

                    event = await obj.add_event(
                        CALENDAR_ID,
                        f"🎁 Новый гифтбокс заказ № {giftbox_order_number}",
                        f"📃 Описание заказа: {data['giftbox_note']}\n"
                        f"💬 Имя клиента: {message.from_user.full_name}\n"
                        f"💬 Телеграм клиента: @{message.from_user.username}",
                        f'{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}',  # '2023-02-02T09:07:00',
                        f'{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}',  # '2023-02-03T17:07:00'
                    )

        else:
            await bot.send_message(
                message.from_id, f"❌ Чек не подошел. %s " % check_doc["repost_msg"]
            )


# ------------------------------------GET VIEW GIFTBOX ORDER--------------------------------------
# /посмотреть_мои_гифтбокс_заказы
async def get_clients_giftbox_order(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.order_type == "гифтбокс")
            .where(Orders.user_id == message.from_id)
        ).all()

    if orders == []:
        await bot.send_message(
            message.from_id,
            f"⭕️ У вас пока нет гифтбокс заказов.\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_client.kb_client_choice_order_view,
        )

    else:
        message_to_send = ""
        for order in orders:
            message_to_send = (
                f"🎁 Гифтбокс заказ № {order.order_number}\n"
                f"🕒 Дата открытия заказа: {order.creation_date.strftime('%H:%M %d/%m/%Y')}\n"
            )
            if order.order_note != None:
                message_to_send += f"💬 Описание заказа: {order.order_note}\n"

            if any(
                str(order_state) in order.order_state
                for order_state in list(STATES["closed"].values())
            ):
                message_to_send += f"❌ Состояние заказа: {order.order_state}\n"

            elif any(
                str(order_state) in order.order_state
                for order_state in [STATES["open"], STATES["paid"]]
            ):
                message_to_send += f"🟡 Состояние заказа: {order.order_state}\n"

            elif order.order_state == STATES["complete"]:
                message_to_send += f"🟢 Состояние заказа: {order.order_state}\n"

            await bot.send_message(message.from_user.id, message_to_send)
            message_to_send = ""

        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_client.kb_client_choice_order_view,
        )


# --------------------------------------GIFTBOX------------------------------------------
def register_handlers_client_giftbox(dp: Dispatcher):
    dp.register_message_handler(
        giftbox_command,
        Text(equals=kb_client.client_main["client_want_giftbox"], ignore_case=True),
        state=None,
    )
    dp.register_message_handler(giftbox_command, commands=["get_giftbox"], state=None)
    # dp.register_message_handler(giftbox_order_get_having_item,
    # state=FSM_Client_giftbox_having.giftbox_choice_having_item)
    # dp.register_message_handler(giftbox_order_get_name,
    # state=FSM_Client_giftbox_having.giftbox_name)
    dp.register_message_handler(
        giftbox_order_giftbox_note_choice,
        state=FSM_Client_giftbox_having.giftbox_note_choice,
    )
    dp.register_message_handler(
        giftbox_order_add_giftbox_note, state=FSM_Client_giftbox_having.giftbox_get_note
    )
    dp.register_message_handler(
        giftbox_order_pay_method,
        state=FSM_Client_giftbox_having.giftbox_choice_pay_method,
    )
    dp.register_message_handler(
        process_successful_giftbox_payment_by_photo,
        content_types=["photo", "document"],
        state=FSM_Client_giftbox_having.get_check_photo,
    )

    dp.register_message_handler(
        get_clients_giftbox_order,
        Text(
            equals=kb_client.choice_order_view["client_watch_giftbox_order"],
            ignore_case=True,
        ),
        state=None,
    )
    dp.register_message_handler(
        get_clients_giftbox_order, commands=["посмотреть_мои_гифтбокс_заказы"]
    )
