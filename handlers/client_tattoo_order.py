
from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback, full_timep_default, \
    HourTimePicker, hour_timep_callback, MinuteTimePicker, minute_timep_callback, \
    SecondTimePicker, second_timep_callback, \
    MinSecTimePicker, minsec_timep_callback, minsec_timep_default
from aiogram_calendar import simple_cal_callback, SimpleCalendar,\
    dialog_cal_callback, DialogCalendar
from aiogram_timepicker import result, carousel, clock
    
from msg.main_msg import *
from keyboards import kb_client, kb_admin
from handlers.other import *
from handlers.client import ORDER_CODE_LENTH, fill_client_table, \
    DARA_ID, FSM_Client_username_info, CALENDAR_ID

from handlers.calendar_client import obj

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *
from datetime import datetime

# from diffusers import StableDiffusionPipeline
# import torch


#--------------------------------------------------CREATE TATTOO ORDER--------------------------------------
class FSM_Client_tattoo_order(StatesGroup):
    client_choice_main_or_temporary_tattoo = State()
    tattoo_order_photo = State()
    change_tattoo_from_galery = State()
    tattoo_name = State() 
    tattoo_size = State()
    choice_colored_or_not = State()
    # choice_number_of_details = State()
    get_choice_tattoo_place = State()
    choice_tattoo_place = State()
    choice_size_for_tattoo_from_galery = State()
    choice_tattoo_order_date_and_time_meeting = State()
    next_choice_tattoo_order_date_meeting = State()
    date_meeting = State()
    date_time = State()
    tattoo_note = State()
    order_desctiption_choiсe = State()
    order_desctiption = State()
    
    # TODO нужно ли делать оплату тату заказа? - Пока нет 
    tattoo_order_choice_sending_check_documents = State() 
    load_check_document_to_tattoo_order = State()
    

# Начало диалога с пользователем, который хочет добавить новый заказ тату, хочу тату 🕸
async def start_create_new_tattoo_order(message: types.Message):
    # -> get_client_choice_main_or_temporary_tattoo
    await FSM_Client_tattoo_order.client_choice_main_or_temporary_tattoo.set() 
    await bot.send_message(message.from_id,
        '🌿 Отлично, давай подберем уникальную татуировку!\n\n'\
        f'{MSG_CLIENT_WANT_CURRENT_OR_NOT_TATTOO}',
        reply_markup = kb_client.kb_client_choice_main_or_temporary_tattoo)
    


