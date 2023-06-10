from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    MenuButton,
)
from keyboards.kb_admin import create_kb
from msg.main_msg import LIST_BACK_TO_HOME

# 📷 ⏱ 🛠 ⚙️ 📎 ❤️ ☎️ 🗓 🌿 💬 🕒 🔴 🟢 🟡 ⁉️‼️ ❓ ❕ ❌ ⭕️ 🛑 ⛔️ ☘️ 🖇 🎨 ➡️ ❗️
# 🍀 🌴 🍃 🕸 💳 🎉 🎁 📃 🎫  🏚 🔙 ❔ 📏 😓 📅 ⚡️\ 🚫 ⏪ 🔄 🔆 💰 🔧 📅 🗾 🪴

back_lst = ["Назад 🔄"]
cancel_lst = ["Отмена ❌"]
yes_str = "Да 🍀"
no_str = "Нет ❌"
yes = KeyboardButton(yes_str)
no = KeyboardButton(no_str)
now_str = "Сейчас 🍀"
later_str = "Потом 🕒"
back_btn = KeyboardButton(back_lst[0])
cancel_btn = KeyboardButton(cancel_lst[0])
later = KeyboardButton(later_str)
now = KeyboardButton(now_str)

next_action_lst = ["Далее ➡️"]
no_tattoo_note_from_client = ["Мне нечего добавить 🙅‍♂️"]
colored_tattoo_choice = ["Ч/б тату 🖤", "Цветное тату ❤️"]

get_information = {
    "send_info_sketch_development": "Разработка эскиза 🛠",
    "send_info_contraindications": "Противопоказания 🚫",
    "send_info_preparing": "Подготовка к сеансу 🪖",
    "send_info_couple_tattoo": "Парная татуировка 👥",
    "send_info_tattoo_care": "Уход за тату 🕸",
    "send_info_restrictions_after_the_session": "Ограничения после сеанса 🙅‍♂️",
    "send_info_correction": "Коррекция 🔧",
    "send_info_address": "Адрес 🏰",
    "send_info_cooperation": "Сотрудничество 👫",
}

choice_order_type_to_payloading = {
    "Тату заказы 🕸": ["переводное тату", "постоянное тату"],
    "Заказы эскизов 🎨": ["эскиз"],
    "Гифтбоксы 🎁": ["гифтбокс"],
    "Сертификаты 🎫": ["сертификат"],
}

size_dict = {
    "10-15": "10 - 15 см2",
    "15-20": "15 - 20 см2",
    "20-25": "20 - 25 см2",
    "25-35": "25 - 35 см2",
}

another_size = "Другой размер"

number_tattoo_details = {
    "1_detail": "1 основная деталь",
    "2_detail": "2 основных детали",
    "3_detail": "3 основных детали",
    "4_detail": "4 основных детали",
    "5_detail:": "5 основных детали",
    "more_details": "Точно больше пяти основных деталей",
}

description_ai_generation_img = "Инструкция по генерации изображения"

tattoo_body_places = [
    "Лицо 🧑🏻‍🦲",
    "Шея 👤",
    "Левое плечо 💪",
    "Грудь 🫁",
    "Правое плечо 🦾",
    "Живот 🥼",
    "Пальцы правой руки 👈",
    "Правая ладонь 🤚",
    "Правая рука 💪",
    "Левая рука 🦾",
    "Левая ладонь ✋",
    "Пальцы левой руки 👉",
    "Левая Лопатка 💪",
    "Поясница 👤",
    "Правая Лопатка 🦾",
    "Левое бедро 🦵",
    "Правое бедро 🦿",
    "Пальцы правой ноги 👣",
    "Правая нога 👢",
    "Левая нога 🧦",
    "Пальцы левой ноги 👣",
    "Другое место 🙅‍♂️",
    "Пока не знаю, какое место я хотел бы выбрать 🤷🏻‍♂️",
]

client_still_want_his_sketch = "Все же хочу свой эскиз для тату 🙅‍♂️"

