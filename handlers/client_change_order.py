from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from msg.main_msg import *
from keyboards import kb_client, kb_admin
from handlers.other import STATES, clients_status, get_key
from handlers.client import (
    CODE_LENTH,
    fill_client_table,
    DARA_ID,
    FSM_Client_username_info,
    CALENDAR_ID,
)
from handlers.calendar_client import obj

from sqlalchemy.orm import Session
from sqlalchemy import select
from db.sqlalchemy_base.db_classes import *
from datetime import datetime



class FSM_Client_client_change_order(StatesGroup):
    get_order_type = State()
    get_order_number = State()
    get_column_name_to_change = State()
    get_new_value = State()


# изменить заказы
async def get_command_client_change_order_menu(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(select(Orders).where(Orders.user_id == message.from_id)).all()
    
    if orders == []:
        await bot.send_message(message.from_id, f"{MSG_NO_ORDER_IN_TABLE}\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}")
    else:
        await FSM_Client_client_change_order.get_order_type.set()
        kb_orders = ReplyKeyboardMarkup(resize_keyboard= True)
        with Session(engine) as session:
            constant_tattoo_orders = session.scalars(select(Orders)
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]]))
                ).all()        

            shifting_tattoo_orders = session.scalars(select(Orders)
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["shifting_tattoo"]]))
                ).all()
            
            giftbox_orders = session.scalars(select(Orders)
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["giftbox"]]))
                ).all()
            
            sketch_orders = session.scalars(select(Orders)
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["sketch"]]))
                ).all()
        
        if constant_tattoo_orders != []:
            kb_orders.add(KeyboardButton(kb_client.order_change['constant_tattoo']))
        
        if shifting_tattoo_orders != []:
            kb_orders.add(KeyboardButton(kb_client.order_change['shifting_tattoo']))
        
        if giftbox_orders != []:
            kb_orders.add(KeyboardButton(kb_client.order_change['giftbox']))
        
        if sketch_orders != []:
            kb_orders.add(KeyboardButton(kb_client.order_change['sketch']))
        
        kb_orders.add(kb_admin.home_btn)
        
        await bot.send_message(
            message.from_id, 
            "❔ Какой заказ хотите дополнить или изменить?",
            reply_markup= kb_orders
        )


async def get_order_type(message: types.Message, state: FSMContext):
    
    if message.text in list(kb_client.order_change.values()):
        async with state.proxy() as data:
            data['order_type'] = kb_admin.price_lst_types[
                    await get_key(kb_client.order_change, message.text)
                ]
            data['order_type_key'] = await get_key(kb_client.order_change, message.text)
            
            with Session(engine) as session:
                orders = session.scalars(select(Orders)
                    .where(Orders.user_id == message.from_id)
                    .where(Orders.order_type == data['order_type'])
                ).all()
        
        kb_orders = ReplyKeyboardMarkup(resize_keyboard= True)
        orders_lst = []
        for order in orders:
            item = f"{order.order_number} {order.order_type}"
            kb_orders.add(KeyboardButton(item))
            orders_lst.append(item)
        kb_orders.add(kb_client.back_btn).add(kb_client.cancel_btn)
        async with state.proxy() as data:
            data['orders_lst'] = orders_lst
        
        await FSM_Client_client_change_order.next() #-> get_order_number
        
        await bot.send_message(
            message.from_id, 
            "❕ Пожалуйста, выберете номер заказа для изменения",
            reply_markup= kb_orders
        )
    

    elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_main,
        )
    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


