from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES
from handlers.other import *

# from diffusers import StableDiffusionPipeline
# import torch

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, date, time, timedelta
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

from prettytable import PrettyTable
from msg.main_msg import *


async def get_giftbox_order_command_list(message: types.Message):
    if (
        message.text.lower() == "гифтбокс заказ"
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            "Какую команду гифтбокс заказа хочешь выполнить?",
            reply_markup=kb_admin.kb_giftbox_order_commands,
        )


# -------------------------------------------------GIFTBOX ORDER COMMANDS-------------------------------------
async def send_to_view_giftbox_order(
    message: types.Message, orders: ScalarResult["Orders"]
):
    if orders == []:
        await message.reply(
            f"{MSG_NO_ORDER_IN_TABLE}\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
            reply_markup=kb_admin.kb_giftbox_order_commands,
        )
    else:
        for order in orders:
            with Session(engine) as session:
                user = session.scalars(
                    select(User).where(User.telegram_id == order.user_id)
                ).all()

            if user != []:
                with Session(engine) as session:
                    phone = (
                        session.scalars(
                            select(User).where(User.telegram_id == order.user_id)
                        )
                        .one()
                        .phone
                    )
            else:
                phone = "Нет номера"

            await bot.send_message(
                message.from_user.id,
                f'Гифтбокс заказ № {order.order_number} от {order.creation_date.strftime("%H:M %d/%m/%Y")}\n'
                f"- Имя пользователя: {order.username}\n"
                f"- телефон: {phone}\n"
                f"- описание заказа: {order.order_note}\n"
                f"- состояние заказа: {order.order_state}\n",
            )


class FSM_Admin_send_to_view_giftbox_orders(StatesGroup):
    giftbox_order_state = State()


# /посмотреть_гифтбокс_заказы
async def command_get_info_giftbox_orders(message: types.Message):
    if (
        message.text.lower()
        in ["/посмотреть_гифтбокс_заказы", "посмотреть гифтбокс заказы"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_send_to_view_giftbox_orders.giftbox_order_state.set()
        await bot.send_message(
            message.from_user.id,
            "В каком статусе хочешь посмотреть заказы?",
            reply_markup=kb_admin.kb_order_statuses,
        )


async def get_status_to_view_giftbox_orders(message: types.Message, state: FSMContext):
    if message.text in kb_admin.statuses_order_lst:
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders)
                .where(Orders.order_type == "гифтбокс")
                .where(Orders.order_state == message.text)
            ).all()
        await send_to_view_giftbox_order(message, orders)
        await bot.send_message(
            message.from_user.id, f"Всего гифтбокс заказов: {len(orders)}"
        )
        await state.finish()

    elif message.text in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS + LIST_BACK_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.giftbox_order_commands,
        )

    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_TO_SEND)


class FSM_Admin_send_to_view_giftbox_order(StatesGroup):
    giftbox_order_number = State()


async def get_status_to_view_giftbox_order(message: types.Message):
    if (
        message.text.lower()
        in ["/посмотреть_гифтбокс_заказ", "посмотреть гифтбокс заказ"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders)
                .where(Orders.order_type == "гифтбокс")
                .where(Orders.order_state == message.text)
            ).all()

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for order in orders:
            kb.add(
                f"{order.order_number} клиент:{order.username} статус:{order.order_state}"
            )
        kb.add(LIST_BACK_TO_HOME[0])

        await FSM_Admin_send_to_view_giftbox_order.giftbox_order_number.set()
        await bot.send_message(
            message.from_user.id,
            "Какой номер заказа хочешь посмотреть?",
            reply_markup=kb,
        )


async def get_giftbox_order_number_to_view(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.order_type == "гифтбокс")
            .where(Orders.order_state == message.text)
        ).all()

    kb_order_number_lst = []
    for order in orders:
        kb_order_number_lst.append(
            f"{order.order_number} клиент:{order.username} статус:{order.order_state}"
        )

    if message.text in kb_order_number_lst:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders)
                .where(Orders.order_type == "гифтбокс")
                .where(Orders.order_number == message.text.split()[0])
            ).all()
        await send_to_view_giftbox_order(message, order)

    elif message.text in LIST_BACK_COMMANDS + LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.giftbox_order_commands,
        )
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_TO_SEND)


class FSM_Admin_change_state_giftbox_orders(StatesGroup):
    giftbox_order_number = State()
    giftbox_order_state = State()


