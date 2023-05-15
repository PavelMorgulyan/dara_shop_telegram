

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup

from handlers.client import ADMIN_NAMES, ORDER_CODE_LENTH, CODE_LENTH
from msg.main_msg import *
from diffusers import StableDiffusionPipeline
import torch
from handlers.other import *
from keyboards import kb_admin, kb_client
import time

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

# ----------------------------------------GENERATE TATTOO ITEM FROM AI--------------------------- 
class FSM_Admin_generate_ai_woman_model(StatesGroup):
    tattoo_desc = State()               # введи описание тату эскиза
    change_ai_img_state = State()


#/generate_ai_img # 'Хочу создать тату эскиз'
async def command_generage_woman_model_img(message: types.Message):
    
    if message.text.lower() in ['хочу создать изображение', '/хочу_создать_изображение'] and \
        str(message.from_user.username) in ADMIN_NAMES:
        await bot.send_message(message.from_id, f'{MSG_GET_DESCRIPTION_TATTOO_FROM_ADMIN}')
        
        await FSM_Admin_generate_ai_woman_model.tattoo_desc.set()
        await bot.send_message(message.from_id, f'{MSG_FILL_TEXT_OR_CHOICE_VARIANT}',
            reply_markup= kb_admin.kb_client_want_to_try_another_later_img)


async def create_ai_img(message: types.Message, state: FSMContext, img_text: str):
    await bot.send_message(message.from_id,
        'Пока думаю над изображением, придется немного подождать. Примерно 40-50 секунд')
    model_id = "./stable-diffusion/cyberrealistic-model/" # .ckpt "stable-diffusion/stable-diffusion-v1-5/"
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
    pipe = pipe.to("cuda")
    
    image = pipe(img_text).images[0]  
    img_name = await generate_random_order_number(ORDER_CODE_LENTH+3)
    
    #! path = f"./img/tattoo_ideas/{message.from_user.username}/{session}/{image_name}.png"
    
    path = f'D:/example_imgs/{str(img_name)}.png' # path = f"./img/tattoo_ideas/{image_name}.png"
    image.save(path)
    
    msg = MSG_ANSWER_AOUT_RESULT_TATTOO_FROM_AI
    ai_img = await bot.send_photo(message.chat.id, open(path, 'rb'))
        # "Да, отличное изображение, хочу такой эскиз ☘️", "Нет, хочу другое изображение 😓"
    id = await generate_random_order_number(CODE_LENTH)
    async with state.proxy() as data:
        data['id'] = id
        data['text'] = img_text
        data['last_img_photo_from_ai'] = ai_img['photo'][0]['file_id']
        data['state'] = 'неудачный'
        
    with Session(engine) as session:
        
        new_falling_img = TattooAI(
            img_id =      id,
            text=         img_text,
            photo=        ai_img['photo'][0]['file_id'],
            state=        'неудачный',
            author_name=  message.from_user.username,
        )
        session.add(new_falling_img)
        session.commit()
        
    await bot.send_message(message.chat.id, msg,
        reply_markup = kb_client.kb_correct_photo_from_ai_or_get_another)