client_main = {
    "client_want_tattoo": "Тату 🕸",
    "client_want_consultation": "Консультация 🌿",
    "client_want_tattoo_sketch": "Эскиз 🎨",
    "client_want_giftbox": "Гифтбокс 🎁",
    "client_want_cert": "Сертификат 🎫",
    "free_dates": "Свободные даты 🗓",
    "clients_orders": "Мои заказы 📃",
    "client_schedule": "Сеансы 🕒",
    "payload_order": "Оплатить заказ 💳",
    "about_tattoo_master": "О тату мастере 🧾",
    "important_info": "Важная информация ❕",
    # ,'Закончить 🌴''Хочу создать тату эскиз 📷'
}

client_schedule_menu = {
    "view_client_events": "Посмотреть мои сеансы 📃",
    "add_new_event": "Новый сеанс 🕒",
    "change_event": "Изменить мой сеанс 🔧",
}

choice_order_view = {
    "client_watch_tattoo_order": "Посмотреть мои тату заказы 🕸",
    "client_add_photo_to_tattoo_order": "Добавить фотографии к тату заказу 📷",
    "client_add_photo_to_sketch_order": "Добавить фотографию к заказу эскиза 🌿",
    "client_watch_giftbox_order": "Посмотреть мои гифтбоксы 🎁",
    "client_watch_cert_order": "Посмотреть мои сертификаты 🎫",
    "client_watch_sketch_order": "Посмотреть мои заказы эскизов 🎨",
    # "client_add_new_schedule_event":    'Добавить новую дату сеанса'
}

choice_order_pay = [
    "Оплатить мой тату заказ 🕸",
    "Оплатить мой гифтбокс заказ 🎁",
    "Оплатить мой сертификат 🎫",
    "Оплатить мой эскиз 🎨",
] + LIST_BACK_TO_HOME


def create_other_size_lst() -> list:
    kb = []
    for t in range(5, 40, 5):
        for i in range(5, 40, 5):
            kb.append(f"{i}x{t}")
    return kb


def create_other_size_btn() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    btn = []
    for j in range(5, 40, 5):
        for i in range(5, 40, 5):
            btn.append(KeyboardButton(f"{i}x{j}"))
            if len(btn) == 5:
                kb.row(btn[0], btn[1], btn[2], btn[3], btn[4])
                btn = []

    kb.add(back_btn).add(cancel_btn)
    return kb


def create_another_size_lst() -> list:
    tmp_lst = []
    for j in range(5, 40, 5):
        for i in range(5, 40, 5):
            tmp_lst.append(f"{i}x{j}")
    return tmp_lst


another_size_lst = create_another_size_lst()


def list_other_number_details() -> list:
    list_details = []
    for i in range(6, 35):
        list_details.append(str(i))
    return list_details


no_photo_in_tattoo_order = {
    "look_tattoo_galery": "Посмотреть галерею тату 📃",
    "load_tattoo_photo": "Загрузить свою фотографию эскиза 📎",
    "load_tattoo_desc": "Хочу эскиз по моему описанию 💬",
    "no_idea_tattoo_photo": "У меня нет идеи для эскиза 😓",
}

choice_place_tattoo = {
    "client_know_place": "Выбрать место 👤",
    "client_has_no_idea_for_place": "Пока не знаю, где будет мое тату 😓",
}

choice_get_photo_for_place_tattoo = {
    "client_want_to_get_place": "Отправить фото/видео 📎",
    "client_dont_want_to_get_place": "Не отправлять, идем дальше ➡️",
}

start_dialog_sketch_order = {"client_want_to_see_galery": "Посмотреть галерею 📃"}

want_another_ai_img = {"want_another_ai_img": "Хочу еще раз попробовать создать эскиз"}

phone_number = {
    "client_send_contact": "Отправить свой телефон ☎️",
    "client_dont_send_contact": "Не оставлять свой телефон, только телеграм 💬",
}

