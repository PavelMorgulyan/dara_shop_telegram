from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES

from db.db_delete_info import delete_info
from db.db_getter import get_info_many_from_table

#from diffusers import StableDiffusionPipeline
#import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup

from prettytable import PrettyTable
from handlers.calendar_client import obj
from msg.main_msg import *





#-------------------------------------------------------CLIENT-------------------------------------------
# /пользователи
async def get_clients_command_list(message: types.Message):
    await message.reply('Какие комманды для пользователей хочешь ввести?',
        reply_markup= kb_admin.kb_clients_commands)


#-------------------------------------------------------VIEW ALL USERS-------------------------------------------
class FSM_Admin_get_info_user(StatesGroup):
    user_name = State()


# /посмотреть_всех_пользователей
async def get_users_info_command(message: types.Message):
    if message.text.lower() == 'посмотреть всех пользователей' and \
        str(message.from_user.username) in ADMIN_NAMES:
        users_names = await get_info_many_from_table('clients')
        i = 0
        if users_names != [] and users_names is not None:
            for user in users_names: # выводим наименования клиентов
                user = list(user)
                i += 1
                tattoo_orders = await get_info_many_from_table('tattoo_orders', 'username', user[0]) 
                giftbox_orders = await get_info_many_from_table('giftbox_orders', 'username', user[0])
                cert_orders = await get_info_many_from_table('сert_orders', 'username', user[0])
                t_orders, c_orders, g_orders, t_active_orders, \
                    c_active_orders, g_active_orders = '', '', '', '', '', ''
                if tattoo_orders != []:
                    for order in tattoo_orders:
                        t_orders += f'{order[9]}, '
                        if 'открытый' in str(order[8]).lower():
                            t_active_orders += f'{order[9]}, '
                else:
                    t_orders = 'Нет тату заказов  '
                    t_active_orders = 'Нет открытых тату заказов  '
                
                if giftbox_orders != []:
                    try:
                        for order in giftbox_orders:
                            g_orders += f'{order[1]}, '
                            if 'открытый' in order[4].lower():
                                g_active_orders += f'{order[1]}, '
                    except:
                        g_orders = 'Нет гифтбокс заказов  '
                        g_active_orders = 'Нет открытых гифтбокс заказов  '
                else:
                    g_orders = 'Нет гифтбокс заказов  '
                    g_active_orders = 'Нет открытых гифтбокс заказов  '
                    
                if cert_orders != []:
                    try:
                        for order in cert_orders:
                            c_orders += f'{order[5]}, '
                            if 'открытый' in str(order[2]).lower():
                                c_active_orders += f'{order[5]}, '
                    except:
                        c_orders = 'Нет заказанных сертификатов  '
                        c_active_orders = 'Нет открытых заказанных сертификатов  '
                else:
                    c_orders = 'Нет заказанных сертификатов  '
                    c_active_orders = 'Нет открытых заказанных сертификатов  '
                    
                if t_active_orders == '':
                    t_active_orders = 'Нет открытых тату заказов  '
                if g_active_orders == '':
                    g_active_orders = 'Нет открытых гифтбокс заказов  '
                if c_active_orders == '':
                    c_active_orders = 'Нет открытых заказанных сертификатов  '
                
                
                await message.reply(f'Имя пользователя: {user[0]}\n'\
                    f'Телеграм: {user[1]}\n'\
                    f'Телефон: {user[2]}\n'\
                    '-----------------------------------------------------------\n'\
                    f'Номера заказов тату: {t_orders[:len(t_orders)-2]}\n'\
                    f'Номера заказов гифтбокс: {g_orders[:len(g_orders)-2]}\n'\
                    f'Номера заказов сертификата: {c_orders[:len(c_orders)-2]}\n'
                    '-----------------------------------------------------------\n'\
                    f'Номера открытых заказов тату: {t_active_orders[:len(t_active_orders)-2]}\n'
                    f'Номера открытых заказов гифтбокс: {g_active_orders[:len(g_active_orders)-2]}\n'
                    f'Номера открытых заказов сертификата: {c_active_orders[:len(c_active_orders)-2]}\n'
                    '-----------------------------------------------------------\n',
                    reply_markup=kb_admin.kb_main)
        else:
            await message.reply(f'Сейчас нет пользователей в базе')


#-------------------------------------------------------VIEW CLIENT-------------------------------------------
# /посмотреть_пользователя
async def get_user_info_command(message: types.Message):
    if message.text.lower() == 'посмотреть пользователя' and \
        str(message.from_user.username) in ADMIN_NAMES:
        users_names = await get_info_many_from_table('clients')
        if users_names != []:
            kb_users_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for ret in users_names:
                kb_users_names.add(KeyboardButton(ret[0])) # выводим наименования клиентов
            await FSM_Admin_get_info_user.user_name.set()
            await message.reply('Какого пользователя хочешь посмотреть?', reply_markup=kb_users_names)
        else:
            await message.reply('Прости, но у тебя пока нет пользователей в таблице')


