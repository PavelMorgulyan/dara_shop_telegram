
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import generate_random_order_number, generate_random_code, \
    CODE_LENTH, ORDER_CODE_LENTH, ADMIN_NAMES, CALENDAR_ID, DARA_ID
                            
from db.db_setter import set_to_table
from db.db_updater import update_info, update_info_in_json
from db.db_filling import dump_to_json
from db.db_delete_info import delete_info, delete_table
from db.db_getter import get_info, get_tables_name, get_info_many_from_table, DB_NAME, sqlite3
from handlers.other import * 

from validate import check_pdf_document_payment, check_photo_payment

#from diffusers import StableDiffusionPipeline
#import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, date, time, timedelta
from aiogram.types.message import ContentType
from aiogram_calendar import simple_cal_callback, SimpleCalendar, dialog_cal_callback, DialogCalendar
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback
from aiogram_timepicker import result, carousel, clock


from prettytable import PrettyTable
from handlers.calendar_client import obj
from msg.main_msg import *


#-----------------------------------  SKETCH COMMANDS LIST-----------------------------------
async def get_tattoo_sketch_order_and_item_command_list(message: types.Message):
    if message.text.lower() in ['эскиз заказы', '/эскиз_заказы'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        await message.reply('Какую команду заказов эскиз хочешь выполнить?',
            reply_markup= kb_admin.kb_tattoo_sketch_commands)


#--------------------------------------  SKETCH COMMANDS -----------------------------------
async def send_to_view_sketch_order(message: types.Message, orders: list):
    username_telegram, username_phone, username = '', '', []
    for order in orders:
        try:
            username = await get_info_many_from_table('clients', 'telegram', order[3])
            username_telegram = list(username[0])[1]
            username_phone = list(username[0])[2]
        except:
            username_telegram = 'Без телеграма'
            username_phone = 'Нет номера'
        '''
            
        '''
        message_to_send = \
            f'№ Заказа эскиза {order[0]} от {order[4]}\n'\
            f'- Описание эскиза: {order[1]}\n' \
            f'- Состояние заказа: {order[5]}\n'\
            f'- Имя пользователя: {order[3]}\n'\
            f'- Telegram пользователя: {username_telegram}\n'\
            f'- Телефон пользователя: {username_phone}\n'
        
        try:
            if '|' not in order[2]:
                await bot.send_photo(message.from_user.id, order[2], message_to_send)
            else:
                '''
                media = [types.InputMediaPhoto('media/Starbucks_Logo.jpg', 'Превосходная фотография'),
                    types.InputMediaPhoto('media/Starbucks_Logo_2.jpg')]  
                    # Показываем, где фото и как её подписать
                    
                await bot.send_chat_action(call.message.chat.id, types.ChatActions.UPLOAD_DOCUMENT)  # Устанавливаем action "Uploading a document..."
                await bot.send_media_group(call.message.chat.id, media=media)  # Отправка фото
                '''
                media = []
                
                for i in range(len(order[2].split('|'))-1):
                    media.append(types.InputMediaPhoto( order[2].split('|')[i], message_to_send))
                # print(f'media: {media}\n\norder[2]:{order[2]}')
                await bot.send_chat_action(message.chat.id, types.ChatActions.UPLOAD_DOCUMENT)
                await bot.send_media_group(message.chat.id, media=media)
                await bot.send_message(message.from_id, message_to_send)
        except:
            await bot.send_message(message.from_id, message_to_send)


#---------------------------------- посмотреть_эскиз_заказы-----------------------------------
# /посмотреть_эскиз_заказы
async def command_get_info_sketch_orders(message: types.Message): 
    # print("ищем заказы в таблице tattoo_sketch_orders") 
    if message.text in ['посмотреть эскиз заказы', '/посмотреть_эскиз_заказы'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            
        orders_into_table = await get_info_many_from_table("tattoo_sketch_orders")
            
        if orders_into_table == []:
            await bot.send_message(message.from_id, MSG_NO_ORDER_IN_TABLE,
                reply_markup = kb_admin.kb_tattoo_sketch_commands)
        else:
            await send_to_view_sketch_order(message, orders_into_table)
            await bot.send_message(message.from_user.id,
                f'Всего заказов: {len(orders_into_table)}',
                reply_markup = kb_admin.kb_tattoo_sketch_commands)


#------------------------------------- посмотреть_эскиз_заказ-----------------------------------
class FSM_Admin_command_get_info_sketch_order(StatesGroup):
    order_name = State()


# /посмотреть_эскиз_заказ
async def command_get_info_sketch_order(message: types.Message): 
    if message.text in ['посмотреть эскиз заказ', '/посмотреть_эскиз_заказ'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        orders_into_table = await get_info_many_from_table('tattoo_sketch_orders')
        if orders_into_table == []:
            await message.reply(MSG_NO_ORDER_IN_TABLE)
        else: 
            kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
            await FSM_Admin_command_get_info_sketch_order.order_name.set()
            
            for order in orders_into_table:
                if order[5] not in list(CLOSED_STATE_DICT.values()):
                    kb_orders.add(KeyboardButton(
                            '№' + str(order[0]) + ' \"' + order[4].split('.')[0] + '\" ' + order[5]
                        )
                    )
            kb_orders.add(KeyboardButton('Назад'))
            await bot.send_message(message.from_user.id, f'Какой заказ хочешь посмотреть?',
                reply_markup = kb_orders)


async def get_name_for_view_sketch_order(message: types.Message, state: FSMContext): 
    orders_into_table = await get_info_many_from_table('tattoo_sketch_orders')
    order_list = []
    for order in orders_into_table:
        order_list.append('№' + str(order[0]) + ' \"' + order[4].split('.')[0] + '\" ' + order[5])
    
    if message.text in order_list:
        order = await get_info_many_from_table('tattoo_sketch_orders', 'order_id', message.text.split()[0][1:])
        await send_to_view_sketch_order(message, order)
        await bot.send_message(message.from_user.id, "Что еще хочешь посмотреть?",
            reply_markup= kb_admin.kb_tattoo_sketch_commands)
        await state.finish()
        
    elif message.text in LIST_CANCEL_COMMANDS+LIST_BACK_COMMANDS:
        await message.reply( 
            "Вы выбрали пойти назад в меню тату. Что еще хочешь посмотреть?",
            reply_markup=kb_admin.kb_tattoo_sketch_commands)
        await state.finish()
        
    else:
        await message.reply( "Пожалуйста, выбери заказ из списка или нажми \"Назад\"")


#-------------------------------------------- удалить_эскиз_заказ---------------------------------
class FSM_Admin_delete_sketch_order(StatesGroup):
    order_number = State()


# /удалить_эскиз_заказ
async def command_delete_info_sketch_order(message: types.Message): 
    if message.text in ['удалить эскиз заказ', '/удалить_эскиз_заказ'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        orders = await get_info_many_from_table('tattoo_sketch_orders')
        if orders == []:
            await message.reply(
                'Прости, пока нет заказов в списке, а значит и удалять нечего. '\
                'Хочешь посмотреть что-то еще?',
                reply_markup=kb_admin.kb_tattoo_sketch_commands)
        else:
            kb_sketch_order_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
            number_not_deleted_order = 0
            for order in orders:
                if order[5] not in CLOSED_STATE_DICT:
                    # выводим наименования тату
                    number_not_deleted_order += 1
                    kb_sketch_order_numbers.add(KeyboardButton(
                        '№' + str(order[0]) + ' \"' + order[4].split('.')[0] + '\" ' + order[5]))
                    
            if number_not_deleted_order != 0:
                kb_sketch_order_numbers.add(KeyboardButton('Назад'))
                await FSM_Admin_delete_sketch_order.order_number.set()
                await message.reply("Какой заказ хотите удалить?",
                    reply_markup=kb_sketch_order_numbers)
            else:
                await message.reply(
                    'Прости, пока нет заказов в списке, они все удалены. Хочешь посмотреть что-то еще?',
                    reply_markup= kb_admin.kb_tattoo_sketch_commands)
            # await message.delete()


async def delete_info_sketch_orders(message: types.Message, state: FSMContext):
    orders = await get_info_many_from_table('tattoo_sketch_orders')
    order_kb_lst = []
    for order in orders:
        order_kb_lst.append('№' + str(order[0]) + ' \"' + order[4].split('.')[0] + '\" ' + order[5])
    
    if message.text in order_kb_lst:
        await delete_info('tattoo_sketch_orders', 'order_id', message.text.split()[0][1:])
        
        await message.reply(f'Заказ эскиза удален.{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_tattoo_sketch_commands)
        await state.finish()
        
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await message.reply(MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_tattoo_sketch_commands)
        await state.finish()
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


#------------------------------ посмотреть активные эскиз заказы-----------------------------------
# 'посмотреть активные эскиз заказы',
async def command_get_info_opened_sketch_orders(message: types.Message): 
    if message.text in ['посмотреть активные эскиз заказы', '/посмотреть_активные_эскиз_заказы'] \
        and str(message.from_user.username) in ADMIN_NAMES:

        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        sqlite_select_query = \
            f"""SELECT * from tattoo_sketch_orders WHERE state in (\'Активный, оплачен\',\
            \'Активный, неоплачен\') """
        cursor.execute(sqlite_select_query)
        orders_into_table = cursor.fetchall()
        if (sqlite_connection):
            sqlite_connection.close()
        
        if orders_into_table is None or orders_into_table == []:
            await bot.send_message(message.from_user.id, MSG_NO_ORDER_IN_TABLE)
        else:
            await send_to_view_sketch_order(message, orders_into_table)
            await bot.send_message(message.from_user.id,
                f'Всего активных заказов: {len(orders_into_table)}',
                reply_markup=kb_admin.kb_tattoo_order_commands)


#--------------------------- посмотреть активные эскиз заказы-----------------------------------
#/посмотреть_закрытые_эскиз_заказы
async def command_get_info_closed_sketch_orders(message: types.Message): 
    if message.text in ['посмотреть закрытые эскиз заказы', '/посмотреть_закрытые_эскиз_заказы'] \
        and str(message.from_user.username) in ADMIN_NAMES:

        sqlite_connection = sqlite3.connect(DB_NAME)
        cursor = sqlite_connection.cursor()
        sqlite_select_query = \
            f"""SELECT * from tattoo_sketch_orders WHERE order_state in (\'Закрыт, оплачен\',\
            \'Закрыт, неоплачен\', \'Закрыт\') """
        cursor.execute(sqlite_select_query)
        orders_into_table = cursor.fetchall()
        
        if (sqlite_connection):
            sqlite_connection.close()
        
        if orders_into_table is None or orders_into_table == []:
            await bot.send_message(message.from_user.id, MSG_NO_ORDER_IN_TABLE)
        else:
            await send_to_view_sketch_order(message, orders_into_table)
            await bot.send_message(
                message.from_user.id, 
                f'Всего закрытых заказов: {len(orders_into_table)}',
                reply_markup=kb_admin.kb_tattoo_order_commands)


class FSM_Admin_command_create_new_sketch_order(StatesGroup):
    get_description = State()
    get_photo_sketch = State()
    get_username_telegram = State()
    get_price = State()
    get_state = State()
    get_check = State()


# добавить эскиз заказ
async def command_create_new_sketch_order(message: types.Message):
    if message.text.lower() in ['добавить эскиз заказ', '/добавить_эскиз_заказ'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            await FSM_Admin_command_create_new_sketch_order.get_description.set() # -> get_new_sketch_description
            await bot.send_message(message.from_id,
                'Ты ввела команду по созданию нового заказа эскиза переводного тату. \n\n'\
                'Данный заказ состоит из: \n'\
                '1) Добавление описания нового эскиза, \n'\
                '2) Добавление фотографий нового эскиза\n'\
                '3) Добавление телеграма клиента\n'\
                '4) Добавление состояния заказа - оплачен или нет\n'\
                '5) Возможность добавления чека, если заказ оплачен' )
            await bot.send_message(message.from_id, 'Введи описание для нового эскиза', 
                reply_markup= kb_client.kb_cancel)


async def fill_sketch_order_table(data:dict, message: types.Message):
    await set_to_table(tuple(data.values()), 'tattoo_sketch_orders')
    date = data['creation_time'] 
    start_time = f'{date.strftime("%Y-%m-%dT%H:%M:%S")}'
    
    if DARA_ID != 0:
        await bot.send_message(DARA_ID, f'Дорогая Тату-мастерица! '\
        f"🕸 Поступил новый заказ на эскиз под номером {data['id']}!")
    
    event = await obj.add_event(CALENDAR_ID,
        f"Новый эскиз заказ № {data['id']}",
        'Описание тату: ' +  data['sketch_description'] + ' \n' + \
        'Имя клиента:' + data['telegram'],
        start_time, # '2023-02-02T09:07:00',
        start_time    # '2023-02-03T17:07:00'
    )
    
    await message.reply(
        '🎉 Отлично, заказ на эскиз оформлен!\n'\
        f"Номер твоего заказа эскиза {data['id']}\n\n"\
        f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
        reply_markup = kb_admin.kb_tattoo_sketch_commands)


async def fill_client_table(data: dict, message: types.Message):
    client = get_info_many_from_table('clients', 'telegram', data['telegram'])
    if client == []:
        await set_to_table(tuple(data.values()), 'clients')
        await message.reply( f'Ты успешно добавила нового клиента! {MSG_DO_CLIENT_WANT_TO_DO_MORE}')
        
    else:
        await message.reply( f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}')


async def get_new_sketch_description(message: types.Message, state: FSMContext):
    tattoo_sketch_order = await generate_random_order_number(CODE_LENTH)
    async with state.proxy() as data:
        data['first_photo'] = False
        data['tattoo_sketch_order'] = tattoo_sketch_order
        data['sketch_photo_list'] = ''
        data['state'] =  'Активный, неоплачен'
        data['check_document'] = 'Без чека'
        
    if message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, 
            reply_markup = kb_admin.kb_tattoo_sketch_commands)
        
        ''' elif message.text == kb_client.yes_str:
        await FSM_Admin_command_create_new_sketch_order.next()
        await bot.send_message(message.from_id, 'Хорошо, добавь фото эскиза',
            reply_markup=kb_client.kb_cancel)
        
        elif message.text == kb_client.no_str:
            for i in range(2):
                await FSM_Admin_command_create_new_sketch_order.next()
            await bot.send_message(message.from_id,
                'Хорошо, закончим с добавлением фотографий для нового эскиза.\n\n'\
                'Для какого пользователя заказ?\n'\
                'Введи его имя или телеграм (с символом \"@\") или ссылку с \"https://t.me/\".\n\n',
                reply_markup= kb_admin.kb_admin_add_name_or_telegram_for_new_order
            ) 
        '''
    else:
        await FSM_Admin_command_create_new_sketch_order.next() # -> get_photo_sketch
        async with state.proxy() as data:
            data['sketch_description'] = message.text
        await bot.send_message(message.from_id,
            'Пожалуйста, добавь фото для нового эскиза',
            reply_markup= kb_client.kb_cancel)


async def get_photo_sketch(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        if message.text in LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(MSG_BACK_TO_HOME, 
                reply_markup = kb_admin.kb_tattoo_sketch_commands)
        elif message.text == kb_client.yes_str:
            async with state.proxy() as data:
                data['first_photo'] = True
            await bot.send_message(message.from_id, 'Добавь еще одно фото через файлы', 
                reply_markup= kb_client.kb_cancel)
            
        elif message.text == kb_client.no_str:
                
            await FSM_Admin_command_create_new_sketch_order.next() # -> get_username_telegram
            await bot.send_message(message.from_id,
                'Хорошо, закончим с добавлением фотографий для нового эскиза.\n\n'\
                'Для какого пользователя заказ?\n'\
                'Введи его имя или телеграм (с символом \"@\") или ссылку с \"https://t.me/\".\n\n',
                #'P.s. Нажимая на пользователя в ТГ сверху будет его имя. '\
                #'А имя с символом \"@\" - ссылка на телеграм',
                reply_markup= kb_client.kb_cancel
            )
        else:
            await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
    
    if message.content_type == 'photo':
        async with state.proxy() as data:
            ''' 
            first_photo = data['first_photo']
            if first_photo:
                data['sketch_photo_list'] = message.photo[0].file_id
            else: '''
            data['sketch_photo_list'] += message.photo[0].file_id + '|'
        
        await bot.send_message(message.from_id, 'Хочешь добавить еще фото?',
            reply_markup= kb_client.kb_yes_no)


async def get_username_telegram(message: types.Message, state: FSMContext):
    if '@' in message.text or 'https://t.me/' in message.text:
        async with state.proxy() as data:
            if '@' in message.text:
                data['username'] = message.text.split('@')[1]
                data['telegram'] = message.text
                
            else:
                data['username'] = message.text.split('/')[3]
                data['telegram'] = '@' + message.text.split('/')[3]
            client = await get_info_many_from_table('clients', 'telegram', data['telegram'])
            if client == []:
                await bot.send_message(message.from_id, 
                    'Хочешь добавить телефон пользователя?',
                    reply_markup= kb_client.kb_yes_no)
            else:
                await FSM_Admin_command_create_new_sketch_order.next() #-> get_sketch_price
                await bot.send_message(message.from_id, 'Добавь цену эскиза переводного тату',
                    reply_markup= kb_admin.kb_price)
        
    elif message.text == kb_client.yes_str:
        await bot.send_message(message.from_id, 'Отправь телефон пользователя',
            reply_markup= kb_client.kb_cancel)
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            data['phone'] = 'Нет номера'
            new_client_data = {
                'username': data['username'],
                'telegram': data['telegram'],
                'phone':    data['phone'] 
            }
            await fill_client_table(new_client_data, message)
            
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)    


async def get_sketch_price(message: types.Message, state: FSMContext):
    if message.text in kb_admin.price + kb_admin.another_price:
        async with state.proxy() as data:
            data['price'] = message.text
        await bot.send_message(message.from_id, 'Данный заказ оплачен?', 
            reply_markup= kb_client.kb_yes_no)
        await FSM_Admin_command_create_new_sketch_order.next() # -> get_sketch_state
            
    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, 
            reply_markup = kb_admin.kb_tattoo_sketch_commands)
        
    elif message.text == 'Другая цена':
        await bot.send_message(message.from_id, 'Хорошо, укажи другую цену',
            reply_markup= kb_admin.kb_another_price)
        
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Admin_command_create_new_sketch_order.previous() # -> get_username_telegram
        await bot.send_message(message.from_id,
            'Для какого пользователя заказ?\n'\
            'Введи его имя или телеграм (с символом \"@\") или ссылку с \"https://t.me/\".\n\n',
            #'P.s. Нажимая на пользователя в ТГ сверху будет его имя. '\
            #'А имя с символом \"@\" - ссылка на телеграм',
            reply_markup= kb_client.kb_cancel
        )
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)  


async def get_sketch_state(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            data['state'] =  'Активный, оплачен'
        await bot.send_message(message.from_id, 'Хочешь добавить чек заказа?', 
            reply_markup= kb_client.kb_yes_no)
        await FSM_Admin_command_create_new_sketch_order.next() # -> get_sketch_check
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            new_sketch_order = {
                'order_id':             data['tattoo_sketch_order'],
                'sketch_description':   data['sketch_description'],
                'photo_list':           data['sketch_photo_list'], 
                'telegram':             data['telegram'],
                'creation_time':        datetime.now(),
                'state':                data['state'],
                'check_document':       data['check_document'],
                'price':                data['price']
            }
        await fill_sketch_order_table(new_sketch_order, message)
        await state.finish()
        
    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, 
            reply_markup = kb_admin.kb_tattoo_sketch_commands)
        
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Admin_command_create_new_sketch_order.previous() # -> get_sketch_price
        await bot.send_message(message.from_id, 'Добавь цену эскиза переводного тату',
            reply_markup= kb_admin.kb_price)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)  


async def get_sketch_check(message: types.Message, state: FSMContext):
    
    if message.content_type == 'text':
        if message.text == kb_client.yes_str:
            await bot.send_message(message.from_id, 
                'Хорошо, добавь фотографию или документ чека', 
                reply_markup= kb_client.kb_cancel)
            
        elif message.text == kb_client.no_str:
            async with state.proxy() as data:
                new_sketch_order = {
                    'order_id':             data['tattoo_sketch_order'],
                    'sketch_description':   data['sketch_description'],
                    'photo_list':           data['sketch_photo_list'], 
                    'telegram':             data['telegram'],
                    'creation_time':        datetime.now(),
                    'state':                data['state'],
                    'check_document':       data['check_document'],
                    'price':                data['price']
                }
            await fill_sketch_order_table(new_sketch_order, message)
            await state.finish()
            
        elif message.text in LIST_CANCEL_COMMANDS:
            await state.finish()
            await message.reply(MSG_BACK_TO_HOME, 
                reply_markup = kb_admin.kb_tattoo_sketch_commands)
            
        elif message.text in LIST_BACK_COMMANDS:
            await FSM_Admin_command_create_new_sketch_order.previous() # -> get_sketch_state
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK} Заказ оплачен?',
                reply_markup= kb_client.kb_yes_no)
            
        else:
            await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST) 
            
    elif message.content_type == 'document':
        async with state.proxy() as data:
            data['check_document'] = message.document.file_id
            check_doc_pdf = await check_pdf_document_payment(
                user_id = message.from_id,
                price = data['price'],
                file_name = data['tattoo_sketch_order'] + '.pdf',
                file_id = data['check_document']
            ) 
            
            if check_doc_pdf:
                new_sketch_order = {
                    'order_id':             data['tattoo_sketch_order'],
                    'sketch_description':   data['sketch_description'],
                    'photo_list':           data['sketch_photo_list'], 
                    'telegram':             data['telegram'],
                    'creation_time':        datetime.now(),
                    'state':                data['state'],
                    'check_document':       data['check_document'],
                    'price':                data['price']
                }
                await fill_sketch_order_table(new_sketch_order, message)
                await state.finish()
            else:
                await message.reply( f'Чек не подошел! Попробуй другой документ или изображение.')  
        
    elif message.content_type == 'photo':
        async with state.proxy() as data:
            data['check_document'] = message.photo[0].file_id
            check_doc_photo = await check_photo_payment(
                message, message.from_id, data['price'], data['tattoo_sketch_order'], data['check_document'])
            
            if check_doc_photo["result"]:
                new_sketch_order = {
                    'order_id':             data['tattoo_sketch_order'],
                    'sketch_description':   data['sketch_description'],
                    'photo_list':           data['sketch_photo_list'], 
                    'telegram':             data['telegram'],
                    'creation_time':        datetime.now(),
                    'state':                data['state'],
                    'check_document':       data['check_document'],
                    'price':                data['price']
                }
                await fill_sketch_order_table(new_sketch_order, message)
                await state.finish()
            else:
                await message.reply( f'Чек не подошел! Попробуй другой документ или изображение.')  