async def get_client_choice_main_or_temporary_tattoo(message: types.Message, state: FSMContext):
    if message.text in list(kb_client.choice_main_or_temporary_tattoo.values()):
        # защита от спама множества заказов. Клиент может заказать только по одному типу товара
        with Session(engine) as session: 
            orders = session.scalars(select(Orders)
                .where(Orders.order_type == message.text[:-2].lower())
                .where(Orders.order_state.in_([STATES['open']]))
                .where(Orders.user_id == message.from_id)).all()
        if orders == []:
            # в прайс-листе находится список размеров
            with Session(engine) as session:
                sizes = session.scalars(select(OrderPriceList)
                    .where(OrderPriceList.type == message.text[:-2].lower())).all()
            kb_client_size_tattoo = ReplyKeyboardMarkup(resize_keyboard=True)
            sizes_lst = []
            for size in sizes:
                sizes_lst.append(f'{size.min_size} - {size.max_size} см2 📏')
                kb_client_size_tattoo.add(KeyboardButton(f'{size.min_size} - {size.max_size} см2 📏'))
            kb_client_size_tattoo.add(KeyboardButton(kb_client.another_size))
            kb_client_size_tattoo.add(kb_client.back_btn).add(kb_client.cancel_btn)
            
            async with state.proxy() as data:
                # tattoo_type = постоянное тату, переводное тату
                data['tattoo_type'] = message.text[:-2].lower()
                data['next_menu_look_tattoo_galery'] = False
                data['load_tattoo_photo'] = False # для меню выбора фото тату - для кнопки "Назад"
                data['load_tattoo_desc'] = False # для меню загрузки описания эскиза тату - для кнопки "Назад"
                data['tattoo_from_galery'] = False # если тату из галереи 
                data['tattoo_photo'] = None # под фото тату
                data['tattoo_photo_tmp_lst'] = ''
                data['tattoo_place_photo'] = []
                data['tattoo_order_photo_counter'] = False
                data['tattoo_place_file_counter'] = 4
                data['tattoo_place_video_note'] = [] # список под видео-записки тела
                data['tattoo_place_video'] = [] # список под видео тела
                data['tattoo_body_place'] = "Без места для тату" # изначальное место для тату в заказе
                data['tattoo_details_number'] = 0 # изначальное количество деталей тату в заказе
                data['order_state'] = STATES["open"] # выставляем статус как открытый
                data['sizes_lst'] = sizes_lst # загружаем список размеров
                data['kb_client_size_tattoo'] = kb_client_size_tattoo            
                data['tattoo_order_number'] = await generate_random_order_number(ORDER_CODE_LENTH)# определяем номер заказа
                data['check_document'] = [] # изначально выставляется в []
                if data['tattoo_type'] == kb_admin.price_lst_types['shifting_tattoo']:
                    # когда тату переводная
                    data['schedule_id'] = None  
                    data['date_meeting'] = None 
                    data['event_type_creation'] = 'no schedule'
                    data['start_date_time'] = None
                    data['end_date_time'] = None
                
            await FSM_Client_tattoo_order.next() # -> load_tattoo_order_photo
            await bot.send_message(message.from_id, f'{MSG_START_TATTOO_ORDER}')
            await bot.send_message(message.from_id, f'{MSG_SCRETH_DEV}\n\n{MSG_GET_PHOTO_FROM_USER}',
                # ['Посмотреть галерею тату 📃', 'Загрузить свою фотографию эскиза 📎', 
                # 'У меня нет фотографии для эскиза 😓', 'Отмена ❌']
                reply_markup = kb_client.kb_no_photo_in_tattoo_order)
        else:
            await bot.send_message(message.from_id, MSG_CLIENT_ALREADY_HAVE_OPEN_ORDER)
        
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, 
            reply_markup = kb_client.kb_client_main)
        
    elif message.text in LIST_BACK_COMMANDS:
        # await FSM_Client_tattoo_order.previous() # ->start_create_new_tattoo_order
        await bot.send_message(message.from_id,
        f'{MSG_CLIENT_GO_BACK} {MSG_CLIENT_WANT_CURRENT_OR_NOT_TATTOO}',
        reply_markup = kb_client.kb_client_choice_main_or_temporary_tattoo)
        
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def load_tattoo_order_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['telegram'] = message.from_id
        data['next_menu_another_size'], data['next_menu_detailed_number'] = False, False
        data['next_menu_change_color'], data['next_menu_size'] = False, False
        data['session'] = await generate_random_order_number(ORDER_CODE_LENTH)
        data['menu_tattoo_list_place'] = False
        data['client_fill_order_note'] = False
        
    #? TODO выдавать ли цену тату при упоминании заказа? - нет,
    #? цена будет известна уже при работе с клиентом
    #? TODO нужно ли выбирать все тату, или только админские? - только админские
    with Session(engine) as session:
        tattoo_items = session.scalars(select(TattooItems)
            .where(TattooItems.creator == "admin")).all()
        
    kb_tattoo_items_for_order = ReplyKeyboardMarkup(resize_keyboard=True)
    list_kb_tattoo_items = []
    for tattoo in tattoo_items:
        kb_tattoo_item_text = f'{tattoo.name}'
        list_kb_tattoo_items.append(kb_tattoo_item_text)
        kb_tattoo_items_for_order.add(KeyboardButton(kb_tattoo_item_text))

    kb_tattoo_items_for_order.add(KeyboardButton(kb_client.client_still_want_his_sketch)
        ).add(kb_client.back_btn).add(kb_client.cancel_btn)
    
    if message.content_type == 'text':
        if any(text in message.text for text in LIST_CANCEL_COMMANDS):
            await state.finish()
            await bot.send_message(message.from_id,  MSG_BACK_TO_HOME, 
                reply_markup = kb_client.kb_client_main)
            
        elif any(text in message.text for text in LIST_BACK_COMMANDS): 
            async with state.proxy() as data:
                next_menu_look_tattoo_galery = data['next_menu_look_tattoo_galery']
                data['next_menu_look_tattoo_galery'] = False
                load_tattoo_desc = data['load_tattoo_desc']
                data['load_tattoo_desc'] = False
                load_tattoo_photo = data['load_tattoo_photo']
                data['load_tattoo_photo'] = False
                
            if next_menu_look_tattoo_galery or load_tattoo_desc or load_tattoo_photo:
                await bot.send_message(message.from_id,  
                    MSG_CLIENT_BACK_AND_WHICH_PHOTO_DO_CLIENT_WANT_TO_LOAD,
                    reply_markup = kb_client.kb_no_photo_in_tattoo_order)
            else:
                await FSM_Client_tattoo_order.previous()
                await bot.send_message(message.from_id,
                    f'{MSG_CLIENT_GO_BACK} {MSG_CLIENT_WANT_CURRENT_OR_NOT_TATTOO}',
                    reply_markup = kb_client.kb_client_choice_main_or_temporary_tattoo)
        
        # 'У меня нет идеи для эскиза 😓'
        elif message.text == kb_client.no_photo_in_tattoo_order['no_idea_tattoo_photo']:
            async with state.proxy() as data:
                data['tattoo_photo_tmp_lst'] = None
                data['tattoo_from_galery'] = False
            for i in range(2):
                await FSM_Client_tattoo_order.next() # -> load_tattoo_order_size
            await bot.send_message(message.from_id,  
                '💬 Хорошо, определимся с эскизом тату для этого заказа позже.')
            await bot.send_message(message.from_id, f'{MSG_CLIENT_CHOICE_TATTOO_NAME}',
                reply_markup = kb_client.kb_back_cancel)
        
        # Хочу эскиз по моему описанию 💬
        elif message.text == kb_client.no_photo_in_tattoo_order['load_tattoo_desc']:
            async with state.proxy() as data:
                data['load_tattoo_desc'] = True
                data['tattoo_from_galery'] = False
                
            await bot.send_message(message.from_id,
                f'{MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT}')
            await bot.send_message(message.from_id,
                f'{MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT_CONCEPTS}')
            ''' 
            await bot.send_message(message.from_id, f'{MSG_STYLES_CHROMATIC_PALETTES}')
            await bot.send_message(message.from_id, f'{MSG_STYLES_MONOCHROMATIC_PALETTES}')
            await bot.send_message(message.from_id, f'{MSG_STYLES_CONTRAST}')
            await bot.send_message(message.from_id, f'{MSG_MOTION_PICTURE_PROCESS}') 
            '''
            await bot.send_message(message.from_id,
                f'💬 введите текст для эскиза, пожалуйста.',
                reply_markup= kb_client.kb_back_cancel)

        # 'Посмотреть галерею тату 📃
        elif message.text == kb_client.no_photo_in_tattoo_order['look_tattoo_galery']:
            async with state.proxy() as data:
                data['next_menu_look_tattoo_galery'] = True
            for tattoo in tattoo_items:
                #? TODO нужно ли выводить размер и цену?
                msg = f'📃 Название: {tattoo.name}\n🎨 Цвет: {tattoo.colored}\n'
                    #\f'🔧 Количество деталей: {tattoo.}\n'
                if tattoo.note not in ['Без описания', None]:
                    msg += f'💬 Описание: {tattoo.note}\n'
                    
                with Session(engine) as session:
                    photos = session.scalars(select(TattooItemPhoto).where(
                        TattooItemPhoto.tattoo_item_name == tattoo.name)).all()
                    
                media = []
                for photo in photos:
                    media.append(types.InputMediaPhoto(photo.photo, msg))
                    
                await bot.send_media_group(message.from_user.id, media= media)
                    
            # выдаем список тату - фотографии, название, цвет, описание    
            await bot.send_message(message.from_id, f'{MSG_WHICH_TATTOO_WANT_TO_CHOOSE}',
                reply_markup = kb_tattoo_items_for_order) 
            
        # переходим сюда, если клиент выбрал эскиз из списка    
        elif message.text in list_kb_tattoo_items: 
            for tattoo in tattoo_items:
                if message.text == f'{tattoo.name}':
                    with Session(engine) as session:
                        photos = session.scalars(select(TattooItemPhoto)
                            .where(TattooItemPhoto.tattoo_item_name == tattoo.name)).one()
                    
                    async with state.proxy() as data:
                        data['tattoo_photo_tmp_lst'] =  f"{photos.photo}|"
                        data['tattoo_name'] = tattoo.name
                        # data['tattoo_photo'] = photos
                        data['tattoo_price'] = tattoo.price
                        # data['tattoo_details_number'] = tattoo[5]
                        data['tattoo_colored'] = tattoo.colored
                        data['tattoo_from_galery'] = True
                        data['menu_change_name'] = False
                        data['next_menu_detailed_number'] = False
                        data['menu_tattoo_list_place'] = False
                        
            await FSM_Client_tattoo_order.next() # -> change_menu_tattoo_from_galery
            await bot.send_message(message.from_id, '📷 Отлично, ты выбрал(а) эскиз для своего тату!')
            await bot.send_message(message.from_id, f'{CLIENT_WANT_TO_CHANGE_MORE}',
                # 'Хочу дать свое название тату', 'Хочу изменить размер тату', 
                # 'Хочу изменить цвета у тату', 'Хочу изменить детали на тату'
                reply_markup = kb_client.kb_tattoo_from_galery_change_options) 
        
        # Загрузить свою фотографию эскиза 📎
        # Все же хочу свой эскиз для тату 🙅‍♂️
        # Добавить еще одно изображение ☘️
        elif message.text in [kb_client.no_photo_in_tattoo_order['load_tattoo_photo'], 
            kb_client.client_still_want_his_sketch, 
            kb_client.client_choice_add_another_photo_to_tattoo_order[
                'client_want_to_add_sketch_to_tattoo_order']
            ]:
            
            async with state.proxy() as data:
                data['tattoo_order_photo_counter'] = 0
                data['load_tattoo_photo'] = True
                
            await bot.send_message(message.from_id, MSG_CLIENT_LOAD_PHOTO,
                reply_markup= kb_client.kb_back_cancel)
            
        # Да, отличное изображение, хочу такой эскиз ☘️
        elif message.text == kb_client.correct_photo_from_ai_or_get_another["correct_photo_from_ai"]:
            
            async with state.proxy() as data:
                data['tattoo_photo'] = data['last_img_photo_from_ai']
                
            for i in range(2):
                await FSM_Client_tattoo_order.next() # -> load_tattoo_order_name
            await bot.send_message(message.from_id,  
                f'{MSG_CLIENT_SUCCESS_CHOICE_PHOTO}'\
                f'{MSG_CLIENT_CHOICE_TATTOO_NAME}',
                reply_markup = kb_client.kb_back_cancel)
            
        # Закончить с добавлением изображений ➡️
        elif message.text == \
            kb_client.client_choice_add_another_photo_to_tattoo_order[
                'client_dont_want_to_add_sketch_to_tattoo_order'
                ]:
            for i in range(2):
                await FSM_Client_tattoo_order.next() # -> load_tattoo_order_name
            
            await bot.send_message(message.from_id, "❕ Хорошо, с фотографиями для эскиза мы пока закончили.")
            await bot.send_message(message.from_id, f'{MSG_CLIENT_CHOICE_TATTOO_NAME}',
                reply_markup= kb_client.kb_back_cancel)
            
        # "Нет, хочу другое изображение 😓"
        elif message.text == kb_client.correct_photo_from_ai_or_get_another["want_another_ai_img"]:
                async with state.proxy() as data:            
                    data['load_tattoo_desc'] = True
                
                await bot.send_message(message.from_id,  
                    '📷 Хорошо, давай получим другое фото. введите текст для эскиза, пожалуйста.',
                    reply_markup= kb_client.kb_back_cancel)
        else:
            try:
                async with state.proxy() as data:
                    load_tattoo_desc = data['load_tattoo_desc']
                    data['load_tattoo_desc'] = False
                    session = data['session']
                    
                # !!!!! заглушка stop_generate_bool. Если false, то клиент может генерить изображения    
                stop_generate_bool = True 
                if load_tattoo_desc and stop_generate_bool != True:
                    #! cd stable-diffusion
                    #! git clone https://huggingface.co/runwayml/stable-diffusion-v1-5
                    ''' from diffusers import StableDiffusionPipeline
                    import torch

                    model_id = "stable-diffusion/stable-diffusion-v1-5/"# .ckpt
                    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
                    pipe = pipe.to("cuda")

                    # prompt = "a photo of an astronaut riding a horse on mars, Technicolo, Monochrome, Light Mode"
                    
                    image = pipe(message.text).images[0]  
                    random_number_for_name = await generate_random_order_number(ORDER_CODE_LENTH)
                    image_name = str(random_number_for_name)
                    
                    #! path = f"./img/tattoo_ideas/{message.from_user.username}/{session}/{image_name}.png"
                    path = f"./img/tattoo_ideas/{image_name}.png"
                    image.save(path) 
                    
                    msg = MSG_ANSWER_AOUT_RESULT_TATTOO_FROM_AI
                    ai_img = await bot.send_photo(message.chat.id, open(path, 'rb'), msg,
                        reply_markup = kb_client.kb_correct_photo_from_ai_or_get_another) 
                    async with state.proxy() as data:
                        data['last_img_photo_from_ai'] = ai_img['photo'][0]['file_id']'''
                        
                elif stop_generate_bool:
                    async with state.proxy() as data:
                        data['tattoo_photo'] = None
                    
                    for i in range(2):
                        await FSM_Client_tattoo_order.next() # -> load_tattoo_order_name
                    await bot.send_message(message.from_id,  
                        '📷 Отлично, ты описал свой эскиз!\n\n'\
                        f'{MSG_CLIENT_CHOICE_TATTOO_NAME}',
                        reply_markup = kb_client.kb_back_cancel)
                
                    
                else:
                    await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
                    
            except:
                await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
            
    elif message.content_type == 'photo':
        async with state.proxy() as data:
            data['tattoo_from_galery'] = False
            data['tattoo_photo_tmp_lst'] += f'{message.photo[0].file_id}|'
            tattoo_order_photo_counter = data['tattoo_order_photo_counter']
            data['tattoo_order_photo_counter'] = message.media_group_id
            
        if tattoo_order_photo_counter != data['tattoo_order_photo_counter']:
            async with state.proxy() as data:
                tattoo_order_photo_counter = data['tattoo_order_photo_counter']
            
            await bot.send_message(message.from_id,  
                '📷 Отлично, ты выбрал(а) фотографию эскиза для своего тату!')
            await bot.send_message(message.from_id, '❔ Хотите добавить еще фото/картинку?',
                reply_markup= kb_client.kb_client_choice_add_another_photo_to_tattoo_order)
            #f'{MSG_CLIENT_CHOICE_TATTOO_NAME}',
            #reply_markup = kb_client.kb_back_cancel)


