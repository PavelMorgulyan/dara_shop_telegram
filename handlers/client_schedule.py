from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from msg.main_msg import *
from keyboards import kb_client, kb_admin
from handlers.other import *

from validate import check_pdf_document_payment, check_photo_payment
from handlers.calendar_client import obj

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *
from datetime import datetime


# Перенести сеанс
# Посмотреть мои сеансы

class FSM_Client_client_create_new_schedule_event(StatesGroup):
    get_order_number = State()
    get_new_schedule_event = State()
    
# команда для вывода меню календаря клиента
async def command_client_schedule_event(message: types.Message):# state: FSMContext)
    with Session(engine) as session:
        orders = session.scalars(select(Orders)
            .where(Orders.order_type.in_([kb_admin.price_lst_types['constant_tattoo']]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.in_([STATES['paid']]))
        ).all()
    if orders == []:
        await bot.send_message(message.from_id, 
            'Уважаемый Клиент! У тебя пока нет заказов для просмотра сеансов. '\
            'Меню сеансов будет доступно после совершения тату заказа на постоянную татуировку.')
    else:
        await bot.send_message(message.from_id, 'Что хотите посмотреть?', 
            reply_markup= kb_client.kb_client_schedule_menu)


# Добавить новый сеанс
async def command_client_create_new_schedule_event(message: types.Message):
    with Session(engine) as session:
        order = session.scalars(select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types['constant_tattoo']]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.in_([STATES['in_work']]))
        ).one()
        schedule_event = session.scalars(select(ScheduleCalendar)
            # .where(ScheduleCalendar.status == 'Закрыт')
            .where(ScheduleCalendar.id == order.schedule_id)).all()
        closed_schedule_event = session.scalars(select(ScheduleCalendar)
            .where(ScheduleCalendar.status == 'Закрыт')
            .where(ScheduleCalendar.id == order.schedule_id)).all()
        
    if schedule_event != [] and len(closed_schedule_event) == len(schedule_event):
    # Если заказ оплачен и имеет статус "в работе", а сеанс уже прошел
        kb = ReplyKeyboardMarkup(resize_keyboard= True)
        kb.add(KeyboardButton(f"№{order.order_number} {order.order_state}"))
        kb.add(kb_client.back_btn).add(kb_client.cancel_btn)
        await FSM_Client_client_create_new_schedule_event.get_order_number.set()
        
        await bot.send_message(message.from_id,
            'Пожалуйста, выберите заказ для нового сеанса', reply_markup = kb)
        
    elif len(closed_schedule_event) < len(schedule_event): 
        await bot.send_message(message.from_id, 'У вас уже есть открытый сеанс. '\
            'Посмотреть данные о сеансе можно по кнопке \"Посмотреть мои сеансы\"')


async def get_order_number_to_create_new_schedule_event_in_order(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        order = session.scalars(select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types['constant_tattoo']]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.in_([STATES['in_work']]))
        ).one()
    kb_msg = f"№{order.order_number} {order.order_state}"
    if message.text in kb_msg:
        async with state.proxy() as data:
            data['kb_order_lst'] = message.text
            
        with Session(engine) as session:
            open_schedule_events = session.scalars(select(ScheduleCalendar)
                .where(ScheduleCalendar.start_datetime > datetime.now())
                .where(ScheduleCalendar.end_datetime > datetime.now())
                .where(ScheduleCalendar.status == 'Свободен')).all()
            await FSM_Client_client_create_new_schedule_event.next() # -> get_schedule_number_to_create_new_event_in_order
        for event in open_schedule_events:
            kb = ReplyKeyboardMarkup(resize_keyboard= True)
            kb.add(KeyboardButton(f"c {event.start_datetime.strftime('%H:%M')} до"\
                f" {event.end_datetime.strftime('%H:%M %d/%m/%Y')}"))
            
            await bot.send_message(message.from_id,
                'Пожалуйста, выберите свободную дату для нового сеанса', reply_markup= kb)
    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(message.from_id, f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_schedule_menu)
        
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_schedule_number_to_create_new_event_in_order(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        open_schedule_events = session.scalars(select(ScheduleCalendar)
            .where(ScheduleCalendar.start_datetime > datetime.now())
            .where(ScheduleCalendar.end_datetime > datetime.now())
            .where(ScheduleCalendar.status == 'Свободен')).all()
    schedule_lst = []
    for event in open_schedule_events:
        schedule_lst.append(f"c {event.start_datetime.strftime('%H:%M')} до "\
            f"{event.end_datetime.strftime('%H:%M %d/%m/%Y')}")
        
    if message.text in schedule_lst:
        with Session(engine) as session:
            start_time = datetime.strptime(f"{message.text[0]} {message.text[3]}", "%H:%M %d/%m/%Y")
            end_time = datetime.strptime(f"{message.text[2]} {message.text[3]}", "%H:%M %d/%m/%Y")
            open_schedule_events = session.scalars(select(ScheduleCalendar)
                .where(ScheduleCalendar.start_datetime == start_time)
                .where(ScheduleCalendar.end_datetime == end_time)).one()
            open_schedule_events.status = 'Занят'
            session.commit()
        await bot.send_message(message.from_id, "Отлично, в заказе появился новый сеанс!\n"\
            f"Жду вас в {message.text}!")
        
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_client.kb_client_schedule_menu)
        await state.finish()
    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(message.from_id, f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_schedule_menu)
        
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Client_client_create_new_schedule_event.previous() #-> get_order_number_to_create_new_schedule_event_in_order
        async with state.proxy() as data:
            kb_order_lst = data['kb_order_lst']
        await bot.send_message(message.from_id,
            'Пожалуйста, выберите заказ для нового сеанса', reply_markup = kb_order_lst)
        
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


class FSM_Client_client_change_schedule_event(StatesGroup):
    get_order_number = State()


async def command_get_view_schedule_event_to_client(message: types.Message):
    with Session(engine) as session:
        order = session.scalars(select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types['constant_tattoo']]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.in_([STATES['in_work'], STATES['open'], STATES['paid']])))
        

class FSM_Client_client_view_schedule_event(StatesGroup):
    get_order_number = State()


def register_handlers_client_schedule(dp: Dispatcher):
    dp.register_message_handler(command_client_schedule_event,
        Text(equals= kb_client.client_main['client_schedule'], ignore_case=True), state=None)
    
    dp.register_message_handler(command_client_create_new_schedule_event, 
        Text(equals= kb_client.client_schedule_menu['add_new_event'], ignore_case=True), state=None)
    dp.register_message_handler(get_order_number_to_create_new_schedule_event_in_order,
        state= FSM_Client_client_create_new_schedule_event.get_order_number)
    dp.register_message_handler(get_schedule_number_to_create_new_event_in_order,
        state= FSM_Client_client_create_new_schedule_event.get_new_schedule_event)
    
    dp.register_message_handler(command_get_view_schedule_event_to_client,
        Text(equals= kb_client.client_schedule_menu['view_client_events'], ignore_case=True), state=None)