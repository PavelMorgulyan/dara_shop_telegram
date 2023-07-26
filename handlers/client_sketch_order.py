from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from msg.main_msg import *
from keyboards import kb_client, kb_admin
from handlers.other import generate_random_order_number, STATES, clients_status
from handlers.client import (
    CODE_LENTH,
    fill_client_table,
    DARA_ID,
    FSM_Client_username_info,
    CALENDAR_ID,
)
from handlers.calendar_client import obj

from sqlalchemy.orm import Session
from sqlalchemy import select
from db.sqlalchemy_base.db_classes import *
from datetime import datetime

"""
    Статусы заказа:
    Открыт — заказ был создан в базе данных, но ещё не был обработан.
    Обработан — оплата была получена.
    Выполнен — вся работа по заказу завершена.
    Отклонен — заказ отклонен админом.
    Отложен — заказ ещё не обработан, так как в нём содержатся товары, которых нет в наличии. 
        Только для гифтбокса
    Аннулирован — заказ был отменён покупателем.
    Ожидает ответа — заказ был создан, когда покупатель оформил заявку на обратный ответ.
"""


# -----------------------------------------CREATE TATTOO SKETCH ORDER-------------------------------
# Хочу эскиз тату
class FSM_Client_tattoo_sketch_order(StatesGroup):
    tattoo_sketch_note = State()
    load_sketch_photo = State()


# Начало диалога с пользователем, который хочет добавить новый заказ эскиза
async def start_create_new_tattoo_sketch_order(message: types.Message):
    # защита от спама множества заказов. Клиент может заказать только по одному типу товара
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.order_type == "эскиз")
            .where(Orders.order_state.in_([STATES["open"]]))
            .where(Orders.user_id == message.from_id)
        ).all()
        user = session.scalars(select(User).where(User.telegram_id == message.from_id)).all()
        
    if user == []:
        await bot.send_message(message.from_id, MSG_INFO_START_ORDER) 
        await bot.send_message(message.from_id, MSG_INFO_SKETCH_ORDER)
    
    if orders == []:
        await FSM_Client_tattoo_sketch_order.tattoo_sketch_note.set()
        await bot.send_message(
            message.from_id,
            "🕸 Отлично, давай сделаем эскиз! \n\n"
            f"{MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT_CONCEPTS}",
            reply_markup=kb_client.kb_start_dialog_sketch_order,
        )
    else:
        await bot.send_message(message.from_id, MSG_CLIENT_ALREADY_HAVE_OPEN_ORDER)


async def fill_sketch_order_table(data: dict, message: types.Message):
    new_user = False
    with Session(engine) as session:
        user = session.scalars(
            select(User).where(User.telegram_id == message.from_id)
        ).all()
        if user == []:
            user = User(
                name=message.from_user.full_name,
                telegram_name=f"@{message.from_user.username}",
                telegram_id=message.from_id,
                phone=None,
                status=clients_status['client']
            )
            session.add(user)
            session.commit()
            new_user = True

        price = (
            session.scalars(
                select(OrderPriceList).where(OrderPriceList.type == "эскиз")
            )
            .one()
            .price
        ) 
        new_tattoo_sketch_order = Orders(
            order_type="эскиз",
            user_id=message.from_id,
            order_photo=data["photo_lst"],
            order_note=data["sketch_description"],
            order_state=data["state"],
            creation_date=datetime.now(),
            order_number=data["tattoo_sketch_order_number"],
            price=price,
            check_document=data["check_document"],
            username=message.from_user.full_name,
        )
        session.add(new_tattoo_sketch_order)
        session.commit()

    date = datetime.now()

    if DARA_ID != 0:
        await bot.send_message(
            DARA_ID,
            f"Дорогая Тату-мастерица! "
            f"🕸 Поступил новый заказ на эскиз под номером {data['tattoo_sketch_order_number']}!",
        )

    if data["sketch_description"] is None:
        data["sketch_description"] = "Без описания"

    event = await obj.add_event(
        CALENDAR_ID,
        f"Новый эскиз заказ №{str(data['tattoo_sketch_order_number'])}",
        f"Описание эскиза тату: {data['sketch_description']}; "
        f"📃 Статус заказа: {data['state']}. \n"
        f"💬 Имя клиента: {message.from_user.full_name}\n"
        f"💬 Телеграм клиента: @{message.from_user.username}",
        f'{date.strftime("%Y-%m-%dT%H:%M:%S")}',  # '2023-02-02T09:07:00',
        f'{date.strftime("%Y-%m-%dT%H:%M:%S")}',  # '2023-02-03T17:07:00'
    )

    await bot.send_message(
        message.from_id,
        "🎉 Заказ на эскиз оформлен! "
        f"Номер заказа эскиза {data['tattoo_sketch_order_number']}",
    )

    await bot.send_message(
        message.from_id,
        f"❕ Оплата эскиза осуществляется только после того, как администратор подтвердит заказ. "
        "К вам придет уведомление через бота о том, что заказ подтвержден и готов к оплате.\n"
        "💬 Скоро Дара свяжется с тобой!\n\n",
    )
    if new_user:
        await bot.send_message(
            message.chat.id,
            MSG_TO_CHOICE_CLIENT_PHONE,
            reply_markup=kb_client.kb_phone_number,
        )
        await FSM_Client_username_info.phone.set()
    else:
        await bot.send_message(
            message.from_id,
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_client.kb_client_main,
        )


