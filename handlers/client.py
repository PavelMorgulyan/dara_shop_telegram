from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
# from handlers.client_new_giftbox import *

from handlers.other import * 
from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

from msg.main_msg import *
from db.db_setter import set_to_table
from db.db_updater import update_info
from db.db_filling import db_dump_from_json_tattoo_items
from db.db_getter import get_info_many_from_table, DB_NAME, sqlite3

#from diffusers import StableDiffusionPipeline
#import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, date, time, timedelta
from aiogram.types.message import ContentType

from handlers.calendar_client import obj
import os


PAYMENTS_PROVIDER_TOKEN = os.environ["PAYMENTS_PROVIDER_TOKEN_DARA_TELEGRAM_BOT"]
ADMIN_NAMES = ['MorgulyanPavel', 'dara_redwan']
CODE_LENTH = 8
ORDER_CODE_LENTH = 10
CALENDAR_ID = 'pmorgukyan@gmail.com'
DARA_ID = 0


# start
async def command_start(message: types.Message):
    if message.from_user.username not in ADMIN_NAMES:
        await bot.send_message(message.from_user.id, 'Привет пользователь!',
            reply_markup = kb_client.kb_client_main)
        await message.delete()
        
    else:
        await bot.send_message(
            message.from_user.id, 
            'Привет админ! Какие команды хочешь выполнить?',
            reply_markup = kb_admin.kb_main)
        admin_tattoo_item = Session(engine).scalars(select(TattooItems)).all()
        if admin_tattoo_item == []:
            await db_dump_from_json_tattoo_items()
        
        await message.delete()

    #     await bot.send_message(message.from_id, 
    #       'Общение с ботом через ЛС, напишите ему: https://t.me/DaraShopBot')


# свободные даты
async def open_date_command(message: types.Message):    
    schedule = Session(engine).scalars(select(ScheduleCalendar).where(
        ScheduleCalendar.status == "Свободен").where(
        ScheduleCalendar.event_type == "тату заказ"))
    
    date_list = ''
    for date in schedule:
        date_list += f'🗓 {date.date} c {date.start_time} по {date.end_time}\n'
    month_today = int(datetime.strftime(datetime.now(), '%m'))
    year_today = int(datetime.strftime(datetime.now(), '%Y'))
    
    schedule_photo = await get_info_many_from_table('schedule_photo', 'name', f'{month_today} {year_today}')
    if schedule_photo != [] and schedule != []:
        await bot.send_photo( message.from_user.id, list(schedule_photo[0])[1],
            f'Вот мои свободные даты в этом месяце:\n{date_list}',
            reply_markup = kb_client.kb_client_main)
        
    elif schedule != [] and schedule_photo == []:
        await bot.send_message(message.from_user.id, 
            f'Вот мои свободные даты в этом месяце:\n{date_list}',
            reply_markup = kb_client.kb_client_main)
    else:
        await bot.send_message(message.from_id,  
            '❌ Прости, но в месяце пока нет свободных дат.\n\n '\
            '💬 Не переживай, позже я с тобой свяжусь!')


class FSM_Client_consultation(StatesGroup):
    choice_consultation_event_date = State()


# хочу консультацию
async def consultation_client_command(message: types.Message):
    if message.text.lower() in ['хочу консультацию 🌿', '/get_consultation', 'get_consultation']:
        
        schedule = Session(engine).scalars(select(ScheduleCalendar).where(ScheduleCalendar.status == 'Свободен').where(
            ScheduleCalendar.event_type == 'консультация'))
        
        if schedule == []:
            # TODO нужно ли давать выбор пользователю, чтобы он сам вбил дату консультации?
            await bot.send_message(message.from_id, MSG_NO_SCHEDULE_CONSULTATION)
        
        else:
            # TODO нужно ли выдавать фото расписания для консультаций?
            kb_date_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            msg_date_str = 'Вот мои свободные даты для консультаций в этом месяце:\n'
            
            for date in schedule:
                str_item = f"{date.date.strftime('%/d/%m/%Y')} c {date[1]} по {date[2]}\n"
                
                if date.date >= datetime.now():
                    msg_date_str += str_item
                    kb_date_schedule.add(KeyboardButton(str_item))
                    
            kb_date_schedule.add(kb_client.cancel_btn)
            await FSM_Client_consultation.choice_consultation_event_date.set()

            await bot.send_message(message.from_id, f'{msg_date_str}\n Какую консультацию хочешь?',
                reply_markup= kb_date_schedule)