client_choice_send_more_photo_to_skatch_order = {
    "more_photo": "Отправить еще фото 📎",
    "end_order": "Закончить заказ эскиза ➡️",
}

kb_phone_number = (
    ReplyKeyboardMarkup(resize_keyboard=True)
    .add(KeyboardButton(phone_number["client_send_contact"], request_contact=True))
    .add(KeyboardButton(phone_number["client_dont_send_contact"]))
)

client_want_to_get_example_text_for_ai_img = "Хочу пример текста изображения"

""" kb_client_main =  ReplyKeyboardMarkup(resize_keyboard=True).row(
    KeyboardButton('Хочу тату 🕸'), KeyboardButton('Хочу консультацию 🌿'),
    KeyboardButton('Хочу гифтбокс 🎁'), KeyboardButton('Хочу сертификат 🎫'), 
).add(KeyboardButton('Свободные даты')).add(KeyboardButton('Посмотреть мои заказы')
).add(KeyboardButton('Оплатить заказ')).add(KeyboardButton('О тату мастере')) """

kb_cancel = ReplyKeyboardMarkup(resize_keyboard=True).add(cancel_btn)
kb_back = ReplyKeyboardMarkup(resize_keyboard=True).add(back_btn)
kb_back_cancel = ReplyKeyboardMarkup(resize_keyboard=True).add(back_btn).add(cancel_btn)

# b16 = KeyboardButton('Хочу готовый гифтбокс')
# menu_client_main_button = MenuButton(client_main)

correct_photo_from_ai_or_get_another = {
    "correct_photo_from_ai": "Да, отличное изображение, хочу такой эскиз ☘️",
    "client_want_to_change_this_text": "Хочу поменять данный текст и получить другое изображение 🛠",
    "client_want_to_try_again": "Хочу попробовать еще раз с тем же текстом 💬",
    "client_want_to_try_another_later_img": "Хочу попробовать еще раз с другими моими текстами 🎨",
    "want_another_ai_img": "Нет, хочу другое изображение 😓",
}

choice_main_or_temporary_tattoo = {
    "main_tattoo": "Постоянное тату 🕸",
    "temporary_tattoo": "Переводное тату 🕒",
}

client_choice_add_another_photo_to_tattoo_order = {
    "client_want_to_add_sketch_to_tattoo_order": "Добавить еще одно изображение ☘️",
    "client_dont_want_to_add_sketch_to_tattoo_order": "Закончить с добавлением изображений ➡️",
}

client_choice_add_photo_type = {
    "client_want_to_add_sketch_photo": "Добавить фото для эскиза 🎨",
    "client_want_to_add_body_photo": "Добавить фото части тела 👤",
}