async def send_to_view_tattoo_admin_sketch(message: types.Message):
    with Session(engine) as session:
        tattoo = session.scalars(select(TattooItems).where(TattooItems.name == message.text)).one()
        # ? TODO нужно ли выводить размер и цену?
        msg = f"📃 Название: {tattoo.name}\n🎨 Цвет: {tattoo.colored}\n"

        if tattoo.note.lower() not in ["без описания", None]:
            msg += f"💬 Описание: {tattoo.note}\n"  # 💰 Цена: {tattoo.price}\n'

        with Session(engine) as session:
            photos = session.scalars(
                select(TattooItemPhoto).where(
                    TattooItemPhoto.tattoo_item_name == tattoo.name
                )
            ).all()
        media = []
        for photo in photos:
            media.append(types.InputMediaPhoto(photo.photo, msg))

        await bot.send_media_group(message.from_user.id, media=media)


async def get_sketch_desc_order(message: types.Message, state: FSMContext):
    tattoo_sketch_order_number = await generate_random_order_number(CODE_LENTH)
    async with state.proxy() as data:
        data["tattoo_sketch_order_number"] = tattoo_sketch_order_number
        data["sketch_order_photo_counter"] = 0
        data["sketch_photo"] = []
    with Session(engine) as session:
        tattoo_items = session.scalars(
            select(TattooItems).where(TattooItems.creator == "admin")
        ).all()
    kb_tattoo_names = ReplyKeyboardMarkup(resize_keyboard= True)
    tattoo_name_lst = []
    for tattoo in tattoo_items:
        tattoo_name_lst.append(tattoo.name)
        kb_tattoo_names.add(KeyboardButton(tattoo.name))
        
    kb_tattoo_names.add(kb_client.back_btn).add(kb_client.cancel_btn)
    if message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_main,
        )

    elif message.text in LIST_BACK_COMMANDS:
        await bot.send_message(
            message.from_id,
            f"{MSG_CLIENT_GO_BACK}{MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT_CONCEPTS}",
            reply_markup=kb_client.kb_start_dialog_sketch_order,
        )

    # Посмотреть галерею 📃
    elif (
        message.text == kb_client.start_dialog_sketch_order["client_want_to_see_galery"]
    ):
        await bot.send_message(
            message.from_id, "📃 Какое тату показать?", reply_markup= kb_tattoo_names
        )
    elif message.text in tattoo_name_lst:
        await send_to_view_tattoo_admin_sketch(message)
        await bot.send_message(
            message.from_user.id, "❔ Какое описание оставить для эскиза? Напишите ответ в строке.",
            reply_markup= kb_client.kb_back_cancel
        )

    # переход: Хочешь отправить фото твоей идеи для переводной татуировки?' -> Да
    elif message.text == kb_client.yes_str:
        await FSM_Client_tattoo_sketch_order.next()  # -> get_photo_sketch_order
        await bot.send_message(
            message.from_id,
            "📎 Отправь фото идеи для эскиза тату!",
            reply_markup=kb_client.kb_back_cancel,
        )

    # переход: Хочешь отправить фото твоей идеи для переводной татуировки?' -> Нет
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            doc = (
                []
            )  # [CheckDocument(doc=None, order_number= data['tattoo_sketch_order_number'])]
            new_sketch_order = {
                "tattoo_sketch_order_number": tattoo_sketch_order_number,
                "sketch_description": data["sketch_description"],
                "photo_lst": [],
                "state": STATES["open"],
                "check_document": doc,
            }
            await fill_sketch_order_table(new_sketch_order, message)
        await state.finish()

    else:
        async with state.proxy() as data:
            data["sketch_description"] = message.text

        await bot.send_message(
            message.from_id,
            "❔ Хотите отправить фото идеи для переводной татуировки?",
            reply_markup=kb_client.kb_yes_no,
        )


