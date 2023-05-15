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
        for j in range(0, 1):
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
    photo = message.photo[0].file_id
    async with state.proxy() as data:
        photo_name = data['name_schedule_photo']
    new_schedule_photo = {
        "name"  : photo_name,
        "photo" : photo
    }
    await set_to_table( tuple(new_schedule_photo.values()), 'schedule_photo')
    await message.reply(f'Отлично! Ты добавила фото календаря! \n\n'\
        f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
        reply_markup= kb_admin.kb_schedule_commands)
    await state.finish()


class FSM_Admin_create_new_date_to_schedule(StatesGroup):
    event_type_choice = State()
    date_choice = State()
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
    if message.text.lower() in ['тату заказ', 'консультация']:
        async with state.proxy() as data:
            data['event_type'] = message.text.lower()
        await FSM_Admin_create_new_date_to_schedule.next() # -> choice_how_to_create_new_date_to_schedule
        # [ 'Хочу ввести конкретную дату', 'Хочу выбрать день недели и месяц']
        await message.reply(
            f'Хорошо, ты выбрала добавить в расписание {message.text}'\
            ' Хочешь ввести конкретную дату, или просто выбрать месяц и день недели?',
            reply_markup= kb_admin.kb_new_date_choice)
    else:
        await message.reply('Выбери, пожалуйста, слова из представленного \
            выбора кнопок - тату заказ или консультация.', 
            reply_markup= kb_admin.kb_event_type_schedule)


async def choice_how_to_create_new_date_to_schedule(
    message: types.Message, state: FSMContext):
    await FSM_Admin_create_new_date_to_schedule.next()
    if message.text == 'Хочу ввести конкретную дату':
        async with state.proxy() as data:
            data['user_id'] = message.from_user.id
        
        for i in range(2):
            await FSM_Admin_create_new_date_to_schedule.next() # -> get_day_by_date_for_schedule
        await message.reply('Давай выберем конкретную дату. Введи ее',
            reply_markup=await DialogCalendar().start_calendar())
    else:
        await message.reply('Давай выберем месяц. Выбери имя месяца из списка',
            reply_markup= kb_admin.kb_month_for_schedule)


