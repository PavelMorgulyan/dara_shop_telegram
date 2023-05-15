
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES

from db.db_setter import set_to_table
from db.db_updater import update_info
from handlers.other import * 
from db.db_getter import get_info_many_from_table

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
from msg.main_msg import *



async def get_giftbox_order_command_list(message: types.Message): 
    if message.text.lower() == 'гифтбокс заказ' and \
        str(message.from_user.username) in ADMIN_NAMES:
        await message.reply('Какую команду гифтбокс заказа хочешь выполнить?',
            reply_markup=kb_admin.kb_giftbox_order_commands)


#-------------------------------------------------------GIFTBOX ORDER COMMANDS-----------------------------------------COMPLETE

async def show_giftbox_order(message:types.Message, giftbox_orders: list):

    for ret in giftbox_orders:
        try:
            username_phone = await get_info_many_from_table('clients', 'username', ret[3])
            username_phone = list(username_phone[0])[2]
        except:
            username_phone = 'Нет номера'
            
        await bot.send_message(message.from_user.id,
            f'Гифтбокс заказ № {ret[1]}\n'\
            f'- Имя пользователя: {ret[3]}\n'\
            f'- телефон: {username_phone}\n'\
            f'- описание заказа: {ret[0]}\n'\
            f'- состояние заказа: {ret[5]}\n'\
            f'- дата открытия заказа: {ret[2]}\n') 
        

