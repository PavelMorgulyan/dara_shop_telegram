from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from msg.main_msg import *
from keyboards import kb_client, kb_admin
from handlers.other import *
from handlers.client import (
    CODE_LENTH,
    ORDER_CODE_LENTH,
    fill_client_table,
    CALENDAR_ID,
    DARA_ID,
    FSM_Client_username_info,
)
from validate import check_pdf_document_payment, check_photo_payment
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from db.db_setter import set_to_table
from db.db_getter import get_info_many_from_table

from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select
from db.sqlalchemy_base.db_classes import *


# -------------------------------------------------------сert ORDER-----------------------------------------
class FSM_Client_сert_item(StatesGroup):
    сert_price = State()
    сert_payment_choise = State()
    cert_payment_state_first = State()
    # cert_payment_state_second = State()


# /хочу_сертификат Отправляем цену сертификата
async def command_load_сert_item(message: types.Message):
    if message.text in ["Xочу сертификат 🎫", "/get_certificate"]:
        await FSM_Client_сert_item.сert_price.set()
        await bot.send_message(
            message.from_id,
            "❔ На какую цену хотите сертификат?",
            reply_markup=kb_admin.kb_price,
        )


async def load_сert_price(message: types.Message, state: FSMContext):
    if message.text in kb_admin.price + kb_admin.another_price:
        async with state.proxy() as data:
            data["price"] = message.text
            data["status"] = STATES["open"]

        await FSM_Client_сert_item.next()  # -> load_сert_payment_choice
        await bot.send_message(
            message.from_id,
            f"❔ Хотите оплатить сертификат сейчас или сделать это лично позже?",
            reply_markup=kb_client.kb_pay_now_later,
        )

    elif message.text == "Другая":
        await bot.send_message(
            message.from_id,
            f"❔ На какую сумму хотите сертификат?",
            reply_markup=kb_admin.kb_another_price,
        )

    elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_CANCEL_ACTION + MSG_BACK_TO_HOME,
            reply_markup=kb_client.kb_client_main,
        )
    else:
        await bot.send_message(
            message.from_id, f"⭕️ Пожалуйста, выберете сумму из списка"
        )


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


