from create_bot import dp, bot
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text

from msg.main_msg import *
from msg.msg_client_schedule import *
from keyboards import kb_client, kb_admin
from handlers.other import *

from validate import check_pdf_document_payment, check_photo_payment
from handlers.calendar_client import obj

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *
from datetime import datetime


# Перенести сеанс
# Посмотреть мои сеансы 📃

class FSM_Client_client_create_new_schedule_event(StatesGroup):
    get_order_number = State()
    get_new_schedule_event = State()


# команда для вывода меню календаря клиента
async def command_client_schedule_event(message: types.Message):  # state: FSMContext)
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]]))
            .where(Orders.user_id == message.from_id)
            # .where(Orders.order_state.in_([STATES['paid'], STATES['in_work']] + list(STATES['closed'].values())))
        ).all()
    if orders == []:
        await bot.send_message(message.from_id, MSG_CLIENT_HAVE_NO_ORDER)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_CREATE_ORDER)
    else:
        await bot.send_message(
            message.from_id,
            MSG_WHAT_CLIENT_WANT_TO_SEE_IN_SCHEDULE,
            reply_markup=kb_client.kb_client_schedule_menu,
        )


# Добавить новый сеанс
async def command_client_create_new_schedule_event(message: types.Message):
    with Session(engine) as session:
        order = session.scalars(
            select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.in_([STATES["in_work"]]))
        ).all()
        
        opened_orders = session.scalars(
            select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.not_in([STATES["in_work"]]))
        ).all()
        
    if opened_orders != [] and order == []:
        await bot.send_message(
            message.from_id,
            (
                f"Уважаемый Клиент! У Вас еще нет заказов, в статусе \"{STATES['in_work']}\"\n"
                "Добавить новый сеанс можно только к заказам в этом статусе.\n"
                "По всем вопросам обращайтесь к https://t.me/dara_redwan"
            )
        )
        
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup= kb_client.kb_client_schedule_menu
        )
    else:
        schedule_event = session.scalars(
            select(ScheduleCalendar)
            # .where(ScheduleCalendar.status == 'Закрыт')
            .where(ScheduleCalendar.id == order[0].schedule_id)
        ).all()
        
        closed_schedule_event = session.scalars(
            select(ScheduleCalendar)
            .where(ScheduleCalendar.status == "Закрыт")
            .where(ScheduleCalendar.id == order[0].schedule_id)
        ).all()
        if schedule_event != [] and len(closed_schedule_event) == len(schedule_event):
            # Если заказ оплачен и имеет статус "в работе", а сеанс уже прошел
            kb = ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add(KeyboardButton(f"№{order[0].order_number} {order[0].order_state}"))
            kb.add(kb_client.back_btn).add(kb_client.cancel_btn)
            await FSM_Client_client_create_new_schedule_event.get_order_number.set()

            await bot.send_message(
                message.from_id,
                "❕ Пожалуйста, выберите заказ для нового сеанса. "
                "Список заказов находится у вас в списке кнопок.",
                reply_markup=kb,
            )

        elif len(closed_schedule_event) < len(schedule_event):
            await bot.send_message(
                message.from_id,
                "❌ У вас уже есть открытый сеанс.\n"
                '❕ Посмотреть данные о сеансе можно по кнопке "Посмотреть мои сеансы"',
            )


