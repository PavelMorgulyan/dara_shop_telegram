from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import generate_random_order_number, generate_random_code, \
    CODE_LENTH, ORDER_CODE_LENTH, ADMIN_NAMES, CALENDAR_ID, DARA_ID

from db.db_setter import set_to_table
from db.db_updater import update_info
from db.db_delete_info import delete_info, delete_table
from db.db_getter import get_info_many_from_table, DB_NAME, sqlite3
from handlers.other import * 
from handlers.admin_tattoo_order import FSM_Admin_tattoo_order

from handlers.other import * 
from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult, Sequence
from db.sqlalchemy_base.db_classes import *
from datetime import datetime

#from diffusers import StableDiffusionPipeline
#import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
from aiogram_calendar import dialog_cal_callback, DialogCalendar
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback


from prettytable import PrettyTable
from handlers.calendar_client import obj
from msg.main_msg import *


#--------------------------------------- SEND TO ADMIN ALL SCHEDULE AT 12:00----------------------------
async def send_notification_schedule():
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    closed_states_str = ', '.join([f'{key.capitalize()}: {value}' for key, value in CLOSED_STATE_DICT.items()])
    
    sqlite_select_query = \
        f"""SELECT * from giftbox_orders WHERE order_state not in \'({closed_states_str})\'"""
    cursor.execute(sqlite_select_query)
    orders = cursor.fetchall()
    if (sqlite_connection):
            sqlite_connection.close()
    for order in orders:
        if DARA_ID != 0:
            await bot.send_message(DARA_ID, "Дорогая тату мастерица! \
                Вот твое расписание на сегодня:\n")
            
            schedule = await get_info_many_from_table('schedule_calendar') 
            await get_view_schedule(DARA_ID, schedule) 


#-------------------------------- CREATE NEW SCHEDULE---------------------------------
async def command_get_schedule_command_list(message: types.Message):
    if message.text == 'Расписание' and \
        str(message.from_user.username) in ADMIN_NAMES:
        await message.reply('Какие комманды хочешь сделать?',
            reply_markup=kb_admin.kb_schedule_commands)

#-------------------------------------- ADD NEW PHOTO SCHEDULE DATE -----------------------------------
# /добавить фото расписания
class FSM_Admin_create_new_photo_to_schedule(StatesGroup):
    number_month_year_for_photo = State()
    photo_to_schedule = State()


async def command_new_photo_to_schedule(message: types.Message):
    if message.text.lower() == 'добавить фото расписания' and \
        str(message.from_user.username) in ADMIN_NAMES:
        kb_month_year = ReplyKeyboardMarkup(resize_keyboard=True)
        month_today = int(datetime.strftime(datetime.now(), '%m'))
        year_today = int(datetime.strftime(datetime.now(), '%Y'))
        for j in range(0, 3):
            for i in range(month_today, 12):
                kb_month_year.add(KeyboardButton(f'{i} {year_today+j}'))
        kb_month_year.add(KeyboardButton('Назад'))
        await FSM_Admin_create_new_photo_to_schedule.number_month_year_for_photo.set()
        await message.reply('На какой месяц хочешь добавить фото к расписанию?',
            reply_markup= kb_month_year)


async def get_name_for_photo_to_schedule(message: types.Message, state: FSMContext):
    names_photo_list = []
    month_today = int(datetime.strftime(datetime.now(), '%m'))
    year_today = int(datetime.strftime(datetime.now(), '%Y'))
    for j in range(0, 1):
        for i in range(month_today, 12):
            names_photo_list.append(f'{i} {year_today+j}')
    if message.text.lower() in names_photo_list:
        async with state.proxy() as data:
            data['name_schedule_photo'] = message.text
        await FSM_Admin_create_new_photo_to_schedule.next()
        await message.reply('Хорошо, а теперь добавь фото календаря')
        
    elif message.text.lower() in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply('Хорошо, отменим действие. Что хочешь еще сделать?',
            reply_markup=kb_admin.kb_schedule_commands)
    else:
        await message.reply('Пожалуйста, введи корректный месяц и год для команды.\
            Выбери из списка')


async def get_photo_to_schedule(message: types.Message, state: FSMContext):
    if message.content_type == 'photo':
        async with state.proxy() as data:
            photo_name = data['name_schedule_photo']
            
        with Session(engine) as session:
            new_schedule_photo = SchedulePhoto(
                name=  photo_name,
                photo= message.photo[0].file_id
            )
            session.add(new_schedule_photo)
            session.commit()
        
        await bot.send_message(message.from_id, f'Отлично! Ты добавила фото календаря! \n\n'\
            f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_schedule_commands)
        await state.finish()
        
    elif message.content_type == 'text':
        if message.text in LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(MSG_CANCEL_ACTION + MSG_BACK_TO_HOME,
                reply_markup= kb_admin.kb_price_list_commands)
        

#-------------------------------------- ADD NEW SCHEDULE DATE -----------------------------------
class FSM_Admin_create_new_date_to_schedule(StatesGroup):
    event_type_choice = State()
    date_choice = State()
    year_name = State()
    month_name = State()
    day_name = State()
    day_by_date = State()
    start_time_in_schedule = State()
    end_time_in_schedule = State()
    get_date_if_wrong_month = State()


# /добавить дату в расписание
async def command_create_new_date_to_schedule(message: types.Message):
    if message.text.lower() == 'добавить дату в расписание' and\
        str(message.from_user.username) in ADMIN_NAMES:
        await FSM_Admin_create_new_date_to_schedule.event_type_choice.set()
        # [ 'Хочу ввести конкретную дату', 'Хочу выбрать день недели и месяц']
        await message.reply('Хорошо, давай добавим новую дату в твоем расписании. '\
            'Это будет тату работа или консультация?',
            reply_markup= kb_admin.kb_event_type_schedule)


async def choice_event_type_in_schedule(message: types.Message, state: FSMContext):
    if message.text in kb_admin.event_type_schedule:
        async with state.proxy() as data:
            data['event_type'] = message.text.lower()
            data['year_number'] = datetime.now().strftime('%Y')
            data['user_id'] = message.from_user.id
        await FSM_Admin_create_new_date_to_schedule.next() # -> choice_how_to_create_new_date_to_schedule
        # 'Хочу ввести конкретную дату', 'Хочу выбрать день недели и месяц'
        await message.reply(
            f'Хорошо, ты выбрала добавить в расписание {message.text}.'\
            ' Хочешь ввести конкретную дату, или просто выбрать месяц и день недели?',
            reply_markup= kb_admin.kb_new_date_choice)
    else:
        await message.reply('Выбери, пожалуйста, слова из представленного \
            выбора - тату заказ или консультация.')