async def load_сert_payment_choice(message: types.Message, state: FSMContext):
    if message.text == kb_client.now_str:
        async with state.proxy() as data:
            price = data["price"]
        await FSM_Client_сert_item.next()  # -> process_pre_checkout_query
        await bot.send_message(message.chat.id, "🌿 Отлично, давайте сейчас!")
        await bot.send_message(
            message.chat.id,
            f"📎 Отправьте PDF документ или фотографию чека перевода на сумму {price} "
            "по номеру телефона +7(925)885-07-87 на имя Дария Редван Э",
            reply_markup=kb_client.kb_cancel,
        )

        """
        PRICE_сert_1K = types.LabeledPrice(label='Сертификат на 1000 Р.', amount=100000)
        PRICE_сert_2K = types.LabeledPrice(label='Сертификат на 2000 Р.', amount=200000)
        PRICE_сert_3K = types.LabeledPrice(label='Сертификат на 3000 Р.', amount=300000)
        PRICE_сert_4K = types.LabeledPrice(label='Сертификат на 4000 Р.', amount=400000)
        PRICE_сert_5K = types.LabeledPrice(label='Сертификат на 5000 Р.', amount=500000)
        async with state.proxy() as data:
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
            price = data['сert_price']
            await bot.send_invoice(
                message.chat.id,
                title=f'Сертификат на {price}',
                description='Дарите его любимым и друзьям, все заслуживают прекрасную татушку! :blush:✨',
                provider_token=PAYMENTS_PROVIDER_TOKEN,
                currency='rub',
                is_flexible=False,  # True если конечная цена зависит от способа доставки
                prices=[types.LabeledPrice(label=f"Сертификат на {price}", amount = price)],
                start_parameter='certificate',
                payload='some-invoice-payload-for-our-internal-use'
            )#  ,photo_height=512, photo_width=512, photo_size=512,# !=0/None, иначе изображение не покажется
            await FSM_Client_сert_item.next()
            # await state.finish()
        """
    elif message.text == kb_client.later_str:
        # await bot.send_message(message.chat.id, 'Да, хорошо, давайте позже. '\
        # 'Сертификат будет выдан и активирован тогда, когда будет внесена за него оплата.')

        async with state.proxy() as data:
            data["cert_order_number"] = await generate_random_order_number(
                ORDER_CODE_LENTH
            )
            data["check_document"] = []
            new_cert_order = {
                "price": data["price"],
                "status": data["status"],
                "code": None,
                "cert_order_number": data["cert_order_number"],
                "check_document": data["check_document"],
            }
            await create_cert_order(new_cert_order, message)
        with Session(engine) as session:
            user = session.scalars(
                select(User).where(User.telegram_id == message.from_id)
            ).all()
        await state.finish()
        if user == []:
            await bot.send_message(
                message.chat.id,
                f"🍀 Ваш сертификат почти оформлен! Код сертификата будет выдан после оплаты.",
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
                f"🍀 Ваш сертификат оформлен! Номер заказа: {data['cert_order_number']}. "
                "Код сертификата будет выдан после оплаты.\n\n",
            )
            await bot.send_message(
                message.chat.id,
                '❕ Посмотреть свои сертификаты можно в "Мои заказы 📃" -> '
                '"Посмотреть мои сертификаты 🎫".',
            )

            await bot.send_message(
                message.chat.id,
                MSG_DO_CLIENT_WANT_TO_DO_MORE,
                reply_markup=kb_client.kb_client_main,
            )

    elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_CANCEL_ACTION + MSG_BACK_TO_HOME,
            reply_markup=kb_client.kb_client_main,
        )

    else:
        await bot.send_message(
            message.from_id,
            "⛔️ Пожалуйста, выбери из двух вариантов оплаты:"
            " сейчас или потом. Или отмени действие.",
        )


# @dp.pre_checkout_query_handler(state=FSM_Client_сert_item.cert_payment_state_first)
async def process_pre_checkout_query(
    pre_checkout_query: types.PreCheckoutQuery, state=FSMContext
):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)  # type: ignore
    await FSM_Client_сert_item.next()


# @dp.message_handler(content_types=[ContentType.SUCCESSFUL_PAYMENT],
# state=FSM_Client_сert_item.cert_payment_state_second)
async def process_successful_cert_payment(message: types.Message, state=FSMContext):
    check_doc = {}
    async with state.proxy() as data:  # type: ignore
        price = str(data["price"])

    """
    MESSAGES['successful_payment'].format(
        total_amount=message.successful_payment.total_amount // 100,
        currency=message.successful_payment.currency
    )"""

    if message.content_type == "text":
        if any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
            await state.finish()  # type: ignore
            await bot.send_message(
                message.from_id,
                MSG_CANCEL_ACTION + MSG_BACK_TO_HOME,
                reply_markup=kb_client.kb_client_main,
            )

    else:
        doc_name = data["cert_order_number"]
        user_id = message.from_id

        if message.content_type == "document":
            doc_name += ".pdf"
            file = message.document.file_id
            check_doc = await check_pdf_document_payment(
                user_id, price, doc_name, message.document.file_id
            )

        else:
            doc_name = doc_name[:-4] + ".jpg"
            file = message.photo[0].file_id

            check_doc = await check_photo_payment(
                message, user_id, price, doc_name, file
            )

        if check_doc["result"]:
            async with state.proxy() as data:  # type: ignore
                if ".jpg" not in doc_name:
                    data["check_document"] = message.document.file_id
                else:
                    data["check_document"] = message.photo[0].file_id
                code = await generate_random_code(CODE_LENTH)
                cert_order_number = data["cert_order_number"]
                status = data["status"]
                new_cert_order = {
                    "price": int(data["price"]),
                    "status": STATES["paid"],
                    "code": code,
                    "cert_order_number": data["cert_order_number"],
                    "check_document": data["check_document"],
                }

                await create_cert_order(new_cert_order, message)

            await bot.send_message(
                message.chat.id,
                f"🎉 Заказ оплачен! \n"
                f"🎫 Вот ваш код на сертификат на сумму {price}: {code}. \n\n"
                "❕ Сертификат действует неограничено по времени!",
            )

            with Session(engine) as session:
                user = session.scalars(
                    select(User).where(User.telegram_id == message.from_id)
                ).all()

            if user == []:
                await bot.send_message(
                    message.chat.id,
                    f"🎉 Ваш заказ сертификата под номером {cert_order_number} почти оформлен!",
                )

                await bot.send_message(
                    message.chat.id,
                    MSG_TO_CHOICE_CLIENT_PHONE,
                    reply_markup=kb_client.kb_phone_number,
                )

                await state.finish()  # type: ignore
                await FSM_Client_username_info.phone.set()

            else:
                await bot.send_message(
                    message.chat.id,
                    f"🎉 Ваш заказ сертификата под номером {cert_order_number} оформлен!\n\n"
                    "🟢 Хотите сделать что-нибудь еще?",
                    reply_markup=kb_client.kb_client_main,
                )

                await state.finish()  # type: ignore

            # TODO дополнить id Шуны
            if DARA_ID != 0:
                await bot.send_message(
                    DARA_ID,
                    f"❕Дорогая Тату-мастерица! "
                    f"У пользователя {message.from_user.full_name} появился сертификат на сумму {price}\n"
                    f"Номер сертификата: {cert_order_number}!\n"
                    f"Статус заказа: {status}",
                )

        else:
            await bot.send_message(
                message.from_id, f"❌ Чек не подошел. %s " % check_doc["repost_msg"]
            )