async def get_photo_sketch_order(message: types.Message, state: FSMContext):
    if message.content_type == "text":
        if message.text in LIST_BACK_COMMANDS:
            await FSM_Client_tattoo_sketch_order.previous()  # -> get_sketch_desc_order
            await bot.send_message(
                message.from_id,
                f"{MSG_CLIENT_GO_BACK}"
                "❔Хотите отправить фото идеи для переводной татуировки?",
                reply_markup=kb_client.kb_yes_no,
            )

        elif message.text in LIST_CANCEL_COMMANDS:
            await state.finish()
            await bot.send_message(
                message.from_id,
                f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
                reply_markup=kb_client.kb_client_main,
            )

        elif (
            message.text
            == kb_client.client_choice_send_more_photo_to_skatch_order["more_photo"]
        ):
            async with state.proxy() as data:
                data["sketch_order_photo_counter"] = 0
            await bot.send_message(message.from_id, MSG_CLIENT_LOAD_PHOTO)

        elif (
            message.text
            == kb_client.client_choice_send_more_photo_to_skatch_order["end_order"]
        ):
            async with state.proxy() as data:
                doc = (
                    []
                )  # [CheckDocument(doc=None, order_number= data['tattoo_sketch_order_number'])]
                new_sketch_order = {
                    "tattoo_sketch_order_number": data["tattoo_sketch_order_number"],
                    "sketch_description": data["sketch_description"],
                    "photo_lst": data["sketch_photo"],
                    "state": STATES["open"],
                    "check_document": doc,
                }
            await fill_sketch_order_table(new_sketch_order, message)
            await state.finish()

    elif message.content_type == "photo":
        async with state.proxy() as data:
            data["sketch_photo"].append(
                OrderPhoto(
                    photo=message.photo[0].file_id,
                    order_number=data["tattoo_sketch_order_number"],
                    telegram_user_id=message.from_id,
                )
            )

            sketch_order_photo_counter = data["sketch_order_photo_counter"]
            data["sketch_order_photo_counter"] = message.media_group_id

        if sketch_order_photo_counter != data["sketch_order_photo_counter"]:
            await bot.send_message(
                message.from_id,
                "❔ Хотите отправить еще фотографии? Или можно завершить заказ эскиза?",
                reply_markup=kb_client.kb_client_choice_send_more_photo_to_skatch_order,
            )


# ---------------------------------------------GET VIEW SKETCH ORDER--------------------------------------
class FSM_Client_send_to_client_view_sketch_order(StatesGroup):
    get_order_number = State()


# Посмотреть мои заказы эскизов 🎨
async def get_clients_tattoo_sketch_order(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_type == "эскиз")
        ).all()

    if orders == []:
        await bot.send_message(
            message.from_id,
            f"⭕️ У вас нет заказов для эскизов.\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_client.kb_client_choice_order_view,
        )
    else:
        await FSM_Client_send_to_client_view_sketch_order.get_order_number.set()
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for order in orders:
            kb.add(KeyboardButton(f"Эскиз №{order.order_number} {order.order_state}"))

        kb.add(kb_client.cancel_btn)
        await bot.send_message(
            message.from_id, MSG_WHICH_ORDER_DO_CLIENT_WANT_TO_SEE, reply_markup=kb
        )


