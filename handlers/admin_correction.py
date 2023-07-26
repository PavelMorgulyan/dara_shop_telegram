from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from prettytable import PrettyTable
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES

from handlers.other import *
from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram_calendar import simple_cal_callback, dialog_cal_callback, DialogCalendar
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback
from aiogram_timepicker import result, carousel, clock
from msg.main_msg import *
from handlers.admin_schedule import get_view_schedule


#TODO создать функции: записать пользователя на коррекцию

async def get_correction_commands(message: types.Message):
    if (
        message.text.lower()
        in ["/коррекция", "коррекция"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            MSG_WHICH_COMMAND_TO_EXECUTE,
            reply_markup=kb_admin.kb_correction_commands,
        )


#------------------------------CREATE CORRECTION DATE------------------------------------------
class FSM_Admin_create_correction(StatesGroup):
    order_number = State()
    schedule_type = State()
    new_date = State()
    new_start_time = State()
    new_end_time = State()
    notify_client = State()


async def command_create_correction_event_date(message: types.Message):
    if (
        message.text.lower()
        in ["/создать_запись_на_коррекцию", "создать запись на коррекцию"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await bot.send_message(
            message.from_id, 
            "💭 Данная команда позволяет добавить новый сеанс коррекции к существующему заказу",
        )
        
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
            await FSM_Admin_create_correction.order_number.set()
            await message.reply(
                "❔ К какому заказу добавить сеанс?",
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
        
    if message.text in order_lst:
        async with state.proxy() as data:
            data['kb_tattoo_order_numbers_with_status'] = kb_tattoo_order_numbers_with_status
            data['order_number'] = message.text.split()[0]
            with Session(engine) as session:
                orders = session.scalars(
                        select(Orders).where(Orders.order_number == message.text.split()[0])
                    ).one()
            data['client_name'] = orders.username
            data['client_id'] = order.user_id
        
        await FSM_Admin_create_correction.next() # -> get_schedule_type
        await message.reply(
            "❔ Добавить новый сеанс из календаря или создать новый сеанс?",
            reply_markup= kb_admin.kb_admin_choice_create_new_or_created_schedule_item
        )
        
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(
            MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


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
    kb.add(kb_admin.home_btn)
    
    if message.text == kb_admin.admin_choice_create_new_or_created_schedule_item['create_new_schedule']:
        # -> process_get_new_date_for_new_data_schedule    
        await FSM_Admin_create_correction.next() 
        await message.reply(
            f"🕒 Введите новую дату для тату заказа",
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
            # TODO проверить запонение нового статуса и нового event_type в остальных случаях 
            # изменения статуса и ивента календаря
            
            schedule.status = kb_admin.schedule_event_status['busy']
            schedule.event_type = kb_admin.schedule_event_type['correction']
            
            session.commit()
            
        await bot.send_message(
            message.from_id, 
            MSG_ADMIN_ADD_NEW_CORRECTION_EVENT_TO_CLIENT_TATTOO_ORDER
        )
        
        #-> get_anwser_to_notify_client
        for i in range(3):
            await FSM_Admin_create_correction.next()
        
        await bot.send_message(
            message.from_id,
            MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
            reply_markup=kb_client.kb_yes_no,
        )
        
    elif message.text == kb_admin.admin_choice_create_new_or_created_schedule_item['choice_created_schedule']:
        await bot.send_message(
            message.from_id, "❔ Какой день выбираешь?", reply_markup=kb
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
        await FSM_Admin_create_correction.previous() 
        await message.reply(
            "❔ К какому заказу добавить сеанс?",
            reply_markup=kb_tattoo_order_numbers_with_status,
        )


@dp.callback_query_handler(
    dialog_cal_callback.filter(),
    state=FSM_Admin_create_correction.new_date,
)
async def process_get_new_date_for_new_data_schedule(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)  # type: ignore
    if selected:
        await callback_query.message.answer(
            f'🕒 Вы выбрали новую дату {date.strftime("%d/%m/%Y")}'
        )

        async with state.proxy() as data:
            data["date_meeting"] = date
            user_id = data["user_id"]
            new_date_tattoo_order = data["new_date_tattoo_order"]
            schedule_id = data["schedule_id"]

        if new_date_tattoo_order:
            # -> process_hour_timepicker_new_start_time_in_tattoo_order
            await FSM_Admin_create_correction.next()
            await bot.send_message(
                user_id,
                f"💬 Введи новое время для тату заказа",
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
    state=FSM_Admin_create_correction.new_start_time,
)
async def process_hour_timepicker_new_start_time_in_tattoo_order(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore

    if r.selected:
        await callback_query.message.edit_text(
            f'🕒 Вы выбрали время {r.time.strftime("%H:%M")} ',
        )
        async with state.proxy() as data:
            user_id = data["user_id"]
            data["start_time_in_tattoo_order"] = r.time.strftime("%H:%M")
        # -> process_hour_timepicker_new_end_time_in_tattoo_order
        await FSM_Admin_create_correction.next()
        await bot.send_message(
            user_id,
            f"🕒 Введите время окончания сеанса",
            reply_markup=await FullTimePicker().start_picker(),
        )


# выбираем новое время конца сеанса
@dp.callback_query_handler(
    full_timep_callback.filter(),
    state=FSM_Admin_create_correction.new_end_time,
)
async def process_hour_timepicker_new_end_time_in_tattoo_order(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    r = await FullTimePicker().process_selection(callback_query, callback_data)  # type: ignore

    if r.selected:
        await callback_query.message.edit_text(
            f'🕒 Вы выбрали время {r.time.strftime("%H:%M")}'
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
            f"🎉 У тату заказа №{order_number} добавилась дата сеанса с "
            f"{start_time_in_tattoo_order.strftime('%Y-%m-%d %H:%M')} по"
            f"{end_time_in_tattoo_order.strftime('%Y-%m-%d %H:%M')}.\n\n"
            "🕒 А также добавилась новая дата в календаре.",
        )
        #-> get_anwser_to_notify_client
        await FSM_Admin_create_correction.next()
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
                MSG_CLIENT_HAVE_NEW_CORRECTION_DATE_IN_TATTOO_ORDER_WITH_NO_OLD_SCHEDULE
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


#-------------------------------VIEW CORRECTION DATES---------------------
async def command_view_correction_event_dates(message: types.Message):
    if (
        message.text.lower()
        in ["/записи_на_коррекцию", "записи на коррекцию"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            events = session.scalars(select(ScheduleCalendar)
                    .where(ScheduleCalendar.event_type == kb_admin.schedule_event_type['correction'])
                ).all()
            
        await get_view_schedule(message.from_id, events)


# TODO добавить функцию "изменить запись на коррекцию", "удалить запись на коррекцию"


def register_handlers_admin_correction(dp: Dispatcher):
    # ---------------------------ADD NEW SCHEDULE EVENT OT TATTOO ORDER -------------
    dp.register_message_handler(
        command_create_correction_event_date,
        Text(equals="создать запись на коррекцию", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_tattoo_order_number_to_new_schedule_event,
        state=FSM_Admin_create_correction.order_number
    )
    dp.register_message_handler(
        get_schedule_type,
        state=FSM_Admin_create_correction.schedule_type
    )
    dp.register_message_handler(
        get_anwser_to_notify_client,
        state=FSM_Admin_create_correction.notify_client
    )
    #---------------------SEND_TO_VIEW_CORRECTION_EVENT_DATES--------------
    #TODO сделать функцию "записи на коррекцию"
    
    dp.register_message_handler(
        command_view_correction_event_dates,
        Text(equals="записи на коррекцию", ignore_case=True),
        state=None,
    )
    
    dp.register_message_handler(
        get_correction_commands,
        Text(equals="Коррекция", ignore_case=True),
        state=None,
    )