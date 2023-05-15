
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
from keyboards import kb_client
from handlers.other import *
from handlers.client import CODE_LENTH, ORDER_CODE_LENTH, fill_client_table, \
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
    
    # TODO нужно ли делать оплату тату заказа? Пока прихожу к мысли, что нет 20.02.2023
    tattoo_order_choice_sending_check_documents = State() 
    load_check_document_to_tattoo_order = State()
    

# Начало диалога с пользователем, который хочет добавить новый заказ тату, хочу тату 🕸
async def start_create_new_tattoo_order(message: types.Message):
    # -> get_client_choice_main_or_temporary_tattoo
    await FSM_Client_tattoo_order.client_choice_main_or_temporary_tattoo.set() 
    await bot.send_message(message.from_id,
        '🌿Отлично, давай подберем тебе твою уникальную татуировку!\n\n'\
        f'{MSG_CLIENT_WANT_CURRENT_OR_NOT_TATTOO}',
        reply_markup = kb_client.kb_client_choice_main_or_temporary_tattoo)


async def get_client_choice_main_or_temporary_tattoo(message: types.Message, state: FSMContext):
    if message.text in list(kb_client.choice_main_or_temporary_tattoo.values()):
        # в прайс-листе находится список размеров
        sizes = Session(engine).scalars(select(TattooOrderPriceList))
        kb_client_size_tattoo = ReplyKeyboardMarkup(resize_keyboard=True)
        sizes_lst = []
        for size in sizes:
            sizes_lst.append(f'{size.max_size} - {size.min_size} см2 📏')
            kb_client_size_tattoo.add(f'{size.max_size} - {size.min_size} см2 📏')
        kb_client_size_tattoo.add(kb_client.back_btn).add(kb_client.cancel_btn)
        
        async with state.proxy() as data:
            # tattoo_type = постоянное тату, переводное тату
            data['tattoo_type'] = message.text.split()[0].lower() 
            data['next_menu_look_tattoo_galery'] = False
            data['tattoo_from_galery'] = False
            data['tattoo_photo'] = ''
            data['tattoo_place_photo'] = []
            data['tattoo_order_photo_counter'] = False
            data['tattoo_place_file_counter'] = 4
            data['tattoo_place_video_note'] = ''
            data['tattoo_place_video'] = ''
            data['tattoo_body_place'] = "Без места для тату"
            data['tattoo_details_number'] = 0
            data['order_state'] = OPEN_STATE_DICT["open"]
            data['sizes_lst'] = sizes_lst
            data['kb_client_size_tattoo'] = kb_client_size_tattoo
            
            if data['tattoo_type'] == 'переводное':
                # выставляем '-' в date_meeting, start_date_time, end_date_time 
                # когда тату переводная
                data['schedule_id'] = 0
                data['date_meeting'] = '-'
                data['event_type_creation'] = 'no schedule'
                data['start_date_time'] = '-'
                data['end_date_time'] = '-'
            
        await FSM_Client_tattoo_order.next() # -> load_tattoo_order_photo
        await bot.send_message(message.from_id, f'{MSG_START_TATTOO_ORDER}')
        await bot.send_message(message.from_id, f'{MSG_SCRETH_DEV}\n\n{MSG_GET_PHOTO_FROM_USER}',
            # ['Посмотреть галерею тату 📃', 'Загрузить свою фотографию эскиза 📎', 
            # 'У меня нет фотографии для эскиза 😓', 'Отмена ❌']
            reply_markup = kb_client.kb_no_photo_in_tattoo_order)
        
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
    # tattoo_items = await get_info_many_from_table('tattoo_items', 'creator', 'admin')
    tattoo_items = Session(engine).scalars(select(TattooItems).where(TattooItems.creator.in_(["admin"])))
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
                
            if next_menu_look_tattoo_galery:
                await bot.send_message(message.from_id,  
                    MSG_CLIENT_BACK_AND_WHICH_PHOTO_DO_CLIENT_WANT_TO_LOAD,
                    reply_markup = kb_client.kb_no_photo_in_tattoo_order)
            else:
                await FSM_Client_tattoo_order.previous()
                await bot.send_message(message.from_id,
                    f'{MSG_CLIENT_GO_BACK} {MSG_CLIENT_WANT_CURRENT_OR_NOT_TATTOO}',
                    reply_markup = kb_client.kb_client_choice_main_or_temporary_tattoo)
                
        elif message.text == kb_client.no_photo_in_tattoo_order['no_idea_tattoo_photo']:
            async with state.proxy() as data:
                data['tattoo_photo'] = 'Тату заказ без фотографии'
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
                f'💬 Введи текст для эскиза, пожалуйста.',
                reply_markup= kb_client.kb_back_cancel)

        # 'Посмотреть галерею тату 📃
        elif message.text == kb_client.no_photo_in_tattoo_order['look_tattoo_galery']:
            async with state.proxy() as data:
                data['next_menu_look_tattoo_galery'] = True
            for tattoo in tattoo_items:
                #? TODO нужно ли выводить размер и цену?
                msg = f'📃 Название: {tattoo.name}\n🎨 Цвет: {tattoo.colored}\n'
                    #\f'🔧 Количество деталей: {tattoo[5]}\n'
                if tattoo.note != 'без описания':
                    msg += f'💬 Описание: {tattoo.note}\n'#💰 Цена: {tattoo[2]}\n'
                
                await bot.send_photo(message.from_user.id, tattoo.photo , msg)
                
            # выдаем список тату - фотографии, название, цвет, описание    
            await bot.send_message(message.from_id, f'{MSG_WHICH_TATTOO_WANT_TO_CHOOSE}',
                reply_markup = kb_tattoo_items_for_order) 
            
        # переходим сюда, если клиент выбрал эскиз из списка    
        elif message.text in list_kb_tattoo_items: 
            for tattoo in tattoo_items:
                if message.text == f'{tattoo.name}':
                    async with state.proxy() as data:      
                        data['tattoo_name'] = tattoo.name
                        data['tattoo_photo'] = tattoo.photo # + '|'
                        data['tattoo_price'] = tattoo.price
                        # data['tattoo_details_number'] = tattoo[5]
                        data['tattoo_colored'] = tattoo.colored
                        data['tattoo_from_galery'] = True
                        data['menu_change_name'] = False
                        data['next_menu_detailed_number'] = False
                        data['menu_tattoo_list_place'] = False
                        
            await FSM_Client_tattoo_order.next() # -> change_menu_tattoo_from_galery
            await bot.send_message(message.from_id, '📷 Отлично, ты выбрал(а) эскиз для своего тату!'\
                f'{CLIENT_WANT_TO_CHANGE_MORE}',
                # 'Хочу дать свое название тату', 'Хочу изменить размер тату', 
                # 'Хочу изменить цвета у тату', 'Хочу изменить детали на тату'
                reply_markup = kb_client.kb_tattoo_from_galery_change_options) 
            
        elif message.text in [kb_client.no_photo_in_tattoo_order['load_tattoo_photo'], 
            kb_client.client_still_want_his_sketch, 
            kb_client.client_choice_add_another_photo_to_tattoo_order['client_want_to_add_sketch_to_tattoo_order']]:
            async with state.proxy() as data:
                data['tattoo_order_photo_counter'] = 0
                
            await bot.send_message(message.from_id, MSG_CLIENT_LOAD_PHOTO,
                reply_markup= kb_client.kb_back_cancel)
            
        # "Да, отличное изображение, хочу такой эскиз ☘️",
        elif message.text == kb_client.correct_photo_from_ai_or_get_another["correct_photo_from_ai"]:
            
            async with state.proxy() as data:
                data['tattoo_photo'] = data['last_img_photo_from_ai']
                
            for i in range(2):
                await FSM_Client_tattoo_order.next() # -> load_tattoo_order_name
            await bot.send_message(message.from_id,  
                f'{MSG_CLIENT_SUCCESS_CHOICE_PHOTO}'\
                f'{MSG_CLIENT_CHOICE_TATTOO_NAME}',
                reply_markup = kb_client.kb_back_cancel)
            
        #'Закончить с добавлением изображений ➡️'
        elif message.text == \
            kb_client.client_choice_add_another_photo_to_tattoo_order[
                'client_dont_want_to_add_sketch_to_tattoo_order']:
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
                    '📷 Хорошо, давай получим другое фото. Введи текст для эскиза, пожалуйста.',
                    reply_markup= kb_client.kb_back_cancel)
        else:
            try:
                async with state.proxy() as data:
                    load_tattoo_desc = data['load_tattoo_desc']
                    data['load_tattoo_desc'] = False
                    session = data['session']
                    
                # !!!!! заглушка data['load_tattoo_desc']. Если false, то клиент может генерить изображения    
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
                        data['tattoo_photo'] = 'Тату заказ без фотографии|' +\
                            str(await generate_random_order_number(ORDER_CODE_LENTH)) +\
                            f'|Описание эскиза: {message.text}'
                    
                    await FSM_Client_tattoo_order.next()
                    await FSM_Client_tattoo_order.next() # -> load_tattoo_order_name
                    await bot.send_message(message.from_id,  
                        '📷 Отлично, ты описал свой эскиз!\n\n'\
                        f'{MSG_CLIENT_CHOICE_TATTOO_NAME}',
                        reply_markup = kb_client.kb_back_cancel)
                
                else:
                    await bot.send_message(message.from_id,  MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
                    
            except:
                await bot.send_message(message.from_id,  MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
            
    elif message.content_type == 'photo':
        async with state.proxy() as data:
            data['tattoo_from_galery'] = False
            data['tattoo_photo'] += f'{message.photo[0].file_id}|'
            tattoo_order_photo_counter = data['tattoo_order_photo_counter']
            data['tattoo_order_photo_counter'] = message.media_group_id
            
        if tattoo_order_photo_counter != data['tattoo_order_photo_counter']:
            async with state.proxy() as data:
                tattoo_order_photo_counter = data['tattoo_order_photo_counter']
            
            await bot.send_message(message.from_id,  
                '📷 Отлично, ты выбрал(а) фотографию эскиза для своего тату!')
            await bot.send_message( message.from_id, '❔ Хочешь добавить еще фото/картинку?',
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
            # tattoo_items = await get_info_many_from_table('tattoo_items', 'creator', 'admin')
            tattoo_items = Session(engine).scalars(select(TattooItems).where(
                TattooItems.creator == "admin"))
            
            kb_tattoo_items_for_order = ReplyKeyboardMarkup(resize_keyboard=True)
            for tattoo in tattoo_items:
                # tattoo = list(tattoo)
                kb_tattoo_items_for_order.add(KeyboardButton(f'{tattoo.name}'))
            kb_tattoo_items_for_order.add(KeyboardButton(kb_client.client_still_want_his_sketch)
                ).add(kb_client.back_btn).add(kb_client.cancel_btn)
            # TODO добавить inline кнопки
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}{MSG_WHICH_TATTOO_WANT_TO_CHOOSE}',
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
            f'🎨 Хорошо, давай поменяем цвет тату. Изначальный цвет тату: {color}\n\n'\
            f'{MSG_WHICH_COLOR_WILL_BE_TATTOO}',
            reply_markup = kb_client.kb_colored_tattoo_choice)
    
    # меняем детали в тату
    elif message.text == \
        kb_client.tattoo_from_galery_change_options['client_want_to_change_tattoo_details']:
        async with state.proxy() as data:
            data['next_menu_detailed_number'] = True
            photo = data['tattoo_photo'].split('|')[0]
            
        await bot.send_photo(message.from_id, photo)
        await bot.send_message(message.from_id,  f'🔧 Хорошо, давай поменяем детали в тату.\n'\
            # f' Изначальное количество деталей в тату: {details}\n\n'\
            '❔ Опиши, какие детали хочешь изменить или убрать из эскиза этого тату?',
            reply_markup = kb_client.kb_back_cancel)

    # ничего не хочу менять -> get_choice_tattoo_place
    elif message.text == kb_client.tattoo_from_galery_change_options['no_change']:
        async with state.proxy() as data:      
            name = data['tattoo_name'] 
            color = data['tattoo_colored']
            
        for i in range(4):
            await FSM_Client_tattoo_order.next() # -> get_choice_tattoo_place
            
        await bot.send_message(message.from_id,  
            f'🌿 Хорошо, ты выбрал тату под названием \"{name}\". \nТату будет {color.lower()}\n\n'\
            f'❔ Хочешь указать место, где будет располагаться тату?', 
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
        
    elif message.text.lower() == 'другой размер':
        async with state.proxy() as data:
            data['next_menu_another_size'] = True
            
        await bot.send_message(message.from_id, '❔ Какой размер тату ты хотел бы?',
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
                    f'🍃 Хорошо, твои изменения деталей в данном эскизе сохранены.\n\n'\
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


# Отправляем размер тату и выбираем свободную дату
async def load_tattoo_order_size(message: types.Message, state: FSMContext):  

    async with state.proxy() as data:
        sizes_lst = data['sizes_lst']
        
    if message.text.lower() == 'другой размер':
        async with state.proxy() as data:
            data['next_menu_another_size'] = True
            
        await bot.send_message(message.from_id, '❔ Какой размер тату ты хотел бы?',
            reply_markup = kb_client.kb_another_size)
        
    elif any(text in message.text for text in sizes_lst):
        async with state.proxy() as data:
            data['tattoo_size'] = message.text
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
        
        await bot.send_message(message.from_id, '❔ Хочешь указать место, где будет располагаться тату?',
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

    session = Session(engine)
    schedule = select(ScheduleCalendar).where(ScheduleCalendar.status == "Свободен").where(
        ScheduleCalendar.event_type == "тату заказ")
    
    if schedule == []:
        await bot.send_message(message.from_id, MSG_TO_NO_SCHEDULE,
            reply_markup= kb_client.kb_next_action)
    else:
        kb_schedule = ReplyKeyboardMarkup(resize_keyboard=True)
        
        schedule_photo = session.scalars(select(SchedulePhoto).where(
            SchedulePhoto.name == datetime.strftime(datetime.now(), '%m %Y'))).one()
        
        async with state.proxy() as data:
            kb_items_list = []
            date_list_full_for_msg = ''
            for date in session.scalars(schedule):
    
                if date.date > datetime.now():
                    month = await get_month_from_number(date.date.strftime("%m"))
                    item_in_kb = f"{month} {date.date.strftime('%d/%m/%Y')} c {date.start_time} по {date.end_time} 🗓"
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
        data['check_document'] = '-'
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
            
        elif tattoo_type == 'переводное':
            for i in range(7):
                # пропускаем добавление фотографии и выбор календаря,
                # переходим сразу в заполнение tattoo order note
                await FSM_Client_tattoo_order.next() # -> # load_tattoo_order_note
                
            await bot.send_message(message.from_id,   
                f'🌿 А теперь введи что-нибудь о своем тату!'\
                    ' Чем подробнее описание твоего тату, тем лучше! \n\n'\
                f'➡️ Или нажми \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
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
                '❔ Хочешь отправить фото или видео, где тату будет располагаться?',
                reply_markup= kb_client.kb_choice_get_photo_for_place_tattoo)
    
    # "Да, хочу отправить фото/видео "
    elif message.text == kb_client.choice_get_photo_for_place_tattoo['client_want_to_get_place']:
        await FSM_Client_tattoo_order.next() # -> get_photo_place_for_tattoo
        await bot.send_message(message.from_id,  
            '📎 Отправь фото своей части тела, на котором будет твое тату, пожалуйста\n\n'\
            '❕ Можно добавлять сразу несколько файлов.',
            reply_markup= kb_client.kb_back_cancel)
    
    # "Нет, не хочу"
    elif message.text == kb_client.choice_get_photo_for_place_tattoo['client_dont_want_to_get_place']:
        await bot.send_message(message.from_id, 'Не проблема, добавим фото/видео для тату позже.')
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
            
        elif tattoo_type == 'переводное':
            for i in range(7):
                # пропускаем добавление фотографии и выбор календаря,
                # переходим сразу в заполнение tattoo order note
                await FSM_Client_tattoo_order.next() # -> # load_tattoo_order_note
                
            await bot.send_message(message.from_id,   
                f'🌿 А теперь введи что-нибудь о своем тату!'\
                    ' Чем подробнее описание твоего тату, тем лучше! \n\n'\
                f'➡️ Или нажми \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
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
                '❔ Хочешь указать место, где будет располагаться тату?', 
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
                '❔ Хочешь отправить фото или видео, где тату будет располагаться?',
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
                '📎 Хорошо, отправь еще фотографию или видео через файлы.', 
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
                    
                if tattoo_type == 'постоянное тату':
                    # выводим на экран расписание и переходим дальше
                    for i in range(2):
                        await FSM_Client_tattoo_order.next() #! -> choice_tattoo_order_date_and_time_meeting
                    await view_schedule_to_client(message, state) 
                else:
                    # переходим в заполнение order note
                    for i in range(7):
                        await FSM_Client_tattoo_order.next() # -> load_tattoo_order_note
                        
                    await bot.send_message(message.from_id,   
                        f'🌿 А теперь введи что-нибудь о своем тату!'\
                        ' Чем подробнее описание твоего тату, тем лучше! \n\n'\
                        f'➡️ Или нажми \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
                        reply_markup= kb_client.kb_no_tattoo_note_from_client)
            
        elif any(text in message.text for text in LIST_CANCEL_COMMANDS):
            await state.finish()
            await bot.send_message(message.from_id, 
                MSG_BACK_TO_HOME, reply_markup=kb_client.kb_client_main)
        
        elif any(text in message.text for text in LIST_BACK_COMMANDS):
            await FSM_Client_tattoo_order.previous() # -> get_choice_tattoo_place
            await bot.send_message(message.from_id,  f'{MSG_CLIENT_GO_BACK}\n\n'\
                '🗾 Выбери место для своего тату',
                reply_markup= kb_client.kb_place_for_tattoo)
        else:
            await bot.send_message(message.from_id,  f'📎 Пожалуйста, отправь фотографию через файлы')
            
    if message.content_type == 'photo':
        async with state.proxy() as data:
            data['tattoo_place_photo'].append(
                TattooPlacePhoto(
                    tattoo_order_id = data['tattoo_order_number'], photo = message.photo[0].file_id
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
            data['tattoo_place_video_note'] += f'{message.video_note.file_id}|'
        
        await bot.send_message(message.from_id, 
            '📷 Отлично, ты добавил(а) видеосообщение места для своего тату!')
        await bot.send_message(message.from_id, MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY, 
            reply_markup= kb_client.kb_yes_no)
        
    elif message.content_type == 'video':
        async with state.proxy() as data:
            data['tattoo_place_video'] += f'{message.video.file_id}|'
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
        
    if message.text.lower() == 'другой размер':
        async with state.proxy() as data:
            data['next_menu_another_size'] = True
            
        await bot.send_message(message.from_id, '❔ Какой размер тату ты хотел бы?',
            reply_markup = kb_client.kb_another_size)
        
    elif any(text in message.text for text in sizes_lst):
        async with state.proxy() as data:
            data['tattoo_size'] = message.text
            data['next_menu_another_size'] = False
            tattoo_type = data['tattoo_type']
            
        await bot.send_message(message.from_id, 
            f'📏 Отлично, вы указали размер тату равным {message.text}')
        
        if tattoo_type.lower() == 'постоянное тату':
            await FSM_Client_tattoo_order.next() #! -> choice_tattoo_order_date_and_time_meeting
            await view_schedule_to_client(message, state)
            
        else:
            for i in range(5):
                await FSM_Client_tattoo_order.next() #! -> load_tattoo_order_note
                
            await bot.send_message(message.from_id,
                f'🌿 А теперь введи что-нибудь о своем тату! '\
                'Чем подробнее описание твоего тату, тем лучше! \n\n'\
                f'➡️ Или нажми \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
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
                    '📎 Отправь фото своей части тела, на котором будет твое тату, пожалуйста',
                    reply_markup= kb_client.kb_back_cancel)
            else:
                for i in range(2):
                    await FSM_Client_tattoo_order.previous() # -> get_choice_tattoo_place
                    
                await bot.send_message(message.from_id,  f'{MSG_CLIENT_GO_BACK}'\
                    '❔ Хочешь указать место, где будет располагаться тату?',
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
        await FSM_Client_tattoo_order.next()
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
            await bot.send_message(message.from_id,  f'{MSG_CLIENT_GO_BACK}'\
                '❔ Хочешь определить место, где будет располагаться тату?',
                reply_markup = kb_client.kb_choice_place_tattoo)
        else:
            for i in range(2):
                await FSM_Client_tattoo_order.previous() # -> get_choice_tattoo_place
            await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}'\
                '❔ Хочешь добавить фотографию места, где будет располагаться тату?',
                reply_markup = kb_client.kb_choice_get_photo_for_place_tattoo)
            
    elif message.text in kb_client.next_action_lst: # 'Далее ➡️'
        async with state.proxy() as data:
            data['date_meeting'] = 'Без указания даты сеанса'
            data['event_type_creation'] = 'from schedule'
            data['start_date_time'] = 'Без указания начала сеанса'
            data['end_date_time'] = 'Без указания конца сеанса'
            data['schedule_id'] = 0
            
        for i in range(4):
            await FSM_Client_tattoo_order.next() # -> load_tattoo_order_note
            
        await bot.send_message(message.from_id,
            f'🌿 А теперь введи что-нибудь о своем тату! Чем подробнее описание твоего тату, тем лучше! \n\n'\
            f'➡️ Или нажми \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
            reply_markup= kb_client.kb_no_tattoo_note_from_client
        )
        
    else:
        async with state.proxy() as data:
            data['event_type_creation'] = 'from schedule'
            schedule_list = data['date_free_kb_items_list']
            
            if message.text in schedule_list: # если выбираем конкретную дату из календаря  
                if '/' in message.text.split()[1]:
                    # Февраль 06/02/2023 c 14:00:00 по 17:00:00
                    data['date_meeting'] = message.text.split()[1]
                    ''' datetime(year = int(message.text.split()[1].split('/')[2]),
                            month =    int(message.text.split()[1].split('/')[1]),
                            day =      int(message.text.split()[1].split('/')[0]),
                            hour =     int(message.text.split()[3].split(':')[0]),
                            minute =   int(message.text.split()[3].split(':')[1]),
                            second =   int(message.text.split()[3].split(':')[2]),
                    ) 
                    '''
                    data['start_date_time'] = message.text.split()[3]
                    data['end_date_time'] = message.text.split()[5]
                    data['schedule_id'] = 0
                    for event in data['date_free_list']:
                        if event[3] == message.text.split()[1] and \
                            event[1] == message.text.split()[3]:
                            data['schedule_id'] = event[0] 
                            #обновлять статус  расписания в базе будем по id
                    for i in range(4):
                        await FSM_Client_tattoo_order.next() # -> load_tattoo_order_note
                        
                    await bot.send_message(message.from_id,   
                        f'🌿 Прекрасно! 📅 Вы выбрали дату {message.text.split()[1]} и '\
                        f'время {message.text.split()[3]}')
                    
                    await bot.send_message(message.from_id, 
                        f'🌿 А теперь введи что-нибудь о своем тату! Чем подробнее описание твоего тату, тем лучше!\n\n'\
                        f'➡️ Или нажми \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
                        reply_markup= kb_client.kb_no_tattoo_note_from_client
                    )
                else: # если выбираем день из календаря  
                    data['start_date_time'] = message.text.split()[3]
                    data['end_date_time'] = message.text.split()[5]
                    await FSM_Client_tattoo_order.next()
                    dates = await get_dates_from_month_and_day_of_week(
                        month=message.text.split()[0],
                        day=message.text.split()[1]
                    ) 
                    kb_dates = ReplyKeyboardMarkup(resize_keyboard=True)
                    for date in dates:
                        kb_dates.add(KeyboardButton(date))
                    day = message.text.split()[1]
                    await bot.send_message(message.from_id, f'Хорошо, в какой {day} хочешь пойти?',
                        reply_markup= kb_dates)
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
        '🕒 А теперь введи удобное для тебя время.',
        reply_markup= await FullTimePicker().start_picker())


# перехода нет, т.к. пользователь  не будет выставлять свою дату
# выбираем дату заказа
@dp.callback_query_handler(dialog_cal_callback.filter(), state=FSM_Client_tattoo_order.date_meeting)
async def load_datemeeting(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data) # type: ignore
    async with state.proxy() as data:
        user_id = data['telegram']
        
    if selected:
        new_date = f'{date.strftime("%d/%m/%Y")}'
        await callback_query.message.answer(f'Вы выбрали {new_date}')
        if date > datetime.now(): 
            async with state.proxy() as data:
                data['date_meeting'] = new_date #  message.text
                data['event_type'] = 'тату заказ'
                data['event_type_creation'] = 'from user'
            await FSM_Client_tattoo_order.next()
            await bot.send_message(user_id,
                f'📅 Прекрасно, дата встречи теперь {new_date}! \n\n')
            
            await bot.send_message(user_id,
                '🕒 А теперь введи удобное для тебя время.',
                reply_markup= await FullTimePicker().start_picker())
        else:
            await bot.send_message(user_id, f'{MSG_NOT_CORRECT_DATE_NOW_LESS_CHOICEN}'\
                f'{MSG_LET_CHOICE_NORMAL_DATE}')


# перехода нет, т.к. пользователь  не будет выставлять свою дату
# выбираем время заказа
@dp.callback_query_handler(full_timep_callback.filter(), 
    state=FSM_Client_tattoo_order.date_time)
async def process_hour_timepicker(callback_query: CallbackQuery,
    callback_data: dict, state: FSMContext):
    r = await FullTimePicker().process_selection(callback_query, callback_data) # type: ignore
    if r.selected:  
        await callback_query.message.edit_text(
            f'Вы выбрали время для тату в {r.time.strftime("%H:%M:%S")} ',
        )
        # await callback_query.message.delete_reply_markup()
        async with state.proxy() as data:
            data['start_date_time'] = r.time.strftime("%H:%M:%S")
            data['end_date_time'] = str(int(r.time.strftime("%H")) + 3) + \
                str(r.time.strftime(":%M:%S"))
            data['schedule_id'] = await generate_random_order_number(CODE_LENTH)
            user_id = data['telegram']
            meeting_date = data['start_date_time']

            with Session(engine) as session:
                new_schedule_event = ScheduleCalendar(
                    schedule_id= int(data['schedule_id']),
                    start_time= data['start_date_time'],
                    end_time= data['end_date_time'],
                    date= data['date_meeting'],
                    status= 'Занят',
                    event_type= data['event_type']
                )
                session.add_all([new_schedule_event])
                session.commit()
            
        await FSM_Client_tattoo_order.next()
        await bot.send_message(user_id,
            f'📅 Прекрасно! Вы выбрали дату {meeting_date} и '\
            f'🕒 время {r.time.strftime("%H:%M:%S")}.'
        )
        await bot.send_message(user_id, 
            f'🌿 А теперь введи что-нибудь о своем тату! Чем подробнее описание твоего тату, тем лучше! \n\n'\
            f'➡️ Или нажми \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
            reply_markup= kb_client.kb_no_tattoo_note_from_client
        )


async def load_tattoo_order_note(message: types.Message, state: FSMContext):
    if any(text in message.text for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, MSG_BACK_TO_HOME, reply_markup=kb_client.kb_client_main)
        
    elif any(text in message.text for text in LIST_BACK_COMMANDS): # идем назад
        async with state.proxy() as data:
            tattoo_type = data['tattoo_type']
            if tattoo_type.lower() == 'постоянное тату':
            
                if data['event_type_creation'] == 'from schedule':
                    await view_schedule_to_client(message, state) # выводим календарь
                    await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}'\
                        '❔ Какую дату ты хочешь выбрать из предложенных?')
                    
                    for i in range(4):
                        await FSM_Client_tattoo_order.previous() # -> choice_tattoo_order_date_and_time_meeting

                elif data['event_type_creation'] == 'from user':
                    await FSM_Client_tattoo_order.previous()
                    await bot.send_message(message.from_id,  f'{MSG_CLIENT_GO_BACK}'\
                        '🕒 Введи удобное для тебя время.',
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
                            '❔ Хочешь определить место, где будет располагаться тату?',
                            reply_markup = kb_client.kb_choice_place_tattoo)
                        
                    else:
                        await bot.send_message(message.from_id, f'{MSG_CLIENT_GO_BACK}'\
                            '❔ Хочешь добавить фотографию места, где будет располагаться тату?',
                            reply_markup = kb_client.kb_choice_get_photo_for_place_tattoo)
                        
    else:
        
        async with state.proxy() as data:
            if message.text in kb_client.no_tattoo_note_from_client:
                data['tattoo_note'] = 'Без описания тату'
            else:
                data['tattoo_note'] = message.text
            
            data['tattoo_order_number'] = await generate_random_order_number(ORDER_CODE_LENTH)   
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
            data['tattoo_price'] = Session(engine).scalars(select(TattooOrderPriceList).where(
                TattooOrderPriceList.min_size == min_size).where(
                TattooOrderPriceList.max_size == max_size)).one().price
            
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
            creator = "admin" if not data['tattoo_from_galery'] else "client"
                
            """
                Определяем новое Тату - TattooItems
            """
            new_tattoo_item = TattooItems(
                tattoo_name=    data['tattoo_name'],
                tattoo_photo=   data['tattoo_photo'],
                tattoo_price=   data['tattoo_price'],
                tattoo_note=    data['tattoo_note'],
                tattoo_colored= data['tattoo_colored'],
                creator=        creator     
            )

            if not data['tattoo_from_galery']:
                new_table_items.append(new_tattoo_item)
            
            """
                Определяем нового пользователя, если его нет в базе - User
            """
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
                
            user_id= session.scalars(select(User).where(
                User.telegram_id == message.from_id)).one().id
            """
                Определяем новый документ - CheckDocument
            """
            
            check_document = CheckDocument(
                order_number = data['tattoo_order_number'],
                user=   message.from_id,
                doc=    data['check_document'],
            )
            new_table_items.append(check_document)
            """
                Определяем новое фото тела - TattooPlacePhoto
            """
            new_tattoo_body_photo = TattooPlacePhoto(
                order_number = data["tattoo_order_number"],
                user_id=    user_id,
                photo=      data['tattoo_place_photo']
            )
            new_table_items.append(new_tattoo_body_photo)
            
            """
                Определяем новое видео заметку тела - TattooPlaceVideoNote
            """
            new_tattoo_place_video_note = TattooPlaceVideoNote(
                order_number = data["tattoo_order_number"],
                user_id=    user_id,
                video=      data['tattoo_place_video_note']
            )
            new_table_items.append(new_tattoo_place_video_note)
            
            """
                Определяем новое видео тела - TattooPlaceVideo
            """
            new_tattoo_place_video = TattooPlaceVideo(
                order_number = data["tattoo_order_number"],
                user_id=    user_id,
                video=      data['tattoo_place_video']
            )
            new_table_items.append(new_tattoo_place_video)
            
            new_tattoo_order = Orders(
                telegram=                  f'@{message.from_user.username}',
                order_name=                data['tattoo_name'],
                order_type=                data['tattoo_type'],
                order_photo=               [new_tattoo_item],
                tattoo_size=               data['tattoo_size'],
                date_meeting=              data['date_meeting'],
                date_time=                 data['start_date_time'],
                tattoo_note=               data['tattoo_note'],
                order_note=                data['order_note'],
                order_state=               data['order_state'],
                order_number=              data['tattoo_order_number'],
                creation_date=             data['creation_date'],
                tattoo_price=              data['tattoo_price'],
                check_document=            [check_document],
                username=                  data['username'],
                schedule_id=               data['schedule_id'],
                tattoo_colored=            data['tattoo_colored'],
                tattoo_details_number=     data['tattoo_details_number'],
                tattoo_body_place=         data['tattoo_body_place'],
                tattoo_place_photo=        [new_tattoo_body_photo],
                tattoo_place_video_note=   [new_tattoo_place_video_note],
                tattoo_place_video=        [new_tattoo_place_video],
                code=                       None
            )
            new_table_items.append(new_tattoo_order)
            session.add_all(new_table_items)
            session.commit()
            
        status = data['order_state']
        tattoo_order_number = data['tattoo_order_number'] 
        event_body_text = \
            'Название тату: '   +   data['tattoo_name'] + ' \n' + \
            'Описание тату: '   +   data['tattoo_note'] + ' \n' + \
            'Описание заказа: ' +   data['order_note']  + ' \n' + \
            f'Имя клиента: {message.from_user.full_name}\n'\
            f'Телеграм клиента: @{message.from_user.username}'
            
        if data['tattoo_type'] == 'постоянное тату': # если заказ на постоянную татуировку
            schedule_id = data['schedule_id']
            end_time_meeting = data['end_date_time']
            date_meeting = data['date_meeting']
            start_time_meeting = data['start_date_time']
            
            # await db_filling_from_command('tattoo_items.json', new_tattoo_info)
            if schedule_id != 0:
                schedule_event = session.scalars(select(ScheduleCalendar).where(
                    ScheduleCalendar.schedule_id == "schedule_id")).one()
                schedule_event.status = 'Занят'
                session.commit()
                
            # TODO дополнить id Шуны и добавить интеграцию с Google Calendar !!!
            if DARA_ID != 0:
                await bot.send_message(DARA_ID, f'Дорогая Тату-мастерица! '\
                    f'🕸 Поступил новый заказ на тату под номером {tattoo_order_number}! '\
                    f'📃 Статус заказа: {status}. \n'
                    f'🕒 Дата встречи: {date_meeting} в {start_time_meeting}\n'\
                    f'💬 Телеграм клиента: @{message.from_user.username}')
                
            date_meeting = date_meeting.split('/')
            start_time = f'{date_meeting[2]}-{date_meeting[1]}-'\
                f'{date_meeting[0]}T{start_time_meeting}'
            end_time = f'{date_meeting[2]}-{date_meeting[1]}-'\
                f'{date_meeting[0]}T{end_time_meeting}'
            
                
            event = await obj.add_event(CALENDAR_ID,
                f'Новый тату заказ № {tattoo_order_number}',
                event_body_text,
                start_time, # '2023-02-02T09:07:00',
                end_time    # '2023-02-03T17:07:00'
            )
            
        else: # если заказ на переводную татуировку
            if DARA_ID != 0:
                await bot.send_message(DARA_ID, 
                    f'Дорогая Тату-мастерица! '\
                    f'🕸 Поступил новый заказ на переводное тату под номером {tattoo_order_number}! '\
                    f'📃 Статус заказа: {status}. \n'\
                    f'💬 Телеграм клиента: @{message.from_user.username}')
                
                event = await obj.add_event(CALENDAR_ID,
                    f'Новый переводное тату, заказ № {tattoo_order_number}',
                    event_body_text,
                    f'datetime.now().strftime("%Y-%m-%dT%H:%M:%S")', # '2023-02-02T09:07:00',
                    f'datetime.now().strftime("%Y-%m-%dT%H:%M:%S")'    # '2023-02-03T17:07:00'
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
                f'{MSG_THANK_FOR_ORDER}'
                f'{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
                reply_markup= kb_client.kb_client_main)


async def choiсe_tattoo_order_desctiption(message: types.Message, state: FSMContext):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            data['client_fill_order_note'] = True
            
        await bot.send_message(message.from_id,  'Хорошо! Опиши, чего именно ты хочешь,'\
            'и какие идеи у тебя есть, это очень важно!',
            reply_markup= kb_client.kb_back_cancel)
        
    elif message.text == kb_client.no_str:
        async with state.proxy() as data:
            data['order_note'] = 'Без описания заказа'
            data['client_fill_order_note'] = False
            
        await bot.send_message(message.from_id, f'🚫 Хорошо, пока оставим заказ без описания')
        
        await fill_tattoo_order_table(message, state)

    elif any(text in message.text for text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME):
        await state.finish()
        await bot.send_message(message.from_id,  MSG_BACK_TO_HOME, reply_markup=kb_client.kb_client_main)
        
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
                f'🌿 А теперь введи что-нибудь о своем тату!\n'
                'Чем подробнее описание твоего тату, тем лучше!\n\n'\
                f'➡️ Или нажми \"{kb_client.no_tattoo_note_from_client[0]}\" для продолжения',
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
            await bot.send_message(message.from_id,  MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


#---------------------------------------------GET VIEW TATTOO ORDER--------------------------------------
async def send_to_client_view_tattoo_order(message: types.Message, orders: ScalarResult["Orders"]):
    for order in orders:
        message_to_send = f'Тату заказ № {order.order_number} от {order.creation_date}\n'
        
        if order.order_type == 'постоянное тату':
            message_to_send += f'🕒 Дата и время встречи: {order.date_meeting} {order.date_time}\n'
        
        message_to_send += \
            f'🪴 Тип тату: {order.order_type}\n'\
            f'🍃 Имя: {order.order_name}\n'\
            f'📏 Размер: {order.tattoo_size}\n'\
            f'📜 Описание тату: {order.tattoo_note}\n' \
            f'💬 Описание заказа: {order.order_note}\n'\
            f'🎨 {order.colored} тату\n'\
            f'👤 Местоположение тату: {order.bodyplace}\n'
            #f'💰 Цена: {ret[11]}'
            #f'🎚 Количество основных деталей: {ret[16]}\n'\
                
        if order.order_state in list(CLOSED_STATE_DICT.values()):
            message_to_send += f'❌ Состояние заказа: {order.order_state}\n'
        else:
            message_to_send += f'📃 Состояние заказа: {order.order_state}\n'
            
        # TODO нужно ли скидывать пользователю чек с его оплатой?
        print(f"order.check_document:{order.check_document}")
        if any(str(check_state) in order.check_document for check_state in \
            ['Чек не добавлен', '-']):
            message_to_send += '⭕️ Чек не добавлен\n'
        else:
            message_to_send += '🍀 Чек добавлен\n'
            
        media = []
        tattoo_photos = Session(engine).scalars(select(OrderPhoto).where(
            OrderPhoto.order_number == order.order_number))
        body_photos = Session(engine).scalars(select(TattooPlacePhoto).where(
            TattooPlacePhoto.order_number == order.order_number))
        tattoo_place_video = Session(engine).scalars(select(TattooPlaceVideo).where(
            TattooPlaceVideo.order_number == order.order_number))
        
        for photo_tattoo in tattoo_photos:
            media.append(types.InputMediaPhoto(photo_tattoo.photo, message_to_send))
                
        # body photo 
        for photo_bodyplace in body_photos:
            media.append(types.InputMediaPhoto(photo_bodyplace.photo,
                f'👤 Местоположение тату: {order.bodyplace}'))
                
        for video_bodyplace in tattoo_place_video:
            media.append(types.InputMediaVideo(video_bodyplace.video))
                
        if media != []:
            await bot.send_chat_action(message.chat.id, types.ChatActions.UPLOAD_DOCUMENT)
            await bot.send_media_group(message.chat.id, media= media)
            await bot.send_message(message.from_id, message_to_send)
        else:
            if order.tattoo_photo == []:
                await bot.send_photo(message.from_user.id, order.tattoo_photo, message_to_send)  

            else:
                await bot.send_message(message.from_user.id, message_to_send)
        
        # tattoo_place_video_note
        for video_note in order.tattoo_place_video_note:
            await bot.send_video_note( message.chat.id, video_note)


#/посмотреть_мои_тату_заказы
async def get_clients_tattoo_order(message: types.Message):
    orders = Session(engine).scalars(select(Orders).where(
        Orders.username == 'message.from_user.full_name')).all()
    
    if orders == []:
        await bot.send_message(message.from_id,  
            f'⭕️ У тебя пока нет тату заказов. {MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
    else:
        await send_to_client_view_tattoo_order(message, orders)
            
        await bot.send_message(message.from_user.id, MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_client.kb_choice_order_view)


#/добавить_фото_в_тату_заказ
class FSM_Client_get_new_photo_to_tattoo_order(StatesGroup):
    get_order_id = State() 
    get_photo_type = State() 
    get_new_photo = State()
    
    
async def get_new_photo_to_tattoo_order(message: types.Message):
    orders = Session(engine).scalars(select(Orders).where(
        Orders.order_state.not_in([CLOSED_STATE_DICT.values()])).where(
        Orders.username == message.from_user.full_name).where(
        Orders.order_type.in_(['постоянное тату', 'переводное тату'])))
    
    if orders == []:
        await bot.send_message(message.from_id, 
            f'⭕️ У тебя пока нет тату заказов.\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}',
            reply_markup= kb_client.kb_choice_order_view)
    else:
        kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
        for order in orders:
            creation_date = order.creation_date.strftime("%d/%m/%Y")
            order_number = order.order_number
            kb_orders.add(f'Тату заказ № {order_number} от {creation_date}')
        kb_orders.add(kb_client.back_lst[0]).add(kb_client.cancel_lst[0])
        await FSM_Client_get_new_photo_to_tattoo_order.get_order_id.set()
        await bot.send_message(message.from_id, '❔ Для какого заказа хочешь добавить фотографию?',
            reply_markup= kb_orders)


async def get_order_id_to_add_new_photo(message: types.Message, state: FSMContext):    
    orders = select(Orders).where(
        Orders.order_state.not_in([CLOSED_STATE_DICT.values()])).where(
        Orders.username == message.from_user.full_name).where(
        Orders.order_type.in_(['постоянное тату', 'переводное тату']))
    
    kb_orders_lst = []
    for order in orders:
        creation_date = order.creation_date.strftime("%d/%m/%Y") # TODO нужно получить %d/%m/%Y
        order_number = order.tattoo_order_number
        kb_orders_lst.append(f'Тату заказ № {order_number} от {creation_date}')
        
    if message.text in kb_orders_lst:
        async with state.proxy() as data:
            data['tattoo_order_number'] = message.text.split()[3]
        await FSM_Client_get_new_photo_to_tattoo_order.next() # -> get_photo_type
        await bot.send_message(message.from_id, 
            '❔ Ты хочешь добавить фотографию для эскиза или фотографию изображения тела?',
            reply_markup= kb_client.kb_client_choice_add_photo_type)
        
    elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, f'{MSG_CANCEL_ACTION}{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
        reply_markup= kb_client.kb_choice_order_view)


async def get_photo_type(message: types.Message, state: FSMContext):
    # "Добавить фото для эскиза 🎨", "Добавить фото части тела 👤"
    if message.text in list(kb_client.client_choice_add_photo_type.values()):
        async with state.proxy() as data:
            # пользователь вносит сюда выбор типа фотографии: фотографию эскиза тату или тела
            data['photo_type'] = message.text.split()[-1] 
        await FSM_Client_get_new_photo_to_tattoo_order.next() #! -> get_new_photo
        
        await bot.send_message( message.from_id, 
            '📎 Хорошо, добавь новое фото в заказ через файлы, пожалуйта',
            reply_markup= kb_client.kb_back_cancel)
        
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Client_get_new_photo_to_tattoo_order.previous() #! -> get_order_id_to_add_new_photo
        kb_orders = ReplyKeyboardMarkup(resize_keyboard=True)
        orders = Session(engine).scalars(select(Orders).where(
            Orders.username == message.from_user.full_name).where(
            Orders.order_type.in_(['постоянное тату', 'переводное тату'])))
        
        for order in orders:
            creation_date = order.creation_date.strftime("%H:%M %d/%m/%Y")
            
            kb_orders.add(f'Тату заказ № {order.order_number} от {creation_date}')
        kb_orders.add(kb_client.back_lst[0]).add(kb_client.cancel_lst[0])
        await bot.send_message(message.from_id, '❔ Для какого заказа хочешь добавить фотографию?',
            reply_markup= kb_orders)
        
    elif any(text in message.text.lower() for text in LIST_CANCEL_COMMANDS):
        await state.finish()
        await bot.send_message(message.from_id, f'{MSG_CANCEL_ACTION}{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
        reply_markup= kb_client.kb_choice_order_view)
        
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_new_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        tattoo_order_number = data['tattoo_order_number']
        photo_type = data['photo_type']
    # order = await get_info_many_from_table('tattoo_orders', 'tattoo_order_number', tattoo_order_number)
    order = Session(engine).scalars(select(Orders).where(
        Orders.order_number == tattoo_order_number)).one()
    
    order_id = order.id
    user_id = Session(engine).scalars(select(User).where(
        User.name == message.from_user.full_name)).one()

    if message.content_type == 'photo':
        new_photo = f'{message.photo[0].file_id}'    
        photo_type = 'tattoo_photo' if photo_type == '🎨' else 'tattoo_place_photo'
        
        if photo_type == 'tattoo_photo':
            order.order_photo.append(OrderPhoto(
                order_number = tattoo_order_number, 
                order_id=order_id, 
                photo = new_photo, 
                user= user_id
            ))
            
            
        elif photo_type == 'tattoo_place_photo':
            order.tattoo_place_photo.append(TattooPlacePhoto(
                order_number = tattoo_order_number, 
                order_id=order_id, 
                photo = new_photo, 
                user=user_id
            ))
            
        Session(engine).commit()
        await state.finish()
        await bot.send_message(message.from_id,
            f'🎉 Отлично, ты обновил фотографии в заказе {tattoo_order_number}!\n\n'\
            f'{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
        
    elif message.content_type == 'video_note':
        order.tattoo_place_video_note.append(TattooPlaceVideoNote(
                order_number = tattoo_order_number, 
                order_id=order_id, 
                video = message.video_note.file_id, 
                user=user_id
            ))
            
        Session(engine).commit()
        await state.finish()
        await bot.send_message(message.from_id,
            f'🎉 Отлично, ты обновил фотографии в заказе {tattoo_order_number}!\n\n'\
            f'{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
        
    elif message.content_type == 'video':
        order.tattoo_place_video.append(TattooPlaceVideo(
                order_number = tattoo_order_number, 
                order_id=order_id, 
                video = message.video.file_id, 
                user=user_id
            ))
        Session(engine).commit()
        await state.finish()
        await bot.send_message(message.from_id,
            f'🎉 Отлично, ты обновил фотографии в заказе {tattoo_order_number}!\n\n'\
            f'{MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT}',
            reply_markup= kb_client.kb_choice_order_view)
        
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Client_get_new_photo_to_tattoo_order.previous() # -> get_photo_type
        await bot.send_message(message.from_id, 
            '❔ Ты хочешь добавить фотографию для эскиза или фотографию изображения тела?',
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