async def change_menu_tattoo_from_galery(message: types.Message, state: FSMContext):
    print(await state.get_state())
    async with state.proxy() as data:
        sizes_lst = data['sizes_lst']
        
    if any(text in message.text for text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME):
        await state.finish()
        await bot.send_message(message.from_id, 
            MSG_BACK_TO_HOME, reply_markup = kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS):
        async with state.proxy() as data:
            next_menu_size = data['next_menu_size']
            next_menu_another_size = data['next_menu_another_size']
            next_menu_detailed_number = data['next_menu_detailed_number']
            next_menu_change_color = data['next_menu_change_color']
            tattoo_from_galery = data['tattoo_from_galery']
            menu_change_name = data['menu_change_name']
            kb_client_size_tattoo = data['kb_client_size_tattoo']
            
            data['next_menu_another_size'], data['next_menu_detailed_number'] = False, False
            data['next_menu_change_color'], data['menu_change_name'] =  False, False
        
        if next_menu_another_size:
            await bot.send_message(message.from_id, 
                f'{MSG_CLIENT_GO_BACK}{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
                reply_markup= kb_client_size_tattoo)
            
        elif next_menu_detailed_number or next_menu_change_color or next_menu_size or menu_change_name:
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}{CLIENT_WANT_TO_CHANGE_MORE}',
                reply_markup= kb_client.kb_tattoo_from_galery_change_options)
            
        elif tattoo_from_galery:
            await FSM_Client_tattoo_order.previous() # -> load_tattoo_order_photo
            with Session(engine) as session:
                tattoo_items = session.scalars(select(TattooItems)
                    .where(TattooItems.creator == "admin")).all()
            
            kb_tattoo_items_for_order = ReplyKeyboardMarkup(resize_keyboard=True)
            for tattoo in tattoo_items:
                kb_tattoo_items_for_order.add(KeyboardButton(f'{tattoo.name}'))
                
            kb_tattoo_items_for_order.add(KeyboardButton(
                    kb_client.client_still_want_his_sketch)
                ).add(kb_client.back_btn).add(kb_client.cancel_btn)
            # TODO добавить inline кнопки
            await bot.send_message(message.from_id, 
                f'{MSG_CLIENT_GO_BACK}{MSG_WHICH_TATTOO_WANT_TO_CHOOSE}',
                reply_markup = kb_tattoo_items_for_order)
            
        else:
            await FSM_Client_tattoo_order.previous() # -> load_tattoo_order_photo
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}{MSG_GET_PHOTO_FROM_USER}',
                reply_markup= kb_client.kb_no_photo_in_tattoo_order)
    
    # меняем имя тату
    elif message.text == \
        kb_client.tattoo_from_galery_change_options['client_want_to_change_tattoo_name']:
        async with state.proxy() as data:
            data['menu_change_name'] = True
            
        await bot.send_message(message.from_id, f'📏 Хорошо, давай поменяем имя тату\n\n'\
            f'{MSG_CLIENT_CHOICE_TATTOO_NAME}', reply_markup = kb_client.kb_back_cancel)
        
    # меняем цвет тату
    elif message.text == \
        kb_client.tattoo_from_galery_change_options['client_want_to_change_tattoo_color']:
        
        async with state.proxy() as data:
            data['next_menu_change_color'] = True
            color = data['tattoo_colored']
            
        await bot.send_message(message.from_id, 
            f'🎨 Изначальный цвет тату: {color}\n\n'\
            f'{MSG_WHICH_COLOR_WILL_BE_TATTOO}',
            reply_markup = kb_client.kb_colored_tattoo_choice)
    
    # меняем детали в тату
    elif message.text == \
        kb_client.tattoo_from_galery_change_options['client_want_to_change_tattoo_details']:
        async with state.proxy() as data:
            data['next_menu_detailed_number'] = True
            photo = data['tattoo_photo_tmp_lst'].split('|')[0]
            
        await bot.send_photo(message.from_id, photo)
        await bot.send_message(message.from_id,  # f'🔧 Давайте поменяем детали в тату.\n'\
            # f' Изначальное количество деталей в тату: {details}\n\n'\
            '🔧❔ Опишите, какие детали Хотите изменить или убрать из эскиза этого тату?',
            reply_markup = kb_client.kb_back_cancel)

    # ничего не хочу менять -> get_choice_tattoo_place
    elif message.text == kb_client.tattoo_from_galery_change_options['no_change']:
        async with state.proxy() as data:      
            name = data['tattoo_name'] 
            color = data['tattoo_colored']
            
        for i in range(4):
            await FSM_Client_tattoo_order.next() # -> get_choice_tattoo_place
            
        await bot.send_message(message.from_id,  
            f'🌿 Вы выбрали тату под названием \"{name}\".\nТату будет {color.lower()}')
        await bot.send_message(message.from_id, 
            f'❔ Хотите указать место, где будет располагаться тату?', 
            reply_markup= kb_client.kb_choice_place_tattoo)
        # await view_schedule_to_client(message, state)
        
    # изменяем размер у тату из галереи
    elif any(text in message.text for text in sizes_lst):
        async with state.proxy() as data:
            data['tattoo_size'] = message.text
            data['next_menu_another_size'] = False
            
        await bot.send_message(message.from_id,  
            f'📏 Отлично, вы выбрали размер {message.text}\n\n'\
            f'{CLIENT_WANT_TO_CHANGE_MORE}',
            reply_markup = kb_client.kb_tattoo_from_galery_change_options)
        
    elif message.text.lower() == kb_client.another_size:
        async with state.proxy() as data:
            data['next_menu_another_size'] = True
            
        await bot.send_message(message.from_id, '❔ Какой размер тату вы хотели бы?',
            reply_markup = kb_client.kb_another_size)
    
    # ['Ч/б тату 🖤', 'Цветное тату ❤️']
    elif any(text in message.text for text in kb_client.colored_tattoo_choice):
        async with state.proxy() as data:
            data['tattoo_colored'] = message.text.split()[0]
        await bot.send_message(message.from_id,  
            f'🍃 Хорошо, тату будет {message.text.split()[0].lower()}\n\n'\
            f'{CLIENT_WANT_TO_CHANGE_MORE}',
            reply_markup = kb_client.kb_tattoo_from_galery_change_options)
    else:
        try:
            async with state.proxy() as data:
                next_menu_detailed_number = data['next_menu_detailed_number']
                menu_change_name = data['menu_change_name']
                
            if next_menu_detailed_number:
                async with state.proxy() as data:
                    data['tattoo_details_number'] = message.text
                await bot.send_message(message.from_id, 
                    f'🍃 Хорошо, ваши изменения деталей в данном эскизе сохранены.\n\n'\
                    f'{CLIENT_WANT_TO_CHANGE_MORE}',
                    reply_markup = kb_client.kb_tattoo_from_galery_change_options)
                
            elif menu_change_name:
                async with state.proxy() as data:
                    data['tattoo_name'] = message.text
                await bot.send_message(message.from_id, 
                    f'🍃 Хорошо, теперь у тату будет имя {message.text}\n\n'\
                    f'{CLIENT_WANT_TO_CHANGE_MORE}',
                    reply_markup = kb_client.kb_tattoo_from_galery_change_options)
            else:
                await bot.send_message(message.from_id,  MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
        except:
            await bot.send_message(message.from_id,  MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# Отправляем название тату
async def load_tattoo_order_name(message: types.Message, state: FSMContext):
    print(await state.get_state())
    if any(text in message.text for text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME):
        await state.finish()
        await bot.send_message(message.from_id,  MSG_BACK_TO_HOME, 
            reply_markup = kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS):
        for i in range(2):
            await FSM_Client_tattoo_order.previous() # -> load_tattoo_order_photo
            
        await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}{MSG_GET_PHOTO_FROM_USER}',
            reply_markup=kb_client.kb_no_photo_in_tattoo_order)
    else:
        async with state.proxy() as data:
            data['tattoo_name'] = message.text
            data['telegram'] = message.from_id
            kb_client_size_tattoo = data['kb_client_size_tattoo']
        await FSM_Client_tattoo_order.next() # -> load_tattoo_order_size
        # в прайс-листе находится список размеров

        await bot.send_message(message.from_id,  f'{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
            reply_markup= kb_client_size_tattoo)


# Отправляем размер тату и выбираем выбираем цвет тату
async def load_tattoo_order_size(message: types.Message, state: FSMContext):  
    print(await state.get_state())
    async with state.proxy() as data:
        sizes_lst = data['sizes_lst']
        
    if message.text == kb_client.another_size: # 'Другой размер'
        async with state.proxy() as data:
            data['next_menu_another_size'] = True
            
        await bot.send_message(message.from_id, '❔ Какой размер тату вы хотели бы?',
            reply_markup = kb_client.kb_another_size)
        
    elif message.text in sizes_lst + kb_client.another_size_lst:
        async with state.proxy() as data:
            data['tattoo_size'] = message.text
            if 'x' in message.text:
                tmp = message.text.split('x')
                data['tattoo_size'] = f"{tmp[0]} - {tmp[1]} см2 📏"
                
            data['next_menu_another_size'] = False
            
        await FSM_Client_tattoo_order.next() # -> get_choice_colored_or_not
        await bot.send_message(message.from_id,  
            f'📏 Отлично, вы выбрали размер {message.text}')
        
        await bot.send_message(message.from_id,
            '❔ А теперь скажи, это тату будет цветным или ч/б?',
            reply_markup= kb_client.kb_colored_tattoo_choice)
        
    elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME,
            reply_markup= kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS): 
        async with state.proxy() as data:
            next_menu_another_size = data['next_menu_another_size']
            data['next_menu_another_size'] = False
            
        if next_menu_another_size == False:
            await FSM_Client_tattoo_order.previous() # -> load_tattoo_order_name
            await bot.send_message(message.from_id, 
                f'{MSG_CLIENT_GO_BACK}{MSG_CLIENT_CHOICE_TATTOO_NAME}',
                # ['Посмотреть галерею тату 📃', 'Загрузить свою фотографию эскиза 📎', 
                # 'У меня нет фотографии для эскиза 😓', 'Назад 🔙', 'Отмена ❌']
                reply_markup = kb_client.kb_back_cancel
            )
        else:
            async with state.proxy() as data:
                kb_client_size_tattoo = data['kb_client_size_tattoo']
            
            await bot.send_message(message.from_id, 
                f'{MSG_CLIENT_GO_BACK}{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
                reply_markup= kb_client_size_tattoo)
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_choice_colored_or_not(message: types.Message, state: FSMContext):
    if any(text in message.text for text in kb_client.colored_tattoo_choice):
        async with state.proxy() as data:
            data['tattoo_colored'] = message.text.split()[0]
            
        await FSM_Client_tattoo_order.next() # -> get_choice_tattoo_place
        await bot.send_message(message.from_id,
            f'🍃 Хорошо, вашу тату будет {message.text.split()[0].lower()}')
        
        await bot.send_message(message.from_id, '❔ Хотите указать место, где будет располагаться тату?',
            # "Да, я знаю, где будет располагаться мое тату и хочу выбрать место", "Нет, я пока не знаю, где будет мое тату"
            reply_markup= kb_client.kb_choice_place_tattoo)
            
    elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup= kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS):
        await FSM_Client_tattoo_order.previous() # -> load_tattoo_order_size
        await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}')
        async with state.proxy() as data:
            kb_client_size_tattoo = data['kb_client_size_tattoo']
            
        await bot.send_message(message.from_id, f'{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
            reply_markup= kb_client_size_tattoo)
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


