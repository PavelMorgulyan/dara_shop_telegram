
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES, CALENDAR_ID, DARA_ID

from db.db_setter import set_to_table
from db.db_updater import update_info
from db.db_getter import get_info_many_from_table, DB_NAME, sqlite3
from handlers.other import * 

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

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
import string, random
from handlers.calendar_client import obj
from msg.main_msg import *
import json


#------------------------------------------ PRICE LIST COMMANDS -----------------------------------
async def get_price_list_commands(message: types.Message):
    if message.text in ['Прайс-лист', '/прайслист'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        await message.reply('Какую команду прайслиста хочешь выполнить?',
            reply_markup= kb_admin.kb_price_list_commands )


#/создать новый прайс-лист на тату
class FSM_Admin_create_price_list(StatesGroup):
    get_min_size_to_new_price_list = State()
    get_max_size_to_new_price_list = State()
    get_price_to_new_price_list = State()


async def command_create_new_price_list_to_tattoo_order(message: types.Message):
    if message.text in ['создать новый прайс-лист на тату', '/создать_новый_прайслист_на_тату'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            await FSM_Admin_create_price_list.get_min_size_to_new_price_list.set()
            await message.reply('Введи, пожалуйста, минимальный размер тату в прайс-листе', 
                reply_markup=kb_admin.kb_sizes)


async def get_min_size_to_new_price_list(message: types.Message, state: FSMContext):
    
    if any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await message.reply(MSG_CANCEL_ACTION + MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_price_list_commands)
        
    elif int(message.text) in kb_admin.sizes_lst:
        async with state.proxy() as data:
            data['min_size'] = int(message.text)
        await FSM_Admin_create_price_list.next()
        await message.reply('Введи, пожалуйста, максимальный размер тату в прайс-листе', 
            reply_markup=kb_admin.kb_sizes)
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_max_size_to_new_price_list(message: types.Message, state: FSMContext):
    
    if any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await message.reply(MSG_CANCEL_ACTION + MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_price_list_commands)
        
    elif int(message.text) in kb_admin.sizes_lst:
        async with state.proxy() as data:
            data['max_size'] = int(message.text)
            min_size = data['min_size']
            max_size = int(message.text)
            
        if max_size > min_size:
            
            """ sqlite_connection = sqlite3.connect(DB_NAME)
            cursor = sqlite_connection.cursor()
            sqlite_select_query = \
                f"SELECT id from tattoo_order_price_list WHERE min_size = {min_size} and\
                    max_size = {max_size}"

            cursor.execute(sqlite_select_query)
            id = cursor.fetchall()
            sqlite_connection.close() """
            
            price = Session(engine).scalars(select(TattooOrderPriceList).where(
                TattooOrderPriceList.min_size == min_size).where(
                TattooOrderPriceList.max_size == max_size)).all()
            
            if price == []:
                await FSM_Admin_create_price_list.next()
                await message.reply('Введи, пожалуйста, цену тату в прайс-листе', 
                    reply_markup= kb_admin.kb_price)
            else:
                await message.reply('У тебя уже есть прайс-лист с такими размерами. '\
                    'Введи, пожалуйста, другой размер.',
                    reply_markup= kb_admin.kb_sizes)
        else:
            await message.reply('Максимальный размер не может быть меньше минимального. '\
                    'Введи, пожалуйста, другой размер.',
                    reply_markup= kb_admin.kb_sizes)
                
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Admin_create_price_list.previous()
        await message.reply(f'{MSG_BACK}.'\
            '❔ Какой минимальный размер хочешь поставить в этой прайс-листе?',
            reply_markup= kb_admin.kb_sizes)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_price_to_new_price_list(message: types.Message, state: FSMContext):
    if any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await message.reply(MSG_CANCEL_ACTION + MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_price_list_commands)
        
    elif message.text == kb_admin.another_price_lst[0]:
        await message.reply('Выбери другую цену для прайс-листа', reply_markup= kb_admin.kb_another_price)
        
    elif message.text in kb_admin.price_lst + kb_admin.another_price_lst:
        async with state.proxy() as data:
            data['price'] = message.text
            with Session(engine) as session:
                new_price_list = TattooOrderPriceList(
                    min_size=  data['min_size'],
                    max_size=  data['max_size'],
                    price=     data['price']
                )
                session.add(new_price_list)
                session.commit()
            min_size, max_size = data['min_size'], data['max_size']
            price = data['price']
        
        await message.reply(
            f'📃 Отлично, теперь у вас новый прайс-лист на размер'\
            f' {min_size} - {max_size} см2 по цене {price}!\n\n'\
            f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup=kb_admin.kb_price_list_commands)
        await state.finish()
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)

async def send_to_view_price_list(message:types.Message, data: ScalarResult[TattooOrderPriceList]):
    headers_dct  = {'Номер' : 'с', 'Min см2' : 'с', 'Max см2' : 'с', 'Цена р.' : 'r'}
    # Определяем таблицу
    table = PrettyTable(list(headers_dct.keys()), left_padding_width = 1, right_padding_width= 1) 
    for header in list(headers_dct.keys()):
        table.align[header] = headers_dct[header]

    for item in data:
        table.add_row([item.id, item.max_size, item.min_size, item.price])
        
    await bot.send_message(message.from_id, f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
    # or use markdown<font color="#fa8e47">
    # await message.reply(f```{table}```, parse_mode="HTML")# types.ParseMode.MARKDOWN_V2)
        
    # await message.reply(f'Вот твои цены\n{table}') # Печатаем таблицу


#/посмотреть_прайслист_на_тату
async def get_to_view_price_list(message: types.Message):
    if message.text in ['посмотреть прайс-лист на тату', '/посмотреть_прайслист_на_тату'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            
            prices = Session(engine).scalars(select(TattooOrderPriceList))
            if prices == []:
                await message.reply(MSG_NO_PRICE_LIST_IN_DB,
                    reply_markup= kb_admin.kb_price_list_commands)
            else:
                await send_to_view_price_list(message, prices)


# удалить прайс-лист тату
class FSM_Admin_delete_price_list(StatesGroup):
    get_name_price_for_delete = State()


async def delete_price_list(message: types.Message):
    if message.text in ['удалить прайс-лист на тату', '/удалить_прайслист_на_тату'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            prices = Session(engine).scalars(select(TattooOrderPriceList))
            if prices == []:
                await message.reply(MSG_NO_PRICE_LIST_IN_DB,
                    reply_markup= kb_admin.kb_price_list_commands)
            else:
                kb = ReplyKeyboardMarkup(resize_keyboard=True)
                await FSM_Admin_delete_price_list.get_name_price_for_delete.set()
                for item in prices:
                    kb.add(KeyboardButton(
                            f'Минимальный размер: {item.min_size} | '\
                            f'Максимальный размер: {item.max_size} | '\
                            f'Цена: {item.price}'
                        )
                    )
                kb.add(kb_admin.kb_back_home)
                await message.reply(f'❔ Какой прайс-лист хочешь удалить?', reply_markup= kb)


async def get_name_for_deleting_price_list(message: types.Message, state: FSMContext):
    
    prices = Session(engine).scalars(select(TattooOrderPriceList))
    price_list = []
    for item in prices:
        price_list.append(
            f'Минимальный размер: {item.min_size} | '\
            f'Максимальный размер: {item.max_size} | '\
            f'Цена: {item.price}'
        )
    if message.text in price_list:
        min_size = message.text.split()[2]
        max_size = message.text.split()[6]
        price = message.text.split()[9] + message.text.split()[10]
        
        price = Session(engine).scalars(select(TattooOrderPriceList).where(
            TattooOrderPriceList.max_size == max_size).where(
            TattooOrderPriceList.min_size == min_size)).one()
        Session(engine).delete(price)
        Session(engine).commit()
        
        await state.finish()
        await message.reply(f'Вы удалили прайс-лист {min_size} - {max_size} по цене {price}.\n\n'\
            f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}', reply_markup= kb_admin.kb_price_list_commands)
        
    elif message.text in LIST_CANCEL_COMMANDS:
        await message.reply(MSG_CANCEL_ACTION + MSG_BACK_TO_HOME)
        await state.finish()
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


class FSM_Admin_change_price_list(StatesGroup):
    get_price_list_name_for_changing = State()
    get_new_status_price_list =  State()
    update_new_status_price_list = State()


#/изменить_прайслист_на_тату
async def change_price_list(message: types.Message):
    if message.text in ['изменить прайс-лист на тату', '/изменить_прайслист_на_тату'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            prices = Session(engine).scalars(select(TattooOrderPriceList))
            if prices == []:
                await message.reply(MSG_NO_PRICE_LIST_IN_DB,
                    reply_markup= kb_admin.kb_price_list_commands)
            else:
                kb = ReplyKeyboardMarkup()
                await FSM_Admin_change_price_list.get_price_list_name_for_changing.set()
                for price in prices:
                    kb.add(KeyboardButton(
                            f'id: {price[0]}|Минимальный размер: {price[1]}|'\
                            f'Максимальный размер: {price[2]}|'\
                            f'Цена: {price[3]}'
                        )
                    )
                await message.reply(f'❔ Какой прайс-лист хочешь поменять?', reply_markup=kb)


async def get_price_list_name_for_changing(message: types.Message, state: FSMContext):
    prices = Session(engine).scalars(select(TattooOrderPriceList))
    
    price_list = []
    for price in prices:
        price_list.append(f'id: {price.id}|Минимальный размер: {price.min_size}|'\
            f'Максимальный размер: {price.max_size}|Цена: {price.price}')
    
    if message.text in price_list:
        async with state.proxy() as data:
            data['id'] = message.text.split('|')[0].split()[1]
            data['min_size'] = message.text.split('|')[1].split()[1]
            data['max_size'] = message.text.split('|')[2].split()[1]
            data['price'] = message.text.split('|')[3].split()[1]
        # 'Минимальный размер' 'Макимальный размер' 'Цена'
        await FSM_Admin_change_price_list.next()
        await message.reply(f'Какую позицию хочешь поменять?',
            reply_markup= kb_admin.kb_change_price_list)


async def get_new_status_price_list(message: types.Message, state: FSMContext):
    if message.text in ['Минимальный размер', 'Макимальный размер', 'Цена']:
        async with state.proxy() as data:
            data['type'] = message.text
            
        await FSM_Admin_change_price_list.next()
        kb = {
            'Минимальный размер':kb_client.kb_another_number_details,
            'Макимальный размер':kb_client.kb_another_number_details,
            'Цена':kb_admin.kb_price
        }
        
        await message.reply('Хорошо, а теперь введи новое значение.', reply_markup= kb[message.text])
            
    elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await message.reply(MSG_CANCEL_ACTION)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_price_list_commands)
    else:
        await message.reply('⭕️ Пожалуйста, выбери из представленных вариантов',
            reply_markup=kb_admin.kb_change_price_list)


async def update_new_status_price_list(message: types.Message, state: FSMContext):
    if message.text == 'Другая цена':
        await message.reply('Хорошо, введи другую цену',
            reply_markup= kb_admin.kb_another_price)
    
    if not any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        async with state.proxy() as data:
            price_list_type = data['type']
            id = data['id']
        updating_price = Session(engine).get(TattooOrderPriceList, id) 
        price_list_types = {
            "Минимальный размер":   updating_price.min_size,
            "Максимальный размер":  updating_price.max_size,
            "Цена":                 updating_price.price
        }

        price_list_types[price_list_type] = message.text
        
        await state.finish()
        await message.reply(
            f'Отлично, вы поменяли \"{price_list_type}\" у прайстлиста!')
        
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_admin.kb_price_list_commands)
    else:
        await state.finish()
        await message.reply(MSG_CANCEL_ACTION + MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_admin.kb_price_list_commands)


def register_handlers_admin_price_list(dp: Dispatcher):
    #-------------------------------------------PRICE LIST COMMANDS----------------------------------
    dp.register_message_handler(get_price_list_commands,
        Text(equals='Прайс-лист', ignore_case=True), state=None)

    dp.register_message_handler(command_create_new_price_list_to_tattoo_order, 
        Text(equals='создать новый прайс-лист на тату', ignore_case=True), state=None)
    dp.register_message_handler(command_create_new_price_list_to_tattoo_order,
        commands=['/создать_новый_прайслист_на_тату'])
    dp.register_message_handler(get_min_size_to_new_price_list,
        state=FSM_Admin_create_price_list.get_min_size_to_new_price_list)
    dp.register_message_handler(get_max_size_to_new_price_list,
        state=FSM_Admin_create_price_list.get_max_size_to_new_price_list)
    dp.register_message_handler(get_price_to_new_price_list,
        state=FSM_Admin_create_price_list.get_price_to_new_price_list)
    
    dp.register_message_handler(get_to_view_price_list,
        Text(equals='посмотреть прайс-лист на тату', ignore_case=True), state=None)
    dp.register_message_handler(get_to_view_price_list,
        commands=['/посмотреть_прайслист_на_тату'], state=None)
    
    dp.register_message_handler(delete_price_list,
        Text(equals='удалить прайс-лист на тату', ignore_case=True), state=None)
    dp.register_message_handler(delete_price_list, commands=['/удалить_прайслист_на_тату'], state=None)
    dp.register_message_handler(get_name_for_deleting_price_list,
        state=FSM_Admin_delete_price_list.get_name_price_for_delete)
    
    dp.register_message_handler(change_price_list, commands=['/изменить_прайслист_на_тату'], state=None)
    dp.register_message_handler(change_price_list,
        Text(equals='изменить прайс-лист на тату', ignore_case=True), state=None)
    dp.register_message_handler(get_price_list_name_for_changing,
        state=FSM_Admin_change_price_list.get_price_list_name_for_changing)
    dp.register_message_handler(get_new_status_price_list,
        state=FSM_Admin_change_price_list.get_new_status_price_list)
    dp.register_message_handler(update_new_status_price_list,
        state=FSM_Admin_change_price_list.update_new_status_price_list)