from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from msg.main_msg import *
from keyboards import kb_client, kb_admin
from handlers.other import *

from validate import check_pdf_document_payment, check_photo_payment
from handlers.calendar_client import obj

from db.db_setter import set_to_table
from db.db_updater import update_info
from db.db_getter import get_info_many_from_table, DB_NAME, sqlite3

from datetime import datetime


# 📷 ⏱ 🛠 ⚙️ 📎 ❤️ ☎️ 🗓 💬 🕒 🔴 🟢 🟡 ⁉️‼️ ❓❕❌
# ⭕️ 🛑 ⛔️ 🌿 ☘️ 🍀 🌴 🍃 🕸 💳 🎉 🎁 📃 🎫 📏 📜 🏷


#-------------------------------------Pay order----------------------------------------
class FSM_Client_paid_order(StatesGroup):
    order_name = State() 
    order_check_document = State()


async def command_get_payment_order_choice(message: types.Message):
    if message.text.lower() in ['оплатить заказ 💳', '/pay_for_the_order']:
        await bot.send_message(message.from_id, "❔ Какие заказы хочешь оплатить?",
            reply_markup= kb_client.kb_choice_order_type_to_payloading)
        # await FSM_Client_paid_order.order_name.set()


async def send_to_view_tattoo_orders(orders):
    kb_unpaid_orders = ReplyKeyboardMarkup(resize_keyboard=True)
    unpaid_orders_bool = False
    orders_str = 'Заказы:\n'
    for ret in orders:
        creation_date = ret[10].split('.')[0].split()[0]
        orders_str += \
            f'🕸 Тату заказ № {ret[9]} от {creation_date}\n'\
            f'🕒 Дата и время встречи: {ret[4]} {ret[5]}\n'\
            f'📜 Наименования тату: {ret[1]}\n'\
            f'📏 Размер: {ret[3]}\n'\
            f'🍃 Описание тату: {ret[6]}\n' \
            f'💬 Описание заказа: {ret[7]}\n'\
            f'📃 Состояние заказа: {ret[8]}\n'

        ''' 
        if ret[12] in ['Чек не добавлен', 'Без чека']:
            orders_str += '⛔️ Чек не добавлен\n\n'
        else:
            orders_str += '🍀 Чек добавлен\n\n' '''
        
        if ret[8] == OPEN_STATE_DICT["open"]:
            unpaid_orders_bool = True
            msg_answer_str = f'Тату заказ № {ret[9]} на {ret[4]} {ret[5]} от {creation_date} 🕸'
            kb_unpaid_orders.add(KeyboardButton(msg_answer_str))
            
    kb_unpaid_orders.add(KeyboardButton(kb_client.back_lst[0]))
    return kb_unpaid_orders, orders_str, unpaid_orders_bool


async def send_to_view_tattoo_sketch_orders(orders):
    kb_unpaid_orders = ReplyKeyboardMarkup(resize_keyboard=True)
    unpaid_orders_bool = False
    orders_str = 'Заказы:\n'
    for ret in orders:
        creation_date = ret[10].split('.')[0].split()[0]
    
    orders_str += '\nВаши заказанные эскизы:\n'
    for ret in orders:
        creation_date = ret[4].split('.')[0].split()[0]
        orders_str += \
            f'🕸 Эскиз № {ret[0]} от {creation_date}\n'\
            f'📜 Описание эскиза тату: {ret[1]}\n'\
            f'📃 Состояние заказа: {ret[5]}\n'

        ''' 
        if ret[6] in ['Чек не добавлен', 'Без чека']:
            orders_str += '⛔️ Чек не добавлен\n\n'
        else:
            orders_str += '🍀 Чек добавлен\n\n' '''
        
        if ret[8] == OPEN_STATE_DICT["open"]:
            unpaid_orders_bool = True
            kb_unpaid_orders.add(KeyboardButton(f'Эскиз заказ № {ret[0]} от {creation_date} 🎨'))
            
    kb_unpaid_orders.add(KeyboardButton(kb_client.back_lst[0]))
    return kb_unpaid_orders, orders_str, unpaid_orders_bool


