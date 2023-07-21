from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import (
    generate_random_order_number,
    CODE_LENTH,
    ORDER_CODE_LENTH,
    ADMIN_NAMES,
    CALENDAR_ID,
)

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

from validate import check_pdf_document_payment, check_photo_payment

# from diffusers import StableDiffusionPipeline
# import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# from datetime import datetime
import datetime
from aiogram.types.message import ContentType
from aiogram_calendar import simple_cal_callback, dialog_cal_callback, DialogCalendar
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback
from aiogram_timepicker import result, carousel, clock

from handlers.calendar_client import obj
from msg.main_msg import *
import re
from handlers.other import *
from prettytable import PrettyTable


#TODO закончить добавление нового тату заказа и изменение тату заказа для админа

# ----------------------------------- TATTOO ORDER COMMANDS LIST-----------------------------------
async def get_tattoo_order_and_item_command_list(message: types.Message):
    if (
        message.text in [kb_admin.order_commands['tattoo'], "/тату_заказы"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            MSG_WHICH_COMMAND_TO_EXECUTE,
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )


# ------------------------------------- TATTOO ORDER COMMANDS-----------------------------------
async def send_to_view_tattoo_order(
    message: types.Message, tattoo_orders: ScalarResult["Orders"]
):
    if tattoo_orders == []:
        await bot.send_message(
            message.from_id,
            MSG_NO_ORDER_IN_TABLE,
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
    else:
        for order in tattoo_orders:
            with Session(engine) as session:
                user = session.scalars(
                    select(User).where(User.name == order.username)
                ).all()

            if user != []:
                for item in user:
                    username_telegram = (
                        "Без телеграма"
                        if item.telegram_name in ["", None]
                        else item.telegram_name
                    )
                    username_phone = (
                        "Без номера" if item.phone in ["", None] else item.phone
                    )
            else:
                username_telegram = "Без телеграма"
                username_phone = "Без номера"

            msg = f"Тату заказ № {order.order_number} от {order.creation_date}\n"

            msg += (
                f"🪴 Тип тату: {order.order_type}\n"
                f"🍃 Имя: {order.order_name}\n"
                f"📏 Размер: {order.tattoo_size}\n"
                f"📜 Описание тату: {order.tattoo_note}\n"
                f"💬 Описание заказа: {order.order_note}\n"
                f"🎨 {order.colored} тату\n"
                f"👤 Местоположение тату: {order.bodyplace}\n"
                f"- Цена заказа: {order.price}\n"
                f"- Имя пользователя: {order.username}\n"
                f"- Telegram пользователя: {username_telegram}\n"
                f"- Телефон пользователя: {username_phone}\n"
            )
            if order.order_type == "постоянное тату":
                i = 0
                schedule_lst = session.scalars(
                    select(ScheduleCalendarItems).where(
                        ScheduleCalendarItems.order_number == order.order_number
                    )
                ).all()
                if schedule_lst not in [None, []]:
                    # msg += "🕒 Даты встреч:\n"
                    for schedule in schedule_lst:
                        i += 1
                        start_time = session.get(
                            ScheduleCalendar, schedule.schedule_id
                        ).start_datetime.strftime("%d/%m/%Y с %H:%M")
                        
                        end_time = session.get(
                            ScheduleCalendar, schedule.schedule_id
                        ).end_datetime.strftime("%H:%M")

                        msg += f"\t{i}) {start_time} до {end_time}\n"
                else:
                    msg += (f"🕒 Дата и время встречи не выбраны - "
                        "свободных ячеек в календаре нет.\n")
                    
            if order.order_state in list(STATES["closed"].values()):
                msg += f"❌ Состояние заказа: {order.order_state}\n"
            else:
                msg += f"📃 Состояние заказа: {order.order_state}\n"
                
            tattoo_photos = session.scalars(select(OrderPhoto)
                .where(OrderPhoto.order_id == order.id)).all()
            body_photos = session.scalars(select(TattooPlacePhoto)
                .where(TattooPlacePhoto.order_id == order.id)).all()
            
            media = []
            for photo in tattoo_photos + body_photos:
                media.append(types.InputMediaPhoto(photo.photo))

            await bot.send_media_group(message.from_user.id, media=media)
            
            with Session(engine) as session:
                check_document = session.scalars(
                    select(CheckDocument).where(CheckDocument.id == order.order_number)
                ).all()
            if check_document not in [[], None]:
                print(order.check_document)  # TODO сделать вывод чеков
                for doc in check_document:
                    if doc is not None and doc.doc is not None:
                        try:
                            await bot.send_document(
                                message.from_user.id, doc.doc, "Чек на оплату заказа"
                            )
                        except:
                            await bot.send_photo(
                                message.from_user.id, doc.doc, "Чек на оплату заказа"
                            )
                    else:
                        msg += "❌ Чек не добавлен"
            else:
                msg += "❌ Чек не добавлен"
            await bot.send_message(message.from_id, msg)


async def send_to_view_tattoo_order_in_table(message: types.Message, tattoo_orders: ScalarResult["Orders"]):
    if tattoo_orders == []:
        await bot.send_message(
            message.from_id,
            MSG_NO_ORDER_IN_TABLE,
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
    else:
        headers = [
            "№",
            "Тип",
            "Имя",
            "Размер",
            #"📜 Описание тату: {order.tattoo_note}\n"
            #"💬 Описание заказа: {order.order_note}\n"
            "Цвет",
            "Местоположение",
            "Цена",
            "Клиент",
            "Статус",
            "Сеансы"
        ]
        table = PrettyTable(
            headers, left_padding_width=1, right_padding_width=1
        )  # Определяем таблицу
        for order in tattoo_orders:
            with Session(engine) as session:
                schedule_lst = session.scalars(
                    select(ScheduleCalendarItems).where(
                        ScheduleCalendarItems.order_number == order.order_number
                    )
                ).all()
                
            if order.order_type == kb_admin.price_lst_types["constant_tattoo"]:
                i = 0
                sessions = ''
                if schedule_lst not in [None, []]:
                    # sessions += "🕒 Даты встреч:\n"
                    for schedule in schedule_lst:
                        i += 1
                        start_time = session.get(
                            ScheduleCalendar, schedule.schedule_id
                        ).start_datetime.strftime("%d/%m/%Y\n%H:%M")
                        
                        end_time = session.get(
                            ScheduleCalendar, schedule.schedule_id
                        ).end_datetime.strftime("%H:%M")

                        sessions += f"{i}) {start_time} - {end_time}\n"
                else:
                    sessions = (f"---")

            table.add_row(
                [
                    order.order_number,
                    order.order_type.split()[0],
                    order.order_name,
                    order.tattoo_size,
                    order.colored,
                    order.bodyplace[:-2],
                    order.price,
                    order.username,
                    order.order_state,
                    sessions
                ]
            )
        await bot.send_message(
            message.from_id, f"<pre>{table}</pre>", parse_mode=types.ParseMode.HTML
        )


# ------------------------------------------ посмотреть_тату_заказы--------------------------------
class FSM_Admin_get_info_orders(StatesGroup):
    order_status_name = State()
    get_view_type = State()


# /посмотреть_тату_заказы
async def command_get_info_tattoo_orders(message: types.Message):
    # print("ищем заказы в таблице tattoo_orders")
    if (
        message.text in ["посмотреть тату заказы", "/посмотреть_тату_заказы"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders)
                    .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"],
                        kb_admin.price_lst_types["shifting_tattoo"]]))
                ).all()
            
        if orders == []:
            await bot.send_message(
                message.from_id,
                MSG_NO_ORDER_IN_TABLE,
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
        else:
            await FSM_Admin_get_info_orders.order_status_name.set()
            await bot.send_message(
                message.from_user.id,
                MSG_WHITH_ORDER_STATE_ADMIN_WANT_TO_SEE,
                reply_markup=kb_admin.kb_order_statuses,
            )


async def get_status_name(message: types.Message, state: FSMContext):
    if message.text in statuses_order_lst:
        async with state.proxy() as data:
            data['order_state'] = message.text
        await FSM_Admin_get_info_orders.next()
        await bot.send_message(
            message.from_user.id,
            MSG_HOW_TO_VIEW_THE_DATA,
            reply_markup=kb_admin.kb_type_to_view_data,
        )
    elif message.text in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await bot.send_message(
            message.from_user.id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()

    else:
        await message.reply(MSG_NO_CORRECT_INFO_TO_SEND)


async def get_view_type(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        order_state = data['order_state']
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
                .where(Orders.order_state == order_state)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"],
                    kb_admin.price_lst_types["shifting_tattoo"]]))
        ).all()
            
    if message.text == kb_admin.type_to_view_data['table']:
        await send_to_view_tattoo_order_in_table(message, orders)
        await bot.send_message(
            message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE, reply_markup= kb_admin.kb_tattoo_order_commands
        )
        await state.finish()
        
    elif message.text == kb_admin.type_to_view_data['line']:
        await send_to_view_tattoo_order(message, orders)
        await bot.send_message(
            message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE, reply_markup= kb_admin.kb_tattoo_order_commands
        )
        await state.finish()

    elif message.text in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await bot.send_message(
            message.from_user.id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()

    else:
        await message.reply(MSG_NO_CORRECT_INFO_TO_SEND)


# ------------------------------------- посмотреть_тату_заказ------------------------------
"""
    Открыт — заказ был создан в базе данных, но ещё не был обработан.
    Обработан — оплата была получена.
    Выполнен — вся работа по заказу завершена.
    Отклонен — заказ отклонен админом.
    Отложен — заказ ещё не обработан, так как в нём содержатся товары, которых нет в наличии. 
        Только для гифтбокса
    Аннулирован — заказ был отменён покупателем.
"""


class FSM_Admin_command_get_info_tattoo_order(StatesGroup):
    order_name = State()


# /посмотреть_тату_заказ
async def command_get_info_tattoo_order(message: types.Message):
    if (
        message.text in ["посмотреть тату заказ", "/посмотреть_тату_заказ"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders).where(
                    Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"],
                        kb_admin.price_lst_types["shifting_tattoo"]])
                )
            ).all()

        if orders == []:
            await message.reply(MSG_NO_ORDER_IN_TABLE)
        else:
            kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
            await FSM_Admin_command_get_info_tattoo_order.order_name.set()
            for order in orders:
                kb_orders.add(
                    KeyboardButton(
                        f"{order.order_number} "
                        f'"{order.order_name}" статус: {order.order_state}'
                    )
                )

            kb_orders.add(kb_admin.home_btn)
            await bot.send_message(
                message.from_user.id,
                MSG_WHICH_ADMIN_ORDER_WANT_TO_SEE,
                reply_markup=kb_orders,
            )


async def get_name_for_view_tattoo_order(message: types.Message, state: FSMContext):
    if message.text not in LIST_BACK_COMMANDS:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == message.text.split()[0])
            ).all()

        await send_to_view_tattoo_order(message, order)
        await bot.send_message(
            message.from_user.id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()

    elif message.text in LIST_BACK_COMMANDS:
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )
        await state.finish()
    else:
        await message.reply('Пожалуйста, выбери заказ из списка или нажми "Назад"')


# ------------------------------------------- удалить_тату_заказ--------------------------------
class FSM_Admin_delete_tattoo_order(StatesGroup):
    tattoo_order_number = State()


# /удалить_тату_заказ
async def command_delete_info_tattoo_orders(message: types.Message):
    if (
        message.text in ["удалить тату заказ", "/удалить_тату_заказ"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            "❕❕❕ Данная функция полностью удаляет заказ из таблицы.\n\n"
            f"❕ Если необходимо перевести заказы в статусы {', '.join(list(STATES['closed'].values()))}, "
            'то необходимо использовать кнопку "Изменить статус тату заказа"'
        )
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders).where(
                    Orders.order_type.in_([
                        kb_admin.price_lst_types['constant_tattoo'], 
                        kb_admin.price_lst_types['shifting_tattoo']
                    ])
                )
            ).all()
        if orders == []:
            await message.reply(
                MSG_NO_ORDER_IN_TABLE,
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
        else:
            kb_tattoo_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
            for order in orders:
                # выводим наименования тату
                kb_tattoo_order_numbers.add(
                    KeyboardButton(
                        f'{order.order_number} "{order.order_name}" {order.order_state}'
                    )
                )
            kb_tattoo_order_numbers.add(kb_admin.home_btn)
            await FSM_Admin_delete_tattoo_order.tattoo_order_number.set()
            await message.reply(
                "❔ Какой заказ хотите удалить?", reply_markup=kb_tattoo_order_numbers
            )


async def delete_info_tattoo_orders(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders).where(
                Orders.order_type.in_([
                    kb_admin.price_lst_types["constant_tattoo"],
                    kb_admin.price_lst_types["shifting_tattoo"]])
                )
        ).all()
    choosen_kb_order_lst = []
    for order in orders:
        choosen_kb_order_lst.append(
            f'{order.order_number} "{order.order_name}" {order.order_state}'
        )

    if message.text in choosen_kb_order_lst:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == message.text.split()[0])
            ).one()
            schedule_event = session.scalars(
                select(ScheduleCalendar).where(ScheduleCalendar.id == order.schedule_id)
            ).one()
            session.delete(order)
            schedule_event.status = kb_admin.schedule_event_status['free']
            session.commit()

        # service.events().delete(calendarId='primary', eventId='eventId').execute()
        """ 
        print("---------------------------------")
        print(await obj.get_calendar_events(CALENDAR_ID))
        print("---------------------------------") 
        """
        event_list = await obj.get_calendar_events(CALENDAR_ID)
        # TODO нужно удалять ивент из Google Calendar
        for event in event_list:
            if event["summary"].split()[4] == message.text.split()[0]:
                await obj.delete_event(CALENDAR_ID, event["id"])

        await message.reply(
            f"Заказ удален. {MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()
    else:
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )
        await state.finish()


