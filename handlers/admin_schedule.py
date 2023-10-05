from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import (
    ADMIN_NAMES,
    CALENDAR_ID,
    DARA_ID,
)
from handlers.other import *
from handlers.admin_tattoo_order import FSM_Admin_tattoo_order

from handlers.other import *
from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult, Sequence
from db.sqlalchemy_base.db_classes import *

# from diffusers import StableDiffusionPipeline
# import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from aiogram_calendar import dialog_cal_callback, DialogCalendar
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback

from prettytable import PrettyTable
from handlers.calendar_client import obj
from msg.main_msg import *
import json


# --------------------------------------- SEND TO ADMIN ALL SCHEDULE AT 12:00----------------------------
async def send_notification_schedule():
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders).where(
                Orders.order_type.in_("переводное тату", "постоянное тату").where(
                    Orders.order_state.in_(list(STATES["closed"].values()))
                )
            )
        ).all()

    for order in orders:
        if DARA_ID != 0:
            await bot.send_message(
                DARA_ID,
                "📃 Дорогая тату мастерица! Вот твое расписание на сегодня:\n"
                f"{order.order_type}\n"
                f"Номер заказа: {order.order_number}"
                f"Статус заказа: {order.order_state}",
            )
            with Session(engine) as session:
                schedule = session.scalars(ScheduleCalendar).all()
            await get_view_schedule(DARA_ID, schedule)


# -------------------------------- CREATE NEW SCHEDULE---------------------------------
async def command_get_schedule_command_list(message: types.Message):
    if message.text == "Расписание" and str(message.from_user.username) in ADMIN_NAMES:
        await message.reply(
            MSG_WHICH_COMMAND_TO_EXECUTE, 
            reply_markup=kb_admin.kb_schedule_commands
        )


# -------------------------------------- ADD NEW PHOTO SCHEDULE DATE -----------------------------------
# /добавить фото расписания
class FSM_Admin_create_new_photo_to_schedule(StatesGroup):
    number_month_year_for_photo = State()
    photo_to_schedule = State()


