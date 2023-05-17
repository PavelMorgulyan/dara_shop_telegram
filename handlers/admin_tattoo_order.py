
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import generate_random_order_number, \
    CODE_LENTH, ORDER_CODE_LENTH, ADMIN_NAMES, CALENDAR_ID

from db.db_setter import set_to_table
from db.db_updater import update_info
from db.db_delete_info import delete_info
from db.db_getter import get_info_many_from_table, DB_NAME, sqlite3

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

from validate import check_pdf_document_payment, check_photo_payment
#from diffusers import StableDiffusionPipeline
#import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# from datetime import datetime
import datetime
from aiogram.types.message import ContentType
from aiogram_calendar import simple_cal_callback, dialog_cal_callback, DialogCalendar
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback
from aiogram_timepicker import result, carousel, clock

from prettytable import PrettyTable
from handlers.calendar_client import obj
from msg.main_msg import *
import re
from handlers.other import * 


#----------------------------------- TATTOO ORDER COMMANDS LIST-----------------------------------
async def get_tattoo_order_and_item_command_list(message: types.Message):
    if message.text.lower() in ['тату заказы', '/тату_заказы'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        await message.reply('Какую команду заказов тату хочешь выполнить?',
            reply_markup=kb_admin.kb_tattoo_order_commands)


#------------------------------------- TATTOO ORDER COMMANDS-----------------------------------
async def send_to_view_tattoo_order(message: types.Message, tattoo_orders: ScalarResult["Orders"]):

    for order in tattoo_orders:
        user = Session(engine).scalars(select(User).where(
            User.name == order.username)).one()
    
        username_telegram = 'Без телеграма' if user.telegram_name == '' else user.telegram_name
        username_phone = 'Без номера' if user.phone == '' else user.phone

        message_to_send = f'Тату заказ № {order.order_number} от {order.creation_date}\n'
        
        if order.order_type == 'постоянное тату':
            message_to_send += f"🕒 Дата и время встречи: {order.start_date_meeting.strftime('%d/%m/%Y %H:%M')}\n"
        
        message_to_send += \
            f'🪴 Тип тату: {order.order_type}\n'\
            f'🍃 Имя: {order.order_name}\n'\
            f'📏 Размер: {order.tattoo_size}\n'\
            f'📜 Описание тату: {order.tattoo_note}\n' \
            f'💬 Описание заказа: {order.order_note}\n'\
            f'🎨 {order.colored} тату\n'\
            f'👤 Местоположение тату: {order.bodyplace}\n'\
            f'- Цена заказа: {order.price}\n'\
            f'- Имя пользователя: {order.username}\n'\
            f'- Telegram пользователя: {username_telegram}\n'\
            f'- Телефон пользователя: {username_phone}\n'
            
            #f'💰 Цена: {ret[11]}'
            #f'🎚 Количество основных деталей: {ret[16]}\n'\
                
        if order.order_state in list(CLOSED_STATE_DICT.values()):
            message_to_send += f'❌ Состояние заказа: {order.order_state}\n'
        else:
            message_to_send += f'📃 Состояние заказа: {order.order_state}\n'
        
        if order.check_document not in ['Чек не добавлен', 'Без чека']:
            try:
                await bot.send_document(message.from_user.id, order.check_document, 'Чек на оплату заказа')
            except:
                await bot.send_photo(message.from_user.id, order.check_document, 'Чек на оплату заказа')


#------------------------------------------ посмотреть_тату_заказы--------------------------------
class FSM_Admin_get_info_orders(StatesGroup):
    order_status_name = State()


# /посмотреть_тату_заказы
async def command_get_info_tattoo_orders(message: types.Message): 
    # print("ищем заказы в таблице tattoo_orders") 
    if message.text in ['посмотреть тату заказы', '/посмотреть_тату_заказы'] and \
        str(message.from_user.username) in ADMIN_NAMES:

        orders_into_table = Session(engine).scalars(select(Orders)).all()
        if orders_into_table == []:
            await bot.send_message(message.from_id, MSG_NO_ORDER_IN_TABLE,
                reply_markup = kb_admin.kb_tattoo_order_commands)
        else:
            await FSM_Admin_get_info_orders.order_status_name.set()
            await bot.send_message(message.from_user.id, 
                f'Заказы в каком статусе хочешь посмотреть?',
                reply_markup = kb_admin.kb_order_statuses)


async def get_status_name(message: types.Message, state: FSMContext): 
    if message.text in statuses_order_lst:
        orders = Session(engine).scalars(select(Orders).where(
            Orders.order_state == message.text))
        
        if orders == []:
            await bot.send_message(message.from_user.id, MSG_NO_ORDER_IN_TABLE)
        else:
            await send_to_view_tattoo_order(message, orders)
            
        await bot.send_message(message.from_user.id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
        
    elif message.text in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await bot.send_message(message.from_user.id, MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
        
    else:
        await message.reply( "Пожалуйста, выбери заказ из списка или нажми \"Назад\"")


#------------------------------------- посмотреть_тату_заказ------------------------------
'''
    Открыт — заказ был создан в базе данных, но ещё не был обработан.
    Обработан — оплата была получена.
    Выполнен — вся работа по заказу завершена.
    Отклонен — заказ отклонен админом.
    Отложен — заказ ещё не обработан, так как в нём содержатся товары, которых нет в наличии. 
        Только для гифтбокса
    Аннулирован — заказ был отменён покупателем.
'''

class FSM_Admin_command_get_info_tattoo_order(StatesGroup):
    order_name = State()


# /посмотреть_тату_заказ
async def command_get_info_tattoo_order(message: types.Message): 
    if message.text in ['посмотреть тату заказ', '/посмотреть_тату_заказ'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        orders = Session(engine).scalars(select(TattooOrders))
        
        if orders == []:
            await message.reply(MSG_NO_ORDER_IN_TABLE)
        else: 
            kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
            await FSM_Admin_command_get_info_tattoo_order.order_name.set()
            # await send_to_view_tattoo_order(message, orders_into_table)
            for order in orders:
                kb_orders.add(KeyboardButton(f"{order.tattoo_order_number} \
                    \"{order.tattoo_name}\" статус: {order.order_state}"))
                
            kb_orders.add(KeyboardButton('Назад'))
            await bot.send_message(message.from_user.id, f'Какой заказ хочешь посмотреть?',
            reply_markup = kb_orders)


async def get_name_for_view_tattoo_order(message: types.Message, state: FSMContext): 
    if message.text not in LIST_BACK_COMMANDS:
        order = Session(engine).scalars(select(TattooOrders).where(
            TattooOrders.tattoo_order_number == message.text.split()[0]))
        
        await send_to_view_tattoo_order(message, order)
        await bot.send_message(message.from_user.id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_tattoo_order_commands)
        await state.finish()
        
    elif message.text in LIST_BACK_COMMANDS:
        await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
    else:
        await message.reply("Пожалуйста, выбери заказ из списка или нажми \"Назад\"")


#------------------------------------------- удалить_тату_заказ--------------------------------
class FSM_Admin_delete_tattoo_order(StatesGroup):
    tattoo_order_number = State()


# /удалить_тату_заказ
async def command_delete_info_tattoo_orders(message: types.Message): 
    if message.text in ['удалить тату заказ', '/удалить_тату_заказ'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        tattoo_orders = await get_info_many_from_table('tattoo_orders')
        if tattoo_orders == []:
            await message.reply('Прости, пока нет заказов в списке, а значит и удалять нечего. '\
                'Хочешь посмотреть что-то еще?', reply_markup= kb_admin.kb_tattoo_order_commands)
        else:
            kb_tattoo_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
            number_not_deleted_order = 0
            for ret in tattoo_orders:
                if ret[8] in list(CLOSED_STATE_DICT.values()):
                    # выводим наименования тату
                    number_not_deleted_order += 1
                    kb_tattoo_order_numbers.add(KeyboardButton(f"{ret[9]} \"{ret[1]}\" {ret[8]}"))
                    
            if number_not_deleted_order != 0:
                kb_tattoo_order_numbers.add(KeyboardButton('Назад'))
                await FSM_Admin_delete_tattoo_order.tattoo_order_number.set()
                await message.reply("Какой заказ хотите удалить?",
                    reply_markup= kb_tattoo_order_numbers)
            else:
                await message.reply(
                    f'Прости, пока нет заказов в списке, они все удалены. {MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                    reply_markup= kb_admin.kb_tattoo_order_commands)
            # await message.delete()


async def delete_info_tattoo_orders(message: types.Message, state: FSMContext):
    tattoo_orders = Session(engine).scalars(select(TattooOrders))
    choosen_kb_order_lst = []
    for order in tattoo_orders:
        choosen_kb_order_lst.append(
            f"{order.tattoo_order_number} \"{order.tattoo_name}\" {order.order_state}")
    
    if message.text in choosen_kb_order_lst:
        tattoo_order = Session(engine).scalars(select(TattooOrders).where(
            TattooOrders.tattoo_order_number == message.text.split()[0])).one()
        
        await delete_info('tattoo_orders', 'tattoo_order_number', message.text.split()[0])
        
        await update_info('schedule_calendar', 'id', tattoo_order[14], 'status', 'Свободен')
        await update_info(
            table_name= 'tattoo_orders', 
            column_name_condition='tattoo_order_number',
            condition_value= message.text.split()[0], 
            column_name_value= 'schedule_id', 
            value= 'Без даты ивента'
        )

        # service.events().delete(calendarId='primary', eventId='eventId').execute()
        ''' 
        print("---------------------------------")
        print(await obj.get_calendar_events(CALENDAR_ID))
        print("---------------------------------") 
        '''
        event_list = await obj.get_calendar_events(CALENDAR_ID)
        # TODO нужно удалять ивент из Google Calendar
        for event in event_list:
            if event['summary'].split()[4] == message.text.split()[0]:
                await obj.delete_event(CALENDAR_ID, event['id'])
        
        await message.reply(f'Заказ удален. {MSG_DO_CLIENT_WANT_TO_DO_MORE}', 
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
    else:
        await message.reply(MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()


#----------------------------- изменить_статус_тату_заказа--------------------------------
class FSM_Admin_tattoo_order_change_status(StatesGroup):
    tattoo_order_number = State()
    tattoo_order_new_status = State()
    get_answer_for_getting_check_document = State()
    get_price_for_check_document = State()
    get_check_document = State()


# /изменить_статус_тату_заказа, изменить статус тату заказа
async def command_tattoo_order_change_status(message: types.Message): 
    if message.text in ['изменить статус тату заказа', '/изменить_статус_тату_заказа'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        tattoo_orders = await get_info_many_from_table('tattoo_orders')
        kb_tattoo_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
        if tattoo_orders is None or tattoo_orders == []:
            await message.reply(f"{MSG_NO_ORDER_IN_TABLE}")
        else:
            for ret in tattoo_orders: # выводим номера тату заказов и их статус
                kb_tattoo_order_numbers.add(KeyboardButton(ret[9] + ' , статус: ' + ret[8])) 
            kb_tattoo_order_numbers.add(KeyboardButton('Назад'))
            await FSM_Admin_tattoo_order_change_status.tattoo_order_number.set()
            await message.reply("У какого заказа хотите поменять статус?",
                reply_markup= kb_tattoo_order_numbers)
    # await message.delete()


async def get_new_status_for_tattoo_order(message: types.Message, state: FSMContext): 
    if message.text != 'Назад':
        async with state.proxy() as data:
            data['tattoo_order_number'] = message.text.split()[0]
        await FSM_Admin_tattoo_order_change_status.next()
        
        await bot.send_message(message.from_id, MSG_SEND_ORDER_STATE_INFO)
        await bot.send_message(message.from_id, f'Хорошо, какой статус выставляем?',
            reply_markup= kb_admin.kb_change_status_order)
        
    elif message.text in LIST_BACK_TO_HOME + LIST_BACK_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_tattoo_order_commands)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def complete_new_status_for_tattoo_order(message: types.Message, state: FSMContext): 
    async with state.proxy() as data:
        tattoo_order_number = data['tattoo_order_number'] 
        data['new_state'] = message.text
    await update_info('tattoo_orders', 'tattoo_order_number', tattoo_order_number,
        'order_state', message.text)
    
    order = await get_info_many_from_table('tattoo_orders', 'tattoo_order_number', tattoo_order_number) 
    schedule_id = order[0][14]
    
    
    if message.text in ['Аннулирован', 'Отклонен']:
        await update_info('schedule_calendar', 'id', schedule_id, 'status', 'Свободен')
        
    if message.text in ['Обработан', 'Выполнен']:
        await FSM_Admin_tattoo_order_change_status.next()
        await message.reply(f'Хочешь добавить чек к заказу?',
            reply_markup= kb_client.kb_yes_no)
    else:
        await message.reply(
            f'Готово! Вы обновили статус заказа {tattoo_order_number} на \"{message.text}\"',
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish() #  полностью очищает данные


async def get_answer_for_getting_check_document(message: types.Message, state: FSMContext): 
    if message.text == kb_client.yes_str:
        await FSM_Admin_tattoo_order_change_status.next()
        await message.reply(f'Хорошо, на какую сумму чек?',
            reply_markup= kb_admin.kb_price )
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            tattoo_order_number = data['tattoo_order_number'] 
            new_state = data['new_state']
            
        await message.reply(
            f'Готово! Вы обновили статус заказа {tattoo_order_number} на \'{new_state}\'',
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
    else:
        await message.reply(
            f'На этот вопрос можно ответит только \'Да\' или \'Нет\'.Выбери правильный ответ',
            reply_markup= kb_client.kb_yes_no)


async def get_price_for_check_document(message: types.Message, state: FSMContext): 
    if message.text == 'Другая цена':
        await bot.send_message(message.from_id, 'Хорошо, укажи другую цену',
            reply_markup= kb_admin.kb_another_price)
        
    elif message.text in kb_admin.price + kb_admin.another_price:
        async with state.proxy() as data:
            data['tattoo_order_price'] = message.text
        await FSM_Admin_tattoo_order_change_status.next()
        await message.reply(f'Хорошо, а теперь приложи чек на эту сумму', 
            reply_markup= kb_client.kb_back_cancel)
        
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_tattoo_order_commands)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_check_document(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        tattoo_order_number = data['tattoo_order_number'] 
        price = data['tattoo_order_price']
        
    if message.content_type == 'document':
        check_doc_pdf = await check_pdf_document_payment(
            user_id= message.from_id, 
            price= price, 
            file_name= message.document.file_name, 
            file_id= message.document.file_id
        ) 
        
        if check_doc_pdf["result"]:
            await update_info('tattoo_orders', 'tattoo_order_number',
                tattoo_order_number, 'check_document', message.document.file_id)
            await state.finish()
            await bot.send_message(message.from_id, 
                f'Чек подошел! Заказ № {tattoo_order_number} обрел свой чек! '\
                'Хочешь сделать что-нибудь еще?', 
                reply_markup= kb_admin.kb_tattoo_order_commands)
        else:
            await message.reply( f'Чек не подошел! %s' % check_doc_pdf["report_msg"])
            
    if message.content_type == 'text':
        if message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_tattoo_order_commands)
            
        elif message.text in LIST_BACK_COMMANDS:
            await FSM_Admin_tattoo_order_change_status.previous()
            await message.reply(f'{MSG_CLIENT_GO_BACK}❔ На какую сумму чек?',
                reply_markup= kb_admin.kb_price)
        
    if message.content_type == 'photo':     
        message.photo[0].file_id
        check_photo = await check_photo_payment(
            message= message, 
            user_id= message.from_id,
            price= price,
            file_name= message.document.file_name, 
            file_id= message.photo[0].file_id
        ) 
        
        if check_photo["result"]:
            await update_info('tattoo_orders', 'tattoo_order_number',
                tattoo_order_number, 'check_document', message.document.file_id)
            await state.finish()
            await bot.send_message(message.from_id, 
                f'Чек подошел! Заказ № {tattoo_order_number} обрел свой чек! '\
                'Хочешь сделать что-нибудь еще?', 
                reply_markup= kb_admin.kb_tattoo_order_commands)
        else:
            await message.reply(check_photo["report_msg"]) # type: ignore


#------------------------------------CHANGE TATTOO ORDER-----------------------------------
class FSM_Admin_change_tattoo_order(StatesGroup):
    tattoo_order_number = State()
    tattoo_new_state = State()
    new_start_time_session = State()
    new_end_time_session = State()
    new_photo = State()

# /изменить_тату_заказ
async def command_command_change_info_tattoo_order(message: types.Message):
    if message.text in ['изменить тату заказ', '/изменить_тату_заказ'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        orders = Session(engine).scalars(select(TattooOrders))
        kb_tattoo_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
        if orders == []:
            await message.reply(f"{MSG_NO_ORDER_IN_TABLE}")
            
        else:
            for order in orders: # выводим номера тату заказов и их статус
                kb_tattoo_order_numbers.add(KeyboardButton(f'{order.tattoo_order_number}, \
                    статус: {order.order_state}')) 
            kb_tattoo_order_numbers.add(KeyboardButton('Хочу сначала посмотреть заказ')
                ).add(KeyboardButton('Назад'))
            await FSM_Admin_change_tattoo_order.tattoo_order_number.set()
            await message.reply("У какого заказа хочешь поменять какую-либо информацию?",
                reply_markup= kb_tattoo_order_numbers)


#-------------------------------------get_tattoo_order_number-----------------------------------
async def get_tattoo_order_number(message: types.Message, state: FSMContext):
    orders = Session(engine).scalars(select(TattooOrders))
    tattoo_str_list, tattoo_order_numbers = [], []
    kb_tattoo_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
    kb_tattoo_order_numbers_with_status = ReplyKeyboardMarkup(resize_keyboard=True)
    
    for order in orders:
        msg_item = f'{order.tattoo_order_number}, статус: {order.order_state}'
        tattoo_str_list.append(msg_item)
        tattoo_order_numbers.append(order.tattoo_order_number)
        kb_tattoo_order_numbers.add(KeyboardButton(order.tattoo_order_number))  # type: ignore
        kb_tattoo_order_numbers_with_status.add(KeyboardButton(msg_item))
        
    kb_tattoo_order_numbers.add('Отмена')
    kb_tattoo_order_numbers_with_status.add('Отмена')
    async with state.proxy() as data:
        data['menu_new_username'] = False
        data['menu_new_telegram'] = False
        data['menu_new_tattoo_name'] = False
        data['menu_new_order_note'] = False
        data['menu_new_tattoo_note'] = False
        data['orders'] = orders 
        
    if message.text in ['Хочу сначала посмотреть заказ', 
        kb_admin.admin_choice_watch_order_or_change_order['admin_want_to_watch_order'] ]:
        await bot.send_message(message.from_id, 'Какой заказ хочешь посмотреть?', 
            reply_markup= kb_tattoo_order_numbers)
        
    elif message.text == \
        kb_admin.admin_choice_watch_order_or_change_order['admin_want_to_change_order']:
        await message.reply(
            "У какого заказа хочешь поменять какую-либо информацию?",
            reply_markup= kb_tattoo_order_numbers_with_status
        )

    elif message.text in tattoo_order_numbers:
        order = Session(engine).scalars(select(TattooOrders).where(
            TattooOrders.tattoo_order_number == message.text))
        async with state.proxy() as data:
            data['order'] = order.one()
            
        await send_to_view_tattoo_order(message, order)
        
        await bot.send_message(message.from_id,
            'Хочешь посмотреть еще заказ или уже хочешь что-то в заказе изменить?',
            #  'Хочу еще посмотреть заказы','Хочу изменить информацию в заказе'
            reply_markup= kb_admin.kb_admin_choice_watch_order_or_change_order)
        
    elif message.text in tattoo_str_list:
        async with state.proxy() as data:
            data['order_number'] = message.text.split()[0]
            data['telegram'] = message.from_id
            
        await FSM_Admin_change_tattoo_order.next()
        await bot.send_message(message.from_id, 'Какую информацию хочешь поменять?',
            reply_markup= kb_admin.kb_tattoo_order_change_info_list)
        
    elif message.text in LIST_BACK_COMMANDS:
        await message.reply("У какого заказа хочешь поменять какую-либо информацию?",
            reply_markup= kb_tattoo_order_numbers)
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


#---------------------------------------get_new_state_info-----------------------------------
async def get_to_view_schedule(message: types.Message, state: FSMContext, schedule: list):
    kb_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
    if schedule == []:
        
        await bot.send_message(message.from_id, MSG_TO_NO_SCHEDULE)
        await bot.send_message(message.from_id, 'Хочешь изменить что-то еще?',
            reply_markup= kb_admin.kb_tattoo_order_change_info_list)
        await state.finish()
        
    else:
        kb_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
        today = int(datetime.datetime.strftime(datetime.datetime.now(), '%m %Y'))
        
        schedule_photo = Session(engine).scalars(select(SchedulePhoto).where(
            SchedulePhoto.name == today)).one()
        
        date_list_full_for_msg = ''
        for date in schedule:
            date_list_full_for_msg += date + '\n'
            kb_schedule.add(KeyboardButton(date))
                
        # .add(KeyboardButton('Хочу выбрать свою дату'))        
        kb_schedule.add(kb_client.back_btn).add(kb_client.cancel_btn)
        
        # выдаем на экран свободное фото расписания, или просто сообщение, если фото нет
        if schedule_photo == []:
            await bot.send_message( message.from_user.id,
                f'{MSG_MY_FREE_CALENDAR_DATES}'\
                f'{date_list_full_for_msg}')
        else:
            await bot.send_photo( message.from_user.id, schedule_photo.photo,
                f'{MSG_MY_FREE_CALENDAR_DATES}'\
                f'{date_list_full_for_msg}')
            
    kb_schedule.add(LIST_BACK_TO_HOME)
    await bot.send_message(message.from_id, 'Хорошо, укажи новую дату встречи', 
        reply_markup= kb_schedule)


async def get_new_state_info(message: types.Message, state: FSMContext):

    schedule = Session(engine).scalars(select(ScheduleCalendar).where(
        ScheduleCalendar.status.in_(["Свободен"])).where(
        ScheduleCalendar.event_type.in_(['тату заказ']))
    )
    kb_items_list = []
    for date in schedule:
        month_name = await get_month_from_number(date.date.strftime("%m"), lang= 'ru')
        item_in_kb = f'{month_name} {date.date} c {date.start_time} по {date.end_time} 🗓'
        kb_items_list.append(item_in_kb)

    async with state.proxy() as data:
        data['date_free_list'] = schedule
        order_number = data['order_number']
        order = data['order']
        
    if message.text in list(kb_admin.tattoo_order_change_info_list.keys()):
        # меняем фотографии тела/тату

        if message.text in list(kb_admin.tattoo_order_change_photo.keys()):
            async with state.proxy() as data:
                data['photo_type'] = message.text
            for i in range(3):
                await FSM_Admin_change_tattoo_order.next() # -> get_new_photo
            img_item = kb_admin.tattoo_order_change_info_list[message.text].split()[1:]
            await bot.send_message(message.from_id,
                f'Хорошо, отправь новую фотографию/изображение {img_item}')
            
        elif message.text == 'Цвет тату':
            await bot.send_message(message.from_id, 'Хорошо, какой цвет будет у тату?',
                reply_markup= kb_client.kb_colored_tattoo_choice)
            
        elif message.text == 'Дату встречи':
            await get_to_view_schedule(message, state, kb_items_list)
            
        elif message.text == 'Описание тату':
            async with state.proxy() as data:
                data['menu_new_tattoo_note'] = True
                
            await bot.send_message(message.from_id, 'Хорошо, укажи новое описание тату',
                reply_markup= kb_client.kb_cancel)
        
        elif message.text == 'Описание заказа':
            async with state.proxy() as data:
                data['menu_new_order_note'] = True
                
            await bot.send_message(message.from_id, 'Хорошо, укажи новое описание заказа',
                reply_markup= kb_client.kb_cancel)
            
        elif message.text == 'Время встречи':
            await FSM_Admin_change_tattoo_order.next() #-> process_hour_timepicker_start_session
            await bot.send_message(message.from_id, 'Хорошо, укажи новое время встречи', 
                reply_markup= await FullTimePicker().start_picker())
            
        elif message.text == 'Имя тату':
            async with state.proxy() as data:
                data['menu_new_tattoo_name'] = True
                
            await bot.send_message(message.from_id, 'Хорошо, укажи новое имя тату',
                reply_markup= kb_client.kb_cancel)
            
        elif message.text == 'Имя пользователя':
            async with state.proxy() as data:
                data['menu_new_username'] = True
                
            await bot.send_message(message.from_id, 'Хорошо, укажи новое имя пользователя',
                reply_markup= kb_client.kb_cancel)
            
        elif message.text == 'Телеграм пользователя':
            async with state.proxy() as data:
                data['menu_new_telegram'] = True
            await bot.send_message(message.from_id, 'Хорошо, укажи новое Телеграм пользователя',
                reply_markup= kb_client.kb_cancel)
            
        elif message.text == 'Место части тела для тату':
            await bot.send_message(message.from_id, 'Хорошо, укажи новую часть тела',
                reply_markup= kb_client.kb_place_for_tattoo)
            
        elif message.text == 'Цена':
            await bot.send_message(message.from_id, 'Хорошо, укажи новую цену',
                reply_markup= kb_admin.kb_price)
            
        elif message.text == 'Тип тату':#! А мы вообще меняем тут "тип тату"?
            await bot.send_message(message.from_id, 'Хорошо, укажи тип тату',
                reply_markup= kb_client.kb_client_choice_main_or_temporary_tattoo)
            
    elif message.text == 'Другая цена':
        await bot.send_message(message.from_id, 'Хорошо, укажи другую цену',
            reply_markup= kb_admin.kb_another_price)
        
    elif message.text in kb_admin.price + kb_admin.another_price: # меняем цену
        order.price = message.text
        Session(engine).commit()
        # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'price', message.text)
        
        await bot.send_message(message.from_id,
            f'Вы поменяли цену на {message.text} \n\n'\
            f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
    # меняем тип тату на постоянное    
    elif message.text == kb_client.choice_main_or_temporary_tattoo['main_tattoo']:
        order.tattoo_type = message.text
        Session(engine).commit()
        
        # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'tattoo_type', message.text)
        await bot.send_message(message.from_id,
            f'Вы поменяли тип тату на {message.text}! Нужно выставить дату и время встречи')
                
        await get_to_view_schedule(message, state, kb_items_list)
        
    # меняем тип тату на переводное   
    elif message.text == kb_client.choice_main_or_temporary_tattoo['temporary_tattoo']:
        await bot.send_message(message.from_id,
            'При изменении тату на переводное, '\
            'то занятый при этом календарный рабочий день становится свободным.')
        order.tattoo_type = message.text
        order.date_meeting = '-'
        order.date_time = '-'
        ''' 
        await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'tattoo_type', message.text)
        
        await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'date_meeting', '-')
        
        await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'date_time', '-') '''
        
        # TODO проверить правильность 
        schedule_to_change = Session(engine).scalars(select(ScheduleCalendar).where(
            ScheduleCalendar.schedule_id == order.schedule_id)).one()
        async with state.proxy() as data:
            data['schedule_to_change'] = schedule_to_change
            
        schedule_to_change.status = 'Свободен'
        Session(engine).commit()
        # await update_info('schedule_calendar', 'schedule_id', schedule_id, 'status', 'Свободен')
        
        await bot.send_message(message.from_id, 
            f'Вы поменяли у заказа {order.tattoo_order_number} тип тату на {message.text}!')
        
        await bot.send_message(message.from_id, f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_tattoo_order_commands)
        
    # меняем часть тела
    elif message.text in kb_client.tattoo_body_places:
        order.bodyplace = message.text
        Session(engine).commit()
        # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'bodyplace', message.text)
        
        await bot.send_message(message.from_id,
            f'Вы поменяли цену на {message.text} \n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
    # меняем цвет
    elif message.text in kb_client.colored_tattoo_choice:
        order.colored = message.text.split()[0].lower()
        Session(engine).commit()
        # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'colored', message.text.split()[0].lower())
        
        await bot.send_message(message.from_id,
            f'Вы поменяли цвет на {message.text} \n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
        
    elif message.text == kb_client.tattoo_body_places[-2]: # Другое место 🙅‍♂️
        async with state.proxy() as data:
            data['menu_new_another_bodyplace'] = True
            
        await bot.send_message(message.from_id, 'Хорошо, укажи местоположение тату на теле',
            reply_markup= kb_client.kb_cancel)
    # elif message.text == kb_client.tattoo_body_places[-1]:
        
    elif message.text in kb_items_list:
        async with state.proxy() as data:
            data['date_meeting'] = message.text.split()[1]
            data['start_date_time'] = message.text.split()[3]
            data['end_date_time'] = message.text.split()[5]
            
            for event in data['date_free_list']:
                if event[3] == message.text.split()[1] and event[1] == message.text.split()[3]:
                    data['schedule_id'] = event[0]
                    
            order.date_meeting = data['date_meeting']
            order.start_time = data['start_date_time']
            
            # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'date_meeting', data['date_meeting'])
            # await update_info('tattoo_orders', 'tattoo_order_number', order_number, date_time', data['start_date_time'])
            schedule_to_change = Session(engine).scalars(select(ScheduleCalendar).where(
                ScheduleCalendar.schedule_id == data['schedule_id'])).one()
            
            schedule_to_change.status = 'Занят'
            Session(engine).commit()
            # await update_info('schedule_calendar', 'schedule_id', data['schedule_id'], 'status', 'Занят')
        
        # await update_info('tattoo_orders', 'tattoo_order_number', order_number,
        # 'end_time', data['end_date_time'])
        await bot.send_message(message.from_id,
            f'Вы поменяли дату встречи на {message.text} \n\n'\
            f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_tattoo_order_commands)
        await state.finish()
        
    else:
        async with state.proxy() as data:
            menu_new_username = data['menu_new_username']
            menu_new_telegram = data['menu_new_telegram']
            menu_new_tattoo_name = data['menu_new_tattoo_name']
            menu_new_order_note = data['menu_new_order_note']
            menu_new_tattoo_note = data['menu_new_tattoo_note']
        if menu_new_username:
            order.username = message.text
            Session(engine).commit()
            # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'username', message.text)
            await bot.send_message(message.from_id,
                f'Вы поменяли имя пользователя на {message.text}')
            await bot.send_message(message.from_id, f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_admin.kb_tattoo_order_commands)
            await state.finish()
            
        elif menu_new_telegram:
            # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'telegram', message.text)
            order.telegram = message.text
            Session(engine).commit()
            await bot.send_message(message.from_id,
                f'Вы поменяли телеграм пользователя на {message.text} \n\n'\
                f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_admin.kb_tattoo_order_commands)
            await state.finish()
            
        elif menu_new_tattoo_name:
            # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'tattoo_name', message.text)
            order.tattoo_name = message.text
            Session(engine).commit()
            await bot.send_message(message.from_id,
                f'Вы поменяли имя тату на {message.text} \n\n'\
                f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_admin.kb_tattoo_order_commands)
            await state.finish()
            
        elif menu_new_order_note:
            # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'order_note', message.text)
            order.order_note = message.text
            Session(engine).commit()
            await bot.send_message(message.from_id,
                f'Вы поменяли описание заказа тату на {message.text} \n\n'\
                f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_admin.kb_tattoo_order_commands)
            await state.finish()
            
        elif menu_new_tattoo_note:
            # await update_info('tattoo_orders', 'tattoo_order_number', order_number, 'tattoo_note', message.text)
            order.tattoo_note = message.text
            Session(engine).commit()
            await bot.send_message(message.from_id,
                f'Вы поменяли описание тату на {message.text} \n\n'\
                f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_admin.kb_tattoo_order_commands)
            await state.finish()
        else:
            await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


@dp.callback_query_handler(full_timep_callback.filter(), 
    state=FSM_Admin_change_tattoo_order.new_start_time_session)
async def process_hour_timepicker_start_session(callback_query: CallbackQuery,
    callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data) # type: ignore
    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время для начала сеанса тату в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        async with state.proxy() as data:
            data['start_date_time'] = r.time.strftime("%H:%M")
            schedule_id = data['schedule_id']
            user_id = data['telegram']
            await update_info('schedule_calendar', 'schedule_id', schedule_id,
                'start_time', data['start_date_time'])
            
        await FSM_Admin_change_tattoo_order.next() #-> process_hour_timepicker_end_session
        await bot.send_message(user_id,
            f'📅 Прекрасно! Вы выбрали время начала сеанса {r.time.strftime("%H:%M")}.'
        )
        await bot.send_message(user_id, 'А теперь введи время конца сеанса',
            reply_markup= await FullTimePicker().start_picker())


@dp.callback_query_handler(full_timep_callback.filter(), 
    state=FSM_Admin_change_tattoo_order.new_end_time_session)
async def process_hour_timepicker_end_session(callback_query: CallbackQuery,
    callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data) # type: ignore
    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время для конца сеанса тату в {r.time.strftime("%H:%M")} ',
        )
        async with state.proxy() as data:
            data['end_date_time'] = r.time.strftime("%H:%M")
            schedule_id = data['schedule_id']
            user_id = data['telegram']
            await update_info('schedule_calendar', 'schedule_id', schedule_id,
                'end_time', data['end_date_time'])
            
        await bot.send_message(user_id,
            f'📅 Прекрасно! Вы выбрали время начала сеанса {r.time.strftime("%H:%M")}.'
        )
        await state.finish()
        await bot.send_message(user_id,
            f'Вы поменяли время начала и конца сеанса! {MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_tattoo_order_commands)


async def get_new_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        photo_type = data['photo_type']
        order_number = data['order_number']
        
    if photo_type == 'Фотография тату':
        await update_info('tattoo_orders', 'tattoo_order_number', order_number,
            'tattoo_photo', message.photo[0].file_id)
        
    elif photo_type == 'Фото части тела':
        await update_info('tattoo_orders', 'tattoo_order_number', order_number,
            'tattoo_place_file', message.photo[0].file_id)
        
    await bot.send_message(message.from_id,
        f'Вы поменяли {photo_type} \n\n'\
        f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
        reply_markup= kb_admin.kb_tattoo_order_commands)
    
    await state.finish()


#------------------------------------------CREATE TATTOO ORDER-----------------------------------
class FSM_Admin_tattoo_order(StatesGroup):
    get_tattoo_type = State()
    tattoo_choice = State()
    tattoo_name = State()
    tattoo_photo = State()
    tattoo_size = State()
    tattoo_color = State()
    
    schedule_for_tattoo_order_choice = State()
    new_tattoo_order_date_from_schedule =  State()
    
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
    if message.text in ['добавить тату заказ', '/добавить_тату_заказ'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        await FSM_Admin_tattoo_order.get_tattoo_type.set() # -> choice_tattoo_order_admin
        await bot.send_message(message.from_id, "Привет, админ. Сейчас будет создан тату заказ. "\
            "Тату заказ будет для переводного тату или для постоянного?",
            reply_markup = kb_client.kb_client_choice_main_or_temporary_tattoo)


async def get_tattoo_type(message: types.Message, state: FSMContext):
    if message.text in list(kb_client.choice_main_or_temporary_tattoo.values()):
        if message.text.split()[0].lower() == "переводное":
            async with state.proxy() as data:
                data['date_meeting'] = 'Без указания даты сеанса'
                data['start_date_time'] = 'Без указания начала сеанса'
                data['end_date_time'] = 'Без указания конца сеанса'
            
        async with state.proxy() as data:
            # tattoo_type = постоянное, переводное
            data['tattoo_type'] = message.text.split()[0].lower()
            
            data['tattoo_photo'] = ''
            data['tattoo_order_photo_counter'] = 0
            data['tattoo_place_file'] = ''
            data['client_add_tattoo_place_photo'] = True
            
        await FSM_Admin_tattoo_order.next() # -> choice_tattoo_order_admin
        await bot.send_message(message.from_id, 
            'Хорошо, теперь определи, это тату из твоей галереи или нет?',
            reply_markup= kb_client.kb_yes_no)
        
    elif message.text in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands)
    
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST) 


# Отправляем название тату 
async def choice_tattoo_order_admin(message: types.Message, state: FSMContext):
    list_kb_tattoo_items = []
    if message.text == kb_client.yes_str:
        admin_tattoo_items = await get_info_many_from_table('tattoo_items')
        kb_tattoo_items_for_order = ReplyKeyboardMarkup(resize_keyboard=True)
        await bot.send_message(message.from_id, 'Вот твоя галлерея:')
        
        for tattoo in admin_tattoo_items:
            kb_tattoo_items_for_order.add(KeyboardButton(f'{tattoo[0]}'))
            list_kb_tattoo_items.append(f'{tattoo[0]}')
            tattoo = list(tattoo) #? TODO нужно ли выводить размер и цену?
            msg = f'📃 Название: {tattoo[0]}\n🎨 Цвет: {tattoo[3]}\n'
                #\f'🔧 Количество деталей: {tattoo[5]}\n'
                
            if tattoo[4].lower() != 'без описания':
                msg += f'💬 Описание: {tattoo[4]}\n'#💰 Цена: {tattoo[2]}\n'
            
            await bot.send_photo(message.from_user.id, tattoo[1] , msg)
            
        # выдаем список тату - фотографии, название, цвет, описание    
        await bot.send_message(message.from_id, '❔ Какое тату хочешь выбрать?',
            reply_markup = kb_tattoo_items_for_order) 
        
    elif message.text in list_kb_tattoo_items:
        tattoo = await get_info_many_from_table('tattoo_items', 'name', message.text)
        async with state.proxy() as data:
            data['telegram'] = message.from_user.id 
            data['tattoo_name'] = message.text
            data['price'] = list(tattoo[0])[2] # price
            data['tattoo_photo'] = list(tattoo[0])[1] # photo
            data['colored'] = list(tattoo[0])[3] # colored
            data['tattoo_note'] = list(tattoo[0])[4] # colored
            data['tattoo_from_galery'] = True
        for i in range(3):
            await FSM_Admin_tattoo_order.next() # -> tattoo_size
            
        await bot.send_message(message.from_id, 
            'Введи размер тату (в см). Размер не может быть больше 150 см2 и меньше 0',
            reply_markup= kb_client.kb_client_size_tattoo)
        
    elif message.text == kb_client.no_str:
        await FSM_Admin_tattoo_order.next() # -> load_tattoo_order_name
        async with state.proxy() as data:
            data['tattoo_from_galery'] = False
            
        await bot.send_message(message.from_id,
            "Хорошо. Давай определимся с названием тату. Какое будет название?", 
            reply_markup= kb_client.kb_cancel)
        
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands)
    
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)       


async def load_tattoo_order_name(message: types.Message, state: FSMContext):
    if message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands)
        
    elif message.text == kb_client.yes_str:
        await FSM_Admin_tattoo_order.next() # -> load_tattoo_order_photo
        await message.reply(MSG_CLIENT_LOAD_PHOTO, reply_markup= kb_client.kb_cancel) 
        
    elif message.text == kb_client.no_str:
        for i in range(2):
            await FSM_Admin_tattoo_order.next() # -> load_tattoo_order_size
        await bot.send_message(message.from_id, "Хорошо, оставим пока данный заказ без эскиза")
        
        await bot.send_message(message.from_id, MSG_CLIENT_CHOICE_TATTOO_SIZE, 
            reply_markup= kb_client.kb_client_size_tattoo) 
        
    else:
        async with state.proxy() as data:
            # ставим сюда id телеги, чтобы бот мог ответить пользователю при выборе даты
            data['telegram'] = message.from_user.id 
            data['tattoo_name'] = message.text
        
        await bot.send_message(message.from_id, f"Название тату будет {message.text}")
        await bot.send_message(message.from_id, f"Хочешь добавить фотографию эскиза тату?", 
            reply_markup= kb_client.kb_yes_no)
    
        

# Отправляем фото 
async def load_tattoo_order_photo(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        if message.text in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
            await state.finish()
            await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_tattoo_order_commands)
        
        elif message.text in [kb_client.no_photo_in_tattoo_order['load_tattoo_photo'], 
            kb_client.client_choice_add_another_photo_to_tattoo_order['client_want_to_add_sketch_to_tattoo_order']]:
            
            async with state.proxy() as data:
                data['tattoo_order_photo_counter'] = 0
                
            await bot.send_message(message.from_id, MSG_CLIENT_LOAD_PHOTO,
                reply_markup= kb_client.kb_back_cancel)
            
        #'Закончить с добавлением изображений ➡️'
        elif message.text == \
            kb_client.client_choice_add_another_photo_to_tattoo_order[
                'client_dont_want_to_add_sketch_to_tattoo_order']:
            await FSM_Admin_tattoo_order.next() # -> load_tattoo_order_size
            await bot.send_message( message.from_id, "❕ Хорошо, с фотографиями для эскиза мы пока закончили.")
            await bot.send_message( message.from_id, f'{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
                reply_markup= kb_client.kb_client_size_tattoo)
        else:
            await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
        
    elif message.content_type == 'photo':
        async with state.proxy() as data:
            data['tattoo_from_galery'] = False
            data['tattoo_photo'] += f'{message.photo[0].file_id}|'
            tattoo_order_photo_counter = data['tattoo_order_photo_counter']
            data['tattoo_order_photo_counter'] = message.media_group_id
            
        if tattoo_order_photo_counter != data['tattoo_order_photo_counter']:
            async with state.proxy() as data:
                tattoo_order_photo_counter = data['tattoo_order_photo_counter']
            
            await bot.send_message(message.from_id,  
                '📷 Отлично, ты выбрал(а) фотографию эскиза для своего тату!')
            await bot.send_message( message.from_id, '❔ Хочешь добавить еще фото/картинку?',
                reply_markup= kb_client.kb_client_choice_add_another_photo_to_tattoo_order)


# Отправляем размер тату 
async def load_tattoo_order_size(message: types.Message, state: FSMContext):
    if message.text in list(kb_client.size_dict.values()):
        async with state.proxy() as data:
            data['tattoo_size'] = message.text
            data['tattoo_place_file_counter'] = 0 
            data['tattoo_place_video_note'] = ''
            data['tattoo_place_video'] = ''
            tattoo_from_galery = data['tattoo_from_galery']
            tattoo_type = data['tattoo_type']
            
        if tattoo_from_galery and tattoo_type.lower() == 'постоянное':
            for i in range(2):
                await FSM_Admin_tattoo_order.next() # -> load_tattoo_order_schedule_choice
            
            # ['Хочу выбрать дату из календаря', 'Хочу новую дату в календарь']
            await message.reply('Хорошо, а теперь напиши дату или даты тату заказа.'\
                ' Хочешь выбрать дату заказа из календаря, или добавить новую дату в календарь и заказ?',
                reply_markup = kb_admin.kb_schedule_for_tattoo_order_choice) # await DialogCalendar().start_calendar()
            
        else:
            await FSM_Admin_tattoo_order.next() # -> get_tattoo_color
            await bot.send_message(message.from_id, MSG_WHICH_COLOR_WILL_BE_TATTOO, 
                reply_markup= kb_client.kb_colored_tattoo_choice)
            
    elif message.text in  LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_tattoo_color( message: types.Message, state: FSMContext):
    if any(text in message.text for text in kb_client.colored_tattoo_choice):
        async with state.proxy() as data:
            data['tattoo_colored'] = message.text.split()[0]
            tattoo_type = data['tattoo_type']
            
        await bot.send_message(message.from_id,  
            f'🍃 Хорошо, тату будет {message.text.split()[0].lower()}')
        
        if tattoo_type.lower() == 'постоянное':
            await FSM_Admin_tattoo_order.next() # -> load_tattoo_order_schedule_choice
            
            # ['Хочу выбрать дату из календаря', 'Хочу новую дату в календарь']
            await message.reply('Хорошо, а теперь напиши дату или даты тату заказа.'\
                ' Хочешь выбрать дату заказа из календаря, или добавить новую дату в календарь и заказ?',
                reply_markup = kb_admin.kb_schedule_for_tattoo_order_choice)
        else:
            for i in range(6):
                await FSM_Admin_tattoo_order.next() # -> load_tattoo_order_note
            
            await bot.send_message(message.from_id, 
                'А теперь введи что-нибудь об этом тату. Так ты добавишь параметр \"описание тату\"',
                reply_markup= kb_client.kb_cancel)
        
    elif message.text in  LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def load_tattoo_order_schedule_choice(message: types.Message, state: FSMContext):
    if message.text == 'Хочу выбрать дату из календаря':
        with Session(engine) as session:
            schedule = session.scalars(select(ScheduleCalendar).where(
                ScheduleCalendar.status == 'Свободен').where(
                ScheduleCalendar.event_type == 'тату заказ').order_by(ScheduleCalendar.start_datetime))
                
        if schedule == []:
            await message.reply(
                f'У тебя пока нет расписания. Тогда создадим новую дату. Выбери пожалуйста, дату',
                reply_markup = await DialogCalendar().start_calendar())
            
            for i in range(2):
                await FSM_Admin_tattoo_order.next() # -> load_datemiting
        else:
            async with state.proxy() as data:
                data['date_free_list'] = schedule
            kb_date_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
            date_list = ''
            for date in schedule:
                if '/' in date[3]:
                    date_time = datetime.strptime(f"{date[3]} 00:00:00", "%d/%m/%Y %H:%M")
                    
                    if date_time >= datetime.datetime.now():
                        date_list += f'{date[4]} {date[3]} c {date[1]} по {date[2]}\n'
                        kb_date_schedule.add(KeyboardButton(f'{date[4]} {date[3]} c {date[1]} по {date[2]}'))
                else:
                    dates = await get_dates_from_month_and_day_of_week(month=date[4], day=date[3]) 
                    if dates != []:
                        date_list += f'{date[4]} {date[3]} c {date[1]} по {date[2]}\n'
                        kb_date_schedule.add(
                            KeyboardButton(f'{date[4]} {date[3]} c {date[1]} по {date[2]}'))        
            kb_date_schedule.add(KeyboardButton('Отмена'))
            month_today = int(datetime.datetime.strftime(datetime.datetime.now(), '%m'))
            year_today = int(datetime.datetime.strftime(datetime.datetime.now(), '%Y'))
            schedule_photo = \
                await get_info_many_from_table(
                    'schedule_photo', 'name', f'{month_today} {year_today}')
            await FSM_Admin_tattoo_order.next() # -> load_new_tattoo_order_date_from_schedule
            
            if schedule_photo != []:
                await bot.send_photo(
                    message.from_user.id, list(schedule_photo[0])[1],
                    f'Вот твои свободные даты в этом месяце:\n{date_list}'\
                    'Какую дату и время выбираешь?',
                    reply_markup= kb_date_schedule)
                
            else:
                await bot.send_message(message.from_user.id,
                    f'Вот твои свободные даты в этом месяце:\n{date_list}'\
                    'Какую дату и время выбираешь?',
                    reply_markup= kb_date_schedule)
                
    elif message.text == 'Хочу новую дату в календарь':
        await FSM_Admin_tattoo_order.next()
        await FSM_Admin_tattoo_order.next() # -> load_datemiting
        await message.reply(f'Тогда создадим новую дату. Выбери пожалуйста, дату',
            reply_markup = await DialogCalendar().start_calendar())
    else:
        await message.reply(f'Пожалуйста, выбери ответ из предложенных вариантов')


async def load_new_tattoo_order_date_from_schedule(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date_meeting'] = message.text.split()[1]          
        data['start_date_time'] = message.text.split()[3]
        data['end_date_time'] = message.text.split()[5]
        data['schedule_id'] = 0
        
        for event in data['date_free_list']:
            if event[3] == message.text.split()[1] and event[1] == message.text.split()[3]:
                data['schedule_id'] = event[0]
                
        for i in range(4):
            await FSM_Admin_tattoo_order.next()
        await message.reply( 
            f'Прекрасно! Вы выбрали дату {message.text.split()[1]} и время {message.text.split()[3]}.\n'\
            'А теперь введи что-нибудь о своем тату')


# выбираем новую дату заказа
@dp.callback_query_handler(dialog_cal_callback.filter(), state=FSM_Admin_tattoo_order.date_meeting)
async def load_datemiting(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data) # type: ignore
    if selected:
        await callback_query.message.answer(f'Вы выбрали {date.strftime("%d/%m/%Y")}')
        username_id = 0
        async with state.proxy() as data:
            username_id = data['telegram']
            
        if date <= datetime.now():
            await bot.send_message(username_id, "Эта дата уже прошла. Выбери другую дату.",
                reply_markup = await DialogCalendar().start_calendar())
            
        else:
            async with state.proxy() as data:
                data['date_meeting'] =  f'{date.strftime("%d/%m/%Y")}' #  message.text
                data['month_number'] = int(f'{date.strftime("%m")}')
                data['month_name'] = await get_month_from_number(data['month_number'], 'ru')
                
            await FSM_Admin_tattoo_order.next()
            await bot.send_message(username_id,
                'А теперь введи удобное для тебя время.',
                reply_markup=await FullTimePicker().start_picker())


# выбираем начало времени заказа
@dp.callback_query_handler(full_timep_callback.filter(), state=FSM_Admin_tattoo_order.start_date_time)
async def process_hour_timepicker_start(callback_query: CallbackQuery, callback_data: dict, state: FSMContext): 
    r = await FullTimePicker().process_selection(callback_query, callback_data) # type: ignore
    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время начала тату заказа в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            data['start_date_time'] = r.time.strftime("%H:%M")
            username_id = data['telegram']
        
        
        await FSM_Admin_tattoo_order.next()
        await bot.send_message(username_id, 'А теперь введи время окончания тату заказа',
            reply_markup=await FullTimePicker().start_picker())


# выбираем конец времени заказа
@dp.callback_query_handler(full_timep_callback.filter(), state=FSM_Admin_tattoo_order.end_date_time)
async def process_hour_timepicker_end(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data) # type: ignore
    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время конца заказа тату в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        username_id = 0
        async with state.proxy() as data:
            data['end_date_time'] = r.time.strftime("%H:%M")
            username_id = data['telegram']
            schedule_id = await generate_random_order_number(CODE_LENTH)
            data['schedule_id'] = schedule_id
            
            new_schedule_event = {
                "schedule_id" :     schedule_id,
                "start_time" :      data['start_date_time'],
                "end_time"  :       data['end_date_time'], 
                "date"  :           data['date_meeting'],
                "month_name"  :     data['month_name'],
                "month_number"  :   data['month_number'],
                "status"  :         'Занят',
                "event_type":       'тату заказ'
            }
            
        await set_to_table( tuple(new_schedule_event.values()), 'schedule_calendar')

        await FSM_Admin_tattoo_order.next() # -> load_tattoo_order_note
        await bot.send_message(username_id, 
            'А теперь введи что-нибудь об этом тату. Так ты добавишь параметр \"описание тату\"',
            reply_markup= kb_client.kb_cancel)  


# Отправляем описание тату 
async def load_tattoo_order_note(message: types.Message, state: FSMContext):
    if message.text in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands)
    else:
        async with state.proxy() as data:
            data['tattoo_note'] = message.text
        await FSM_Admin_tattoo_order.next()
        await bot.send_message(message.from_id, "Хочешь добавить места, где будет расположено тату?",
            reply_markup= kb_client.kb_yes_no)
    
async def get_body_name( message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        await bot.send_message(message.from_id, "Какое место будет у тату?",
            reply_markup= kb_client.kb_place_for_tattoo)
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            data['tattoo_body_place'] = "Без места для тату"
            data['tattoo_place_file'] = ""
            
        for i in range(2):
            await FSM_Admin_tattoo_order.next() # -> choiсe_tattoo_order_desctiption
        await message.reply(
            'Хочешь чего-нибудь добавить к описанию этого заказа?\nОтветь \"Да\" или \"Нет\"',
            reply_markup= kb_client.kb_yes_no)
        
    elif message.text in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_tattoo_order_commands)
        
    elif message.text in kb_client.tattoo_body_places:
        async with state.proxy() as data:
            data['tattoo_body_place'] = message.text
            
        await FSM_Admin_tattoo_order.next()
        await bot.send_message(message.from_id, "Хочешь добавить фото местоположения?",
            reply_markup= kb_client.kb_yes_no) 


async def get_body_photo(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        if message.text == kb_client.yes_str:
            async with state.proxy() as data:
                data['tattoo_place_file_counter'] = 0 
            
            await bot.send_message(message.from_id, "Отправь фото места для тату", 
                reply_markup= kb_client.kb_cancel)
            
        elif message.text == kb_client.no_str:
            async with state.proxy() as data:
                data['tattoo_place_file'] = ""
                data['tattoo_place_video_note'] = ""
                data['tattoo_place_video'] = ""
                
            await FSM_Admin_tattoo_order.next() #-> choiсe_tattoo_order_desctiption
            await message.reply(
                'Хочешь чего-нибудь добавить к описанию этого заказа?\nОтветь \"Да\" или \"Нет\"',
                reply_markup= kb_client.kb_yes_no)
            
        elif message.text in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(MSG_BACK_TO_HOME, reply_markup= kb_admin.kb_tattoo_order_commands)
            
        elif message.text == \
            kb_client.client_choice_add_another_photo_to_tattoo_order["client_want_to_add_sketch_to_tattoo_order"]:
                await bot.send_message(message.from_id, "Отправь еще фото места для тату", 
                    reply_markup= kb_client.kb_cancel)
                
        elif message.text ==\
            kb_client.client_choice_add_another_photo_to_tattoo_order["client_dont_want_to_add_sketch_to_tattoo_order"]:
                await FSM_Admin_tattoo_order.next() #-> choiсe_tattoo_order_desctiption
                await message.reply(
                    'Хочешь чего-нибудь добавить к описанию этого заказа?\nОтветь \"Да\" или \"Нет\"',
                    reply_markup= kb_client.kb_yes_no)
        
        else:
            await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
            
    elif message.content_type == 'photo':
        async with state.proxy() as data:
            data['tattoo_place_file'] += f'{message.photo[0].file_id}|'
            data['client_add_tattoo_place_photo'] = True
            
            tattoo_place_file_counter = data['tattoo_place_file_counter']
            data['tattoo_place_file_counter'] = message.media_group_id
            
        if tattoo_place_file_counter != data['tattoo_place_file_counter']:
            async with state.proxy() as data:
                tattoo_place_file_counter = data['tattoo_place_file_counter']
            
            await bot.send_message(message.from_id, 
                '📷 Отлично, ты добавил(а) фотографию места для своего тату!')
            
            await bot.send_message(message.from_id, 
                MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY, 
                reply_markup= kb_client.kb_client_choice_add_another_photo_to_tattoo_order)
            # client_choice_add_another_photo_to_tattoo_order = {
            #'client_want_to_add_sketch_to_tattoo_order' : 'Добавить еще одно изображение ☘️',
            #'client_dont_want_to_add_sketch_to_tattoo_order' : 'Закончить с добавлением изображений ➡️'}
    
    elif message.content_type == 'video_note':
        async with state.proxy() as data:
            data['tattoo_place_video_note'] += f'{message.video_note.file_id}|'
        
        await bot.send_message(message.from_id, 
            '📷 Отлично, ты добавил(а) видеосообщение места для своего тату!')
        await bot.send_message(message.from_id, 
            MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY, 
            reply_markup= kb_client.kb_yes_no)
        
    elif message.content_type == 'video':
        async with state.proxy() as data:
            data['tattoo_place_video'] += f'{message.video.file_id}|'
            tattoo_place_file_counter = data['tattoo_place_file_counter']
            data['tattoo_place_file_counter'] = message.media_group_id
            
        if tattoo_place_file_counter != data['tattoo_place_file_counter']:
            async with state.proxy() as data:
                tattoo_place_file_counter = data['tattoo_place_file_counter']
                
            await bot.send_message(message.from_id, 
                '📷 Отлично, ты добавил(а) видео места для своего тату!')
            
            await bot.send_message(message.from_id, 
                MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY, 
                reply_markup= kb_client.kb_yes_no)


async def choiсe_tattoo_order_desctiption(message: types.Message, state: FSMContext):
    await FSM_Admin_tattoo_order.next()
    if message.text == kb_client.yes_str:
        await message.reply('Хорошо! Опиши детали тату')
        
    elif message.text == kb_client.no_str:
        await FSM_Admin_tattoo_order.next()
        async with state.proxy() as data:
            data['order_note'] = 'Без описания заказа'
        await message.reply(
            'Хорошо, тогда будем думать над деталями тату потом. Напиши примерную цену тату заказа. '\
            'Выбери из представленного списка',
            reply_markup= kb_admin.kb_price)
    else:
        await bot.send_message(message.from_id,
            'На данный вопрос можно ответить только \"Да\" или \"Нет\". Введи ответ корректно.')


# Отправляем описание заказа тату 
async def load_order_desctiption_after_choice(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['order_note'] = message.text
    await FSM_Admin_tattoo_order.next()  # -> get_price_tattoo_order_after_choice 
    await message.reply(f'Напиши примерную цену тату заказа. Выбери из представленного списка',
        reply_markup=kb_admin.kb_price) # В любом случае, заказ почти оформлен. 


async def get_price_tattoo_order_after_choice(message: types.Message, state: FSMContext):
    # Заполняем таблицу tattoo_items
    async with state.proxy() as data:

        tattoo_from_galery = data['tattoo_from_galery']
        data['tattoo_price'] = message.text
        data['tattoo_details_number'] = 0
        data['order_state'] = OPEN_STATE_DICT["open"] # выставляем статус заказа как открытый  
        data['tattoo_order_number'] = await generate_random_order_number(ORDER_CODE_LENTH)   
        data['creation_date'] = datetime.strftime(datetime.now(), '%d/%m/%Y %H:%M')
        if not tattoo_from_galery:
            new_tattoo_info = {
                "tattoo_name":  data['tattoo_name'],
                "tattoo_photo": data['tattoo_photo'],
                "tattoo_price": data['tattoo_price'],
                "tattoo_size":  data['tattoo_size'],
                "tattoo_note":  data['tattoo_note'],
                "creator":      "admin"
            }
            await set_to_table(tuple(new_tattoo_info.values()), 'tattoo_items')
            await bot.send_message(message.from_user.id, 
                f' Отлично! В таблице tattoo_items появилась новая строка. '\
                f'Таблица tattoo_items содержит информацию о всех тату, которые были в заказах, '\
                f'и в которые ты создала сама. \n')
            
    await FSM_Admin_tattoo_order.next() # -> get_tattoo_order_state 
    await bot.send_message(message.from_user.id, 
        'Клиент оплатил заказ? Ответь \"Да\" или \"Нет\"',
        reply_markup= kb_client.kb_yes_no)


async def get_tattoo_order_state(message: types.Message, state: FSMContext):
    tattoo_order_number = 0  
    await FSM_Admin_tattoo_order.next()
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            data['order_state'] = PAID_STATE_DICT["paid"]
            
        await bot.send_message(message.from_user.id, 
            f' Хочешь приложить чек к заказу? Ответь \"Да\" или \"Нет\"', 
            reply_markup= kb_client.kb_yes_no)
        
    # await db_filling_from_command('tattoo_items.json', new_tattoo_info)
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            data['order_state'] = OPEN_STATE_DICT["open"]
            data['check_document'] = 'Чек не добавлен'
            tattoo_order_number = data['tattoo_order_number']
        await FSM_Admin_tattoo_order.next()
        await FSM_Admin_tattoo_order.next()
        await bot.send_message(message.from_user.id, f'Заказ № {tattoo_order_number} почти оформлен! '\
            'Осталось ввести имя, телеграм и телефон пользователя, и все будет готово!\n'\
            'Введи, пожалуйста, имя пользователя', reply_markup= kb_client.kb_cancel)
    else:
        await bot.send_message(message.from_id,
            'На данный вопрос можно ответить только \"Да\" или \"Нет\". Введи ответ корректно.')


async def get_tattoo_order_check(message: types.Message, state: FSMContext):
    tattoo_order_number = 0  
    if message.text == kb_client.yes_str:
        await FSM_Admin_tattoo_order.next()
        await bot.send_message(message.from_user.id,'Приложи чек, пожалуйста. Для этого надо в файлах отправить документ с чеком.')

    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            tattoo_order_number = data['tattoo_order_number']
            data['check_document'] = 'Чек не добавлен'
        await FSM_Admin_tattoo_order.next()
        await FSM_Admin_tattoo_order.next()
        await bot.send_message(message.from_user.id, f'Заказ № {tattoo_order_number} почти оформлен! '\
            'Осталось ввести Имя, Телеграм и Телефон пользователя, и все будет готово!\n'\
            'Введи Имя пользователя')
        
    else:
        await bot.send_message(message.from_user.id,
            'На данный вопрос можно ответить только \"Да\" или \"Нет\". Введи ответ корректно.')


async def get_tattoo_order_check_next(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        tattoo_order_number = data['tattoo_order_number']
        price = data['tattoo_price']
        data['check_document'] = message.document.file_id
        check_doc_pdf = await check_photo_payment(
            message, message.from_id, price, message.document.file_name, data['check_document']) 
        
    if check_doc_pdf["result"]:
        await FSM_Admin_tattoo_order.next()
        await bot.send_message(message.from_user.id, f'Чек подошел! Заказ № {tattoo_order_number} почти оформлен! '\
        'Осталось ввести имя, телеграм и телефон пользователя, и все будет готово!\n'\
        'Введи, пожалуйста, имя пользователя')
        
    else:
        await message.reply(check_doc_pdf["report_msg"]) # type: ignore


# выбираем имя покупателя
async def tattoo_order_load_user_name(message: types.Message, state: FSMContext):
    # Заполняем таблицу clients
    tattoo_order_number = 0
    async with state.proxy() as data:
        data['username'] = message.text
        tattoo_order_number = data['tattoo_order_number']
        tattoo_order_tuple_data = {
            "telegram":             data['telegram'],
            "tattoo_name":          data['tattoo_name'],
            "tattoo_photo":         data['tattoo_photo'], 
            "tattoo_size":          data['tattoo_size'] ,
            "date_meeting":         data['date_meeting'] ,
            "date_time":            data['start_date_time'] , 
            "tattoo_note":          data['tattoo_note'] , 
            "order_note":           data['order_note'] , 
            "order_state":          data['order_state'] , 
            "tattoo_order_number":  data['tattoo_order_number'] , 
            "creation_date":        data['creation_date'] , 
            "tattoo_price":         data['tattoo_price'] , 
            "check_document":       data['check_document'] , 
            "username":             data['username'],
            "schedule_id" :         data['schedule_id'],
            "tattoo_colored":           data['tattoo_colored'],
            "tattoo_details_number":    data['tattoo_details_number'],
            "tattoo_body_place":        data['tattoo_body_place'],
            "tattoo_place_file":        data['tattoo_place_file'],
            "tattoo_type":              data['tattoo_type'],
            "tattoo_place_video_note":  data['tattoo_place_video_note'],
            "tattoo_place_video":       data['tattoo_place_video']
        }
    
        metting_calendar_event ={
            "date_meeting": data['start_date_time'] + ' ' +  data['date_meeting'],
            "order_number": data['tattoo_order_number'] 
        }
        
        
        await update_info('schedule_calendar', 'id', data['schedule_id'], 'status', 'Занят')
        
        time_meeting = data['start_date_time'] 
        date_meeting = data['date_meeting'].split('/')
        start_time =  f'{date_meeting[2]}-{date_meeting[1]}-{date_meeting[0]}T{time_meeting}'
        end_time_meeting = data['end_date_time']
        

        end_time = f'{date_meeting[2]}-{date_meeting[1]}-{date_meeting[0]}T{end_time_meeting}'
            
        event = await obj.add_event(CALENDAR_ID,
            f'Новый тату заказ № {tattoo_order_number}',
                'Название тату: ' +    data['tattoo_name'] + ', \n' + \
                'Описание тату: ' +    data['tattoo_note'] + ', \n' + \
                'Описание заказа: ' +  data['order_note'] + ', \n' + \
                'Имя клиента: ' +      message.text,
            start_time, # '2023-02-02T09:07:00',
            end_time    # '2023-02-03T17:07:00'
        )
        
    print("tattoo_order_tuple_data.values():", tuple(tattoo_order_tuple_data.values()))
    await set_to_table(tuple(tattoo_order_tuple_data.values()), 'tattoo_orders')

    user_name = ''
    user = []
    try:
        user = await get_info_many_from_table('clients', 'username', message.text)
        user_name = list(user[0])[0]
    except:
        print("У вас еще не было заказов и пользователей")
        
    await state.finish()
    await FSM_Admin_username_info.user_name.set()
    
    async with state.proxy() as data:
        data['username'] = message.text
        data['order_number'] = tattoo_order_number
        
    if user != [] and user is not None:
        if message.text != user_name:
            await FSM_Admin_username_info.next()
            await FSM_Admin_username_info.next()
            await message.reply('Хорошо, а теперь введи его телеграм') 
        else:
            await FSM_Admin_username_info.next()
            await message.reply(f'Это пользователь под именем {user_name}?',
                reply_markup= kb_client.kb_yes_no)
    else:
        await FSM_Admin_username_info.next()
        await FSM_Admin_username_info.next()
        await message.reply('Хорошо, а теперь введи ссылку на его телеграм')


#TODO: ЗАКОНЧИТЬ ЗАПОЛНЕНИЕ НОВОГО ПОЛЬЗОВАТЕЛЯ ДЛЯ ТАТУ ЗАКАЗА, ДЛЯ АДМИНА
async def answer_user_name(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            username, telegram, phone = data['username'], data['telegram'], data['phone']
            order_number = data['order_number']
            await bot.send_message(
                message.from_user.id,
                f'Хорошо, твой заказ под номером {order_number}'\
                f' оформлен на пользователя {username} с телеграмом {telegram}, телефон {phone}!',
                reply_markup=kb_admin.kb_main)
        await state.finish()
    elif message.text == kb_client.no_str:
        await FSM_Admin_username_info.next()
        await message.reply('Хорошо, это другой пользователь, введи ссылку на его телеграм') 
    else:
        await FSM_Admin_username_info.next()


async def load_telegram(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['telegram'] = message.text
    await FSM_Admin_username_info.next()
    await message.reply(
        'Хорошо, а теперь введи его телефон, или нажми на кнопку \"Я не знаю его телефона\"',
        reply_markup=kb_admin.kb_admin_has_no_phone_username)


async def load_phone(message: types.Message, state: FSMContext):
    if message.text in kb_admin.phone_answer:
        number = 'Нет номера'
    else:
        number = message.text
        result = re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?'\
            '[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', number)
        
        if not result:
            await message.reply('Номер не корректен. Пожалуйста, введи номер заново.')
        
    async with state.proxy() as data:
        new_client_info = {
            "username": data['username'],
            "telegram": data['telegram'],
            "phone": number
        }
        await set_to_table(tuple(new_client_info.values()), 'clients')
        username, telegram, phone = data['username'], data['telegram'], number
        tattoo_order_number = data['order_number']
        print('Таблица clients пополнилась новыми данными')
        await bot.send_message(
            message.from_user.id, f'Хорошо, твой заказ под номером {tattoo_order_number}'\
            f' оформлен на пользователя {username} с телеграмом {telegram}, телефон: {phone}!',
            reply_markup= kb_admin.kb_main)
        await state.finish() #  полностью очищает данные


def register_handlers_admin_tattoo_order(dp: Dispatcher):
    #-------------------------------------------------------TATTOO ORDER--------------------------------------------
    dp.register_message_handler(get_tattoo_order_and_item_command_list, commands=['тату_заказы'])
    dp.register_message_handler(get_tattoo_order_and_item_command_list, 
        Text(equals='Тату заказы', ignore_case=True), state=None)

    dp.register_message_handler(command_get_info_tattoo_orders, commands=['посмотреть_тату_заказы'])
    dp.register_message_handler(command_get_info_tattoo_orders,
        Text(equals='посмотреть тату заказы', ignore_case=True), state=None)
    dp.register_message_handler(get_status_name, state=FSM_Admin_get_info_orders.order_status_name)

    dp.register_message_handler(command_get_info_tattoo_order, commands=['посмотреть_тату_заказ'])
    dp.register_message_handler(command_get_info_tattoo_order,
        Text(equals='посмотреть тату заказ', ignore_case=True), state=None)
    
    dp.register_message_handler(get_name_for_view_tattoo_order,
        state=FSM_Admin_command_get_info_tattoo_order.order_name)

    dp.register_message_handler(command_delete_info_tattoo_orders,
        commands=['удалить_тату_заказ', 'удалить'])
    dp.register_message_handler(command_delete_info_tattoo_orders, 
        Text(equals='удалить тату заказ', ignore_case=True), state=None)
    dp.register_message_handler(delete_info_tattoo_orders,
        state=FSM_Admin_delete_tattoo_order.tattoo_order_number)
    
    dp.register_message_handler(command_tattoo_order_change_status, commands=['изменить_статус_тату_заказа'])
    dp.register_message_handler(command_tattoo_order_change_status,
        Text(equals='изменить статус тату заказа', ignore_case=True), state=None)
    dp.register_message_handler(get_new_status_for_tattoo_order,
        state=FSM_Admin_tattoo_order_change_status.tattoo_order_number)
    dp.register_message_handler(complete_new_status_for_tattoo_order,
        state=FSM_Admin_tattoo_order_change_status.tattoo_order_new_status)

    dp.register_message_handler(get_answer_for_getting_check_document,
        state=FSM_Admin_tattoo_order_change_status.get_answer_for_getting_check_document)
    dp.register_message_handler(get_price_for_check_document,
        state=FSM_Admin_tattoo_order_change_status.get_price_for_check_document)

    dp.register_message_handler(get_check_document, content_types=['photo', 'document'],
        state=FSM_Admin_tattoo_order_change_status.get_check_document)
    
    #---------------------------------------------CHANGE TATTOO ORDER-------------------------------------
    dp.register_message_handler(command_command_change_info_tattoo_order,
        commands=['изменить_тату_заказ'])
    dp.register_message_handler(command_command_change_info_tattoo_order,
        Text(equals='изменить тату заказ', ignore_case=True), state=None)
    
    dp.register_message_handler(get_tattoo_order_number,
        state=FSM_Admin_change_tattoo_order.tattoo_order_number)
    dp.register_message_handler(get_new_state_info,
        state=FSM_Admin_change_tattoo_order.tattoo_new_state)
    dp.register_message_handler(get_new_photo, content_types=['photo'],
        state=FSM_Admin_change_tattoo_order.new_photo)
    
    #--------------------------------------------CREATE TATTOO ORDER--------------------------------------
    dp.register_message_handler(command_command_create_tattoo_orders,
        commands=['добавить_тату_заказ'])
    dp.register_message_handler(command_command_create_tattoo_orders,
        Text(equals='добавить тату заказ', ignore_case=True), state=None)
    dp.register_message_handler(get_tattoo_type, state=FSM_Admin_tattoo_order.get_tattoo_type)
    dp.register_message_handler(choice_tattoo_order_admin, state=FSM_Admin_tattoo_order.tattoo_choice)
    dp.register_message_handler(load_tattoo_order_name, state=FSM_Admin_tattoo_order.tattoo_name)
    dp.register_message_handler(load_tattoo_order_photo, content_types=['photo', 'text'],
        state=FSM_Admin_tattoo_order.tattoo_photo)
    dp.register_message_handler(load_tattoo_order_size, state=FSM_Admin_tattoo_order.tattoo_size)
    dp.register_message_handler(get_tattoo_color, state=FSM_Admin_tattoo_order.tattoo_color)
    
    dp.register_message_handler(load_tattoo_order_schedule_choice,
        state=FSM_Admin_tattoo_order.schedule_for_tattoo_order_choice)
    dp.register_message_handler(load_new_tattoo_order_date_from_schedule,
        state=FSM_Admin_tattoo_order.new_tattoo_order_date_from_schedule)

    # dp.register_message_handler(load_datemiting, state=FSM_Client_tattoo_order.date_meeting)
    dp.register_message_handler(load_tattoo_order_note, state=FSM_Admin_tattoo_order.tattoo_note)
    dp.register_message_handler(get_body_name, state=FSM_Admin_tattoo_order.get_body_name_state)
    dp.register_message_handler(get_body_photo, content_types=['photo', 'text', 'video', 'video_note'],
        state=FSM_Admin_tattoo_order.get_body_photo_state)
    dp.register_message_handler(choiсe_tattoo_order_desctiption,
        state=FSM_Admin_tattoo_order.order_desctiption_choiсe)
    dp.register_message_handler(load_order_desctiption_after_choice,
        state=FSM_Admin_tattoo_order.order_desctiption)
    dp.register_message_handler(get_price_tattoo_order_after_choice,
        state=FSM_Admin_tattoo_order.tattoo_order_price)
    
    dp.register_message_handler(get_tattoo_order_state,
        state=FSM_Admin_tattoo_order.tattoo_order_state)
    
    dp.register_message_handler(get_tattoo_order_check,
        state=FSM_Admin_tattoo_order.tattoo_order_check)
    dp.register_message_handler(get_tattoo_order_check_next, content_types=['photo', 'document'],
        state=FSM_Admin_tattoo_order.tattoo_order_check_next)
    
    dp.register_message_handler(tattoo_order_load_user_name,
        state=FSM_Admin_tattoo_order.user_name)
    dp.register_message_handler(answer_user_name,
        state=FSM_Admin_username_info.user_name_answer)
    dp.register_message_handler(load_telegram,
        state=FSM_Admin_username_info.telegram) # добавляет всю инфу про пользователя
    dp.register_message_handler(load_phone,
        state=FSM_Admin_username_info.phone) # добавляет всю инфу про пользователя