async def get_order_number_to_create_new_schedule_event_in_order(
    message: types.Message, state: FSMContext
):
    with Session(engine) as session:
        order = session.scalars(
            select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.in_([STATES["in_work"]]))
        ).one()
    kb_msg = f"№{order.order_number} {order.order_state}"
    msg = ""
    if message.text in kb_msg:
        async with state.proxy() as data:
            data["kb_order_lst"] = message.text

        with Session(engine) as session:
            open_schedule_events = session.scalars(
                select(ScheduleCalendar)
                .order_by(ScheduleCalendar.start_datetime)
                .where(ScheduleCalendar.start_datetime > datetime.now())
                .where(ScheduleCalendar.end_datetime > datetime.now())
                .where(ScheduleCalendar.status == "Свободен")
            ).all()
            await FSM_Client_client_create_new_schedule_event.next()  # -> get_schedule_number_to_create_new_event_in_order
        open_schedule_events_lst = []
        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for event in open_schedule_events:
            item = f"c {event.start_datetime.strftime('%H:%M')} до {event.end_datetime.strftime('%H:%M %d/%m/%Y')}"
            open_schedule_events_lst.append(item)
            msg += f"{item}\n"
            kb.add(KeyboardButton(msg))

            async with state.proxy() as data:
                data["open_schedule_events_lst"] = open_schedule_events_lst

            await bot.send_message(
                message.from_id,
                "❕ Пожалуйста, выберите свободную дату для нового сеанса. "
                "Список свободных дат появился выше.",
                reply_markup=kb,
            )

    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_schedule_menu,
        )

    else:
        await bot.send_message(
            message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


async def get_schedule_number_to_create_new_event_in_order(
    message: types.Message, state: FSMContext
):
    async with state.proxy() as data:
        open_schedule_events_lst = data["open_schedule_events_lst"]

    if message.text in open_schedule_events_lst:
        with Session(engine) as session:
            start_time = datetime.strptime(
                f"{message.text[0]} {message.text[3]}", "%H:%M %d/%m/%Y"
            )
            end_time = datetime.strptime(
                f"{message.text[2]} {message.text[3]}", "%H:%M %d/%m/%Y"
            )
            open_schedule_events = session.scalars(
                select(ScheduleCalendar)
                .where(ScheduleCalendar.start_datetime == start_time)
                .where(ScheduleCalendar.end_datetime == end_time)
            ).one()
            open_schedule_events.status = "Занят"
            session.commit()
        await bot.send_message(
            message.from_id,
            "☘️ Отлично, в заказе появился новый сеанс!\n"
            f"❕ Жду вас в {message.text}!",
        )

        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_client.kb_client_schedule_menu,
        )
        await state.finish()
    elif message.text in LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_schedule_menu,
        )

    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Client_client_create_new_schedule_event.previous()  # -> get_order_number_to_create_new_schedule_event_in_order
        async with state.proxy() as data:
            kb_order_lst = data["kb_order_lst"]
        await bot.send_message(
            message.from_id,
            "❕ Пожалуйста, выберите заказ для нового сеанса",
            reply_markup=kb_order_lst,
        )

    else:
        await bot.send_message(
            message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


# -------------------------------------------CHANGE_SCHEDULE_EVENT_CLIENT-------------------------------
class FSM_Client_client_change_schedule_event(StatesGroup):
    client_get_answer_yes_no = State()
    get_order_number = State()
    get_new_free_schedule_event_to_order = State()
    # get_new_event_schedule_date = State()


async def command_client_change_schedule_event(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]]))
            .where(Orders.user_id == message.from_id)
            .where(
                Orders.order_state.in_(
                    [STATES["processed"], STATES["paid"], STATES["in_work"]]
                )
            )
            # .where(Orders.order_state.in_([STATES['in_work'],
            # STATES['open'], STATES['complete'], STATES['paid']]))
        ).all()
        
        opened_orders = session.scalars(
            select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.in_([STATES["open"]] + list(STATES['closed'].values())))
            # .where(Orders.order_state.in_([STATES['in_work'],
            # STATES['open'], STATES['complete'], STATES['paid']]))
        ).all()
    if orders == [] and opened_orders == []:
        await bot.send_message(message.from_id, MSG_CLIENT_HAVE_NO_ORDER)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_CREATE_ORDER)
        
    elif orders == [] and opened_orders != []:
        await bot.send_message(
            message.from_id, 
            (
                f"⛔️ Уважаемый Клиент! У вас нет заказов в статусах"
                f" \"{STATES['processed']}\", \"{STATES['paid']}\" и \"{STATES['in_work']}\".\n\n"
                f"❕ Ожидайте, пока администратор изменит ваш заказ на один из этих статусов."
            )
        )
        await bot.send_message(
            message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE
        )
        
    else:
        await bot.send_message(
            message.from_id, MSG_QUESTION_CLIENT_ABOUT_CHANGING_SCHEDULE_EVENT
        )
        # -> get_client_answer_to_change_schedule
        await FSM_Client_client_change_schedule_event.client_get_answer_yes_no.set()
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_CONTINUE_CHANGING_SCHEDULE_EVENT,
            reply_markup=kb_client.kb_yes_no,
        )


