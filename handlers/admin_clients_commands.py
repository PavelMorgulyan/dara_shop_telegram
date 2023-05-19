from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup

from prettytable import PrettyTable
from handlers.calendar_client import obj
from msg.main_msg import *

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *



#-------------------------------------------------------CLIENT-------------------------------------------
# /пользователи
async def get_clients_command_list(message: types.Message):
    await message.reply('Какие комманды для пользователей хочешь ввести?',
        reply_markup= kb_admin.kb_clients_commands)


#-------------------------------------------------------VIEW ALL USERS-------------------------------------------
class FSM_Admin_get_info_user(StatesGroup):
    user_name = State()

async def send_to_view_users_orders(user_lst:list, message: types.Message):
    if user_lst != []:
        for user in user_lst: # выводим наименования клиентов
            with Session(engine) as session:
                orders = session.scalars(select(Orders).where(
                    Orders.username == user.name)).all()
            for order in orders:
                headers  = ['№', 'Тип заказа', 'Пользователь', 'Номер заказа', 'Статус',]
                table = PrettyTable(headers, left_padding_width = 1, right_padding_width= 1)  # Определяем таблицу
                table.add_row([order.id, order.order_type, order.username, order.order_number, order.order_state])
        await bot.send_message(message.from_id, f'<pre>{table}</pre>', parse_mode=types.ParseMode.HTML)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE, reply_markup= kb_admin.kb_clients_commands)
    else:
        await message.reply(f'Сейчас нет пользователей в базе. {MSG_DO_CLIENT_WANT_TO_DO_MORE}')
    
    
# /посмотреть_всех_пользователей
async def get_users_info_command(message: types.Message):
    if message.text.lower() == 'посмотреть всех пользователей' and \
        str(message.from_user.username) in ADMIN_NAMES:
        with Session(engine) as session:
            users = session.scalars(select(User)).all()
        await send_to_view_users_orders(users, message)


#-------------------------------------------------------VIEW CLIENT-------------------------------------------
# /посмотреть_пользователя
async def get_user_info_command(message: types.Message):
    if message.text.lower() == 'посмотреть пользователя' and \
        str(message.from_user.username) in ADMIN_NAMES:
        with Session(engine) as session:
            users = session.scalars(select(User)).all()
        if users != []:
            kb_users_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for user in users:
                kb_users_names.add(KeyboardButton(user.name)) # выводим наименования клиентов
            await FSM_Admin_get_info_user.user_name.set()
            await message.reply('Какого пользователя хочешь посмотреть?', reply_markup= kb_users_names)
        else:
            await message.reply('Прости, но у тебя пока нет пользователей в таблице')


async def get_user_info_command_with_name(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        users = session.scalars(select(User)).all()
    user_name_lst = []
    for user in users:
        user_name_lst.append(user.name)
        
    if message.text in user_name_lst:
        await send_to_view_users_orders(users, message)
        await state.finish()
    else:
        await message.reply(f'Пользователя с именем {message.text} нет. Попробуй другого.')


#---------------------------------DELETE CLIENT-------------------------------------
class FSM_Admin_delete_info_user(StatesGroup):
    user_name = State()
    
# /удалить_пользователя
async def delete_username_command(message: types.Message):
    if message.text.lower() == 'удалить пользователя' and str(message.from_user.username) in ADMIN_NAMES:
        with Session(engine) as session:
            users = session.scalars(select(User)).all()
        if users == []:
            await message.reply('У тебя пока нет пользователей в базе. Чего еще хочешь сделать?',
                reply_markup= kb_admin.kb_main)
        else:
            kb_users_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for user in users:
                kb_users_names.add(KeyboardButton(user.name)) # выводим наименования пользователей
            await FSM_Admin_delete_info_user.user_name.set()
            
            await message.reply('Какого пользователя хочешь удалить?', reply_markup=kb_users_names)


async def delete_user_with_name(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        users = session.scalars(select(User)).all()
    user_name_lst = []
    for user in users:
        user_name_lst.append(user.name)
    if message.text in user_name_lst:
        with Session(engine) as session:
            user = session.scalars(select(User).where(User.name == message.text)).one()
            session.delete(user)
            session.commit()
            
        await message.reply(f'Готово! Вы удалили пользователя {message.text}',
            reply_markup= kb_admin.kb_clients_commands)
        await state.finish()
    else:
        await message.reply(f'Пользователя с именем {message.text} нет. Попробуй другого.')


def register_handlers_admin_client_commands(dp: Dispatcher):
    #-------------------------------------------------------CLIENTS------------------------------------------------------
    dp.register_message_handler(get_clients_command_list, commands=['пользователи'])
    dp.register_message_handler(get_clients_command_list,
        Text(equals='пользователи', ignore_case=True), state=None)


    dp.register_message_handler(delete_username_command, commands=['удалить_пользователя'])
    dp.register_message_handler(delete_username_command,
        Text(equals='удалить пользователя', ignore_case=True), state=None)
    dp.register_message_handler(delete_user_with_name, state=FSM_Admin_delete_info_user.user_name)
    
    dp.register_message_handler(get_users_info_command, commands=['посмотреть_всех_пользователей'])
    dp.register_message_handler(get_users_info_command,
        Text(equals='посмотреть всех пользователей', ignore_case=True), state=None)
    
    dp.register_message_handler(get_user_info_command, commands=['посмотреть_пользователя'])
    dp.register_message_handler(get_user_info_command, 
        Text(equals='посмотреть пользователя', ignore_case=True))
    dp.register_message_handler(get_user_info_command_with_name,
        state=FSM_Admin_get_info_user.user_name)