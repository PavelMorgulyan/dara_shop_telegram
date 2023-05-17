
from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from msg.main_msg import *
from keyboards import kb_client, kb_admin
from handlers.other import generate_random_code, generate_random_order_number, CLOSED_STATE_DICT
from handlers.client import CODE_LENTH, ORDER_CODE_LENTH, fill_client_table, \
    DARA_ID, FSM_Client_username_info, CALENDAR_ID
from handlers.calendar_client import obj


from db.db_setter import set_to_table
from db.db_updater import update_info
from db.db_getter import get_info_many_from_table, DB_NAME, sqlite3

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *
from datetime import datetime

'''
    Статусы заказа:
    Открыт — заказ был создан в базе данных, но ещё не был обработан.
    Обработан — оплата была получена.
    Выполнен — вся работа по заказу завершена.
    Отклонен — заказ отклонен админом.
    Отложен — заказ ещё не обработан, так как в нём содержатся товары, которых нет в наличии. 
        Только для гифтбокса
    Аннулирован — заказ был отменён покупателем.
    Ожидает ответа — заказ был создан, когда покупатель оформил заявку на обратный ответ.
'''


#-----------------------------------------CREATE TATTOO SKETCH ORDER-------------------------------
# Хочу эскиз тату
class FSM_Client_tattoo_sketch_order(StatesGroup):
    tattoo_sketch_note = State()
    load_sketch_photo = State()


# Начало диалога с пользователем, который хочет добавить новый заказ тату, хочу тату 🕸
async def start_create_new_tattoo_sketch_order(message: types.Message):
    await FSM_Client_tattoo_sketch_order.tattoo_sketch_note.set()
    await bot.send_message(message.from_id,  
        '🕸 Отлично, давай сделаем тебе эскиз! \n\n'\
        f'{MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT_CONCEPTS}',
        reply_markup = kb_client.kb_start_dialog_sketch_order
    )


async def fill_sketch_order_table(data:dict, message: types.Message):
    new_user = False
    with Session(engine) as session:
        new_tattoo_sketch_photo = SketchPhoto(
            tattoo_sketch_order_number = data["tattoo_sketch_order_number"],
            telegram_user_id = message.from_id,
            photo = data['photo']
        )
        user = session.scalars(select(User).where(
            User.telegram_id == message.from_id)).one()
        
        if user == []:
            new_user = User(
                name=message.from_user.full_name,
                telegram_name = f'@{message.from_user.username}',
                telegram_id= message.from_id,
                phone= '-'
            )
            session.add(new_user)
            session.commit()
            new_user = True
                
        new_tattoo_sketch_check_doc = CheckDocument(
            order_number= data["tattoo_sketch_order_number"],
            telegram_user_id= message.from_id,
            doc= data['check_document']
        )
        
        new_tattoo_sketch_order = Orders(
            desc= data['sketch_description'],
            photo= [new_tattoo_sketch_photo],
            user= message.from_id, 
            creation_time= data['creation_time'],
            telegram_user_id = message.from_id,
            order_state= data['state'],
            check_document= [new_tattoo_sketch_check_doc],
            price= data['price']
        )
        session.add_all([new_tattoo_sketch_photo, new_tattoo_sketch_check_doc, new_tattoo_sketch_order])
        session.commit()
        
    date = data['creation_time'] 
    start_time = f'{date.strftime("%Y-%m-%dT%H:%M")}'
    
    if DARA_ID != 0:
        await bot.send_message(DARA_ID, f'Дорогая Тату-мастерица! '\
        f"🕸 Поступил новый заказ на эскиз под номером {data['tattoo_sketch_order_number']}!")
    
    event = await obj.add_event(CALENDAR_ID,
        f"Новый эскиз заказ № " +   data['tattoo_sketch_order_number'],
        'Описание тату: ' +         data['sketch_description'] + ' \n' + \
        f'Имя клиента:@{message.from_user.username}',
        start_time, # '2023-02-02T09:07:00',
        start_time    # '2023-02-03T17:07:00'
    )
    
    await bot.send_message(message.from_id,  
        '🎉 Отлично, заказ на эскиз оформлен! '\
        f"Номер твоего заказа эскиза {data['tattoo_sketch_order_number']}\n\n"\
        f"❕Оплата эскиза осуществляется только после того, как Дара подтвердит заказ. '\
        'К тебе придет уведомление через бота о том, что заказ подтвержден и готов к оплате.\n\n'\
        '💬 Скоро Дара свяжется с тобой!\n\n"
    )
    if new_user:
        await bot.send_message(message.chat.id, MSG_TO_CHOICE_CLIENT_PHONE, reply_markup= kb_client.kb_phone_number)
        await FSM_Client_username_info.phone.set()
    else:
        await bot.send_message(message.from_id,  
            f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup = kb_client.kb_client_main)