#! выводим на экран расписание
# get_choice_tattoo_place -> view_schedule_to_client
# get_photo_place_for_tattoo -> view_schedule_to_client
# get_size_tattoo_from_galery -> view_schedule_to_client
# load_tattoo_order_note -> view_schedule_to_client
async def view_schedule_to_client(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        schedule = session.scalars(select(ScheduleCalendar)
            .where(ScheduleCalendar.status == "Свободен")
            .where(ScheduleCalendar.event_type == "тату заказ")).all()
    
    if schedule == []:
        await bot.send_message(message.from_id, MSG_TO_NO_SCHEDULE,
            reply_markup= kb_client.kb_next_action)
    else:
        kb_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
        with Session(engine) as session:
            schedule_photo = session.scalars(select(SchedulePhoto).where(
                SchedulePhoto.name == datetime.strftime(datetime.now(), '%m %Y'))).all()
        
        async with state.proxy() as data:
            kb_items_list = []
            date_list_full_for_msg = ''
            for date in schedule:
                if date.start_datetime > datetime.now():
                    month = await get_month_from_number(int(date.start_datetime.strftime("%m")), 'ru')
                    item_in_kb = f"{month} {date.start_datetime.strftime('%d/%m/%Y c %H:%M')}"\
                        f" по {date.end_datetime.strftime('%H:%M')} 🗓"
                    kb_items_list.append(item_in_kb)
                    date_list_full_for_msg += f'{item_in_kb}\n'
                    kb_schedule.add(KeyboardButton(item_in_kb))
            
            kb_schedule.add(kb_client.back_btn).add(kb_client.cancel_btn) 
            # выдаем на экран свободное фото расписания, или просто сообщение, если фото нет
            
            if schedule_photo == []:
                await bot.send_message(message.from_user.id,
                    f'{MSG_MY_FREE_CALENDAR_DATES}{date_list_full_for_msg}')
                
            else:
                await bot.send_photo( message.from_user.id, schedule_photo.photo,
                    f'{MSG_MY_FREE_CALENDAR_DATES}{date_list_full_for_msg}')
            data['date_free_list'] = schedule
            data['date_free_kb_items_list'] = kb_items_list 
        
        await bot.send_message( message.from_user.id, MSG_TO_GET_SCHEDULE,
            reply_markup= kb_schedule ) # await DialogCalendar().start_calendar()
        #!!! переходим в choice_tattoo_order_date_and_time_meeting


# --------------------------------------------get_choice_tattoo_place---------------------------------
async def get_choice_tattoo_place(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['client_add_tattoo_place_photo'] = False
        tattoo_type = data['tattoo_type']
    # if message.content_type == 'text':
    # "Да, я знаю, где будет располагаться мое тату и хочу выбрать место"
    if message.text == kb_client.choice_place_tattoo["client_know_place"]:
        # await FSM_Client_tattoo_order.next()
        async with state.proxy() as data:
            data['menu_tattoo_list_place'] = True
            
        await bot.send_message(message.from_id, 
            '🗾 Хорошо, тогда выбери место для своего тату, пожалуйста',
            reply_markup= kb_client.kb_place_for_tattoo)
    #
    # "Нет, я пока не знаю, где будет мое тату"
    elif message.text in [kb_client.choice_place_tattoo["client_has_no_idea_for_place"],
        kb_client.tattoo_body_places[-1]]: # 'Пока не знаю, какое место я хотел бы выбрать 🤷🏻‍♂️'
        async with state.proxy() as data:
            data['tattoo_body_place'] = "Без места для тату"
            tattoo_from_galery = data['tattoo_from_galery']
        
        await bot.send_message(message.from_id, MSG_TATTOO_ORDER_CLIENT_CHOICE_BODY_LATER)
            
        if tattoo_from_galery:
            for i in range(2):
                await FSM_Client_tattoo_order.next() # -> get_size_tattoo_from_galery
                
            async with state.proxy() as data:
                kb_client_size_tattoo = data['kb_client_size_tattoo']
            
            await bot.send_message(message.from_id,  f'{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
                reply_markup= kb_client_size_tattoo)
            
        elif tattoo_type == kb_admin.price_lst_types['shifting_tattoo']:
            for i in range(7):
                # пропускаем добавление фотографии и выбор календаря,
                # переходим сразу в заполнение tattoo order note
                await FSM_Client_tattoo_order.next() # -> # load_tattoo_order_note
                
            await bot.send_message(message.from_id,   
                f'🌿 А теперь введите что-нибудь о своем тату!'\
                    ' Чем подробнее описание тату, тем лучше! \n\n'\
                f'➡️ Или нажмите \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
                reply_markup= kb_client.kb_no_tattoo_note_from_client
            )
        else:# выводим на экран расписание и переходим дальше
            for i in range(3):
                await FSM_Client_tattoo_order.next() #! -> choice_tattoo_order_date_and_time_meeting
            await view_schedule_to_client(message, state) 
        
    elif message.text in kb_client.tattoo_body_places:
        async with state.proxy() as data:
            data['tattoo_body_place'] = message.text
            
        if message.text == kb_client.tattoo_body_places[:-2]: # Другое место 🙅‍♂️
            await bot.send_message(message.from_id,
                '❔ Какое место ты хотел(а) бы использовать для тату?',
                reply_markup= kb_client.kb_back_cancel)
        else:
            await bot.send_message(message.from_id, 
                f'🌿 Хорошо, с местом определились, это будет {message.text.lower()}')
            
            await bot.send_message(message.from_id,
                '❔ Хотите отправить фото или видео, где тату будет располагаться?',
                reply_markup= kb_client.kb_choice_get_photo_for_place_tattoo)
    
    # "Да, хочу отправить фото/видео "
    elif message.text == kb_client.choice_get_photo_for_place_tattoo['client_want_to_get_place']:
        await FSM_Client_tattoo_order.next() # -> get_photo_place_for_tattoo
        await bot.send_message(message.from_id,  
            '📎 Отправьте фото части тела, на котором будет тату, пожалуйста\n\n'\
            '❕ Можно добавлять сразу несколько файлов.',
            reply_markup= kb_client.kb_back_cancel)
    
    # "Нет, не хочу"
    elif message.text == kb_client.choice_get_photo_for_place_tattoo['client_dont_want_to_get_place']:
        await bot.send_message(message.from_id, '❕ Не проблема, добавить фото/видео для тату можно позже.')
        async with state.proxy() as data:
            tattoo_from_galery = data['tattoo_from_galery']
            data['client_add_tattoo_place_photo'] = False
            
        if tattoo_from_galery:
            for i in range(2):
                await FSM_Client_tattoo_order.next() # -> get_size_tattoo_from_galery
                
            async with state.proxy() as data:
                kb_client_size_tattoo = data['kb_client_size_tattoo']
            
            await bot.send_message(message.from_id,  f'{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
                reply_markup= kb_client_size_tattoo)
            
        elif tattoo_type == kb_admin.price_lst_types['shifting_tattoo']:
            for i in range(7):
                # пропускаем добавление фотографии и выбор календаря,
                # переходим сразу в заполнение tattoo order note
                await FSM_Client_tattoo_order.next() # -> # load_tattoo_order_note
                
            await bot.send_message(message.from_id,   
                f'🌿 А теперь введите что-нибудь о своем тату!'\
                    ' Чем подробнее описание тату, тем лучше! \n\n'\
                f'➡️ Или нажмите \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
                reply_markup= kb_client.kb_no_tattoo_note_from_client
            )
        else:# выводим на экран расписание и переходим дальше
            for i in range(3):
                await FSM_Client_tattoo_order.next() #! -> choice_tattoo_order_date_and_time_meeting
            await view_schedule_to_client(message, state) 

    elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup= kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS):
        async with state.proxy() as data:
            tattoo_from_galery = data['tattoo_from_galery']
            menu_tattoo_list_place = data['menu_tattoo_list_place']
            data['menu_tattoo_list_place'] = False
            
        if menu_tattoo_list_place:
            await bot.send_message(message.from_id,  f'{MSG_CLIENT_GO_BACK} '\
                '❔ Хотите указать место, где будет располагаться тату?', 
                reply_markup = kb_client.kb_choice_place_tattoo)
            
        elif tattoo_from_galery:
            for i in range(4):
                await FSM_Client_tattoo_order.previous() # -> change_menu_tattoo_from_galery
            
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}{CLIENT_WANT_TO_CHANGE_MORE}',
                # 'Хочу дать свое название тату', 'Хочу изменить размер тату', 
                # 'Хочу изменить цвета у тату', 'Хочу изменить детали на тату'
                reply_markup = kb_client.kb_tattoo_from_galery_change_options) 
        else:
            await FSM_Client_tattoo_order.previous() # -> get_choice_colored_or_not
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}'\
                '❔ А теперь скажи, это тату будет цветным или ч/б?',
                reply_markup=kb_client.kb_colored_tattoo_choice)
    else:
        async with state.proxy() as data:
            tattoo_body_place = data['tattoo_body_place']
            
        if tattoo_body_place == 'Другое место 🙅‍♂️':
            async with state.proxy() as data:
                data['tattoo_body_place'] = message.text
                
            await bot.send_message(message.from_id, 
                f'🌿 Хорошо, с местом определились, это будет {message.text.lower()}')
            await bot.send_message(message.from_id,
                '❔ Хотите отправить фото или видео, где тату будет располагаться?',
                reply_markup= kb_client.kb_choice_get_photo_for_place_tattoo)
        else:
            await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# ------------------------------------------get_photo_place_for_tattoo---------------------------------
async def get_photo_place_for_tattoo(message: types.Message, state: FSMContext):
    print(await state.get_state())
    if message.content_type == 'text':
        async with state.proxy() as data:
            tattoo_from_galery = data['tattoo_from_galery']
        
        if message.text == kb_client.yes_str:
            async with state.proxy() as data:
                data['tattoo_place_file_counter'] = 0 
                
            await bot.send_message( message.from_id, 
                '📎 Хорошо, Отправьте еще фотографию или видео через файлы.', 
                reply_markup= kb_client.kb_back_cancel)
            
        elif message.text == kb_client.no_str:
            if tattoo_from_galery:
                await FSM_Client_tattoo_order.next() # -> get_size_tattoo_from_galery
                
                async with state.proxy() as data:
                    kb_client_size_tattoo = data['kb_client_size_tattoo']
                
                await bot.send_message(message.from_id, f'{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
                    reply_markup= kb_client_size_tattoo)
            
            else:
                async with state.proxy() as data:
                    tattoo_type = data['tattoo_type']
                    
                if tattoo_type == kb_admin.price_lst_types['constant_tattoo']:
                    # выводим на экран расписание и переходим дальше
                    for i in range(2):
                        await FSM_Client_tattoo_order.next() #! -> choice_tattoo_order_date_and_time_meeting
                    await view_schedule_to_client(message, state) 
                else:
                    # переходим в заполнение order note
                    for i in range(6):
                        await FSM_Client_tattoo_order.next() # -> load_tattoo_order_note
                        
                    await bot.send_message(message.from_id,   
                        f'🌿 А теперь введите что-нибудь о своем тату!'\
                        ' Чем подробнее описание тату, тем лучше! \n\n'\
                        f'➡️ Или нажмите \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
                        reply_markup= kb_client.kb_no_tattoo_note_from_client)
            
        elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
            await state.finish()
            await bot.send_message(message.from_id, 
                MSG_BACK_TO_HOME, reply_markup=kb_client.kb_client_main)
        
        elif any(text in message.text for text in LIST_BACK_COMMANDS):
            await FSM_Client_tattoo_order.previous() # -> get_choice_tattoo_place
            await bot.send_message(message.from_id,  f'{MSG_CLIENT_GO_BACK}'\
                '🗾 Выбери место для своего тату',
                reply_markup= kb_client.kb_place_for_tattoo)
        else:
            await bot.send_message(message.from_id,  f'📎 Пожалуйста, Отправьте фотографию через файлы')
            
    if message.content_type == 'photo':
        async with state.proxy() as data:
            data['tattoo_place_photo'].append(
                TattooPlacePhoto(
                    order_number = data['tattoo_order_number'], 
                    photo = message.photo[0].file_id,
                    telegram_user_id= message.from_id
                )
            )
            data['client_add_tattoo_place_photo'] = True
            
            tattoo_place_file_counter = data['tattoo_place_file_counter']
            data['tattoo_place_file_counter'] = message.media_group_id
            
        if tattoo_place_file_counter != data['tattoo_place_file_counter']:
            async with state.proxy() as data:
                tattoo_place_file_counter = data['tattoo_place_file_counter']
            
            await bot.send_message(message.from_id, 
                '📷 Отлично, ты добавил(а) фотографию места для своего тату!')
            await bot.send_message(message.from_id, MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY, 
                reply_markup= kb_client.kb_yes_no)
    
    elif message.content_type == 'video_note':
        async with state.proxy() as data:
            data['tattoo_place_video_note'].append(
                TattooPlaceVideoNote(
                    order_number = data['tattoo_order_number'], 
                    video = message.video_note.file_id,
                    telegram_user_id= message.from_id
                )
            )
        
        await bot.send_message(message.from_id, 
            '📷 Отлично, ты добавил(а) видеосообщение места для своего тату!')
        await bot.send_message(message.from_id, MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY, 
            reply_markup= kb_client.kb_yes_no)
        
    elif message.content_type == 'video':
        async with state.proxy() as data:
            data['tattoo_place_video'].append(
                TattooPlaceVideo(
                    order_number = data['tattoo_order_number'], 
                    video = message.video.file_id,
                    telegram_user_id= message.from_id
                )
            )
            tattoo_place_file_counter = data['tattoo_place_file_counter']
            data['tattoo_place_file_counter'] = message.media_group_id
            
        if tattoo_place_file_counter != data['tattoo_place_file_counter']:
            async with state.proxy() as data:
                tattoo_place_file_counter = data['tattoo_place_file_counter']
            await bot.send_message(message.from_id, 
                '📷 Отлично, ты добавил(а) видео места для своего тату!')
            await bot.send_message(message.from_id, MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY, 
                reply_markup= kb_client.kb_yes_no)