# ----------------------------- изменить_статус_тату_заказа--------------------------------
class FSM_Admin_tattoo_order_change_status(StatesGroup):
    tattoo_order_number = State()
    tattoo_order_new_status = State()
    get_answer_for_getting_check_document = State()
    get_price_for_check_document = State()
    get_check_document = State()


# /изменить_статус_тату_заказа, изменить статус тату заказа
async def command_tattoo_order_change_status(message: types.Message):
    if (
        message.text in ["изменить статус тату заказа", "/изменить_статус_тату_заказа"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"],
                    kb_admin.price_lst_types["shifting_tattoo"]]))
                .where(Orders.user_id == message.from_id)
            ).all()
        kb_tattoo_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
        if orders == []:
            await message.reply(f"{MSG_NO_ORDER_IN_TABLE}")
        else:
            for order in orders:  # выводим номера тату заказов и их статус
                kb_tattoo_order_numbers.add(
                    KeyboardButton(
                        f'{order.order_number} "{order.order_name}" статус: {order.order_state}'
                    )
                )
            kb_tattoo_order_numbers.add(kb_admin.home_btn)
            await FSM_Admin_tattoo_order_change_status.tattoo_order_number.set() #->get_new_status_for_tattoo_order
            await message.reply(
                MSG_WHICH_ADMIN_ORDER_WANT_TO_CHANGE,
                reply_markup=kb_tattoo_order_numbers,
            )
    # await message.delete()


async def get_new_status_for_tattoo_order(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"],
                kb_admin.price_lst_types["shifting_tattoo"]]))
            .where(Orders.user_id == message.from_id)
        ).all()
    tattoo_order_numbers_lst = []
    for order in orders:
        tattoo_order_numbers_lst.append(
            f'{order.order_number} "{order.order_name}" статус: {order.order_state}'
        )
    if message.text in tattoo_order_numbers_lst:
        async with state.proxy() as data:
            data["order_number"] = message.text.split()[0]
            data['current_order_status'] = message.text.split()[3]
        await FSM_Admin_tattoo_order_change_status.next() #->complete_new_status_for_tattoo_order

        await bot.send_message(message.from_id, MSG_SEND_ORDER_STATE_INFO)
        
        kb_new_status = ReplyKeyboardMarkup(resize_keyboard=True)
        for status in status_distribution[kb_admin.price_lst_types["constant_tattoo"]][message.text.split()[3]]\
            + list(STATES['closed'].values()):
                
            kb_new_status.add(KeyboardButton(status))
        kb_new_status.add(kb_client.cancel_btn)
        await bot.send_message(
            message.from_id, f"Какой статус выставляем?", reply_markup=kb_new_status,
        )

    elif message.text in LIST_BACK_TO_HOME + LIST_BACK_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def complete_new_status_for_tattoo_order(
    message: types.Message, state: FSMContext
):
    '''   
        Список действий:
        0 - не меняется 
        1 - отсылаем сообщение пользователю о действии
        2 - просим добавить чек, если его нет
        3 - подтверждаем оплату
        4 - подтверждаем дату заказа (если есть)
        
            ------------------------------------------
            Был         Стал         Действие
            "Открыт": "Открыт"          0
            "Открыт"  "Обработан"       1, 2
            "Открыт": "Отклонен"        1
            "Открыт": "Отложен"         1
            "Открыт": "Аннулирован"     1
            ------------------------------------------
            Обработан   Открыт          1
            Обработан   Обработан       0
            Обработан   Оплачен         1
            Обработан   Отклонен
            Обработан   Отложен
            Обработан   Аннулирован
            ------------------------------------------
            Оплачен   Открыт          1
            Оплачен   Обработан       0
            Оплачен   Оплачен         1
            Оплачен   Выполняется
            Оплачен   Выполнен
            Оплачен   Отклонен
            Оплачен   Отложен
            Оплачен   Аннулирован
    '''
    async with state.proxy() as data:
        current_order_status = data['current_order_status'] # определяем предыдущий статус заказа
        order_number = data["order_number"] # определяем номер заказа
    
    with Session(engine) as session: # определяем заказ
        order = session.scalars(
            select(Orders).where(Orders.order_number == order_number)
        ).one()
        username = order.username # определяем имя клиента заказа
        user_id = order.user_id # определяем тг id клиента заказа
    
    if message.text in status_distribution[kb_admin.price_lst_types["constant_tattoo"]][current_order_status]:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == order_number)
            ).one()
            order.order_state = message.text
            schedule_id = order.schedule_id
            session.commit()

        async with state.proxy() as data:
            data["new_state"] = message.text 
            
        if message.text in list(STATES["closed"].values()):
            schedule_id_lst = []
            if schedule_id != []: # если есть сеанс по данному заказу и мы переводим его в закрытые статусы
                for id in order.schedule_id:
                    schedule_id_lst.append(id)
                
                """
                    Если есть сеанс в статусе Занят, но не Свободен или Закрытый, 
                    то переводим в статус Свободен
                    
                    Такой сеанс может быть только один. 
                    Остальные сеансы по заказу могут быть только в статусе Закрытый
                    
                    Перевод в статус Закрытый должен быть автоматический по достижению
                    окончания времени сеанса
                """
                with Session(engine) as session:
                    schedule_busy_event = session.scalars(select(ScheduleCalendar)
                        .where(ScheduleCalendar.id.in_(schedule_id_lst))
                        .where(ScheduleCalendar.status== kb_admin.schedule_event_status['busy'])
                    ).all()
                    
                    if schedule_busy_event !=[]:
                        schedule_busy_event[0].status = kb_admin.schedule_event_status['free']
                        session.commit()
                
            await message.reply(MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT_ABOUT_CHANGING_ORDER_STATE, 
                reply_markup=kb_client.kb_yes_no)
            
            """  elif message.text in [STATES['paid']]: # оплачен
            await FSM_Admin_tattoo_order_change_status.next() # -> get_answer_for_getting_check_document
            await message.reply(MSG_GET_CHECK, reply_markup=kb_client.kb_yes_no) """
            
        elif message.text in [STATES['paid'], STATES["processed"], STATES['open'], STATES['in_work']]:
            await message.reply(MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT_ABOUT_CHANGING_ORDER_STATE, 
                reply_markup=kb_client.kb_yes_no)
            
    elif message.text == kb_client.yes_str:
        async with state.proxy() as data:
            new_state = data["new_state"]
        await bot.send_message(user_id, 
            (
                f"❕ Уважаемый {username}!\n"
                f"❕ Статус тату заказа {order_number} изменился с {current_order_status} на {new_state}.\n\n"
                f"За подробностями об изменении статуса заказа обращайтесь к "
                "@dara_redwan (https://t.me/dara_redwan)"
            )
        )
        
        await bot.send_message(
            message.from_id,
            f'❕ Готово! Вы обновили статус заказа {order_number} на "{new_state}"'
        )
        
        if new_state == STATES['paid']:
            await FSM_Admin_tattoo_order_change_status.next() # -> get_answer_for_getting_check_document
            await message.reply(MSG_GET_CHECK, reply_markup=kb_client.kb_yes_no)
            
        else:
            await bot.send_message(
                message.from_id,
                MSG_DO_CLIENT_WANT_TO_DO_MORE, 
                reply_markup= kb_admin.kb_tattoo_order_commands
            )
            await state.finish() # полностью очищает данные
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            new_state = data["new_state"]
            
        await bot.send_message(
            message.from_id,
            f'❕ Готово! Вы обновили статус заказа {order_number} на "{new_state}"',
        )
        
        if new_state == STATES['paid']:
            await FSM_Admin_tattoo_order_change_status.next() # -> get_answer_for_getting_check_document
            await message.reply(MSG_GET_CHECK, reply_markup=kb_client.kb_yes_no)
            
        else:
            await bot.send_message(
                message.from_id,
                MSG_DO_CLIENT_WANT_TO_DO_MORE, 
                reply_markup= kb_admin.kb_tattoo_order_commands
            )
            await state.finish() # полностью очищает данные
        
    elif message.text in LIST_BACK_TO_HOME + LIST_BACK_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_answer_for_getting_check_document(
    message: types.Message, state: FSMContext
):
    if message.text == kb_client.yes_str:
        await FSM_Admin_tattoo_order_change_status.next() #-> get_price_for_check_document
        await message.reply(
            f"На какую сумму чек?", reply_markup=kb_admin.kb_price
        )

    elif message.text == kb_client.no_str:

        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE, 
            reply_markup= kb_admin.kb_tattoo_order_commands
        )
        await state.finish()
        
    else:
        await message.reply(
            f"На этот вопрос можно ответит только 'Да' или 'Нет'. Выбери правильный ответ",
            reply_markup=kb_client.kb_yes_no,
        )


# Возможность добавления цены через ввод, а не кб
async def process_callback_set_price_from_line(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 
        MSG_ADMIN_SET_ANOTHER_PRICE_FROM_LINE, reply_markup= kb_client.kb_cancel
    )


async def get_price_for_check_document(message: types.Message, state: FSMContext):
    if message.text in kb_admin.another_price_lst:
        await bot.send_message(
            message.from_id,
            MSG_ADMIN_SET_ANOTHER_PRICE,
            reply_markup=kb_admin.kb_another_price_full,
        )
        await bot.send_message(
            message.from_id, 
            MSG_ADMIN_CAN_SET_ANOTHER_PRICE,
            reply_markup= kb_admin.kb_set_another_price_from_line
        )

    elif message.text.isdigit():
        async with state.proxy() as data:
            data["tattoo_order_price"] = message.text
        await FSM_Admin_tattoo_order_change_status.next() # -> get_check_document
        await message.reply(
            MSG_ADMIN_GET_CHECK_TO_ORDER,
            reply_markup=kb_client.kb_back_cancel,
        )

    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_check_document(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        order_number = data["order_number"]
        price = str(data["tattoo_order_price"])

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
                        doc= message.document.file_id,
                    )
                if order.check_document in [[], None]:
                    order.check_document = [new_check_item]
                else:
                    order.check_document.append(new_check_item)
                session.commit()
            
            await state.finish()
            await bot.send_message(message.from_id, MSG_SUCCESS_CHANGING)
            await bot.send_message(
                message.from_id,
                f"🌿 Чек подошел! Заказ № {order_number} обрел свой чек!\n\n"
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
        else:
            await message.reply(f"❌ Чек не подошел! {check_doc_pdf['report_msg']}")

    if message.content_type == "text":
        if message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(
                MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
            )

        elif message.text in LIST_BACK_COMMANDS:
            await FSM_Admin_tattoo_order_change_status.previous() #-> get_price_for_check_document
            await message.reply(
                f"{MSG_CLIENT_GO_BACK}❔ На какую сумму чек?",
                reply_markup=kb_admin.kb_price,
            )

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
                            doc= message.photo[0].file_id,
                        )
                    order.check_document = [new_check_item]
                else:
                    order.check_document.append(new_check_item)
                session.commit()
            await bot.send_message(message.from_id, MSG_SUCCESS_CHANGING)
            await state.finish()
            await bot.send_message(
                message.from_id,
                f"Чек подошел! Заказ № {order_number} обрел свой чек! "
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
        else:
            await message.reply(f"❌ Чек не подошел! {check_photo['report_msg']}")  # type: ignore


# ------------------------------------CHANGE TATTOO ORDER-----------------------------------
class FSM_Admin_change_tattoo_order(StatesGroup):
    tattoo_order_number = State()
    tattoo_new_state = State()
    day_by_date = State()
    new_start_time_session = State()
    new_end_time_session = State()
    new_photo = State()


# /изменить_тату_заказ
async def command_command_change_info_tattoo_order(message: types.Message):
    if (
        message.text in ["изменить тату заказ", "/изменить_тату_заказ"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):  
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders).where(
                    Orders.order_type.in_(
                        [
                            kb_admin.price_lst_types["constant_tattoo"],
                            kb_admin.price_lst_types["shifting_tattoo"]
                        ]
                    )
                )
            ).all()
        kb_tattoo_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
        if orders == []:
            await message.reply(f"{MSG_NO_ORDER_IN_TABLE}")

        else:
            for order in orders:  # выводим номера тату заказов и их статус
                kb_tattoo_order_numbers.add(
                    KeyboardButton(f"{order.order_number} статус: {order.order_state}")
                )
            kb_tattoo_order_numbers.add(
                KeyboardButton(kb_admin.admin_view_orders['watch'])
            ).add(kb_admin.home_btn)
            await FSM_Admin_change_tattoo_order.tattoo_order_number.set()
            await message.reply(
                "У какого заказа хочешь поменять какую-либо информацию?",
                reply_markup=kb_tattoo_order_numbers,
            )