async def get_sketch_desc_order(message: types.Message, state: FSMContext):
    tattoo_sketch_order_number = await generate_random_order_number(CODE_LENTH)
    async with state.proxy() as data:
        data['tattoo_sketch_order_number'] = tattoo_sketch_order_number
        data['sketch_order_photo_counter'] = 0
        data['sketch_photo'] = ''
        data['telegram_user_id'] = message.from_id
        
    if message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup= kb_client.kb_client_main)
        
    elif message.text in LIST_BACK_COMMANDS:
            await bot.send_message(message.from_id,  
                f'{MSG_CLIENT_GO_BACK}{MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT_CONCEPTS}', 
                reply_markup= kb_client.kb_start_dialog_sketch_order)
            
    elif message.text == kb_client.start_dialog_sketch_order['client_want_to_see_galery']:
        tattoo_items = await get_info_many_from_table('tattoo_items', 'creator', 'admin')
        await bot.send_message(message.from_id, '📃 Вот мои эскизы для тату')
        for tattoo in tattoo_items:
            tattoo = list(tattoo) #? TODO нужно ли выводить размер и цену?
            msg = f'📃 Название: {tattoo[0]}\n🎨 Цвет: {tattoo[3]}\n'
                #\f'🔧 Количество деталей: {tattoo[5]}\n'
                
            if tattoo[4].lower() != 'без описания':
                msg += f'💬 Описание: {tattoo[4]}\n' #💰 Цена: {tattoo[2]}\n'
            
            await bot.send_photo(message.from_user.id, tattoo[1] , msg)
            
        await bot.send_message(message.from_user.id,'❔ Какое описание хочешь оставить для своего эскиза?')
    
    # переход: Хочешь отправить фото твоей идеи для переводной татуировки?' -> Да
    elif message.text == kb_client.yes_str:
        await FSM_Client_tattoo_sketch_order.next() # -> load_sketch_photo
        await bot.send_message(message.from_id, '📎 Хорошо, отправь фото твоей идеи для эскиза тату!',
            reply_markup= kb_client.kb_back_cancel)
        
    # переход: Хочешь отправить фото твоей идеи для переводной татуировки?' -> Нет
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            new_sketch_order = {
                'tattoo_sketch_order_number':   tattoo_sketch_order_number,
                'sketch_description':       data['sketch_description'],
                'photo_lst':                '-',
                'creation_time':            datetime.now(),
                'state':                    'Открыт',
                'check_document':           '-',
                'price':                    '-'
            }
            await fill_sketch_order_table(new_sketch_order, message)
        await state.finish()
    
    else:
        async with state.proxy() as data:
            data['telegram'] = f'@{message.from_user.username}'
            data['sketch_description'] = message.text
        
        await bot.send_message(message.from_id,  
            '❔ Хочешь отправить фото твоей идеи для переводной татуировки?', 
            reply_markup= kb_client.kb_yes_no)


async def get_photo_sketch_order(message: types.Message, state: FSMContext):
    if message.content_type == 'text':
        if message.text in LIST_BACK_COMMANDS:
            await FSM_Client_tattoo_sketch_order.previous() # -> get_sketch_desc_order
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}'\
                '❔ Хочешь отправить фото твоей идеи для переводной татуировки?', 
                reply_markup= kb_client.kb_yes_no)
            
        elif message.text in LIST_CANCEL_COMMANDS:
            await state.finish()
            await bot.send_message(message.from_id,  MSG_BACK_TO_HOME, reply_markup = kb_client.kb_client_main)
            
        elif message.text == kb_client.client_choice_send_more_photo_to_skatch_order['more_photo']:
            async with state.proxy() as data:
                data['sketch_order_photo_counter'] = 0
            await bot.send_message(message.from_id, '📎 Хорошо, отправь еще фотографии твоей идеи!')
            
        elif message.text == kb_client.client_choice_send_more_photo_to_skatch_order['end_order']:
            async with state.proxy() as data:
                new_sketch_order = {
                    'tattoo_sketch_order_number':   data['tattoo_sketch_order_number'],
                    'sketch_description':           data['sketch_description'],
                    'photo_lst':                    data['sketch_photo'], 
                    'creation_time':                datetime.now(),
                    'state':                        'Открыт',
                    'check_document':               '-',
                    'price':                        '-',
                }
            await fill_sketch_order_table(new_sketch_order, message)
            await state.finish()
            
    elif message.content_type == 'photo':
        async with state.proxy() as data:
            data['sketch_photo'] += f'{message.photo[0].file_id}|'
            
            sketch_order_photo_counter = data['sketch_order_photo_counter']
            data['sketch_order_photo_counter'] = message.media_group_id
        
        if sketch_order_photo_counter != data['sketch_order_photo_counter']:
            
            await bot.send_message(message.from_id, 
                '❔ Хочешь отправить еще фотографии или завершить заказ эскиза?',
                reply_markup= kb_client.kb_client_choice_send_more_photo_to_skatch_order)