# -----------------------------------get_size_tattoo_from_galery---------------------------------
# попадаем сюда, только если тату из галереи, и нужно уточнить размер тату у клиента
async def get_size_tattoo_from_galery(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        sizes_lst = data['sizes_lst']
        
    if message.text.lower() == kb_client.another_size:
        async with state.proxy() as data:
            data['next_menu_another_size'] = True
            
        await bot.send_message(message.from_id, '❔ Какой размер тату вы хотели бы?',
            reply_markup = kb_client.kb_another_size)
        
    elif any(text in message.text for text in sizes_lst):
        async with state.proxy() as data:
            data['tattoo_size'] = message.text[:-1]
            data['next_menu_another_size'] = False
            tattoo_type = data['tattoo_type']
            
        await bot.send_message(message.from_id, 
            f'📏 Отлично, вы указали размер тату равным {message.text[:-1]}')
        
        if tattoo_type.lower() == kb_admin.price_lst_types['constant_tattoo']:
            await FSM_Client_tattoo_order.next() #! -> choice_tattoo_order_date_and_time_meeting
            await view_schedule_to_client(message, state)
            
        else:
            for i in range(5):
                await FSM_Client_tattoo_order.next() #! -> load_tattoo_order_note
                
            await bot.send_message(message.from_id,
                f'🌿 А теперь введите что-нибудь о своем тату! '\
                'Чем подробнее описание тату, тем лучше! \n\n'\
                f'➡️ Или нажмите \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
                reply_markup= kb_client.kb_no_tattoo_note_from_client
            )
        
    elif any(text in message.text for text in LIST_CANCEL_COMMANDS): # отмена
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup=kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS): # назад
        async with state.proxy() as data:
            next_menu_another_size = data['next_menu_another_size']
            client_add_tattoo_place_photo = data['client_add_tattoo_place_photo']
            data['client_add_tattoo_place_photo'], data['next_menu_another_size'] = False, False
            
        if next_menu_another_size == False:
            if client_add_tattoo_place_photo:
                await FSM_Client_tattoo_order.previous() # -> get_photo_place_for_tattoo
                await bot.send_message(message.from_id,   f'{MSG_CLIENT_GO_BACK}'\
                    '📎 Отправьте фото части тела, на котором будет тату, пожалуйста',
                    reply_markup= kb_client.kb_back_cancel)
            else:
                for i in range(2):
                    await FSM_Client_tattoo_order.previous() # -> get_choice_tattoo_place
                    
                await bot.send_message(message.from_id,  f'{MSG_CLIENT_GO_BACK}'\
                    '❔ Хотите указать место, где будет располагаться тату?',
                    reply_markup= kb_client.kb_choice_place_tattoo)
        else:
            async with state.proxy() as data:
                kb_client_size_tattoo = data['kb_client_size_tattoo']
            
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
                reply_markup= kb_client_size_tattoo)
    else:
        await bot.send_message(message.from_id,  MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# -------------------------------choice_tattoo_order_date_and_time_meeting------------------------
# choice_tattoo_place ->-> choice_tattoo_order_date_and_time_meeting -> next_choice_tattoo_order_date_meeting
# get_size_tattoo_from_galery -> choice_tattoo_order_date_and_time_meeting ->-> load_datemeeting
async def choice_tattoo_order_date_and_time_meeting(message: types.Message, state: FSMContext):
    ''' #! перехода в это условие нет, т.к. пользователь не будет выставлять свою дату
    if message.text == 'Хочу выбрать свою дату':
        for i in range(2):
            await FSM_Client_tattoo_order.next() # -> load_datemeeting
        await bot.send_message(message.from_id,  'Хорошо, а теперь выбери свою дату, '\
            'когда тебе будет удобно сделать тату 🗓',
            reply_markup = await DialogCalendar().start_calendar() ) '''
        
    if any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id,
            MSG_BACK_TO_HOME, reply_markup= kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS):
        async with state.proxy() as data:
            tattoo_body_place = data['tattoo_body_place']
            tattoo_from_galery = data['tattoo_from_galery']
            
        await FSM_Client_tattoo_order.previous() # -> get_size_tattoo_from_galery
        if tattoo_from_galery:
            async with state.proxy() as data:
                kb_client_size_tattoo = data['kb_client_size_tattoo']
            
            await bot.send_message(message.from_id, 
                f'{MSG_CLIENT_GO_BACK}{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
                reply_markup= kb_client_size_tattoo)

        elif tattoo_body_place == "Без места для тату":
            for i in range(2):
                await FSM_Client_tattoo_order.previous() # -> get_choice_tattoo_place
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}')
            await bot.send_message(message.from_id,'❔ Хотите определить место, где будет располагаться тату?',
                reply_markup = kb_client.kb_choice_place_tattoo)
        else:
            for i in range(2):
                await FSM_Client_tattoo_order.previous() # -> get_choice_tattoo_place
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}'\
                '❔ Хотите добавить фотографию места, где будет располагаться тату?',
                reply_markup = kb_client.kb_choice_get_photo_for_place_tattoo)
            
    elif message.text in kb_client.next_action_lst: # 'Далее ➡️'
        async with state.proxy() as data:
            data['date_meeting'] = None
            data['event_type_creation'] = 'from_schedule'
            data['start_date_time'] = None
            data['end_date_time'] = None
            data['schedule_id'] = []
            
        for i in range(4):
            await FSM_Client_tattoo_order.next() # -> load_tattoo_order_note
            
        await bot.send_message(message.from_id,
            f'🌿 А теперь введите что-нибудь о своем тату! '\
            'Чем подробнее описание тату, тем лучше! \n\n'\
            f'➡️ Или нажмите \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
            reply_markup= kb_client.kb_no_tattoo_note_from_client
        )
        
    else:
        async with state.proxy() as data:
            data['event_type_creation'] = 'from_schedule'
            schedule_lst = data['date_free_kb_items_list']
            
            if message.text in schedule_lst: # если выбираем конкретную дату из календаря  
                # f"{month} {date.start_datetime.strftime('%d/%m/%Y c %H:%M')} по 
                # {date.end_datetime.strftime('%H:%M')} 🗓"
                # Февраль 06/02/2023 c 14:00:00 по 17:00:00
                with Session(engine) as session:
                    schedule_event = session.scalars(select(ScheduleCalendar)
                        .where(ScheduleCalendar.start_datetime == datetime.strptime(
                            f"{message.text.split()[1]} {message.text.split()[3]}", '%d/%m/%Y %H:%M'))
                        .where(ScheduleCalendar.end_datetime == datetime.strptime(
                            f"{message.text.split()[1]} {message.text.split()[5]}", '%d/%m/%Y %H:%M'))
                    ).one()
                data['date_meeting'] = schedule_event.start_datetime
                data['start_date_time'] = schedule_event.start_datetime.strftime('%H:%M')
                data['end_date_time'] = schedule_event.end_datetime.strftime('%H:%M')
                data['schedule_id'] = schedule_event.id
                
                for i in range(4):
                    await FSM_Client_tattoo_order.next() # -> load_tattoo_order_note
                    
                await bot.send_message(message.from_id,   
                    f"🌿 Прекрасно! 📅 Вы выбрали дату "\
                    f"{data['date_meeting'].strftime('%d/%m/%Y с %H:%M')} до {data['end_date_time']}")
                
                await bot.send_message(message.from_id, 
                    f'🌿 А теперь введите что-нибудь о своем тату! '\
                    'Чем подробнее описание тату, тем лучше!\n\n'\
                    f'➡️ Или нажмите \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
                    reply_markup= kb_client.kb_no_tattoo_note_from_client
                )
                
            else:
                await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def next_choice_tattoo_order_date_meeting(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date_meeting'] = message.text
    for i in range(2):
        await FSM_Client_tattoo_order.next() #-> load_tattoo_order_note
    await bot.send_message(message.from_id,  
        f'📅 Прекрасно, дата встречи теперь {message.text}!')
    
    await bot.send_message(message.from_id, 
        '🕒 А теперь введите удобное для вас время.',
        reply_markup= await FullTimePicker().start_picker())


# перехода нет, т.к. пользователь пока не будет выставлять свою дату
# выбираем дату заказа
@dp.callback_query_handler(dialog_cal_callback.filter(), state=FSM_Client_tattoo_order.date_meeting)
async def load_datemeeting(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data) # type: ignore
    async with state.proxy() as data:
        user_id = data['telegram']
        
    if selected:
        await callback_query.message.answer(f'Вы выбрали {date.strftime("%d/%m/%Y")}')
        if date > datetime.now(): 
            async with state.proxy() as data:
                data['date_meeting'] = date #  message.text
                data['event_type_creation'] = 'from user'
            await FSM_Client_tattoo_order.next()
            await bot.send_message(user_id,
                f'📅 Прекрасно, дата встречи теперь {date.strftime("%d/%m/%Y")}! \n\n')
            
            await bot.send_message(user_id,
                '🕒 А теперь введите удобное для вас время.',
                reply_markup= await FullTimePicker().start_picker())
        else:
            await bot.send_message(user_id, f'{MSG_NOT_CORRECT_DATE_NOW_LESS_CHOICEN}'\
                f'{MSG_LET_CHOICE_NORMAL_DATE}')


# перехода нет, т.к. пользователь пока не будет выставлять свою дату
# выбираем время заказа
@dp.callback_query_handler(full_timep_callback.filter(), 
    state=FSM_Client_tattoo_order.date_time)
async def process_hour_timepicker(callback_query: CallbackQuery,
    callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data) # type: ignore
    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время для тату в {r.time.strftime("%H:%M")} ',
        )
        # await callback_query.message.delete_reply_markup()
        async with state.proxy() as data:
            data['start_date_time'] = r.time.strftime("%H:%M")
            data['end_date_time'] = str(int(r.time.strftime("%H")) + 3) + \
                str(r.time.strftime(":%M"))
            
            user_id = data['telegram']
            start_datetime= datetime.strptime(
                f"{data['date_meeting'].strftime('%Y-%m-%d')} {data['start_date_time']}", 
                '%Y-%m-%d %H:%M'
            )
            
            end_datetime= datetime.strptime(
                f"{data['date_meeting'].strftime('%Y-%m-%d')} {data['end_date_time']}", 
                '%Y-%m-%d %H:%M'
            )
            
            with Session(engine) as session:
                new_schedule_event = ScheduleCalendar(
                    start_datetime= start_datetime,
                    end_datetime= end_datetime,
                    status= 'Занят',
                    event_type= data['order_type']
                )
                session.add(new_schedule_event)
                session.commit()
            
        await FSM_Client_tattoo_order.next()
        await bot.send_message(user_id,
            f"📅 Прекрасно! Вы выбрали дату {data['date_meeting'].strftime('%d/')} и "\
            f"🕒 время {r.time.strftime('%H:%M')}."
        )
        await bot.send_message(user_id, 
            f'🌿 А теперь введите что-нибудь о своем тату! Чем подробнее описание тату, тем лучше! \n\n'\
            f'➡️ Или нажмите \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
            reply_markup= kb_client.kb_no_tattoo_note_from_client
        )