# выбираем год или конкретную дату
async def choice_how_to_create_new_date_to_schedule(message: types.Message, state: FSMContext):
    
    if message.text == kb_admin.new_date_choice['one_date']: # Хочу ввести конкретную дату
        for i in range(4):
            await FSM_Admin_create_new_date_to_schedule.next() # -> get_day_by_date_for_schedule
        await message.reply('Давай выберем конкретную дату. Введи ее',
            reply_markup=await DialogCalendar().start_calendar())
        
    elif message.text == kb_admin.new_date_choice['many_dates']: # Хочу выбрать день недели и месяц
        await FSM_Admin_create_new_date_to_schedule.next() #-> get_schedule_year
        await message.reply('Давай выберем год. Выбери год из списка',
            reply_markup= kb_admin.kb_years)
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_schedule_year(message: types.Message, state: FSMContext):
    if int(message.text) in kb_admin.years_lst:
        await FSM_Admin_create_new_date_to_schedule.next() #->get_schedule_month
        async with state.proxy() as data:
            data['year_number'] = message.text
            
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for month in kb_admin.month:
            month_number = await get_month_number_from_name(month)
            if datetime.strptime(f"{message.text}-{month_number}-1 00:00", '%Y-%m-%d %H:%M') > datetime.now():
                kb.add(KeyboardButton(month))
        
        await message.reply(
            f'Ты выбрала год {message.text}. Давай выберем месяц. Выбери имя месяца из списка',
            reply_markup= kb)
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# добавляем месяц и выбираем день недели
async def get_schedule_month(message: types.Message, state: FSMContext):
    if message.text in kb_admin.month:
        async with state.proxy() as data:
            data['month_name'] = message.text
            data['month_number'] = await get_month_number_from_name(message.text)

        await FSM_Admin_create_new_date_to_schedule.next() # -> get_schedule_day
        await message.reply('Хорошо. Какой день недели?',
            reply_markup = kb_admin.kb_days_for_schedule)
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# добавляем день недели и выбираем начало рабочего дня
async def get_schedule_day(message: types.Message, state: FSMContext): 
    if message.text in kb_admin.days:
        async with state.proxy() as data:
            data['date'] = message.text
            
        for i in range(2):
            await FSM_Admin_create_new_date_to_schedule.next() # -> process_hour_timepicker_start_time
            
        await bot.send_message(message.from_user.id, 'Отлично, давай определимся со временем. '\
            'С какого времени начинается твой рабочее расписание в этот день?',
            reply_markup = await FullTimePicker().start_picker())
        
    elif message.text == kb_admin.new_date_choice['one_date']:
        await FSM_Admin_create_new_date_to_schedule.next() # -> get_day_by_date_for_schedule
        await bot.send_message(message.from_user.id, "Выбери конкретную дату",
            reply_markup = await DialogCalendar().start_calendar())
        
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await bot.send_message(message.from_user.id, MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
        


@dp.callback_query_handler(dialog_cal_callback.filter(), 
    state=FSM_Admin_create_new_date_to_schedule.day_by_date)
async def get_day_by_date_for_schedule(callback_query: CallbackQuery,
    callback_data: dict, state: FSMContext):
    
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data) # type: ignore
    username_id = 0
    async with state.proxy() as data:
        username_id = data['user_id']
        
    if selected:
        await callback_query.message.answer(f'Вы выбрали {date}')
        if date > datetime.now():
            # async def load_datemiting(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['date'] = date # f'{date.strftime("%d/%m/%Y")}' #  message.text
                data['month_name'] = await get_month_from_number(int(date.strftime("%m")), 'ru')
                data['month_number'] = int(date.strftime("%m"))
            await FSM_Admin_create_new_date_to_schedule.next()
            await bot.send_message(username_id,
                'Отлично, давай определимся со временем. '\
                'С какого времени начинается твой рабочее расписание в этот день?',
                reply_markup= await FullTimePicker().start_picker())
            
        else:
            await bot.send_message(username_id,
                "Выбери еще раз конкретную дату. '\
                'Дата должна быть позже в этом году, а не раньше.",
                reply_markup= await DialogCalendar().start_calendar())


# выбираем время начала рабочего дня
@dp.callback_query_handler(full_timep_callback.filter(),
    state=FSM_Admin_create_new_date_to_schedule.start_time_in_schedule)
async def process_hour_timepicker_start_time(callback_query: CallbackQuery,
    callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)# type: ignore
    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали начало рабочего дня в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            username_id = data['user_id']
            if int(r.time.strftime("%H")) > 8 and int(r.time.strftime("%H")) < 24:
                
                data['start_time_in_schedule'] = r.time.strftime("%H:%M")
                await FSM_Admin_create_new_date_to_schedule.next()
                await bot.send_message(username_id,
                    'Когда заканчивается твой рабочее расписание в этот день?',
                    reply_markup=await FullTimePicker().start_picker())
                
            elif int(r.time.strftime("%H")) < 8:
                await bot.send_message(username_id,
                    'Прости, но ты так рано не работаешь. '\
                    'Вряд-ли и ты захочешь работать в 8 утра. Введи другое время ',
                    reply_markup=await FullTimePicker().start_picker())
                
            elif int(r.time.strftime("%H")) > 23:
                await bot.send_message(username_id,
                    'Прости, но ты так поздно не работаешь. '\
                    'Вряд-ли и ты захочешь работать в 23 вечера. \
                    Введи другое время',
                    reply_markup= await FullTimePicker().start_picker())


@dp.callback_query_handler(full_timep_callback.filter(),
    state=FSM_Admin_create_new_date_to_schedule.end_time_in_schedule)
