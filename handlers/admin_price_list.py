
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES, CALENDAR_ID, DARA_ID
from handlers.other import * 

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup

from prettytable import PrettyTable
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
    get_price_list_name = State()
    get_min_size_to_new_price_list = State()
    get_max_size_to_new_price_list = State()
    get_price_to_new_price_list = State()


async def command_create_new_price_list_to_tattoo_order(message: types.Message):
    if message.text in ['создать новый прайс-лист', '/создать_новый_прайслист'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            await FSM_Admin_create_price_list.get_price_list_name.set()
            await message.reply('На что хочешь создать прайс-лист?',
                reply_markup= kb_admin.kb_price_lst_types)


async def get_price_list_name(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.price_lst_types.values()):
        async with state.proxy() as data:
            data['price_lst_type'] = message.text
            
        if message.text in [kb_admin.price_lst_types['constant_tattoo'], 
                kb_admin.price_lst_types['shifting_tattoo']]:
            await FSM_Admin_create_price_list.next()
            await message.reply('Введи, пожалуйста, минимальный размер тату в прайс-листе', 
                reply_markup= kb_admin.kb_sizes)
            
        elif message.text in [kb_admin.price_lst_types['giftbox'], kb_admin.price_lst_types['sketch']]:
            for i in range(3):
                await FSM_Admin_create_price_list.next() #-> get_price_to_new_price_list
            await message.reply(f'Какую цену хочешь установить на {message.text}?',
                reply_markup= kb_admin.kb_price)


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
            price_lst_type = data['price_lst_type']
            max_size = int(message.text)
            
        if max_size > min_size:
            with Session(engine) as session:
                price = session.scalars(select(OrderPriceList)
                    .where(OrderPriceList.type == price_lst_type)
                    .where(OrderPriceList.min_size == min_size)
                    .where(OrderPriceList.max_size == max_size)).all()
            
            if price == []:
                await FSM_Admin_create_price_list.next()
                await message.reply('Введи, пожалуйста, цену в прайс-листе', 
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
        await message.reply('Выбери другую цену для прайс-листа', 
            reply_markup= kb_admin.kb_another_price_full)
        
    elif message.text in kb_admin.price_lst + kb_admin.another_price_full_lst:
        async with state.proxy() as data:
            price_lst_type = data['price_lst_type']
            if price_lst_type in [kb_admin.price_lst_types['constant_tattoo'], 
                kb_admin.price_lst_types['shifting_tattoo']]:
                with Session(engine) as session:
                    new_price_list = OrderPriceList(
                        type= price_lst_type,
                        min_size=  data['min_size'],
                        max_size=  data['max_size'],
                        price=     message.text
                    )
                    session.add(new_price_list)
                    session.commit()
                min_size, max_size = data['min_size'], data['max_size']
            
                await message.reply(
                    f'📃 Отлично, теперь у вас новый прайс-лист на размер'\
                    f' {min_size} - {max_size} см2 по цене {message.text}!\n\n'\
                    f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                    reply_markup= kb_admin.kb_price_list_commands)
            else:
                with Session(engine) as session:
                    new_price_list = OrderPriceList(
                        type=       price_lst_type,
                        min_size=   None,
                        max_size=   None,
                        price=      message.text
                    )
                    session.add(new_price_list)
                    session.commit()
                await message.reply(
                    f'📃 Отлично, теперь у вас новый прайс-лист на {price_lst_type}'
                    f' по цене {message.text}!\n\n'\
                    f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                    reply_markup= kb_admin.kb_price_list_commands)
                
        await state.finish()
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)

async def send_to_view_price_list(
    message:types.Message, 
    data: ScalarResult[OrderPriceList], 
    price_lst_type: str) -> None:
    if price_lst_type in [kb_admin.price_lst_types['constant_tattoo'], 
        kb_admin.price_lst_types['shifting_tattoo']]:
        headers_dct  = {'Номер' : 'с', 'Тип':'с', 'Min см2' : 'с', 'Max см2' : 'с', 'Цена р.' : 'r'}
        # Определяем таблицу
        table = PrettyTable(list(headers_dct.keys()), left_padding_width = 1, right_padding_width= 1) 
        for header in headers_dct.keys():
            table.align[header] = headers_dct[header]
        i = 0
        for item in data:
            i += 1
            table.add_row([str(i), item.type, item.min_size, item.max_size, item.price])
            
        await bot.send_message(message.from_id, f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
        
    else:
        headers_dct  = {'Номер' : 'с', 'Тип':'с', 'Цена р.' : 'r'}
        # Определяем таблицу
        table = PrettyTable(list(headers_dct.keys()), left_padding_width = 1, right_padding_width= 1) 
        for header in headers_dct.keys():
            table.align[header] = headers_dct[header]
        i = 0
        for item in data:
            i += 1
            table.add_row([str(i), item.type, item.price])
            
        await bot.send_message(message.from_id, f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
    # or use markdown<font color="#fa8e47">
    # await message.reply(f```{table}```, parse_mode="HTML")# types.ParseMode.MARKDOWN_V2)
        
    # await message.reply(f'Вот твои цены\n{table}') # Печатаем таблицу


class FSM_Admin_get_to_view_price_lst(StatesGroup):
    get_price_list_type = State()


#/посмотреть_прайслист_на_тату
async def get_to_view_price_list(message: types.Message):
    if message.text in ['посмотреть прайс-лист', '/посмотреть_прайслист'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            await FSM_Admin_get_to_view_price_lst.get_price_list_type.set()
            await message.reply('На что хочешь посмотреть прайс-лист?',
                reply_markup= kb_admin.kb_price_lst_types)


async def get_price_list_name_to_view(message: types.Message, state: FSMContext):
    if message.text in [kb_admin.price_lst_types['constant_tattoo'], 
            kb_admin.price_lst_types['shifting_tattoo']]:
        
        with Session(engine) as session:
            prices = session.scalars(select(OrderPriceList)
                .where(OrderPriceList.type == message.text)
                .order_by(OrderPriceList.min_size)
                .order_by(OrderPriceList.max_size)).all()
            
        if prices == []:
            await message.reply(MSG_NO_PRICE_LIST_IN_DB,
                reply_markup= kb_admin.kb_price_list_commands)
            await state.finish()
        else:
            await send_to_view_price_list(message, prices, message.text)
            await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
                reply_markup= kb_admin.kb_price_list_commands)
            await state.finish()
            
    elif message.text in [kb_admin.price_lst_types['giftbox'], kb_admin.price_lst_types['sketch']]:
        with Session(engine) as session:
            prices = session.scalars(select(OrderPriceList)
                .where(OrderPriceList.type == message.text)).all()
            if prices == []:
                await message.reply(MSG_NO_PRICE_LIST_IN_DB)
            else:
                await send_to_view_price_list(message, prices, message.text)
                
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_admin.kb_price_list_commands)
        await state.finish()
        
    elif message.text in LIST_CANCEL_COMMANDS:
        await message.reply(MSG_CANCEL_ACTION + MSG_BACK_TO_HOME)
        await state.finish()
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# удалить прайс-лист тату
class FSM_Admin_delete_price_list(StatesGroup):
    get_name_price_for_delete = State()


async def delete_price_list(message: types.Message):
    if message.text in ['удалить прайс-лист', '/удалить_прайслист'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            await bot.send_message(message.from_id, 
                'Удалить можно только плайс-листы для тату!\n'\
                'Чтобы поменять прайс-лист для гифтбокса или эскиза, '\
                'нужно нажать кнопку \"изменить прайс-лист\"')
            
            with Session(engine) as session:
                prices = session.scalars(select(OrderPriceList)).all()
                
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
                kb.add(kb_admin.cancel_btn)
                await message.reply(f'❔ Какой прайс-лист хочешь удалить?', reply_markup= kb)


async def get_name_for_deleting_price_list(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        prices = session.scalars(select(OrderPriceList)).all()
        
    price_list = []
    for item in prices:
        price_list.append(
            f'Минимальный размер: {item.min_size} | '\
            f'Максимальный размер: {item.max_size} | '\
            f'Цена: {item.price}'
        )
    if message.text in price_list:
        with Session(engine) as session:
            price = session.scalars(select(OrderPriceList).where(
                OrderPriceList.min_size == message.text.split()[2]).where(
                OrderPriceList.max_size == message.text.split()[6])
                ).one()
            min_size, max_size, price = price.min_size, price.max_size, price.price
            session.delete(price)
            session.commit()
        await state.finish()
        await message.reply(
            f'Вы удалили прайс-лист {min_size} - {max_size} по цене {price}.')
        
        await bot.send_message(message.from_id, 
            f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_admin.kb_price_list_commands)

    elif message.text in LIST_CANCEL_COMMANDS:
        await message.reply(MSG_CANCEL_ACTION + MSG_BACK_TO_HOME)
        await state.finish()
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


class FSM_Admin_change_price_list(StatesGroup):
    get_price_lst_type = State()
    get_price_list_name_for_changing = State()
    get_new_status_price_list =  State()
    update_new_status_price_list = State()


#/изменить_прайслист
async def change_price_list(message: types.Message):
    if message.text in ['изменить прайс-лист', '/изменить_прайслист'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            await FSM_Admin_change_price_list.get_price_lst_type.set()
            await message.reply('Какой тип прайс-листа хочешь изменить?',
                reply_markup= kb_admin.kb_price_lst_types)


async def get_price_list_name_to_change(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.price_lst_types.values()):
        async with state.proxy() as data:
            data['price_lst_type'] = message.text 
            
        
    if message.text in [kb_admin.price_lst_types['constant_tattoo'], 
            kb_admin.price_lst_types['shifting_tattoo']]:
        with Session(engine) as session:
            prices = session.scalars(select(OrderPriceList)
                .where(OrderPriceList.type.in_([kb_admin.price_lst_types['constant_tattoo'], 
                    kb_admin.price_lst_types['shifting_tattoo']]))).all()
        if prices == []:
            await message.reply(MSG_NO_PRICE_LIST_IN_DB,
                reply_markup= kb_admin.kb_price_list_commands)
        else:
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            for price in prices:
                
                kb.add(KeyboardButton(
                        f'id: {price.id}|Минимальный размер: {price.min_size}|'\
                        f'Максимальный размер: {price.max_size}|'\
                        f'Цена: {price.price}'
                    )
                )
                await FSM_Admin_change_price_list.next()
            kb.add(LIST_BACK_TO_HOME[0])
            await message.reply(f'❔ Какой прайс-лист хочешь поменять?', reply_markup=kb)
            
    elif message.text in [kb_admin.price_lst_types['giftbox'], kb_admin.price_lst_types['sketch']]:
        await message.reply(f'Введи, пожалуйста, цену в прайс-листе для {message.text}', 
            reply_markup= kb_admin.kb_price)
        
    elif message.text in kb_admin.price_lst + kb_admin.another_price_full_lst:
        async with state.proxy() as data:
            price_lst_type= data['price_lst_type'] 
            
        with Session(engine) as session:
            price_lst = session.scalars(select(OrderPriceList)
                .where(OrderPriceList.type == price_lst_type)).one()
            old_price = price_lst.price
            price_lst.price = message.text
            session.commit()
        await message.reply(f'Отлично, ты поменял цену у {price_lst_type} c {old_price} на '\
            f'{message.text}')
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        await state.finish()
            
    elif message.text in kb_admin.another_price_lst:
        await message.reply('Введи другую цену', reply_markup= kb_admin.kb_another_price_full)
        
    elif message.text in LIST_CANCEL_COMMANDS:
        await message.reply(MSG_CANCEL_ACTION + MSG_BACK_TO_HOME)
        await state.finish()
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_price_list_name_for_changing(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        prices = session.scalars(select(OrderPriceList)).all()
    
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
    if message.text in ['Минимальный размер', 'Макcимальный размер', 'Цена']:
        async with state.proxy() as data:
            data['type'] = message.text
            
        await FSM_Admin_change_price_list.next()
        kb = {
            'Минимальный размер':kb_client.kb_another_number_details,
            'Макcимальный размер':kb_client.kb_another_number_details,
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
    if message.text == kb_admin.another_price_lst[0]: # 'Другая цена'
        await message.reply('Введи другую цену',
            reply_markup= kb_admin.kb_another_price_full)
    
    elif not any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        async with state.proxy() as data:
            price_list_type = data['type']
            id = data['id']
        
        with Session(engine) as session:
            updating_price = session.get(OrderPriceList, id) 

            if price_list_type == "Минимальный размер":
                updating_price.min_size = message.text
            elif price_list_type == "Макcимальный размер":
                updating_price.max_size = message.text
            else:
                updating_price.price = message.text
            session.commit()
            
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
        Text(equals='создать новый прайс-лист', ignore_case=True), state=None)
    dp.register_message_handler(command_create_new_price_list_to_tattoo_order,
        commands=['создать_новый_прайслист'])
    dp.register_message_handler(get_price_list_name,
        state=FSM_Admin_create_price_list.get_price_list_name)
    dp.register_message_handler(get_min_size_to_new_price_list,
        state=FSM_Admin_create_price_list.get_min_size_to_new_price_list)
    dp.register_message_handler(get_max_size_to_new_price_list,
        state=FSM_Admin_create_price_list.get_max_size_to_new_price_list)
    dp.register_message_handler(get_price_to_new_price_list,
        state=FSM_Admin_create_price_list.get_price_to_new_price_list)
    
    dp.register_message_handler(get_to_view_price_list,
        Text(equals='посмотреть прайс-лист', ignore_case=True), state=None)
    dp.register_message_handler(get_to_view_price_list,
        commands=['/посмотреть_прайслист_на_тату'], state=None)
    dp.register_message_handler(get_price_list_name_to_view,
        state=FSM_Admin_get_to_view_price_lst.get_price_list_type)
    
    
    dp.register_message_handler(delete_price_list,
        Text(equals='удалить прайс-лист', ignore_case=True), state=None)
    dp.register_message_handler(delete_price_list, commands=['/удалить_прайслист'], state=None)
    dp.register_message_handler(get_name_for_deleting_price_list,
        state=FSM_Admin_delete_price_list.get_name_price_for_delete)
    
    dp.register_message_handler(change_price_list, commands=['/изменить_прайслист'], state=None)
    dp.register_message_handler(change_price_list,
        Text(equals='изменить прайс-лист', ignore_case=True), state=None)
    dp.register_message_handler(get_price_list_name_to_change,
        state=FSM_Admin_change_price_list.get_price_lst_type)
    dp.register_message_handler(get_price_list_name_for_changing,
        state=FSM_Admin_change_price_list.get_price_list_name_for_changing)
    dp.register_message_handler(get_new_status_price_list,
        state=FSM_Admin_change_price_list.get_new_status_price_list)
    dp.register_message_handler(update_new_status_price_list,
        state=FSM_Admin_change_price_list.update_new_status_price_list)