async def load_tattoo_order_note(message: types.Message, state: FSMContext):
    if any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup=kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS): # идем назад
        async with state.proxy() as data:
            tattoo_type = data['tattoo_type']
            if tattoo_type == kb_admin.price_lst_types['constant_tattoo']:
            
                if data['event_type_creation'] == 'from_schedule':
                    await view_schedule_to_client(message, state) # выводим календарь
                    await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}'\
                        '❔ Какую дату ты Хотите выбрать из предложенных?')
                    
                    for i in range(4):
                        # -> choice_tattoo_order_date_and_time_meeting
                        await FSM_Client_tattoo_order.previous() 

                elif data['event_type_creation'] == 'from user':
                    await FSM_Client_tattoo_order.previous()
                    await bot.send_message(message.from_id,  f'{MSG_CLIENT_GO_BACK}'\
                        '🕒 введите удобное для вас время.',
                        reply_markup = await FullTimePicker().start_picker())
            else: # если тату переводное
                # если тату из галереи
                tattoo_from_galery = data['tattoo_from_galery']
                tattoo_body_place = data['tattoo_body_place']
                if tattoo_from_galery:
                    for i in range(5):
                        await FSM_Client_tattoo_order.previous() #-> get_size_tattoo_from_galery
                    
                    async with state.proxy() as data:
                        kb_client_size_tattoo = data['kb_client_size_tattoo']
                    
                    await bot.send_message(message.from_id, 
                        f'{MSG_CLIENT_GO_BACK}{MSG_CLIENT_CHOICE_TATTOO_SIZE}',
                        reply_markup= kb_client_size_tattoo)
                else:
                    for i in range(7):
                        await FSM_Client_tattoo_order.previous() #-> get_choice_tattoo_place
                    
                    if tattoo_body_place == "Без места для тату":
                        await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}'\
                            '❔ Хотите определить место, где будет располагаться тату?',
                            reply_markup = kb_client.kb_choice_place_tattoo)
                        
                    else:
                        await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}'\
                            '❔ Хотите добавить фотографию места, где будет располагаться тату?',
                            reply_markup = kb_client.kb_choice_get_photo_for_place_tattoo)
                        
    else:
        async with state.proxy() as data:
            if message.text in kb_client.no_tattoo_note_from_client:
                data['tattoo_note'] = 'Без описания тату'
            else:
                data['tattoo_note'] = message.text
            
            data['creation_date'] = datetime.now()
            data['username'] = message.from_user.full_name
            split_numbers = 0
            if ' ' in data['tattoo_size']:
                slpiting_symbol = ' '
                split_numbers = 2
            else:
                slpiting_symbol = 'x'
                split_numbers = 1
                
            min_size = int(data['tattoo_size'].split(slpiting_symbol)[0])
            max_size = int(data['tattoo_size'].split(slpiting_symbol)[split_numbers]) 
            # Определяем цену тату
            price = Session(engine).scalars(select(OrderPriceList)
                .where(OrderPriceList.min_size == min_size)
                .where(OrderPriceList.max_size == max_size)).all()
                
            #! Выставляем цену в None, если у нас в прайс-листе не таких размеров
            #! эту цену потом нужно будет заполнить админу
            data['tattoo_price'] = None if price == [] else price[0].price 
            
        await FSM_Client_tattoo_order.next()
        await bot.send_message(message.from_id, f'{MSG_CLIENT_WANT_TO_FILL_ORDER_NOTE}',
            reply_markup= kb_client.kb_yes_no)


