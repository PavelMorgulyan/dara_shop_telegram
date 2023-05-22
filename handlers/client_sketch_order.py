
from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from msg.main_msg import *
from keyboards import kb_client, kb_admin
from handlers.other import generate_random_order_number, STATES
from handlers.client import CODE_LENTH, fill_client_table, \
    DARA_ID, FSM_Client_username_info, CALENDAR_ID
from handlers.calendar_client import obj


from sqlalchemy.orm import Session
from sqlalchemy import select
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
        user = session.scalars(select(User).where(User.telegram_id == message.from_id)).one()
        if user == []:
            user = User(
                name=           message.from_user.full_name,
                telegram_name=  f'@{message.from_user.username}',
                telegram_id=    message.from_id,
                phone=          None
            )
            session.add(user)
            session.commit()
            new_user = True

        new_tattoo_sketch_order = Orders(
            order_type=             'эскиз',
            order_name=             None,
            user_id=                message.from_id,
            order_photo=            data['photo_lst'],
            tattoo_size=            None,
            tattoo_note=            None,
            order_note=             data['sketch_description'],
            order_state=            data['state'],
            order_number=           data['tattoo_sketch_order_number'],
            price=                  data['price'],
            check_document=         data['check_document'],
            username=               message.from_user.full_name,
            schedule_id=            None,
            colored=                None,
            bodyplace=              None,
            tattoo_place_photo=     None,
            tattoo_place_video_note=None,
            tattoo_place_video=     None,
            code=                   None
        )
        session.add(new_tattoo_sketch_order)
        session.commit()
        
    date = data['creation_time'] 
    
    if DARA_ID != 0:
        await bot.send_message(DARA_ID, f'Дорогая Тату-мастерица! '\
        f"🕸 Поступил новый заказ на эскиз под номером {data['tattoo_sketch_order_number']}!")
    
    event = await obj.add_event(CALENDAR_ID,
        f"Новый эскиз заказ №{data['tattoo_sketch_order_number']}",
        f"Описание эскиза тату: {data['sketch_description']}\n" \
        f'Имя клиента:@{message.from_user.username}',
        f'{date.strftime("%Y-%m-%dT%H:%M")}', # '2023-02-02T09:07:00',
        f'{date.strftime("%Y-%m-%dT%H:%M")}'    # '2023-02-03T17:07:00'
    )
    
    await bot.send_message(message.from_id,  
        '🎉 Отлично, заказ на эскиз оформлен! '\
        f"Номер твоего заказа эскиза {data['tattoo_sketch_order_number']}")
    
    await bot.send_message(message.from_id,  
        f"❕Оплата эскиза осуществляется только после того, как Дара подтвердит заказ. '\
        'К тебе придет уведомление через бота о том, что заказ подтвержден и готов к оплате.\n'\
        '💬 Скоро Дара свяжется с тобой!\n\n"
    )
    if new_user:
        await bot.send_message(message.chat.id, MSG_TO_CHOICE_CLIENT_PHONE, 
            reply_markup= kb_client.kb_phone_number)
        await FSM_Client_username_info.phone.set()
    else:
        await bot.send_message(message.from_id, f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup = kb_client.kb_client_main)


async def get_sketch_desc_order(message: types.Message, state: FSMContext):
    tattoo_sketch_order_number = await generate_random_order_number(CODE_LENTH)
    async with state.proxy() as data:
        data['tattoo_sketch_order_number'] = tattoo_sketch_order_number
        data['sketch_order_photo_counter'] = 0
        data['sketch_photo'] = []
        
    if message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup= kb_client.kb_client_main)
        
    elif message.text in LIST_BACK_COMMANDS:
            await bot.send_message(message.from_id,  
                f'{MSG_CLIENT_GO_BACK}{MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT_CONCEPTS}', 
                reply_markup= kb_client.kb_start_dialog_sketch_order)
    
    # Посмотреть галерею 📃
    elif message.text == kb_client.start_dialog_sketch_order['client_want_to_see_galery']:
        with Session(engine) as session:
            tattoo_items = session.scalars(select(TattooItems).where(TattooItems.creator == 'admin')).all()
            
        await bot.send_message(message.from_id, '📃 Вот мои эскизы для тату')
        for tattoo in tattoo_items:
            #? TODO нужно ли выводить размер и цену?
            msg = f'📃 Название: {tattoo.name}\n🎨 Цвет: {tattoo.colored}\n'
                #\f'🔧 Количество деталей: {tattoo[5]}\n'
                
            if tattoo.note not in ['без описания', None]:
                msg += f'💬 Описание: {tattoo.note}\n' #💰 Цена: {tattoo.price}\n'
                
            with Session(engine) as session:
                photos = session.scalars(select(TattooItemPhoto).where(
                    TattooItemPhoto.tattoo_item_name == tattoo.name)).all()
            media = []
            for photo in photos:
                media.append(types.InputMediaPhoto(photo.photo, msg))
                
            await bot.send_media_group(message.from_user.id, media= media)
            
        await bot.send_message(message.from_user.id,'❔ Какое описание хочешь оставить для своего эскиза?')
    
    # переход: Хочешь отправить фото твоей идеи для переводной татуировки?' -> Да
    elif message.text == kb_client.yes_str:
        await FSM_Client_tattoo_sketch_order.next() # -> load_sketch_photo
        await bot.send_message(message.from_id, '📎 Хорошо, отправь фото твоей идеи для эскиза тату!',
            reply_markup= kb_client.kb_back_cancel)
        
    # переход: Хочешь отправить фото твоей идеи для переводной татуировки?' -> Нет
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            doc = [CheckDocument(doc=None, order_number= data['tattoo_sketch_order_number'])]
            new_sketch_order = {
                'tattoo_sketch_order_number':   tattoo_sketch_order_number,
                'sketch_description':           data['sketch_description'],
                'photo_lst':                    None,
                'creation_time':                datetime.now(),
                'state':                        STATES["open"],
                'check_document':               doc,
                'price':                        None,
            }
            await fill_sketch_order_table(new_sketch_order, message)
        await state.finish()
    
    else:
        async with state.proxy() as data:
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
                doc = [CheckDocument(doc=None, order_number= data['tattoo_sketch_order_number'])]
                new_sketch_order = {
                    'tattoo_sketch_order_number':   data['tattoo_sketch_order_number'],
                    'sketch_description':           data['sketch_description'],
                    'photo_lst':                    data['sketch_photo'], 
                    'creation_time':                datetime.now(),
                    'state':                        STATES["open"],
                    'check_document':               doc,
                    'price':                        None
                }
            await fill_sketch_order_table(new_sketch_order, message)
            await state.finish()
            
    elif message.content_type == 'photo':
        async with state.proxy() as data:
            data['sketch_photo'].append(
                OrderPhoto(
                    photo=              message.photo[0].file_id, 
                    order_number=       data['tattoo_sketch_order_number'],
                    telegram_user_id=   message.from_id)
                )
            
            sketch_order_photo_counter = data['sketch_order_photo_counter']
            data['sketch_order_photo_counter'] = message.media_group_id
        
        if sketch_order_photo_counter != data['sketch_order_photo_counter']:
            
            await bot.send_message(message.from_id, 
                '❔ Хочешь отправить еще фотографии или завершить заказ эскиза?',
                reply_markup= kb_client.kb_client_choice_send_more_photo_to_skatch_order)