async def get_sketch_order_number(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_type == "эскиз")
        ).all()
    kb_lst = []
    for order in orders:
        kb_lst.append(f"Эскиз №{order.order_number} {order.order_state}")

    if message.text in kb_lst:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == message.text.split()[1][1:])
            ).one()

            creation_date = order.creation_date.strftime("%H:%M %d/%m/%Y")
            msg = (
                f"Заказ № {order.order_number} от {creation_date}\n"
                f"📜 Описание тату эскиза: {order.order_note}\n"
            )

            if order.order_name is not None:
                msg += f"🍃 Имя: {order.order_name}\n"

            if order.order_state in list(STATES["closed"].values()):
                msg += f"❌ Состояние заказа: {order.order_state}\n"
            else:
                msg += f"📃 Состояние заказа: {order.order_state}\n"

            sketch_photos = (
                Session(engine)
                .scalars(
                    select(OrderPhoto).where(
                        OrderPhoto.order_number == order.order_number
                    )
                )
                .all()
            )
            media = []
            for sketch_photo in sketch_photos:
                media.append(types.InputMediaPhoto(sketch_photo.photo, msg))

            if media != []:
                await bot.send_chat_action(
                    message.chat.id, types.ChatActions.UPLOAD_DOCUMENT
                )
                await bot.send_media_group(message.chat.id, media=media)
                if len(media) > 1:
                    await bot.send_message(message.from_user.id, msg)

        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_client.kb_client_choice_order_view,
        )
        await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_choice_order_view,
        )

    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


# ----------------------------------------CLIENT UPDATE SKETCH ORDER PHOTO----------------------------------
class FSM_Client_get_new_photo_to_sketch_order(StatesGroup):
    get_order_id = State()
    get_new_photo = State()


# Добавить фотографию к заказу эскиза 🌿
async def command_client_add_new_photo_to_sketch_order(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.order_type == "эскиз")
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.not_in(list(STATES["closed"].values())))
        ).all()

    if orders == []:
        await bot.send_message(message.from_id, "⭕️ У вас пока нет заказанных эскизов.")
        await bot.send_message(
            message.from_id,
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_client.kb_client_choice_order_view,
        )
    else:
        kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
        for order in orders:
            kb_orders.add(
                KeyboardButton(
                    f"Эскиз №{order.order_number} от "
                    f"{order.creation_date.strftime('%H:%M %d/%m/%Y')}"
                )
            )
        kb_orders.add(kb_client.cancel_btn)

        await FSM_Client_get_new_photo_to_sketch_order.get_order_id.set()
        await bot.send_message(
            message.from_id,
            "❔ Для какого заказа хотите добавить фотографию?",
            reply_markup=kb_orders,
        )


async def get_order_id_to_add_new_photo_to_sketch_order(
    message: types.Message, state: FSMContext
):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.order_type == "эскиз")
            .where(Orders.user_id == message.from_id)
        ).all()
    kb_orders_lst = []
    for order in orders:
        kb_orders_lst.append(
            f"Эскиз №{order.order_number} от "
            f"{order.creation_date.strftime('%H:%M %d/%m/%Y')}"
        )

    if message.content_type == "text":
        if message.text in kb_orders_lst:
            async with state.proxy() as data:
                data["sketch_order_number"] = message.text.split()[1][1:]
                data["sketch_photo"] = []
                data["sketch_order_photo_counter"] = 0

            await FSM_Client_get_new_photo_to_sketch_order.next()  # -> get_photo_to_sketch_order
            await bot.send_message(
                message.from_id,
                MSG_CLIENT_LOAD_PHOTO,
                reply_markup=kb_client.kb_back_cancel,
            )

        elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
            await state.finish()
            await bot.send_message(
                message.from_id,
                f"{MSG_CANCEL_ACTION}{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}",
                reply_markup=kb_client.kb_client_choice_order_view,
            )
        else:
            await bot.send_message(
                message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
            )


