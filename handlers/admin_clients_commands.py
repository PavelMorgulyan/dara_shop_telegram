from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_admin, kb_client
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES
from handlers.other import clients_status

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup

from prettytable import PrettyTable
from handlers.calendar_client import obj
from msg.main_msg import *

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *
import json

# -----------------------------------CLIENT-------------------------------------------
# /пользователи
async def get_clients_command_list(message: types.Message):
    await message.reply(
        MSG_WHICH_COMMAND_TO_EXECUTE,
        reply_markup=kb_admin.kb_clients_commands,
    )


#--------------------------------ADD NEW USER-------------------------------------
# TODO закончить command_add_users_info_command
class FSM_Admin_add_user(StatesGroup):
    user_status = State()
    user_name = State()
    user_telegram = State()
    user_phone = State()

async def command_add_users_info_command(message: types.Message):
    if (
        message.text.lower() == "добавить пользователя"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_add_user.user_status.set()
        await message.reply(
            "❔ В каком статусе пользователь?", reply_markup=kb_admin.kb_user_status
        )


async def get_user_status(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.user_status.values()):
        async with state.proxy() as data:
            data['user_status'] = clients_status['admin'] \
                if message.text == kb_admin.user_status['admin'] else clients_status['client']


# -------------------------------VIEW ALL USERS-------------------------------------------
class FSM_Admin_get_info_user(StatesGroup):
    user_name = State()
    

async def get_client_orders(user: ScalarResult["User"]) -> dict:
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders).where(Orders.username == user.name)
        ).all()
    order_numbers, order_statuses, order_types = ("", "", "")
    if orders != []:
        for order in orders:
            order_types += f"{order.order_type}\n"
            order_numbers += f"{order.order_number}\n"
            order_statuses += f"{order.order_state}\n"
    else:
        order_numbers, order_statuses, order_types = ("---", "---", "---")
    
    return {
        "order_numbers":order_numbers, 
        "order_statuses":order_statuses, 
        "order_types":order_types
    }


async def send_to_view_users_orders(user_lst: ScalarResult["User"], message: types.Message):
    if user_lst != []:
        with open("config.json", "r") as config_file:
            data = json.load(config_file)
        headers = [
            "Имя",
            "Телеграм",
            "Телефон",
            "Статус пользователя",
            "Тип заказа",
            "Номер заказа",
            "Статус заказа"
        ]
        if data['mode'] == 'pc':
            table = PrettyTable(
                headers, left_padding_width=1, right_padding_width=1
            )  # Определяем таблицу
            
            for user in user_lst:  # выводим наименования клиентов
                orders = await get_client_orders(user)
                table.add_row(
                    [
                        user.name,
                        user.telegram_name,
                        user.phone,
                        user.status,
                        orders["order_types"],
                        orders["order_numbers"],
                        orders["order_statuses"],
                    ]
                )
            await bot.send_message(
                message.from_id, f"<pre>{table}</pre>", parse_mode=types.ParseMode.HTML
            )
        else:
            msg = "Пользователи:\n"
            for user in user_lst:  # выводим наименования клиентов
                orders = await get_client_orders(user)
                msg += (
                    f"- Имя: {user.name}\n"
                    f"- Телеграм: {user.telegram_name}\n"
                    f"- Телефон: {user.phone}",
                    f"- Статус пользователя: {user.status}\n"
                    f"- Тип заказа: {orders['order_types']}\n"
                    f"- Номер заказа: {orders['order_numbers']}\n"
                    f"- Статус заказа: {orders['order_statuses']}\n\n"
                )
            
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_clients_commands,
        )
    else:
        await message.reply(MSG_NO_USERS_IN_DB)