#------------------------------------SKETCH ORDER-------------------------------------------
def register_handlers_admin_sketch(dp: Dispatcher):
    dp.register_message_handler(get_tattoo_sketch_order_and_item_command_list,
        commands=['эскиз_заказы'])
    dp.register_message_handler(get_tattoo_sketch_order_and_item_command_list,
        Text(equals='Эскиз заказы', ignore_case=True), state=None)
    
    dp.register_message_handler(command_get_info_sketch_orders, commands=['посмотреть_эскиз_заказы'])
    dp.register_message_handler(command_get_info_sketch_orders,
        Text(equals='посмотреть эскиз заказы', ignore_case=True), state=None)
    
    dp.register_message_handler(command_get_info_sketch_order, commands=['посмотреть_эскиз_заказ'])
    dp.register_message_handler(command_get_info_sketch_order,
        Text(equals='посмотреть эскиз заказ', ignore_case=True), state=None)
    dp.register_message_handler(get_name_for_view_sketch_order,
        state=FSM_Admin_command_get_info_sketch_order.order_name)
    
    dp.register_message_handler(command_delete_info_sketch_order, commands=['удалить_эскиз_заказ'])
    dp.register_message_handler(command_delete_info_sketch_order,
        Text(equals='удалить эскиз заказ', ignore_case=True), state=None)
    dp.register_message_handler(delete_info_sketch_orders, 
        state=FSM_Admin_delete_sketch_order.order_number)
    
    dp.register_message_handler(command_get_info_opened_sketch_orders,
        Text(equals='посмотреть активные эскиз заказы', ignore_case=True), state=None)
    
    dp.register_message_handler(command_get_info_closed_sketch_orders,
        Text(equals='посмотреть закрытые эскиз заказы', ignore_case=True), state=None)

    dp.register_message_handler(command_create_new_sketch_order, commands=['добавить_эскиз_заказ'])
    dp.register_message_handler(command_create_new_sketch_order, 
        Text(equals='добавить эскиз заказ', ignore_case=True), state=None)
    
    dp.register_message_handler(get_new_sketch_description, 
        state=FSM_Admin_command_create_new_sketch_order.get_description)
    dp.register_message_handler(get_photo_sketch, content_types=['photo', 'text'],
        state=FSM_Admin_command_create_new_sketch_order.get_photo_sketch)
    dp.register_message_handler(get_username_telegram,
        state=FSM_Admin_command_create_new_sketch_order.get_username_telegram)
    dp.register_message_handler(get_sketch_price,
        state=FSM_Admin_command_create_new_sketch_order.get_price)
    dp.register_message_handler(get_sketch_state,
        state=FSM_Admin_command_create_new_sketch_order.get_state)
    dp.register_message_handler(get_sketch_check, content_types=['photo', 'document', 'text'], 
        state=FSM_Admin_command_create_new_sketch_order.get_check)