async def fill_tattoo_order_table(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        #? TODO Стоит ли добавлять в таблицу tattoo_items тату от клиента?
        #! Ошибка: - Название: derhtyrjtyu
        #! - Цена: 15 000
        #! - Цвет: Мне нечего добавить 🙅‍♂️
        #! - Описание: Цветное
        #! - Создатель: client
        
        new_user = False
        with Session(engine) as session:
            new_table_items = []
            order_photo_lst = []
            tattoo_photo_lst = []
            """
                Определяем новое Тату - TattooItemPhoto
            """
            
            if data['tattoo_photo_tmp_lst'] != '':
                print(f"{data['tattoo_photo_tmp_lst']}")
                for photo in data['tattoo_photo_tmp_lst'].split('|'):
                    # при split('|') возникает еще одна переменная '', ее необходимо не добавлять
                    if photo != '': 
                        tattoo_photo_lst.append(TattooItemPhoto(
                            photo= photo,
                            tattoo_item_name= data['tattoo_name'])
                        )
                        order_photo_lst.append(OrderPhoto(
                            order_number=       data['tattoo_order_number'],
                            telegram_user_id=   message.from_id, 
                            photo=              photo)
                        )
            else:
                tattoo_photo_lst.append(TattooItemPhoto(
                    photo= None,
                    tattoo_item_name= data['tattoo_name'])
                )
                
            creator = "admin" if data['tattoo_from_galery'] else "client"
            if creator != 'admin':
                new_tattoo_item = TattooItems(
                    name=    data['tattoo_name'],
                    photos=  tattoo_photo_lst,
                    price=   data['tattoo_price'],
                    note=    data['tattoo_note'],
                    colored= data['tattoo_colored'],
                    creator= creator   
                )
                new_table_items.append(new_tattoo_item)
            
            """
                Определяем нового пользователя, если его нет в базе - User
            """
            user = []
            users = session.scalars(select(User)).all()
            if users != []:
                user = session.scalars(select(User).where(
                    User.telegram_id == message.from_id)).all()
                
            if user == [] or users == []:
                new_user = User(
                    name=           message.from_user.full_name,
                    telegram_name = f'@{message.from_user.username}',
                    telegram_id=    message.from_id,
                    phone=          None
                )
                session.add(new_user)
                session.commit()
                new_user = True
                
    async with state.proxy() as data:
        
        with Session(engine) as session:
            schedule_item = None
            if data['schedule_id'] not in [None, []]:
                schedule_item = [ScheduleCalendarItems(
                    schedule_id=  data['schedule_id'],
                    order_number= data['tattoo_order_number'])
                ]
            
            new_tattoo_order = Orders( 
                order_type=             data['tattoo_type'],
                order_name=             data['tattoo_name'],
                user_id=                message.from_id,
                order_photo=            order_photo_lst,
                tattoo_size=            data['tattoo_size'],
                tattoo_note=            data['tattoo_note'],
                order_note=             data['order_note'],
                order_state=            data['order_state'],
                order_number=           data['tattoo_order_number'],
                creation_date=          data['creation_date'],
                price=                  data['tattoo_price'],
                check_document=         data['check_document'],
                username=               data['username'],
                schedule_id=            schedule_item,
                colored=                data['tattoo_colored'],
                # tattoo_details_number=  data['tattoo_details_number'],
                bodyplace=              data['tattoo_body_place'],
                tattoo_place_photo=     data['tattoo_place_photo'],
                tattoo_place_video_note=data['tattoo_place_video_note'],
                tattoo_place_video=     data['tattoo_place_video']
            )
            new_table_items.append(new_tattoo_order)
            session.add_all(new_table_items)
            session.commit()
            
        with Session(engine) as session:   
            status = data['order_state']
            tattoo_order_number = data['tattoo_order_number'] 
            event_body_text = \
                f"Название тату: {data['tattoo_name']}\n"\
                f"Описание тату: {data['tattoo_note']}\n"\
                f"Описание заказа: {data['order_note']}\n"\
                f"Имя клиента: {message.from_user.full_name}\n"\
                f"Телеграм клиента: @{message.from_user.username}"
            # если заказ на постоянную татуировку    
            if data['tattoo_type'] == kb_admin.price_lst_types['constant_tattoo']: 
                
                if data['schedule_id'] not in [None, []]:
                    schedule_event = session.scalars(select(ScheduleCalendar)
                        .where(ScheduleCalendar.id == data['schedule_id'])).one()
                    schedule_event.status = 'Занят'
                    session.commit()
                    
                # TODO дополнить id Шуны и добавить интеграцию с Google Calendar !!!
                if DARA_ID != 0:
                    if data['date_meeting'] is not None:
                        await bot.send_message(DARA_ID, f"Дорогая Тату-мастерица! \n"\
                            f"🕸 Поступил новый заказ на тату под номером {tattoo_order_number}!\n"\
                            f"📃 Статус заказа: {status}. \n"
                            f"🕒 Дата встречи: {data['date_meeting']} в {data['start_date_time']} до "\
                            f"{data['end_date_time']}\n"
                            f"💬 Имя клиента: {message.from_user.full_name}\n"\
                            f"💬 Телеграм клиента: @{message.from_user.username}")
                        
                        event = await obj.add_event(
                            CALENDAR_ID,
                            f'Новый тату заказ № {tattoo_order_number}',
                            f'{event_body_text}',
                            data['date_meeting'].strftime(f"%Y-%m-%dT{data['start_date_time']}:00"),
                            data['date_meeting'].strftime(f"%Y-%m-%dT{data['end_date_time']}:00")
                        )
                    else:
                        await bot.send_message(DARA_ID, f"Дорогая Тату-мастерица! \n"\
                            f"🕸 Поступил новый заказ на тату под номером {tattoo_order_number}! \n"\
                            f"📃 Статус заказа: {status}. \n"\
                            f"🕒 Дата встречи неизвестна. Необходимо договориться с клиентом о дате встречи.\n"\
                            f"💬 Имя клиента: {message.from_user.full_name}\n"\
                            f"💬 Телеграм клиента: @{message.from_user.username}")
                    
                        event = await obj.add_event(
                            CALENDAR_ID,
                            f'Новый тату заказ № {tattoo_order_number}',
                            f'{event_body_text}\n'\
                            f'Дата встречи неизвестна. Необходимо договориться с клиентом о дате встречи.',
                            f'{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}',
                            f'{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}')
                
            else: # если заказ на переводную татуировку
                if DARA_ID != 0:
                    await bot.send_message(DARA_ID, 
                        f'Дорогая Тату-мастерица! '\
                        f'🕸 Поступил новый заказ на переводное тату под номером {tattoo_order_number}! '\
                        f'📃 Статус заказа: {status}. \n'\
                        f"💬 Имя клиента: {message.from_user.full_name}\n"\
                        f'💬 Телеграм клиента: @{message.from_user.username}')
                    
                    event = await obj.add_event(CALENDAR_ID,
                        f'Новый переводное тату, заказ № {tattoo_order_number}',
                        event_body_text,
                        f'{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}',
                        f'{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}'  
                    )
            await state.finish()
        
        if new_user:
            await bot.send_message(message.chat.id, 
                f'🎉 Ваш заказ тату под номером {tattoo_order_number} почти оформлен!\n\n'\
                f'{MSG_TO_CHOICE_CLIENT_PHONE}',
                reply_markup= kb_client.kb_phone_number)
            await FSM_Client_username_info.phone.set()
        else:
            await bot.send_message(message.chat.id, 
                f'🎉 Ваш заказ тату под номером {tattoo_order_number} оформлен!')
            
            await bot.send_message(message.chat.id, 
                f'{MSG_THANK_FOR_ORDER}\n'
                f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_client.kb_client_main)


async def choiсe_tattoo_order_desctiption(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            data['client_fill_order_note'] = True
            
        await bot.send_message(message.from_id, '❕ Хорошо! Опиши, чего именно ты Хотите,'\
            'и какие идеи у вас есть, это очень важно!',
            reply_markup= kb_client.kb_back_cancel)
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            data['order_note'] = 'Без описания заказа'
            data['client_fill_order_note'] = False
            
        await bot.send_message(message.from_id, f'🚫 Хорошо, пока оставим заказ без описания')
        
        await fill_tattoo_order_table(message, state)

    elif any(text in message.text for text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME):
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup=kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS):
        async with state.proxy() as data:
            client_fill_order_note = data['client_fill_order_note']
            
        if client_fill_order_note:
            await bot.send_message(message.from_id,
                f'{MSG_CLIENT_GO_BACK}{MSG_CLIENT_WANT_TO_FILL_ORDER_NOTE}',
                reply_markup= kb_client.kb_yes_no)
        else:
            await FSM_Client_tattoo_order.previous() # -> load_tattoo_order_note
            await bot.send_message(message.from_id,  f'{MSG_CLIENT_GO_BACK}'\
                f'🌿 А теперь введите что-нибудь о своем тату!\n'
                'Чем подробнее описание тату, тем лучше!\n\n'\
                f'➡️ Или нажмите \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
                reply_markup= kb_client.kb_no_tattoo_note_from_client
            )
        
    else:
        async with state.proxy() as data:
            client_fill_order_note = data['client_fill_order_note']
            data['client_fill_order_note'] = False
            
        if client_fill_order_note == True:
            async with state.proxy() as data:
                data['order_note'] = message.text
            await fill_tattoo_order_table(message, state)
        else:
            await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


#---------------------------------------------GET VIEW TATTOO ORDER--------------------------------------
async def send_to_client_view_tattoo_order(message: types.Message, orders: ScalarResult["Orders"]):
    for order in orders:
        msg = f'Тату заказ № {order.order_number} от {order.creation_date}\n'
        
        if order.order_type == kb_admin.price_lst_types['constant_tattoo']:
            i = 0
            if order.schedule_id is not None:
                
                with Session(engine) as session:
                    schedule_lst = session.scalars(select(ScheduleCalendarItems)
                        .where(ScheduleCalendarItems.order_number == order.order_number)).all()
                for schedule in schedule_lst:
                    msg += "🕒 Даты встреч:\n" if len(schedule_lst) > 1 else "🕒 Дата встречи: "
                    with Session(engine) as session:
                        i += 1
                        # определяем статус ивента 
                        status = session.get(ScheduleCalendar, schedule.schedule_id).status
                        status = 'Скоро встреча' if status == 'Занят' else 'Прошел'
                        start_time = session.get(ScheduleCalendar, schedule.schedule_id
                            ).start_datetime.strftime('%d/%m/%Y с %H:%M')
                        end_time = session.get(ScheduleCalendar, schedule.schedule_id
                            ).end_datetime.strftime('%H:%M')
                        time = f"{start_time} до {end_time}"
                        msg += \
                            f"\t{i}) {time} - {status}\n" if len(schedule_lst) > 1 else f"{time} - {status}\n"
            else:
                msg += \
                    f"🕒 Дата и время встречи не выбраны - свободных ячеек в календаре нет.\n"
        msg += \
            f'🪴 Тип тату: {order.order_type}\n'\
            f'🍃 Имя: {order.order_name}\n'\
            f'📏 Размер: {order.tattoo_size}\n'\
            f'📜 Описание тату: {order.tattoo_note}\n' \
            f'💬 Описание заказа: {order.order_note}\n'\
            f'🎨 {order.colored} тату\n'\
            f'👤 Местоположение тату: {order.bodyplace}\n'
            #f'💰 Цена: {order.price]}'
        
        if order.order_state in list(STATES["closed"].values()):
            msg += f'❌ Состояние заказа: {order.order_state}\n'
        else:
            msg += f'📃 Состояние заказа: {order.order_state}\n'
        
        
        with Session(engine) as session:
            check_document_lst = session.scalars(select(CheckDocument)
                .where(CheckDocument.order_number == order.order_number)).all()
        if check_document_lst != []:
            for doc in check_document_lst:
                if doc.doc in ['Чек не добавлен', '-', None, '']:
                    msg += '⭕️ Чек не добавлен\n'
                else:
                    msg += '🍀 Чек добавлен\n'
        else:
            msg += '⭕️ Чек не добавлен\n'
            
        media = []
        tattoo_photos = Session(engine).scalars(select(OrderPhoto)
            .where(OrderPhoto.order_number == order.order_number)).all()
        
        body_photos = Session(engine).scalars(select(TattooPlacePhoto)
            .where(TattooPlacePhoto.order_number == order.order_number)).all()
        
        tattoo_place_video = Session(engine).scalars(select(TattooPlaceVideo)
            .where(TattooPlaceVideo.order_number == order.order_number)).all()
            
        for photo_tattoo in tattoo_photos:
            media.append(types.InputMediaPhoto(photo_tattoo.photo, msg))
                
        # body photo
        for photo_bodyplace in body_photos:
            media.append(types.InputMediaPhoto(photo_bodyplace.photo,
                f'👤 Местоположение тату: {order.bodyplace}'))
            
        if tattoo_place_video != []:
            for video_bodyplace in tattoo_place_video:
                media.append(types.InputMediaVideo(video_bodyplace.video))
                    
        if media != []:
            await bot.send_chat_action(message.chat.id, types.ChatActions.UPLOAD_DOCUMENT)
            await bot.send_media_group(message.chat.id, media= media)
            if len(media) > 1:
                await bot.send_message(message.from_id, msg)

        # tattoo_place_video_note
        for video_note in order.tattoo_place_video_note:
            await bot.send_video_note(message.chat.id, video_note.video)


class FSM_Client_send_to_client_view_tattoo_order(StatesGroup):
    get_order_number = State()


#/посмотреть_мои_тату_заказы
async def get_clients_tattoo_order(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(select(Orders)
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_type.in_(["переводное тату", "постоянное тату"]))).all()
    
    if orders == []:
        await bot.send_message(message.from_id, f'⭕️ У вас пока нет тату заказов.')
        await bot.send_message(message.from_id, f'{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
    else:
        await FSM_Client_send_to_client_view_tattoo_order.get_order_number.set()
        kb = ReplyKeyboardMarkup(resize_keyboard= True)
        for order in orders:
            kb.add(
                KeyboardButton(f"Тату заказ №{order.order_number} \"{order.order_name}\" {order.order_state}")
            )
        kb.add(KeyboardButton(kb_client.cancel_lst[0]))
        await bot.send_message(message.from_id, MSG_WHICH_ORDER_DO_CLIENT_WANT_TO_SEE,
            reply_markup= kb)


async def get_tattoo_order_number_to_view(message: types.Message, state: FSMContext):  
    with Session(engine) as session:
        orders = session.scalars(select(Orders)
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_type.in_(["переводное тату", "постоянное тату"]))).all()
    kb_answer_lst = []
    for order in orders:
        kb_answer_lst.append(f"Тату заказ №{order.order_number} \"{order.order_name}\" {order.order_state}")
        
    if message.text in kb_answer_lst:
        with Session(engine) as session:
            orders = session.scalars(select(Orders)
                .where(Orders.order_number == message.text.split()[2][1:])).all()
            
            await send_to_client_view_tattoo_order(message, orders)
    
        await bot.send_message(message.from_user.id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_client.kb_choice_order_view)
        await state.finish()
        
    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(message.from_id, f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME }",
            reply_markup=kb_client.kb_choice_order_view)
        
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


#/добавить_фото_в_тату_заказ
class FSM_Client_get_new_photo_to_tattoo_order(StatesGroup):
    get_order_id = State() 
    get_photo_type = State() 
    get_new_photo = State()
    
    