async def process_hour_timepicker_end_time(callback_query: CallbackQuery,
    callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)# type: ignore
    if r.selected: 
        new_event_to_schedule_bool = False
        await callback_query.message.edit_text(
            f'Вы выбрали конец рабочего дня в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            username_id = data['user_id']
            start_time = data['start_time_in_schedule']
            if r.time.strftime("%H:%M") > start_time:
                data['end_time_in_schedule'] = r.time.strftime("%H:%M")
                
                date = data['date']
                year = data['year_number']
                month_name = data['month_name']
                month_number = data['month_number']
                end_time = data['end_time_in_schedule']
                month_name_from_number = await get_month_from_number(month_number, 'ru')
                
                if date not in kb_admin.days and month_name_from_number != month_name:
                    for i in range(2):
                        await FSM_Admin_create_new_date_to_schedule.previous() #-> get_day_by_date_for_schedule
                    await bot.send_message(username_id,
                        f'Дата {date} и месяц {month_name} не совпадают. '\
                        'Введите месяц и дату в этом месяце корректно',
                        reply_markup = await DialogCalendar().start_calendar())
                else:
                    new_event_to_schedule_bool = True
                
                if new_event_to_schedule_bool:
                    if date not in kb_admin.days:
                        
                        start_datetime = datetime.strptime(
                            f"{date.strftime('%Y-%m-%d')} {start_time}", '%Y-%m-%d %H:%M')
                        
                        end_datetime = datetime.strptime(
                            f"{date.strftime('%Y-%m-%d')} {r.time.strftime('%H:%M')}", '%Y-%m-%d %H:%M')
                        
                        with Session(engine) as session:
                            new_schedule_event = ScheduleCalendar(
                                start_datetime= start_datetime,
                                end_datetime=   end_datetime,
                                status=         'Свободен',
                                event_type=     data['event_type']
                            )
                            session.add(new_schedule_event)
                            session.commit()
                            
                        await bot.send_message(username_id,
                            f"Отлично, теперь в {month_name} в {date.strftime('%d/%m/%Y')} c {start_time} " \
                            f"по {end_time} у тебя рабочее время!",
                            reply_markup = kb_admin.kb_schedule_commands)
                    else:
                        
                        dates = await get_dates_from_month_and_day_of_week(
                            date, month_name, year, start_time, end_time)
                        
                        dates_str = ''
                        for iter_date in dates:
                            with Session(engine) as session:
                                new_schedule_event = ScheduleCalendar(
                                    start_datetime= iter_date['start_datetime'],
                                    end_datetime=   iter_date['end_datetime'],
                                    status=         'Свободен',
                                    event_type=     data['event_type']
                                )
                                session.add(new_schedule_event)
                                session.commit()
                            
                            dates_str += f"{iter_date['start_datetime'].strftime('%d/%m/%Y')}, "
                            
                        await bot.send_message(username_id,
                            f'Отлично, теперь в {month_name} все {date}'\
                            f' ({dates_str[:len(dates_str)-2]})'\
                            f' c {start_time} по {end_time} у тебя рабочее время!',
                            reply_markup= kb_admin.kb_schedule_commands)
                        
                    await state.finish()
            else:
                await bot.send_message(username_id, 
                    f'Время окончания работы должно быть позже времени начала работ.'\
                    ' Введи время заново',
                    reply_markup= await FullTimePicker().start_picker())



#------------------------------------------------------- VIEW SCHEDULE-----------------------------------
async def get_view_schedule(user_id: int, schedule: ScalarResult[ScheduleCalendar]):
    if schedule == []:
        await bot.send_message(user_id, 
            f'{MSG_NO_SCHEDULE_IN_TABLE}\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}')
    else:
        headers  = ['N', 'Месяц', 'Дата', 'Время начала', 'Время конца', 'Статус', 'Тип', 'Заказы']
        table = PrettyTable(headers, left_padding_width = 0, right_padding_width=0)  # Определяем таблицу
        i = 0
        for date in schedule:
            order_number = ''
            with Session(engine) as session:
                orders = session.scalars(select(Orders).where(Orders.id == date.schedule_id))
            if orders != []:
                for order in orders:
                    order_number += f'{order.order_number} '
            else:
                order_number = 'Нет заказов'
            i+=1
            table.add_row(
                [
                    i, 
                    await get_month_from_number(int(date.start_datetime.strftime('%m')), 'ru'), 
                    date.start_datetime.strftime('%d/%m/%Y'), 
                    date.start_datetime.strftime('%H:%M'), 
                    date.end_datetime.strftime('%H:%M'),
                    date.status, 
                    date.event_type, 
                    order_number
                ]
            )

        await bot.send_message(user_id, f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
        # table = PrettyTable(headers, left_padding_width = 0, right_padding_width=0)


# /посмотреть_мое_расписание
async def command_view_schedule(message: types.Message):
    if message.text == 'посмотреть мое расписание' and \
        str(message.from_user.username) in ADMIN_NAMES:
        with Session(engine) as session:
            schedule = session.scalars(select(ScheduleCalendar).order_by(
                ScheduleCalendar.start_datetime)).all()
        await get_view_schedule(message.from_user.id, schedule) 
        # events = await obj.get_calendar_events(CALENDAR_ID)

        '''
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
        '''

        # for event in events['items']:
        #    print(event['summary'])


# /посмотреть_мое_занятое_расписание
async def command_view_busy_schedule(message: types.Message):
    if message.text == 'посмотреть мое занятое расписание' and \
        str(message.from_user.username) in ADMIN_NAMES:
        with Session(engine) as session:
            schedule = session.scalars(select(ScheduleCalendar).where(
                ScheduleCalendar.status == 'Занят').order_by(
                ScheduleCalendar.start_datetime)).all()
        await get_view_schedule(message.from_user.id, schedule) 


# /посмотреть мое свободное расписание
async def command_view_opened_schedule(message: types.Message):
    if message.text == 'посмотреть мое свободное расписание' and \
        str(message.from_user.username) in ADMIN_NAMES:
        schedule = Session(engine).scalars(select(ScheduleCalendar).where(
            ScheduleCalendar.status == 'Свободен').order_by(
                ScheduleCalendar.start_datetime)).all()
        await get_view_schedule(message.from_user.id, schedule)  


#---------------------------------------- VIEW ALL PHOTOS SCHEDULE-----------------------------------
# /посмотреть_фотографии_расписания
async def command_get_view_photos_schedule(message:types.Message):
    if message.text.lower() in \
        ['/посмотреть_фотографии_расписания', 'посмотреть фотографии расписания'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            photos_schedule  = Session(engine).scalars(select(SchedulePhoto)).all()
            if photos_schedule == []:
                await bot.send_message(message.from_id, MSG_NO_SCHEDULE_PHOTO_IN_TABLE)
                await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
            else:
                for photo in photos_schedule:
                    await bot.send_photo(message.chat.id, photo.photo, 
                        f"Название фотографии календаря: 0{photo.name}")
                await message.reply('Что еще хочешь сделать?')


#----------------------------------------- VIEW PHOTO SCHEDULE-----------------------------------
class FSM_Admin_get_view_schedule_photo(StatesGroup):
    schedule_photo_name = State()


# /посмотреть_одну_фотографию_расписания
async def command_get_view_photo_schedule(message:types.Message):
    if message.text.lower() in \
        ['/посмотреть_фотографии_расписания', 'посмотреть фотографию расписания'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            
            with Session(engine) as session:
                photos_schedule = session.scalars(select(SchedulePhoto)).all()
                
            kb_photos_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            if photos_schedule == []:
                await bot.send_message(message.from_id, 
                    f'{MSG_NO_SCHEDULE_PHOTO_IN_TABLE}\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}')
            else:
                for photo in photos_schedule:
                    kb_photos_schedule.add(KeyboardButton( photo.name))
                kb_photos_schedule.add(KeyboardButton('Назад'))
                await FSM_Admin_get_view_schedule_photo.schedule_photo_name.set()
                await message.reply(f"Какую фотографию хочешь посмотреть?", reply_markup= kb_photos_schedule)


async def get_schedule_photo_to_view(message: types.Message, state: FSMContext ):
    with Session(engine) as session:
        photos_schedule = session.scalars(select(SchedulePhoto)).all()
    photo_names_list = []
    for photo in photos_schedule:
        photo_names_list.append(photo.name)
        
    if message.text in photo_names_list:
        with Session(engine) as session:
            photos_schedule = session.scalars(select(SchedulePhoto).where(
                SchedulePhoto.name == message.text)).one()
            
        await bot.send_photo(message.chat.id, photo.photo, 
            f"Название фотографии календаря: {photo.name}")
        await message.reply('Что еще хочешь сделать?', reply_markup=kb_admin.kb_schedule_commands)
        await state.finish()
        
    elif message.text == 'Назад':
        await message.reply('Хорошо, вы вернулись в меню расписания. Что хочешь сделать?',
            reply_markup= kb_admin.kb_schedule_commands)
        await state.finish()
    else:
        await message.reply('Пожалуйста, выбери наименование фотографии расписания из списка '\
            'или отмени действие')


#-------------------------------------- DELETE PHOTO SCHEDULE-----------------------------------
class FSM_Admin_delete_schedule_photo(StatesGroup):
    schedule_photo_name = State()


# /удалить_фото_расписания
async def delete_photo_schedule(message: types.Message):
    if message.text.lower() in ['/удалить_фото_расписания', 'удалить фото расписания'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        with Session(engine) as session:
            photos_schedule = session.scalars(select(SchedulePhoto)).all()
            
        kb_photos_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
        for photo in photos_schedule:
            kb_photos_schedule.add(KeyboardButton( photo.name))
            await bot.send_photo(message.chat.id, photo.photo,
                f"Название фотографии календаря: {photo.name}")
        kb_photos_schedule.add(KeyboardButton('Назад'))
        await FSM_Admin_delete_schedule_photo.schedule_photo_name.set()
        await message.reply('Какое фото хочешь удалить?',
            reply_markup= kb_photos_schedule)

async def get_schedule_photo_to_delete(message: types.Message, state: FSMContext ):
    with Session(engine) as session:
        photos_schedule = session.scalars(select(SchedulePhoto)).all()
    photo_names_list = []
    for photo in photos_schedule:
        photo_names_list.append(photo.name)
        
    if message.text in photo_names_list:
        with Session(engine) as session:
            photo = session.scalars(select(SchedulePhoto).where(
                SchedulePhoto.name == message.text)).one()
            session.delete(photo)
            session.commit()
            
        await message.reply(
            f'Отлично, фото \"0{message.text}\" удалено из расписания.\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_schedule_commands)
        await state.finish()
        
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await message.reply('Хорошо, вы вернулись в меню расписания. Что хочешь сделать?',
            reply_markup= kb_admin.kb_schedule_commands)
        await state.finish()
        
    else:
        await message.reply('Пожалуйста, выбери наименование фотографии расписания из списка '\
            'или отмени действие')


#------------------------------------------------------- CHANGE SCHEDULE-----------------------------------
class FSM_Admin_change_schedule(StatesGroup):
    event_name = State()
    event_change = State()
    start_time_in_schedule = State()
    month_or_day_get_name_for_new_state_schedule = State()
    new_date_in_schedule = State()
    
    get_answer_choice_new_date_or_no_date_in_tattoo_order = State()
    get_new_date_for_tattoo_order = State()
    start_time_in_tattoo_order = State()
    end_time_in_tattoo_order = State()

    get_anwser_to_notify_client = State()
    # get_new_day_name_if_month_is_not_succsess = State()

# /изменить_мое_расписание, изменить мое расписание
async def command_change_schedule(message: types.Message):  # state=None
    if message.text == 'изменить мое расписание' and \
        str(message.from_user.username) in ADMIN_NAMES:
            
        with Session(engine) as session:
            schedule = session.scalars(select(ScheduleCalendar)).all()
            
        headers  = ['Номер', 'Месяц', 'Дата', 'Время начала','Время конца', 'Статус', 'Тип']
        table = PrettyTable(headers, left_padding_width = 0, right_padding_width=0)  # Определяем таблицу
        kb_date_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
        
        for date in schedule:
            # date = list(date)
            row_item = \
                f"id:{date.id}|{date.start_datetime.strftime('%d/%m/%Y')} c "\
                f"{date.start_datetime.strftime('%H:%M')} по "\
                f"{date.end_datetime.strftime('%H:%M')} статус:{date.status} тип:{date.event_type}\n"
            
            table.add_row([
                date.id, 
                await get_month_from_number(int(date.start_datetime.strftime('%m')), 'ru'), 
                date.start_datetime.strftime('%d/%m/%Y'), 
                date.start_datetime.strftime('%H:%M'), 
                date.end_datetime.strftime('%H:%M'), 
                date.status, 
                date.event_type
                ]
            )
            kb_date_schedule.add(KeyboardButton(row_item))
            
        await message.reply(f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
        await FSM_Admin_change_schedule.event_name.set() # event_name
        await bot.send_message(message.from_id,
            'Какую позицию хочешь изменить? Выбери из списка',
            reply_markup= kb_date_schedule)


async def get_event_date(message:types.Message, state: FSMContext ): # state=FSM_Admin_change_schedule.event_name
    with Session(engine) as session:
        schedule = session.scalars(select(ScheduleCalendar)).all()
    data_list = []
    for date in schedule:
        data_list.append(f"id:{date.id}|{date.start_datetime.strftime('%d/%m/%Y')} c "\
            f"{date.start_datetime.strftime('%H:%M')} по "\
            f"{date.end_datetime.strftime('%H:%M')} статус:{date.status} тип:{date.event_type}\n")
    
    if message.text in data_list:
        async with state.proxy() as data:
            data['event_date_old'] = message.text 
            data['schedule_id'] = data_list.index(message.text)+1
            data['user_id'] = message.from_user.id
            
        with Session(engine) as session:
            schedule = session.get(ScheduleCalendar, data_list.index(message.text)+1)
            
        async with state.proxy() as data:
            data['old_schedule_status'] = schedule.status
            
        await FSM_Admin_change_schedule.next()
        # ['Время начала работы', 'Время окончания работы', 'Дату', 'Статус', 'Тип']
        await message.reply(f'Что хочешь изменить? \n', reply_markup= kb_admin.kb_date_states)
        
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_schedule_commands)
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def update_schedule_table(state: FSMContext):
    async with state.proxy() as data:
        username_id = data['user_id']
        schedule_id = data['schedule_id']
        event_date_old = data['event_date_old'].split("|")[1].split()
        
    with Session(engine) as session:
        new_date = session.get(ScheduleCalendar, schedule_id)

    old_data_to_send = {
        "id":           new_date.id,
        "month":        event_date_old[0],
        "date":         event_date_old[1],
        "start time":   event_date_old[3],
        "end time":     event_date_old[5],
        "state":        event_date_old[7],
        "type":         event_date_old[9] + ' ' + event_date_old[10],
    }

    new_data_to_send = {
        "id":           new_date.id,
        "month":        await get_month_from_number(int(new_date.start_datetime.strftime('%m')), 'ru'), 
        "date":         new_date.start_datetime.strftime('%d/%m/%Y'), 
        "start time":   new_date.start_datetime.strftime('%H:%M'), 
        "end time":     new_date.end_datetime.strftime('%H:%M'), 
        "state":        new_date.status, 
        "type":         new_date.event_type
    }
    headers  = ['Месяц', 'Дата', 'Время начала','Время конца', 'Статус', 'Тип']
    table = PrettyTable(headers, left_padding_width = 1, right_padding_width= 1)  # Определяем таблицу
    table.add_row(list(old_data_to_send.values()))
    await bot.send_message(username_id, f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
    
    table_next = PrettyTable(headers, left_padding_width = 1, right_padding_width= 1)
    table_next.add_row(list(new_data_to_send.values()))
    await bot.send_message(username_id, f'<pre>{table_next}</pre>', parse_mode=types.ParseMode.HTML)
        


# state - FSM_Admin_change_schedule.event_change    
async def get_new_state_event_in_schedule(message:types.Message, state: FSMContext ):
    if message.text in kb_admin.date_states:
        async with state.proxy() as data:
            data['new_event_date_state'] = message.text
            data['new_date_tattoo_order'] = False
            
        if message.text == 'Дату':
            for i in range(3):
                await FSM_Admin_change_schedule.next() # -> get_changing_day_by_date_for_schedule
            await message.reply("Ввыбери конкретную дату",
                reply_markup= await DialogCalendar().start_calendar())
            
        elif message.text == 'Время начала работы':
            await message.reply('Выбери новое время начала работы',
                reply_markup= await FullTimePicker().start_picker())
            
        elif message.text == 'Время окончания работы':
            await message.reply('Выбери новое время окончания работы',
                reply_markup= await FullTimePicker().start_picker())
        
        # TODO При изменении статуса нужно проверять,
        # TODO есть ли какой-либо заказ в это время, и менять дату расписания для заказа + оповещать пользователя
        elif message.text == 'Статус': 
            for i in range(2):
                await FSM_Admin_change_schedule.next() #-> set_new_state_event_in_schedule
                
            await message.reply('Выбери новый статус. Какой статус поставим?',
                reply_markup= kb_admin.kb_free_or_close_event_in_schedule)
        
        elif message.text == 'Тип':
            await message.reply('Выбери новый тип даты календаря. Какой поставим?',
                reply_markup= kb_admin.kb_type_of_schedule)
            
        elif message.text in kb_admin.type_of_schedule_lst:
            async with state.proxy() as data:
                schedule_id = data['schedule_id']
                
            with Session(engine) as session:
                schedule_event = session.get(ScheduleCalendar, schedule_id)
                schedule_event.event_type = message.text
                session.commit()
                
            await update_schedule_table(state)
            await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE, 
                reply_markup= kb_admin.kb_schedule_commands)
            await state.finish()
            
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_schedule_commands)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)



# выбираем новое время начала или конца рабочего дня
@dp.callback_query_handler(full_timep_callback.filter(), state=FSM_Admin_change_schedule.start_time_in_schedule)
async def process_hour_timepicker_start_or_end_time(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)# type: ignore
    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время {r.time.strftime("%H:%M")} ',
        )
        async with state.proxy() as data:
            schedule_id = data['schedule_id']
            new_event_date_state = data['new_event_date_state']
            
        with Session(engine) as session:
            schedule_event = session.get(ScheduleCalendar, schedule_id)
            if new_event_date_state == 'Время начала работы':
                schedule_event.start_datetime = datetime.strptime(
                    schedule_event.start_datetime.strftime('%Y-%m-%d') + ' ' + \
                    r.time.strftime("%H:%M"), '%Y-%m-%d %H:%M')
            else:
                schedule_event.start_datetime = datetime.strptime(
                    schedule_event.end_datetime.strftime('%Y-%m-%d') + ' ' + \
                    r.time.strftime("%H:%M"), '%Y-%m-%d %H:%M')
            session.commit()
            
        await update_schedule_table(state)
        await state.finish()


# state=FSM_Admin_change_schedule.month_or_day_get_name_for_new_state_schedule)
async def set_new_state_event_in_schedule(message:types.Message, state: FSMContext): 
    with Session(engine) as session:
        orders = session.scalars(select(Orders).where(
            Orders.order_state.in_([CLOSED_STATE_DICT["postponed"], OPEN_STATE_DICT["open"]])).where(
            Orders.schedule_id == None).where(
            Orders.order_type == 'тату заказ'
            )).all()
        
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    order_kb_lst = []
    for order in orders:
        item_str = f'{order.order_number} {order.order_name} {order.order_state}'
        kb.add(KeyboardButton(item_str))
        order_kb_lst.append(item_str)
        
    # ['Свободен', 'Занят']
    if message.text in kb_admin.free_or_close_event_in_schedule: 
        async with state.proxy() as data:
            schedule_id = data['schedule_id']
            data['new_schedule_state'] = message.text
            new_schedule_state = message.text
        
        # Ищем в бд заказ, который связан с этим ивентом
        with Session(engine) as session:
            tattoo_order = session.scalars(select(Orders).where(
                Orders.order_type == 'тату заказ').where(
                Orders.schedule_id == schedule_id)).one()

        if tattoo_order != []:
            async with state.proxy() as data:
                data['order_id'] = tattoo_order.id
                data['tattoo_order_start_date_meeting'] = tattoo_order.start_date_meeting
                data['tattoo_order_end_date_meeting'] = tattoo_order.end_date_meeting
                data['tattoo_order_number'] = tattoo_order.order_number
                data['client_id'] = tattoo_order.user_id
                data['client_name'] = tattoo_order.username
                old_schedule_state = data['old_schedule_state']
                
            await bot.send_message(message.from_id, 
                f'С этим расписанием у вас связан тату заказ. '\
                'Если читаешь это сообщение в первый раз, то нажми кнопку \
                    \"Информация об изменении статусов календаря\"')
            
            if old_schedule_state == 'Занят' and new_schedule_state == 'Свободен':
                await FSM_Admin_change_schedule.next() #-> get_answer_choice_new_date_or_no_date_in_tattoo_order
                
                # 'Хочу поставить новую дату для этого тату заказа', 
                # 'Хочу оставить дату для этого тату заказа неопределенной', 
                # 'Информация об изменении статусов календаря'
                await bot.send_message(message.from_id, 
                    'Хочешь изменить изменить дату встречи, или хочешь поставить '\
                    'неизвестную дату встречи на этот заказ?',
                    reply_markup= kb_admin.kb_choice_new_date_or_no_date_in_tattoo_order)
                
            elif old_schedule_state == 'Свободен' and new_schedule_state == 'Занят':
                
                # "Добавить самому новый заказ в этот календарный день",
                # "Выбрать из тех заказов, у которых нет даты сеанса",
                # "Оставить данный календарный день занятым без заказов"
                await message.reply('Какое действие хочешь выбрать?',
                    kb_admin.admin_chioce_get_new_order_to_schedule_event)
                
            else:
                await message.reply(
                    'Ты выбрал такой же статус календаря. Пожалуйста, введи другой статус',
                    reply_markup= kb_admin.kb_free_or_close_event_in_schedule)
        else:
            await update_schedule_table(state)
            await state.finish()
            
    # "Добавить самому новый заказ в этот календарный день". 
    # Если статус календаря меняется со Свободен на закрыт
    # -> если админ хочет добавить в пустой заказ новый ивент календаря из уже созданных в бд
    elif message.text == kb_admin.admin_chioce_get_new_order_to_schedule_event['new_order']:
        async with state.proxy() as data:
            schedule_id = data['schedule_id']
            new_schedule_state = data['new_schedule_state']
        
        # меняем статус календаря
        with Session(engine) as session:
            schedule_event = session.get(ScheduleCalendar, schedule_id)
            schedule_event.status = new_schedule_state
            session.commit()
            
        await FSM_Admin_tattoo_order.get_tattoo_type.set()
        await bot.send_message(message.from_id, "Привет, админ. Сейчас будет создан тату заказ. "\
            "Тату заказ будет для переводного тату или для постоянного?",
            reply_markup = kb_client.kb_client_choice_main_or_temporary_tattoo)
    
    # "Выбрать из тех заказов, у которых нет даты сеанса" -> выдает список заказов без расписания
    # Если статус календаря меняется со Свободен на закрыт
    elif message.text == kb_admin.admin_chioce_get_new_order_to_schedule_event['choice_created_order']:
        await bot.send_message(message.from_id, 'Какой заказ хочешь выбрать?', reply_markup= kb)
    
    # Если статус календаря меняется со Свободен на закрыт -> просто меняем статус
    elif message.text == kb_admin.admin_chioce_get_new_order_to_schedule_event['no_order']:
        async with state.proxy() as data:
            schedule_id = data['schedule_id']
            new_schedule_state = data['new_schedule_state']
        
        # меняем статус календаря
        with Session(engine) as session:
            schedule_event = session.get(ScheduleCalendar, schedule_id)
            schedule_event.status = new_schedule_state
            session.commit()
            
        await update_schedule_table(state)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE, 
            reply_markup= kb_admin.kb_schedule_commands)
        
    # Если статус календаря меняется со Свободен на закрыт
    # если админ хочет добавить в пустой заказ новый ивент календаря из уже созданных в бд
    elif message.text in order_kb_lst:
        async with state.proxy() as data:
            schedule_id = data['schedule_id']
            data['notify_type'] = 'new_date_from_schedule_with_no_old_schedule'
            
        with Session(engine) as session:
            order = session.get(Orders, order_kb_lst.index(message.text)+1)
            schedule = session.get(ScheduleCalendar, schedule_id)
            order.schedule_id = schedule.id
            order.start_date_meeting = schedule.start_datetime
            order.end_date_meeting = schedule.end_datetime
            if order.order_state == CLOSED_STATE_DICT["postponed"]: # Отложен
                order.order_state = OPEN_STATE_DICT["open"] # Открыт
            session.commit()
        await update_schedule_table(state)
        await bot.send_message(message.from_id, MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
            reply_markup= kb_client.kb_yes_no)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_answer_choice_new_date_or_no_date_in_tattoo_order(message:types.Message, state: FSMContext):
    with Session(engine) as session:
        schedule_events = session.scalars(select(ScheduleCalendar).where(
            ScheduleCalendar.status == 'Свободен')).all()
        
    schedule_events_kb_lst = []
    for event in schedule_events:
        schedule_events_kb_lst.append(f"{event.start_datetime.strftime('%d/%m/%Y с %H:%M')} по \
            {event.end_datetime.strftime('%H:%M')}")
    
    # 'Хочу поставить новую дату для этого тату заказа'
    if message.text == kb_admin.choice_new_date_or_no_date_in_tattoo_order['new_date']:
        await bot.send_message(message.from_id, 
            "Хочешь выбрать из календаря или создать новый день в расписании?",
            reply_markup= kb_admin.admin_choice_create_new_or_created_schedule_item)
    
    # "Создать новое расписание"
    elif message.text == kb_admin.admin_choice_create_new_or_created_schedule_item["create_new_schedule"]:
        async with state.proxy() as data:
            data['new_date_tattoo_order'] = True
        await FSM_Admin_change_schedule.next() #-> process_get_new_date_for_new_data_schedule
        await message.reply(f'Введи новую дату для тату заказа', 
            reply_markup= await DialogCalendar().start_calendar())
    
    elif message.text in schedule_events_kb_lst:
        async with state.proxy() as data:
            data['user_id'] = message.from_user.id
            order_id = data['order_id']
            tattoo_order_number = data['tattoo_order_number'] 
            client_id = data['client_id']
            data['notify_type'] = 'new_date_from_schedule'
            
            with Session(engine) as session:
                tattoo_order = session.get(Orders, order_id)
                
                tattoo_order.start_date_meeting= datetime.strptime(
                    f'{message.text.split()[0:3]}', '%d/%m/%Y с %H:%M')
                
                tattoo_order.end_date_meeting= datetime.strptime(
                    f'{message.text.split()[0]} {message.text.split()[4]}', '%d/%m/%Y %H:%M')
                tattoo_order.schedule_id = schedule_events_kb_lst.index(message.text) + 1
                session.commit()

            async with state.proxy() as data:
                data['new_start_date'] = message.text.split()[0] # %d/%m/%Y
                data['new_start_time'] = message.text.split()[2] # %H:%M
                data['new_end_time'] = message.text.split()[4] # %H:%M
            
            await bot.send_message(message.from_id, MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
                reply_markup= kb_client.kb_yes_no)
            
    elif message.text == kb_admin.admin_choice_create_new_or_created_schedule_item["choice_created_schedule"]:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for event in schedule_events_kb_lst:
            kb.add(KeyboardButton(event))
        await bot.send_message(message.from_id, "Какой день выбираешь?", reply_markup=kb)
        
    elif message.text == kb_admin.choice_new_date_or_no_date_in_tattoo_order['info']:
        await bot.send_message(message.from_id, MSG_CHANGE_SCHEDULE_STATUS_ACTIONS_INFO) 
        
    elif message.text == kb_admin.choice_new_date_or_no_date_in_tattoo_order['no_date']:
        async with state.proxy() as data:
            data['user_id'] = message.from_user.id
            order_id = data['order_id']
            
        with Session(engine) as session:
            tattoo_order = session.get(Orders, order_id)
            tattoo_order.start_date_meeting = None # datetime.strptime("1970-01-01 00:00", '%Y-%m-%d %H:%M')
            tattoo_order.end_date_meeting = None
            tattoo_order.schedule_id = None
            tattoo_order_number = tattoo_order.order_number
            client_id = tattoo_order.user_id
            tattoo_order.order_state = CLOSED_STATE_DICT["postponed"] # Отложен
            session.commit()
        await message.reply(f'Хорошо, тату заказ № {tattoo_order_number} теперь без даты и времени встречи')
        
        async with state.proxy() as data:
            data['client_id'] = client_id
            data['notify_type'] = 'no_date'
        
        await update_schedule_table(state)
        
        await bot.send_message(message.from_id, MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
            reply_markup= kb_client.kb_yes_no)
        
    elif message.text == kb_client.yes_str:
        async with state.proxy() as data:
            client_id = data['client_id']
            notify_type = data['notify_type']
            order_id = data['order_id']
            start_date_meeting = data['tattoo_order_start_date_meeting']
            end_date_meeting = data['tattoo_order_end_date_meeting']
            client_name = data['client_name']
            
        if notify_type == 'no_date':
            await bot.send_message(client_id, MSG_CLIENT_NO_DATE_IN_TATTOO_ORDER % 
                [client_name, order_id, start_date_meeting.strftime('%d/%m/%Y c %H:%M ') + 
                end_date_meeting.strftime('по %H:%M')])
            
        elif notify_type == 'new_date_from_schedule':
            async with state.proxy() as data:
                new_start_date = data['new_start_date']
                new_start_time = data['new_start_time'] 
                new_end_time = data['new_end_time']
                
            await bot.send_message(client_id, MSG_CLIENT_HAVE_NEW_DATE_IN_TATTOO_ORDER % [
                    client_name, 
                    order_id, 
                    start_date_meeting.strftime('%d/%m/%Y'),
                    new_start_date, 
                    start_date_meeting.strftime('%H:%M'), 
                    new_start_time, 
                    end_date_meeting.strftime('%H:%M'), 
                    new_end_time
                ]
            )
        elif notify_type == 'new_date_from_schedule_with_no_old_schedule':
            await bot.send_message(
                client_id, 
                MSG_CLIENT_HAVE_NEW_DATE_IN_TATTOO_ORDER_WITH_NO_OLD_SCHEDULE % [
                    client_name, 
                    order_id, 
                    start_date_meeting.strftime('%H:%M %d/%m/%Y'),
                    end_date_meeting.strftime('%H:%M')
                ]
            )
        await state.finish()
        
    elif message.text == kb_client.no_str:
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            kb_admin.kb_schedule_commands)
        await state.finish()
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


@dp.callback_query_handler(dialog_cal_callback.filter(),
    state=FSM_Admin_change_schedule.get_new_date_for_tattoo_order)
async def process_get_new_date_for_new_data_schedule(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)# type: ignore
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали новую дату {date.strftime("%d/%m/%Y")}')

        async with state.proxy() as data:
            data['date_meeting'] = date
            user_id = data['user_id']
            new_date_tattoo_order = data['new_date_tattoo_order']
            schedule_id = data['schedule_id']
            
        if new_date_tattoo_order:
            await FSM_Admin_change_schedule.next()
            await bot.send_message(
                user_id, f'Хорошо, а теперь введи новое время для тату заказа',
                reply_markup = await FullTimePicker().start_picker())
            
        else:
            with Session(engine) as session:
                schedule_event = session.get(ScheduleCalendar, schedule_id)
                schedule_event.start_datetime = datetime.strptime(
                    f"{date.strftime('%Y-%m-%d')} {schedule_event.start_datetime.strftime('%H:%M')}",
                    '%Y-%m-%d %H:%M'
                )
                schedule_event.end_datetime = datetime.strptime(
                    f"{date.strftime('%Y-%m-%d')} {schedule_event.start_datetime.strftime('%H:%M')}",
                    '%Y-%m-%d %H:%M'
                )
                session.commit()
            await update_schedule_table(state)
            await bot.send_message(user_id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
                reply_markup= kb_admin.kb_schedule_commands)
            await state.finish()


# выбираем новое время начала 
@dp.callback_query_handler(full_timep_callback.filter(),
    state=FSM_Admin_change_schedule.start_time_in_tattoo_order)
async def process_hour_timepicker_new_start_time_in_tattoo_order(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)# type: ignore

    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время {r.time.strftime("%H:%M")} ',
        )
        async with state.proxy() as data:
            user_id = data['user_id']
            data['start_time_in_tattoo_order'] = r.time.strftime("%H:%M")
        await FSM_Admin_change_schedule.next()
        await bot.send_message(user_id, f'А теперь введи время окончания сеанса',
            reply_markup= await FullTimePicker().start_picker())