async def get_photo_to_sketch_order(message: types.Message, state: FSMContext):
    if message.content_type == "photo":
        async with state.proxy() as data:
            data["sketch_photo"].append(
                OrderPhoto(
                    photo=message.photo[0].file_id,
                    order_number=data["sketch_order_number"],
                    telegram_user_id=message.from_id,
                )
            )
            sketch_order_photo_counter = data["sketch_order_photo_counter"]
            data["sketch_order_photo_counter"] = message.media_group_id

        if sketch_order_photo_counter != data["sketch_order_photo_counter"]:
            async with state.proxy() as data:
                sketch_order_photo_counter = data["sketch_order_photo_counter"]

            await bot.send_message(
                message.from_id,
                "📷 Отлично, вы выбрали фотографию эскиза для своего тату!",
            )
            await bot.send_message(
                message.from_id,
                "❔ Хотите добавить еще фото/картинку?",
                reply_markup=kb_client.kb_yes_no,
            )

    if message.content_type == "text":
        if message.text == kb_client.yes_str:
            async with state.proxy() as data:
                data["sketch_order_photo_counter"] = 0

            await bot.send_message(
                message.from_id,
                "📎 Добавьте еще фотографию через файлы.",
                reply_markup=kb_client.kb_back_cancel,
            )

        elif message.text == kb_client.no_str:
            async with state.proxy() as data:
                sketch_photo = data["sketch_photo"]
                sketch_order_number = data["sketch_order_number"]

            with Session(engine) as session:
                order = session.scalars(
                    select(Orders).where(Orders.order_number == sketch_order_number)
                ).one()
                for photo in sketch_photo:
                    order.order_photo.append(photo)
                    session.commit()

            await state.finish()
            await bot.send_message(
                message.from_id,
                f"🎉 Отлично, в заказе {sketch_order_number} появилась новая фотография!\n\n"
                f"{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}",
                reply_markup=kb_client.kb_client_choice_order_view,
            )

        elif any(
            text in message.text.lower()
            for text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME
        ):
            await state.finish()
            await bot.send_message(
                message.from_id,
                f"{MSG_CANCEL_ACTION}{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}",
                reply_markup=kb_client.kb_client_choice_order_view,
            )

        elif any(text in message.text.lower() for text in LIST_BACK_COMMANDS):
            await FSM_Client_get_new_photo_to_sketch_order.previous()

            with Session(engine) as session:
                orders = session.scalars(
                    select(Orders)
                    .where(Orders.user_id == message.from_id)
                    .where(Orders.order_state.not_in(list(STATES["closed"].values())))
                    .where(Orders.order_type == "эскиз")
                ).all()

            kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
            for order in orders:
                kb_orders.add(
                    KeyboardButton(
                        f"Эскиз №{order.order_number} от "
                        f"{order.creation_date.strftime('%H:%M %d/%m/%Y')}"
                    )
                )

            kb_orders.add(kb_client.back_lst[0]).add(kb_client.cancel_lst[0])

            await bot.send_message(
                message.from_id,
                "❔ Для какого заказа добавить фотографию?",
                reply_markup=kb_orders,
            )
        else:
            await bot.send_message(
                message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
            )


# -------------------------------------------SKETCH_TATTOO_ORDER----------------------------------
def register_handlers_client_sketch(dp: Dispatcher):
    dp.register_message_handler(
        start_create_new_tattoo_sketch_order,
        Text(
            equals=kb_client.client_main["client_want_tattoo_sketch"], ignore_case=True
        ),
        state=None,
    )
    dp.register_message_handler(
        start_create_new_tattoo_sketch_order, commands=["get_sketch_tattoo"], state=None
    )
    dp.register_message_handler(
        get_sketch_desc_order, state=FSM_Client_tattoo_sketch_order.tattoo_sketch_note
    )
    dp.register_message_handler(
        get_photo_sketch_order,
        content_types=["photo", "text"],
        state=FSM_Client_tattoo_sketch_order.load_sketch_photo,
    )

    dp.register_message_handler(
        get_clients_tattoo_sketch_order,
        Text(
            equals=kb_client.choice_order_view["client_watch_sketch_order"],
            ignore_case=True,
        ),
        state=None,
    )
    dp.register_message_handler(
        get_sketch_order_number,
        state=FSM_Client_send_to_client_view_sketch_order.get_order_number,
    )

    dp.register_message_handler(
        command_client_add_new_photo_to_sketch_order,
        Text(
            equals=kb_client.choice_order_view["client_add_photo_to_sketch_order"],
            ignore_case=True,
        ),
        state=None,
    )
    dp.register_message_handler(
        get_order_id_to_add_new_photo_to_sketch_order,
        state=FSM_Client_get_new_photo_to_sketch_order.get_order_id,
    )
    dp.register_message_handler(
        get_photo_to_sketch_order,
        content_types=["photo", "text"],
        state=FSM_Client_get_new_photo_to_sketch_order.get_new_photo,
    )
