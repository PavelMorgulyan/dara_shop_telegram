from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, MenuButton
# from keyboards.kb_client import *
from msg.main_msg import LIST_BACK_TO_HOME
from handlers.other import statuses_order_lst
from datetime import datetime


another_price_lst = ['Другая цена']
another_price_btn = KeyboardButton(another_price_lst[0])
back_lst = ['Назад 🔄'] 
cancel_lst = ['Отмена ❌']
yes = KeyboardButton('Да 🍀') 
no = KeyboardButton('Нет ❌')
back_btn = KeyboardButton(back_lst[0])
cancel_btn = KeyboardButton(cancel_lst[0])
later = KeyboardButton('Потом 🕒')
now = KeyboardButton('Сейчас 🍀')

commands_button = [
    'Команды',
    'Начать как пользователь',
    'Расписание',
    'Тату заказы',
    'Эскиз заказы',
    'Татуировки',
    'Гифтбокс заказ',
    'Гифтбокс продукт',
    'Сертификат',
    'Свеча',
    'Прайс-лист',
    'Пользователи',
    'Хочу создать изображение',
    'Удалить таблицу',
    'Создать json файл',
    'Получить данные из json',
    '/help'
]

tattoo_order_commands =[ 
    'добавить тату заказ',
    'посмотреть тату заказы',
    'посмотреть тату заказ',
    'удалить тату заказ',
    'изменить статус тату заказа',
    'изменить тату заказ'
]

tattoo_sketch_commands =[ 
    'добавить эскиз заказ',
    'посмотреть эскиз заказы',
    'посмотреть эскиз заказ',
    'удалить эскиз заказ',
    'посмотреть активные эскиз заказы',
    'посмотреть удаленные эскиз заказы',
    'посмотреть закрытые эскиз заказы',
    'изменить статус эскиз заказа'
]

tattoo_items_commands = [
    'посмотреть тату',
    'посмотреть все тату',
    'добавить тату',
    'удалить тату',
    'посмотреть все мои тату',
    'посмотреть мои тату',
    'посмотреть все пользовательские тату',
    'посмотреть пользовательские тату',
    'изменить тату'
]

giftbox_order_commands = [
    'посмотреть гифтбокс заказы',
    'посмотреть закрытые гифтбокс заказы',
    'посмотреть активные оплаченные гифтбокс заказы',
    'посмотреть активные неоплаченные гифтбокс заказы',
    'поменять статус гифтбокс заказа'
]

giftbox_item_commands = [
    'добавить новый гифтбокс',
    'поменять цену гифтбокса',
    'посмотреть все гифтбоксы',
    'посмотреть гифтбокс'
]

schedule_commands = [
    'посмотреть мое расписание',
    'посмотреть мое занятое расписание',
    'посмотреть мое свободное расписание',
    'добавить дату в расписание',
    'изменить мое расписание',
    'посмотреть фотографии расписания',
    'посмотреть фотографию расписания',
    'добавить фото расписания',
    'удалить фото расписания',
    'удалить дату в расписании'
]

candle_item_commands = [
    'добавить свечу',
    'посмотреть список свечей',
    'посмотреть список имеющихся свечей',
    'посмотреть список не имеющихся свечей',
    'посмотреть свечу',
    'удалить свечу'
]

sert_item_commands = [
    'добавить заказ на сертификат',
    'посмотреть заказанные сертификаты'
]

clients_commands = [
    'посмотреть всех пользователей',
    'посмотреть пользователя',
    'удалить пользователя'
]


'''
    Открыт — заказ был создан в базе данных, но ещё не был обработан.
    Обработан — оплата была получена.
    Выполнен — вся работа по заказу завершена.
    Отклонен — заказ отклонен админом.
    Отложен — заказ ещё не обработан, так как в нём содержатся товары, которых нет в наличии или нет даты сеанса.
    Аннулирован — заказ был отменён покупателем.
    Ожидает ответа — заказ был создан, когда покупатель оформил заявку на обратный ответ.
'''