# --------------------------------------GET VIEW CERT ORDER-----------------------------------------
# /посмотреть_мои_сертификаты
async def get_clients_cert_order(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.user_id == message.from_id)
            .where(order.order_type == "сертификат")
        ).all()
    if orders == []:
        await bot.send_message(
            message.from_id,
            "⭕️ У тебя пока нет сертификатов. "
            'Ты можешь приобрести сертификат по кнопке "Хочу сертификат" в главном меню.',
            reply_markup=kb_client.kb_choice_order_view,
        )
    else:
        msg = ""
        for order in orders:
            msg += (
                f"🎫 Cертификат № {order.order_number}\n"
                f"💰 Цена сертификата: {order.price}\n"
            )

            if order.order_state == STATES["paid"]:
                msg += f"🏷 Код сертификата: {order.code}\n"

            elif order.code in [STATES["complete"]] + list(STATES["closed"].values()):
                msg += "🚫 Сертификат уже использован\n"

            else:
                msg += "⛔️ Сертификат неоплачен\n"

            await bot.send_message(message.from_user.id, msg)
            msg = ""

        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_client.kb_choice_order_view,
        )


# ------------------------------------------сert------------------------------------------------------
def register_handlers_client_cert(dp: Dispatcher):
    dp.register_message_handler(
        command_load_сert_item,
        Text(equals=kb_client.client_main["client_want_cert"], ignore_case=True),
    )
    dp.register_message_handler(
        command_load_сert_item, commands=["get_certificate"], state=None
    )
    dp.register_message_handler(load_сert_price, state=FSM_Client_сert_item.сert_price)
    dp.register_message_handler(
        load_сert_payment_choice, state=FSM_Client_сert_item.сert_payment_choise
    )
    dp.register_message_handler(
        process_successful_cert_payment,
        content_types=["photo", "document", "message", "text"],
        state=FSM_Client_сert_item.cert_payment_state_first,
    )
    dp.register_message_handler(
        get_clients_cert_order,
        Text(
            equals=kb_client.choice_order_view["client_watch_cert_order"],
            ignore_case=True,
        ),
    )
    # dp.pre_checkout_query_handler(process_pre_checkout_query, func=lambda query: True)
    # dp.register_message_handler(process_successful_payment,  content_types=ContentType.SUCCESSFUL_PAYMENT)