# /посмотреть_всех_пользователей
async def get_users_info_command(message: types.Message):
    if (
        message.text.lower() == "посмотреть всех пользователей"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            users = session.scalars(select(User)).all()
        await send_to_view_users_orders(users, message)


# -------------------------------------------------------VIEW CLIENT-------------------------------------------
# /посмотреть_пользователя
async def get_user_info_command(message: types.Message):
    if (
        message.text.lower() == "посмотреть пользователя"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            users = session.scalars(select(User)).all()
        if users != []:
            kb_users_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for user in users:
                kb_users_names.add(
                    KeyboardButton(user.name)
                )  # выводим наименования клиентов
            kb_users_names.add(kb_client.cancel_btn)
            
            await FSM_Admin_get_info_user.user_name.set()
            await message.reply(
                "❔ Какого пользователя посмотреть?", reply_markup=kb_users_names
            )
        else:
            await message.reply(MSG_NO_USERS_IN_DB)


async def get_user_info_command_with_name(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        users = session.scalars(select(User)).all()
    user_name_lst = []
    for user in users:
        user_name_lst.append(user.name)

    if message.text in user_name_lst:
        await send_to_view_users_orders(users, message)
        await state.finish()
        
    else:
        await message.reply(
            f"Пользователя с именем {message.text} нет. Попробуй другого."
        )


# ---------------------------------DELETE CLIENT-------------------------------------
class FSM_Admin_delete_info_user(StatesGroup):
    user_name = State()


# /удалить_пользователя
async def delete_username_command(message: types.Message):
    if (
        message.text.lower() == "удалить пользователя"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            users = session.scalars(select(User)).all()
        if users == []:
            await message.reply(
                f"⭕️ Пока нет пользователей в базе.\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_main,
            )
        else:
            kb_users_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for user in users:
                kb_users_names.add(
                    KeyboardButton(user.name)
                )  # выводим наименования пользователей
            await FSM_Admin_delete_info_user.user_name.set()

            await message.reply(
                "❔ Какого пользователя удалить?", reply_markup=kb_users_names
            )


async def delete_user_with_name(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        users = session.scalars(select(User)).all()
    user_name_lst = []
    for user in users:
        user_name_lst.append(user.name)
    if message.text in user_name_lst:
        with Session(engine) as session:
            user = session.scalars(select(User).where(User.name == message.text)).one()
            session.delete(user)
            session.commit()

        await message.reply(
            f"Готово! Пользователь {message.text} удален",
            reply_markup=kb_admin.kb_clients_commands,
        )
        await state.finish()
    else:
        await message.reply(
            f"⭕️ Пользователя с именем {message.text} нет. Попробуй другого."
        )


# ---------------------------------SET CLIENT TO BLACK LIST-------------------------------------
class FSM_Admin_set_client_to_black_list(StatesGroup):
    user_name = State()


async def command_set_client_to_black_list(message: types.Message):
    if (
        message.text.lower() == "добавить пользователя в черный список"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            users = session.scalars(select(User)).all()
        if users == []:
            await message.reply(MSG_NO_USERS_IN_DB)
            
        else:
            kb_users_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for user in users:
                kb_users_names.add(
                    KeyboardButton(user.name)
                )  # выводим наименования пользователей
            kb_users_names.add(kb_client.cancel_btn)
            await FSM_Admin_set_client_to_black_list.user_name.set()

            await message.reply(
                "❔ Какого пользователя добавить в черный список?", reply_markup=kb_users_names
            )


async def set_to_black_list_user_with_name(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        users = session.scalars(select(User)).all()
    user_name_lst = []
    for user in users:
        user_name_lst.append(user.name)
    if message.text in user_name_lst:
        async with state.proxy() as data:
            data['username'] = message.text

        await message.reply(
            "❔ Точно хотите забанить пользователя?",
            reply_markup= kb_client.kb_yes_no
        )
        await state.finish()
    
    elif message.text == kb_client.yes_str:
        async with state.proxy() as data:
            username = data['username']
        
        with Session(engine) as session:
            user = session.scalars(select(User).where(User.name == username)).one()
            user.status = clients_status["banned"]
            await message.reply(
                f"🎉 Готово! Пользователь {message.text} забанен.",
                reply_markup=kb_admin.kb_clients_commands,
            )
            await state.finish()
            
    elif message.text == kb_client.no_str:
        await message.reply(
                f"{MSG_CANCEL_ACTION}{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_clients_commands,
            )
        await state.finish()
    else:
        await message.reply(
            f"⭕️ Пользователя с именем {message.text} нет. Попробуй другого."
        )


def register_handlers_admin_client_commands(dp: Dispatcher):
    # ----------------------------------------CLIENTS------------------------------------------------------
    dp.register_message_handler(get_clients_command_list, commands=["пользователи"])
    dp.register_message_handler(
        get_clients_command_list,
        Text(equals="пользователи", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        delete_username_command, commands=["удалить_пользователя"]
    )
    dp.register_message_handler(
        delete_username_command,
        Text(equals="удалить пользователя", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        delete_user_with_name, state=FSM_Admin_delete_info_user.user_name
    )

    dp.register_message_handler(
        get_users_info_command, commands=["посмотреть_всех_пользователей"]
    )
    dp.register_message_handler(
        get_users_info_command,
        Text(equals="посмотреть всех пользователей", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        get_user_info_command, commands=["посмотреть_пользователя"]
    )
    dp.register_message_handler(
        get_user_info_command, Text(equals="посмотреть пользователя", ignore_case=True)
    )
    dp.register_message_handler(
        get_user_info_command_with_name, state=FSM_Admin_get_info_user.user_name
    )


    dp.register_message_handler(command_set_client_to_black_list,
        Text(equals="отправить пользователя в черный список", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        command_set_client_to_black_list, commands=["отправить_пользователя_в_черный_список"]
    )
    dp.register_message_handler(
        set_to_black_list_user_with_name, state=FSM_Admin_set_client_to_black_list.user_name
    )