kb_choice_order_type_to_payloading = create_kb(
    list(choice_order_type_to_payloading.keys()) + cancel_lst
)
kb_client_choice_add_photo_type = create_kb(
    list(client_choice_add_photo_type.values()) + back_lst + cancel_lst
)
kb_client_choice_add_another_photo_to_tattoo_order = create_kb(
    list(client_choice_add_another_photo_to_tattoo_order.values())
    + back_lst
    + cancel_lst
)
kb_next_action = create_kb(next_action_lst + back_lst + cancel_lst)
kb_client_schedule_menu = create_kb(
    list(client_schedule_menu.values()) + LIST_BACK_TO_HOME
)
kb_get_information = create_kb(list(get_information.values()) + LIST_BACK_TO_HOME)
kb_no_photo_in_tattoo_order = create_kb(
    list(no_photo_in_tattoo_order.values()) + back_lst + cancel_lst
)
kb_colored_tattoo_choice = create_kb(colored_tattoo_choice + back_lst + cancel_lst)
kb_choice_get_photo_for_place_tattoo = create_kb(
    list(choice_get_photo_for_place_tattoo.values()) + back_lst + cancel_lst
)
kb_want_another_ai_img = create_kb(
    list(want_another_ai_img.values()) + back_lst + cancel_lst
)
kb_correct_photo_from_ai_or_get_another = create_kb(
    list(correct_photo_from_ai_or_get_another.values()) + back_lst + cancel_lst
)
kb_no_tattoo_note_from_client = create_kb(
    no_tattoo_note_from_client + back_lst + cancel_lst
)
kb_client_main = create_kb(list(client_main.values()))
kb_client_price_сert = ReplyKeyboardMarkup(resize_keyboard=True)
kb_gitf_main_choice = ReplyKeyboardMarkup(resize_keyboard=True)
kb_yes_no = (
    ReplyKeyboardMarkup(resize_keyboard=True).row(yes, no).add(back_btn).add(cancel_btn)
)
kb_have_yes_no = ReplyKeyboardMarkup(resize_keyboard=True)
kb_pay_now_later = (
    ReplyKeyboardMarkup(resize_keyboard=True)
    .row(now, later)
    .add(back_btn)
    .add(cancel_btn)
)
kb_okey = ReplyKeyboardMarkup(resize_keyboard=True)
kb_giftbox_changes_choice = ReplyKeyboardMarkup(resize_keyboard=True)
kb_choice_order_view = create_kb(list(choice_order_view.values()) + LIST_BACK_TO_HOME)
kb_choice_order_pay = create_kb(choice_order_pay)
kb_choice_place_tattoo = create_kb(
    list(choice_place_tattoo.values()) + back_lst + cancel_lst
)
kb_client_choice_main_or_temporary_tattoo = create_kb(
    list(choice_main_or_temporary_tattoo.values()) + cancel_lst
)
# Количество деталей в тату
""" kb_number_tattoo_details = ReplyKeyboardMarkup(resize_keyboard=True).row(
    one_detail, two_details, three_details, four_details, five_details, more_details
    ).add(back_btn).add(cancel_btn) 
"""
kb_number_tattoo_details = create_kb(
    list(number_tattoo_details.values()) + back_lst + cancel_lst
)
another_number_details = [str(i) for i in range(6, 35)]
kb_another_number_details = create_kb(another_number_details + back_lst + cancel_lst)
kb_start_dialog_sketch_order = create_kb(
    list(start_dialog_sketch_order.values()) + cancel_lst
)

kb_client_size_tattoo = create_kb(list(size_dict.values()) + back_lst + cancel_lst)

kb_another_size = create_other_size_btn()

kb_client_choice_send_more_photo_to_skatch_order = create_kb(
    list(client_choice_send_more_photo_to_skatch_order.values()) + back_lst + cancel_lst
)

tattoo_from_galery_change_options = {
    "client_want_to_change_tattoo_name": "Хочу дать свое название тату 💬",
    # 'client_want_to_change_tattoo_size':    'Хочу изменить размер тату 📏',
    "client_want_to_change_tattoo_color": "Хочу изменить цвета у тату 🎨",
    "client_want_to_change_tattoo_details": "Хочу изменить детали на тату 🔧",
    "no_change": "Ничего не хочу менять ➡️",
}
kb_tattoo_from_galery_change_options = create_kb(
    list(tattoo_from_galery_change_options.values()) + back_lst + cancel_lst
)
no_name_for_tattoo = ["Пока не знаю, какое будет имя 🤷🏻‍♂️"]

kb_no_name_for_tattoo = create_kb(no_name_for_tattoo + back_lst + cancel_lst)
# ✋🤚💪🦾🦵🦿☝️👤🧑🏻‍🦲
# TODO доделать вывод мест для тату
kb_place_for_tattoo = create_kb(tattoo_body_places + back_lst + cancel_lst)

giftbox_note_dict = {
    "client_want_to_add_something": "Да, мне есть чего добавить! 🌿",
    "client_dont_add_something": "Нечего добавить ➡️",
}

kb_giftbox_note = create_kb(list(giftbox_note_dict.values()) + cancel_lst)