async def command_new_photo_to_schedule(message: types.Message):
    if (
        message.text.lower() == "добавить фото расписания"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        kb_month_year = ReplyKeyboardMarkup(resize_keyboard=True)
        month_today = int(datetime.strftime(datetime.now(), "%m"))
        year_today = int(datetime.strftime(datetime.now(), "%Y"))
        for j in range(0, 3):
            for i in range(month_today, 12):
                kb_month_year.add(KeyboardButton(f"{i} {year_today+j}"))
        kb_month_year.add(KeyboardButton("Назад"))
        await FSM_Admin_create_new_photo_to_schedule.number_month_year_for_photo.set()
        await message.reply(
            "❔ На какой месяц хочешь добавить фото к расписанию?",
            reply_markup=kb_month_year,
        )


async def get_name_for_photo_to_schedule(message: types.Message, state: FSMContext):
    names_photo_list = []
    month_today = int(datetime.strftime(datetime.now(), "%m"))
    year_today = int(datetime.strftime(datetime.now(), "%Y"))
    for j in range(0, 1):
        for i in range(month_today, 12):
            names_photo_list.append(f"{i} {year_today+j}")
    if message.text.lower() in names_photo_list:
        async with state.proxy() as data:
            data["name_schedule_photo"] = message.text
        await FSM_Admin_create_new_photo_to_schedule.next()
        await message.reply("📷 Добавьте фото календаря через файлы")

    elif message.text.lower() in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            f"{MSG_CANCEL_ACTION}. {MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_schedule_commands,
        )
    else:
        await message.reply(
            MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


async def get_photo_to_schedule(message: types.Message, state: FSMContext):
    if message.content_type == "photo":
        async with state.proxy() as data:
            photo_name = data["name_schedule_photo"]

        with Session(engine) as session:
            new_schedule_photo = SchedulePhoto(
                name=photo_name, photo=message.photo[0].file_id
            )
            session.add(new_schedule_photo)
            session.commit()
            await bot.send_message(message.from_id, MSG_SUCCESS_CHANGING)
            
        await bot.send_message(
            message.from_id,
            f"Отлично! Ты добавила фото календаря! \n\n"
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_schedule_commands,
        )
        
        await state.finish()

    elif message.content_type == "text":
        if message.text in LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(
                MSG_CANCEL_ACTION + MSG_BACK_TO_HOME,
                reply_markup=kb_admin.kb_price_list_commands,
            )


# ------------------------------ ADD_NEW_SCHEDULE_DATE ---------------
class FSM_Admin_create_new_date_to_schedule(StatesGroup):
    event_type_choice = State()
    date_choice = State()
    year_name = State()
    month_name = State()
    day_name = State()
    day_by_date = State()
    start_time_in_schedule = State()
    end_time_in_schedule = State()
    choice_connect_order_to_new_event = State()
    connect_order_to_new_event = State()


# /добавить дату в расписание
async def command_create_new_date_to_schedule(message: types.Message):
    if (
        message.text == "добавить дату в расписание"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_create_new_date_to_schedule.event_type_choice.set()
        # [ 'Хочу ввести конкретную дату', 'Хочу выбрать день недели и месяц']
        await message.reply(
            "🕒 Давай добавим новую дату в расписании.\n\n"
            "❔ Это будет тату работа, коррекция, консультация "
            "или свободное время (для любых видов занятий)?",
            reply_markup=kb_admin.kb_type_of_schedule,
        )


async def choice_event_type_in_schedule(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.schedule_event_type.values()):
        async with state.proxy() as data:
            data["event_type"] = message.text
            data["year_number"] = datetime.now().strftime("%Y")
            data["user_id"] = message.from_user.id
            
        # -> choice_how_to_create_new_date_to_schedule
        await FSM_Admin_create_new_date_to_schedule.next()
        
        # 'Хочу ввести конкретную дату', 'Хочу выбрать день недели и месяц'
        await message.reply(
            f"💭 Выбрано событие как \"{message.text}\".\n"
            "❔ Ввести конкретную дату или выбрать месяц и день недели?",
            reply_markup=kb_admin.kb_new_date_choice,
        )
        await bot.send_message(
            message.from_id,
            MSG_INFO_ADMIN_CREATE_NEW_SCHEDULE_EVENT
        )
        
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_schedule_commands
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# выбираем год или конкретную дату
async def choice_how_to_create_new_date_to_schedule(
    message: types.Message, state: FSMContext
):
    if (
        message.text == kb_admin.new_date_choice["one_date"]
    ):  # Хочу ввести конкретную дату
        for _ in range(4):
            await FSM_Admin_create_new_date_to_schedule.next()  # -> get_day_by_date_for_schedule
        await message.reply(
            "💬 Давай выберем конкретную дату. Введите ее",
            reply_markup=await DialogCalendar().start_calendar(),
        )

    elif (
        message.text == kb_admin.new_date_choice["many_dates"]
    ):  # Хочу выбрать день недели и месяц
        await FSM_Admin_create_new_date_to_schedule.next()  # -> get_schedule_year
        await message.reply(
            "💬 Давай выберем год. Выберите год из списка",
            reply_markup=kb_admin.kb_years.add(kb_client.cancel_btn)
        )
    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


async def get_schedule_year(message: types.Message, state: FSMContext):
    if int(message.text) in kb_admin.years_lst:
        await FSM_Admin_create_new_date_to_schedule.next() # ->get_schedule_month
        async with state.proxy() as data:
            data["year_number"] = message.text

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        name_month_now = await get_month_from_number(int(datetime.now().strftime('%m')), lang='ru')
        kb.add(KeyboardButton(name_month_now))
        
        for month in kb_admin.month:
            month_number = await get_month_number_from_name(month)
            
            if (
                datetime.strptime(
                    f"{message.text}-{month_number}-01 00:00", "%Y-%m-%d %H:%M"
                )
                >= datetime.now()
            ):
                kb.add(KeyboardButton(month))
                
        await message.reply(
            f"💬 Выбран год {message.text}. Давай выберем месяц. Выбери имя месяца из списка",
            reply_markup=kb.add(kb_client.cancel_btn),
        )
    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


# добавляем месяц и выбираем день недели
async def get_schedule_month(message: types.Message, state: FSMContext):
    if message.text in kb_admin.month:
        async with state.proxy() as data:
            data["month_name"] = message.text
            data["month_number"] = await get_month_number_from_name(message.text)

        await FSM_Admin_create_new_date_to_schedule.next()  # -> get_schedule_day
        await message.reply(
            "❔ Какой день недели?", reply_markup=kb_admin.kb_days_for_schedule
        )
    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


# добавляем день недели и выбираем начало рабочего дня
async def get_schedule_day(message: types.Message, state: FSMContext):
    if message.text in kb_admin.days:
        async with state.proxy() as data:
            data["date"] = message.text

        for _ in range(2):
            await FSM_Admin_create_new_date_to_schedule.next() # -> process_hour_timepicker_start_time

        await bot.send_message(
            message.from_user.id,
            f"🕒 Отлично, день недели будет {message.text}. Давай определимся со временем.\n"
            "❔ С какого времени начинается твой рабочее расписание в этот день?",
            reply_markup=await FullTimePicker().start_picker(),
        )

    elif message.text == kb_admin.new_date_choice["one_date"]:
        await FSM_Admin_create_new_date_to_schedule.next()  # -> get_day_by_date_for_schedule
        await bot.send_message(
            message.from_user.id,
            "💬 Выбери конкретную дату",
            reply_markup=await DialogCalendar().start_calendar(),
        )

    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await bot.send_message(
            message.from_user.id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()


@dp.callback_query_handler(
    dialog_cal_callback.filter(),
    state=FSM_Admin_create_new_date_to_schedule.day_by_date,
)
async def get_day_by_date_for_schedule(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    username_id = 0
    async with state.proxy() as data:
        username_id = data["user_id"]

    if selected:
        await callback_query.message.answer(f"Вы выбрали {date}")
        if date > datetime.now():
            # async def load_datemiting(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data["date"] = date  # f'{date.strftime("%d/%m/%Y")}' #  message.text
                data["month_name"] = await get_month_from_number(
                    int(date.strftime("%m")), "ru"
                )
                data["month_number"] = int(date.strftime("%m"))
            await FSM_Admin_create_new_date_to_schedule.next()
            await bot.send_message(
                username_id,
                "🎉 Отлично, давай определимся со временем.\n"
                "❔ С какого времени начинается сеанс?",
                reply_markup=await FullTimePicker().start_picker(),
            )

        else:
            await bot.send_message(
                username_id,
                "Выбери еще раз конкретную дату. '\
                'Дата должна быть позже в этом году, а не раньше.",
                reply_markup=await DialogCalendar().start_calendar(),
            )


# выбираем время начала рабочего дня
@dp.callback_query_handler(
    full_timep_callback.filter(),
    state=FSM_Admin_create_new_date_to_schedule.start_time_in_schedule,
)
async def process_hour_timepicker_start_time(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore
    if r.selected:
        await callback_query.message.edit_text(
            f'Вы выбрали начало рабочего дня в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            username_id = data["user_id"]
            if int(r.time.strftime("%H")) > 8 and int(r.time.strftime("%H")) < 24:
                data["start_time_in_schedule"] = r.time.strftime("%H:%M")
                # -> process_hour_timepicker_end_time
                await FSM_Admin_create_new_date_to_schedule.next()
                await bot.send_message(
                    username_id,
                    "❔ Когда заканчивается сеанс?",
                    reply_markup=await FullTimePicker().start_picker(),
                )

            elif int(r.time.strftime("%H")) < 8:
                await bot.send_message(
                    username_id,
                    "❌ Прости, но ты так рано не работаешь. "
                    "Вряд-ли и ты захочешь работать в 8 утра.\n\n"
                    "💬 Введи другое время",
                    reply_markup=await FullTimePicker().start_picker(),
                )

            elif int(r.time.strftime("%H")) > 23:
                await bot.send_message(
                    username_id,
                    "❌ Прости, но ты так поздно не работаешь. "
                    "Вряд-ли и ты захочешь работать в 23 вечера.\n\n"
                    "💬 Введи другое время",
                    reply_markup=await FullTimePicker().start_picker(),
                )


@dp.callback_query_handler(
    full_timep_callback.filter(),
    state=FSM_Admin_create_new_date_to_schedule.end_time_in_schedule,
)
async def process_hour_timepicker_end_time(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore
    if r.selected:
        new_event_to_schedule_bool = False
        await callback_query.message.edit_text(
            f'Выбран конец рабочего дня в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            username_id = data["user_id"]
            start_time = data["start_time_in_schedule"]
            
            if r.time.strftime("%H:%M") > start_time:
                data["end_time_in_schedule"] = r.time.strftime("%H:%M")
                date, year = data["date"], data["year_number"]
                month_name, month_number = data["month_name"], data["month_number"]
                end_time = data["end_time_in_schedule"]
                month_name_from_number = await get_month_from_number(month_number, "ru")

                if date not in kb_admin.days and month_name_from_number != month_name:
                    # -> get_day_by_date_for_schedule
                    for _ in range(2):
                        await FSM_Admin_create_new_date_to_schedule.previous()  

                    await bot.send_message(
                        username_id,
                        f"❌ Дата {date} и месяц {month_name} не совпадают.\n\n"
                        "💬 Введите месяц и дату в этом месяце корректно",
                        reply_markup=await DialogCalendar().start_calendar(),
                    )
                else:
                    new_event_to_schedule_bool = True

                if new_event_to_schedule_bool:
                    if date not in kb_admin.days:
                        start_datetime = datetime.strptime(
                            f"{date.strftime('%Y-%m-%d')} {start_time}",
                            "%Y-%m-%d %H:%M",
                        )

                        end_datetime = datetime.strptime(
                            f"{date.strftime('%Y-%m-%d')} {r.time.strftime('%H:%M')}",
                            "%Y-%m-%d %H:%M",
                        )
                        
                        data['start_datetime'] = start_datetime
                        data['end_datetime'] = end_datetime

                        with Session(engine) as session:
                            """ 
                                Проверяем, нет ли в расписании такой даты
                                с таким же статусом, временем и тд
                                для этого достаем календарь из бд
                                а ниже делаем проверку
                            """
                            schedule = session.scalars(select(ScheduleCalendar)
                                .where(ScheduleCalendar.start_datetime == start_datetime)
                                .where(ScheduleCalendar.end_datetime == end_datetime)
                            ).all()
                            
                            orders = session.scalars(select(Orders)
                                .where(Orders.order_type.in_([
                                    kb_admin.price_lst_types["constant_tattoo"],
                                    kb_admin.price_lst_types["shifting_tattoo"],
                                    kb_admin.price_lst_types["sketch"]
                                ]))
                            ).all()
                            
                            # если дата не в бд
                            if schedule == []:
                                new_schedule_event = ScheduleCalendar(
                                    start_datetime=start_datetime,
                                    end_datetime=end_datetime,
                                    status=kb_admin.schedule_event_status['free'],
                                    event_type=data["event_type"],
                                )
                                session.add(new_schedule_event)
                                session.commit()
                                
                                await bot.send_message(username_id, MSG_SUCCESS_CHANGING)
                                await bot.send_message(
                                    username_id,
                                    f"🎉 Отлично, теперь в {month_name} в {date.strftime('%d/%m/%Y')}"
                                    f" c {start_time} "
                                    f"по {end_time} у тебя рабочее время!",
                                )
                                
                                if orders == []:
                                    await state.finish()
                                    
                                # Если есть заказы, предлагаем назначить на это время заказ
                                else:
                                    # -> choice_order_to_schedule_event
                                    await FSM_Admin_create_new_date_to_schedule.next()
                                    await bot.send_message(
                                        username_id,
                                        "❔ Добавить к этому сеансу заказ?",
                                        reply_markup=kb_client.kb_yes_no
                                    )
                                
                            else:
                                await bot.send_message(
                                    username_id,
                                    f"❌ Дата {date.strftime('%d/%m/%Y')} с {start_time} по "
                                    f"{r.time.strftime('%H:%M')} уже занята.\n\n"
                                    "❕ Выберите новое время окончания сеанса",
                                    reply_markup=await FullTimePicker().start_picker(),
                                )
                                
                    # если добавляется множество дат
                    else:
                        
                        """ записываем все даты выбранного месяца и года  """
                        dates = await get_dates_from_month_and_day_of_week(
                            date, month_name, year, start_time, end_time
                        )
                        
                        """ определяем переменную для вывода списка дат """
                        no_added_dates = False
                        dates_str, dates_not_added  = ("", "")
                        for iter_date in dates:
                            with Session(engine) as session:
                                schedule = session.scalars(select(ScheduleCalendar)
                                    .where(ScheduleCalendar.start_datetime==iter_date["start_datetime"])
                                    .where(ScheduleCalendar.end_datetime==iter_date["end_datetime"])
                                ).all()
                                
                                """ Делаем проверку на наличие даты в бд """
                                if schedule == []:
                                    new_schedule_event = ScheduleCalendar(
                                        start_datetime=iter_date["start_datetime"],
                                        end_datetime=iter_date["end_datetime"],
                                        status=kb_admin.schedule_event_status['free'],
                                        event_type=data["event_type"],
                                    )
                                    session.add(new_schedule_event)
                                    session.commit()
                                    dates_str += (
                                        f"{iter_date['start_datetime'].strftime('%d/%m/%Y')}, "
                                    )
                                else:
                                    no_added_dates = True
                                    dates_not_added += (
                                        f"{iter_date['start_datetime'].strftime('%d/%m/%Y')}, "
                                    )
                            
                        await bot.send_message(username_id, MSG_SUCCESS_CHANGING)
                        msg = ""
                        if len(dates_str) == 0:
                            msg += "❗️ Все даты были дубликатами!\n\n"
                            
                        else:
                            msg += (
                                f"🎉 Отлично, теперь в {month_name} во все эти даты ({date}: "
                                f"{dates_str[:len(dates_str)-2]})"
                                f" c {start_time} по {end_time} у тебя рабочее время!\n\n"
                            )
                            
                        if no_added_dates:
                            msg += (
                                "❗️ Даты, которые не были добавлены, т.к. были дубликатами:"
                                f"({dates_not_added[:len(dates_str)-2]})"
                            )
                        
                        await bot.send_message(
                            username_id,
                            msg,
                            reply_markup=kb_admin.kb_schedule_commands,
                        )
                        await state.finish()
            else:
                await bot.send_message(
                    username_id,
                    f"❌ Время окончания работы должно быть позже времени начала работ."
                    " Введи время заново",
                    reply_markup=await FullTimePicker().start_picker(),
                )


async def choice_order_to_schedule_event(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        with Session(engine) as session:
            orders = session.scalars(select(Orders)
                .where(Orders.order_type.in_([
                    kb_admin.price_lst_types["constant_tattoo"],
                    kb_admin.price_lst_types["shifting_tattoo"],
                    kb_admin.price_lst_types["sketch"]
                ]))
            ).all()
            
        kb = ReplyKeyboardMarkup(resize_keyboard=True) 
        order_lst = []
        msg_order = '' 
        for number, order in enumerate(orders):
            item = f"№{order.order_number} {order.order_type} {order.order_state}"
            order_lst.append(item)
            msg_order += f"{number}) {item} {order.order_name}\n"
            kb.add(KeyboardButton(item))
        
        kb.add(kb_admin.cancel_btn)
        
        async with state.proxy() as data:
            data['order_lst'] = order_lst
            
        await bot.send_message(message.from_id, f"📃 Список заказов: {msg_order}")
        
        await bot.send_message(
            message.from_id,
            "❔ Какой заказ привязать к созданной дате?",
            reply_markup= kb
        )
        
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS + [kb_client.no_str]:
        await bot.send_message(
            message.from_user.id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()
        
    else:
        await bot.send_message(
            message.from_user.id,
            MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST,
        )


async def get_order_number_to_connect_with_new_event(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        order_lst = data['order_lst']
        start_datetime = data['start_datetime']
        end_datetime = data['end_datetime']
    
    if message.text in order_lst:
        order_number = message.text.split()[0][1:]
        with Session(engine) as session:
            order = session.scalars(select(Orders)
                .where(Orders.order_number == order_number)
            ).one()
            
            schedule_new_event = session.scalars(select(ScheduleCalendar)
                .where(ScheduleCalendar.start_datetime == start_datetime)
                .where(ScheduleCalendar.end_datetime == end_datetime)
            ).one()
            
            new_order_schedule_event = ScheduleCalendarItems(
                order_number = order_number,
                order_id= order.id,
                schedule_mapped_id= schedule_new_event.id
            )
            
            session.add(new_order_schedule_event)
            schedule_new_event.status = kb_admin.schedule_event_status['busy']
            session.commit()
        
        await bot.send_message(message.from_id, MSG_SUCCESS_CHANGING)
        
        await bot.send_message(
            message.from_id,
            f"🎉 Отлично, заказ под номером {order_number} успешно привязан!\n\n"
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup= kb_admin.kb_schedule_commands
        )
        await state.finish()
        
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await bot.send_message(
            message.from_user.id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_tattoo_order_commands,
        )
        await state.finish()
        
    else:
        await bot.send_message(
            message.from_user.id,
            MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST,
        )
    
    

# ------------------------------------------ VIEW SCHEDULE-----------------------------------
async def get_view_schedule(user_id: int, schedule: ScalarResult[ScheduleCalendar]):
    if schedule == []:
        await bot.send_message(
            user_id, f"{MSG_NO_SCHEDULE_IN_TABLE_IN_STATUS}\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}"
        )
    else:
        headers = [
            "N",
            "Месяц",
            "Дата",
            "Начало",
            "Конец",
            "Статус",
            "Тип",
            "Заказы",
        ]
        # Определяем таблицу
        table = PrettyTable(
            headers, left_padding_width=0, right_padding_width=0
        ) 
        # Определяем конфигурацию
        with open("config.json", "r") as config_file:
            data = json.load(config_file)
            
        if data['mode'] == 'pc':
            for number, date in enumerate(schedule):
                order_number = ""
                with Session(engine) as session:
                    # выбираем заказы 
                    orders = session.scalars(
                        select(Orders)
                        .join(ScheduleCalendarItems)
                        .where(ScheduleCalendarItems.schedule_id == date.id)
                    ).all()

                if orders != []:
                    order_number += f"{orders[0].order_number}"
                else:
                    order_number = "---"
                    
                table.add_row(
                    [
                        number + 1,
                        await get_month_from_number(
                            int(date.start_datetime.strftime("%m")), "ru"
                        ),
                        date.start_datetime.strftime("%d/%m/%Y"),
                        date.start_datetime.strftime("%H:%M"),
                        date.end_datetime.strftime("%H:%M"),
                        date.status,
                        date.event_type,
                        order_number,
                    ]
                )

            await bot.send_message(
                user_id, f"<pre>{table}</pre>", parse_mode=types.ParseMode.HTML
            )
            
        elif data['mode'] == 'phone':
            msg = "📃 Календарь:\n"
            for number, date in enumerate(schedule):
                order_number = ""
                with Session(engine) as session:
                    # необходимо ввыбрать заказы в данных
                    orders = session.scalars(
                        select(Orders)
                        .join(ScheduleCalendarItems)
                        .where(ScheduleCalendarItems.schedule_id == date.id)
                    ).all()

                if orders != []:
                    order_number += f"{orders[0].order_number}"
                else:
                    order_number = "Нет заказов"
                    
                month = await get_month_from_number(
                    int(date.start_datetime.strftime("%m")), "ru"
                )
                msg += (
                    f"№{number + 1}\n"
                    f"- {headers[1]}: {month}\n"
                    f"- {headers[2]}: {date.start_datetime.strftime('%d/%m/%Y')}\n"
                    f"- {headers[3]}: {date.start_datetime.strftime('%H:%M')}\n"
                    f"- {headers[4]}: {date.end_datetime.strftime('%H:%M')}\n"
                    f"- {headers[5]}: {date.status}\n"
                    f"- {headers[6]}: {date.event_type}\n"
                    f"- {headers[7]}: {order_number}\n\n"
                )
            await bot.send_message(user_id, msg)
            
        # table = PrettyTable(headers, left_padding_width = 0, right_padding_width=0)


# /посмотреть_мое_расписание
async def command_view_schedule(message: types.Message):
    if (
        message.text == "посмотреть мое расписание"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            schedule = session.scalars(
                select(ScheduleCalendar).order_by(ScheduleCalendar.start_datetime)
            ).all()
        await get_view_schedule(message.from_user.id, schedule)
        # events = await obj.get_calendar_events(CALENDAR_ID)

        """
        {
            'kind': 'calendar#events',
            'etag': '"p33gfhjkohjpfo0g"', 
            'summary': 'pmorgukyan@gmail.com',
            'updated': '2023-01-31T15:12:37.244Z',
            'timeZone': 'Europe/Moscow',
            'accessRole': 'owner',
            'defaultReminders': [],
            'nextSyncToken': 'COD4zpiM8vwCEOD4zpiM8vwCGAUghfra8AE=', 

            'items': 
            [
                {
                    'kind': 'calendar#event',
                    'etag': '"3350355914488000"', 
                    'id': 'e2oqiqj12cmtc2o43ko9483vmo', !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                    'status': 'confirmed', 
                    'htmlLink': 'https://www.google.com/calendar/event?eid=ZTJvcWlxajEyY210YzJvNDNrbzk0ODN2bW8gcG1vcmd1a3lhbkBt',
                    'created': '2023-01-31T15:12:37.000Z',
                    'updated': '2023-01-31T15:12:37.244Z', 
                    'summary': 'Новый тату заказ', 
                    'description': 'Классное тату', 
                    'location': 'Москва', 
                    'creator': 
                        {'email': 'dara-service-account-google-ca@quantum-studio-335116.iam.gserviceaccount.com'},
                    'organizer': {'email': 'pmorgukyan@gmail.com', 'self': True},
                    'start': {'dateTime': '2023-02-06T18:00:00+03:00', 'timeZone': 'Europe/Moscow'},
                    'end': {'dateTime': '2023-02-06T20:00:00+03:00', 'timeZone': 'Europe/Moscow'},
                    'iCalUID': 'e2oqiqj12cmtc2o43ko9483vmo@google.com', 'sequence': 0,
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 1440},
                            {'method': 'popup', 'minutes': 10}
                        ]
                    }, 
                    'eventType': 'default'
                }
            ]
        }
        """

        # for event in events['items']:
        #    print(event['summary'])


# /посмотреть_мое_занятое_расписание
async def command_view_busy_schedule(message: types.Message):
    if (
        message.text == "посмотреть мое занятое расписание"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            schedule = session.scalars(
                select(ScheduleCalendar)
                .where(ScheduleCalendar.status == kb_admin.schedule_event_status['busy'])
                .order_by(ScheduleCalendar.start_datetime)
            ).all()
        await get_view_schedule(message.from_user.id, schedule)


# /посмотреть мое свободное расписание
async def command_view_opened_schedule(message: types.Message):
    if (
        message.text == "посмотреть мое свободное расписание"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        schedule = (
            Session(engine)
            .scalars(
                select(ScheduleCalendar)
                .where(ScheduleCalendar.status == kb_admin.schedule_event_status['free'])
                .order_by(ScheduleCalendar.start_datetime)
            )
            .all()
        )
        await get_view_schedule(message.from_user.id, schedule)


# ---------------------------------------- VIEW_ALL_PHOTOS_SCHEDULE--------------------------
# /посмотреть_фотографии_расписания
async def command_get_view_photos_schedule(message: types.Message):
    if (
        message.text.lower()
        in ["/посмотреть_фотографии_расписания", "посмотреть фотографии расписания"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            photos_schedule = session.scalars(select(SchedulePhoto)).all()
        if photos_schedule == []:
            await bot.send_message(message.from_id, MSG_NO_SCHEDULE_PHOTO_IN_TABLE)
            await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        else:
            for photo in photos_schedule:
                await bot.send_photo(
                    message.chat.id,
                    photo.photo,
                    f"Название фотографии календаря: 0{photo.name}",
                )
            await message.reply(MSG_DO_CLIENT_WANT_TO_DO_MORE)


# ----------------------------------------- VIEW_PHOTO_SCHEDULE------------------------------
class FSM_Admin_get_view_schedule_photo(StatesGroup):
    schedule_photo_name = State()


# /посмотреть_одну_фотографию_расписания
async def command_get_view_photo_schedule(message: types.Message):
    if (
        message.text.lower()
        in ["/посмотреть_фотографии_расписания", "посмотреть фотографию расписания"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            photos_schedule = session.scalars(select(SchedulePhoto)).all()

        kb_photos_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
        if photos_schedule == []:
            await bot.send_message(
                message.from_id,
                f"{MSG_NO_SCHEDULE_PHOTO_IN_TABLE}\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_schedule_commands
            )
        else:
            for photo in photos_schedule:
                kb_photos_schedule.add(KeyboardButton(photo.name))
            kb_photos_schedule.add(kb_client.cancel_btn)
            await FSM_Admin_get_view_schedule_photo.schedule_photo_name.set()
            await message.reply(
                f"❔ Какую фотографию посмотреть?", reply_markup=kb_photos_schedule
            )


async def get_schedule_photo_to_view(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        photos_schedule = session.scalars(select(SchedulePhoto)).all()
    photo_names_list = []
    for photo in photos_schedule:
        photo_names_list.append(photo.name)

    if message.text in photo_names_list:
        with Session(engine) as session:
            photos_schedule = session.scalars(
                select(SchedulePhoto).where(SchedulePhoto.name == message.text)
            ).one()

        await bot.send_photo(
            message.chat.id, photo.photo, f"Название фотографии календаря: {photo.name}"
        )
        await message.reply(
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}", reply_markup=kb_admin.kb_schedule_commands
        )
        await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await message.reply(
            f"{MSG_BACK_TO_HOME}",
            reply_markup=kb_admin.kb_schedule_commands,
        )
        await state.finish()
    else:
        await message.reply(
            MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


# -------------------------------------- DELETE PHOTO SCHEDULE-----------------------------------
class FSM_Admin_delete_schedule_photo(StatesGroup):
    schedule_photo_name = State()


# /удалить_фото_расписания
async def delete_photo_schedule(message: types.Message):
    if (
        message.text.lower() in ["/удалить_фото_расписания", "удалить фото расписания"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            photos_schedule = session.scalars(select(SchedulePhoto)).all()

        if photos_schedule == []:
            await bot.send_message(message.from_id, MSG_NO_SCHEDULE_PHOTO_IN_TABLE)
            await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
            
        else:
            kb_photos_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            for photo in photos_schedule:
                kb_photos_schedule.add(KeyboardButton(photo.name))
                await bot.send_photo(
                    message.chat.id,
                    photo.photo,
                    f"Название фотографии календаря: {photo.name}",
                )
            kb_photos_schedule.add(kb_client.cancel_btn)
            await FSM_Admin_delete_schedule_photo.schedule_photo_name.set()
            await message.reply(
                "❔ Какое фото удалить?", reply_markup=kb_photos_schedule
            )


async def get_schedule_photo_to_delete(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        photos_schedule = session.scalars(select(SchedulePhoto)).all()
    photo_names_list = []
    for photo in photos_schedule:
        photo_names_list.append(photo.name)

    if message.text in photo_names_list:
        with Session(engine) as session:
            photo = session.scalars(
                select(SchedulePhoto).where(SchedulePhoto.name == message.text)
            ).one()
            session.delete(photo)
            session.commit()
        await bot.send_message(message.from_id, MSG_SUCCESS_CHANGING)
        await message.reply(
            f'Фото "0{message.text}" удалено из расписания.\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup=kb_admin.kb_schedule_commands,
        )
        await state.finish()

    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await message.reply(
            f"{MSG_BACK_TO_HOME}",
            reply_markup=kb_admin.kb_schedule_commands,
        )
        await state.finish()

    else:
        await message.reply(
            MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


# --------------------------------------------CHANGE SCHEDULE-----------------------------------
class FSM_Admin_change_schedule(StatesGroup):
    event_name = State()
    event_change = State()
    start_time_in_schedule = State()
    month_or_day_get_name_for_new_state_schedule = State()

    get_answer_choice_new_date_or_no_date_in_tattoo_order = State()
    get_new_date_for_tattoo_order = State()
    start_time_in_tattoo_order = State()
    end_time_in_tattoo_order = State()

    get_anwser_to_notify_client = State()
    # get_new_day_name_if_month_is_not_succsess = State()


# /изменить_мое_расписание, изменить мое расписание
async def command_change_schedule(message: types.Message):  # state=None
    if (
        message.text == "изменить мое расписание"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            schedule = session.scalars(select(ScheduleCalendar)
                .order_by(ScheduleCalendar.start_datetime)
            ).all()
        if schedule == []:
            await bot.send_message(message.from_id, MSG_NO_SCHEDULE_IN_TABLE)
            await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
                reply_markup=kb_admin.kb_schedule_commands,
            )
            
        else:
            kb_date_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            for i, date in enumerate(schedule):
                kb_date_schedule.add(KeyboardButton(str(i + 1)))
            kb_date_schedule.add(kb_admin.home_btn)
            
            await get_view_schedule(message.from_id, schedule)
            
            await FSM_Admin_change_schedule.event_name.set()  # event_name, -> get_event_date
            await bot.send_message(
                message.from_id,
                "❔ Какой сеанс изменить? Выберите номер из вышепредставленного списка",
                reply_markup=kb_date_schedule,
            )


async def get_event_date(
    message: types.Message, state: FSMContext
):  # state=FSM_Admin_change_schedule.event_name
    with Session(engine) as session:
        schedule_lst = session.scalars(select(ScheduleCalendar)
            .order_by(ScheduleCalendar.start_datetime)
        ).all()

    if message.text.isdigit():
        if int(message.text) in range(len(schedule_lst)):
            date = schedule_lst[int(message.text)-1]
            await message.reply(
                (
                    f"Вы выбрали {date.start_datetime.strftime('%d/%m/%Y %H:%M')} - "
                    f"{date.end_datetime.strftime('%H:%M')}, "
                    f"статус: {date.status}, "
                    f"тип: {date.event_type}"
                )
            )
            
            async with state.proxy() as data:
                data["schedule_id"] = date.id
                data["user_id"] = message.from_user.id
                
                data["event_date_old"] = {
                    "date": date.start_datetime.strftime('%d/%m/%Y'),
                    "start_time": date.start_datetime.strftime('%H:%M'),
                    "end_time":date.end_datetime.strftime('%H:%M'),
                    "status": date.status,
                    "type":date.event_type
                }
            await FSM_Admin_change_schedule.next() #-> get_new_state_event_in_schedule
            # ['Время начала работы', 'Время окончания работы', 'Дату', 'Статус', 'Тип']
            await message.reply(
                f"❔ Что изменить?", reply_markup=kb_admin.kb_date_states
            )

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_schedule_commands
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def update_schedule_table(state: FSMContext):
    async with state.proxy() as data:
        username_id = data["user_id"]
        schedule_id = data["schedule_id"]
        event_date_old = data["event_date_old"]

    with Session(engine) as session:
        new_date = session.get(ScheduleCalendar, schedule_id)

    old_data_to_send = {
        "id":           new_date.id,
        "date":         event_date_old["date"],
        "start_time":   event_date_old["start_time"],
        "end_time":     event_date_old["end_time"],
        "status":       event_date_old["status"],
        "type":         event_date_old["type"],
    }

    new_data_to_send = {
        "id":           new_date.id,
        "date":         new_date.start_datetime.strftime("%d/%m/%Y"),
        "start_time":   new_date.start_datetime.strftime("%H:%M"),
        "end_time":     new_date.end_datetime.strftime("%H:%M"),
        "status":       new_date.status,
        "type":         new_date.event_type,
    }
    
    with open("config.json", "r") as config_file:
        data = json.load(config_file)
        
    if data['mode'] == "pc":
        headers = ["N", "Дата", "Начало", "Конец", "Статус", "Тип"]
        table = PrettyTable(
            headers, left_padding_width=1, right_padding_width=1
        )  # Определяем таблицу
        table.add_row(list(old_data_to_send.values()))
        await bot.send_message(
            username_id, f"<pre>{table}</pre>", parse_mode=types.ParseMode.HTML
        )
        await bot.send_message(username_id, "➡️ Дата и время изменились на:")
        
        table_next = PrettyTable(headers, left_padding_width=1, right_padding_width=1)
        table_next.add_row(list(new_data_to_send.values()))
        await bot.send_message(
            username_id, f"<pre>{table_next}</pre>", parse_mode=types.ParseMode.HTML
        )
    
    else:
        await bot.send_message(
            username_id, 
            "🕒 Старая дата:\n"
            f"- Дата: {old_data_to_send['date']}\n"
            f"- Начало: {old_data_to_send['start_time']}\n"
            f"- Конец: {old_data_to_send['end_time']}\n"
            f"- Статус: {old_data_to_send['status']}\n"
            f"- Тип: {old_data_to_send['type']}"
        )
        await bot.send_message(username_id, "➡️ Дата и время изменились на:")
        await bot.send_message(
            username_id, 
            "🕒 Новая дата:\n"
            f"- Дата: {new_data_to_send['date']}\n"
            f"- Начало: {new_data_to_send['start_time']}\n"
            f"- Конец: {new_data_to_send['end_time']}\n"
            f"- Статус: {new_data_to_send['status']}\n"
            f"- Тип: {new_data_to_send['type']}\n"
        )
        
    await bot.send_message(
        username_id, 
        MSG_DO_CLIENT_WANT_TO_DO_MORE, 
        reply_markup=kb_admin.kb_schedule_commands
    )


# state - FSM_Admin_change_schedule.event_change
async def get_new_state_event_in_schedule(message: types.Message, state: FSMContext):
    if message.text in kb_admin.date_states:
        async with state.proxy() as data:
            data["new_event_date_state"] = message.text
            data["new_date_tattoo_order"] = False

        if message.text == "Дату":
            for _ in range(3):
                await FSM_Admin_change_schedule.next()  # -> get_changing_day_by_date_for_schedule
            await message.reply(
                "💬 Выберите конкретную дату",
                reply_markup=await DialogCalendar().start_calendar(),
            )

        elif message.text == "Время начала работы":
            await FSM_Admin_change_schedule.next() #-> process_hour_timepicker_start_or_end_time
            await message.reply(
                "💬 Выберите новое время начала работы",
                reply_markup=await FullTimePicker().start_picker(),
            )

        elif message.text == "Время окончания работы":
            await FSM_Admin_change_schedule.next() #-> process_hour_timepicker_start_or_end_time
            await message.reply(
                "💬 Выберите новое время окончания работы",
                reply_markup=await FullTimePicker().start_picker(),
            )

        # TODO При изменении статуса нужно проверять,
        # есть ли какой-либо заказ в это время, 
        # и менять дату расписания для заказа + оповещать пользователя
        elif message.text == "Статус":
            for _ in range(2):
                await FSM_Admin_change_schedule.next()  # -> set_new_state_event_in_schedule

            await message.reply(
                "💬 Выберите новый статус сеанса",
                reply_markup=kb_admin.kb_free_or_close_event_in_schedule,
            )

        elif message.text == "Тип":
            await message.reply(
                "💬 Выберите новый тип даты календаря",
                reply_markup=kb_admin.kb_type_of_schedule,
            )

        elif message.text in list(kb_admin.schedule_event_type.values()):
            async with state.proxy() as data:
                schedule_id = data["schedule_id"]

            with Session(engine) as session:
                schedule_event = session.get(ScheduleCalendar, schedule_id)
                schedule_event.event_type = message.text.lower()
                session.commit()
            await bot.send_message(message.from_id, MSG_SUCCESS_CHANGING)
            await update_schedule_table(state)
            await bot.send_message(
                message.from_id,
                MSG_DO_CLIENT_WANT_TO_DO_MORE,
                reply_markup=kb_admin.kb_schedule_commands,
            )
            await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_schedule_commands
        )

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# выбираем новое время начала или конца рабочего дня
@dp.callback_query_handler(
    full_timep_callback.filter(), state=FSM_Admin_change_schedule.start_time_in_schedule
)
async def process_hour_timepicker_start_or_end_time(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore
    if r.selected:
        await callback_query.message.edit_text(
            f'🕒 Выбрано время {r.time.strftime("%H:%M")} ',
        )
        async with state.proxy() as data:
            user_id = data['user_id']
            schedule_id = data["schedule_id"]
            new_event_date_state = data["new_event_date_state"]

        with Session(engine) as session:
            schedule_event = session.get(ScheduleCalendar, schedule_id)
            new_time = datetime.strptime(
                f"{schedule_event.start_datetime.strftime('%Y-%m-%d')} "
                f"{r.time.strftime('%H:%M')}",
                "%Y-%m-%d %H:%M",
            )
            
            if new_event_date_state == "Время начала работы":
                schedule_event.start_datetime = new_time
                
            else:
                schedule_event.end_datetime = new_time
                
            session.commit()
        await bot.send_message(user_id, MSG_SUCCESS_CHANGING)
        await update_schedule_table(state)
        await state.finish()


# Выставляем новый статус у сеанса
# state=FSM_Admin_change_schedule.month_or_day_get_name_for_new_state_schedule)
async def set_new_state_event_in_schedule(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(
                Orders.order_state.in_([STATES["closed"]["postponed"], STATES["open"]])
            )
            .where(Orders.schedule_id == None)
            .where(Orders.order_type == kb_admin.price_lst_types['constant_tattoo'])
        ).all()

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    order_kb_lst = []
    for order in orders:
        item_str = f"{order.order_number} {order.order_name} {order.order_state}"
        kb.add(KeyboardButton(item_str))
        order_kb_lst.append(item_str)

    # если меняем статус
    # {"free" : "Свободен", "busy":  "Занят", "close": "Закрыт"}
    if message.text in list(kb_admin.schedule_event_status.values()):
        async with state.proxy() as data:
            schedule_id = data["schedule_id"]
            data["new_schedule_state"] = message.text
            new_schedule_state = message.text
        # Ищем в бд заказ, который связан с этим ивентом
        with Session(engine) as session:
            schedule = session.get(ScheduleCalendar, schedule_id)
            
            tattoo_order = session.scalars(
                select(ScheduleCalendarItems)
                .where(ScheduleCalendarItems.order_id == schedule.id)
            ).all()
            
        if tattoo_order != []:
            order = session.scalars(select(Orders)
                .where(Orders.order_number == tattoo_order[0].order_number)).one()
            
            async with state.proxy() as data:
                data["order_id"] = order.id
                data["tattoo_order_number"] = order.order_number
                
                
                with Session(engine) as session:
                    
                    start_date_meeting = session.get(
                        ScheduleCalendar, schedule_id
                    ).start_datetime
                    
                    end_date_meeting = session.get(
                        ScheduleCalendar, schedule_id
                    ).end_datetime

                data["tattoo_order_start_date_meeting"] = start_date_meeting
                data["tattoo_order_end_date_meeting"] = end_date_meeting

                data["client_id"] = order.user_id
                data["client_name"] = order.username
                old_schedule_state = data["event_date_old"]['status']

            await bot.send_message(
                message.from_id,
                f"С этим расписанием у вас связан тату заказ. "
                'Если читаешь это сообщение в первый раз, то нажми кнопку \
                    "Информация об изменении статусов календаря"',
            )

            if (
                    old_schedule_state in [
                        kb_admin.schedule_event_status['busy'],
                        kb_admin.schedule_event_status['close']
                    ]
                    and new_schedule_state == kb_admin.schedule_event_status['free']
                ):
                
                # -> get_answer_choice_new_date_or_no_date_in_tattoo_order
                await FSM_Admin_change_schedule.next()  

                # 'Хочу поставить новую дату для этого тату заказа',
                # 'Хочу оставить дату для этого тату заказа неопределенной',
                # "Просто изменить статус календаря"
                # 'Информация об изменении статусов календаря'
                await bot.send_message(
                    message.from_id,
                    "❔ Изменить изменить дату встречи, или поставить "
                    "неизвестную дату встречи на этот заказ?\n\n"
                    "❔ Или просто изменить статус сеанса?",
                    reply_markup=kb_admin.kb_choice_new_date_or_no_date_in_tattoo_order,
                )
            elif old_schedule_state == kb_admin.schedule_event_status['free'] and \
                new_schedule_state == kb_admin.schedule_event_status['busy']:
                    await bot.send_message(
                        message.from_id,
                        "❔ Точно хотите закрыть данный сеанс?",
                        reply_markup= kb_admin.kb_admin_choice_close_or_not_opened_schedule_event
                    )

            elif old_schedule_state == kb_admin.schedule_event_status['free'] and \
                new_schedule_state == kb_admin.schedule_event_status['busy']:
                # "Добавить самому новый заказ в этот календарный день",
                # "Выбрать из тех заказов, у которых нет даты сеанса",
                # "Оставить данный календарный день занятым без заказов"
                await message.reply(
                    "❔ Какое действие хочешь выбрать?",
                    reply_markup=kb_admin.admin_choice_get_new_order_to_schedule_event,
                )
                
            # если статусы равны
            elif old_schedule_state == new_schedule_state:
                await message.reply(
                    "Выбран такой же статус календаря. Пожалуйста, введи другой статус",
                    reply_markup=kb_admin.kb_free_or_close_event_in_schedule,
                )
                
        else:
            await update_schedule_table(state)
            await state.finish()

    # "Добавить самому новый заказ в этот календарный день".
    # Если статус календаря меняется со Свободен на занят
    # -> если админ хочет добавить в пустой заказ новый ивент календаря из уже созданных в бд
    elif (
        message.text
        == kb_admin.admin_choice_get_new_order_to_schedule_event["new_order"]
    ):
        async with state.proxy() as data:
            schedule_id = data["schedule_id"]
            new_schedule_state = data["new_schedule_state"]

        # меняем статус календаря
        with Session(engine) as session:
            schedule_event = session.get(ScheduleCalendar, schedule_id)
            schedule_event.status = new_schedule_state
            session.commit()
        await message.reply(MSG_SUCCESS_CHANGING)
        await FSM_Admin_tattoo_order.get_tattoo_type.set()
        await bot.send_message(
            message.from_id,
            "Привет, админ. Сейчас будет создан тату заказ. "
            "Тату заказ будет для переводного тату или для постоянного?",
            reply_markup=kb_client.kb_client_choice_main_or_temporary_tattoo,
        )

    # "Выбрать из тех заказов, у которых нет даты сеанса" -> выдает список заказов без расписания
    # Если статус календаря меняется со Свободен на занят
    elif (
        message.text
        == kb_admin.admin_choice_get_new_order_to_schedule_event["choice_created_order"]
    ):
        await bot.send_message(
            message.from_id, "Какой заказ хочешь выбрать?", reply_markup=kb
        )

    # Если статус календаря меняется со Свободен на занят -> просто меняем статус
    elif (
        message.text
        == kb_admin.admin_choice_get_new_order_to_schedule_event["no_order"]
    ):
        async with state.proxy() as data:
            schedule_id = data["schedule_id"]
            new_schedule_state = data["new_schedule_state"]

        # меняем статус календаря
        with Session(engine) as session:
            schedule_event = session.get(ScheduleCalendar, schedule_id)
            schedule_event.status = new_schedule_state
            session.commit()
        await message.reply(MSG_SUCCESS_CHANGING)
        await update_schedule_table(state)
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_schedule_commands,
        )

    # Если статус календаря меняется со Свободен на занят
    # если админ хочет добавить в пустой заказ новый ивент календаря из уже созданных в бд
    elif message.text in order_kb_lst:
        async with state.proxy() as data:
            schedule_id = data["schedule_id"]
            data["notify_type"] = "new_date_from_schedule_with_no_old_schedule"

        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(Orders.order_number == message.text.split()[0])
            ).one()
            schedule = session.get(ScheduleCalendar, schedule_id)
            order.schedule_id = schedule.id

            if order.order_state == STATES["closed"]["postponed"]: # Отложен
                order.order_state = STATES["open"]  # Открыт
            session.commit()
        await message.reply(MSG_SUCCESS_CHANGING)
        await update_schedule_table(state)
        
        await bot.send_message(
            message.from_id,
            MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
            reply_markup=kb_client.kb_yes_no,
        )

    # Если статус календаря меняется со Свободен на закрыт
    # админ хочет закрыть сеанс
    elif message.text == kb_admin.admin_choice_close_or_not_opened_schedule_event['close']:
        async with state.proxy() as data:
            schedule_id = data["schedule_id"]
        with Session(engine) as session:
            schedule = session.get(ScheduleCalendar, schedule_id)
            schedule.status = kb_admin.schedule_event_status['close']
            session.commit()
        await message.reply(MSG_SUCCESS_CHANGING)
        await update_schedule_table(state)
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_schedule_commands,
        )
    # TODO message.text == kb_admin.admin_choice_close_or_not_opened_schedule_event['dont_close']:
    # "Не закрывать сеанс"
    
    
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_answer_choice_new_date_or_no_date_in_tattoo_order(
    message: types.Message, state: FSMContext
):
    with Session(engine) as session:
        schedule_events = session.scalars(
            select(ScheduleCalendar).where(ScheduleCalendar.status.in_(
                    [kb_admin.schedule_event_status['free']]
                )
            )
        ).all()
    
    schedule_events_kb_lst = []
    for event in schedule_events:
        schedule_events_kb_lst.append(
            f"{event.start_datetime.strftime('%d/%m/%Y с %H:%M')} по \
            {event.end_datetime.strftime('%H:%M')}"
        )

    # 'Хочу поставить новую дату для этого тату заказа'
    if message.text == kb_admin.choice_new_date_or_no_date_in_tattoo_order["new_date"]:
        await bot.send_message(
            message.from_id,
            "❔ Выбрать из календаря или создать новый день в расписании?",
            reply_markup=kb_admin.admin_choice_create_new_or_created_schedule_item,
        )

    # "Создать новое расписание"
    elif (
        message.text
        == kb_admin.admin_choice_create_new_or_created_schedule_item[
            "create_new_schedule"
        ]
    ):
        async with state.proxy() as data:
            data["new_date_tattoo_order"] = True
        await FSM_Admin_change_schedule.next()  # -> process_get_new_date_for_new_data_schedule
        await message.reply(
            f"💬 Введи новую дату для тату заказа",
            reply_markup=await DialogCalendar().start_calendar(),
        )

    elif message.text in schedule_events_kb_lst:
        async with state.proxy() as data:
            data["user_id"] = message.from_user.id
            order_id = data["order_id"]
            tattoo_order_number = data["tattoo_order_number"]
            client_id = data["client_id"]
            data["notify_type"] = "new_date_from_schedule"

            with Session(engine) as session:
                tattoo_order = session.get(Orders, order_id)
                tattoo_order.schedule_id = (
                    session.scalars(
                        select(ScheduleCalendar).where(
                            ScheduleCalendar.start_datetime
                            == datetime.strptime(
                                f"{message.text.split()[0]} c {message.text.split()[2]}",
                                "%d/%m/%Y с %H:%M",
                            )
                        )
                    )
                    .one()
                    .id
                )
                session.commit()
            await message.reply(MSG_SUCCESS_CHANGING)

            async with state.proxy() as data:
                data["new_start_date"] = message.text.split()[0]  # %d/%m/%Y
                data["new_start_time"] = message.text.split()[2]  # %H:%M
                data["new_end_time"] =   message.text.split()[4]  # %H:%M

            await bot.send_message(
                message.from_id,
                MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
                reply_markup=kb_client.kb_yes_no,
            )

    elif (
        message.text
        == kb_admin.admin_choice_create_new_or_created_schedule_item[
            "choice_created_schedule"
        ]
    ):
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for event in schedule_events_kb_lst:
            kb.add(KeyboardButton(event))
        await bot.send_message(
            message.from_id, "❔ Какой день выбираешь?", reply_markup=kb
        )

    elif message.text == kb_admin.choice_new_date_or_no_date_in_tattoo_order["info"]:
        await bot.send_message(message.from_id, MSG_CHANGE_SCHEDULE_STATUS_ACTIONS_INFO)

    # Хочу оставить дату для этого тату заказа неопределенной
    elif message.text == kb_admin.choice_new_date_or_no_date_in_tattoo_order["no_date"]:
        async with state.proxy() as data:
            data["user_id"] = message.from_user.id
            order_id = data["order_id"]
        
        with Session(engine) as session:
            # TODO закончить удаления ивента из списка ивентов в заказе
            """ schedule_order_events = session.scalars(select(Orders)
                .where(Orders.order_number == order_id)).one() """
            
            tattoo_order_number = tattoo_order.order_number
            client_id = tattoo_order.user_id
            tattoo_order.order_state = STATES["closed"]["postponed"]  # Отложен
            session.commit()
            
        await message.reply(
            f"Тату заказ № {tattoo_order_number} теперь без даты и времени встречи"
        )
        await message.reply(MSG_SUCCESS_CHANGING)
        
        async with state.proxy() as data:
            data["client_id"] = client_id
            data["notify_type"] = "no_date"

        await update_schedule_table(state)

        await bot.send_message(
            message.from_id,
            MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
            reply_markup=kb_client.kb_yes_no,
        )
        
    # "Просто изменить статус календаря"
    elif message.text == kb_admin.choice_new_date_or_no_date_in_tattoo_order["change"]:
        async with state.proxy() as data:
            new_schedule_state = data["new_schedule_state"]
            schedule_id = data["schedule_id"]
        
        with Session(engine) as session:
            schedule_date = session.get(ScheduleCalendar, int(schedule_id))
            schedule_date.status = new_schedule_state
            session.commit()
        await message.reply(MSG_SUCCESS_CHANGING)
        """ 
        # TODO нужно ли уведомлять пользователя при простом изменении статуса сеанса?
        await bot.send_message(
            message.from_id,
            MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
            reply_markup=kb_client.kb_yes_no,
        ) """
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_schedule_commands,
        )
    # если админ хочет оповестить пользователя и нажимает "Да"
    elif message.text == kb_client.yes_str:
        async with state.proxy() as data:
            client_id = data["client_id"]
            notify_type = data["notify_type"]
            order_id = data["order_id"]
            start_date_meeting = data["tattoo_order_start_date_meeting"]
            end_date_meeting = data["tattoo_order_end_date_meeting"]
            client_name = data["client_name"]

        if notify_type == "no_date":
            await bot.send_message(
                client_id,
                MSG_CLIENT_NO_DATE_IN_TATTOO_ORDER
                % [
                    client_name,
                    order_id,
                    start_date_meeting.strftime("%d/%m/%Y c %H:%M ")
                    + end_date_meeting.strftime("по %H:%M"),
                ],
            )
        elif notify_type == "new_date_from_schedule":
            async with state.proxy() as data:
                new_start_date = data["new_start_date"]
                new_start_time = data["new_start_time"]
                new_end_time = data["new_end_time"]

            await bot.send_message(
                client_id,
                MSG_CLIENT_HAVE_NEW_DATE_IN_TATTOO_ORDER
                % [
                    client_name,
                    order_id,
                    start_date_meeting.strftime("%d/%m/%Y"),
                    new_start_date,
                    start_date_meeting.strftime("%H:%M"),
                    new_start_time,
                    end_date_meeting.strftime("%H:%M"),
                    new_end_time,
                ],
            )
        elif notify_type == "new_date_from_schedule_with_no_old_schedule":
            await bot.send_message(
                client_id,
                MSG_CLIENT_HAVE_NEW_DATE_IN_TATTOO_ORDER_WITH_NO_OLD_SCHEDULE
                % [
                    client_name,
                    order_id,
                    start_date_meeting.strftime("%H:%M %d/%m/%Y"),
                    end_date_meeting.strftime("%H:%M"),
                ],
            )
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            kb_admin.kb_schedule_commands,
        )
        await state.finish()

    # если админ не хочет оповестить пользователя и нажимает "Нет"
    elif message.text == kb_client.no_str:
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_schedule_commands,
        )
        await state.finish()
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


@dp.callback_query_handler(
    dialog_cal_callback.filter(),
    state=FSM_Admin_change_schedule.get_new_date_for_tattoo_order,
)
async def process_get_new_date_for_new_data_schedule(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
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
            await FSM_Admin_change_schedule.next()
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
            await bot.send_message(user_id, MSG_SUCCESS_CHANGING)
                
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
    state=FSM_Admin_change_schedule.start_time_in_tattoo_order,
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
        await FSM_Admin_change_schedule.next()
        await bot.send_message(
            user_id,
            f"А теперь введи время окончания сеанса",
            reply_markup=await FullTimePicker().start_picker(),
        )


# выбираем новое время конца сеанса
@dp.callback_query_handler(
    full_timep_callback.filter(),
    state=FSM_Admin_change_schedule.end_time_in_tattoo_order,
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
            tattoo_order_number = data["tattoo_order_number"]
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
            f"🎉 У тату заказа №{tattoo_order_number} поменялась дата на "
            f"{start_time_in_tattoo_order.strftime('%Y-%m-%d %H:%M')} по"
            f"{end_time_in_tattoo_order.strftime('%Y-%m-%d %H:%M')}. "
            "А также добавилась новая дата в календарь.",
        )
        await FSM_Admin_change_schedule.next() #-> get_anwser_to_notify_client
        await bot.send_message(
            user_id,
            MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
            reply_markup=kb_client.kb_yes_no,
        )


async def get_anwser_to_notify_client(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            await bot.send_message(
                data["client_id"],
                MSG_CLIENT_HAVE_NEW_DATE_IN_TATTOO_ORDER
                % [
                    data["client_id"],
                    data["order_id"],
                    data["tattoo_order_start_date_meeting"].strftime("%d/%m/%Y"),
                    data["new_start_date"],
                    data["tattoo_order_end_date_meeting"].strftime("%H:%M"),
                    data["new_start_time"],
                    data["tattoo_order_end_date_meeting"].strftime("%H:%M"),
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


# ----------------------------------------- DELETE SCHEDULE EVENT-----------------------------------
class FSM_Admin_delete_schedule_date(StatesGroup):
    date_name = State()


# удалить дату в расписании
async def command_delete_date_schedule(message: types.Message):
    if (
        message.text in ["удалить дату в расписании", "/удалить_дату_в_расписании"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            schedule = session.scalars(select(ScheduleCalendar)
                .order_by(ScheduleCalendar.start_datetime)
                .order_by(ScheduleCalendar.end_datetime)
            ).all()

        if schedule == []:
            await message.reply(
                f"{MSG_NO_SCHEDULE_IN_TABLE}",
                reply_markup=kb_admin.kb_schedule_commands,
            )
        else:
            await bot.send_message(
                message.from_id, 
                (
                    "❕❕❕ Данная функция \"удалить дату в расписании\" "
                    "полностью удаляет расписание из базы!\n\n"
                    "Чтобы просто закрыть расписание, необходимо нажать на \"изменить мое расписание\" "
                    "в списке команд Расписания, затем изменить статус конкретной даты.\n\n"
                    "❕ Данная функция не делает проверку на статус в расписании."
                )
            )
            kb_date_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            for date in schedule:
                date_kb_str = (
                    f"{date.id}) {date.start_datetime.strftime('%d/%m/%Y с %H:%M')} по "
                    f"{date.end_datetime.strftime('%H:%M')}, "
                    f"тип: {date.event_type}, статус: {date.status}"
                )
                kb_date_schedule.add(KeyboardButton(date_kb_str))

            kb_date_schedule.add(kb_client.cancel_btn)

            await get_view_schedule(message.from_id, schedule)
            await FSM_Admin_delete_schedule_date.date_name.set()  # -> delete_schedule_date
            await message.reply(
                f"❔ Какую позицию удалить? Выбери из списка\n",
                reply_markup=kb_date_schedule,
            )


async def delete_schedule_date(message: types.Message, state: FSMContext):
    if message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_schedule_commands
        )
    else:
        schedule_id = message.text.split(") ")[0]
        deleted_schedule = message.text.split(") ")[1]
        with Session(engine) as session:
            # удаляем из таблицы schedule_calendar
            schedule = session.get(ScheduleCalendar, schedule_id)
            
            # удаляем из таблицы schedule_calendar_items если есть заказ на этот день
            schedule_items = session.scalars(select(ScheduleCalendar)
                .where(ScheduleCalendarItems.schedule_id == schedule_id)).all()
            if schedule_items != []:
                session.delete(schedule_items[0])
            session.delete(schedule)
            session.commit()
            
        await bot.send_message(message.from_id, MSG_SUCCESS_CHANGING)
        await message.reply(
            f"🎉 Расписание {deleted_schedule} удалено!\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_schedule_commands,
        )
    await state.finish()


# ---------------------------------------SCHEDULE------------------------------------------------------
def register_handlers_admin_schedule(dp: Dispatcher):
    dp.register_message_handler(
        command_get_schedule_command_list, commands=["расписание"]
    )
    dp.register_message_handler(
        command_get_schedule_command_list,
        Text(equals="расписание", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_new_photo_to_schedule,
        Text(equals="добавить фото расписания", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_name_for_photo_to_schedule,
        state=FSM_Admin_create_new_photo_to_schedule.number_month_year_for_photo,
    )
    dp.register_message_handler(
        get_photo_to_schedule,
        content_types=["photo", "text"],
        state=FSM_Admin_create_new_photo_to_schedule.photo_to_schedule,
    )

    dp.register_message_handler(
        command_create_new_date_to_schedule, commands=["добавить_дату_в_расписание"]
    )
    dp.register_message_handler(
        command_create_new_date_to_schedule,
        Text(equals="добавить дату в расписание", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        choice_event_type_in_schedule,
        state=FSM_Admin_create_new_date_to_schedule.event_type_choice,
    )
    dp.register_message_handler(
        choice_how_to_create_new_date_to_schedule,
        state=FSM_Admin_create_new_date_to_schedule.date_choice,
    )
    dp.register_message_handler(
        get_schedule_year, state=FSM_Admin_create_new_date_to_schedule.year_name
    )
    dp.register_message_handler(
        get_schedule_month, state=FSM_Admin_create_new_date_to_schedule.month_name
    )
    dp.register_message_handler(
        get_schedule_day, state=FSM_Admin_create_new_date_to_schedule.day_name
    )
    dp.register_message_handler(
        choice_order_to_schedule_event, 
        state=FSM_Admin_create_new_date_to_schedule.choice_connect_order_to_new_event
    )
    dp.register_message_handler(
        get_order_number_to_connect_with_new_event, 
        state=FSM_Admin_create_new_date_to_schedule.connect_order_to_new_event
    )
    
    #-----------------------------VIEW_SCHEDULE-----------------------------

    dp.register_message_handler(
        command_view_schedule, commands=["посмотреть_мое_расписание"]
    )
    dp.register_message_handler(
        command_view_schedule,
        Text(equals="посмотреть мое расписание", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_view_busy_schedule, commands=["посмотреть_мое_занятое_расписание"]
    )
    dp.register_message_handler(
        command_view_busy_schedule,
        Text(equals="посмотреть мое занятое расписание", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_view_opened_schedule, commands=["посмотреть_мое_свободное_расписание"]
    )
    dp.register_message_handler(
        command_view_opened_schedule,
        Text(equals="посмотреть мое свободное расписание", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_view_photos_schedule, commands=["посмотреть_фотографии_расписания"]
    )
    dp.register_message_handler(
        command_get_view_photos_schedule,
        Text(equals="посмотреть фотографии расписания", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_view_photo_schedule, commands=["посмотреть_фотографию_расписания"]
    )
    dp.register_message_handler(
        command_get_view_photo_schedule,
        Text(equals="посмотреть фотографию расписания", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_schedule_photo_to_view,
        state=FSM_Admin_get_view_schedule_photo.schedule_photo_name,
    )

    dp.register_message_handler(
        delete_photo_schedule, commands=["удалить_фото_расписания"]
    )
    dp.register_message_handler(
        delete_photo_schedule,
        Text(equals="удалить фото расписания", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_schedule_photo_to_delete,
        state=FSM_Admin_delete_schedule_photo.schedule_photo_name,
    )

    dp.register_message_handler(
        command_change_schedule, commands=["изменить_мое_расписание"]
    )
    dp.register_message_handler(
        command_change_schedule,
        Text(equals="изменить мое расписание", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        get_event_date, state=FSM_Admin_change_schedule.event_name
    )
    dp.register_message_handler(
        get_new_state_event_in_schedule, state=FSM_Admin_change_schedule.event_change
    )
    dp.register_message_handler(
        set_new_state_event_in_schedule,
        state=FSM_Admin_change_schedule.month_or_day_get_name_for_new_state_schedule,
    )

    dp.register_message_handler(
        get_answer_choice_new_date_or_no_date_in_tattoo_order,
        state=FSM_Admin_change_schedule.get_answer_choice_new_date_or_no_date_in_tattoo_order,
    )
    dp.register_message_handler(
        get_anwser_to_notify_client,
        state=FSM_Admin_change_schedule.get_anwser_to_notify_client,
    )

    # dp.register_message_handler(get_new_day_name_if_month_is_not_succsess,
    # state=FSM_Admin_change_schedule.get_new_day_name_if_month_is_not_succsess)

    # ---------------------------------------DELETE SCHEDULE---------------------------------------

    dp.register_message_handler(
        command_delete_date_schedule, commands=["удалить_дату_в_расписании"]
    )
    dp.register_message_handler(
        command_delete_date_schedule,
        Text(equals="удалить дату в расписании", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        delete_schedule_date, state=FSM_Admin_delete_schedule_date.date_name
    )