async def get_client_answer_to_change_schedule(
    message: types.Message, state: FSMContext
):
    if message.text == kb_client.yes_str:
        with Session(engine) as session:
            orders = session.scalars(
                select(Orders)
                .join(ScheduleCalendarItems.schedule_mapped_id)
                .where(
                    Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]])
                )
                .where(Orders.user_id == message.from_id)
                .where(
                    Orders.order_state.in_(
                        [STATES["processed"], STATES["paid"], STATES["in_work"]]
                    )
                )
            ).all()

        msg = "Cеансы:\n"
        event_time_lst = []
        orders_view_lst = []
        order_number_with_date_dict = {}
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        i = 0
        for order in orders:
            with Session(engine) as session:
                event = session.scalars(
                    select(ScheduleCalendar).where(
                        ScheduleCalendar.id == order.schedule_id
                    )
                ).one()

            event_time = (
                f"Cеанс {event.start_datetime.strftime('%H:%M')} - "
                f"{event.end_datetime.strftime('%H:%M %d/%m/%Y')} 🕒"
            )

            event_time_lst.append(event_time)
            kb.add(KeyboardButton(f"{event_time}"))

            msg += f"🕸 Заказ №{order.order_number}\n🕒 {event_time[:-2]}\n\n"
            orders_view_lst.append(msg)

            order_number_with_date_dict[i] = {
                "event_id": event.id,
                "order_number": order.order_number,
            }
            i += 1

        async with state.proxy() as data:
            data["orders_view_msg_str"] = msg
            data["event_time_lst"] = event_time_lst
            data["order_number_with_date_dict"] = order_number_with_date_dict
            data["kb_get_client_answer_to_change_schedule"] = kb

        kb.add(kb_client.back_btn).add(kb_client.cancel_btn)
        await FSM_Client_client_change_schedule_event.next()  # -> get_event_schedule_date
        await bot.send_message(message.from_id, f"{msg}")
        await bot.send_message(
            message.from_id, "❔ Какой сеанс хотите перенести?", reply_markup=kb
        )

    elif message.text in LIST_BACK_TO_HOME + [kb_client.no_str] + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_main,
        )

    elif message.text in LIST_BACK_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_WHAT_CLIENT_WANT_TO_SEE_IN_SCHEDULE,
            reply_markup=kb_client.kb_client_schedule_menu,
        )

    else:
        await bot.send_message(
            message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


async def get_event_schedule_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        event_time_lst = data["event_time_lst"]

    if message.text in event_time_lst:
        with Session(engine) as session:
            opened_schedule_events = session.scalars(
                select(ScheduleCalendar)
                .where(ScheduleCalendar.start_datetime > datetime.now())
                .where(ScheduleCalendar.end_datetime > datetime.now())
                .where(ScheduleCalendar.status == "Свободен")
                .order_by(ScheduleCalendar.start_datetime)
            ).all()

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        free_event_time_lst = []
        i = 0
        free_event_id_dict = {}

        for event in opened_schedule_events:
            free_event_time = (
                f"Cеанс {event.start_datetime.strftime('%H:%M')} - "
                f"{event.end_datetime.strftime('%H:%M %d/%m/%Y')} 🕒"
            )
            free_event_time_lst.append(free_event_time)
            free_event_id_dict[i] = event.id
            kb.add(free_event_time)

        await FSM_Client_client_change_schedule_event.next()  # -> get_event_schedule_date
        async with state.proxy() as data:
            data["free_event_time_lst"] = free_event_time_lst
            data["free_event_id_dict"] = free_event_id_dict
            data["old_id_event"] = event_time_lst.index(message.text)

        kb.add(kb_client.back_btn).add(kb_client.cancel_btn)
        await bot.send_message(
            message.from_id, MSG_CLIENT_CHOOSE_CHANGING_EVENT, reply_markup=kb
        )

    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_main,
        )

    elif message.text in LIST_BACK_COMMANDS:
        # TODO доделать возврат
        await FSM_Client_client_change_schedule_event.previous()

    else:
        await bot.send_message(
            message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


async def get_new_event_schedule_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        free_event_time_lst = data["free_event_time_lst"]
        event_time_lst = data["event_time_lst"]
        order_number_with_date_dict = data["order_number_with_date_dict"]
        free_event_id_dict = data["free_event_id_dict"]
        old_id_event = data["old_id_event"]

    if message.text in free_event_time_lst:
        with Session(engine) as session:
            order = session.scalars(
                select(Orders).where(
                    Orders.order_number
                    == order_number_with_date_dict[event_time_lst.index(message.text)][
                        "order_number"
                    ]
                )
            ).one()

            schedule_event = session.get(ScheduleCalendar, old_id_event)
            schedule_event_old_status = schedule_event.status
            schedule_event.status = STATES["closed"]["rejected"]

            new_schedule = session.get(
                ScheduleCalendar,
                free_event_id_dict[free_event_time_lst.index(message.text)],
            )
            # TODO проверить правильность добавление нового сеанса в заказ
            order.schedule_id.append(new_schedule)
            new_time = (
                f"{new_schedule.start_datetime.strftime('%H:%M')} - "
                f"{new_schedule.end_datetime.strftime('%H:%M %d/%m/%Y')} "
            )
            session.commit()

        await bot.send_message(
            message.from_id,
            f"🕒 Ваш новый сеанс по заказу №{order.order_number} будет в {new_time}!\n"
            # f"❕ Вы поменяли статус c {schedule_event_old_status} на {STATES['closed']['rejected']}!\n"\
            "❕ Ожидайте сообщение бота о подтверждении администратором данного статуса.",
        )

        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_client.kb_client_schedule_menu,
        )

        await state.finish()
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"{MSG_CANCEL_ACTION}{MSG_BACK_TO_HOME}",
            reply_markup=kb_client.kb_client_main,
        )

    elif message.text in LIST_BACK_COMMANDS:
        # TODO доделать возврат
        await FSM_Client_client_change_schedule_event.previous()  # -> get_event_schedule_date
        async with state.proxy() as data:
            kb_get_client_answer_to_change_schedule = data[
                "kb_get_client_answer_to_change_schedule"
            ]

        await bot.send_message(
            message.from_id,
            "❔ Какой сеанс хотите перенести?",
            reply_markup=kb_get_client_answer_to_change_schedule,
        )

    else:
        await bot.send_message(
            message.from_id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


""" class FSM_Client_client_view_schedule_event(StatesGroup):
    get_order_number = State() """


# выдать пользователю его сеансы
async def command_get_view_schedule_event_to_client(message: types.Message):
    with Session(engine) as session:
        orders = session.scalars(
            select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types["constant_tattoo"]]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.not_in([STATES["open"]]))
            # .where(Orders.order_state.in_([STATES['in_work'],
            # STATES['open'], STATES['complete'], STATES['paid']]))
        ).all()
        """ opened_orders = session.scalars(select(Orders)
            .join(ScheduleCalendarItems.schedule_mapped_id)
            .where(Orders.order_type.in_([kb_admin.price_lst_types['constant_tattoo']]))
            .where(Orders.user_id == message.from_id)
            .where(Orders.order_state.in_([STATES['open']]))
            # .where(Orders.order_state.in_([STATES['in_work'],
            # STATES['open'], STATES['complete'], STATES['paid']]))
            ).all() """
        #
    if orders == []:  #  and closed_orders:
        await bot.send_message(message.from_id, MSG_CLIENT_HAVE_NO_ORDER)
        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_CREATE_ORDER)
    else:
        for order in orders:
            with Session(engine) as session:
                schedule_event = session.scalars(
                    select(ScheduleCalendar).where(
                        ScheduleCalendar.id == order.schedule_id
                    )
                ).one()
                msg = (
                    f"🕸 Закак №{order.order_number}\n"
                    f"🕒 Дата и время сеанса: {schedule_event.start_datetime.strftime('%H:%M')} "
                    f"по {schedule_event.end_datetime.strftime('%H:%M %d/%m/%Y')}"
                    f"📃 Статус сеанса: {schedule_event.status}"
                )
                await bot.send_message(message.from_id, msg)

        await bot.send_message(message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE)