async def get_new_photo_to_tattoo_order(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(select(Orders)
        .where(Orders.order_state.not_in(list(STATES["closed"].values())))
        .where(Orders.username == message.from_user.full_name)
        .where(Orders.order_type.in_(['постоянное тату', 'переводное тату']))).all()
    
    if orders == []:
        await bot.send_message(message.from_id, 
            f'⭕️ У вас пока нет открытых тату заказов.\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_client.kb_choice_order_view)
    else:
        kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
        for order in orders:
            creation_date = order.creation_date.strftime("%d/%m/%Y")
            order_number = order.order_number
            kb_orders.add(f'Тату заказ №{order_number} от {creation_date}')
        kb_orders.add(kb_client.back_lst[0]).add(kb_client.cancel_lst[0])
        await FSM_Client_get_new_photo_to_tattoo_order.get_order_id.set()
        await bot.send_message(message.from_id, '❔ Для какого заказа Хотите добавить фотографию?',
            reply_markup= kb_orders)


async def get_order_id_to_add_new_photo(message: types.Message, state: FSMContext): 
    with Session(engine) as session:
        orders = session.scalars(select(Orders)
            .where(Orders.order_state.not_in(list(STATES["closed"].values())))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_type.in_(['постоянное тату', 'переводное тату']))).all()
    
    kb_orders_lst = []
    for order in orders:
        creation_date = order.creation_date.strftime("%d/%m/%Y") # TODO нужно получить %d/%m/%Y
        order_number = order.order_number
        kb_orders_lst.append(f'Тату заказ №{order_number} от {creation_date}')
        
    if message.text in kb_orders_lst:
        async with state.proxy() as data:
            data['tattoo_order_number'] = message.text.split()[2][1:]
            data['orders'] = orders
        await FSM_Client_get_new_photo_to_tattoo_order.next() # -> get_photo_type
        await bot.send_message(message.from_id, 
            '❔ Ты Хотите добавить фотографию для эскиза или фотографию изображения тела?',
            reply_markup= kb_client.kb_client_choice_add_photo_type)
        
    elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, 
            f'{MSG_CANCEL_ACTION}{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)


async def get_photo_type(message: types.Message, state: FSMContext):
    # "Добавить фото для эскиза 🎨", "Добавить фото части тела 👤"
    if message.text in list(kb_client.client_choice_add_photo_type.values()):
        async with state.proxy() as data:
            # пользователь вносит сюда выбор типа фотографии: фотографию эскиза тату или тела
            data['photo_type'] = message.text.split()[-1] 
        await FSM_Client_get_new_photo_to_tattoo_order.next() #! -> get_new_photo
        msg = '📎 Хорошо, добавь новое фото в заказ через файлы, пожалуйта.\n\n'\
            '❕ Можно добавлять сразу несколько файлов.\n\n'
            
        if message.text.split()[-1] == '👤':
            msg += '❕ Также ты можешь добавить видео или видео-заметки (если с телефона)'
            
        await bot.send_message(message.from_id, msg, reply_markup= kb_client.kb_back_cancel)
        
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Client_get_new_photo_to_tattoo_order.previous() #! -> get_order_id_to_add_new_photo
        kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
        async with state.proxy() as data:
            orders = data['orders']
        
        for order in orders:
            creation_date = order.creation_date.strftime("%H:%M %d/%m/%Y")
            
            kb_orders.add(f'Тату заказ № {order.order_number} от {creation_date}')
        kb_orders.add(kb_client.back_lst[0]).add(kb_client.cancel_lst[0])
        await bot.send_message(message.from_id, '❔ Для какого заказа Хотите добавить фотографию?',
            reply_markup= kb_orders)
        
    elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, f'{MSG_CANCEL_ACTION}{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
        
    else:
        await bot.send_message(message.from_id, MSG_PLS_SEND_TATTOO_PHOTO_OR_CANCEL_ACTION)


async def get_new_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        tattoo_order_number = data['tattoo_order_number']
        photo_type = data['photo_type']
        
    if message.content_type == 'photo':
        new_photo = f'{message.photo[0].file_id}'    
        photo_type = 'tattoo_photo' if photo_type == '🎨' else 'tattoo_place_photo'
        with Session(engine) as session:
            order = session.scalars(select(Orders)
                .where(Orders.order_number == tattoo_order_number)).one()
            if photo_type == 'tattoo_photo':
                order.order_photo.append(OrderPhoto(
                    order_number= tattoo_order_number, 
                    telegram_user_id= message.from_id, 
                    photo= new_photo)
                )
            elif photo_type == 'tattoo_place_photo':
                order.tattoo_place_photo.append(TattooPlacePhoto(
                    order_number = tattoo_order_number, 
                    # order_id=order_id, 
                    photo= new_photo, 
                    telegram_user_id= message.from_id)
                )
            session.commit()
        await state.finish()
        await bot.send_message(message.from_id,
            f'🎉 Отлично, ты обновил фотографии в заказе {tattoo_order_number}!\n\n'\
            f'{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
        
    elif message.content_type == 'video_note':
        with Session(engine) as session:
            order = session.scalars(select(Orders)
                .where(Orders.order_number == tattoo_order_number)).one()
            order.tattoo_place_video_note.append(TattooPlaceVideoNote(
                order_number = tattoo_order_number, 
                # order_id=order_id, 
                video = message.video_note.file_id, 
                utelegram_user_idser=message.from_id)
            )
                
            session.commit()
        await state.finish()
        await bot.send_message(message.from_id,
            f'🎉 Отлично, ты обновил фотографии в заказе {tattoo_order_number}!\n\n'\
            f'{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
        
    elif message.content_type == 'video':
        with Session(engine) as session:
            order = session.scalars(select(Orders)
                .where(Orders.order_number == tattoo_order_number)).one()
            order.tattoo_place_video.append(TattooPlaceVideo(
                    order_number= tattoo_order_number, 
                    # order_id=order_id, 
                    video= message.video.file_id, 
                    user= message.from_id)
                )
            session.commit()
        await state.finish()
        await bot.send_message(message.from_id,
            f'🎉 Отлично, ты обновил фотографии в заказе {tattoo_order_number}!\n\n'\
            f'{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
        
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Client_get_new_photo_to_tattoo_order.previous() # -> get_photo_type
        await bot.send_message(message.from_id, 
            '❔ Ты Хотите добавить фотографию для эскиза или фотографию изображения тела?',
            reply_markup= kb_client.kb_client_choice_add_photo_type)
        
    elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, 
            f'{MSG_CANCEL_ACTION}{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
        
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


#-------------------------------------------TATTOO_ORDER----------------------------------
def register_handlers_client_tattoo_order(dp: Dispatcher):
    dp.register_message_handler(start_create_new_tattoo_order,
        Text(equals= kb_client.client_main['client_want_tattoo'], ignore_case=True), state=None)
    
    dp.register_message_handler(start_create_new_tattoo_order,
        commands=['get_tattoo'], state=None)
    dp.register_message_handler(get_client_choice_main_or_temporary_tattoo,
        state=FSM_Client_tattoo_order.client_choice_main_or_temporary_tattoo)
    dp.register_message_handler(load_tattoo_order_photo, content_types=['photo', 'text'],
        state=FSM_Client_tattoo_order.tattoo_order_photo)
    dp.register_message_handler(change_menu_tattoo_from_galery,
        state=FSM_Client_tattoo_order.change_tattoo_from_galery)
    dp.register_message_handler(load_tattoo_order_name, state=FSM_Client_tattoo_order.tattoo_name)
    dp.register_message_handler(load_tattoo_order_size, 
        state=FSM_Client_tattoo_order.tattoo_size)
    dp.register_message_handler(get_choice_colored_or_not, 
        state=FSM_Client_tattoo_order.choice_colored_or_not)
    # dp.register_message_handler(get_choice_number_of_details, 
    # state=FSM_Client_tattoo_order.choice_number_of_details)
    dp.register_message_handler(get_choice_tattoo_place, 
        state=FSM_Client_tattoo_order.get_choice_tattoo_place)
    dp.register_message_handler(get_photo_place_for_tattoo, 
        content_types=['photo', 'document', 'text', 'video', 'video_note'], 
        state=FSM_Client_tattoo_order.choice_tattoo_place)
    dp.register_message_handler(get_size_tattoo_from_galery,
        state=FSM_Client_tattoo_order.choice_size_for_tattoo_from_galery)
    dp.register_message_handler(choice_tattoo_order_date_and_time_meeting,
        state=FSM_Client_tattoo_order.choice_tattoo_order_date_and_time_meeting)
    dp.register_message_handler(next_choice_tattoo_order_date_meeting,
        state=FSM_Client_tattoo_order.next_choice_tattoo_order_date_meeting)
    # dp.register_message_handler(load_datemiting, state=FSM_Client_tattoo_order.date_meeting)
    dp.register_message_handler(load_tattoo_order_note, state=FSM_Client_tattoo_order.tattoo_note)
    dp.register_message_handler(choiсe_tattoo_order_desctiption,
        state=FSM_Client_tattoo_order.order_desctiption_choiсe)
    # dp.register_message_handler(load_order_desctiption_after_choice,
    # state=FSM_Client_tattoo_order.order_desctiption)
    # dp.register_message_handler(choice_send_check_document_or_not, 
    #   state=FSM_Client_tattoo_order.tattoo_order_choice_sending_check_documents)
    #dp.register_message_handler(load_check_document_to_tattoo_order, content_types=['photo', 'document'], 
    #   state=FSM_Client_tattoo_order.load_check_document_to_tattoo_order)
    
    dp.register_message_handler(get_clients_tattoo_order,
        Text(equals= kb_client.choice_order_view["client_watch_tattoo_order"], ignore_case=True),
        state=None)
    dp.register_message_handler(get_clients_tattoo_order, commands=['посмотреть_мои_тату_заказы'],
        state=None)
    dp.register_message_handler(get_tattoo_order_number_to_view, 
        state=FSM_Client_send_to_client_view_tattoo_order.get_order_number)
    
    
    dp.register_message_handler(get_new_photo_to_tattoo_order,
        Text(equals=kb_client.choice_order_view['client_add_photo_to_tattoo_order'], ignore_case=True),
        state=None)
    dp.register_message_handler(get_new_photo_to_tattoo_order, commands=['добавить_фото_в_тату_заказ'],
        state=None)
    
    dp.register_message_handler(get_order_id_to_add_new_photo, 
        state= FSM_Client_get_new_photo_to_tattoo_order.get_order_id)
    dp.register_message_handler(get_photo_type, 
        state= FSM_Client_get_new_photo_to_tattoo_order.get_photo_type)
    dp.register_message_handler(get_new_photo, content_types=['photo', 'text', 'video', 'video_note'], 
        state= FSM_Client_get_new_photo_to_tattoo_order.get_new_photo)