async def send_to_view_cert_orders(orders):
    kb_unpaid_orders = ReplyKeyboardMarkup(resize_keyboard=True)
    unpaid_orders_bool = False
    orders_str = 'Заказы:\n'
    for ret in orders:
        orders_str += f'🎫 Заказ сертификата № {ret[5]}\n'\
            f'💰 Цена сертификата: {ret[1]}\n\n'
            
        if ret[2] == PAID_STATE_DICT["paid"]:
            orders_str += f'🏷 Код сертификата: {ret[3]}\n\n'
            
        else:
            unpaid_orders_bool = True
            kb_unpaid_orders.add(
                KeyboardButton(f'Сертификат {ret[5]} по цене {ret[1]} 🎫'))
            orders_str += '⛔️ Сертификат неоплачен\n'
            
    kb_unpaid_orders.add(KeyboardButton(kb_client.back_lst[0]))
    return kb_unpaid_orders, orders_str, unpaid_orders_bool


async def send_to_view_giftbox_orders(orders):
    orders_str = 'Заказы:\n'
    unpaid_orders_bool = False
    kb_unpaid_orders = ReplyKeyboardMarkup(resize_keyboard=True)
    for ret in orders:
        creation_date = ret[2].split('.')[0].split()[0]
        orders_str += f'🎁 Гифтбокс заказ № {ret[1]}\n'\
            f'💬 Описание заказа: {ret[0]}\n'\
            f'🕒 Дата открытия заказа: {ret[2]}\n'\
            f'📃 Состояние заказа: {ret[5]}\n\n'
            
        if ret[5] == OPEN_STATE_DICT["open"]:
            unpaid_orders_bool = True
            kb_unpaid_orders.add(KeyboardButton(
                f'Гифтбокс заказ № {ret[1]} от '\
                f'{creation_date} 🎁'))
            
    kb_unpaid_orders.add(KeyboardButton(kb_client.back_lst[0]))
    return kb_unpaid_orders, orders_str, unpaid_orders_bool