async def get_text_from_admin_to_generate_img_ai(message: types.Message, state: FSMContext):
    
    text_img_lst = Session(engine).scalars(select(TattooAI).where(TattooAI.author_name == message.from_user.username))
    unique_text_img = []
    for text_img in text_img_lst:
        if list(text_img)[1] not in unique_text_img:
            unique_text_img.append(list(text_img)[1])
            
    async with state.proxy() as data:
        data['menu_number_img_text'] = False
            
    if message.text in LIST_CANCEL_COMMANDS+LIST_BACK_TO_HOME:
        async with state.proxy() as data:
            menu_number_img_text = data['menu_number_img_text']
            data['menu_number_img_text'] = False
            
        if menu_number_img_text:
            await bot.send_message(message.from_id, f'{MSG_FILL_TEXT_OR_CHOICE_VARIANT}',
                reply_markup= kb_admin.kb_client_want_to_try_another_later_img)
        else:
            await state.finish()
            await message.reply(MSG_BACK_TO_HOME, reply_markup = kb_admin.kb_main)
            
    elif message.text == kb_client.client_want_to_get_example_text_for_ai_img:
        await bot.send_message(message.from_id, f'{MSG_TEXT_EXAMPLES_LINKS}')
        
        await bot.send_message(message.from_id, 'Вот некоторые примеры простых тестов:')
        
        await bot.send_photo(message.from_id, open('img/tattoo_ideas/00017-881277398.png', 'rb'), 
            MSG_EXAMPLE_TEXT_PORTRAIT_WOMAN_MODEL_IN_HOME_EASY)
        time(3)
        await bot.send_photo(message.from_id, open('img/tattoo_ideas/00021-1526834311.png', 'rb'),
            MSG_EXAMPLE_TEXT_PORTRAIT_WOMAN_MODEL_IN_HOME_EASY)
        
        await bot.send_photo(message.from_id, open('img/tattoo_ideas/00036-3411177118', 'rb'),
            MSG_EXAMPLE_TEXT_BACK_WOMAN_MODEL_IN_HOME_EASY)
        
        time(3)
        await bot.send_message(message.from_id, f'{MSG_FILL_TEXT_OR_CHOICE_VARIANT}')
        
    elif message.text == kb_admin.admin_want_to_generate_img_from_ai_woman: # 'Сгенерируй мне модель женщины'
        text_to_ai = MSG_EXAMPLE_TEXT_PORTRAIT_WOMAN_MODEL_IN_HOME
        await FSM_Admin_generate_ai_woman_model.next()
        await create_ai_img(message, state, text_to_ai)
        
    elif message.text == kb_client.description_ai_generation_img:
        await bot.send_message(message.from_id, f"{MSG_START_INSTRUCTION_OF_GENERATING_AI_IMGS}")
        time(5)
        await bot.send_message(message.from_id, f"{MSG_GET_DESCRIPTION_WOMAN_MODEL_FROM_ADMIN_CONCEPTS}")
        time(5)
        await bot.send_message(message.from_id, f'{MSG_STYLES_CHROMATIC_PALETTES}')
        time(5)
        await bot.send_message(message.from_id, f'{MSG_STYLES_MONOCHROMATIC_PALETTES}')
        time(3)
        await bot.send_message(message.from_id, f'{MSG_STYLES_CONTRAST}')
        time(3)
        await bot.send_message(message.from_id, f'{MSG_MOTION_PICTURE_PROCESS}') 
        time(3)
        await bot.send_message(message.from_id, f'{MSG_ADD_SYMBOLS_FOR_GETTING_STRONGER_WORD}')
        time(3)
        await bot.send_message(message.from_id, f'{MSG_FILL_TEXT_OR_CHOICE_VARIANT}')
        
    elif message.text == \
            kb_client.correct_photo_from_ai_or_get_another['client_want_to_try_another_later_img']:
            if text_img_lst == []:
                await message.reply('Прости, но у тебя не было пока никаких текстов. Введи новый текст',
                    reply_markup = kb_client.kb_back_cancel)
            else:
                # await FSM_Admin_generate_ai_woman_model.previous()
                async with state.proxy() as data:
                    data['menu_number_img_text'] = True
                    
                kb_list_text_img = ReplyKeyboardMarkup(resize_keyboard=True)
                await bot.send_message(message.chat.id, 'Вот твои прерыдущие тексты:')

                for i in range(len(unique_text_img)):
                    await bot.send_message(message.chat.id, f'{i+1}) {unique_text_img[i]}\n\n')
                    kb_list_text_img.add(KeyboardButton(str(i+1)))
                    
                kb_list_text_img.add(kb_client.back_btn).add(kb_client.cancel_btn)
                await message.reply('Какой текст хочешь снова использовать для изображения?',
                    reply_markup= kb_list_text_img)
            
    elif message.text in [str(i+1) for i in range(len(unique_text_img))]:
        await FSM_Admin_generate_ai_woman_model.next()
        text_to_ai = ''
        for i in range(len(unique_text_img)):
            if i+1 == int(message.text):
                text_to_ai = unique_text_img[i]
                
        await bot.send_message(message.chat.id, f'Вы выбрали следующий текст:')
        await bot.send_message(message.chat.id, f'{text_to_ai}')
        await create_ai_img(message, state, text_to_ai)
        
    else:
        await FSM_Admin_generate_ai_woman_model.next()
        text_to_ai = WOMAN_BOHO_STYLE_DESC % (f'({message.text}:1.6),') #! Создание модели девушки из этого описания!
        await create_ai_img(message, state, text_to_ai)