# /посмотреть_гифтбокс_заказы
async def command_get_info_giftbox_orders(message: types.Message): 
    if message.text.lower() in [ '/посмотреть_гифтбокс_заказы', 'посмотреть гифтбокс заказы'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        giftbox_orders = await get_info_many_from_table('giftbox_orders')
        if giftbox_orders is None:
            await message.reply('Пока у вас нет заказов в таблице', reply_markup=kb_admin.kb_main)
        else:
            await show_giftbox_order(message, giftbox_orders)
            await bot.send_message(message.from_user.id, f'Всего гифтбокс заказов: {len(giftbox_orders)}')


# /посмотреть_закрытые_гифтбокс_заказы
async def command_get_info_closed_giftbox_orders(message: types.Message): 
    if message.text.lower() in [ '/посмотреть_закрытые_гифтбокс_заказы', 'посмотреть закрытые гифтбокс заказы'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        giftbox_orders = await get_info_many_from_table('giftbox_orders', 'order_state', 'Закрыт')
        if giftbox_orders is None:
            await message.reply('Пока у вас нет заказов в таблице', reply_markup= kb_admin.kb_giftbox_order_commands)
            
        else:
            await show_giftbox_order(message, giftbox_orders)
            await bot.send_message(message.from_user.id, f'Всего гифтбокс заказов: {len(giftbox_orders)}')
        

# /посмотреть_активные_оплаченные_гифтбокс_заказы
async def command_get_info_active_paid_giftbox_orders(message: types.Message): 
    if message.text.lower() in \
        [ '/посмотреть_активные_оплаченные_гифтбокс_заказы', 'посмотреть активные оплаченные гифтбокс заказы'] \
        and str(message.from_user.username) in ADMIN_NAMES:
        giftbox_orders = await get_info_many_from_table('giftbox_orders', 'order_state', 'Активный, оплачен')
        if giftbox_orders is None:
            await message.reply('Пока у вас нет заказов в таблице', reply_markup=kb_admin.kb_main)
        else:
            await show_giftbox_order(message, giftbox_orders)
            await bot.send_message(message.from_user.id, f'Всего гифтбокс заказов: {len(giftbox_orders)}')

# /посмотреть_активные_неоплаченные_гифтбокс_заказы
async def command_get_info_active_nopaid_giftbox_orders(message: types.Message): 
    if message.text.lower() == 'посмотреть активные неоплаченные гифтбокс заказы' and \
        str(message.from_user.username) in ADMIN_NAMES:
        giftbox_orders = await get_info_many_from_table('giftbox_orders', 'order_state', 'Активный, неоплачен')
        if giftbox_orders is None:
            await message.reply('Пока у вас нет заказов в таблице', reply_markup=kb_admin.kb_main)
        else:
            await show_giftbox_order(message, giftbox_orders)
            await bot.send_message(message.from_user.id, f'Всего гифтбокс заказов: {len(giftbox_orders)}')


class FSM_Admin_change_state_giftbox_orders(StatesGroup):
    giftbox_order_number = State()
    giftbox_order_state = State()

    

# /поменять_статус_гифтбокс_заказа
async def command_change_state_giftbox_order(message: types.Message): 
    if message.text.lower() in [ '/поменять_статус_гифтбокс_заказа', 'поменять статус гифтбокс заказа'] \
        and str(message.from_user.username) in ADMIN_NAMES:

        giftbox_orders = await get_info_many_from_table('giftbox_orders')
        
        if giftbox_orders is None or giftbox_orders == []:
            await message.reply('Пока у вас нет заказов в таблице', reply_markup=kb_admin.kb_main)
        else:
            kb_giftbox_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
            await FSM_Admin_change_state_giftbox_orders.giftbox_order_number.set()
            await show_giftbox_order(message, giftbox_orders)
            for order in giftbox_orders:
                order = list(order)
                kb_giftbox_numbers.add(KeyboardButton(order[1]))
            kb_giftbox_numbers.add(KeyboardButton('Назад'))

            await bot.send_message(message.from_user.id, 
                f'У какого заказа хочешь поменять статус?',
                reply_markup = kb_giftbox_numbers)

# Определяем номер гифтбокс заказа для изменения статуса
async def get_new_state_giftbox_order(message: types.Message, state: FSMContext):
    if message.text.lower() != 'назад':
        async with state.proxy() as data:
            data['giftbox_order_number'] = message.text
        
        await FSM_Admin_change_state_giftbox_orders.next()
        await bot.send_message(message.from_id, MSG_SEND_ORDER_STATE_INFO)
        await message.reply('На какой статус хочешь поменять?',
            reply_markup = kb_admin.kb_change_status_order)
    else:
        await state.finish()
        await message.reply('Хорошо, ты вернулся назад. Что хочешь сделать?',
            reply_markup = kb_admin.kb_giftbox_order_commands)
    
# Определяем новый статус гифтбокс заказа 
async def set_new_state_giftbox_order(message: types.Message, state: FSMContext): 
    async with state.proxy() as data:
        giftbox_number = data['giftbox_order_number']
        
    await update_info('giftbox_orders',  'order_number', giftbox_number, 'order_state', message.text)
    await message.reply(f'Готово! Вы обновили статус заказа {giftbox_number} на {message.text}',
        reply_markup= kb_admin.kb_main)
    await state.finish() #  полностью очищает данные


def register_handlers_admin_giftbox_order(dp: Dispatcher):
    #-------------------------------------------------------COMMANDS GIFTBOX ORDER------------------------------------------------------
    dp.register_message_handler(get_giftbox_order_command_list, commands='гифтбокс_заказ', state=None)
    dp.register_message_handler(get_giftbox_order_command_list,
        Text(equals='гифтбокс заказ', ignore_case=True), state=None)

    dp.register_message_handler(command_get_info_giftbox_orders,
        commands='посмотреть_гифтбокс_заказы', state=None)
    dp.register_message_handler(command_get_info_giftbox_orders,
        Text(equals='посмотреть гифтбокс заказы', ignore_case=True), state=None)
    
    dp.register_message_handler(command_get_info_closed_giftbox_orders, 
        commands='/посмотреть_закрытые_гифтбокс_заказы', state=None)
    dp.register_message_handler(command_get_info_closed_giftbox_orders,
        Text(equals='посмотреть закрытые гифтбокс заказы', ignore_case=True), state=None)

    dp.register_message_handler(command_get_info_active_paid_giftbox_orders, 
        commands='/посмотреть_активные_оплаченные_гифтбокс_заказы', state=None)
    dp.register_message_handler(command_get_info_active_paid_giftbox_orders,
        Text(equals='посмотреть активные оплаченные гифтбокс заказы', ignore_case=True),
        state=None)
    
    dp.register_message_handler(command_get_info_active_nopaid_giftbox_orders, 
        commands='/посмотреть_активные_неоплаченные_гифтбокс_заказы', state=None)
    dp.register_message_handler(command_get_info_active_nopaid_giftbox_orders,
        Text(equals='посмотреть активные неоплаченные гифтбокс заказы', ignore_case=True),
        state=None)
    
    dp.register_message_handler(command_change_state_giftbox_order,
        Text(equals='поменять статус гифтбокс заказа', ignore_case=True), state=None)
    dp.register_message_handler(command_change_state_giftbox_order,
        commands='/поменять_статус_гифтбокс_заказа', state=None)
    dp.register_message_handler(get_new_state_giftbox_order,
        state=FSM_Admin_change_state_giftbox_orders.giftbox_order_number)
    dp.register_message_handler(set_new_state_giftbox_order, 
        state=FSM_Admin_change_state_giftbox_orders.giftbox_order_state)