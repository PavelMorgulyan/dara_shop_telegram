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
from diffusers import (
    StableDiffusionPipeline, 
    DPMSolverMultistepScheduler,
    DiffusionPipeline
)

import torch
from handlers.other import *
from keyboards import kb_admin, kb_client
import time

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *
import json


# --------------------------------GENERATE TATTOO ITEM FROM AI---------------------------
class FSM_Admin_generate_ai_woman_model(StatesGroup):
    tattoo_desc = State()  # введи описание тату эскиза
    change_ai_img_state = State()

class FSM_Admin_change_ai_model(StatesGroup):
    choice_model_name = State()


# /generate_ai_img # 'Cоздать тату эскиз'
async def command_generage_woman_model_img(message: types.Message):
    if (
        message.text
        in ["Создать изображение", "/создать_изображение"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await bot.send_message(
            message.from_id, f"{MSG_GET_DESCRIPTION_TATTOO_FROM_ADMIN}"
        )

        await FSM_Admin_generate_ai_woman_model.tattoo_desc.set()
        await bot.send_message(
            message.from_id,
            f"{MSG_FILL_TEXT_OR_CHOICE_VARIANT}",
            reply_markup=kb_admin.kb_client_want_to_try_another_later_img,
        )


async def create_ai_img(message: types.Message, state: FSMContext, prompt: str):
    await bot.send_message(
        message.from_id,
        "🕒 Пока думаю над изображением, придется немного подождать."
        " Примерно 40-50 секунд",
    )
    with open(f"files\models_configuration.json", encoding="cp1251") as f:
        data = json.load(f)
    
    model_id = data['work']
    
    if model_id == "stabilityai/stable-diffusion-xl-base-1.0":
        pipe = DiffusionPipeline.from_pretrained(
            model_id, 
            torch_dtype=torch.float16, 
            use_safetensors=True, 
            variant="fp16"
        )
    else:
        pipe = StableDiffusionPipeline.from_pretrained(
            pretrained_model_name_or_path=model_id, 
            torch_dtype=torch.float16
        )
    # pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("cuda")

    image = pipe(prompt=prompt).images[0]
    img_name = await generate_random_order_number(ORDER_CODE_LENTH + 3)

    # path = f"./img/tattoo_ideas/{message.from_user.username}/{session}/{image_name}.png"

    path = f"files\\ai_img\\{str(img_name)}.png"
    image.save(path)
    
    ai_img = await bot.send_photo(message.chat.id, open(path, "rb"))
    
    id = await generate_random_order_number(CODE_LENTH)
    async with state.proxy() as data:
        data["id"] = id
        data["text"] = prompt
        data["last_img_photo_from_ai"] = ai_img["photo"][0]["file_id"]
        data["state"] = "неудачный"

    with Session(engine) as session:
        new_falling_img = TattooAIImage(
            id=id,
            description=prompt,
            photo=ai_img["photo"][0]["file_id"],
            status="неудачный",
            author=message.from_user.username,
        )
        session.add(new_falling_img)
        session.commit()
    # "Да, отличное изображение, хочу такой эскиз ☘️",
    # "Нет, хочу другое изображение 😓"
    await bot.send_message(
        message.chat.id,
        MSG_ANSWER_ABOUT_RESULT_TATTOO_FROM_AI,
        reply_markup=kb_client.kb_correct_photo_from_ai_or_get_another,
    )


async def get_text_from_admin_to_generate_img_ai(
    message: types.Message, state: FSMContext
):
    with Session(engine) as session:
        text_img_lst = session.scalars(
            select(TattooAIImage)
            .where(TattooAIImage.author == message.from_user.username)
        ).all()
        
    with open(f"files\example_ai_text\examples.json", encoding="cp1251") as f:
        examples_imgs = json.load(f)    
        
    unique_text_img = []
    for text_img in text_img_lst:
        if text_img.description not in unique_text_img:
            unique_text_img.append(text_img.description)

    async with state.proxy() as data:
        data["menu_number_img_text"] = False

    if message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        async with state.proxy() as data:
            menu_number_img_text = data["menu_number_img_text"]
            data["menu_number_img_text"] = False

        if menu_number_img_text:
            await bot.send_message(
                message.from_id,
                f"{MSG_FILL_TEXT_OR_CHOICE_VARIANT}",
                reply_markup=kb_admin.kb_client_want_to_try_another_later_img,
            )
        else:
            await state.finish()
            await message.reply(
                MSG_BACK_TO_HOME,
                reply_markup=kb_admin.kb_main
            )

    elif message.text == kb_admin.client_want_to_try_another_later_img[
        "client_want_to_get_example_text_for_ai_img"
    ]:
        # "Хочу примеры текста изображения"
        await bot.send_message(message.from_id, f"{MSG_TEXT_EXAMPLES_LINKS}")

        await bot.send_message(
            message.from_id, 
            "Примеры простых тестов:"
        )
        await bot.send_photo(
            message.from_id,
            open("img/tattoo_ideas/00017-881277398.png", "rb"),
            examples_imgs["MSG_EXAMPLE_TEXT_PORTRAIT_WOMAN_MODEL_IN_HOME_EASY"],
        )
        time(3)
        await bot.send_photo(
            message.from_id,
            open("img/tattoo_ideas/00021-1526834311.png", "rb"),
            examples_imgs["MSG_EXAMPLE_TEXT_PORTRAIT_WOMAN_MODEL_IN_HOME_EASY"],
        )

        await bot.send_photo(
            message.from_id,
            open("img/tattoo_ideas/00036-3411177118", "rb"),
            examples_imgs["MSG_EXAMPLE_TEXT_BACK_WOMAN_MODEL_IN_HOME_EASY"],
        )

        time(3)
        await bot.send_message(
            message.from_id,
            MSG_FILL_TEXT_OR_CHOICE_VARIANT
        )

    elif (
        message.text == kb_admin.client_want_to_try_another_later_img[
            "admin_want_to_generate_img_from_ai_woman"
        ]
    ):  # 'Сгенерируй мне модель женщины'
        text_to_ai = examples_imgs["MSG_EXAMPLE_TEXT_PORTRAIT_WOMAN_MODEL_IN_HOME"]
        await FSM_Admin_generate_ai_woman_model.next()
        await create_ai_img(message, state, text_to_ai)

    elif (
        message.text == kb_admin.client_want_to_try_another_later_img[
            "description_ai_generation_img"
        ]
    ):
        await bot.send_message(
            message.from_id, f"{MSG_START_INSTRUCTION_OF_GENERATING_AI_IMGS}"
        )
        time(5)
        await bot.send_message(
            message.from_id, f"{MSG_GET_DESCRIPTION_WOMAN_MODEL_FROM_ADMIN_CONCEPTS}"
        )
        time(5)
        await bot.send_message(message.from_id, f"{MSG_STYLES_CHROMATIC_PALETTES}")
        time(5)
        await bot.send_message(message.from_id, f"{MSG_STYLES_MONOCHROMATIC_PALETTES}")
        time(3)
        await bot.send_message(message.from_id, f"{MSG_STYLES_CONTRAST}")
        time(3)
        await bot.send_message(message.from_id, f"{MSG_MOTION_PICTURE_PROCESS}")
        time(3)
        await bot.send_message(
            message.from_id, f"{MSG_ADD_SYMBOLS_FOR_GETTING_STRONGER_WORD}"
        )
        time(3)
        await bot.send_message(message.from_id, f"{MSG_FILL_TEXT_OR_CHOICE_VARIANT}")

    elif (
        message.text == kb_client.correct_photo_from_ai_or_get_another[
            "client_want_to_try_another_later_img"
        ]
    ):
        if text_img_lst == []:
            await message.reply(
                "❌ Прости, но у тебя не было пока никаких текстов."
                " Введи новый текст",
                reply_markup=kb_client.kb_back_cancel,
            )
        else:
            # await FSM_Admin_generate_ai_woman_model.previous()
            async with state.proxy() as data:
                data["menu_number_img_text"] = True

            kb_list_text_img = ReplyKeyboardMarkup(resize_keyboard=True)
            await bot.send_message(
                message.chat.id, 
                "📃 Вот твои прерыдущие тексты:"
            )

            for i in range(len(unique_text_img)):
                await bot.send_message(
                    message.chat.id, f"{i+1}) {unique_text_img[i]}\n\n"
                )
                kb_list_text_img.add(KeyboardButton(str(i + 1)))

            kb_list_text_img.add(kb_client.back_btn).add(kb_client.cancel_btn)
            await message.reply(
                "❔ Какой текст снова использовать для изображения?",
                reply_markup=kb_list_text_img,
            )

    elif message.text in [str(i + 1) for i in range(len(unique_text_img))]:
        await FSM_Admin_generate_ai_woman_model.next()
        text_to_ai = ""
        for i in range(len(unique_text_img)):
            if i + 1 == int(message.text):
                text_to_ai = unique_text_img[i]

        await bot.send_message(message.chat.id, f"📃 Вы выбрали следующий текст:")
        await bot.send_message(message.chat.id, f"{text_to_ai}")
        await create_ai_img(message, state, text_to_ai)

    elif (
        message.text == 
            kb_admin.client_want_to_try_another_later_img[
                "change_model"
            ]
    ): 
        await state.finish()
        # -> get_new_ai_model
        await FSM_Admin_change_ai_model.choice_model_name.set()
        
        msg = f"📃 Список доступных моделей:\n\n"
        with open(f"files\models_configuration.json") as f:
            models = json.load(f)
        
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for keys, model in models.items():
            if keys != 'work':
                msg += f"- {model}\n"
                kb.add(KeyboardButton(model))
                
        kb.add(kb_client.back_btn).add(kb_client.cancel_btn)

        await bot.send_message(
            message.chat.id,
            f"{msg}\n"
            f"❔ Какую модель выбрать?",
            reply_markup=kb
        )
        
    
    else:
        # -> change_ai_img_state
        await FSM_Admin_generate_ai_woman_model.next()
        text_to_ai = """ WOMAN_BOHO_STYLE_DESC % (f"({message.text}:1.6)") """
        # Создание модели девушки из этого описания!
        await create_ai_img(message, state, message.text)


async def change_ai_img_state(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        text_img_lst = session.scalars(
            select(TattooAIImage)
            .where(TattooAIImage.author == message.from_user.username)
        ).all()

    unique_text_img = []
    for text_img in text_img_lst:
        if text_img.description not in unique_text_img:
            unique_text_img.append(text_img.description)

    if (
        message.text == 
        kb_client.correct_photo_from_ai_or_get_another["correct_photo_from_ai"]
    ):
        async with state.proxy() as data:
            id = data["id"]
        
        with Session(engine) as session:
            img = session.scalars(
                select(TattooAIImage)
                .where(TattooAIImage.id == id)
            ).one()
            img.status = "удачный"
            session.commit()
            
        await message.reply(
            f"🎉 Отлично, получилось удачное изображение! \n\n❔ Попробовать еще?.",
            reply_markup=kb_client.kb_want_another_ai_img,
        )

    elif message.text in LIST_BACK_COMMANDS:
        async with state.proxy() as data:
            menu_number_img_text = data["menu_number_img_text"]
            data["menu_number_img_text"] = False

        if menu_number_img_text:
            await bot.send_message(
                message.chat.id,
                f"{MSG_CLIENT_GO_BACK}",
                reply_markup=kb_client.kb_correct_photo_from_ai_or_get_another,
            )

        else:
            await FSM_Admin_generate_ai_woman_model.previous()
            await message.reply(
                f"{MSG_CLIENT_GO_BACK}\n\n{MSG_FILL_TEXT_OR_CHOICE_VARIANT}",
                reply_markup=kb_admin.kb_client_want_to_try_another_later_img,
            )

    elif message.text in [kb_client.want_another_ai_img["want_another_ai_img"]] + [
        kb_client.correct_photo_from_ai_or_get_another["want_another_ai_img"],
        kb_client.correct_photo_from_ai_or_get_another[
            "client_want_to_change_this_text"
        ],
        kb_client.correct_photo_from_ai_or_get_another["client_want_to_try_again"],
    ]:
        await FSM_Admin_generate_ai_woman_model.previous()

        if message.text in [
            kb_client.correct_photo_from_ai_or_get_another[
                "client_want_to_change_this_text"
            ],
            kb_client.correct_photo_from_ai_or_get_another[
                "client_want_to_try_again"
            ],
        ]:
            async with state.proxy() as data:
                text_to_ai = data["text"]
            await bot.send_message(message.chat.id, "Вот предыдущий текст")
            await bot.send_message(message.chat.id, text_to_ai)

        if (
            message.text
            == kb_client.correct_photo_from_ai_or_get_another[
                "client_want_to_try_again"
            ]
        ):
            await FSM_Admin_generate_ai_woman_model.next()
            await create_ai_img(message, state, text_to_ai)

        else:
            await message.reply(
                f"{MSG_FILL_TEXT_OR_CHOICE_VARIANT}",
                reply_markup=kb_admin.kb_client_want_to_try_another_later_img,
            )

    elif (
        message.text
        == kb_client.correct_photo_from_ai_or_get_another[
            "client_want_to_try_another_later_img"
        ]
    ):
        # await FSM_Admin_generate_ai_woman_model.previous()
        async with state.proxy() as data:
            data["menu_number_img_text"] = True
        kb_list_text_img = ReplyKeyboardMarkup(resize_keyboard=True)
        await bot.send_message(message.chat.id, "📃 Вот твои прерыдущие тексты:")

        for i, text in enumerate(unique_text_img):
            await bot.send_message(
                message.chat.id,
                f"{i + 1}) {text}\n\n"
            )
            kb_list_text_img.add(KeyboardButton(str(i + 1)))

        kb_list_text_img.add(kb_client.back_btn).add(kb_client.cancel_btn)
        await message.reply(
            "❔ Какой текст хочешь снова использовать для изображения?",
            reply_markup=kb_list_text_img,
        )

    elif message.text in [str(i + 1) for i in range(len(unique_text_img))]:
        text_to_ai = ""
        for i in range(len(unique_text_img)):
            if i + 1 == int(message.text):
                text_to_ai = unique_text_img[i]

        await bot.send_message(
            message.chat.id,
            f"📃 Вы выбрали следующий текст:"
        )
        await bot.send_message(message.chat.id, text_to_ai)
        await create_ai_img(message, state, text_to_ai)

    elif message.text in LIST_CANCEL_COMMANDS + LIST_BACK_TO_HOME:
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# --------------CHANGE AI MODEL--------------------------
async def get_new_ai_model(message: types.Message, state: FSMContext):
    
    tmp_dct = {}    
    models_lst = []
    config_file = f"files\models_configuration.json"
    
    with open(config_file) as f:
        models = json.load(f)
        
    for model in models.values():
        models_lst.append(model)
    
    if message.text in models_lst:
        for keys, model in models.items():
            if keys == 'work':
                tmp_dct[keys] = message.text
                tmp_dct[model] = models[keys]
                
            else:
                tmp_dct[keys] = model
                
        with open(config_file, "w", encoding="cp1251") as f:
            json.dump(tmp_dct, f, indent=2, ensure_ascii=True)
            
        await state.finish()
        # -> command_generage_woman_model_img
        await FSM_Admin_generate_ai_woman_model.tattoo_desc.set()
        await bot.send_message(
            message.chat.id, 
            f"🎉 Готово! Модель изменилась на {message.text}\n"
            f"{MSG_FILL_TEXT_OR_CHOICE_VARIANT}",
            reply_markup=kb_admin.kb_client_want_to_try_another_later_img
        )
        
    elif (
            message.text in
            LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS
        ):
        
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)

    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


# TODO продвинутый режим, где будет выбор количества эпох и других параметров
"""  
    1) модель stabilityai/stable-diffusion-xl-base-1.0 дает неплохие результаты для начала
    но слишком долго - 9-10 минут на изображение
    https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0

    2) модель stable-diffusion-v1-5 отрабатывает ужасно, но делает зато быстро

    3) параметры степа и размера изображения банально не срабатывают 
"""


def register_handlers_admin_generate_img(dp: Dispatcher):
    # --------------GENERATE TATTOO ITEM FROM AI-------------------------
    dp.register_message_handler(
        command_generage_woman_model_img,
        commands=["создать_изображение"]
    )
    dp.register_message_handler(
        command_generage_woman_model_img,
        Text(equals="Создать изображение", ignore_case=True),
        state=None
    )
    dp.register_message_handler(
        get_text_from_admin_to_generate_img_ai,
        state=FSM_Admin_generate_ai_woman_model.tattoo_desc,
    )
    dp.register_message_handler(
        change_ai_img_state, 
        state=FSM_Admin_generate_ai_woman_model.change_ai_img_state
    )
    
    dp.register_message_handler(
        get_new_ai_model,
        state=FSM_Admin_change_ai_model.choice_model_name
    )