def register_handlers_client_schedule(dp: Dispatcher):
    dp.register_message_handler(
        command_client_schedule_event,
        Text(equals=kb_client.client_main["client_schedule"], ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_client_create_new_schedule_event,
        Text(equals=kb_client.client_schedule_menu["add_new_event"], ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_order_number_to_create_new_schedule_event_in_order,
        state=FSM_Client_client_create_new_schedule_event.get_order_number,
    )
    dp.register_message_handler(
        get_schedule_number_to_create_new_event_in_order,
        state=FSM_Client_client_create_new_schedule_event.get_new_schedule_event,
    )

    dp.register_message_handler(
        command_client_change_schedule_event,
        Text(equals=kb_client.client_schedule_menu["change_event"], ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_client_answer_to_change_schedule,
        state=FSM_Client_client_change_schedule_event.client_get_answer_yes_no,
    )
    dp.register_message_handler(
        get_event_schedule_date,
        state=FSM_Client_client_change_schedule_event.get_order_number,
    )
    dp.register_message_handler(
        get_new_event_schedule_date,
        state=FSM_Client_client_change_schedule_event.get_new_free_schedule_event_to_order,
    )

    dp.register_message_handler(
        command_get_view_schedule_event_to_client,
        Text(
            equals=kb_client.client_schedule_menu["view_client_events"],
            ignore_case=True,
        ),
        state=None,
    )