# добавляем месяц и выбираем день недели
async def get_month_for_schedule(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['month_name'] = message.text
        data['month_number'] = await get_month_number_from_name(message.text)
        data['user_id'] = message.from_user.id
    await FSM_Admin_create_new_date_to_schedule.next() # -> get_day_for_schedule
    await message.reply('Хорошо. Какой это день недели?',
        reply_markup = kb_admin.kb_days_for_schedule)


# добавляем недели и выбираем начало рабочего дня
async def get_day_for_schedule(message: types.Message, state: FSMContext): 
    if message.text != 'Хочу ввести конкретную дату':
        async with state.proxy() as data:
            data['date'] = message.text
        for i in range(2):
            await FSM_Admin_create_new_date_to_schedule.next() # -> process_hour_timepicker_start_time
            
        await message.reply('Отлично, давай определимся со временем.'\
            ' С какого времени начинается твой рабочее расписание в этот день?',
            reply_markup = await FullTimePicker().start_picker())
    else:
        await FSM_Admin_create_new_date_to_schedule.next() # -> get_day_by_date_for_schedule
        await message.reply("Хорошо, выбери конкретную дату",
            reply_markup = await DialogCalendar().start_calendar())


@dp.callback_query_handler(dialog_cal_callback.filter(), 
    state=FSM_Admin_create_new_date_to_schedule.day_by_date)
async def get_day_by_date_for_schedule(callback_query: CallbackQuery,
    callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data) # type: ignore
    username_id = 0
    async with state.proxy() as data:
        username_id = data['user_id']
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали {date.strftime("%d/%m/%Y")}'
        )
        if datetime(
            year=int(date.strftime("%Y")),
            month=int(date.strftime("%m")),
            day=int(date.strftime("%d"))) > datetime.now():
            # async def load_datemiting(message: types.Message, state: FSMContext):
            async with state.proxy() as data:
                data['date'] =  f'{date.strftime("%d/%m/%Y")}' #  message.text
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
            f'Вы выбрали начало рабочего дня в {r.time.strftime("%H:%M:%S")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            username_id = data['user_id']
            if int(r.time.strftime("%H")) > 8 and int(r.time.strftime("%H")) < 24:
                
                data['start_time_in_schedule'] = r.time.strftime("%H:%M:%S")
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
            f'Вы выбрали конец рабочего дня в {r.time.strftime("%H:%M:%S")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            username_id = data['user_id']
            start_time = data['start_time_in_schedule']
            if r.time.strftime("%H:%M:%S") > start_time:
                data['end_time_in_schedule'] = r.time.strftime("%H:%M:%S")
                
                date = data['date']
                month_name = data['month_name']
                month_number = data['month_number']
                end_time = data['end_time_in_schedule']
                
                if '/' in data['date']:    
                    month_name_from_number = await get_month_from_number(month_number, 'ru')
                    if month_name_from_number != month_name:
                        # await FSM_Admin_create_new_date_to_schedule.next()
                        await bot.send_message(username_id,
                            f'Дата {date} и месяц {month_name} не совпадают. '\
                            'Введите месяц и дату в этом месяце корректно',
                            reply_markup = await DialogCalendar().start_calendar())
                    else:
                        new_event_to_schedule_bool = True
                else:
                    new_event_to_schedule_bool = True
            
                if new_event_to_schedule_bool:
                    schedule_id = await generate_random_order_number(CODE_LENTH)
                    if '/' in date:
                        new_schedule_event = {
                            'id': int(schedule_id),
                            "start_time" :      start_time,
                            "end_time" :        end_time,
                            "date" :            date,
                            "month_name" :      month_name,
                            "month_number":     month_number,
                            "status":          'Свободен',
                            "event_type":       data['event_type']
                            }
                        await set_to_table( tuple(new_schedule_event.values()), 'schedule_calendar')
                        await bot.send_message(username_id,
                            f'Отлично, теперь в {month_name} в {date} c {start_time} ' \
                            f'по {end_time} у тебя рабочее время!',
                            reply_markup = kb_admin.kb_schedule_commands)
                    else:
                        dates = await get_dates_from_month_and_day_of_week(month = month_name, day = date)
                        dates_str, i = '', 1
                        for iter_date in dates:
                            new_schedule_event = {
                                'id': int(schedule_id) + i,
                                "start_time" :      start_time,
                                "end_time" :        end_time,
                                "date" :            iter_date,
                                "month_name" :      month_name,
                                "month_number" :    month_number,
                                "status":           'Свободен',
                                "event_type":       data['event_type']
                                }
                            i += 1
                            dates_str += f'{iter_date}, '
                            await set_to_table(tuple(new_schedule_event.values()), 'schedule_calendar') 
                        await bot.send_message(username_id,
                            f'Отлично, теперь в {month_name} все {date}'\
                            f' ({dates_str[:len(dates_str)-2]})'\
                            f' c {start_time} по {end_time} у тебя рабочее время!',
                            reply_markup=kb_admin.kb_schedule_commands)
                    await state.finish()
            else:
                await bot.send_message(username_id, 
                    f'Время окончания работы должно быть позже времени начала работ.'\
                    ' Введи время заново',
                    reply_markup= await FullTimePicker().start_picker())


@dp.callback_query_handler(dialog_cal_callback.filter(), 
    state=FSM_Admin_create_new_date_to_schedule.get_date_if_wrong_month)
async def get_day_by_date_for_schedule_if_wrong_month_and_date(callback_query: CallbackQuery, 
    callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)# type: ignore
    username_id = 0
    new_event_to_schedule_bool = False
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали {date.strftime("%d/%m/%Y")}'
        )
        # async def load_datemiting(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            data['date'] =  f'{date.strftime("%d/%m/%Y")}' #  message.text
            username_id = data['user_id']
            date = data['date']
            month_name = data['month_name']
            month_number = data['month_number']
            start_time = data['start_time_in_schedule']
            end_time = data['end_time_in_schedule']
            if '/' in data['date']:    
                if date.strftime("%m") != month_number:
                    await bot.send_message(username_id, f'Дата {date} не совпадает.'\
                        ' Введите месяц и дату в этом месяце корректно',
                        reply_markup=await DialogCalendar().start_calendar())
                else:
                    new_event_to_schedule_bool = True
            else:
                new_event_to_schedule_bool = True
            
            if new_event_to_schedule_bool:
                schedule_id = await generate_random_order_number(CODE_LENTH)
                with Session(engine) as session:
                        new_schedule_event = ScheduleCalendar(
                            schedule_id=   int(schedule_id),
                            start_time=    start_time,
                            end_time=      end_time,
                            date=          date,
                            status=        'Свободен',
                            event_type=    data['event_type']
                        )
                        session.add(new_schedule_event)
                        session.commit()
                
                await bot.send_message(username_id,
                    f"Отлично, теперь в {date.strftime('%d/%m/%Y')} c {start_time}"\
                    f" по {end_time} у тебя рабочее время!",
                    reply_markup= kb_admin.kb_schedule_commands)
                await state.finish()