async def command_send_to_view_cert_orders_to_payloading(message: types.Message):
    orders = \
        await get_info_many_from_table("cert_orders", 'telegram', f'@{message.from_user.username}')
    
    if orders == []:
        await bot.send_message(message.from_id,  
            '⭕️ У тебя пока нет заказов эскизов для оплаты.\n\n'\
            '❔ Не хочешь ли оформить какой-нибудь заказ?',
                reply_markup= kb_client.kb_client_main)
        
    else:
        kb_unpaid_orders, orders_str, unpaid_orders_bool = await send_to_view_cert_orders(orders)
        
        if unpaid_orders_bool:
            await bot.send_message(message.from_id, f'📃 Твои заказы:\n {orders_str}',
                reply_markup= kb_unpaid_orders)
            await FSM_Client_paid_order.order_name.set()
            await bot.send_message(message.from_id, '❔ Какие заказы хочешь оплатить?')
        
        else:
            await bot.send_message(message.from_id,  
                f'📃 Твои тату заказы:\n {orders_str} \n\n'\
                f'🍀 У тебя все заказы оплачены! {MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_client.kb_client_main)


async def command_send_to_view_giftbox_orders_to_payloading(message: types.Message):
    orders = \
        await get_info_many_from_table("giftbox_orders", 'telegram', f'@{message.from_user.username}')
    
    if orders == []:
        await bot.send_message(message.from_id,  
            '⭕️ У тебя пока нет гифтбоксов для оплаты.\n\n'\
            '❔ Не хочешь ли оформить какой-нибудь заказ?',
                reply_markup= kb_client.kb_client_main)
        
    else:
        kb_unpaid_orders, orders_str, unpaid_orders_bool = await send_to_view_giftbox_orders(orders)
        
        if unpaid_orders_bool:
            await bot.send_message(message.from_id, f'📃 Твои заказы:\n {orders_str}',
                reply_markup= kb_unpaid_orders)
            await FSM_Client_paid_order.order_name.set()
            await bot.send_message(message.from_id, '❔ Какие заказы хочешь оплатить?')
            
        else:
            await bot.send_message(message.from_id,  
                f'📃 Твои тату заказы:\n {orders_str} \n\n'\
                f'🍀 У тебя все заказы оплачены! {MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_client.kb_client_main)


async def command_send_to_view_tattoo_sketch_orders_to_payloading(message: types.Message):
    orders = \
        await get_info_many_from_table("tattoo_sketch_orders", 'telegram', f'@{message.from_user.username}')
    
    if orders == []:
        await bot.send_message(message.from_id,  
            '⭕️ У тебя пока нет заказов эскизов для оплаты.\n\n'\
            '❔ Не хочешь ли оформить какой-нибудь заказ?',
                reply_markup= kb_client.kb_client_main)
        
    else:
        kb_unpaid_orders, orders_str, unpaid_orders_bool = await send_to_view_tattoo_sketch_orders(orders)
        
        if unpaid_orders_bool:
            await bot.send_message(message.from_id, f'📃 Твои заказы:\n {orders_str}',
                reply_markup= kb_unpaid_orders)
            await FSM_Client_paid_order.order_name.set()
            await bot.send_message(message.from_id, '❔ Какие заказы хочешь оплатить?')
            
        else:
            await bot.send_message(message.from_id,  
                f'📃 Твои тату заказы:\n {orders_str} \n\n'\
                f'🍀 У тебя все заказы оплачены! {MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_client.kb_client_main)


async def command_send_to_view_tattoo_orders_to_payloading(message: types.Message):
    orders = \
        await get_info_many_from_table("tattoo_orders", 'telegram', f'@{message.from_user.username}')
    
    if orders == []:
        await bot.send_message(message.from_id,  
            '⭕️ У тебя пока нет тату заказов для оплаты.\n\n'\
            '❔ Не хочешь ли оформить какой-нибудь заказ?',
                reply_markup= kb_client.kb_client_main)
        
    else:
        kb_unpaid_orders, orders_str, unpaid_orders_bool = await send_to_view_tattoo_orders(orders)
                
        if unpaid_orders_bool:
            await bot.send_message(message.from_id, f'📃 Твои заказы:\n {orders_str}',
                reply_markup= kb_unpaid_orders)
            await FSM_Client_paid_order.order_name.set()
            await bot.send_message(message.from_id, '❔ Какие заказы хочешь оплатить?')
        else:
            await bot.send_message(message.from_id,  
                f'📃 Твои тату заказы:\n {orders_str} \n\n'\
                f'🍀 У тебя все заказы оплачены! {MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_client.kb_client_main)


async def get_order_name_for_paid(message: types.Message, state=FSMContext):
    if not any(text in message.text for text in LIST_BACK_COMMANDS+LIST_CANCEL_COMMANDS):
        msg = message.text.split()
        price, order_id = '', ''
        async with state.proxy() as data: # type: ignore
            data['order_type'] = msg[0]
            if msg[0] == 'Тату':
                order_id = msg[3]
                data['order_id'] = msg[3]
                order = await get_info_many_from_table('tattoo_orders', 'tattoo_order_number', msg[3])
                price = list(order[0])[11]
                
            elif msg[0] == 'Гифтбокс': 
                order_id = msg[3]
                data['order_id']  = msg[3]
                order = await get_info_many_from_table('giftbox_orders', 'order_number', msg[3])
                price = list(order[0])[6]
                
            elif msg[0] == 'Сертификат': 
                order_id = msg[1]
                data['order_id'] = msg[1]
                price = msg[4] + ' ' + msg[5]
            
            elif msg[0] == 'Эскиз': 
                order_id = msg[1]
                data['order_id'] = msg[1]
                price = msg[4] + ' ' + msg[5]
                
            data['price'] = price
        
        await FSM_Client_paid_order.next()
        await bot.send_message(message.from_id,  
            f'🧾 Хорошо, ты выбрал заказ № {order_id}\n\n'\
            f'Пожалуйста, добавь файл или фотографию чека о переводе на сумму {price}',
            reply_markup= kb_client.kb_back_cancel)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS):
        await state.finish() # type: ignore
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup= kb_client.kb_client_main)


async def get_order_check_document_for_paid(message: types.Message, state=FSMContext):
    try:
        if message.text in LIST_BACK_COMMANDS:
            await FSM_Client_paid_order.previous()
            # TODO доделать кнопку Назад
            async with state.proxy() as data: # type: ignore
                order_type = data['order_type']
                
            orders = get_info_many_from_table(order_type, 'telegram', f'@{message.from_user.username}')
            #! TODO проверить правильность заполнения view_dict
            view_dict = {
                "tattoo_orders": send_to_view_tattoo_orders,
                "tattoo_sketch_orders": send_to_view_tattoo_sketch_orders,
                "giftbox_orders": send_to_view_giftbox_orders,
                "cert_orders": send_to_view_cert_orders
            }
            kb_unpaid_orders, orders_str, unpaid_orders_bool = await view_dict[order_type](orders)
            
            await bot.send_message(message.from_id, f'📃 Твои заказы:\n {orders_str}',
                reply_markup= kb_unpaid_orders)
            
            await bot.send_message(message.from_id, '❔ Какие заказы хочешь оплатить?')
            
        elif message.text in LIST_CANCEL_COMMANDS:
            await state.finish() # type: ignore
            await bot.send_message(message.from_id,  MSG_CANCEL_ACTION + MSG_BACK_TO_HOME,
                reply_markup= kb_client.kb_client_main)
            
        else:
            async with state.proxy() as data:  # type: ignore
                order_type = data['order_type']
                order_id = data['order_id']
                
            order_type_set = {  #table name, id number, price number, order number
                "Тату":         ["tattoo_orders", 9, 11, "tattoo_order_number"], 
                "Гифтбокс":     ["giftbox_orders", 1, 6, "order_number"],
                "Сертификат":   ["сert_orders", 5, 1, "cert_order_number"],
                "Эскиз":        ["tattoo_sketch_order"], # TODO доделать оплату эскзиза
            }        
            check_doc = {}
            order = await get_info_many_from_table( 
                order_type_set[order_type][0],
                order_type_set[order_type][3],
                order_id 
            )
            price = order[0][ order_type_set[order_type][2] ]
            doc_name = order_id
            
            if message.content_type == "document":
                # print("message.document.file_name: ", message.document.file_name)
                check_doc = await check_pdf_document_payment(
                    message.from_id, 
                    price,
                    doc_name,
                    message.document.file_id
                ) 
            elif message.content_type == "photo":
                # print("message.photo img:", message.photo[0])
                
                doc_name += '.jpg'
                check_doc = await check_photo_payment(
                    message,
                    message.from_id,
                    price,
                    doc_name,
                    message.photo[0].file_id
                )
            
            
            if check_doc["result"]:
                check_document_successful_download = ''
                if '.jpg' not in doc_name:
                    check_document_successful_download = message.document.file_id
                else:
                    check_document_successful_download = message.photo[0].file_id
                    
                await update_info(
                    order_type_set[order_type][0], # table name
                    order_type_set[order_type][3], # column name of order number
                    order_id,                      # column value - order id
                    "order_state",
                    PAID_STATE_DICT["paid"]
                )
                
                await update_info(
                    order_type_set[order_type][0], # table name
                    order_type_set[order_type][3], # column name of order number
                    order_id,                      # column value - order id
                    "check_document",
                    check_document_successful_download
                )
                
                await bot.send_message(message.from_id,  
                    f'🎉 Отлично, вы оплатили заказ № {order_id}! \n\n'\
                    '❔ Хотите сделать что-то еще?',
                    reply_markup= kb_client.kb_client_main)
                await state.finish() # type: ignore
                
            else:
                await bot.send_message(message.from_id, check_doc["report_msg"]) # type: ignore
                
    except Exception as ex:
        print("Exception: ", ex)


def register_handlers_client_payload(dp: Dispatcher):
#--------------------------Pay order-------------------------
    dp.register_message_handler( command_get_payment_order_choice,
        Text(equals= kb_client.client_main['payload_order'], ignore_case=True), state= None)
    dp.register_message_handler( command_get_payment_order_choice, 
        commands='pay_for_the_order', state= None)
    
    dp.register_message_handler(command_send_to_view_tattoo_sketch_orders_to_payloading,
        Text(equals= kb_client.choice_order_type_to_payloading["tattoo_sketch_orders"], ignore_case=True),
        state= None)

    dp.register_message_handler(command_send_to_view_tattoo_orders_to_payloading,
        Text(equals= kb_client.choice_order_type_to_payloading["tattoo_orders"], ignore_case=True),
        state= None)
    dp.register_message_handler(command_send_to_view_giftbox_orders_to_payloading,
        Text(equals= kb_client.choice_order_type_to_payloading["giftbox_orders"], ignore_case=True),
        state= None)
    
    dp.register_message_handler(command_send_to_view_cert_orders_to_payloading,
        Text(equals= kb_client.choice_order_type_to_payloading["cert_orders"], ignore_case=True),
        state= None)
    
    dp.register_message_handler( get_order_name_for_paid,
        state= FSM_Client_paid_order.order_name)
    dp.register_message_handler(
        get_order_check_document_for_paid,
        Text(equals=[kb_client.cancel_lst[0], kb_client.back_lst[0]], ignore_case= True), 
        state= FSM_Client_paid_order.order_check_document)
    
    dp.register_message_handler( get_order_check_document_for_paid,
        content_types=['photo', 'document', 'message'], 
        state= FSM_Client_paid_order.order_check_document)
        