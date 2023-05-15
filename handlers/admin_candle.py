
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES

from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from db.db_setter import set_to_table
from db.db_getter import get_info_many_from_table

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from db.db_delete_info import delete_info
from prettytable import PrettyTable
from handlers.calendar_client import obj
from msg.main_msg import *


#--------------------------------------CANDLE COMMAND LIST-----------------------------------
# /добавить_свечу, Отправляем название свечи 
async def get_candle_command_list(message: types.Message):
    if message.text.lower() in ['свеча', '/свеча'] and \
        str(message.from_user.username) in ADMIN_NAMES:
            await message.reply('Какую команду со свечами хочешь выполнить?',
                reply_markup=kb_admin.kb_candle_item_commands)


#-----------------------------------------CANDLE ITEM-----------------------------------COMPLETE
class FSM_Admin_candle_item(StatesGroup):
    candle_name = State()
    candle_photo = State()
    candle_price = State() 
    candle_note = State()
    candle_state = State()
    candle_numbers = State()


# /добавить_свечу, Отправляем название свечи 
async def command_load_candle_item(message: types.Message):
    if message.text.lower() in ['добавить свечу', '/добавить_свечу'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        await FSM_Admin_candle_item.candle_name.set()
        await message.reply('Введи название свечи') 


# Отправляем название свечи 
async def load_candle_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['candle_name'] = message.text
    await FSM_Admin_candle_item.next()
    await message.reply('А теперь загрузи фотографию свечи') 


# Отправляем фото свечи
async def load_candle_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['candle_photo'] = message.photo[0].file_id
    await FSM_Admin_candle_item.next()
    await message.reply('Введи цену свечи')


# Отправляем стоимость свечи
async def load_candle_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['candle_price'] = message.text
    await FSM_Admin_candle_item.next()
    await message.reply('Введи описание свечи')


# Отправляем описание свечи 
async def load_candle_note(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['candle_note'] = message.text
    await FSM_Admin_candle_item.next()
    await message.reply('Свеча есть в наличии?', reply_markup= kb_client.kb_have_yes_no)


# Отправляем статус товара свечей и заводим новую строку в таблице candle_items, если количество свечей = 0
async def load_candle_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['candle_state'] = message.text
    
    if message.text == 'Есть в наличии':
        await FSM_Admin_candle_item.next()
        await message.reply('Сколько таких свечей у тебя есть? Напиши количество',
            reply_markup=kb_admin.kb_main)
    else:
        async with state.proxy() as data:
            data['candle_state'] = message.text
            data['candle_numbers'] = 0
            await set_to_table(tuple(data.values()), 'candle_items')
        await message.reply('Готово! Вы добавили свечу в таблицу', reply_markup=kb_admin.kb_main)
        await state.finish() #  полностью очищает данные


# Добавляем количество закупленных свечей данного типа и заводим новую строку в таблице candle_items
async def load_candle_numbers(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['candle_numbers'] = int(message.text)
        await set_to_table(tuple(data.values()), 'candle_items')
    await message.reply('Готово! Вы добавили свечу в таблицу', reply_markup=kb_admin.kb_main)
    await state.finish() #  полностью очищает данные


#---------------------------------CANDLE /посмотреть_список_свечей--------------------------COMPLETE
# /посмотреть_список_свечей,  посмотреть список свечей
async def command_get_info_candles(message: types.Message): 
    if message.text.lower() in ['посмотреть список свечей', '/посмотреть_список_свечей'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        candles = await get_info_many_from_table('candle_items')
        if candles == []:
            await bot.send_message(message.from_user.id, "Увы, в базе пока нет свечей(")
        else:
            for item in candles:
                await bot.send_photo(
                    message.from_user.id, item[1] , f' Свеча {item[0]}\n- Цена: {item[2]}' \
                    f'\n- Описание: {item[3]}\n- Статус: {item[4]}\n- Количество: {item[5]}'
                ) 


class FSM_Admin_get_info_candle_item(StatesGroup):
    candle_name = State()  


class FSM_Admin_delete_info_candle_item(StatesGroup):
    candle_name = State()  


#-------------------------------------------CANDLE /посмотреть_свечу-----------------------COMPLETE  
# /посмотреть_свечу
async def command_get_info_candle(message: types.Message): 
    if message.text.lower() in ['посмотреть свечу', '/посмотреть_свечу'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        candles = await get_info_many_from_table('candle_items')
        kb_candles_names = ReplyKeyboardMarkup(resize_keyboard=True)
        for item in candles:
            kb_candles_names.add(item[0])
        await FSM_Admin_get_info_candle_item.candle_name.set()
        await message.reply('Какое свечу хочешь посмотреть?', reply_markup=kb_candles_names)


async def get_candle_name_for_info(message: types.Message, state: FSMContext): 
    try:
        candle = await get_info_many_from_table('candle_items', 'name', message.text)
        item = candle[0]
        msg = \
            f'- Название: {item[0]}\n'\
            f'- Цена: {item[2]}\n' \
            f'- Статус: {item[4]}\n'\
            f'- Количество: {item[5]}\n'
        
        if str(item[3]).lower() != 'без описания':
            msg += f'- Описание: {item[3]}\n'
            
        await bot.send_photo(message.from_user.id, item[1], msg) 
        
        await message.reply('Чего еще хочешь посмотреть?',
            reply_markup= kb_admin.kb_candle_item_commands)
        await state.finish() #  полностью очищает данные
    except:
        await message.reply('Неверное указание имени свечи, попробуй другую')


#-----------------------CANDLE /посмотреть_список_имеющихся_свечей--------------------------COMPLETE 
# /посмотреть_список_имеющихся_свечей
async def command_get_info_candles_having(message: types.Message):
    if message.text.lower() in ['посмотреть список имеющихся свечей',
        '/посмотреть_список_имеющихся_свечей'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        candles = await get_info_many_from_table(
            'candle_items', column_name='state', condition='Есть в наличии')
        i = 1
        if candles == []:
            await bot.send_message(message.from_user.id, 
                "Увы, у тебя пока нет купленных свечей(")
        else:
            for item in candles:
                await bot.send_photo(
                    message.from_user.id, item[1] ,  f' Свеча {item[0]}\n- Цена: {item[2]}'\
                    f'\n- Описание: {item[3]}\n- Статус: {item[4]}\n-  Количество: {item[5]}',
                    reply_markup=kb_admin.kb_main
                ) 
                i += 1
        await message.reply('Чего еще хочешь посмотреть, моя госпожа?', 
            reply_markup=kb_admin.kb_candle_item_commands)


#--------------------------CANDLE /посмотреть_список_не_имеющихся_свечей-------------------COMPLETE
# /посмотреть_список_не_имеющихся_свечей
async def command_get_info_candles_not_having(message: types.Message):
    if message.text.lower() in ['посмотреть список не имеющихся свечей', 
        '/посмотреть_список_не_имеющихся_свечей'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        candles = await get_info_many_from_table('candle_items', 'state', 'Не в наличии')
        i = 1
        if candles == []:
            await bot.send_message(message.from_user.id, 
                "У тебя все свечи есть! Глянь в таблице купленных свечей")
        else:
            for item in candles:
                await bot.send_photo(
                    message.from_user.id, item[1] ,  f'  Свеча  {item[0]}\n- Цена: {item[2]}' \
                    f'\n- Описание: {item[3]}\n- Статус: {item[4]}\n- Количество: {item[5]}',
                    reply_markup=kb_admin.kb_main) 
                i += 1
        await message.reply('Чего еще хочешь посмотреть, моя госпожа?', 
            reply_markup= kb_admin.kb_candle_item_commands)


#---------------------------------------------CANDLE /удалить_свечу--------------------------COMPLETE
# /удалить_свечу
async def delete_info_candle_in_table(message: types.Message): 
    if message.text.lower() in ['удалить свечу', '/удалить_свечу'] and\
        str(message.from_user.username) in ADMIN_NAMES:
        candles = await get_info_many_from_table('candle_items')
        if candles == []:
            await bot.send_message(message.from_user.id, 
                "В базе пока нет свечей")
        else:
            i = 1
            kb_candle_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in candles:
                await bot.send_photo(
                    message.from_user.id, 
                    item[1], 
                    f'Свеча {item[0]}\n'\
                    f'- Цена: {item[2]}\n' \
                    f'- Размер: {item[3]}\n'\
                    f'- Описание: {item[4]}'
                ) 
                kb_candle_names.add(KeyboardButton(item[0]))
                i += 1
            kb_candle_names.add(KeyboardButton('Отмена'))
            await FSM_Admin_delete_info_candle_item.candle_name.set()
            await bot.send_message(message.from_user.id, "Какую свечу удалить?",
                reply_markup= kb_candle_names)


async def delete_info_candle_in_table_next(message: types.Message, state: FSMContext):
    candle = await get_info_many_from_table('candle_items', 'name', message.text)
    if message.text == list(candle[0])[0]:
        await delete_info('candle_items', 'name', message.text)
        await message.reply(f'Готово! Вы удалили свечу {message.text}', 
            reply_markup= kb_admin.kb_main)
        await state.finish()
        
    elif message.text in LIST_CANCEL_COMMANDS:
        await bot.send_message(message.from_user.id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


def register_handlers_admin_candle(dp: Dispatcher):
    #-------------------------------------CANDLE--------------------------------------
    dp.register_message_handler(get_candle_command_list, commands=['свеча'], state=None)
    dp.register_message_handler(get_candle_command_list, 
        Text(equals='свеча', ignore_case=True), state=None)

    dp.register_message_handler(command_load_candle_item, commands=['добавить_свечу'], state=None)
    dp.register_message_handler(command_load_candle_item, 
        Text(equals='добавить свечу', ignore_case=True), state=None)
    dp.register_message_handler(load_candle_name, state=FSM_Admin_candle_item.candle_name)
    dp.register_message_handler(load_candle_photo, content_types=['photo'], 
        state=FSM_Admin_candle_item.candle_photo)
    dp.register_message_handler(load_candle_price, state=FSM_Admin_candle_item.candle_price)
    dp.register_message_handler(load_candle_note, state=FSM_Admin_candle_item.candle_note)
    dp.register_message_handler(load_candle_state, state=FSM_Admin_candle_item.candle_state)
    dp.register_message_handler(load_candle_numbers, state=FSM_Admin_candle_item.candle_numbers)
    
    dp.register_message_handler(command_get_info_candles,
        commands=['посмотреть_список_свечей'])
    dp.register_message_handler(command_get_info_candles,
        Text(equals='посмотреть список свечей', ignore_case=True), state=None)
    
    dp.register_message_handler(command_get_info_candles_having,
        commands=['посмотреть_список_имеющихся_свечей'])
    dp.register_message_handler(command_get_info_candles_having,
        Text(equals='посмотреть список имеющихся свечей', ignore_case=True), state=None)
    
    dp.register_message_handler(command_get_info_candles_not_having,
        commands=['посмотреть_список_не_имеющихся_свечей'])
    dp.register_message_handler(command_get_info_candles_not_having,
        Text(equals='посмотреть список не имеющихся свечей', ignore_case=True), state=None)

    dp.register_message_handler(command_get_info_candle,
        commands=['посмотреть_свечу'])
    dp.register_message_handler(command_get_info_candle,
        Text(equals='посмотреть свечу', ignore_case=True), state=None)
    dp.register_message_handler(get_candle_name_for_info,
        state=FSM_Admin_get_info_candle_item.candle_name)
    
    dp.register_message_handler(delete_info_candle_in_table, commands=['удалить_свечу'])
    dp.register_message_handler(delete_info_candle_in_table,
        Text(equals='удалить свечу', ignore_case=True), state=None)
    dp.register_message_handler(delete_info_candle_in_table_next,
        state=FSM_Admin_delete_info_candle_item.candle_name)