async def choice_consultation_event_date(message: types.Message,  state: FSMContext):
    schedule = await get_info_many_from_table('schedule_calendar', 'status', 'Свободен')
    schedule_consultation_list = []
    
    for date in schedule:
        date = list(date)
        #if date[7].lower() == 'консультация':
        schedule_consultation_list.append( f'{date[4]} {date[3]} c {date[1]} по {date[2]}')

    if any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup = kb_client.kb_client_main)
        
    elif message.text in schedule_consultation_list:
        await update_info('schedule_calendar', 'id', message.text.split()[0], 'status', 'Занят')

        if DARA_ID != 0: # TODO дополнить id Шуны и добавить интеграцию с Google Calendar !!!
            await bot.send_message(DARA_ID,
                f'Дорогая Тату-мастерица! '\
                f'Поступил новая консультация! '
                f'Дата встречи: {message.text}')
            
        date_meeting = message.text.split()[1].split('/')
        start_time = f'{date_meeting[2]}-{date_meeting[1]}-{date_meeting[0]}T{message.text.split()[3]}'
        end_time = f'{date_meeting[2]}-{date_meeting[1]}-{date_meeting[0]}T{message.text.split()[4]}'

        event = await obj.add_event(CALENDAR_ID,
            'Новая консультация',
            f'Новая консультация от пользователя {message.from_user.full_name}', 
            start_time, # '2023-02-02T09:07:00',
            end_time    # '2023-02-03T17:07:00'
        )

        await state.finish()
        await bot.send_message(message.from_id,  
            f'🎉 Отлично! Вы забронировали консультацию на {message.text}.\n\n'\
            '🌿 Жду вас в своей студии!',
            reply_markup= kb_client.kb_client_main)
        
        await bot.send_message(message.from_id,  
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_client.kb_client_main)
    
    else:
        await bot.send_message(message.from_id, 
            f'❌ Прошу, выбери дату консультации из предложенных вариантов.')


# О тату мастере
async def send_contact_info_command(message: types.Message):
    await bot.send_message(message.from_user.id, MSG_ABOUT_TATTOO_MASTER,
        reply_markup = kb_client.kb_client_main)
    # print(message.from_user)
    print(message.from_id) # используем это для DARA_ID


# меню "важная информация"
# /important_info
async def send_info_menu(message: types.Message):
    await bot.send_message(
        message.from_id, 
        MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET,
        reply_markup=kb_client.kb_get_information)


# /посмотреть_мои_заказы, /my_orders
async def get_clients_orders(message: types.Message):
    await bot.send_message(message.from_id,  f'{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
        reply_markup= kb_client.kb_choice_order_view)


# /send_info_sketch_development
async def send_info_sketch_development(message: types.Message):
    await bot.send_message(message.from_id, MSG_SCRETH_DEV)
    await bot.send_message(message.from_id, MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET)


# /send_info_contraindications
async def send_info_contraindications(message: types.Message):
    await bot.send_message(message.from_id, MSG_CONTRAINDICATIONS)
    await bot.send_message(message.from_id, MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET)


# /send_info_preparing
async def send_info_preparing(message: types.Message):
    await bot.send_message(message.from_id, MSG_PREPARING_TATTOO_ORDER )
    await bot.send_message(message.from_id, MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET)


# /send_info_couple_tattoo
# TODO парная татушка - заказ? добавление этого бота в общий чат?
async def send_info_couple_tattoo(message: types.Message):
    await bot.send_message(message.from_id, MSG_COUPLE_TATTOO )
    await bot.send_message(message.from_id, MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET)


# /send_info_tattoo_care   
async def send_info_tattoo_care(message: types.Message):
    await bot.send_message(message.from_id, MSG_TATTOO_CARE )
    await bot.send_message(message.from_id, MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET)


# /send_info_restrictions_after_the_session   
async def send_info_restrictions_after_the_session(message: types.Message):
    await bot.send_message(message.from_id, MSG_RESTICTIONS_AFTER_THE_SESSION )
    await bot.send_message(message.from_id, MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET)


#/send_info_correction
async def send_info_correction(message: types.Message):
    await bot.send_message(message.from_id, MSG_CORRECTION )
    await bot.send_message(message.from_id, MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET)
    
    
#/send_info_address
async def send_info_address(message: types.Message):
    await bot.send_message(message.from_id, MSG_ADDRESS )
    await bot.send_message(message.from_id, MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET)


