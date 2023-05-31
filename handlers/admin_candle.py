from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES

from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from db.db_setter import set_to_table
from db.db_getter import get_info_many_from_table

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from db.db_delete_info import delete_info
from handlers.calendar_client import obj
from msg.main_msg import *

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

# --------------------------------------CANDLE COMMAND LIST-----------------------------------
# /добавить_свечу, Отправляем название свечи
async def get_candle_command_list(message: types.Message):
    if (
        message.text.lower() in ["свеча", "/свеча"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            "Какую команду со свечами хочешь выполнить?",
            reply_markup=kb_admin.kb_candle_item_commands,
        )


# -----------------------------------------CANDLE ITEM-----------------------------------COMPLETE
class FSM_Admin_candle_item(StatesGroup):
    candle_name = State()
    candle_photo = State()
    candle_price = State()
    candle_note = State()
    candle_state = State()
    candle_numbers = State()


# /добавить_свечу, Отправляем название свечи
async def command_load_candle_item(message: types.Message):
    if (
        message.text.lower() in ["добавить свечу", "/добавить_свечу"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_candle_item.candle_name.set()
        await message.reply(
            "Определи название свечи", reply_markup= kb_client.kb_back_cancel
        )


# Отправляем название свечи
async def load_candle_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["candle_name"] = message.text
    await FSM_Admin_candle_item.next()
    await message.reply("А теперь загрузи одну фотографию свечи")


# Отправляем фото свечи
async def load_candle_photo(message: types.Message, state: FSMContext):
    if message.content_type == 'photo':
        async with state.proxy() as data:
            data["candle_photo"] = message.photo[0].file_id
            data['menu_another_price'] = False
        await FSM_Admin_candle_item.next()
        await message.reply("Определи цену свечи", reply_markup= kb_admin.kb_price)
        
    elif message.content_type == 'text':
        if message.text in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS + LIST_BACK_COMMANDS:
            await state.finish()
            await bot.send_message(
                message.from_id,
                MSG_BACK_TO_HOME,
                reply_markup=kb_admin.kb_candle_item_commands,
            )
        else:
            await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_TO_SEND)


# Отправляем стоимость свечи
async def load_candle_price(message: types.Message, state: FSMContext):
    if message.text in kb_admin.price_lst + kb_admin.another_price_full_lst:
        async with state.proxy() as data:
            data["candle_price"] = int(message.text)
        await FSM_Admin_candle_item.next()
        await message.reply(
            "Введи описание свечи", reply_markup= kb_client.kb_back_cancel
        )
        
    elif message.text == kb_admin.another_price_lst[0]:
        async with state.proxy() as data:
            data['menu_another_price'] = True
        await message.reply(
            MSG_ADMIN_SET_ANOTHER_PRICE, reply_markup=kb_admin.kb_another_price_full
        )
    elif message.text in LIST_BACK_COMMANDS:
        async with state.proxy() as data:
            menu_another_price = data['menu_another_price']
            data['menu_another_price'] = False
            
        if menu_another_price:
            await message.reply("Определи цену свечи", reply_markup= kb_admin.kb_price)
        else:
            await FSM_Admin_candle_item.previous() #-> load_candle_photo
            await message.reply(
                "А теперь загрузи одну фотографию свечи", reply_markup= kb_client.kb_back_cancel
            )
        
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
            await state.finish()
            await bot.send_message(
                message.from_id,
                MSG_BACK_TO_HOME,
                reply_markup= kb_admin.kb_candle_item_commands,
            )
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_TO_SEND)


# Отправляем описание свечи
async def load_candle_note(message: types.Message, state: FSMContext):
    if message.text in LIST_BACK_COMMANDS + LIST_CANCEL_COMMANDS:
            await state.finish()
            await bot.send_message(
                message.from_id,
                MSG_BACK_TO_HOME,
                reply_markup= kb_admin.kb_candle_item_commands,
            )
    else:
        async with state.proxy() as data:
            data["candle_note"] = message.text
        await FSM_Admin_candle_item.next() #->load_candle_state
        await message.reply("Свеча есть в наличии?", reply_markup=kb_client.kb_yes_no)


# Отправляем статус товара свечей и заводим новую строку в таблице candle_items, если количество свечей = 0
async def load_candle_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["candle_state"] = message.text

    if message.text == kb_client.yes_str:
        await message.reply(
            "Сколько таких свечей у тебя есть? Напиши количество",
            reply_markup=kb_admin.kb_sizes,
        )
    elif message.text in [kb_client.no_str] + kb_admin.sizes_lst:
        async with state.proxy() as data:
            data["candle_quantity"] = 0 if message.text == kb_client.no_str else int(message.text)
            name = data['candle_name']
            price= data['candle_price']
            with Session(engine) as session:
                new_candle_item = CandleItems(
                    name= data['candle_name'],
                    photo= data["candle_photo"],
                    price= data['candle_price'],
                    note= data["candle_note"],
                    quantity= data['candle_quantity']
                )
                session.add(new_candle_item)
                session.commit()
        await message.reply(
            f"Готово! Вы добавили свечу {name} по цене {price} в таблицу", 
            reply_markup=kb_admin.kb_candle_item_commands
        )
        await state.finish()  #  полностью очищает данные
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
            await state.finish()
            await bot.send_message(
                message.from_id,
                MSG_BACK_TO_HOME,
                reply_markup= kb_admin.kb_candle_item_commands,
            )
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_TO_SEND)