# Посмотреть мои заказы эскизов 🎨
async def get_clients_tattoo_sketch_order(message: types.Message):
    orders = Session(engine).scalars(select(TattooSketchOrders).where(TattooSketchOrders.telegram_user_id == message.from_id))
    if orders == []:
        await bot.send_message(message.from_id,  
            f'⭕️ У тебя пока нет заказов для эскизов.\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_client.kb_choice_order_view)
    else:
        for order in orders:
            creation_date = order.creation_time.split('.')[0]
            message_to_send = f'Заказ № {order.sketch_order_number} от {creation_date}\n'\
                f'📜 Описание тату эскиза: {order.desc}\n'
            
            if any(str(order_state) in order[5] for order_state in list(CLOSED_STATE_DICT.values())):
                message_to_send += f'❌ Состояние заказа: {order.order_state}\n'
            else:
                message_to_send += f'📃 Состояние заказа: {order.order_state}\n'
                
            if '|' in order.photo:
                photos = order[2].split('|')
                await bot.send_photo(message.from_user.id, photos, message_to_send)
                
            elif '-' not in order[2]:
                await bot.send_photo(message.from_user.id, order[2], message_to_send)
            else:
                message_to_send += '⭕️ \n'
                await bot.send_message(message.from_user.id, message_to_send)
            
        await bot.send_message(message.from_user.id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_client.kb_choice_order_view)


class FSM_Client_get_new_photo_to_sketch_order(StatesGroup):
    get_order_id = State() 
    get_new_photo = State()


async def command_client_add_new_photo_to_sketch_order(message: types.Message):
    sqlite_connection = sqlite3.connect(DB_NAME)
    cursor = sqlite_connection.cursor()
    
    # TODO выставить нормальные статусы
    closed_state_str = ', '.join([f'{key.capitalize()}: {value}' for key, value in \
        CLOSED_STATE_DICT.items()])
    
    sqlite_select_query = \
        f"""SELECT * from tattoo_sketch_orders WHERE \'state\' not in ({closed_state_str})
            and telegram = \'@{message.from_user.username}\'"""
            
    cursor.execute(sqlite_select_query)
    orders = cursor.fetchall()
    sqlite_connection.close()
    if orders == []:
        await bot.send_message(message.from_id,  
            f'⭕️ У тебя пока нет заказанных эскизов.\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_client.kb_choice_order_view)
    else:
        kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
        for ret in orders:
            creation_date = ret[4].split('.')[0]
            kb_orders.add(f'Эскиз заказ № {ret[0]} от {creation_date}')
        kb_orders.add(kb_client.back_lst[0]).add(kb_client.cancel_lst[0])
        await FSM_Client_get_new_photo_to_sketch_order.get_order_id.set()
        await bot.send_message(message.from_id, '❔ Для какого заказа хочешь добавить фотографию?',
            reply_markup= kb_orders)


async def get_order_id_to_add_new_photo_to_sketch_order(message: types.Message, state: FSMContext):
    orders = await get_info_many_from_table('tattoo_sketch_orders', 'telegram', f'@{message.from_user.username}')
    kb_orders_lst = []
    photo_list = ''
    for ret in orders:
        creation_date = ret[4].split('.')[0]
        kb_orders_lst.append(f'Эскиз заказ № {ret[0]} от {creation_date}')
        photo_list = ret[2]
        
    if message.content_type == 'text':
        if message.text in kb_orders_lst:
            async with state.proxy() as data:
                data['sketch_order_number'] = message.text.split()[3]
                data['sketch_photo'] = photo_list
                data['sketch_order_photo_counter'] = 0 
                
            await FSM_Client_get_new_photo_to_sketch_order.next() # -> get_photo_to_sketch_order
            await bot.send_message(message.from_id, 
                MSG_CLIENT_LOAD_PHOTO,
                reply_markup= kb_client.kb_client_choice_add_photo_type)
            
        elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
            await state.finish()
            await bot.send_message(message.from_id, 
                f'{MSG_CANCEL_ACTION}{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
                reply_markup= kb_client.kb_choice_order_view)
        else:
            await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_photo_to_sketch_order(message: types.Message, state: FSMContext):
    if message.content_type == 'photo':
        async with state.proxy() as data:
            data['sketch_photo'] += f'{message.photo[0].file_id}|'
            sketch_order_photo_counter = data['sketch_order_photo_counter']
            data['sketch_order_photo_counter'] = message.media_group_id
            
        if sketch_order_photo_counter != data['sketch_order_photo_counter']:
            async with state.proxy() as data:
                sketch_order_photo_counter = data['sketch_order_photo_counter']
            
            await bot.send_message(message.from_id,  
                '📷 Отлично, ты выбрал(а) фотографию эскиза для своего тату!')
            await bot.send_message( message.from_id, '❔ Хочешь добавить еще фото/картинку?',
                reply_markup= kb_client.kb_yes_no)
            
    if message.content_type == 'text':
        if message.text == kb_client.yes_str:
            async with state.proxy() as data:
                data['sketch_order_photo_counter'] = 0 
                
            await bot.send_message( message.from_id, 
                '📎 Хорошо, отправь еще фотографию через файлы.', 
                reply_markup= kb_client.kb_back_cancel)
            
        elif message.text == kb_client.no_str:
            async with state.proxy() as data:
                sketch_photo = data['sketch_photo']
                sketch_order_number = data['sketch_order_number']
                
            await update_info('tattoo_sketch_orders', 'order_id', sketch_order_number, 'photo_lst', sketch_photo)
            await state.finish()
            await bot.send_message(message.from_id,
                f'🎉 Отлично, ты обновил фотографии в заказе {sketch_order_number}!\n\n'\
                f'{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
                reply_markup= kb_client.kb_choice_order_view)
            
        elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME):
            await state.finish()
            await bot.send_message(message.from_id, 
                f'{MSG_CANCEL_ACTION}{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
                reply_markup= kb_client.kb_choice_order_view)
            
        elif any(text in message.text.lower() for text in LIST_BACK_COMMANDS):
            await FSM_Client_get_new_photo_to_sketch_order.previous()
            
            sqlite_connection = sqlite3.connect(DB_NAME)
            cursor = sqlite_connection.cursor()
            
            closed_state_str = ', '.join([f'{key.capitalize()}: {value}' for key, value in \
                CLOSED_STATE_DICT.items()])
            #TODO выставит нормальные значения статусов 
            sqlite_select_query = \
                f"""SELECT * from tattoo_sketch_orders WHERE \'state\' not in ({closed_state_str}) \
                    and telegram = \'@{message.from_user.username}\'"""
            cursor.execute(sqlite_select_query)
            orders = cursor.fetchall()
            sqlite_connection.close()
            
            kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
            for ret in orders:
                creation_date = ret[4].split('.')[0]
                kb_orders.add(f'Эскиз заказ № {ret[0]} от {creation_date}')
            kb_orders.add(kb_client.back_lst[0]).add(kb_client.cancel_lst[0])
            
            await bot.send_message(message.from_id, '❔ Для какого заказа хочешь добавить фотографию?',
                reply_markup= kb_orders)
        else:
            await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


#-------------------------------------------SKETCH_TATTOO_ORDER----------------------------------
def register_handlers_client_sketch(dp: Dispatcher):
    dp.register_message_handler(start_create_new_tattoo_sketch_order,
        Text(equals= kb_client.client_main['client_want_tattoo_sketch'], ignore_case=True), state=None)
    dp.register_message_handler(start_create_new_tattoo_sketch_order,
        commands=['get_sketch_tattoo'], state=None)
    dp.register_message_handler(get_sketch_desc_order,
        state=FSM_Client_tattoo_sketch_order.tattoo_sketch_note)
    dp.register_message_handler(get_photo_sketch_order, content_types=['photo', 'text'],
        state=FSM_Client_tattoo_sketch_order.load_sketch_photo)
    
    dp.register_message_handler(get_clients_tattoo_sketch_order,
        Text(equals=kb_client.choice_order_view['client_watch_sketch_order'], ignore_case=True), state=None)
    
    dp.register_message_handler(command_client_add_new_photo_to_sketch_order,
        Text(equals=kb_client.choice_order_view['client_add_photo_to_sketch_order'], ignore_case=True), state=None)
    dp.register_message_handler(get_order_id_to_add_new_photo_to_sketch_order, 
        state= FSM_Client_get_new_photo_to_sketch_order.get_order_id)
    dp.register_message_handler(get_photo_to_sketch_order, content_types=['photo', 'text'], 
        state= FSM_Client_get_new_photo_to_sketch_order.get_new_photo)