# /поменять_статус_гифтбокс_заказа
async def command_change_state_giftbox_order(message: types.Message):
    if (
        message.text.lower()
        in ["/поменять_статус_гифтбокс_заказа", "поменять статус гифтбокс заказа"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            giftbox_orders = session.scalars(
                select(Orders).where(Orders.order_type == "гифтбокс")
            ).all()

        if giftbox_orders is None or giftbox_orders == []:
            await message.reply(
                f"{MSG_NO_ORDER_IN_TABLE}\n\n{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
                reply_markup=kb_admin.kb_giftbox_order_commands,
            )
        else:
            kb_giftbox_numbers = ReplyKeyboardMarkup(resize_keyboard=True)
            await FSM_Admin_change_state_giftbox_orders.giftbox_order_number.set()
            await send_to_view_giftbox_order(message, giftbox_orders)
            for order in giftbox_orders:
                kb_giftbox_numbers.add(
                    KeyboardButton(f"{order.order_number} {order.order_state}")
                )

            kb_giftbox_numbers.add(KeyboardButton(LIST_BACK_TO_HOME[0]))
            await bot.send_message(
                message.from_user.id,
                f"У какого заказа хочешь поменять статус?",
                reply_markup=kb_giftbox_numbers,
            )


# Определяем номер гифтбокс заказа для изменения статуса
async def get_new_state_giftbox_order(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        giftbox_orders = session.scalars(
            select(Orders).where(Orders.order_type == "гифтбокс")
        ).all()
    kb_lst = []
    for order in giftbox_orders:
        kb_lst.append(f"{order.order_number} {order.order_state}")

    if message.text in kb_lst:
        async with state.proxy() as data:
            data["giftbox_order_number"] = message.text

        await FSM_Admin_change_state_giftbox_orders.next()
        await bot.send_message(message.from_id, MSG_SEND_ORDER_STATE_INFO)
        await message.reply(
            "На какой статус хочешь поменять?",
            reply_markup=kb_admin.kb_change_status_order,
        )
    else:
        await state.finish()
        await message.reply(
            "Хорошо, ты вернулся назад. Что хочешь сделать?",
            reply_markup=kb_admin.kb_giftbox_order_commands,
        )


# Определяем новый статус гифтбокс заказа
async def set_new_state_giftbox_order(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        giftbox_number = data["giftbox_order_number"]
    with Session(engine) as session:
        order = session.scalars(
            select(Orders).where(Orders.order_number == giftbox_number)
        ).one()
        order.order_state == message.text
        session.commit()

    await message.reply(
        f"Готово! Вы обновили статус заказа {giftbox_number} на {message.text}",
        reply_markup=kb_admin.kb_giftbox_order_commands,
    )
    await state.finish()  #  полностью очищает данные


def register_handlers_admin_giftbox_order(dp: Dispatcher):
    # ----------------------------------COMMANDS GIFTBOX ORDER--------------------------------------------
    dp.register_message_handler(
        get_giftbox_order_command_list, commands="гифтбокс_заказ", state=None
    )
    dp.register_message_handler(
        get_giftbox_order_command_list,
        Text(equals="гифтбокс заказ", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_giftbox_orders,
        commands="посмотреть_гифтбокс_заказы",
        state=None,
    )
    dp.register_message_handler(
        command_get_info_giftbox_orders,
        Text(equals="посмотреть гифтбокс заказы", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_status_to_view_giftbox_orders,
        state=FSM_Admin_send_to_view_giftbox_orders.giftbox_order_state,
    )

    dp.register_message_handler(
        get_status_to_view_giftbox_order,
        Text(equals="посмотреть гифтбокс заказ", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_giftbox_order_number_to_view,
        state=FSM_Admin_send_to_view_giftbox_order.giftbox_order_number,
    )

    dp.register_message_handler(
        command_change_state_giftbox_order,
        Text(equals="поменять статус гифтбокс заказа", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        command_change_state_giftbox_order,
        commands="/поменять_статус_гифтбокс_заказа",
        state=None,
    )
    dp.register_message_handler(
        get_new_state_giftbox_order,
        state=FSM_Admin_change_state_giftbox_orders.giftbox_order_number,
    )
    dp.register_message_handler(
        set_new_state_giftbox_order,
        state=FSM_Admin_change_state_giftbox_orders.giftbox_order_state,
    )