#------------------------------------------------------- VIEW SCHEDULE-----------------------------------
async def get_view_schedule(user_id: int, schedule: ScalarResult[ScheduleCalendar]):
    if schedule == []:
        await bot.send_message(user_id, 
            f'❌ У тебя пока нет расписания. Хочешь что-нибудь еще сделать?',
            reply_markup= kb_admin.kb_schedule_commands)
    else:
        headers  = ['N', 'Месяц', 'Дата', 'Время начала', 'Время конца', 'Статус', 'Тип', 'Заказы']
        table = PrettyTable(headers, left_padding_width = 0, right_padding_width=0)  # Определяем таблицу
        i = 0
        for date in schedule:
            order_number = ''
            # orders = await get_info_many_from_table('tattoo_orders', 'schedule_id', date[0])
            orders = Session(engine).scalars(select(TattooOrders).where(TattooOrders.schedule_id == date.schedule_id))
            if orders != []:
                for order in orders:
                    order_number += f'{order.tattoo_order_number} '
            else:
                order_number = 'Нет заказов'
            i+=1
            table.add_row([i, date.date.strftime('%m'), date.date.strftime('%d/%m/%Y'), 
                date.start_time, date.end_time, date.status, date.event_type, order_number])

        await bot.send_message(user_id, f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
        # table = PrettyTable(headers, left_padding_width = 0, right_padding_width=0)


# /посмотреть_мое_расписание
async def command_view_schedule(message: types.Message):
    if message.text == 'посмотреть мое расписание' and str(message.from_user.username) in ADMIN_NAMES:
        schedule = Session(engine).scalars(select(ScheduleCalendar))
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
        schedule = Session(engine).scalars(select(ScheduleCalendar).where(ScheduleCalendar.status == 'Занят'))
        await get_view_schedule(message.from_user.id, schedule) 


# /посмотреть мое свободное расписание
async def command_view_opened_schedule(message: types.Message):
    if message.text == 'посмотреть мое свободное расписание' and \
        str(message.from_user.username) in ADMIN_NAMES:
        schedule = Session(engine).scalars(select(ScheduleCalendar).where(ScheduleCalendar.status == 'Свободен'))
        await get_view_schedule(message.from_user.id, schedule)  


#------------------------------------------------------- VIEW ALL PHOTOS SCHEDULE-----------------------------------
# /посмотреть_фотографии_расписания
async def command_get_view_photos_schedule(message:types.Message):
    if message.text.lower() in \
        ['/посмотреть_фотографии_расписания', 'посмотреть фотографии расписания'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            photos_schedule  = Session(engine).scalars(select(SchedulePhoto))
            for photo in photos_schedule:
                await bot.send_photo(message.chat.id, photo.photo, 
                    f"Название фотографии календаря: 0{photo.name}")
            await message.reply('Что еще хочешь сделать?')


#------------------------------------------------------- VIEW PHOTO SCHEDULE-----------------------------------
class FSM_Admin_get_view_schedule_photo(StatesGroup):
    schedule_photo_name = State()


# /посмотреть_одну_фотографию_расписания
async def command_get_view_photo_schedule(message:types.Message):
    if message.text.lower() in \
        ['/посмотреть_фотографии_расписания', 'посмотреть фотографию расписания'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            photos_schedule  = await get_info_many_from_table('schedule_photo')
            kb_photos_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            for photo in photos_schedule:
                kb_photos_schedule.add(KeyboardButton( photo[0]))
            kb_photos_schedule.add(KeyboardButton('Назад'))
            await FSM_Admin_get_view_schedule_photo.schedule_photo_name.set()
            await message.reply(f"Какую фотографию хочешь посмотреть?", reply_markup=kb_photos_schedule)
            
async def get_schedule_photo_to_view(message: types.Message, state: FSMContext ):
    photos_schedule  = await get_info_many_from_table('schedule_photo')
    photo_names_list = []
    for photo in photos_schedule:
        photo_names_list.append(photo[0])
        
    if message.text in photo_names_list:
        photo = await get_info_many_from_table('schedule_photo', 'name', message.text)
        photo = list(photo[0])
        await bot.send_photo(message.chat.id, photo[1], 
            f"Название фотографии календаря: {photo[0]}")
        await message.reply('Что еще хочешь сделать?', reply_markup=kb_admin.kb_schedule_commands)
        await state.finish()
        
    elif message.text == 'Назад':
        await message.reply('Хорошо, вы вернулись в меню расписания. Что хочешь сделать?',
            reply_markup= kb_admin.kb_schedule_commands)
        await state.finish()
    else:
        await message.reply('Пожалуйста, выбери наименование фотографии расписания из списка '\
            'или отмени действие')


#------------------------------------------------------- DELETE PHOTO SCHEDULE-----------------------------------
class FSM_Admin_delete_schedule_photo(StatesGroup):
    schedule_photo_name = State()


# /удалить_фото_расписания
async def delete_photo_schedule(message: types.Message):
    if message.text.lower() in ['/удалить_фото_расписания', 'удалить фото расписания'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        photos_schedule  = await get_info_many_from_table('schedule_photo')
        kb_photos_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
        for photo in photos_schedule:
            kb_photos_schedule.add(KeyboardButton( photo[0]))
            await bot.send_photo(message.chat.id, photo[1],
                f"Название фотографии календаря: {photo[0]}")
        kb_photos_schedule.add(KeyboardButton('Назад'))
        await FSM_Admin_delete_schedule_photo.schedule_photo_name.set()
        await message.reply('Какое фото хочешь удалить?',
            reply_markup= kb_photos_schedule)

async def get_schedule_photo_to_delete(message: types.Message, state: FSMContext ):
    photos_schedule  = await get_info_many_from_table('schedule_photo')
    photo_names_list = []
    for photo in photos_schedule:
        photo_names_list.append(photo[0])
        
    if message.text in photo_names_list:
        await delete_info('schedule_photo', 'name', message.text)
        await message.reply('Отлично, вы удалили фото из расписания? Хочешь сделать что-то еще?',
            reply_markup= kb_admin.kb_schedule_commands)
        await state.finish()
    elif message.text in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
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

    get_new_date_if_month_is_not_succsess = State()
    # get_new_day_name_if_month_is_not_succsess = State()

# /изменить_мое_расписание, изменить мое расписание
async def command_change_schedule(message: types.Message):  # state=None
    if message.text == 'изменить мое расписание' and \
        str(message.from_user.username) in ADMIN_NAMES:
        # schedule = await get_info_many_from_table('schedule_calendar')
        schedule = Session(engine).scalars(select(ScheduleCalendar))
        headers  = ['Номер', 'Месяц', 'Дата', 'Время начала','Время конца', 'Статус', 'Тип']
        table = PrettyTable(headers, left_padding_width = 0, right_padding_width=0)  # Определяем таблицу
        kb_date_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
        i = 0
        for date in schedule:
            # date = list(date)
            row_item = f'id:{date[0]}|{date[4]} {date[3]} c {date[1]} по '\
                f'{date[2]} статус: {date[6]} тип: {date[7]}\n'
            i+=1
            table.add_row([i, date[4], date[3], date[1], date[2], date[6], date[7]])
            kb_date_schedule.add(KeyboardButton(row_item))
            
        await message.reply(f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
        await FSM_Admin_change_schedule.event_name.set()
        await bot.send_message(message.from_id,
            'Какую позицию хочешь изменить? Выбери из списка',
            reply_markup= kb_date_schedule)


async def get_event_date(message:types.Message, state: FSMContext ): # state=FSM_Admin_change_schedule.event_name
    schedule = await get_info_many_from_table('schedule_calendar')
    data_list = []
    for date in schedule:
        data_list.append(f'id:{date[0]}|{date[4]} {date[3]} c {date[1]} по '\
            f'{date[2]} статус: {date[6]} тип: {date[7]}')
        
    if message.text in data_list:
        async with state.proxy() as data:
            data['event_date_old'] = message.text 
            data['schedule_id'] = message.text.split("|")[0].split(":")[1]
            data['user_id'] = message.from_user.id
        await FSM_Admin_change_schedule.next()
        # ['Месяц', 'День недели', 'Время начала работы', 'Время окончания работы', 'Дату', 'Статус']
        await message.reply(f'Что хочешь изменить? \n', reply_markup= kb_admin.kb_date_states)
        
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_schedule_commands)
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# state=FSM_Admin_change_schedule.event_change    
async def get_new_state_event_in_schedule(message:types.Message, state: FSMContext ): 
    async with state.proxy() as data:
        data['new_event_date_state'] = message.text
    await FSM_Admin_change_schedule.next()  
    
    if message.text == 'Дату':
        await FSM_Admin_change_schedule.next()
        await FSM_Admin_change_schedule.next()
        await message.reply("Хорошо, выбери конкретную дату",
            reply_markup= await DialogCalendar().start_calendar())
        
    elif message.text == 'Месяц':
        await FSM_Admin_change_schedule.next()  
        await message.reply('Хорошо, выбери выбери новый месяц',
            reply_markup= kb_admin.kb_month_for_schedule)
        
    elif message.text == 'День недели':
        await FSM_Admin_change_schedule.next()
        await message.reply('Хорошо, выбери новый день недели',
            reply_markup= kb_admin.kb_days_for_schedule)
        
    elif message.text == 'Время начала работы':
        await message.reply('Хорошо, выбери новое время начала работы',
            reply_markup= await FullTimePicker().start_picker())
        
    elif message.text == 'Время окончания работы':
        await message.reply('Хорошо, выбери новое время окончания работы',
            reply_markup= await FullTimePicker().start_picker())
    
    # TODO При изменении статуса нужно проверять,
    # TODO есть ли какой-либо заказ в это время, и менять дату расписания для заказа + оповещать пользователя
    elif message.text == 'Статус':
        await FSM_Admin_change_schedule.next()  
        
        await message.reply('Хорошо, выбери новый статус. Какой статус поставим?',
            reply_markup= kb_admin.kb_free_or_close_event_in_schedule)


async def update_schedule_table(state: FSMContext, updating_columns_list: list, updating_values_list: list):
    async with state.proxy() as data:
        username_id = data['user_id']
        schedule_id = data['schedule_id']
        event_date_old = data['event_date_old'].split("|")[1].split()
        
    for i in range(len(updating_values_list)):
        await update_info('schedule_calendar', 'id', schedule_id, updating_columns_list[i], updating_values_list[i])
        
    event_date_new = await get_info_many_from_table('schedule_calendar', 'id', schedule_id)
    event_date_new = list(event_date_new[0])
    old_data_to_send = {
        "month":        event_date_old[0],
        "date":         event_date_old[1],
        "start time":   event_date_old[3],
        "end time":     event_date_old[5],
        "state":        event_date_old[7],
        "type":         event_date_old[9] + ' ' + event_date_old[10],
    }
    
    new_data_to_send = {
        "month":        event_date_new[4],
        "date":         event_date_new[3],
        "start time":   event_date_new[1],
        "end time":     event_date_new[2],
        "state":        event_date_new[6],
        "type":         event_date_new[7]
    }
    headers  = ['Месяц', 'Дата', 'Время начала','Время конца', 'Статус', 'Тип']
    table = PrettyTable(headers, left_padding_width = 1, right_padding_width= 1)  # Определяем таблицу
    table.add_row(list(old_data_to_send.values()))
    await bot.send_message(username_id, f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
    
    table_next = PrettyTable(headers, left_padding_width = 1, right_padding_width= 1)
    table_next.add_row(list(new_data_to_send.values()))
    await bot.send_message(username_id, f'<pre>{table_next}</pre>', parse_mode=types.ParseMode.HTML)
        
    await bot.send_message(username_id, f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
        reply_markup= kb_admin.kb_schedule_commands)


# выбираем новую дату в календаре
@dp.callback_query_handler(dialog_cal_callback.filter(), state=FSM_Admin_change_schedule.new_date_in_schedule)
async def get_changing_day_by_date_for_schedule(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data) # type: ignore
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали новую дату {date.strftime("%d/%m/%Y")}'
        )
        async with state.proxy() as data:
            new_event_date_state = data['new_event_date_state']
            
        column_name_for_update = {'Дату': 'date'}
        
        await update_schedule_table(
            state= state,
            updating_columns_list= [column_name_for_update[new_event_date_state]],
            updating_values_list= [date.strftime("%d/%m/%Y")]
        )
        
        await state.finish()


# выбираем новое время начала или конца рабочего дня
@dp.callback_query_handler(full_timep_callback.filter(), state=FSM_Admin_change_schedule.start_time_in_schedule)
async def process_hour_timepicker_start_or_end_time(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)# type: ignore
    column_name_for_update = ''
    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время {r.time.strftime("%H:%M:%S")} ',
        )
        # await callback_query.message.delete_reply_markup()
        async with state.proxy() as data:
            new_event_date_state = data['new_event_date_state']
        column_name_for_update = {
            'Время начала работы':      'start_time',
            'Время окончания работы':   'end_time'
        }
        await update_schedule_table(
            state= state,
            updating_columns_list= [column_name_for_update[new_event_date_state]],
            updating_values_list= [r.time.strftime("%H:%M:%S")]
        )
        await state.finish()


# state=FSM_Admin_change_schedule.month_or_day_get_name_for_new_state_schedule)
async def set_new_state_event_in_schedule(message:types.Message, state: FSMContext): 

    async with state.proxy() as data:
        schedule_id = data['schedule_id']
        new_event_date_state = data['new_event_date_state']
        
    if new_event_date_state == 'Месяц':
        updating_columns_list = ['month_name', 'month_number']
        updating_values_list = [message.text, await get_month_number_from_name(message.text)]
        
    elif new_event_date_state == 'День недели':
        updating_columns_list = ['date']
        updating_values_list = [message.text]
        
    elif new_event_date_state == 'Статус':
        updating_columns_list = ['status']
        updating_values_list =  [message.text]
        
        tattoo_orders = await get_info_many_from_table('tattoo_orders', 'schedule_id', schedule_id)
        
        if tattoo_orders != []:
            data['tattoo_order_number'] = list(tattoo_orders[0])[9]
            # ['Хочу поставить новую дату для этого тату заказа', 
            # 'Хочу оставить дату для этого тату заказа неопределенной']
            await FSM_Admin_change_schedule.next() 
            await FSM_Admin_change_schedule.next()
            await message.reply(f'С этим расписанием у вас связан тату заказ. '\
                'Хочешь изменить изменить дату встречи, или хочешь поставить '\
                'неизвестную дату встречи на этот заказ?',
            reply_markup= kb_admin.kb_choice_new_date_or_no_date_in_tattoo_order)
                
        await update_schedule_table(state, updating_columns_list, updating_values_list)
        await state.finish()


async def get_answer_choice_new_date_or_no_date_in_tattoo_order(message:types.Message, state: FSMContext):
    if message.text == 'Хочу поставить новую дату для этого тату заказа':
        await FSM_Admin_change_schedule.next()
        await message.reply(f'Хорошо, введи новую дату для тату заказа', 
            reply_markup= await DialogCalendar().start_calendar())

    elif message.text == 'Хочу оставить дату для этого тату заказа неопределенной':
        async with state.proxy() as data:
            data['user_id'] = message.from_user.id
            tattoo_order_number = data['tattoo_order_number']
            # date_meeting TEXT, date_time TEXT,
        await update_info('tattoo_orders', 'tattoo_order_number', tattoo_order_number, 'date_meeting',
            'Без даты встречи')
        
        await update_info('tattoo_orders', 'tattoo_order_number', tattoo_order_number, 'date_time',
            'Без времени встречи')
        
        await update_info('tattoo_orders', 'tattoo_order_number', tattoo_order_number, 'schedule_id', '0')

        await message.reply(f'Хорошо, тату заказ № {tattoo_order_number} теперь без даты и времени встречи',
            reply_markup=kb_admin.kb_main)

    else:
        await message.reply(f'Ответь на вопрос корректно, пожалуйста')

@dp.callback_query_handler(dialog_cal_callback.filter(),
    state=FSM_Admin_change_schedule.get_new_date_for_tattoo_order)
async def process_get_new_date_for_new_data_schedule(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)# type: ignore
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали новую дату {date.strftime("%d/%m/%Y")}')

        async with state.proxy() as data:
            data['date_meeting'] = date.strftime("%d/%m/%Y")
            user_id = data['user_id']

        await FSM_Admin_change_schedule.next()
        await bot.send_message(
            user_id, f' Хорошо, а теперь введи новое время для тату заказа',
            reply_markup = await FullTimePicker().start_picker())


# выбираем новое время начала 
@dp.callback_query_handler(full_timep_callback.filter(),
    state=FSM_Admin_change_schedule.start_time_in_tattoo_order)
async def process_hour_timepicker_new_start_time_in_tattoo_order(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)# type: ignore

    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время {r.time.strftime("%H:%M:%S")} ',
        )
        async with state.proxy() as data:
            user_id = data['user_id']
            data['start_time_in_tattoo_order'] = r.time.strftime("%H:%M:%S")
        await FSM_Admin_change_schedule.next()
        await bot.send_message(user_id, f'А теперь введи примерное время окончания сеанса')


# выбираем новое время конца сеанса
@dp.callback_query_handler(full_timep_callback.filter(),
    state=FSM_Admin_change_schedule.end_time_in_tattoo_order)
async def process_hour_timepicker_new_end_time_in_tattoo_order(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data)# type: ignore

    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время {r.time.strftime("%H:%M:%S")} ')
        date_meeting, user_id, end_time_in_tattoo_order = '', '', ''
        async with state.proxy() as data:
            start_time_in_tattoo_order = data['start_time_in_tattoo_order']
            end_time_in_tattoo_order = r.time.strftime("%H:%M:%S")
            tattoo_order_number = data['tattoo_order_number']

            user_id = data['user_id']
            date_meeting = data['date_meeting']
            schedule_id = await generate_random_order_number(CODE_LENTH)

        await update_info('tattoo_orders', 'tattoo_order_number',
            tattoo_order_number, 'date_meeting', 'Без даты встречи')

        await update_info('tattoo_orders', 'tattoo_order_number',
            tattoo_order_number, 'date_time', 'Без времени встречи')
        
        schedule_id = await generate_random_order_number(CODE_LENTH)
        new_schedule_event = {
            "schedule_id" :     schedule_id,
            "start_time" :      start_time_in_tattoo_order,
            "end_time"  :       end_time_in_tattoo_order, 
            "date"  :           date_meeting,
            "month_name"  :     await get_month_from_number(int(date_meeting.split('/')[1]), "ru"),
            "month_number"  :   date_meeting.split('/')[1],
            "status"  :         'Занят',
            "event_type":       'тату заказ'
        }

        await set_to_table( tuple(new_schedule_event.values()) , 'schedule_calendar') 
        
        await bot.send_message(
            user_id, f'У тату заказа № {tattoo_order_number} поменялась дата на {date_meeting} '\
            f'и на время {start_time_in_tattoo_order}. А также добавилась новая дата в календарь. '\
            'Что еще хочешь сделать?',
            reply_markup = kb_admin.kb_schedule_commands)
        await state.finish()


@dp.callback_query_handler(dialog_cal_callback.filter(),
    state=FSM_Admin_change_schedule.get_new_date_if_month_is_not_succsess)
async def process_get_new_date_if_month_is_not_succsess(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)# type: ignore
    if selected:
        await callback_query.message.answer(
            f'Вы выбрали новую дату {date.strftime("%d/%m/%Y")}'
        )
        update_event_to_schedule_bool = False
        async with state.proxy() as data:
            
            month_name = data['month_name']
            new_month_number = date.strftime("%m")
            new_month_name = await get_month_from_number(int(new_month_number), 'ru')
            if new_month_name != month_name:
                await bot.send_message(data['user_id'], 
                    f'Все еще неверная дата и месяц. Введи дату соответствующую месяцу {month_name}.',
                    reply_markup= await DialogCalendar().start_calendar()) 
            else:
                update_event_to_schedule_bool = True
            
        # Если обновленный месяц подошел, т.е. в дате нет / 
        # или наименование обновленного месяца совпадает со значением в %d/%m/%Y
        if update_event_to_schedule_bool:
            updating_columns_list = ['month_name', 'month_number', 'date']
            updating_values_list = [
                month_name, 
                await get_month_number_from_name(month_name), 
                date.strftime("%d/%m/%Y")
            ]
            await update_schedule_table(
                state= state,
                updating_columns_list= updating_columns_list,
                updating_values_list= updating_values_list
            )
            await state.finish()


async def get_new_day_name_if_month_is_not_succsess(message:types.Message, state: FSMContext):
    if message.text in kb_admin.days:
        async with state.proxy() as data:
            updating_values_list = [data['month_name'], data['month_number'], message.text]
            
        updating_columns_list = ['month_name', 'month_number', 'date']
        await update_schedule_table(
            state= state,
            updating_columns_list= updating_columns_list,
            updating_values_list= updating_values_list
        )
        await state.finish()
    else:
        await message.reply('Введи день недели корректно, выбери из списка')


#----------------------------------------- DELETE SCHEDULE EVENT-----------------------------------    
class FSM_Admin_delete_schedule_date(StatesGroup):
    date_name = State()


# удалить дату в расписании
async def command_delete_date_schedule(message: types.Message):
    if message.text in ['удалить дату в расписании', '/удалить_дату_в_расписании'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        schedule = await get_info_many_from_table('schedule_calendar')
        if schedule == []:
            await message.reply(f'{MSG_NO_SCHEDULE_IN_TABLE}. {MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_admin.kb_schedule_commands)
        else:
            kb_date_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            date_list = ''
            for date in schedule:
                date = tuple(date)
                str_date = f'id:{date[0]}|{date[4]} {date[3]} c {date[1]} по {date[2]},'\
                    f' тип: {date[7]}, статус: {date[6]}\n'
                date_list += str_date + '\n'
                kb_date_schedule.add(KeyboardButton(str_date))
                
            kb_date_schedule.add(kb_client.cancel_btn)
            await message.reply(f'Вот твое расписание:\n{date_list}',
                reply_markup= kb_admin.kb_main)
            
            await FSM_Admin_delete_schedule_date.date_name.set()
            await message.reply(f'Какую позицию хочешь изменить? Выбери из списка\n',
                reply_markup= kb_date_schedule)


async def delete_schedule_date(message:types.Message, state: FSMContext):
    if message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_tattoo_order_commands)
    else:
        schedule_id = message.text.split("|")[0].split(':')[1]
        deleted_schedule = message.text.split("|")[1]
        await delete_info('schedule_calendar', 'id', schedule_id)
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
    dp.register_message_handler(get_photo_to_schedule, content_types=['photo'],
        state=FSM_Admin_create_new_photo_to_schedule.photo_to_schedule)

    dp.register_message_handler(command_create_new_date_to_schedule, commands=['добавить_дату_в_расписание'])
    dp.register_message_handler(command_create_new_date_to_schedule,
        Text(equals='добавить дату в расписание', ignore_case=True), state=None)
    dp.register_message_handler(choice_event_type_in_schedule,
        state=FSM_Admin_create_new_date_to_schedule.event_type_choice)
    dp.register_message_handler(choice_how_to_create_new_date_to_schedule,
        state=FSM_Admin_create_new_date_to_schedule.date_choice)
    dp.register_message_handler(get_month_for_schedule,
        state=FSM_Admin_create_new_date_to_schedule.month_name)
    dp.register_message_handler(get_day_for_schedule, state=FSM_Admin_create_new_date_to_schedule.day_name)

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

    # dp.register_message_handler(get_new_day_name_if_month_is_not_succsess,
    #                             state=FSM_Admin_change_schedule.get_new_day_name_if_month_is_not_succsess)
    
    #-------------------------------------------------------DELETE SCHEDULE------------------------------------------------------

    dp.register_message_handler(command_delete_date_schedule, commands=['удалить_дату_в_расписании'])
    dp.register_message_handler(command_delete_date_schedule,
        Text(equals='удалить дату в расписании', ignore_case=True), state=None)
    
    dp.register_message_handler(delete_schedule_date, state=FSM_Admin_delete_schedule_date.date_name)