price_list_commands = [
    'посмотреть прайс-лист на тату',
    'изменить прайс-лист на тату',
    'создать новый прайс-лист на тату',
    'удалить прайс-лист на тату'
]


tattoo_order_change_info_list = {
    'Имя тату' :                    'tattoo_name',
    'Фотография/изображение тату':  'tattoo_photo',
    'Цвет тату':                    'colored',
    'Описание тату' :               'tattoo_note',
    'Описание заказа' :             'order_note',
    'Имя пользователя':             'username',
    'Телеграм пользователя':        'telegram',
    'Дату встречи' :                'date_mitting',
    'Время встречи' :               'time_mitting',
    'Фотография части тела':        'tattoo_place_file',
    'Место части тела для тату':    'bodyplace',
    'Цена':                         'price',
    'Тип тату':                     'tattoo_type'
}

tattoo_order_change_photo = {
    'Фотография тату': 'tattoo_photo',
    'Фото части тела': 'tattoo_place_file'
}

new_tattoo_item_state  = {
    'Имя':"name",
    'Фотография':"photo",
    'Цена':"price",
    'Размер':"size",
    'Цвет':"colored",
    'Количество деталей':"details_number",
    'Описание': "note",
    'Создатель' : "creator"
}


in_stock_button = ['Есть в наличии', 'Нет в наличии, нужно докупать']

# https://shinyband.com/glitterss
sequin_types = [
    'ShinyBand Биоглиттер Медь 600р', 
    'ShinyBand Биоглиттер Золото',
    'ShinyBand Биоглиттер Фуксия', 
    'ShinyBand Биоглиттер Серебро',
    'ShinyBand Биоглиттер Праймер',
    'ShinyBand Полупрозрачные/дуохромные Лила 350р',
    'ShinyBand Полупрозрачные/дуохромные Селена 350р',
    'ShinyBand Полупрозрачные/дуохромные Пегас 350р',
    'ShinyBand Полупрозрачные/дуохромные Аура 350р',
    'ShinyBand Полупрозрачные/дуохромные Лисий мед 350р',
    'ShinyBand Полупрозрачные/дуохромные Хамелион 350р',
    'ShinyBand Полупрозрачные/дуохромные Эйфория 350р',
    'ShinyBand Полупрозрачные/дуохромные Пикси 350р',
    'ShinyBand Полупрозрачные/дуохромные Неон 350р',
    'ShinyBand Полупрозрачные/дуохромные Снегопад 350р',
    'ShinyBand Полупрозрачные/дуохромные Новогодний 350р',
    'ShinyBand Полупрозрачные/дуохромные Созвездие риге 350р',
]


def create_kb_with_interval(lst: list, interval: int) -> ReplyKeyboardMarkup:
    kb_full_lst = []
    tmp_lst = []
    j = 0
    while j in range(len(lst) - interval):
        for i in range(interval):
            tmp_lst.append(KeyboardButton(lst[j + i]))
        kb_full_lst.append(tmp_lst)
        tmp_lst = []
        j += interval
    return ReplyKeyboardMarkup(keyboard=kb_full_lst, resize_keyboard=True)


def create_kb(text: list) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for item in text: 
        kb.add(KeyboardButton(item))
    return kb


#-----------------------------------------SCHEDULE------------------------------------------------------
event_type_schedule = ['Тату заказ', 'Консультация']