#/send_info_cooperation
async def send_info_cooperation(message: types.Message):
    await bot.send_message(message.from_id, MSG_COOPERATION )
    await bot.send_message(message.from_id, MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET)


class FSM_Client_username_info(StatesGroup):
    phone = State()

# закончить
async def close_command(message: types.Message, state: FSMContext):
    # await state.finish()
    await bot.send_message(message.from_user.id,
        'Удачи и добра тебе, друг, но знай - я всегда к твоим услугам!',
        reply_markup= kb_client.kb_client_main)


async def fill_client_table(data, message:types.Message):
    # Заполняем таблицу clients
    with Session(engine) as session:
        user = session.scalars(select(User).where(User.telegram_id == message.from_id)).one()
        user.phone = data['phone']
        session.commit()
        
    await bot.send_message(message.from_id, f'{MSG_THANK_FOR_ORDER}\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
        reply_markup= kb_client.kb_client_main)


# выбираем telegram покупателя
async def load_phone(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        if message.text not in LIST_CANCEL_COMMANDS + LIST_BACK_COMMANDS + LIST_BACK_TO_HOME:
            async with state.proxy() as data:
                if message.text == kb_client.phone_number['client_send_contact']:
                    data['phone'] = message.text
                elif message.text == kb_client.phone_number['client_dont_send_contact']:
                    data['phone'] = None
                await fill_client_table(data, message) 
            await state.finish() #  полностью очищает данные
            
        elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
            await bot.send_message(message.from_id, 'Вы точно хотите оставить заказ без телефона?',
                reply_markup= kb_client.kb_yes_no)
            
        elif message.text == kb_client.yes_str:
            await bot.send_message(message.from_id, 
                '❌ Хорошо, вы не стали добавлять телефон и вернулись в меню.')
            await bot.send_message(message.from_id,
                f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_client.kb_client_main)
            await state.finish()
            
        elif message.text == kb_client.no_str:
            await bot.send_message(message.from_id, 
                '☎️ Хорошо, тогда отправь свой телефон, пожалуйста.')
            
        else:
            await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
            
    elif message.content_type == 'contact':
        async with state.proxy() as data:
            data['phone'] = message.contact.phone_number
            await fill_client_table(data, message)
            
        await state.finish() #  полностью очищает данные


async def cancel_command(message: types.Message, state=FSMContext):
    if message.text in LIST_CANCEL_COMMANDS:
        current_state = await state.get_state()  # type: ignore
        if current_state is None:
            return
        await state.finish() # type: ignore
        
        if str(message.from_user.username) not in ADMIN_NAMES:
            await bot.send_message(message.from_id, MSG_BACK_TO_HOME, 
                reply_markup= kb_client.kb_client_main)
        else:
            await bot.send_message(message.from_id, MSG_BACK_TO_HOME, 
                reply_markup= kb_admin.kb_main)


async def back_to_home_command(message: types.Message, state=FSMContext):
    if message.text in LIST_BACK_TO_HOME:
        current_state = await state.get_state() # type: ignore
        if current_state is not None:
            await state.finish() # type: ignore
        if str(message.from_user.username) not in ADMIN_NAMES:
            await bot.send_message(message.from_id,  MSG_BACK_TO_HOME, 
                reply_markup= kb_client.kb_client_main)
        else:
            await bot.send_message(message.from_id, MSG_BACK_TO_HOME, 
                reply_markup= kb_admin.kb_main)


# @dp.message_handler(state="*", commands='отмена')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await bot.send_message(message.from_id, MSG_CANCEL_ACTION + MSG_BACK_TO_HOME, 
        reply_markup= kb_client.kb_client_main)