# -------------------------------------get_tattoo_order_number-----------------------------------
async def get_tattoo_order_number(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders).where(
                Orders.order_type.in_([
                            kb_admin.price_lst_types["constant_tattoo"],
                            kb_admin.price_lst_types["shifting_tattoo"]
                        ]
                    )
                )
            ).all()
    tattoo_lst, tattoo_order_numbers = [], []
    kb_tattoo_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
    kb_tattoo_order_numbers_with_status = ReplyKeyboardMarkup(resize_keyboard=True)

    for order in orders:
        msg_item = f"{order.order_number} статус: {order.order_state}"
        tattoo_lst.append(msg_item)
        tattoo_order_numbers.append(order.order_number)
        kb_tattoo_order_numbers.add(KeyboardButton(order.order_number))  # type: ignore
        kb_tattoo_order_numbers_with_status.add(KeyboardButton(msg_item))

    kb_tattoo_order_numbers.add(kb_client.cancel_btn)
    kb_tattoo_order_numbers_with_status.add(kb_client.cancel_btn)
    async with state.proxy() as data:
        data["menu_new_username"] = False
        data["menu_new_telegram"] = False
        data["menu_new_tattoo_name"] = False
        data["menu_new_order_note"] = False
        data["menu_new_tattoo_note"] = False
        data["menu_new_price"] = False
        data["orders"] = orders
        data['create_new_schedule_event'] = False
        data["user_id"] = message.from_id

    if message.text in [
        kb_admin.admin_view_orders['watch'],
        kb_admin.admin_choice_watch_order_or_change_order["watch"],
    ]:
        await bot.send_message(
            message.from_id,
            MSG_WHICH_ADMIN_ORDER_WANT_TO_SEE,
            reply_markup=kb_tattoo_order_numbers,
        )

    elif (message.text == kb_admin.admin_choice_watch_order_or_change_order["change"]):
        
        await message.reply(
            "❔ У какого заказа хочешь поменять какую-либо информацию?",
            reply_markup=kb_tattoo_order_numbers_with_status,
        )

    elif message.text in tattoo_order_numbers:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == message.text)
            ).all()
        async with state.proxy() as data:
            data["order"] = order[0]

        await send_to_view_tattoo_order(message, order)

        await bot.send_message(
            message.from_id,
            "❔ Посмотреть еще заказ или уже изменить что-то в заказе?",
            #  'Хочу еще посмотреть заказы','Хочу изменить информацию в заказе'
            reply_markup=kb_admin.kb_admin_choice_watch_order_or_change_order,
        )

    elif message.text in tattoo_lst:
        async with state.proxy() as data:
            data["order_number"] = message.text.split()[0]
            with Session(engine) as session:
                order = session.scalars(
                        select(Orders)
                            .where(Orders.order_number == message.text.split()[0])
                    ).one()
            data['order'] = order
            data["telegram"] = message.from_id
            data['current_order_status'] = order.order_state

        await FSM_Admin_change_tattoo_order.next() #-> get_new_state_info
        await bot.send_message(
            message.from_id,
            MSG_WHICH_ORDER_COLUMN_NAME_WILL_CHANGING,
            reply_markup=kb_admin.kb_tattoo_order_columns_to_change_lst,
        )

    elif message.text in LIST_BACK_COMMANDS:
        await message.reply(
            "❔ Какой заказ хотите дополнить или изменить?",
            reply_markup=kb_tattoo_order_numbers,
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# ---------------------------------------get_new_state_info-----------------------------------
async def get_to_view_schedule(
    message: types.Message, state: FSMContext, schedule: list
):
    kb_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
    if schedule == []:
        await bot.send_message(message.from_id, "⭕️ В календаре нет свободных дат")
        # TODO сделать функцию "создать новый ивент в календаре"
        await bot.send_message(
            message.from_id, 
            "Необходимо создать новый свободный сеанс в календаре\n"
            "Выбери новую дату для календаря",
            reply_markup=await DialogCalendar().start_calendar()
        )
        async with state.proxy() as data:
            data['create_new_schedule_event'] = True
        
        await FSM_Admin_change_tattoo_order.next() #-> get_day_by_date_for_schedule
        
    else:
        kb_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
        today = int(datetime.strftime(datetime.now(), "%m %Y"))
        with Session(engine) as session:
            schedule_photo = session.scalars(
                select(SchedulePhoto).where(SchedulePhoto.name == today)
            ).one()

        date_list_full_for_msg = ""
        for date in schedule:
            date_list_full_for_msg += date + "\n"
            kb_schedule.add(KeyboardButton(date))

        # .add(KeyboardButton('Хочу выбрать свою дату'))
        kb_schedule.add(kb_client.back_btn).add(kb_client.cancel_btn)

        # выдаем на экран свободное фото расписания, или просто сообщение, если фото нет
        if schedule_photo == []:
            await bot.send_message(
                message.from_user.id,
                f"{MSG_MY_FREE_CALENDAR_DATES}" f"{date_list_full_for_msg}",
            )
        else:
            await bot.send_photo(
                message.from_user.id,
                schedule_photo.photo,
                f"{MSG_MY_FREE_CALENDAR_DATES}" f"{date_list_full_for_msg}",
            )

    kb_schedule.add(kb_admin.home_btn)
    await bot.send_message(
        message.from_id, "Укажи новую дату встречи", reply_markup=kb_schedule
    )


# Возможность добавления цены через ввод, а не кб
async def process_callback_set_price_from_line(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 
        MSG_ADMIN_SET_ANOTHER_PRICE_FROM_LINE, reply_markup= kb_client.kb_cancel
    )


async def get_new_state_info(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        schedule = session.scalars(
            select(ScheduleCalendar)
            .order_by(ScheduleCalendar.start_datetime)
            .where(ScheduleCalendar.start_datetime > datetime.now())
            .where(ScheduleCalendar.status == kb_admin.schedule_event_status['free'])
            .where(ScheduleCalendar.event_type == kb_admin.price_lst_types['constant_tattoo'])
        ).all()
    kb_schedule_event_lst = []
    for date in schedule:
        month_name = await get_month_from_number(
            int(date.start_datetime.strftime("%m")), lang="ru"
        )
        item_in_kb = f"{month_name} {date.start_datetime.strftime('%d/%m/%Y с %H:%M')}"\
            f" по {date.end_datetime.strftime('%H:%M')} 🗓"
        kb_schedule_event_lst.append(item_in_kb)

    async with state.proxy() as data:
        data["date_free_list"] = schedule
        order_number = data["order_number"]
        order = data["order"]
        
    if message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )
        
    elif message.text in list(kb_admin.tattoo_order_columns_to_change_lst.keys()):
        # меняем фотографии тела/тату

        if message.text in list(kb_admin.tattoo_order_change_photo.keys()):
            async with state.proxy() as data:
                data["photo_type"] = message.text
            for i in range(3):
                await FSM_Admin_change_tattoo_order.next()  # -> get_new_photo
            
            await bot.send_message(
                message.from_id,
                MSG_CLIENT_LOAD_PHOTO,
                reply_markup= kb_client.kb_back_cancel
            )

        elif message.text == "Цвет тату":
            await bot.send_message(
                message.from_id,
                MSG_WHICH_COLOR_WILL_BE_TATTOO,
                reply_markup=kb_client.kb_colored_tattoo_choice,
            )

        elif message.text == "Дату и время сеанса":
            await get_to_view_schedule(message, state, kb_schedule_event_lst)

        elif message.text == "Описание тату":
            async with state.proxy() as data:
                data["menu_new_tattoo_note"] = True

            await bot.send_message(
                message.from_id,
                "Укажи новое описание тату",
                reply_markup=kb_client.kb_cancel,
            )

        elif message.text == "Описание заказа":
            async with state.proxy() as data:
                data["menu_new_order_note"] = True

            await bot.send_message(
                message.from_id,
                "Укажи новое описание заказа",
                reply_markup=kb_client.kb_cancel,
            )

        elif message.text == "Время встречи":
            await FSM_Admin_change_tattoo_order.next()  # -> process_hour_timepicker_start_session
            await bot.send_message(
                message.from_id,
                "Укажи новое время встречи",
                reply_markup=await FullTimePicker().start_picker(),
            )

        elif message.text == "Имя тату":
            async with state.proxy() as data:
                data["menu_new_tattoo_name"] = True

            await bot.send_message(
                message.from_id,
                "Укажи новое имя тату",
                reply_markup=kb_client.kb_cancel,
            )
        elif message.text == "Статус":
            async with state.proxy() as data:
                order_number = data['order_number']
                current_order_status = data['current_order_status']
                
            await state.finish()
            await FSM_Admin_tattoo_order_change_status.tattoo_order_new_status.set()
            
            async with state.proxy() as data:
                data['order_number'] = order_number
                data['current_order_status'] = current_order_status
                
            kb_new_status = ReplyKeyboardMarkup(resize_keyboard=True)
            for status in status_distribution[
                kb_admin.price_lst_types["constant_tattoo"]][current_order_status] \
                + list(STATES['closed'].values()):
                    
                kb_new_status.add(KeyboardButton(status))
            kb_new_status.add(kb_client.cancel_btn)
            
            await bot.send_message(
                message.from_id, f"Какой статус выставляем?", reply_markup=kb_new_status,
            )
            
        elif message.text == "Имя пользователя":
            
            async with state.proxy() as data:
                data["menu_new_username"] = True

            await bot.send_message(
                message.from_id,
                "Укажи новое имя пользователя",
                reply_markup=kb_client.kb_cancel,
            )

        elif message.text == "Телеграм пользователя":
            async with state.proxy() as data:
                data["menu_new_telegram"] = True
            await bot.send_message(
                message.from_id,
                "Укажи новое Телеграм пользователя",
                reply_markup=kb_client.kb_cancel,
            )

        elif message.text == "Место части тела для тату":
            await bot.send_message(
                message.from_id,
                "Укажи новую часть тела",
                reply_markup=kb_client.kb_place_for_tattoo,
            )

        elif message.text == "Цена":
            async with state.proxy() as data:
                data["menu_new_price"] = True
            await bot.send_message(
                message.from_id,
                "Укажи новую цену",
                reply_markup=kb_admin.kb_price,
            )
            await bot.send_message(
                message.from_id, 
                MSG_ADMIN_CAN_SET_ANOTHER_PRICE,
                reply_markup= kb_admin.kb_set_another_price_from_line
            )
        elif message.text == "Тип тату":  #? TODO А мы вообще меняем тут "тип тату"?
            await bot.send_message(
                message.from_id,
                "Укажи новый тип тату\n\n"
                "❕ При изменении типа тату с переводного на постоянное необходимо добавить "
                "дату и время сеанса.\n\n"
                "❕ При изменении типа тату с постояного на переводное дату сеанса можно удалить, "
                "а ранее занятое время в календаре становится свободным.",
                reply_markup=kb_client.kb_client_choice_main_or_temporary_tattoo,
            )

    elif message.text in kb_admin.another_price_lst:
        await bot.send_message(
            message.from_id,
            MSG_ADMIN_SET_ANOTHER_PRICE,
            reply_markup=kb_admin.kb_another_price_full,
        )
        await bot.send_message(
            message.from_id, 
            MSG_ADMIN_CAN_SET_ANOTHER_PRICE,
            reply_markup= kb_admin.kb_set_another_price_from_line
        )

    elif (
        message.text in kb_admin.price_lst + kb_admin.another_price_full_lst
        or message.text.isdigit()
    ):  # меняем цену
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == order_number)
            ).one()
            order.price = int(message.text)
            session.commit()

        await bot.send_message(
            message.from_id,
            f"Вы поменяли цену на {message.text} \n\n"
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()
    # меняем тип тату на постоянное
    elif message.text == kb_client.choice_main_or_temporary_tattoo["main_tattoo"]:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == order_number)
            ).one()
            order.order_type = message.text[:-2].lower()
            session.commit()

        await bot.send_message(
            message.from_id,
            f"Вы поменяли тип тату на {message.text}! Нужно выставить дату и время встречи",
        )
        await get_to_view_schedule(message, state, kb_schedule_event_lst)

    # меняем тип тату на переводное
    elif message.text == kb_client.choice_main_or_temporary_tattoo["temporary_tattoo"]:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == order_number)
            ).one()
            schedule_item = session.scalars(
                select(ScheduleCalendarItems).where(ScheduleCalendarItems.order_number == order.order_number)
            ).one()
            schedule_calendar =session.scalars(
                select(ScheduleCalendar).where(ScheduleCalendar.id == schedule_item.schedule_id)
            ).one()
            schedule_calendar.status = kb_admin.schedule_event_status['free']
            order.order_type = message.text
            order.schedule_id.remove(schedule_item.id)
            # TODO проверить правильность
            
            session.commit()

        await bot.send_message(
            message.from_id,
            f"Вы поменяли у заказа {order.order_number} тип тату на {message.text}!",
        )

        await bot.send_message(
            message.from_id,
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )

    # меняем часть тела
    elif message.text in kb_client.tattoo_body_places:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == order_number)
            ).one()
            order.bodyplace = message.text
            session.commit()

        await bot.send_message(
            message.from_id,
            f"Вы поменяли цену на {message.text} \n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()

    # меняем цвет
    elif message.text in kb_client.colored_tattoo_choice:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == order_number)
            ).one()
            order.colored = message.text.split()[0].lower()
            session.commit()

        await bot.send_message(
            message.from_id,
            f"Вы поменяли цвет на {message.text} \n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()

    # меняем часть тела
    elif message.text == kb_client.tattoo_body_places[-2]:  # Другое место 🙅‍♂️
        async with state.proxy() as data:
            data["menu_new_another_bodyplace"] = True

        await bot.send_message(
            message.from_id,
            "Укажи местоположение тату на теле",
            reply_markup=kb_client.kb_cancel,
        )
    # elif message.text == kb_client.tattoo_body_places[-1]:

    elif message.text in kb_schedule_event_lst:
        async with state.proxy() as data:
            data["date_meeting"] = message.text.split()[1]
            data["start_date_time"] = message.text.split()[3]
            data["end_date_time"] = message.text.split()[5]

            for event in data["date_free_list"]:
                if (
                    event[3] == message.text.split()[1]
                    and event[1] == message.text.split()[3]
                ):
                    data["schedule_id"] = event[0]

            with Session(engine) as session:
                order = session.scalars(
                    select(Orders).where(Orders.order_number == order_number)
                ).one()
                order.schedule_id.append(data["schedule_id"])
                session.commit()

                schedule_to_change = session.scalars(
                    select(ScheduleCalendar).where(
                        ScheduleCalendar.id == data["schedule_id"]
                    )
                ).one()

                schedule_to_change.status = kb_admin.schedule_event_status['busy']
                session.commit()
        await message.reply(MSG_SUCCESS_CHANGING)
        await bot.send_message(
            message.from_id,
            f"Вы поменяли дату встречи на {message.text} \n\n"
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()

    else:
        async with state.proxy() as data:
            menu_new_username = data["menu_new_username"]
            menu_new_telegram = data["menu_new_telegram"]
            menu_new_tattoo_name = data["menu_new_tattoo_name"]
            menu_new_order_note = data["menu_new_order_note"]
            menu_new_tattoo_note = data["menu_new_tattoo_note"]
            menu_new_price = data["menu_new_price"]
        if menu_new_username:
            with Session(engine) as session:
                order = session.scalars(
                    select(Orders).where(Orders.order_number == order_number)
                ).one()
                order.username = message.text
                session.commit()
            await bot.send_message(
                message.from_id, f"Вы поменяли имя пользователя на {message.text}"
            )
            await bot.send_message(
                message.from_id,
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
            await state.finish()

        elif menu_new_telegram:
            with Session(engine) as session:
                order = session.scalars(
                    select(Orders).where(Orders.order_number == order_number)
                ).one()
                order.user_id = message.text
                session.commit()

            await bot.send_message(
                message.from_id,
                f"Вы поменяли телеграм пользователя на {message.text} \n\n"
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
            await state.finish()

        elif menu_new_tattoo_name:
            with Session(engine) as session:
                order = session.scalars(
                    select(Orders).where(Orders.order_number == order_number)
                ).one()
                order.order_name = message.text
                session.commit()
            await bot.send_message(
                message.from_id,
                f"Вы поменяли имя тату на {message.text} \n\n"
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
            await state.finish()

        elif menu_new_order_note:
            with Session(engine) as session:
                order = session.scalars(
                    select(Orders).where(Orders.order_number == order_number)
                ).one()
                order.order_note = message.text
                session.commit()
            await bot.send_message(
                message.from_id,
                f"Вы поменяли описание заказа тату на {message.text} \n\n"
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
            await state.finish()

        elif menu_new_tattoo_note:
            with Session(engine) as session:
                order = session.scalars(
                    select(Orders).where(Orders.order_number == order_number)
                ).one()
                order.tattoo_note = message.text
                session.commit()
            await bot.send_message(
                message.from_id,
                f"Вы поменяли описание тату на {message.text} \n\n"
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
            await state.finish()
        else:
            await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


@dp.callback_query_handler(
    dialog_cal_callback.filter(),
    state=FSM_Admin_change_tattoo_order.day_by_date,
)
async def get_day_by_date_for_schedule(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)  # type: ignore
    username_id = 0
    async with state.proxy() as data:
        username_id = data["user_id"]

    if selected:
        await callback_query.message.answer(f"Вы выбрали {date}")
        if date > datetime.now():
            # async def load_datemiting(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data["date"] = date.strftime("%d/%m/%Y")
                
            await FSM_Admin_change_tattoo_order.next() #-> process_hour_timepicker_start_session
            await bot.send_message(
                username_id,
                "Отлично, давай определимся со временем. "
                "С какого времени начинается сеанс?",
                reply_markup=await FullTimePicker().start_picker(),
            )

        else:
            await bot.send_message(
                username_id,
                "Выбери еще раз конкретную дату. '\
                'Дата должна быть позже в этом году, а не раньше.",
                reply_markup=await DialogCalendar().start_calendar(),
            )


@dp.callback_query_handler(
    full_timep_callback.filter(),
    state=FSM_Admin_change_tattoo_order.new_start_time_session,
)
async def process_hour_timepicker_start_session(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore
    if r.selected:
        """await callback_query.message.edit_text(
            f'Вы выбрали время для начала сеанса тату в {r.time.strftime("%H:%M")} ',
        )"""
        # await callback_query.message.delete_reply_markup()
        async with state.proxy() as data:
            data["start_time"] = r.time.strftime("%H:%M:%S")
            user_id = data["telegram"]

        await FSM_Admin_change_tattoo_order.next()  # -> process_hour_timepicker_end_session
        await bot.send_message(
            user_id,
            f'📅 Прекрасно! Вы выбрали время начала сеанса {r.time.strftime("%H:%M")}.',
        )
        await bot.send_message(
            user_id,
            "А теперь введи время конца сеанса",
            reply_markup=await FullTimePicker().start_picker(),
        )


@dp.callback_query_handler(
    full_timep_callback.filter(),
    state=FSM_Admin_change_tattoo_order.new_end_time_session,
)
async def process_hour_timepicker_end_session(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore
    if r.selected:
        """await callback_query.message.edit_text(
            f'Вы выбрали время для конца сеанса тату в {r.time.strftime("%H:%M")} ',
        )"""
        async with state.proxy() as data:
            data["end_time"] = r.time.strftime("%H:%M:%S")
            order_number = data["order_number"]
            # schedule_event_type = data['schedule_event_type']
            user_id = data["telegram"]
            
            with Session(engine) as session:
                order = session.scalars(select(Orders).where(Orders.order_number == order_number)).one()
                start_time = datetime.strptime(f"{data['date']}T{data['start_time']}","%d/%m/%YT%H:%M:%S")
                end_time = datetime.strptime(f"{data['date']}T{data['end_time']}","%d/%m/%YT%H:%M:%S")
                new_schedule_event = ScheduleCalendar(
                    start_datetime= start_time,
                    end_datetime=end_time, 
                    status= kb_admin.schedule_event_status['busy'], 
                    event_type= kb_admin.schedule_event_type['tattoo']
                )
                session.add(new_schedule_event)
                session.commit()
                
                schedule_event = session.scalars(select(ScheduleCalendar)
                    .where(ScheduleCalendar.start_datetime == start_time)
                    .where(ScheduleCalendar.end_datetime == end_time)).one()
                
                order.schedule_id = [
                    ScheduleCalendarItems(
                        order_number=order_number,
                        schedule_id=schedule_event.id
                    )
                ]
                
                """ start_datetime = schedule.start_datetime
                schedule.start_datetime = datetime.strptime(
                    f"{start_datetime.strftime('%d/%m/%Y')} "
                    f"{data['start_date_time'].strftime('%H:%M')}",
                    "%d/%m/%Y %H:%M",
                )

                end_datetime = schedule.end_datetime
                schedule.end_datetime = datetime.strptime(
                    f"{end_datetime.strftime('%d/%m/%Y')} "
                    f"{r.time.strftime('%H:%M')}",
                    "%d/%m/%Y %H:%M",
                ) """
                session.commit()
        await bot.send_message(user_id,MSG_SUCCESS_CHANGING)
        await bot.send_message(
            user_id,
            f'📅 Прекрасно! Вы выбрали время конца сеанса {r.time.strftime("%H:%M")}.',
        )
        await state.finish()
        await bot.send_message(
            user_id,
            f"Вы поменяли время дату и время сеанса!\n\n {MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )


async def get_new_photo(message: types.Message, state: FSMContext):
    if message.content_type == "photo":
        async with state.proxy() as data:
            photo_type = data["photo_type"]
            order_number = data["order_number"]

        if photo_type == "Изображение тату":
            with Session(engine) as session:
                order = session.scalars(
                    select(Orders).where(Orders.order_number == order_number)
                ).one()
                new_photo_item = OrderPhoto(
                    order_number=order.order_number,
                    telegram_user_id=order.user_id,
                    photo=message.photo[0].file_id,
                )
                if order.order_photo is None:
                    order.order_photo = [new_photo_item]
                else:
                    order.order_photo.append(new_photo_item)
                    
                session.commit()

        elif photo_type == "Фото части тела":
            with Session(engine) as session:
                order = session.scalars(
                    select(Orders).where(Orders.order_number == order_number)
                ).one()
                new_body_photo_item = TattooPlacePhoto(
                    order_number=order.order_number,
                    telegram_user_id=order.user_id,
                    photo=message.photo[0].file_id,
                )
                if order.tattoo_place_photo is None:
                    order.tattoo_place_photo = [new_body_photo_item]
                else:
                    order.tattoo_place_photo.append(new_body_photo_item)
                session.commit()

        await bot.send_message(
            message.from_id,
            f"Вы поменяли {photo_type} \n\n" f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )

        await state.finish()


# ------------------------------------------CREATE TATTOO ORDER-----------------------------------
class FSM_Admin_tattoo_order(StatesGroup):
    get_tattoo_type = State()
    tattoo_choice = State()
    tattoo_name = State()
    tattoo_photo = State()
    tattoo_size = State()
    tattoo_color = State()

    schedule_for_tattoo_order_choice = State()
    new_tattoo_order_date_from_schedule = State()

    date_meeting = State()
    start_date_time = State()
    end_date_time = State()

    tattoo_note = State()
    get_body_name_state = State()
    get_body_photo_state = State()

    order_desctiption_choiсe = State()
    order_desctiption = State()
    tattoo_order_price = State()
    tattoo_order_state = State()
    tattoo_order_check = State()
    tattoo_order_check_next = State()
    user_name = State()


class FSM_Admin_username_info(StatesGroup):
    user_name = State()
    user_name_answer = State()
    telegram = State()
    phone = State()


# Начало диалога с пользователем, который хочет добавить новый заказ тату
# @dp.message_handler(commands='Загрузить', state=None) #
async def command_command_create_tattoo_orders(message: types.Message):
    if (
        message.text in ["добавить тату заказ", "/добавить_тату_заказ"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_tattoo_order.get_tattoo_type.set()  # -> choice_tattoo_order_admin
        await bot.send_message(
            message.from_id,
            "Привет, админ. Сейчас будет создан тату заказ. "
            "Тату заказ будет для переводного тату или для постоянного?",
            reply_markup=kb_client.kb_client_choice_main_or_temporary_tattoo,
        )


async def get_tattoo_type(message: types.Message, state: FSMContext):
    if message.text in list(kb_client.choice_main_or_temporary_tattoo.values()):
        if message.text.split()[0].lower() == "переводное":
            async with state.proxy() as data:
                data["date_meeting"] = "Без указания даты сеанса"
                data["start_date_time"] = "Без указания начала сеанса"
                data["end_date_time"] = "Без указания конца сеанса"

        async with state.proxy() as data:
            # tattoo_type = постоянное, переводное
            data["tattoo_type"] = message.text.split()[0].lower()

            data["tattoo_photo_tmp_lst"] = ""
            data["tattoo_order_photo_counter"] = 0
            data["tattoo_place_file"] = ""
            data["client_add_tattoo_place_photo"] = True

        await FSM_Admin_tattoo_order.next()  # -> choice_tattoo_order_admin
        await bot.send_message(
            message.from_id,
            "Хорошо, теперь определи, это тату из твоей галереи или нет?",
            reply_markup=kb_client.kb_yes_no,
        )

    elif message.text in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# Отправляем название тату
async def choice_tattoo_order_admin(message: types.Message, state: FSMContext):
    list_kb_tattoo_items = []
    if message.text == kb_client.yes_str:
        with Session(engine) as session:
            admin_tattoo_items = session.scalars(select(TattooItems)).all()
        kb_tattoo_items_for_order = ReplyKeyboardMarkup(resize_keyboard=True)
        await bot.send_message(message.from_id, "Вот твоя галлерея:")

        for tattoo in admin_tattoo_items:
            kb_tattoo_items_for_order.add(KeyboardButton(f"{tattoo.name}"))
            list_kb_tattoo_items.append(f"{tattoo.name}")
            msg = f"📃 Название: {tattoo.name}\n🎨 Цвет: {tattoo.colored}\n"
            # \f'🔧 Количество деталей: {tattoo[5]}\n'

            if tattoo.note.lower() != "без описания":
                msg += f"💬 Описание: {tattoo.note}\n"  # 💰 Цена: {tattoo[2]}\n'
            
            media = []
            for photo in tattoo.photos:
                media.append(types.InputMediaPhoto(photo.photo, msg))
            
            if media != []:
                await bot.send_chat_action(
                    message.chat.id, types.ChatActions.UPLOAD_DOCUMENT
                )
                await bot.send_media_group(message.chat.id, media=media)
                if len(media) > 1:
                    await bot.send_message(message.from_user.id, msg)

            # await bot.send_media_group(message.from_user.id, media=media)

        # выдаем список тату - фотографии, название, цвет, описание
        await bot.send_message(
            message.from_id,
            "❔ Какое тату хочешь выбрать?",
            reply_markup=kb_tattoo_items_for_order,
        )

    elif message.text in list_kb_tattoo_items:
        with Session(engine) as session:
            tattoo = session.scalars(select(TattooItems)
                .where(TattooItems.name == message.text)).one()
        async with state.proxy() as data:
            data["telegram"] = message.from_user.id
            data["tattoo_name"] = message.text
            data["price"] = tattoo.price
            data["tattoo_photo_tmp_lst"] = tattoo.photos 
            data["colored"] = tattoo.colored
            data["tattoo_note"] = tattoo.note  
            data["tattoo_from_galery"] = True
        for i in range(3):
            await FSM_Admin_tattoo_order.next()  # -> tattoo_size

        await bot.send_message(
            message.from_id,
            "Введи размер тату (в см). Размер не может быть больше 150 см2 и меньше 0",
            reply_markup=kb_client.kb_client_size_tattoo,
        )

    elif message.text == kb_client.no_str:
        await FSM_Admin_tattoo_order.next()  # -> load_tattoo_order_name
        async with state.proxy() as data:
            data["tattoo_from_galery"] = False

        await bot.send_message(
            message.from_id,
            "Хорошо. Давай определимся с названием тату. Какое будет название?",
            reply_markup=kb_client.kb_cancel,
        )

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def load_tattoo_order_name(message: types.Message, state: FSMContext):
    if message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )

    elif message.text == kb_client.yes_str:
        await FSM_Admin_tattoo_order.next()  # -> load_tattoo_order_photo
        await message.reply(MSG_CLIENT_LOAD_PHOTO, reply_markup=kb_client.kb_cancel)

    elif message.text == kb_client.no_str:
        for i in range(2):
            await FSM_Admin_tattoo_order.next()  # -> load_tattoo_order_size
        await bot.send_message(
            message.from_id, "Хорошо, оставим пока данный заказ без эскиза"
        )

        await bot.send_message(
            message.from_id,
            MSG_CLIENT_CHOICE_TATTOO_SIZE,
            reply_markup=kb_client.kb_client_size_tattoo,
        )

    else:
        async with state.proxy() as data:
            # ставим сюда id телеги, чтобы бот мог ответить пользователю при выборе даты
            data["telegram"] = message.from_user.id
            data["tattoo_name"] = message.text

        await bot.send_message(message.from_id, f"Название тату будет {message.text}")
        await bot.send_message(
            message.from_id,
            f"Хочешь добавить фотографию эскиза тату?",
            reply_markup=kb_client.kb_yes_no,
        )


# Отправляем фото
async def load_tattoo_order_photo(message: types.Message, state: FSMContext):
    if message.content_type == "text":
        if (
            message.text
            in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME
        ):
            await state.finish()
            await message.reply(
                MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
            )

        elif message.text in [
            kb_client.no_photo_in_tattoo_order["load_tattoo_photo"],
            kb_client.client_choice_add_another_photo_to_tattoo_order["add"],
        ]:
            async with state.proxy() as data:
                data["tattoo_order_photo_counter"] = 0

            await bot.send_message(
                message.from_id,
                MSG_CLIENT_LOAD_PHOTO,
                reply_markup=kb_client.kb_back_cancel,
            )

        #'Закончить с добавлением изображений ➡️'
        elif (
            message.text
            == kb_client.client_choice_add_another_photo_to_tattoo_order["end"]
        ):
            await FSM_Admin_tattoo_order.next()  # -> load_tattoo_order_size
            await bot.send_message(
                message.from_id,
                "❕ Хорошо, с фотографиями для эскиза закончили.",
            )
            await bot.send_message(
                message.from_id,
                f"{MSG_CLIENT_CHOICE_TATTOO_SIZE}",
                reply_markup=kb_client.kb_client_size_tattoo,
            )
        else:
            await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)

    elif message.content_type == "photo":
        async with state.proxy() as data:
            data["tattoo_from_galery"] = False
            data["tattoo_photo_tmp_lst"] += f"{message.photo[0].file_id}|"
            tattoo_order_photo_counter = data["tattoo_order_photo_counter"]
            data["tattoo_order_photo_counter"] = message.media_group_id

        if tattoo_order_photo_counter != data["tattoo_order_photo_counter"]:
            async with state.proxy() as data:
                tattoo_order_photo_counter = data["tattoo_order_photo_counter"]

            await bot.send_message(
                message.from_id,
                "📷 Отлично, ты выбрал(а) фотографию эскиза для своего тату!",
            )
            await bot.send_message(
                message.from_id,
                "❔ Хочешь добавить еще фото/картинку?",
                reply_markup=kb_client.kb_client_choice_add_another_photo_to_tattoo_order,
            )


# Отправляем размер тату
async def load_tattoo_order_size(message: types.Message, state: FSMContext):
    if message.text in list(kb_client.size_dict.values()):
        async with state.proxy() as data:
            data["tattoo_size"] = message.text
            data["tattoo_place_file_counter"] = 0
            data["tattoo_place_video_note"] = ""
            data["tattoo_place_video"] = ""
            tattoo_from_galery = data["tattoo_from_galery"]
            tattoo_type = data["tattoo_type"]

        if tattoo_from_galery and tattoo_type.lower() == "постоянное":
            for i in range(2):
                await FSM_Admin_tattoo_order.next()  # -> load_tattoo_order_schedule_choice

            # ['Хочу выбрать дату из календаря', 'Хочу новую дату в календарь']
            await message.reply(
                "Хорошо, а теперь напиши дату или даты тату заказа. "
                "Хочешь выбрать дату заказа из календаря, или добавить новую дату в календарь и заказ?",
                reply_markup=kb_admin.kb_schedule_for_tattoo_order_choice,
            )  # await DialogCalendar().start_calendar()

        else:
            await FSM_Admin_tattoo_order.next()  # -> get_tattoo_color
            await bot.send_message(
                message.from_id,
                MSG_WHICH_COLOR_TYPE_WILL_BE_TATTOO,
                reply_markup=kb_client.kb_colored_tattoo_choice,
            )

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_tattoo_color(message: types.Message, state: FSMContext):
    if any(text in message.text for text in kb_client.colored_tattoo_choice):
        async with state.proxy() as data:
            data["tattoo_colored"] = message.text.split()[0]
            tattoo_type = data["tattoo_type"]

        await bot.send_message(
            message.from_id, f"🍃 Хорошо, тату будет {message.text.split()[0].lower()}"
        )

        if tattoo_type.lower() == "постоянное":
            await FSM_Admin_tattoo_order.next()  # -> load_tattoo_order_schedule_choice

            # ['Хочу выбрать дату из календаря', 'Хочу новую дату в календарь']
            await message.reply(
                "Хорошо, а теперь напиши дату или даты тату заказа."
                " Хочешь выбрать дату заказа из календаря, или добавить новую дату в календарь и заказ?",
                reply_markup=kb_admin.kb_schedule_for_tattoo_order_choice,
            )
        else:
            for i in range(6):
                await FSM_Admin_tattoo_order.next()  # -> load_tattoo_order_note

            await bot.send_message(
                message.from_id,
                'А теперь введи что-нибудь об этом тату. Так ты добавишь параметр "описание тату"',
                reply_markup=kb_client.kb_cancel,
            )

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def load_tattoo_order_schedule_choice(message: types.Message, state: FSMContext):
    if message.text == "Хочу выбрать дату из календаря":
        with Session(engine) as session:
            schedule = session.scalars(
                select(ScheduleCalendar)
                .where(ScheduleCalendar.status == kb_admin.schedule_event_status['free'])
                .where(ScheduleCalendar.event_type.in_([
                        kb_admin.schedule_event_type['tattoo'],
                        kb_admin.schedule_event_type['free']
                    ])
                )
                .order_by(ScheduleCalendar.start_datetime)
            )

        if schedule == []:
            await message.reply(
                f"У тебя пока нет расписания. Тогда создадим новую дату. Выбери пожалуйста, дату",
                reply_markup=await DialogCalendar().start_calendar(),
            )

            for i in range(2):
                await FSM_Admin_tattoo_order.next()  # -> load_datemiting
        else:
            async with state.proxy() as data:
                data["date_free_list"] = schedule
            kb_date_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            date_lst_to_view = ""
            for date in schedule:
                kb_schedule_item = (
                    f"{date.start_datetime.strftime('%d/%m/%Y с %H:%M')} до "
                    f"{date.end_datetime.strftime('%H:%M')}"
                )
                
                date_lst_to_view += f"{kb_schedule_item}\n"
                kb_date_schedule.add(KeyboardButton(kb_schedule_item))

            async with state.proxy() as data:
                data["date_lst_to_view"] = date_lst_to_view
                data["kb_date_schedule"] = kb_date_schedule

            kb_date_schedule.add(kb_client.cancel_btn)
            schedule_photo_name = datetime.now().strftime("%m %Y")
            with Session(engine) as session:
                schedule_photo = session.scalars(select(SchedulePhoto)
                    .where(SchedulePhoto.name == schedule_photo_name)).all()
            await FSM_Admin_tattoo_order.next()  # -> load_new_tattoo_order_date_from_schedule

            if schedule_photo == []:
                await bot.send_message(
                    message.from_user.id,
                    f"Свободные даты в этом месяце:\n{date_lst_to_view}"
                    "Какую дату и время выбираешь?",
                    reply_markup=kb_date_schedule,
                )

            else:
                await bot.send_photo(
                    message.from_user.id,
                    schedule_photo[0].photo,
                    f"Свободные даты в этом месяце:\n{date_lst_to_view}"
                    "Какую дату и время выбираешь?",
                    reply_markup=kb_date_schedule,
                )
                

    elif message.text == "Хочу новую дату в календарь":
        for i in range(2):
            await FSM_Admin_tattoo_order.next()  # -> load_datemiting
        await message.reply(
            f"Тогда создадим новую дату. Выбери пожалуйста, новую дату",
            reply_markup=await DialogCalendar().start_calendar(),
        )
    else:
        await message.reply(f"Пожалуйста, выбери ответ из предложенных вариантов")


async def load_new_tattoo_order_date_from_schedule(
    message: types.Message, state: FSMContext
):
    async with state.proxy() as data:
        date_lst_to_view = data["date_lst_to_view"]
    
    if message.text in date_lst_to_view.split('\n'):
        data["date"] = message.text.split()[0]
        data["start_time"] = message.text.split()[2]
        data["end_time"] = message.text.split()[4]

        for i in range(4):
            await FSM_Admin_tattoo_order.next() #-> load_tattoo_order_note
        await message.reply(
            f"Прекрасно! Вы выбрали дату {message.text.split()[2]} и время {message.text.split()[4]}.\n"
            "А теперь введи что-нибудь о своем тату"
        )


# выбираем новую дату заказа
@dp.callback_query_handler(
    dialog_cal_callback.filter(), state=FSM_Admin_tattoo_order.date_meeting
)
async def load_datemiting(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)  # type: ignore
    if selected:
        await callback_query.message.answer(f'Вы выбрали {date.strftime("%d/%m/%Y")}')
        username_id = 0
        async with state.proxy() as data:
            username_id = data["telegram"]

        if date <= datetime.now():
            await bot.send_message(
                username_id,
                "Эта дата уже прошла. Выбери другую дату.",
                reply_markup=await DialogCalendar().start_calendar(),
            )

        else:
            async with state.proxy() as data:
                data['date'] = date
                data["date_meeting"] = f'{date.strftime("%d/%m/%Y")}'  #  message.text
                data["month_number"] = int(f'{date.strftime("%m")}')
                data["month_name"] = await get_month_from_number(data["month_number"], "ru")

            await FSM_Admin_tattoo_order.next()
            await bot.send_message(
                username_id,
                "А теперь введи удобное для тебя время.",
                reply_markup=await FullTimePicker().start_picker(),
            )


# выбираем начало времени заказа
@dp.callback_query_handler(
    full_timep_callback.filter(), state=FSM_Admin_tattoo_order.start_date_time
)
async def process_hour_timepicker_start(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore
    if r.selected:
        await callback_query.message.edit_text(
            f'Вы выбрали время начала тату заказа в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            data["start_date_time"] = r.time.strftime("%H:%M")
            username_id = data["telegram"]

        await FSM_Admin_tattoo_order.next()
        await bot.send_message(
            username_id,
            "А теперь введи время окончания тату заказа",
            reply_markup=await FullTimePicker().start_picker(),
        )


# выбираем конец времени заказа
@dp.callback_query_handler(
    full_timep_callback.filter(), state=FSM_Admin_tattoo_order.end_date_time
)
async def process_hour_timepicker_end(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore
    if r.selected:
        await callback_query.message.edit_text(
            f'Вы выбрали время конца заказа тату в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            data["end_date_time"] = r.time.strftime("%H:%M")
            username_id = data["telegram"]
            schedule_id = await generate_random_order_number(CODE_LENTH)
            data["schedule_id"] = schedule_id

            with Session(engine) as session:
                new_schedule_event = ScheduleCalendar(
                    start_datetime = datetime.strptime(
                        f"{data['date']} {data['start_time']}", "%d/%m/%Y %H:%M"
                    ),
                    end_datetime= datetime.strptime(
                        f"{data['date']} {r.time.strftime('%H:%M')}", "%d/%m/%Y %H:%M"
                    ),
                    status = kb_admin.schedule_event_status['busy'], 
                    event_type = kb_admin.schedule_event_type['tattoo']
                )
                session.add(new_schedule_event)
                session.commit()

        await FSM_Admin_tattoo_order.next()  # -> load_tattoo_order_note
        await bot.send_message(
            username_id,
            'А теперь введи что-нибудь об этом тату. Так ты добавишь параметр "описание тату"',
            reply_markup=kb_client.kb_cancel,
        )


# Отправляем описание тату
async def load_tattoo_order_note(message: types.Message, state: FSMContext):
    if message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )
    else:
        async with state.proxy() as data:
            data["tattoo_note"] = message.text
        await FSM_Admin_tattoo_order.next()
        await bot.send_message(
            message.from_id,
            "❔ Добавить места, где будет расположено тату?",
            reply_markup=kb_client.kb_yes_no,
        )


async def get_body_name(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        await bot.send_message(
            message.from_id,
            "❔ Какое место будет у тату?",
            reply_markup=kb_client.kb_place_for_tattoo,
        )

    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            data["tattoo_body_place"] = "Без места для тату"
            data["tattoo_place_file"] = ""

        for i in range(2):
            await FSM_Admin_tattoo_order.next()  # -> choiсe_tattoo_order_desctiption
        await message.reply(
            '❔ Что-нибудь добавить к описанию этого заказа?\nОтветь "Да" или "Нет"',
            reply_markup=kb_client.kb_yes_no,
        )

    elif message.text in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )

    elif message.text in kb_client.tattoo_body_places:
        async with state.proxy() as data:
            data["tattoo_body_place"] = message.text

        await FSM_Admin_tattoo_order.next()
        await bot.send_message(
            message.from_id,
            "❔ Добавить фото местоположения?",
            reply_markup=kb_client.kb_yes_no,
        )


async def get_body_photo(message: types.Message, state: FSMContext):
    if message.content_type == "text":
        if message.text == kb_client.yes_str:
            async with state.proxy() as data:
                data["tattoo_place_file_counter"] = 0

            await bot.send_message(
                message.from_id,
                "Отправь фото места для тату",
                reply_markup=kb_client.kb_cancel,
            )

        elif message.text == kb_client.no_str:
            async with state.proxy() as data:
                data["tattoo_place_file"] = ""
                data["tattoo_place_video_note"] = ""
                data["tattoo_place_video"] = ""

            await FSM_Admin_tattoo_order.next()  # -> choiсe_tattoo_order_desctiption
            await message.reply(
                '❔ Добавить что-то к описанию этого заказа?\nОтветь "Да" или "Нет"',
                reply_markup=kb_client.kb_yes_no,
            )

        elif (
            message.text
            in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS
        ):
            await state.finish()
            await message.reply(
                MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
            )

        elif (message.text == kb_client.client_choice_add_another_photo_to_tattoo_order["add"]):
            await bot.send_message(
                message.from_id,
                MSG_SEND_ANOTHER_PHOTO,
                reply_markup=kb_client.kb_cancel,
            )

        elif (message.text == kb_client.client_choice_add_another_photo_to_tattoo_order["end"]):
            await FSM_Admin_tattoo_order.next()  # -> choiсe_tattoo_order_desctiption
            await message.reply(
                '❔ Добавить что-то к описанию этого заказа?\nОтветь "Да" или "Нет"',
                reply_markup=kb_client.kb_yes_no,
            )

        else:
            await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)

    elif message.content_type == "photo":
        async with state.proxy() as data:
            data["tattoo_place_file"] += f"{message.photo[0].file_id}|"
            data["client_add_tattoo_place_photo"] = True

            tattoo_place_file_counter = data["tattoo_place_file_counter"]
            data["tattoo_place_file_counter"] = message.media_group_id

        if tattoo_place_file_counter != data["tattoo_place_file_counter"]:
            async with state.proxy() as data:
                tattoo_place_file_counter = data["tattoo_place_file_counter"]

            await bot.send_message(
                message.from_id,
                "📷 Отлично, ты добавил(а) фотографию места для своего тату!",
            )

            await bot.send_message(
                message.from_id,
                MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY,
                reply_markup=kb_client.kb_client_choice_add_another_photo_to_tattoo_order,
            )
            # client_choice_add_another_photo_to_tattoo_order = {
            #'client_want_to_add_sketch_to_tattoo_order' : 'Добавить еще одно изображение ☘️',
            #'client_dont_want_to_add_sketch_to_tattoo_order' : 'Закончить с добавлением изображений ➡️'}

    elif message.content_type == "video_note":
        async with state.proxy() as data:
            data["tattoo_place_video_note"] += f"{message.video_note.file_id}|"

        await bot.send_message(
            message.from_id,
            "📷 Ввидео-заметка места для тату добавлено!",
        )
        await bot.send_message(
            message.from_id,
            MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY,
            reply_markup=kb_client.kb_yes_no,
        )

    elif message.content_type == "video":
        async with state.proxy() as data:
            data["tattoo_place_video"] += f"{message.video.file_id}|"
            tattoo_place_file_counter = data["tattoo_place_file_counter"]
            data["tattoo_place_file_counter"] = message.media_group_id

        if tattoo_place_file_counter != data["tattoo_place_file_counter"]:
            async with state.proxy() as data:
                tattoo_place_file_counter = data["tattoo_place_file_counter"]

            await bot.send_message(
                message.from_id, "📷 Ввидео места для тату добавлено!"
            )

            await bot.send_message(
                message.from_id,
                MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY,
                reply_markup=kb_client.kb_yes_no,
            )


async def choiсe_tattoo_order_desctiption(message: types.Message, state: FSMContext):
    await FSM_Admin_tattoo_order.next()
    if message.text == kb_client.yes_str:
        await message.reply("Хорошо! Опиши детали тату")

    elif message.text == kb_client.no_str:
        await FSM_Admin_tattoo_order.next()
        async with state.proxy() as data:
            data["order_note"] = "Без описания заказа"
        await message.reply(
            "Хорошо, тогда будем думать над деталями тату потом. Напиши примерную цену тату заказа. "
            "Выбери из представленного списка",
            reply_markup=kb_admin.kb_price,
        )
    else:
        await bot.send_message(
            message.from_id,
            'На данный вопрос можно ответить только "Да" или "Нет". Введите ответ корректно.',
        )


# Отправляем описание заказа тату
async def load_order_desctiption_after_choice(
    message: types.Message, state: FSMContext
):
    async with state.proxy() as data:
        data["order_note"] = message.text
    await FSM_Admin_tattoo_order.next()  # -> get_price_tattoo_order_after_choice
    await message.reply(
        f"Напишите примерную цену тату заказа. Выберите из представленного списка",
        reply_markup=kb_admin.kb_price,
    )  # В любом случае, заказ почти оформлен.


async def get_price_tattoo_order_after_choice(
    message: types.Message, state: FSMContext
):
    # Заполняем таблицу tattoo_items
    async with state.proxy() as data:
        tattoo_from_galery = data["tattoo_from_galery"]
        data["tattoo_price"] = message.text
        data["tattoo_details_number"] = 0
        data["order_state"] = STATES["open"]  # выставляем статус заказа как открытый
        data["order_number"] = await generate_random_order_number(
            ORDER_CODE_LENTH
        )
        data["creation_date"] = datetime.now()
        if not tattoo_from_galery:
            
            await bot.send_message(
                message.from_user.id,
                f"Отлично! В таблице tattoo_items появилась новая строка. "
                f"Таблица tattoo_items содержит информацию о всех тату, которые были в заказах, "
                f"и в которые ты создала сама. \n",
            )

    await FSM_Admin_tattoo_order.next()  # -> get_tattoo_order_state
    await bot.send_message(
        message.from_user.id,
        '❔ Клиент оплатил заказ? Ответь "Да" или "Нет"',
        reply_markup=kb_client.kb_yes_no,
    )


async def get_tattoo_order_state(message: types.Message, state: FSMContext):
    tattoo_order_number = 0
    await FSM_Admin_tattoo_order.next()
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            data["order_state"] = STATES["paid"]

        await bot.send_message(
            message.from_user.id,
            f'❔ Хочешь приложить чек к заказу? Ответь "Да" или "Нет"',
            reply_markup=kb_client.kb_yes_no,
        )
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            data["order_state"] = STATES["open"]
            data["check_document"] = []
            tattoo_order_number = data["order_number"]
        for i in range(2):
            await FSM_Admin_tattoo_order.next()
        await bot.send_message(
            message.from_user.id,
            f"Заказ № {tattoo_order_number} почти оформлен! "
            "Осталось ввести имя, телеграм и телефон пользователя, и все будет готово!\n"
            "Введи, пожалуйста, имя пользователя",
            reply_markup=kb_client.kb_cancel,
        )
    else:
        await bot.send_message(
            message.from_id,
            'На данный вопрос можно ответить только "Да" или "Нет". Введи ответ корректно.',
        )


async def get_tattoo_order_check(message: types.Message, state: FSMContext):
    tattoo_order_number = 0
    if message.text == kb_client.yes_str:
        await FSM_Admin_tattoo_order.next()
        await bot.send_message(
            message.from_user.id,
            MSG_ADMIN_GET_CHECK_TO_ORDER,
        )

    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            tattoo_order_number = data["order_number"]
            
        for i in range(2):
            await FSM_Admin_tattoo_order.next()
        await bot.send_message(
            message.from_user.id,
            f"Заказ № {tattoo_order_number} почти оформлен! "
            "Осталось ввести Имя, Телеграм и Телефон пользователя, и все будет готово!\n"
            "Введи Имя пользователя",
        )

    else:
        await bot.send_message(
            message.from_user.id,
            'На данный вопрос можно ответить только "Да" или "Нет". Введи ответ корректно.',
        )


async def get_tattoo_order_check_next(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        tattoo_order_number = data["order_number"]
        price = data["tattoo_price"]
        
        check_doc_pdf = await check_photo_payment(
            message,
            message.from_id,
            price,
            message.document.file_name,
            message.document.file_id,
        )

    if check_doc_pdf["result"]:
        data["check_document"] = [
                CheckDocument(
                    order_number = tattoo_order_number,
                    doc= message.document.file_id
                )
            ]
        
        await FSM_Admin_tattoo_order.next() #-> tattoo_order_load_user_name
        await bot.send_message(
            message.from_user.id,
            f"Чек подошел! Заказ № {tattoo_order_number} почти оформлен! "
            "Осталось ввести имя, телеграм и телефон пользователя, и все будет готово!\n\n"
            "❕ Введи, пожалуйста, имя пользователя",
        )

    else:
        await message.reply(f"❌ Чек не подошел! {check_doc_pdf['report_msg']}")  # type: ignore


# выбираем имя покупателя
async def tattoo_order_load_user_name(message: types.Message, state: FSMContext):
    # Заполняем таблицу clients
    order_photo_lst = []
    tattoo_photo_lst = []
    async with state.proxy() as data:
        data["username"] = message.text
        tattoo_order_number = data["order_number"]
        with Session(engine) as session:
            
            """
                Определяем новое Тату - TattooItemPhoto
            """

            if data["tattoo_photo_tmp_lst"] != "":
                for photo in data["tattoo_photo_tmp_lst"].split("|"):
                    # при split('|') возникает еще одна переменная '', ее необходимо не добавлять
                    if photo != "":
                        tattoo_photo_lst.append(
                            TattooItemPhoto(
                                photo=photo, tattoo_item_name=data["tattoo_name"]
                            )
                        )
                        order_photo_lst.append(
                            OrderPhoto(
                                order_number=data["order_number"],
                                telegram_user_id=message.from_id,
                                photo=photo,
                            )
                        )
            else:
                tattoo_photo_lst.append(
                    TattooItemPhoto(photo=None, tattoo_item_name=data["tattoo_name"])
                )
            schedule_item = None
            if data["schedule_id"] not in [None, []]:
                schedule_item = [
                    ScheduleCalendarItems(
                        schedule_id=data["schedule_id"],
                        order_number=data["order_number"],
                    )
                ]
            new_tattoo_order = Orders(
                order_type=data["tattoo_type"],
                order_name=data["tattoo_name"],
                user_id=message.from_id,
                order_photo=order_photo_lst,
                tattoo_size=data["tattoo_size"],
                tattoo_note=data["tattoo_note"],
                order_note=data["order_note"],
                order_state=data["order_state"],
                order_number=data["order_number"],
                creation_date=data["creation_date"],
                price=data["tattoo_price"],
                check_document=data["check_document"],
                username=data["username"],
                schedule_id=schedule_item,
                colored=data["tattoo_colored"],
                # tattoo_details_number=  data['tattoo_details_number'],
                bodyplace=data["tattoo_body_place"],
                tattoo_place_photo=data["tattoo_place_photo"],
                tattoo_place_video_note=data["tattoo_place_video_note"],
                tattoo_place_video=data["tattoo_place_video"],
            )
            session.add(new_tattoo_order)
            schedule = session.get(ScheduleCalendar, data["schedule_id"])
            schedule.status = kb_admin.schedule_event_status['busy']
            session.commit()
            
        start_time = datetime.strptime(
            f"{data['date'].strftime('%Y-%m-%d')}T{data['start_time']}:00",
            "%Y-%m-%dT%H:%M:%S"
        )

        end_time = datetime.strptime(
            f"{data['date'].strftime('%Y-%m-%d')}T{data['end_date_time']}:00",
            "%Y-%m-%dT%H:%M:%S"
        )

        event = await obj.add_event(
            CALENDAR_ID,
            f"Новый тату заказ № {tattoo_order_number}",
            f"Название тату: {data['tattoo_name']}, \n"
            f"Описание тату: {data['tattoo_note']}, \n"
            f"Описание заказа: {data['order_note']}, \n"
            f"Имя клиента: {message.from_user.full_name}\n",
            start_time,  # '2023-02-02T09:07:00',
            end_time,  # '2023-02-03T17:07:00'
        )
    
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.name == message.text)).all()
    if user!= []:
        user_name = user[0].name

    await state.finish()
    await FSM_Admin_username_info.user_name.set()

    async with state.proxy() as data:
        data["username"] = message.text
        data["order_number"] = tattoo_order_number

    if user != [] and user is not None:
        if message.text != user_name:
            for i in range(2):
                await FSM_Admin_username_info.next() #-> load_telegram
            await message.reply(MSG_WHICH_USERNAME_IN_ORDER)
        else:
            await FSM_Admin_username_info.next() #-> answer_user_name
            await message.reply(
                f"Это пользователь под именем {user_name}?",
                reply_markup=kb_client.kb_yes_no,
            )
    else:
        for i in range(2):
            await FSM_Admin_username_info.next() #-> load_telegram
        await message.reply(MSG_WHICH_USERNAME_IN_ORDER)


# TODO: ЗАКОНЧИТЬ ЗАПОЛНЕНИЕ НОВОГО ПОЛЬЗОВАТЕЛЯ ДЛЯ ТАТУ ЗАКАЗА, ДЛЯ АДМИНА
async def answer_user_name(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            username, telegram, phone = (
                data["username"],
                data["telegram"],
                data["phone"],
            )
            order_number = data["order_number"]
            await bot.send_message(
                message.from_user.id,
                f"🎉 Заказ под номером {order_number}"
                f" оформлен на пользователя {username} с телеграмом {telegram}, телефон {phone}!",
                reply_markup=kb_admin.kb_main,
            )
        await state.finish()
    elif message.text == kb_client.no_str:
        await FSM_Admin_username_info.next() #-> load_telegram
        await message.reply(
            MSG_WHICH_USERNAME_IN_ORDER
        )
    else:
        await FSM_Admin_username_info.next()


async def load_telegram(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["telegram"] = message.text
    await FSM_Admin_username_info.next() # -> load_phone
    await bot.send_message(
            message.from_id, MSG_ADD_USER_PHONE_TO_DB, reply_markup= kb_client.kb_yes_no
        )
    
    await message.reply(
        MSG_WHICH_USERNAME_PHONE_IN_ORDER,
        reply_markup=kb_admin.kb_admin_has_no_phone_username,
    )


async def load_phone(message: types.Message, state: FSMContext):
    if message.text in kb_admin.phone_answer + [kb_client.no_str]:
        number = "Нет номера"
        
    elif message.text == kb_client.yes_str:
        await message.reply(
            MSG_WHICH_USERNAME_PHONE_IN_ORDER,
            reply_markup=kb_admin.kb_admin_has_no_phone_username,
        )
    else:
        number = message.text
        result = re.match(
            r"^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?"
            "[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$",
            number,
        )

        if not result:
            await message.reply("Номер не корректен. Пожалуйста, введи номер заново.")

        async with state.proxy() as data:
            with Session(engine) as session:
                new_user = User(
                    name = data["username"],
                    telegram_name= data["telegram"],
                    phone= number,
                    status= clients_status['client']
                )
                session.add(new_user)
                session.commit()
                
            username, telegram, phone = data["username"], data["telegram"], number
            tattoo_order_number = data["order_number"]

            await bot.send_message(
                message.from_user.id,
                f"Хорошо, твой заказ под номером {tattoo_order_number}"
                f" оформлен на пользователя {username} с телеграмом {telegram}, телефон: {phone}!",
                reply_markup=kb_admin.kb_tattoo_order_commands,
            )
            await state.finish()  #  полностью очищает данные


# -------------------------------ADD NEW EVENT SCHEDULE TO TATTOO ORDER--------------------------------

class FSM_Admin_create_new_schedule_event_to_tattoo_order(StatesGroup):
    tattoo_order_number = State()
    schedule_type = State()
    new_date = State()
    new_start_time = State()
    new_end_time = State()
    notify_client = State()


# добавить сеанс в заказ
async def command_create_new_schedule_event_to_order(message: types.Message):
    if (
        message.text in ["добавить новый сеанс в тату заказ", "/добавить_новый_сеанс_в_тату_заказ"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):  
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders).where(
                    Orders.order_type.in_(
                        [
                            kb_admin.price_lst_types["constant_tattoo"]
                        ]
                    )
                )
            ).all()
        kb_tattoo_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
        if orders == []:
            await message.reply(f"{MSG_NO_ORDER_IN_TABLE}")

        else:
            for order in orders:  # выводим номера тату заказов и их статус
                kb_tattoo_order_numbers.add(
                    KeyboardButton(f"{order.order_number} статус: {order.order_state}")
                )
            kb_tattoo_order_numbers.add(kb_admin.home_btn)
            await FSM_Admin_change_tattoo_order.tattoo_order_number.set()
            await message.reply(
                "К какому заказу добавить сеанс?",
                reply_markup=kb_tattoo_order_numbers,
            )


async def update_schedule_table(state: FSMContext):
    async with state.proxy() as data:
        username_id = data["user_id"]
        schedule_id = data["schedule_id"]
        event_date_old = data["event_date_old"].split("|")[1].split()

    with Session(engine) as session:
        new_date = session.get(ScheduleCalendar, schedule_id)

    old_data_to_send = {
        "id": new_date.id,
        "month": event_date_old[0],
        "date": event_date_old[1],
        "start time": event_date_old[3],
        "end time": event_date_old[5],
        "state": event_date_old[7],
        "type": event_date_old[9] + " " + event_date_old[10],
    }

    new_data_to_send = {
        "id": new_date.id,
        "month": await get_month_from_number(
            int(new_date.start_datetime.strftime("%m")), "ru"
        ),
        "date": new_date.start_datetime.strftime("%d/%m/%Y"),
        "start time": new_date.start_datetime.strftime("%H:%M"),
        "end time": new_date.end_datetime.strftime("%H:%M"),
        "state": new_date.status,
        "type": new_date.event_type,
    }
    headers = ["Месяц", "Дата", "Время начала", "Время конца", "Статус", "Тип"]
    table = PrettyTable(
        headers, left_padding_width=1, right_padding_width=1
    )  # Определяем таблицу
    table.add_row(list(old_data_to_send.values()))
    await bot.send_message(
        username_id, f"<pre>{table}</pre>", parse_mode=types.ParseMode.HTML
    )

    table_next = PrettyTable(headers, left_padding_width=1, right_padding_width=1)
    table_next.add_row(list(new_data_to_send.values()))
    await bot.send_message(
        username_id, f"<pre>{table_next}</pre>", parse_mode=types.ParseMode.HTML
    )


# ---------------------------get_tattoo_order_number_to_new_schedule_event--------------------------------
async def get_tattoo_order_number_to_new_schedule_event(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders).where(
                Orders.order_type.in_([
                            kb_admin.price_lst_types["constant_tattoo"]
                        ]
                    )
                )
            ).all()
    order_lst = []
    kb_tattoo_order_numbers_with_status = ReplyKeyboardMarkup(resize_keyboard=True)
    
    for order in orders:
        msg_item = f"{order.order_number} статус: {order.order_state}"
        order_lst.append(msg_item)
        kb_tattoo_order_numbers_with_status.add(KeyboardButton(msg_item))
        
    async with state.proxy() as data:
        data['kb_tattoo_order_numbers_with_status'] = kb_tattoo_order_numbers_with_status
    
    if message.text in order_lst:
        async with state.proxy() as data:
            data['order_number'] = message.text.split()[0]
            with Session(engine) as session:
                orders = session.scalars(
                        select(Orders).where(Orders.order_number == message.text.split()[0])
                    ).one()
            data['client_name'] = orders.username
            data['client_id'] = order.user_id
            
        await message.reply(
            "Добавить новый сеанс из календаря или создать новый сеанс?",
            reply_markup= kb_admin.kb_admin_choice_create_new_or_created_schedule_item
        )
        
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )


async def get_schedule_type(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        schedule_events = session.scalars(
            select(ScheduleCalendar).where(ScheduleCalendar.status.in_(
                    [kb_admin.schedule_event_status['free']]
                )
            )
        ).all()
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    schedule_events_kb_lst = []
    for event in schedule_events:
        event_item = (
            f"{event.start_datetime.strftime('%d/%m/%Y с %H:%M')} по "
            f"{event.end_datetime.strftime('%H:%M')}"
        )
            
        schedule_events_kb_lst.append(event_item)
        kb.add(KeyboardButton(event_item))
        
    if message.text == kb_admin.admin_choice_create_new_or_created_schedule_item['create_new_schedule']:
        # -> process_get_new_date_for_new_data_schedule    
        await FSM_Admin_create_new_schedule_event_to_tattoo_order.next() 
        await message.reply(
            f"Введите новую дату для тату заказа",
            reply_markup=await DialogCalendar().start_calendar(),
        )
    elif message.text in schedule_events_kb_lst:
        async with state.proxy() as data:
            order_number = data['order_number']
        start_time = datetime.strptime(f"{message.text.split(' по ')[0]}", '%d/%m/%Y с %H:%M')
        with Session(engine) as session:
            order = session.scalars(select(Orders).where(Orders.order_number == order_number)).one()
            schedule = session.scalars(select(ScheduleCalendar)
                .where(ScheduleCalendar.start_datetime == start_time)
                ).one()
            
            order.schedule_id.append(
                ScheduleCalendarItems(
                    order_number = order_number, 
                    schedule_id = schedule.id
                )
            )
            session.commit()
        
        
    elif message.text == kb_admin.admin_choice_create_new_or_created_schedule_item['choice_created_schedule']:
        
        await bot.send_message(
            message.from_id, "Какой день выбираешь?", reply_markup=kb
        )
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )
    elif message.text in LIST_BACK_COMMANDS:
        async with state.proxy() as data:
            kb_tattoo_order_numbers_with_status = data['kb_tattoo_order_numbers_with_status']
        #-> get_tattoo_order_number_to_new_schedule_event
        await FSM_Admin_create_new_schedule_event_to_tattoo_order.previous() 
        await message.reply(
            "К какому заказу добавить сеанс?",
            reply_markup=kb_tattoo_order_numbers_with_status,
        )


@dp.callback_query_handler(
    dialog_cal_callback.filter(),
    state=FSM_Admin_create_new_schedule_event_to_tattoo_order.new_date,
)
async def process_get_new_date_for_new_data_schedule(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)  # type: ignore
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали новую дату {date.strftime("%d/%m/%Y")}'
        )

        async with state.proxy() as data:
            data["date_meeting"] = date
            user_id = data["user_id"]
            new_date_tattoo_order = data["new_date_tattoo_order"]
            schedule_id = data["schedule_id"]

        if new_date_tattoo_order:
            # -> process_hour_timepicker_new_start_time_in_tattoo_order
            await FSM_Admin_create_new_schedule_event_to_tattoo_order.next()
            await bot.send_message(
                user_id,
                f"Введи новое время для тату заказа",
                reply_markup=await FullTimePicker().start_picker(),
            )

        else:
            with Session(engine) as session:
                schedule_event = session.get(ScheduleCalendar, schedule_id)
                schedule_event.start_datetime = datetime.strptime(
                    f"{date.strftime('%Y-%m-%d')} {schedule_event.start_datetime.strftime('%H:%M')}",
                    "%Y-%m-%d %H:%M",
                )
                schedule_event.end_datetime = datetime.strptime(
                    f"{date.strftime('%Y-%m-%d')} {schedule_event.start_datetime.strftime('%H:%M')}",
                    "%Y-%m-%d %H:%M",
                )
                session.commit()
            await update_schedule_table(state)
            await bot.send_message(
                user_id,
                MSG_DO_CLIENT_WANT_TO_DO_MORE,
                reply_markup=kb_admin.kb_schedule_commands,
            )
            await state.finish()


# выбираем новое время начала
@dp.callback_query_handler(
    full_timep_callback.filter(),
    state=FSM_Admin_create_new_schedule_event_to_tattoo_order.new_start_time,
)
async def process_hour_timepicker_new_start_time_in_tattoo_order(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore

    if r.selected:
        await callback_query.message.edit_text(
            f'Вы выбрали время {r.time.strftime("%H:%M")} ',
        )
        async with state.proxy() as data:
            user_id = data["user_id"]
            data["start_time_in_tattoo_order"] = r.time.strftime("%H:%M")
        # -> process_hour_timepicker_new_end_time_in_tattoo_order
        await FSM_Admin_create_new_schedule_event_to_tattoo_order.next()
        await bot.send_message(
            user_id,
            f"А теперь введи время окончания сеанса",
            reply_markup=await FullTimePicker().start_picker(),
        )


# выбираем новое время конца сеанса
@dp.callback_query_handler(
    full_timep_callback.filter(),
    state=FSM_Admin_create_new_schedule_event_to_tattoo_order.new_end_time,
)
async def process_hour_timepicker_new_end_time_in_tattoo_order(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore

    if r.selected:
        await callback_query.message.edit_text(
            f'Вы выбрали время {r.time.strftime("%H:%M")}'
        )

        async with state.proxy() as data:
            start_time_in_tattoo_order = datetime.strptime(
                f"{data['date_meeting'].strftime('%Y-%m-%d')} {data['start_time_in_tattoo_order']}",
                "%Y-%m-%d %H:%M",
            )
            end_time_in_tattoo_order = datetime.strptime(
                f"{data['date_meeting'].strftime('%Y-%m-%d')} {r.time.strftime('%H:%M')}",
                "%Y-%m-%d %H:%M",
            )
            order_number = data["order_number"]
            user_id = data["user_id"]
            data["new_start_date"] = data["date_meeting"].strftime("%Y-%m-%d")
            data["new_start_time"] = data["start_time_in_tattoo_order"]
            data["new_end_time"] = r.time.strftime("%H:%M")

        with Session(engine) as session:
            new_schedule_event = ScheduleCalendar(
                start_datetime=start_time_in_tattoo_order,
                end_datetime=end_time_in_tattoo_order,
                status=kb_admin.schedule_event_status['busy'],
                event_type= kb_admin.schedule_event_type['tattoo'],
            )
            session.add(new_schedule_event)
            session.commit()

        await bot.send_message(
            user_id,
            f"У тату заказа №{order_number} добавилась дата сеанса с "
            f"{start_time_in_tattoo_order.strftime('%Y-%m-%d %H:%M')} по"
            f"{end_time_in_tattoo_order.strftime('%Y-%m-%d %H:%M')}."
            "А также добавилась новая дата в календаре.",
        )
        #-> get_anwser_to_notify_client
        await FSM_Admin_create_new_schedule_event_to_tattoo_order.next()
        await bot.send_message(
            user_id,
            MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
            reply_markup=kb_client.kb_yes_no,
        )


async def get_anwser_to_notify_client(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            await bot.send_message(
                data['client_id'],
                MSG_CLIENT_HAVE_NEW_DATE_IN_TATTOO_ORDER_WITH_NO_OLD_SCHEDULE
                % [
                    data['client_name'],
                    data['order_number'],
                    f"{data['new_start_date']} {data['new_start_time']}",
                    data["new_end_time"],
                ],
            )
        await update_schedule_table(state)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        await state.finish()

    elif message.text == kb_client.no_str:
        await update_schedule_table(state)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        await state.finish()
    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


def register_handlers_admin_tattoo_order(dp: Dispatcher):
    # --------------------------------------TATTOO ORDER------------------------------
    dp.register_message_handler(
        get_tattoo_order_and_item_command_list, commands=["тату_заказы"]
    )
    dp.register_message_handler(
        get_tattoo_order_and_item_command_list,
        Text(equals="Тату заказы", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_tattoo_orders, commands=["посмотреть_тату_заказы"]
    )
    dp.register_message_handler(
        command_get_info_tattoo_orders,
        Text(equals="посмотреть тату заказы", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_status_name, state=FSM_Admin_get_info_orders.order_status_name
    )
    dp.register_message_handler(
        get_view_type, state=FSM_Admin_get_info_orders.get_view_type
    )

    dp.register_message_handler(
        command_get_info_tattoo_order, commands=["посмотреть_тату_заказ"]
    )
    dp.register_message_handler(
        command_get_info_tattoo_order,
        Text(equals="посмотреть тату заказ", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        get_name_for_view_tattoo_order,
        state=FSM_Admin_command_get_info_tattoo_order.order_name,
    )

    dp.register_message_handler(
        command_delete_info_tattoo_orders, commands=["удалить_тату_заказ"]
    )
    dp.register_message_handler(
        command_delete_info_tattoo_orders,
        Text(equals="удалить тату заказ", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        delete_info_tattoo_orders,
        state=FSM_Admin_delete_tattoo_order.tattoo_order_number,
    )

    dp.register_message_handler(
        command_tattoo_order_change_status, commands=["изменить_статус_тату_заказа"]
    )
    dp.register_message_handler(
        command_tattoo_order_change_status,
        Text(equals="изменить статус тату заказа", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_new_status_for_tattoo_order,
        state=FSM_Admin_tattoo_order_change_status.tattoo_order_number,
    )
    dp.register_message_handler(
        complete_new_status_for_tattoo_order,
        state=FSM_Admin_tattoo_order_change_status.tattoo_order_new_status,
    )

    dp.register_message_handler(
        get_answer_for_getting_check_document,
        state=FSM_Admin_tattoo_order_change_status.get_answer_for_getting_check_document,
    )
    dp.register_message_handler(
        get_price_for_check_document,
        state=FSM_Admin_tattoo_order_change_status.get_price_for_check_document,
    )
    
    dp.register_callback_query_handler(process_callback_set_price_from_line,
        state=FSM_Admin_tattoo_order_change_status.get_price_for_check_document)

    dp.register_message_handler(
        get_check_document,
        content_types=["photo", "document"],
        state=FSM_Admin_tattoo_order_change_status.get_check_document,
    )

    # --------------------------------CHANGE TATTOO ORDER-------------------------------------
    dp.register_message_handler(
        command_command_change_info_tattoo_order, commands=["изменить_тату_заказ"]
    )
    dp.register_message_handler(
        command_command_change_info_tattoo_order,
        Text(equals="изменить тату заказ", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        get_tattoo_order_number, state=FSM_Admin_change_tattoo_order.tattoo_order_number
    )
    dp.register_message_handler(
        get_new_state_info, state=FSM_Admin_change_tattoo_order.tattoo_new_state
    )
    dp.register_callback_query_handler(process_callback_set_price_from_line,
        state=FSM_Admin_change_tattoo_order.tattoo_new_state)
    dp.register_message_handler(
        get_new_photo,
        content_types=["photo"],
        state=FSM_Admin_change_tattoo_order.new_photo,
    )

    # --------------------------CREATE TATTOO ORDER--------------------------------------
    dp.register_message_handler(
        command_command_create_tattoo_orders, commands=["добавить_тату_заказ"]
    )
    dp.register_message_handler(
        command_command_create_tattoo_orders,
        Text(equals="добавить тату заказ", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_tattoo_type, state=FSM_Admin_tattoo_order.get_tattoo_type
    )
    dp.register_message_handler(
        choice_tattoo_order_admin, state=FSM_Admin_tattoo_order.tattoo_choice
    )
    dp.register_message_handler(
        load_tattoo_order_name, state=FSM_Admin_tattoo_order.tattoo_name
    )
    dp.register_message_handler(
        load_tattoo_order_photo,
        content_types=["photo", "text"],
        state=FSM_Admin_tattoo_order.tattoo_photo,
    )
    dp.register_message_handler(
        load_tattoo_order_size, state=FSM_Admin_tattoo_order.tattoo_size
    )
    dp.register_message_handler(
        get_tattoo_color, state=FSM_Admin_tattoo_order.tattoo_color
    )

    dp.register_message_handler(
        load_tattoo_order_schedule_choice,
        state=FSM_Admin_tattoo_order.schedule_for_tattoo_order_choice,
    )
    dp.register_message_handler(
        load_new_tattoo_order_date_from_schedule,
        state=FSM_Admin_tattoo_order.new_tattoo_order_date_from_schedule,
    )

    # dp.register_message_handler(load_datemiting, state=FSM_Client_tattoo_order.date_meeting)
    dp.register_message_handler(
        load_tattoo_order_note, state=FSM_Admin_tattoo_order.tattoo_note
    )
    dp.register_message_handler(
        get_body_name, state=FSM_Admin_tattoo_order.get_body_name_state
    )
    dp.register_message_handler(
        get_body_photo,
        content_types=["photo", "text", "video", "video_note"],
        state=FSM_Admin_tattoo_order.get_body_photo_state,
    )
    dp.register_message_handler(
        choiсe_tattoo_order_desctiption,
        state=FSM_Admin_tattoo_order.order_desctiption_choiсe,
    )
    dp.register_message_handler(
        load_order_desctiption_after_choice,
        state=FSM_Admin_tattoo_order.order_desctiption,
    )
    dp.register_message_handler(
        get_price_tattoo_order_after_choice,
        state=FSM_Admin_tattoo_order.tattoo_order_price,
    )

    dp.register_message_handler(
        get_tattoo_order_state, state=FSM_Admin_tattoo_order.tattoo_order_state
    )

    dp.register_message_handler(
        get_tattoo_order_check, state=FSM_Admin_tattoo_order.tattoo_order_check
    )
    dp.register_message_handler(
        get_tattoo_order_check_next,
        content_types=["photo", "document"],
        state=FSM_Admin_tattoo_order.tattoo_order_check_next,
    )

    dp.register_message_handler(
        tattoo_order_load_user_name, state=FSM_Admin_tattoo_order.user_name
    )
    dp.register_message_handler(
        answer_user_name, state=FSM_Admin_username_info.user_name_answer
    )
    dp.register_message_handler(
        load_telegram, state=FSM_Admin_username_info.telegram
    )  # добавляет всю инфу про пользователя
    dp.register_message_handler(
        load_phone, state=FSM_Admin_username_info.phone
    )  # добавляет всю инфу про пользователя

    # ---------------------------ADD NEW SCHEDULE EVENT OT TATTOO ORDER -------------
    dp.register_message_handler(
        command_create_new_schedule_event_to_order,
        Text(equals="добавить новый сеанс в тату заказ", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_tattoo_order_number_to_new_schedule_event,
        state=FSM_Admin_create_new_schedule_event_to_tattoo_order.tattoo_order_number
    )
    dp.register_message_handler(
        get_schedule_type,
        state=FSM_Admin_create_new_schedule_event_to_tattoo_order.schedule_type
    )
    dp.register_message_handler(
        get_anwser_to_notify_client,
        state=FSM_Admin_create_new_schedule_event_to_tattoo_order.notify_client
    )