# Посмотреть мои заказы эскизов 🎨
async def get_clients_tattoo_sketch_order(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(select(Orders).where(Orders.user_id == message.from_id)).all()
    if orders == []:
        await bot.send_message(message.from_id,  
            f'⭕️ У тебя пока нет заказов для эскизов.\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_client.kb_choice_order_view)
    else:
        for order in orders:
            creation_date = order.creation_date.split('.')[0]
            message_to_send = f'Заказ № {order.order_number} от {creation_date}\n'\
                f'📜 Описание тату эскиза: {order.order_note}\n'
            
            if any(str(order_state) in order[5] for order_state in list(STATES["closed"].values())):
                message_to_send += f'❌ Состояние заказа: {order.order_state}\n'
            else:
                message_to_send += f'📃 Состояние заказа: {order.order_state}\n'
                
            if '|' in order.order_photo:
                photos = order[2].split('|')
                await bot.send_photo(message.from_user.id, photos, message_to_send)
                
            elif '-' not in order[2]:
                await bot.send_photo(message.from_user.id, order.order_photo, message_to_send)
            else:
                message_to_send += '⭕️ \n'
                await bot.send_message(message.from_user.id, message_to_send)
            
        await bot.send_message(message.from_user.id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_client.kb_choice_order_view)


class FSM_Client_get_new_photo_to_sketch_order(StatesGroup):
    get_order_id = State() 
    get_new_photo = State()


async def command_client_add_new_photo_to_sketch_order(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(select(Orders).where(Orders.user_id == message.from_id).where(
            Orders.order_state.not_in(list(STATES["closed"].values())))).all()
    
    if orders == []:
        await bot.send_message(message.from_id, '⭕️ У тебя пока нет заказанных эскизов')
        await bot.send_message(message.from_id, f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_client.kb_choice_order_view)
    else:
        kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
        for order in orders:
            kb_orders.add(f"Эскиз заказ № {order.order_number} от {order.creation_date.split('.')[0]}")
        kb_orders.add(kb_client.back_lst[0]).add(kb_client.cancel_lst[0])
        await FSM_Client_get_new_photo_to_sketch_order.get_order_id.set()
        await bot.send_message(message.from_id, '❔ Для какого заказа хочешь добавить фотографию?',
            reply_markup= kb_orders)


async def get_order_id_to_add_new_photo_to_sketch_order(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(select(Orders).where(Orders.user_id == message.from_id)).all()
    kb_orders_lst = []
    photo_list = ''
    for order in orders:
        kb_orders_lst.append(f"Эскиз заказ № {order.order_number} от {order.creation_date.split('.')[0]}")
        photo_list = order.order_photo
        
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
            data['sketch_photo'].append(OrderPhoto(
                    photo=          message.photo[0].file_id,
                    order_number=   data['sketch_sketch_order_number'],
                    telegram_id=    message.from_id,
                )
            )                                   
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
                
            with Session(engine) as session:
                order = session.scalars(select(Orders).where(Orders.order_number == sketch_order_number)).one()
                order.order_photo = sketch_photo
                session.commit()
                
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
            
            with Session(engine) as session:
                orders = session.scalars(select(Orders).where(Orders.user_id == message.from_id).where(
                    Orders.order_state.not_in(list(STATES["closed"].values())))).all()
            
            kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
            for order in orders:
                kb_orders.add(f"Эскиз заказ № {order.order_number} от {order.creation_date.split('.')[0]}")
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