# выбираем новое время конца сеанса
@dp.callback_query_handler(full_timep_callback.filter(),
    state=FSM_Admin_change_schedule.end_time_in_tattoo_order)
async def process_hour_timepicker_new_end_time_in_tattoo_order(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)# type: ignore

    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время {r.time.strftime("%H:%M")}')

        async with state.proxy() as data:
            start_time_in_tattoo_order = datetime.strptime(
                f"{data['date_meeting'].strftime('%Y-%m-%d')} {data['start_time_in_tattoo_order']}",
                '%Y-%m-%d %H:%M'
            )
            end_time_in_tattoo_order =  datetime.strptime(
                f"{data['date_meeting'].strftime('%Y-%m-%d')} {r.time.strftime('%H:%M')}",
                '%Y-%m-%d %H:%M'
            )
            tattoo_order_number = data['tattoo_order_number']
            user_id = data['user_id']
            data['new_start_date'] = data['date_meeting'].strftime('%Y-%m-%d')
            data['new_start_time'] = data['start_time_in_tattoo_order']
            data['new_end_time'] = r.time.strftime('%H:%M')
            
            
        with Session(engine) as session:
            new_schedule_event = ScheduleCalendar(
                start_datetime= start_time_in_tattoo_order,
                end_datetime =  end_time_in_tattoo_order, 
                status=         'Занят',
                event_type=     'тату заказ'
            )
            session.add(new_schedule_event)
            session.commit()
        
        await bot.send_message(user_id, 
            f"У тату заказа №{tattoo_order_number} поменялась дата на "\
            f"{start_time_in_tattoo_order.strftime('%Y-%m-%d %H:%M')} по"\
            f"{end_time_in_tattoo_order.strftime('%Y-%m-%d %H:%M')}."\
            "А также добавилась новая дата в календарь.")
        await FSM_Admin_change_schedule.next()
        await bot.send_message(user_id, MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT,
            reply_markup = kb_client.kb_yes_no)