async def get_order_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        orders_lst = data['orders_lst']
        order_type_key = data['order_type_key']
        
        data['change_order_note'] = False
        data['photo_type'] = ''
        data['change_tattoo_note'] = False
        data['change_size'] = False
        data['change_tattoo_name'] = False
        data['change_color'] = False
        data['change_bodyplace'] = False
        data['change_bodyplace_video'] = False
        data['change_bodyplace_video_note'] = False
        data['menu_another_price'] = False
        
    with Session(engine) as session:
        sizes = session.scalars(
            select(OrderPriceList).where(
                OrderPriceList.type == kb_admin.price_lst_types[order_type_key]
            )
        ).all()
    kb_client_size_tattoo = ReplyKeyboardMarkup(resize_keyboard=True)
    sizes_lst = []
    for size in sizes:
        sizes_lst.append(f"{size.min_size} - {size.max_size} см2 📏")
        kb_client_size_tattoo.add(
            KeyboardButton(f"{size.min_size} - {size.max_size} см2 📏")
        )
    kb_client_size_tattoo.add(KeyboardButton(kb_client.another_size))
    kb_client_size_tattoo.add(kb_client.back_btn).add(kb_client.cancel_btn)
    
    async with state.proxy() as data:
        data['kb_client_size_tattoo'] = kb_client_size_tattoo
        data['sizes_lst'] = sizes_lst
    
    if message.text in orders_lst:
        async with state.proxy() as data:
            data['order_number'] = message.text.split()[0]
            
        await FSM_Client_client_change_order.next() #-> get_column_name_to_change_order
        await bot.send_message(
            message.from_id,
            MSG_WHICH_ORDER_COLUMN_NAME_WILL_CHANGING,
            reply_markup= kb_client.kb_order_type_columns_names_to_change[order_type_key],
        )
        
    elif message.text in LIST_BACK_COMMANDS:
        kb_orders = ReplyKeyboardMarkup(resize_keyboard= True)
        with Session(engine) as session:
            constant_tattoo_orders = session.scalars(select(Orders)
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]]))
                ).all()        

            shifting_tattoo_orders = session.scalars(select(Orders)
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["shifting_tattoo"]]))
                ).all()
            
            giftbox_orders = session.scalars(select(Orders)
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["giftbox"]]))
                ).all()
            
            sketch_orders = session.scalars(select(Orders)
                .where(Orders.user_id == message.from_id)
                .where(Orders.order_type.in_([kb_admin.price_lst_types["sketch"]]))
                ).all()
        
        if constant_tattoo_orders != []:
            kb_orders.add(KeyboardButton(kb_client.order_change['constant_tattoo']))
        
        if shifting_tattoo_orders != []:
            kb_orders.add(KeyboardButton(kb_client.order_change['shifting_tattoo']))
        
        if giftbox_orders != []:
            kb_orders.add(KeyboardButton(kb_client.order_change['giftbox']))
        
        if sketch_orders != []:
            kb_orders.add(KeyboardButton(kb_client.order_change['sketch']))
        
        kb_orders.add(kb_admin.home_btn)
        
        await bot.send_message(
            message.from_id, 
            "❔ Какой заказ хотите дополнить или изменить?",
            reply_markup= kb_orders
        )
        await FSM_Client_client_change_order.previous()
        
    elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_main,
        )

    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


