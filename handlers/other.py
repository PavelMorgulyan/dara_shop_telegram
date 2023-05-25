import random, string
from datetime import datetime

MONTH_NAME_RU = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май',
    'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

MONTH_NAME_EN = ['january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december']

STATES = {
    "open" :        'Открыт',
    "processed" :   "Обработан",
    "paid":         "Оплачен",
    "in_work":      "Выполняется",
    "complete" :    'Выполнен',
    "closed":{
        "rejected":     'Отклонен', 
        "postponed":    'Отложен', 
        "canceled":     'Аннулирован'
    }
}

DAYS = {
    'Понедельник' : 'Monday', 
    'Вторник':      'Tuesday', 
    'Среда' :       'Wednesday', 
    'Четверг' :     'Thursday', 
    'Пятница' :     'Friday', 
    'Суббота' :     'Saturday', 
    'Воскресенье' : 'Sunday', 
}

statuses_order_lst = list(STATES.values())[:-1] + list(STATES["closed"].values())


async def get_month_from_number(num: int, lang:str) -> str:
    
    if lang == 'en':
        return MONTH_NAME_EN[num - 1]
    else:
        return MONTH_NAME_RU[num - 1]


async def get_month_number_from_name(month_name: str) -> int:
    for i in range(len(MONTH_NAME_RU)):
        if month_name == MONTH_NAME_RU[i]:
            return int(i+1)
    return 0


async def get_dates_from_month_and_day_of_week(
    day:str,
    month: str, 
    year: str, 
    start_time: str, 
    end_time:str) -> list:
    
    date_time_list = []
    i = 0
    while i < 30:
        # try:
        i += 1
        month_number = await get_month_number_from_name(month)
        
        start_datetime = datetime.strptime(
            f"{year}-{month_number}-{i} {start_time}", '%Y-%m-%d %H:%M' 
        )
        
        end_datetime = datetime.strptime(
            f"{year}-{month_number}-{i} {end_time}", '%Y-%m-%d %H:%M' 
        )
        
        if start_datetime.strftime('%A') == DAYS[day] and start_datetime >= datetime.now():
            date_time_list.append({"start_datetime": start_datetime, "end_datetime": end_datetime})
        """ except:
            pass """
        
    return date_time_list


async def generate_random_code(length: int) -> str:
    letters = string.ascii_uppercase + string.digits
    rand_string = ''.join(random.choice(letters) for i in range(length))
    return rand_string


async def generate_random_order_number(length: int) -> str:
    letters = string.digits
    rand_string = ''.join(random.choice(letters) for i in range(length))
    return rand_string