async def get_anwser_to_notify_client(message:types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            await bot.send_message(
                data['client_id'], 
                MSG_CLIENT_HAVE_NEW_DATE_IN_TATTOO_ORDER % [
                    data['client_id'], 
                    data['order_id'], 
                    data['tattoo_order_start_date_meeting'].strftime('%d/%m/%Y'),
                    data['new_start_date'], 
                    data['tattoo_order_end_date_meeting'].strftime('%H:%M'), 
                    data['new_start_time'] , 
                    data['tattoo_order_end_date_meeting'].strftime('%H:%M'), 
                    data['new_end_time']
                ]
            )
        await update_schedule_table(state)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        await state.finish()
        
    elif message.text == kb_client.no_str:
        await update_schedule_table(state)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        await state.finish()
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)

#----------------------------------------- DELETE SCHEDULE EVENT-----------------------------------    
class FSM_Admin_delete_schedule_date(StatesGroup):
    date_name = State()


# удалить дату в расписании
async def command_delete_date_schedule(message: types.Message):
    if message.text in ['удалить дату в расписании', '/удалить_дату_в_расписании'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        with Session(engine) as session:
            schedule = session.scalars(select(ScheduleCalendar)).all()
            
        if schedule == []:
            await message.reply(f'{MSG_NO_SCHEDULE_IN_TABLE}. {MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_admin.kb_schedule_commands)
        else:
            kb_date_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            for date in schedule:
                date_kb_str = f"{date.id}) {date.start_datetime.strftime('%d/%m/%Y с %H:%M')} по "\
                    f"{date.end_datetime.strftime('%H:%M')}, тип: {date.event_type}, статус: {date.status}"
                kb_date_schedule.add(KeyboardButton(date_kb_str))
                
            kb_date_schedule.add(kb_client.cancel_btn)
            
            await get_view_schedule(schedule)
            await FSM_Admin_delete_schedule_date.date_name.set() #-> delete_schedule_date
            await message.reply(f'Какую позицию хочешь удалить? Выбери из списка\n',
                reply_markup= kb_date_schedule)


async def delete_schedule_date(message:types.Message, state: FSMContext):
    if message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_schedule_commands)
    else:
        
        schedule_id = message.text.split().split(") ")[0]
        deleted_schedule = message.text.split(") ")[1]
        with Session(engine) as session:
            schedule = session.get(ScheduleCalendar, schedule_id)
            session.delete(schedule)
            session.commit()
            
        await message.reply(
            f'Отлично, твое расписание {deleted_schedule} удалено! Что еще хочешь сделать?',
            reply_markup= kb_admin.kb_schedule_commands)
    await state.finish()


#-------------------------------------------------------SCHEDULE------------------------------------------------------
def register_handlers_admin_schedule(dp: Dispatcher):
    dp.register_message_handler(command_get_schedule_command_list, commands=['расписание'])
    dp.register_message_handler(command_get_schedule_command_list,
        Text(equals='расписание', ignore_case=True), state=None)
    
    dp.register_message_handler(command_new_photo_to_schedule,
        Text(equals='добавить фото расписания', ignore_case=True), state=None)
    dp.register_message_handler(get_name_for_photo_to_schedule,
        state=FSM_Admin_create_new_photo_to_schedule.number_month_year_for_photo)
    dp.register_message_handler(get_photo_to_schedule, content_types=['photo', 'text'],
        state=FSM_Admin_create_new_photo_to_schedule.photo_to_schedule)

    dp.register_message_handler(command_create_new_date_to_schedule, commands=['добавить_дату_в_расписание'])
    dp.register_message_handler(command_create_new_date_to_schedule,
        Text(equals='добавить дату в расписание', ignore_case=True), state=None)
    dp.register_message_handler(choice_event_type_in_schedule,
        state=FSM_Admin_create_new_date_to_schedule.event_type_choice)
    dp.register_message_handler(choice_how_to_create_new_date_to_schedule,
        state=FSM_Admin_create_new_date_to_schedule.date_choice)
    dp.register_message_handler(get_schedule_year,
        state=FSM_Admin_create_new_date_to_schedule.year_name)
    dp.register_message_handler(get_schedule_month,
        state=FSM_Admin_create_new_date_to_schedule.month_name)
    dp.register_message_handler(get_schedule_day, state=FSM_Admin_create_new_date_to_schedule.day_name)

    dp.register_message_handler(command_view_schedule, commands=['посмотреть_мое_расписание'])
    dp.register_message_handler(command_view_schedule,
        Text(equals='посмотреть мое расписание', ignore_case=True), state=None)

    dp.register_message_handler(command_view_busy_schedule,
        commands=['посмотреть_мое_занятое_расписание'])
    dp.register_message_handler(command_view_busy_schedule,
        Text(equals='посмотреть мое занятое расписание', ignore_case=True), state=None)

    dp.register_message_handler(command_view_opened_schedule,
        commands=['посмотреть_мое_свободное_расписание'])
    dp.register_message_handler(command_view_opened_schedule,
        Text(equals='посмотреть мое свободное расписание', ignore_case=True), state=None)

    dp.register_message_handler(command_get_view_photos_schedule,
        commands=['посмотреть_фотографии_расписания'])
    dp.register_message_handler(command_get_view_photos_schedule,
        Text(equals='посмотреть фотографии расписания', ignore_case=True), state=None)

    dp.register_message_handler(command_get_view_photo_schedule,
        commands=['посмотреть_фотографию_расписания'])
    dp.register_message_handler(command_get_view_photo_schedule,
        Text(equals='посмотреть фотографию расписания', ignore_case=True), state=None)
    dp.register_message_handler(get_schedule_photo_to_view,
        state=FSM_Admin_get_view_schedule_photo.schedule_photo_name)
    
    dp.register_message_handler(delete_photo_schedule, commands=['удалить_фото_расписания'])
    dp.register_message_handler(delete_photo_schedule,
        Text(equals='удалить фото расписания', ignore_case=True), state=None)
    dp.register_message_handler(get_schedule_photo_to_delete,
        state=FSM_Admin_delete_schedule_photo.schedule_photo_name)
    
    dp.register_message_handler(command_change_schedule, commands=['изменить_мое_расписание'])
    dp.register_message_handler(command_change_schedule,
        Text(equals='изменить мое расписание', ignore_case=True), state=None)
    
    dp.register_message_handler(get_event_date, state=FSM_Admin_change_schedule.event_name)
    dp.register_message_handler(get_new_state_event_in_schedule,
        state=FSM_Admin_change_schedule.event_change)
    dp.register_message_handler(set_new_state_event_in_schedule,
        state=FSM_Admin_change_schedule.month_or_day_get_name_for_new_state_schedule)

    dp.register_message_handler(get_answer_choice_new_date_or_no_date_in_tattoo_order,
        state=FSM_Admin_change_schedule.get_answer_choice_new_date_or_no_date_in_tattoo_order)
    dp.register_message_handler(get_anwser_to_notify_client,
        state=FSM_Admin_change_schedule.get_anwser_to_notify_client)

    # dp.register_message_handler(get_new_day_name_if_month_is_not_succsess,
    #                             state=FSM_Admin_change_schedule.get_new_day_name_if_month_is_not_succsess)
    
    #-------------------------------------------------------DELETE SCHEDULE------------------------------------------------------

    dp.register_message_handler(command_delete_date_schedule, commands=['удалить_дату_в_расписании'])
    dp.register_message_handler(command_delete_date_schedule,
        Text(equals='удалить дату в расписании', ignore_case=True), state=None)
    
    dp.register_message_handler(delete_schedule_date, state=FSM_Admin_delete_schedule_date.date_name)