def register_handlers_client(dp: Dispatcher):
    #-----------------------------------------------BEGIN and COMMANDS--------------------------------------------
    dp.register_message_handler(command_start, commands=['start'])
    dp.register_message_handler(open_date_command, 
        Text(equals= kb_client.client_main['free_dates'], ignore_case=True), state=None)
    dp.register_message_handler(open_date_command, commands=['free_dates'])
    dp.register_message_handler(send_contact_info_command,
        Text(equals= kb_client.client_main['about_tattoo_master'], ignore_case=True), state=None)
    dp.register_message_handler(send_contact_info_command, commands=['about_master'])
    
    dp.register_message_handler(send_info_menu,
        Text(equals= kb_client.client_main['important_info'], ignore_case=True), state=None)
    dp.register_message_handler(send_info_menu, commands=['important_info'])
    
    dp.register_message_handler(send_info_sketch_development,
        Text(equals=kb_client.get_information['send_info_sketch_development'], ignore_case=True), 
        state=None)
    dp.register_message_handler(send_info_sketch_development, 
        commands=['send_info_sketch_development'])
    
    dp.register_message_handler(send_info_contraindications,
        Text(equals=kb_client.get_information['send_info_contraindications' ],ignore_case=True), 
        state=None)
    dp.register_message_handler(send_info_contraindications, 
        commands=['send_info_contraindications'])
    
    dp.register_message_handler(send_info_preparing,
        Text(equals=kb_client.get_information['send_info_preparing'], ignore_case=True), 
        state=None)
    dp.register_message_handler(send_info_preparing, commands=['send_info_preparing'])
    
    dp.register_message_handler(send_info_couple_tattoo,
        Text(equals=kb_client.get_information['send_info_couple_tattoo'],ignore_case=True), 
        state=None)
    dp.register_message_handler(send_info_couple_tattoo, commands=['send_info_couple_tattoo'])
    
    dp.register_message_handler(send_info_tattoo_care,
        Text(equals=kb_client.get_information['send_info_tattoo_care'],ignore_case=True), 
        state=None)
    dp.register_message_handler(send_info_tattoo_care, commands=['send_info_tattoo_care'])
    
    dp.register_message_handler(send_info_restrictions_after_the_session,
        Text(equals=kb_client.get_information['send_info_restrictions_after_the_session'], ignore_case=True),
        state=None)
    dp.register_message_handler(send_info_restrictions_after_the_session, 
        commands=['send_info_restrictions_after_the_session'])
    
    dp.register_message_handler(send_info_correction,
        Text(equals=kb_client.get_information['send_info_correction'], ignore_case=True), state=None)
    dp.register_message_handler(send_info_correction, commands=['send_info_correction'])
    
    dp.register_message_handler(send_info_address,
        Text(equals=kb_client.get_information['send_info_address'], ignore_case=True), 
        state=None)
    dp.register_message_handler(send_info_address, commands=['send_info_address'])
    
    dp.register_message_handler(send_info_cooperation,
        Text(equals=kb_client.get_information['send_info_cooperation'], ignore_case=True), 
        state=None)
    dp.register_message_handler(send_info_cooperation, commands=['send_info_cooperation'])
    
    dp.register_message_handler(close_command,
        Text(equals='закончить', ignore_case=True), state="*")
    
    dp.register_message_handler(consultation_client_command,
        Text(equals= kb_client.client_main['client_want_consultation'], ignore_case=True))
    dp.register_message_handler(consultation_client_command, commands=['get_consultation'])
    dp.register_message_handler(choice_consultation_event_date,
        state=FSM_Client_consultation.choice_consultation_event_date)

    # dp.register_message_handler(back_command, commands=['назад'], state='*')
    # dp.register_message_handler(back_command, Text(equals=['назад', 'Назад'],
    # ignore_case=True), state=None)
    dp.register_message_handler(cancel_command, commands=['cancel', 'start'], state='*')
    dp.register_message_handler(cancel_command, 
        Text(equals=LIST_CANCEL_COMMANDS + ['start'], ignore_case=True), state="*")
    dp.register_message_handler(back_to_home_command, commands=['start'], state='*')
    dp.register_message_handler(back_to_home_command, 
        Text(equals=LIST_BACK_TO_HOME + ['start'], ignore_case=True), state="*")
    
    #----------------------------------------Commands------------------------------------------------------
    dp.register_message_handler(cancel_handler, state="*", commands=kb_client.cancel_lst[0])
    dp.register_message_handler(cancel_handler,
        Text(equals=kb_client.cancel_lst[0], ignore_case=True), state="*")
    dp.register_message_handler(cancel_handler, Text(equals='cancel', ignore_case=True), state="*")
    
    dp.register_message_handler(get_clients_orders, commands=['my_orders'], state=None)
    dp.register_message_handler(get_clients_orders,
        Text(equals= kb_client.client_main['clients_orders'], ignore_case=True))
    
    #-------------------------------------Load Client contact----------------------------------------------

    dp.register_message_handler(load_phone, content_types=['contact', 'message'],
        state=FSM_Client_username_info.phone) # добавляет всю инфу про пользователя