async def change_ai_img_state(message: types.Message, state: FSMContext):
    text_img_lst = Session(engine).scalars(select(TattooAI).where(TattooAI.author_name == message.from_user.username))

    unique_text_img = []
    for text_img in text_img_lst:
        if list(text_img)[1] not in unique_text_img:
            unique_text_img.append(list(text_img)[1])

    if message.text == kb_client.correct_photo_from_ai_or_get_another['correct_photo_from_ai']:
        async with state.proxy() as data:
            id = data['id']
        await update_info('tattoo_ai', 'id', id, 'state', 'удачный')
        await message.reply(f'Отлично, получилось удачное изображение! \n\n'\
            'Хочешь попробовать еще?.', reply_markup= kb_client.kb_want_another_ai_img)
        
    elif message.text in LIST_BACK_COMMANDS:
        async with state.proxy() as data:
            menu_number_img_text = data['menu_number_img_text']
            data['menu_number_img_text'] = False
        
        if menu_number_img_text:
            await bot.send_message(message.chat.id,f'{MSG_CLIENT_GO_BACK}',
                reply_markup = kb_client.kb_correct_photo_from_ai_or_get_another)
            
        else:
            await FSM_Admin_generate_ai_woman_model.previous()
            await message.reply(f'{MSG_CLIENT_GO_BACK}\n\n{MSG_FILL_TEXT_OR_CHOICE_VARIANT}',
                reply_markup= kb_admin.kb_client_want_to_try_another_later_img)
            
    elif message.text in [kb_client.want_another_ai_img['want_another_ai_img']] +\
        [
            kb_client.correct_photo_from_ai_or_get_another['want_another_ai_img'],
            kb_client.correct_photo_from_ai_or_get_another['client_want_to_change_this_text'],
            kb_client.correct_photo_from_ai_or_get_another['client_want_to_try_again']
        ]:
                
        await FSM_Admin_generate_ai_woman_model.previous()
        
        if message.text in \
            [
                kb_client.correct_photo_from_ai_or_get_another['client_want_to_change_this_text'],
                kb_client.correct_photo_from_ai_or_get_another['client_want_to_try_again']
            ]:
            async with state.proxy() as data:
                text_to_ai = data['text']
            await bot.send_message(message.chat.id, 'Вот предыдущий текст')
            await bot.send_message(message.chat.id, text_to_ai)
            
        if message.text == kb_client.correct_photo_from_ai_or_get_another['client_want_to_try_again']:
            await FSM_Admin_generate_ai_woman_model.next()
            await create_ai_img(message, state, text_to_ai)
            
        else:
            await message.reply(f'{MSG_FILL_TEXT_OR_CHOICE_VARIANT}',
                reply_markup= kb_admin.kb_client_want_to_try_another_later_img)
            
    elif message.text == \
            kb_client.correct_photo_from_ai_or_get_another['client_want_to_try_another_later_img']:
            # await FSM_Admin_generate_ai_woman_model.previous()
            async with state.proxy() as data:
                data['menu_number_img_text'] = True
            kb_list_text_img = ReplyKeyboardMarkup(resize_keyboard=True)
            await bot.send_message(message.chat.id, 'Вот твои прерыдущие тексты:')

            for i in range(len(unique_text_img)):
                await bot.send_message(message.chat.id, f'{i+1}) {unique_text_img[i]}\n\n')
                kb_list_text_img.add(KeyboardButton(str(i+1)))
                
            kb_list_text_img.add(kb_client.back_btn).add(kb_client.cancel_btn)
            await message.reply('Какой текст хочешь снова использовать для изображения?',
                reply_markup=kb_list_text_img)
            
    elif message.text in [str(i+1) for i in range(len(unique_text_img))]:
        text_to_ai = ''
        for i in range(len(unique_text_img)):
            if i+1 == int(message.text):
                text_to_ai = unique_text_img[i]
                
        await bot.send_message(message.chat.id, f'Вы выбрали следующий текст:')
        await bot.send_message(message.chat.id, f'{text_to_ai}')
        await create_ai_img(message, state, text_to_ai)
        
            
    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, 
            reply_markup = kb_admin.kb_main)
        
    else:
        await message.reply(MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST)\


def register_handlers_admin_generate_img(dp: Dispatcher):
    # --------------------------------------GENERATE TATTOO ITEM FROM AI--------------------------- 
    dp.register_message_handler(command_generage_woman_model_img, commands=['хочу создать изображение'])
    dp.register_message_handler(command_generage_woman_model_img,
        Text(equals='хочу создать изображение', ignore_case=True), state=None)
    dp.register_message_handler(get_text_from_admin_to_generate_img_ai,
        state=FSM_Admin_generate_ai_woman_model.tattoo_desc)
    dp.register_message_handler(change_ai_img_state,
        state=FSM_Admin_generate_ai_woman_model.change_ai_img_state)