days = ['Понедельник', 'Вторник',
    'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

month = [ 'Январь', 'Февраль', 'Март', 'Апрель', 'Май',
    'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

years_lst = [i for i in range(int(datetime.now().strftime('%Y')), int(datetime.now().strftime('%Y'))+5)]

date_states = ['Статус', 'Месяц', 'Дату', 'Время начала работы', 'Время окончания работы']

choice_new_date_or_new_day_name =  ['Хочу ввести конкретную дату', 'Хочу выбрать день недели']

new_date_choice = {
    "one_date": 'Хочу ввести конкретную дату', 
    "many_dates": 'Хочу выбрать день недели и месяц'
}

free_or_close_event_in_schedule = ['Свободен', 'Занят']

type_of_schedule_lst = ['Тату заказ', 'Консультация']

choice_new_date_or_no_date_in_tattoo_order = {
    'new_date': 'Хочу поставить новую дату для этого тату заказа',
    'no_date':  'Хочу оставить дату для этого тату заказа неопределенной', 
    'info':     'Информация об изменении статусов календаря'
}

admin_chioce_get_new_order_to_schedule_event = {
    "new_order":            "Добавить самому новый заказ в этот календарный день",
    "choice_created_order": "Выбрать из тех заказов, у которых нет даты сеанса",
    "no_order":             "Оставить данный календарный день занятым без заказов"
}

schedule_for_tattoo_order_choice = ['Хочу выбрать дату из календаря', 'Хочу новую дату в календарь']

admin_want_to_generate_img_from_ai_woman = 'Сгенерируй мне модель женщины'

phone_answer = ['Я не знаю его телефона']

price_lst = [str(i) for i in range(1000, 20000, 1000)]

another_price_full_lst = [str(i) for i in range(1000, 50000, 1000)]

sizes_lst = [i for i in range(1, 100)]

admin_choice_watch_order_or_change_order = {
    'admin_want_to_watch_order' : 'Хочу еще посмотреть заказы',
    'admin_want_to_change_order': 'Хочу изменить информацию в заказе'
}

admin_add_name_or_telegram_for_new_order = {
    "Добавить имя пользователя": "username",
    "Добавить ссылку на тг пользователя": "telegram"
}

no_note = ['Без описания']

creator_lst = ['admin', 'client']


kb_back_home = create_kb(LIST_BACK_TO_HOME)

""" kb_price = ReplyKeyboardMarkup(resize_keyboard=True
    ).row(KeyboardButton('1 000'), KeyboardButton('2 000'), KeyboardButton('3 000'),
        KeyboardButton('4 000')
    ).row(KeyboardButton( '5 000'), KeyboardButton('6 000'), KeyboardButton('7 000'),
        KeyboardButton('8 000')
    ).row(KeyboardButton( '9 000'), KeyboardButton('10 000'), KeyboardButton('15 000'),
        KeyboardButton('20 000')
    ).add(KeyboardButton('Другая цена')).add(back_btn).add(cancel_btn) """



kb_price = create_kb_with_interval(price_lst, 5).add(another_price_btn).add(back_btn).add(cancel_btn)

kb_change_price_list = ReplyKeyboardMarkup(resize_keyboard=True
    ).row(KeyboardButton('Минимальный размер'), KeyboardButton('Макcимальный размер'),\
    KeyboardButton('Цена')).add(back_btn).add(cancel_btn)


client_want_to_try_another_later_img = {
    "admin_want_to_generate_img_from_ai_woman" :    "Сгенерируй мне модель женщины",
    "client_want_to_get_example_text_for_ai_img":   "Хочу примеры текста изображений",
    "description_ai_generation_img" :               "Хочу подробный текст с описанием о создании изображения",
    "correct_photo_from_ai_or_get_another" :        "Хочу попробовать еще раз с другими моими текстами 🎨"
}

admin_choice_create_new_or_created_schedule_item = {
    "create_new_schedule":      "Создать новое расписание",
    "choice_created_schedule":  "Выбрать из моего расписания"
}

kb_client_want_to_try_another_later_img = create_kb(
    list(client_want_to_try_another_later_img.values())
    + back_lst + cancel_lst
)

kb_order_statuses = create_kb(statuses_order_lst + back_lst + cancel_lst)

kb_admin_add_name_or_telegram_for_new_order = \
    create_kb(list(admin_add_name_or_telegram_for_new_order.keys()) + cancel_lst)
kb_admin_choice_watch_order_or_change_order = \
    create_kb(list(admin_choice_watch_order_or_change_order.values()) + cancel_lst)
kb_tattoo_order_change_info_list = \
    create_kb(list(tattoo_order_change_info_list.keys()) + back_lst + cancel_lst)
kb_another_price_full = create_kb(another_price_full_lst)                
kb_sizes = create_kb_with_interval(sizes_lst + LIST_BACK_TO_HOME, 5)                            
kb_no_note = create_kb(no_note + back_lst + LIST_BACK_TO_HOME)
kb_creator_lst = create_kb(creator_lst)
kb_new_tattoo_item_state = create_kb(list(new_tattoo_item_state.keys()) + LIST_BACK_TO_HOME)
kb_price_list_commands = create_kb(price_list_commands + LIST_BACK_TO_HOME)
kb_main = create_kb(commands_button)
kb_in_stock = create_kb(in_stock_button)
kb_change_status_order = create_kb(statuses_order_lst + LIST_BACK_TO_HOME)
kb_sequin_types = create_kb(sequin_types + LIST_BACK_TO_HOME)
kb_admin_has_no_phone_username = create_kb(phone_answer + LIST_BACK_TO_HOME)
kb_days_for_schedule = create_kb(days + [new_date_choice['one_date']] + LIST_BACK_TO_HOME)
kb_month_for_schedule = create_kb(month + LIST_BACK_TO_HOME)
kb_years = create_kb(years_lst + LIST_BACK_TO_HOME)
kb_date_states = create_kb(date_states + LIST_BACK_TO_HOME)
kb_new_date_choice = create_kb(list(new_date_choice.values()) + LIST_BACK_TO_HOME)
kb_choice_new_date_or_new_day_name = create_kb(choice_new_date_or_new_day_name + LIST_BACK_TO_HOME)
kb_free_or_close_event_in_schedule = create_kb(free_or_close_event_in_schedule + LIST_BACK_TO_HOME)
kb_type_of_schedule =  create_kb(type_of_schedule_lst + LIST_BACK_TO_HOME)
# kb_price = create_kb(price)
kb_choice_new_date_or_no_date_in_tattoo_order = \
    create_kb(list(choice_new_date_or_no_date_in_tattoo_order.values()) + LIST_BACK_TO_HOME)

kb_admin_chioce_get_new_order_to_schedule_event = create_kb(
    list(admin_chioce_get_new_order_to_schedule_event.values()) + LIST_BACK_TO_HOME)

    
kb_admin_choice_create_new_or_created_schedule_item = create_kb(list(
    admin_choice_create_new_or_created_schedule_item.values()) + LIST_BACK_TO_HOME)
kb_tattoo_order_commands = create_kb(tattoo_order_commands + LIST_BACK_TO_HOME)
kb_tattoo_sketch_commands = create_kb(tattoo_sketch_commands + LIST_BACK_TO_HOME)
kb_tattoo_items_commands = create_kb(tattoo_items_commands + LIST_BACK_TO_HOME)
kb_clients_commands = create_kb(clients_commands + LIST_BACK_TO_HOME)
kb_sert_item_commands = create_kb(sert_item_commands + LIST_BACK_TO_HOME)
kb_candle_item_commands = create_kb(candle_item_commands + LIST_BACK_TO_HOME)
kb_schedule_commands = create_kb(schedule_commands + LIST_BACK_TO_HOME)
kb_giftbox_item_commands = create_kb(giftbox_item_commands + LIST_BACK_TO_HOME)
kb_giftbox_order_commands = create_kb(giftbox_order_commands + LIST_BACK_TO_HOME)
kb_event_type_schedule = create_kb(event_type_schedule + LIST_BACK_TO_HOME)
kb_schedule_for_tattoo_order_choice = create_kb(schedule_for_tattoo_order_choice + LIST_BACK_TO_HOME)