async def get_column_name_to_change_order(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        order_number = data['order_number']
    
    await FSM_Client_client_change_order.next() # -> get_new_value_to_change_order
    
    """ "tattoo_sketch_photo":  "Добавить/удалить фотографию тату 📷",
        "tattoo_note":          "Дополнить описание тату 📃",
        "order_note":           "Дополнить описание заказа 💬",
        "size":                 "Изменить размер тату 📏",
        "name":                 "Изменить название тату 💭",
        "color":                "Изменить цвет тату 🎨",
        "bodyplace":            "Изменить местоположение тату 👤",
        "bodyplace_photo":      "Добавить/удалить фотографию тела 📷",
        "bodyplace_video_note": "Добавить/удалить видео-заметки тела 📹",
        "bodyplace_video":      "Добавить/удалить видео тела 🎞", 
        sketch_columns_to_change = {
        "tattoo_sketch_photo":  "Добавить/удалить фотографию эскиза 📷",
        "order_note":          "Дополнить описание эскиза 📃",
}
        """
    
    with Session(engine) as session:
        order = session.scalars(select(Orders).where(Orders.order_number == order_number)).one()
        async with state.proxy() as data:
            data['order_id'] = order.id
        # если меняем описание заказа
        if message.text in [
            kb_client.tattoo_columns_to_change["order_note"],
            kb_client.sketch_columns_to_change["order_note"],
            kb_client.giftbox_columns_to_change["order_note"]
        ]:
            async with state.proxy() as data:
                data['change_order_note'] = True
                
            await bot.send_message(
                message.from_id, f"Описание данного заказа:\n\n{order.order_note}"
            )
            await bot.send_message(
                message.from_id, 
                "Напишите, как бы вы дополнили описание заказа.", 
                reply_markup= kb_client.kb_back_cancel
            )
        
        # если меняем изображения в заказе, фото или тела
        elif message.text in [
            kb_client.tattoo_columns_to_change["tattoo_sketch_photo"],
            kb_client.tattoo_columns_to_change["bodyplace_photo"],
            kb_client.sketch_columns_to_change["tattoo_sketch_photo"]
        ]:
            await bot.send_message(
                message.from_id, f"Изображения данного заказа:\n {order.order_note}"
            )
            media = []
            body_photos = []
            order_photos = session.scalars(select(OrderPhoto)
                .where(OrderPhoto.order_id == order.id)).all()
            
            if order.order_type in [
                kb_admin.price_lst_types["constant_tattoo"],
                kb_admin.price_lst_types["shifting_tattoo"]
                ]:
                
                body_photos = session.scalars(select(TattooPlacePhoto)
                    .where(TattooPlacePhoto.order_id == order.id)).all()

            for photo in order_photos + body_photos:
                media.append(types.InputMediaPhoto(photo.photo, order.order_note))
                
            await bot.send_chat_action(
                    message.chat.id, types.ChatActions.UPLOAD_DOCUMENT
                )
            
            await bot.send_media_group(message.chat.id, media=media)
            
            if len(media) > 1:
                await bot.send_message(message.from_user.id, order.order_note)
            
            if order.order_type in [
                kb_admin.price_lst_types["constant_tattoo"],
                kb_admin.price_lst_types["shifting_tattoo"]
                ]:
                await bot.send_message(
                    message.from_id, 
                    MSG_CLIENT_CHOICE_ADD_TATTOO_PHOTO_OR_BODY_PHOTO, 
                    reply_markup= kb_client.kb_client_choice_add_photo_type
                )
                
            else:
                await bot.send_message(
                    message.from_id, MSG_CLIENT_LOAD_PHOTO, reply_markup= kb_client.kb_back_cancel
                )
        # выбираем добавить изображение эскиза
        elif message.text == kb_client.client_choice_add_photo_type['client_want_to_add_sketch_photo']:
            data['photo_type'] = 'order_photo'
            await bot.send_message(
                message.from_id, MSG_CLIENT_LOAD_PHOTO, reply_markup= kb_client.kb_back_cancel
            )
        # выбираем добавить изображение тела
        elif message.text == kb_client.client_choice_add_photo_type['client_want_to_add_body_photo']:
            async with state.proxy() as data:
                data['photo_type'] = 'body'
            await bot.send_message(
                message.from_id, MSG_CLIENT_LOAD_PHOTO, reply_markup= kb_client.kb_back_cancel
            )
        # меняем описание эскиза тату 
        elif message.text == kb_client.tattoo_columns_to_change["tattoo_note"]:
            async with state.proxy() as data:
                data['change_tattoo_note'] = True
            await bot.send_message(
                message.from_id, f"Описание тату в заказе:\n\n{order.tattoo_note}"
            )
            
            await bot.send_message(
                message.from_id, 
                "Напишите, как бы вы дополнили описание тату.", 
                reply_markup= kb_client.kb_back_cancel
            )
        # меняем размер    
        elif message.text == kb_client.tattoo_columns_to_change["size"]:
            async with state.proxy() as data:
                data['change_size'] = True
                kb_client_size_tattoo = data['kb_client_size_tattoo']
            await bot.send_message(
                message.from_id, f"📏 Размер тату в заказе:\n\n{order.tattoo_size}"
            )
            await bot.send_message(
                message.from_id, 
                "❕ Уважаемый Клиент! При изменении размера тату цена заказа изменится."
            )
            
            await bot.send_message(
                message.from_id, "❕ Выберите новый размер для тату", reply_markup= kb_client_size_tattoo
            )
        # меняем имя  
        elif message.text == kb_client.tattoo_columns_to_change["name"]:
            async with state.proxy() as data:
                data['change_tattoo_name'] = True
            await bot.send_message(
                message.from_id, f"Имя тату в заказе:\n\n{order.order_name}"
            )
            
            await bot.send_message(
                message.from_id, 
                "❕ Напишите новое название тату", 
                reply_markup= kb_client.kb_back_cancel
            )
        # меняем цвет
        elif message.text == kb_client.tattoo_columns_to_change["color"]:
            async with state.proxy() as data:
                data['change_color'] = True
            await bot.send_message(
                message.from_id, f"Цвет тату в заказе:\n\n{order.colored}"
            )
            
            await bot.send_message(
                message.from_id, 
                "Выберите новый цвет для тату", 
                reply_markup= kb_client.kb_colored_tattoo_choice
            )
        elif message.text == kb_client.tattoo_columns_to_change["bodyplace"]:
            async with state.proxy() as data:
                data['change_bodyplace'] = True
            await bot.send_message(
                message.from_id, f"Часть тела в заказе:\n\n{order.bodyplace}"
            )
            
            await bot.send_message(
                message.from_id, 
                "❕ Выберите новую часть тела в заказе", 
                reply_markup= kb_client.kb_colored_tattoo_choice
            )
        # если меняем видеозаметку для тела
        elif message.text == kb_client.tattoo_columns_to_change["bodyplace_video_note"]:
            async with state.proxy() as data:
                data['change_bodyplace_video_note'] = True
                
            body_video = session.scalars(select(TattooPlaceVideoNote)
                .where(TattooPlaceVideoNote.order_id == order.id)).all()
            
            if body_video != []:
                await bot.send_message(message.from_id, "📹 Видеозаписи тела в заказе:")
                for video in body_video:
                    media.append(types.InputMediaPhoto(video.video, order.order_note))
                    
                await bot.send_chat_action(
                    message.chat.id, types.ChatActions.UPLOAD_DOCUMENT
                )
                await bot.send_media_group(message.chat.id, media=media)
            
            await bot.send_message(
                message.from_id, 
                MSG_ADD_NEW_VIDEO_NOTE,
                reply_markup= kb_client.kb_back_cancel
            )
        # если меняем видео для тела
        elif message.text == kb_client.tattoo_columns_to_change["bodyplace_video"]:
            async with state.proxy() as data:
                data['change_bodyplace_video'] = True 
                
            body_video = session.scalars(select(TattooPlaceVideo)
                .where(TattooPlaceVideo.order_id == order.id)).all()
            if body_video != []:
                await bot.send_message(message.from_id, "📹 Видеозаписи тела в заказе:")
                for video in body_video:
                    media.append(types.InputMediaPhoto(video.video, order.order_note))
                    
                await bot.send_chat_action(
                    message.chat.id, types.ChatActions.UPLOAD_DOCUMENT
                )
                await bot.send_media_group(message.chat.id, media=media)
            
            await bot.send_message(
                message.from_id, 
                MSG_ADD_NEW_VIDEO_BODY,
                reply_markup= kb_client.kb_back_cancel
            )
        # отмена
        elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
            await state.finish()
            await bot.send_message(
                message.from_id,
                f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
                reply_markup=kb_client.kb_client_main,
            )

        else:
            await bot.send_message(
                message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
            )


async def get_new_value_to_change_order(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        orders_lst = data['orders_lst']
        order_type_key = data['order_type_key']
        order_number = data['order_number']
        order_id = data['order_id']
        change_order_note= data['change_order_note']
        photo_type_to_add = data['photo_type']
        change_tattoo_note= data['change_tattoo_note']
        change_size= data['change_size']
        change_tattoo_name= data['change_tattoo_name']
        change_color= data['change_color']
        change_bodyplace= data['change_bodyplace']
        change_bodyplace_video= data['change_bodyplace_video']
        change_bodyplace_video_note= data['change_bodyplace_video_note']
            
    if any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_main,
        )
    elif message.content_type == 'photo':
        with Session(engine) as session:
            order= session.get(Orders, order_id)
            if photo_type_to_add == 'sketch':
                order.order_photo.append(
                    OrderPhoto(
                        order_number=data["order_number"],
                        telegram_user_id=message.from_id,
                        photo= f"{message.photo[0].file_id}",
                    )
                )
            elif photo_type_to_add == 'body':
                order.tattoo_place_photo.append(
                    TattooPlacePhoto(
                        order_number=data["order_number"],
                        telegram_user_id=message.from_id,
                        photo= f"{message.photo[0].file_id}",
                    )
                )
                await bot.send_message(
                    message.from_id,
                    MSG_Q_ADD_ANOTHER_IMG,
                    reply_markup= kb_client.kb_client_choice_add_another_photo_to_tattoo_order
                )
            session.commit()
    elif message.content_type == 'video' and change_bodyplace_video:
        with Session(engine) as session:
            order= session.get(Orders, order_id)
            order.tattoo_place_video.append(
                TattooPlaceVideo(
                    order_number=data["order_number"],
                    telegram_user_id=message.from_id,
                    video=message.video.file_id,
                )
            )
            session.commit()
        await bot.send_message(
            message.from_id, MSG_VIDEO_WAS_ADDED_TO_ORDER
        )
        await bot.send_message(
            message.from_id, 
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup= kb_client.kb_client_choice_order_view
        )
        
    elif message.content_type == 'video_note' and change_bodyplace_video_note:
        with Session(engine) as session:
            order= session.get(Orders, order_id)
            order.tattoo_place_video.append(
                TattooPlaceVideoNote(
                    order_number=data["order_number"],
                    telegram_user_id=message.from_id,
                    video=message.video_note.file_id,
                )
            )
            session.commit()
        await bot.send_message(
            message.from_id, MSG_VIDEO_NOTE_WAS_ADDED_TO_ORDER,
        )
        await bot.send_message(
            message.from_id, 
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup= kb_client.kb_client_choice_order_view
        )
    # добавить еще фото в заказ
    elif message.text == kb_client.client_choice_add_another_photo_to_tattoo_order['add']:
        await bot.send_message(
            message.from_id,
            MSG_CLIENT_LOAD_PHOTO,
            reply_markup=kb_client.kb_back_cancel,
        )
    # закончить с добавлением изображений
    elif message.text == kb_client.client_choice_add_another_photo_to_tattoo_order['end']:
        await bot.send_message(message.from_id, MSG_PHOTO_WAS_ADDED_TO_ORDER)
        await bot.send_message(
            message.from_id, 
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup= kb_client.kb_client_choice_order_view
        )
    # Добавить фото части тела 📷
    elif message.text == kb_client.client_choice_add_new_bodyplace_type_file['photo']:
        await bot.send_message(
            message.from_id, MSG_CLIENT_LOAD_PHOTO, reply_markup= kb_client.kb_back_cancel
        )
    # Добавить видео части тела 📹
    elif message.text == kb_client.client_choice_add_new_bodyplace_type_file['video']:
        await bot.send_message(
            message.from_id, MSG_ADD_NEW_VIDEO_BODY, reply_markup= kb_client.kb_back_cancel
        )
    # "Добавить видео-заметку части тела 📹"
    elif message.text == kb_client.client_choice_add_new_bodyplace_type_file['video_note']:
        await bot.send_message(
            message.from_id, MSG_ADD_NEW_VIDEO_NOTE, reply_markup= kb_client.kb_back_cancel
        )
    # "Закончить ➡️" - закончить обновление заказа
    elif message.text == kb_client.client_choice_add_new_bodyplace_type_file['end']:
        await state.finish()
        await bot.send_message(
            message.from_id, 
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup= kb_client.kb_client_choice_order_view
        )
    # другой размер
    elif message.text == kb_client.another_size:
        async with state.proxy() as data:
            data['menu_another_price'] = True
        await bot.send_message(
            message.from_id,
            MSG_WHTCH_TATTOO_ANOTHER_SIZE_DO_CLIENT_WANT,
            reply_markup=kb_client.kb_another_size,
        )
    elif message.text in LIST_BACK_COMMANDS:
        async with state.proxy() as data:
            menu_another_price = data['menu_another_price']
            data['menu_another_price'] = False
            kb_client_size_tattoo = data['kb_client_size_tattoo']
            
        if menu_another_price:
            with Session(engine) as session:
                order= session.get(Orders, order_id)
            await bot.send_message(
                message.from_id, f"📏 Размер тату в заказе:\n\n{order.tattoo_size}"
            )
            await bot.send_message(
                message.from_id, "❕ Уважаемый Клиент! При изменении размера тату цена заказа изменится."
            )
            
            await bot.send_message(
                message.from_id, MSG_CLIENT_CHOICE_TATTOO_SIZE, reply_markup= kb_client_size_tattoo
            )
        else:
            await FSM_Client_client_change_order.previous() #-> get_column_name_to_change_order
            await bot.send_message(
                message.from_id,
                MSG_WHICH_ORDER_COLUMN_NAME_WILL_CHANGING,
                reply_markup= kb_client.kb_order_type_columns_names_to_change[order_type_key],
            )
        
    else:
        with Session(engine) as session:
            order= session.get(Orders, order_id)
            
            if change_order_note:
                order.order_note = message.text
                await bot.send_message(message.from_id, MSG_ORDER_NOTE_WAS_UPDATED)
                await state.finish()
                
            elif change_tattoo_note:
                order.tattoo_note = message.text
                await bot.send_message(message.from_id, MSG_TATTOO_NOTE_WAS_UPDATED)
                await state.finish()
                
            elif change_size and message.text.isdigit():
                order.tattoo_size = int(message.text)
                await bot.send_message(message.from_id, MSG_TATTOO_SIZE_WAS_UPDATED)
                await state.finish()
                
            elif change_tattoo_name:
                order.order_name = message.text
                await bot.send_message(message.from_id, MSG_TATTOO_NAME_WAS_UPDATED)
                await state.finish()
                
            elif change_color and message.text in kb_client.colored_tattoo_choice:
                order.colored = message.text
                await bot.send_message(message.from_id, MSG_TATTOO_COLOR_WAS_UPDATED)
                await state.finish()
            
            elif change_bodyplace and message.text in kb_client.tattoo_body_places:
                order.bodyplace = message.text
                await bot.send_message(message.from_id, MSG_TATTOO_BODYPLACE_WAS_UPDATED)
                await bot.send_message(
                    message.from_id, 
                    MSG_CLIENT_CHOICE_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY,
                    reply_markup= kb_client.kb_client_choice_add_new_bodyplace_type_file
                )
            session.commit()
            
        await bot.send_message(
            message.from_id, 
            f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup= kb_client.kb_client_choice_order_view
        )
        
    

def register_handlers_client_change_order(dp: Dispatcher):
    dp.register_message_handler(get_command_client_change_order_menu,
        Text(equals=kb_client.choice_order_view["client_change_order"], ignore_case=True),
        state=None,
    )
    dp.register_message_handler(get_command_client_change_order_menu,
        commands= 'изменить_заказы')
    dp.register_message_handler(get_order_type,
        state=FSM_Client_client_change_order.get_order_type
    )
    dp.register_message_handler(get_order_number,
        state=FSM_Client_client_change_order.get_order_number
    )
    dp.register_message_handler(get_column_name_to_change_order,
        state=FSM_Client_client_change_order.get_column_name_to_change
    )
    
    dp.register_message_handler(get_new_value_to_change_order,
        state=FSM_Client_client_change_order.get_new_value
    )
    