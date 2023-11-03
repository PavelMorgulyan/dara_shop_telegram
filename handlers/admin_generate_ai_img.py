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
import requests
import io
import base64
from PIL import Image
import numpy as np

# --------------------------------GENERATE TATTOO ITEM FROM AI---------------------------
class FSM_Admin_generate_ai_woman_model(StatesGroup):
    tattoo_desc = State()  # введи описание тату эскиза
    change_ai_img_state = State()

class FSM_Admin_change_ai_model(StatesGroup):
    choice_model_name = State()


class FSM_ai_expert_mode(StatesGroup):
    choice_step_number = State()
    get_seed = State()
    get_batch = State()
    get_cfg_scale = State()
    get_ai_img_size = State()
    get_restore_faces = State()
    get_denoising_strength = State()
    get_sampler_name = State()


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
    
    if model_id['path'] == "stabilityai/stable-diffusion-xl-base-1.0":
        pipe = DiffusionPipeline.from_pretrained(
            model_id, 
            torch_dtype=torch.float16, 
            use_safetensors=True, 
            variant="fp16"
        )
        
    elif model_id['path'] == 'sdapi':
        with open(f"files\sd_api_options.json", encoding="cp1251") as f:
            payload = json.load(f)
            
        payload['prompt'] = prompt
        
        url = 'http://127.0.0.1:7860'
        
        r = requests.post(
            url=f'{url}/sdapi/v1/txt2img',
            json=payload
        ).json()
        
    else:
        pipe = StableDiffusionPipeline.from_pretrained(
            pretrained_model_name_or_path=model_id, 
            torch_dtype=torch.float16
        )
        
    if 'error' in r.keys():
        await bot.send_message(
            message.chat.id,
            r['error']
        )
        
    else:
        img_name = await generate_random_order_number(ORDER_CODE_LENTH + 3)
        id = await generate_random_order_number(CODE_LENTH)
        
        msg = ''
        for k, v in r['parameters'].items():
            msg += f'{k}:{v}\n'
        
        if model_id['path'] == 'sdapi':
            image = Image.open(io.BytesIO(base64.b64decode(r['images'][0])))
        else:
            # pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
            pipe = pipe.to("cuda")
            image = pipe(prompt=prompt).images[0]
        
        path = f"files\\ai_img\\{str(img_name)}.png"
        image.save(path)
        
        ai_img = await bot.send_photo(message.chat.id, open(path, "rb"))
        
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
        # "Да, отличное изображение ☘️",
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
    # "Хочу примеры текста изображения"
    elif message.text == kb_admin.client_want_to_try_another_later_img[
        "client_want_to_get_example_text_for_ai_img"
    ]:
        
        await bot.send_message(message.from_id, f"{MSG_TEXT_EXAMPLES_LINKS}")

        await bot.send_message(
            message.from_id, 
            "📃 Примеры простых тестов:"
        )
        await bot.send_photo(
            message.from_id,
            open("files\\ai_img\\womam_examples\\3.jpg", "rb"),
            examples_imgs["MSG_EXAMPLE_TEXT_PORTRAIT_WOMAN_MODEL_IN_HOME_EASY"],
        )
        time.sleep(3)
        await bot.send_photo(
            message.from_id,
            open("files\\ai_img\\womam_examples\\2.jpg", "rb"),
            examples_imgs["MSG_EXAMPLE_TEXT_PORTRAIT_WOMAN_MODEL_IN_HOME_EASY"],
        )

        await bot.send_photo(
            message.from_id,
            open("files\\ai_img\\womam_examples\\1.jpg", "rb"),
            examples_imgs["MSG_EXAMPLE_TEXT_BACK_WOMAN_MODEL_IN_HOME_EASY"],
        )

        time.sleep(3)
        await bot.send_message(
            message.from_id,
            MSG_FILL_TEXT_OR_CHOICE_VARIANT
        )
    # 'Сгенерируй мне модель женщины'
    elif (
        message.text == kb_admin.client_want_to_try_another_later_img[
            "admin_want_to_generate_img_from_ai_woman"
        ]
    ):  
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
        time.sleep(3)
        await bot.send_message(
            message.from_id, f"{MSG_GET_DESCRIPTION_WOMAN_MODEL_FROM_ADMIN_CONCEPTS}"
        )
        time.sleep(3)
        await bot.send_message(message.from_id, f"{MSG_STYLES_CHROMATIC_PALETTES}")
        time.sleep(3)
        await bot.send_message(message.from_id, f"{MSG_STYLES_MONOCHROMATIC_PALETTES}")
        time.sleep(3)
        await bot.send_message(message.from_id, f"{MSG_STYLES_CONTRAST}")
        time.sleep(3)
        await bot.send_message(message.from_id, f"{MSG_MOTION_PICTURE_PROCESS}")
        time.sleep(3)
        await bot.send_message(
            message.from_id, f"{MSG_ADD_SYMBOLS_FOR_GETTING_STRONGER_WORD}"
        )
        time.sleep(3)
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
    
    # --------------CHANGE_AI_MODEL--------------------------
    elif (
        message.text == kb_admin.client_want_to_try_another_later_img[
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
                msg += f"- {model['path']}\n"
                kb.add(KeyboardButton(model['path']))
                
        kb.add(kb_client.back_btn).add(kb_client.cancel_btn)

        await bot.send_message(
            message.chat.id,
            f"{msg}\n"
            f"❔ Какую модель выбрать?",
            reply_markup=kb
        )
        
    # --------------EXPERT_MODE--------------------------
    elif (
        message.text == kb_admin.client_want_to_try_another_later_img[
            "expert_mode"
        ]
    ):
        '''
            Лучшие параметры фото были такими:
            -- Sampling method: DPM++2M SDE Karras
            -- Upscaler SwinIR 4x
            -- Hires steps 1
            -- Sampling steps 20
            -- Restore faces
            -- CFG Scale 9
            -- WxH - 704
            -- Denoising strenght 0.7
            -- Seed 2262561837
            -- Negative prompt: (deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.3), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation
            
        Возможно, лучше всего действовать через АПИ 
        https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
        '''
        await state.finish()
        # -> get_steps_expert_mode_generate_ai_img
        await FSM_ai_expert_mode.choice_step_number.set()
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(100, 2000, 100):
            kb.add(KeyboardButton(i))
        kb.add(kb_admin.back_btn).add(kb_admin.cancel_btn)
        await bot.send_message(
            message.chat.id,
            f"❔ Сколько стэпов? Обычно от 200 до 100",
            reply_markup=kb
        )
        
    else:
        # -> change_ai_img_state
        await FSM_Admin_generate_ai_woman_model.next()
        # Создание модели девушки из этого описания
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
                f"{MSG_CLIENT_GO_BACK}{MSG_FILL_TEXT_OR_CHOICE_VARIANT}",
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


""" # -----------CHANGE_PARAM------------

async def command_change_ai_parameters(
    message: types.Message, 
    state: FSMContext
    ):
    if message.text == 'Изменить модель' """

# --------------EXPERT_MODE--------------------------
async def get_new_ai_model(message: types.Message, state: FSMContext):
    
    tmp_dct = {}    
    models_lst = []
    config_file = f"files\models_configuration.json"
    
    with open(config_file) as f:
        models = json.load(f)
        
    for model in models.values():
        models_lst.append(model['path'])
    
    if message.text in models_lst:
        for keys, model in models.items():
            n_steps = models[keys]['n_steps']
            
            if keys == 'work':    
                tmp_dct[keys] = {"path":message.text}
                tmp_dct[model['path']] = models[keys]['path']
                
            else:
                tmp_dct[keys] = {"path":models[keys]['path']}
                
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
        
    elif (message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS):
        await state.finish()
        await message.reply(MSG_BACK_TO_HOME, reply_markup=kb_admin.kb_main)
        
    elif message.text in LIST_BACK_COMMANDS:
        await state.finish()
        # -> command_generage_woman_model_img
        await FSM_Admin_generate_ai_woman_model.tattoo_desc.set()
        await bot.send_message(
            message.chat.id, 
            f"{MSG_FILL_TEXT_OR_CHOICE_VARIANT}",
            reply_markup=kb_admin.kb_client_want_to_try_another_later_img
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
    

# TODO продвинутый режим, где будет выбор количества эпох и других параметров
""" 
    Summary:
    1) модель stabilityai/stable-diffusion-xl-base-1.0 дает неплохие результаты для начала
    но слишком долго - 9-10 минут на изображение
    https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0

    2) модель stable-diffusion-v1-5 отрабатывает ужасно, но делает зато быстро

    3) параметры степа и размера изображения банально не срабатывают 
"""

"""
    Для экспертного режима выбираем следующие параметры:
        1) n_steps 
        2) high_noise_frac 
        3) output_type - обычно "latent"
        
    Параметры внутри from_pretrained:
        1) text_encoder_2=base.text_encoder_2
        2) vae=base.vae
        3) torch_dtype=torch.float16
        4) use_safetensors=True
        5) variant="fp16"
"""

"""
    Json для /stapi/v1/txt2img
    
    {
        "prompt": "",
        "negative_prompt": "",
        "styles": [
            "string"
        ],
        "seed": -1,
        "subseed": -1,
        "subseed_strength": 0,
        "seed_resize_from_h": -1,
        "seed_resize_from_w": -1,
        "sampler_name": "string",
        "batch_size": 1,
        "n_iter": 1,
        "steps": 50,
        "cfg_scale": 7,
        "width": 512,
        "height": 512,
        "restore_faces": true,
        "tiling": true,
        "do_not_save_samples": false,
        "do_not_save_grid": false,
        "eta": 0,
        "denoising_strength": 0,
        "s_min_uncond": 0,
        "s_churn": 0,
        "s_tmax": 0,
        "s_tmin": 0,
        "s_noise": 0,
        "override_settings": {},
        "override_settings_restore_afterwards": true,
        "refiner_checkpoint": "string",
        "refiner_switch_at": 0,
        "disable_extra_networks": false,
        "comments": {},
        "enable_hr": false,
        "firstphase_width": 0,
        "firstphase_height": 0,
        "hr_scale": 2,
        "hr_upscaler": "string",
        "hr_second_pass_steps": 0,
        "hr_resize_x": 0,
        "hr_resize_y": 0,
        "hr_checkpoint_name": "string",
        "hr_sampler_name": "string",
        "hr_prompt": "",
        "hr_negative_prompt": "",
        "sampler_index": "Euler",
        "script_name": "string",
        "script_args": [],
        "send_images": true,
        "save_images": false,
        "alwayson_scripts": {}
        }
"""


# Экспертный режим, начало, вопрос о количестве степов
async def get_steps_expert_mode_generate_ai_img(
    message: types.Message, 
    state: FSMContext
    ):
    if message.text.isdigit():
        async with state.proxy() as data:
            data['prompt'] = ''
            data['negative_prompt'] = "(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.3), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation"
            data["seed"]= -1
            data["subseed"]= -1
            data["subseed_strength"]= 0
            data["seed_resize_from_h"]= -1
            data["seed_resize_from_w"]= -1
            data["sampler_name"]= ""
            data["batch_size"]= 1
            data["n_iter"] = 1
            data['steps'] = int(message.text)
        
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("-1"))
        kb.add(kb_admin.back_btn).add(kb_admin.cancel_btn)
        
        await bot.send_message(
            message.chat.id, 
            f"❔ Какое значение у seed? Введи шестизначное значение или -1 (Случайное)",
            reply_markup=kb
        )
        
        await FSM_ai_expert_mode.next() # get_seed_number
    elif message.text in LIST_BACK_COMMANDS:
        await state.finish()
        # -> command_generage_woman_model_img
        await FSM_Admin_generate_ai_woman_model.tattoo_desc.set()
        await bot.send_message(
            message.chat.id, 
            f"{MSG_FILL_TEXT_OR_CHOICE_VARIANT}",
            reply_markup=kb_admin.kb_client_want_to_try_another_later_img
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_seed_number(
    message: types.Message, 
    state: FSMContext
    ):
    
    if message.text.isdigit() or message.text in ['-1', "Случайное"]:
        async with state.proxy() as data:
            if message.text == 'Случайное':
                data['seed'] = int(await generate_random_order_number(6))
            else:
                data['seed'] = int(message.text)
            
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(1, 9):
            kb.add(KeyboardButton(str(i)))
        kb.add(kb_admin.back_btn).add(kb_admin.cancel_btn)
        
        await bot.send_message(
            message.chat.id, 
            f"❔ Какое значение у батча? Введи значение от 1 до 8",
            reply_markup=kb
        )
        
        await FSM_ai_expert_mode.next() # -> get_batch_size
    
    elif message.text in LIST_BACK_COMMANDS:
        # -> get_steps_expert_mode_generate_ai_img
        await FSM_ai_expert_mode.previous()
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(100, 2000, 100):
            kb.add(KeyboardButton(i))
        kb.add(kb_admin.back_btn).add(kb_admin.cancel_btn)
        await bot.send_message(
            message.chat.id,
            f"❔ Сколько стэпов? Обычно от 200 до 100",
            reply_markup=kb
        )
        
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_batch_size(
    message: types.Message, 
    state: FSMContext
    ):
    
    if message.text.isdigit():
        async with state.proxy() as data:
            data['batch_size'] = int(message.text)
            print(f"data['batch_size'] = {message.text}")
        await bot.send_message(
            message.chat.id, 
            f"❔ Какое значение у cfg scale? Введи значение от 6 до 20. В среднем - диапазон от 7 до 9",
            reply_markup=kb_client.kb_another_number_details
        )
        
        await FSM_ai_expert_mode.next() # -> get_cfg_scale
    
    elif message.text in LIST_BACK_COMMANDS:
        # -> 
        await FSM_ai_expert_mode.previous()
    
        
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_cfg_scale(
    message: types.Message, 
    state: FSMContext
    ):
    print(await state.get_state())
    if message.text.isdigit():
        async with state.proxy() as data:
            data['cfg_scale'] = int(message.text)
        await bot.send_message(
            message.chat.id, 
            f"❔ Какой размер картинки? Введи значение от 512х512 до 832x832",
            reply_markup=kb_admin.kb_ai_img_size
        )
        # get_ai_img_size
        await FSM_ai_expert_mode.next()
    
    elif message.text in LIST_BACK_COMMANDS:
        # -> get_seed_number
        await FSM_ai_expert_mode.previous()
    
        await bot.send_message(
            message.chat.id, 
            f"Какое значение у seed? Введи шестизначное значение или -1",
            reply_markup=kb_client.kb_back_cancel
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_ai_img_size(
    message: types.Message, 
    state: FSMContext
    ):
    if message.text in kb_admin.ai_img_size:
        async with state.proxy() as data:
            data['width'] = int(message.text.split('x')[0])
            data['height'] = int(message.text.split('x')[0])
            
        await bot.send_message(
            message.chat.id, 
            f"Выставляем восстановление лиц? ",
            reply_markup=kb_client.kb_yes_no
        )
        # get_restore_faces
        await FSM_ai_expert_mode.next()
    
    elif message.text in LIST_BACK_COMMANDS:
        # -> get_batch_size
        await FSM_ai_expert_mode.previous()
    
        await bot.send_message(
            message.chat.id, 
            f"❔ Какое значение у cfg scale? Введи значение от 6 до 20. В среднем - диапазон от 7 до 9",
            reply_markup=kb_client.kb_another_number_details
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_restore_faces(
    message: types.Message, 
    state: FSMContext
    ):
    if message.text == kb_client.yes_str:
        async with state.proxy() as data:
            data['restore_faces'] = True
            
        kb= ReplyKeyboardMarkup(resize_keyboard=True)
        for i in np.arange(0.0, 1.0, 0.1):
            kb.add(KeyboardButton(i))
        kb.add(kb_admin.back_btn).add(kb_admin.cancel_btn)
        
        await bot.send_message(
            message.chat.id, 
            f"❔ Какое значение у шума (denoising_strength)? Введи от 0.0 до 1.0. Обычно 0.7",
            reply_markup=kb
        )
        await FSM_ai_expert_mode.next() # get_denoising_strength
    
    elif message.text in LIST_BACK_COMMANDS:
        # -> 
        await FSM_ai_expert_mode.previous()
    
        
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_denoising_strength(
    message: types.Message, 
    state: FSMContext
    ):
    if float(message.text) in [i for i in np.arange(0.0, 1.0, 0.1)]:
        async with state.proxy() as data:
            data['denoising_strength'] = float(message.text)
        
        await bot.send_message(
            message.chat.id, 
            f"❔ Какое значение у sampler-а? Выбери сэмплер из списка",
            reply_markup=kb_admin.kb_sampler_names
        )
        await FSM_ai_expert_mode.next() # get_sampler_name
        
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_sampler_name(
    message: types.Message, 
    state: FSMContext
    ):
    if message.text in kb_admin.sampler_names:
        async with state.proxy() as data:
            data['sampler_name'] = message.text
            payload_from_data = dict(data)
            
        option_file = "files\sd_api_options.json"
        with open(option_file, encoding="cp1251") as f:
            option = json.load(f)
        
        for keys, value in payload_from_data.items():
            option[keys] = value
        
        with open(option_file, "w", encoding="cp1251") as f:
            json.dump(option, f, indent=2, ensure_ascii=True)
            
        # -> command_generage_woman_model_img
        await FSM_Admin_generate_ai_woman_model.tattoo_desc.set()
        await bot.send_message(
            message.chat.id, 
            (
                f"🎉 Готово! Параметры генерации изменились на \n" +
                "".join([f'{k}:{v}\n' for k, v in dict(data).items()]) + 
                f"{MSG_FILL_TEXT_OR_CHOICE_VARIANT}"
            ),
            reply_markup=kb_admin.kb_client_want_to_try_another_later_img
        )
        
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


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

    dp.register_message_handler(
        get_steps_expert_mode_generate_ai_img,
        state=FSM_ai_expert_mode.choice_step_number
    )
    dp.register_message_handler(get_seed_number,
        state=FSM_ai_expert_mode.get_seed
    )
    
    dp.register_message_handler(get_batch_size,
        state=FSM_ai_expert_mode.get_batch
    )
    dp.register_message_handler(get_cfg_scale,
        state=FSM_ai_expert_mode.get_cfg_scale
    )
    dp.register_message_handler(get_ai_img_size,
        state=FSM_ai_expert_mode.get_ai_img_size
    )
    dp.register_message_handler(get_restore_faces,
        state=FSM_ai_expert_mode.get_restore_faces
    )
    dp.register_message_handler(get_denoising_strength,
        state=FSM_ai_expert_mode.get_denoising_strength
    )
    dp.register_message_handler(get_sampler_name,
        state=FSM_ai_expert_mode.get_sampler_name
    )