async def get_user_info_command_with_name(message: types.Message, state: FSMContext):
    user = await get_info_many_from_table('clients', 'username', message.text)
    if user != [] and user is not None:
        tattoo_orders = await get_info_many_from_table('tattoo_orders', 'username', message.text)
        giftbox_orders = await get_info_many_from_table('giftbox_orders', 'username', message.text)
        cert_orders = await get_info_many_from_table('сert_orders', 'username', message.text)
        t_orders, c_orders, g_orders, t_active_orders, \
            c_active_orders, g_active_orders = '', '', '', '', '', ''
        if tattoo_orders != []:
            for order in tattoo_orders:
                t_orders += f'{order[9]}, '
                if 'активный' in str(order[8]).lower():
                    t_active_orders += f'{order[9]}, '
        else:
            t_orders = 'Нет тату заказов  '
            t_active_orders = 'Нет открытых тату заказов  '
        
        if giftbox_orders != []:
            try:
                for order in giftbox_orders:
                    g_orders += f'{order[1]}, '
                    if 'активный' in str(order[4]).lower():
                        g_active_orders += f'{order[1]}, '
            except:
                g_orders = 'Нет гифтбокс заказов  '
                g_active_orders = 'Нет открытых гифтбокс заказов  '
        else:
            g_orders = 'Нет гифтбокс заказов  '
            g_active_orders = 'Нет открытых гифтбокс заказов  '
            
        if cert_orders != []:
            try:
                for order in cert_orders:
                    c_orders += f'{order[5]}, '
                    if 'активный' in str(order[2]).lower():
                        c_active_orders += f'{order[5]}, '
            except:
                c_orders = 'Нет заказанных сертификатов  '
                c_active_orders = 'Нет открытых заказанных сертификатов  '
        else:
            c_orders = 'Нет заказанных сертификатов  '
            c_active_orders = 'Нет открытых заказанных сертификатов  '
            
        if t_active_orders == '':
            t_active_orders = 'Нет открытых тату заказов  '
        if g_active_orders == '':
            g_active_orders = 'Нет открытых гифтбокс заказов  '
        if c_active_orders == '':
            c_active_orders = 'Нет открытых заказанных сертификатов  '
        
        user = user[0]
        await message.reply(f'Имя пользователя: {user[0]}\n'\
            f'Телеграм: {user[1]}\n'\
            f'Телефон: {user[2]}\n'\
            '-----------------------------------------------------------\n'\
            f'Номера заказов тату: {t_orders[:len(t_orders)-2]}\n'\
            f'Номера заказов гифтбокс: {g_orders[:len(g_orders)-2]}\n'\
            f'Номера заказов сертификата: {c_orders[:len(c_orders)-2]}\n'
            '-----------------------------------------------------------\n'\
            f'Номера открытых заказов тату: {t_active_orders[:len(t_active_orders)-2]}\n'
            f'Номера открытых заказов гифтбокс: {g_active_orders[:len(g_active_orders)-2]}\n'
            f'Номера открытых заказов сертификата: {c_active_orders[:len(c_active_orders)-2]}\n'
            '-----------------------------------------------------------\n',
            reply_markup= kb_admin.kb_main)
        await state.finish()
    else:
        await message.reply(f'Пользователя с именем {message.text} нет. Попробуй другого')


#---------------------------------DELETE CLIENT-------------------------------------
class FSM_Admin_delete_info_user(StatesGroup):
    user_name = State()
    
# /удалить_пользователя
async def delete_username_command(message: types.Message):
    if message.text.lower() == 'удалить пользователя' and str(message.from_user.username) in ADMIN_NAMES:
        users_names = await get_info_many_from_table('clients')
        if users_names == []:
            await message.reply('У тебя пока нет пользователей в базе. Чего еще хочешь сделать?',
                reply_markup= kb_admin.kb_main)
        else:
            kb_users_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for ret in users_names:
                kb_users_names.add(KeyboardButton(ret[0])) # выводим наименования пользователей
            await FSM_Admin_delete_info_user.user_name.set()
            
            await message.reply('Какого пользователя хочешь удалить?', reply_markup=kb_users_names)


async def delete_user_with_name(message: types.Message, state: FSMContext):
    await delete_info('clients', 'username',  message.text)
    await message.reply(f'Готово! Вы удалили пользователя {message.text}',
        reply_markup= kb_admin.kb_main)
    await state.finish()


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