# ---------------------------------CANDLE /посмотреть_список_свечей--------------------------COMPLETE
# /посмотреть_список_свечей, посмотреть список свечей
async def command_get_info_candles(message: types.Message):
    if (
        message.text.lower()
        in ["посмотреть список свечей", "/посмотреть_список_свечей"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            candles = session.scalars(select(CandleItems)).all()
        if candles == []:
            await bot.send_message(message.from_user.id, "В базе пока нет свечей")
        else:
            for item in candles:
                await bot.send_photo(
                    message.from_user.id,
                    item.photo,
                    f" Свеча {item.name}\n- Цена: {item.price}"
                    f"\n- Описание: {item.note}\n- Количество: {item.quantity}",
                )


class FSM_Admin_get_info_candle_item(StatesGroup):
    candle_name = State()


class FSM_Admin_delete_info_candle_item(StatesGroup):
    candle_name = State()


# -------------------------------------------CANDLE /посмотреть_свечу-----------------------COMPLETE
# /посмотреть_свечу
async def command_get_info_candle(message: types.Message):
    if (
        message.text.lower() in ["посмотреть свечу", "/посмотреть_свечу"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            candles = session.scalars(select(CandleItems)).all()
        kb_candles_names = ReplyKeyboardMarkup(resize_keyboard=True)
        for item in candles:
            kb_candles_names.add(item.name)
        await FSM_Admin_get_info_candle_item.candle_name.set()
        await message.reply(
            "Какое свечу хочешь посмотреть?", reply_markup= kb_candles_names
        )


async def get_candle_name_for_info(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        candles = session.scalars(select(CandleItems)).all()
    kb_candles_names_lst= []
    for candle in candles:
        kb_candles_names_lst.append(candle.name)
        
    if message.text in kb_candles_names_lst:
        with Session(engine) as session:
            item = session.scalars(select(CandleItems)
                .where(CandleItems.name == message.text)).one()
        msg = (
            f"- Название: {item.name}\n"
            f"- Цена: {item.price}\n"
            f"- Количество: {item.quantity}\n"
            f"- Описание: {item.note}\n"
        )

        await bot.send_photo(message.from_user.id, item.photo, msg)

        await message.reply(
            "Чего еще хочешь посмотреть?", reply_markup=kb_admin.kb_candle_item_commands
        )
        await state.finish()  #  полностью очищает данные
    else:
        await message.reply("Неверное указание имени свечи, попробуй другую")


# -----------------------CANDLE /посмотреть_список_имеющихся_свечей--------------------------COMPLETE
# /посмотреть_список_имеющихся_свечей
async def command_get_info_candles_having(message: types.Message):
    if (
        message.text.lower()
        in ["посмотреть список имеющихся свечей", "/посмотреть_список_имеющихся_свечей"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        """ candles = await get_info_many_from_table(
            "candle_items", column_name="state", condition="Есть в наличии"
        ) """
        with Session(engine) as session:
            candles = session.scalars(select(CandleItems)
                .where(CandleItems.quantity != 0)).all()

        if candles == []:
            await bot.send_message(
                message.from_user.id, "У тебя пока нет купленных свечей"
            )
        else:
            for item in candles:
                await bot.send_photo(
                    message.from_user.id,
                    item.photo,
                    f" Свеча {item.name}\n- Цена: {item.price}"
                    f"\n- Описание: {item.note}\n- Количество: {item.quantity}",
                    reply_markup=kb_admin.kb_candle_item_commands,
                )
        await message.reply(
            "Чего еще хочешь посмотреть, моя госпожа?",
            reply_markup=kb_admin.kb_candle_item_commands,
        )


# --------------------------CANDLE /посмотреть_список_не_имеющихся_свечей-------------------COMPLETE
# /посмотреть_список_не_имеющихся_свечей
async def command_get_info_candles_not_having(message: types.Message):
    if (
        message.text.lower()
        in [
            "посмотреть список не имеющихся свечей",
            "/посмотреть_список_не_имеющихся_свечей",
        ]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        
        with Session(engine) as session:
            candles = session.scalars(select(CandleItems)
                .where(CandleItems.quantity == 0)).all()
        if candles == []:
            await bot.send_message(
                message.from_user.id,
                "У тебя все свечи есть! Глянь в таблице купленных свечей",
            )
        else:
            for item in candles:
                await bot.send_photo(
                    message.from_user.id,
                    item.photo,
                    f"  Свеча  {item.name}\n- Цена: {item.price}"
                    f"\n- Описание: {item.note}\n- Статус: {item.note}\n- Количество: {item.quantity}",
                    reply_markup=kb_admin.kb_candle_item_commands,
                )
                i += 1
        await message.reply(
            "Чего еще хочешь посмотреть, моя госпожа?",
            reply_markup=kb_admin.kb_candle_item_commands,
        )


# ---------------------------------------------CANDLE /удалить_свечу--------------------------COMPLETE
# /удалить_свечу
async def delete_info_candle_in_table(message: types.Message):
    if (
        message.text.lower() in ["удалить свечу", "/удалить_свечу"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            candles = session.scalars(select(CandleItems)).all()
            
        if candles == []:
            await bot.send_message(message.from_user.id, "В базе пока нет свечей")
        else:
            kb_candle_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in candles:
                await bot.send_photo(
                    message.from_user.id,
                    item.photo,
                    f"Свеча {item.name}\n"
                    f"- Цена: {item.price}\n"
                    f"- Количество: {item.quantity}\n"
                    f"- Описание: {item.note}",
                )
                kb_candle_names.add(KeyboardButton(item.name))
            kb_candle_names.add(KeyboardButton(LIST_BACK_TO_HOME[0]))
            await FSM_Admin_delete_info_candle_item.candle_name.set()
            await bot.send_message(
                message.from_user.id,
                "Какую свечу удалить?",
                reply_markup=kb_candle_names,
            )


async def delete_info_candle_in_table_next(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        candles = session.scalars(select(CandleItems.name)).all()
    if message.text in candles:
        with Session(engine) as session:
            candle = session.scalars(select(CandleItems)
                .where(CandleItems.name == message.text)).one()
            session.delete(candle)
            session.commit()
            # await delete_info("candle_items", "name", message.text)
            await message.reply(
                f"Готово! Вы удалили свечу {message.text}", reply_markup=kb_admin.kb_candle_item_commands
            )
            await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS:
        await bot.send_message(
            message.from_user.id, MSG_NO_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


def register_handlers_admin_candle(dp: Dispatcher):
    # -------------------------------------CANDLE--------------------------------------
    dp.register_message_handler(get_candle_command_list, commands=["свеча"], state=None)
    dp.register_message_handler(
        get_candle_command_list, Text(equals="свеча", ignore_case=True), state=None
    )

    dp.register_message_handler(
        command_load_candle_item, commands=["добавить_свечу"], state=None
    )
    dp.register_message_handler(
        command_load_candle_item,
        Text(equals="добавить свечу", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        load_candle_name, state=FSM_Admin_candle_item.candle_name
    )
    dp.register_message_handler(
        load_candle_photo,
        content_types=["photo", 'text'],
        state=FSM_Admin_candle_item.candle_photo,
    )
    dp.register_message_handler(
        load_candle_price, state=FSM_Admin_candle_item.candle_price
    )
    dp.register_message_handler(
        load_candle_note, state=FSM_Admin_candle_item.candle_note
    )
    dp.register_message_handler(
        load_candle_state, state=FSM_Admin_candle_item.candle_state
    )
    
    dp.register_message_handler(
        command_get_info_candles, commands=["посмотреть_список_свечей"]
    )
    dp.register_message_handler(
        command_get_info_candles,
        Text(equals="посмотреть список свечей", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_candles_having, commands=["посмотреть_список_имеющихся_свечей"]
    )
    dp.register_message_handler(
        command_get_info_candles_having,
        Text(equals="посмотреть список имеющихся свечей", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(
        command_get_info_candles_not_having,
        commands=["посмотреть_список_не_имеющихся_свечей"],
    )
    dp.register_message_handler(
        command_get_info_candles_not_having,
        Text(equals="посмотреть список не имеющихся свечей", ignore_case=True),
        state=None,
    )

    dp.register_message_handler(command_get_info_candle, commands=["посмотреть_свечу"])
    dp.register_message_handler(
        command_get_info_candle,
        Text(equals="посмотреть свечу", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_candle_name_for_info, state=FSM_Admin_get_info_candle_item.candle_name
    )

    dp.register_message_handler(delete_info_candle_in_table, commands=["удалить_свечу"])
    dp.register_message_handler(
        delete_info_candle_in_table,
        Text(equals="удалить свечу", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        delete_info_candle_in_table_next,
        state=FSM_Admin_delete_info_candle_item.candle_name,
    )
