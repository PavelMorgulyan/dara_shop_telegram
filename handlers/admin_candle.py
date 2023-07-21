from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES

from aiogram.types import CallbackQuery, ReplyKeyboardMarkup

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.calendar_client import obj
from msg.main_msg import *

from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

from prettytable import PrettyTable


async def send_to_view_candle_items(message: types.Message, candles: ScalarResult["CandleItems"]):
    headers = [
        "Имя",
        "Цена",
        "Количество"
    ]
    table = PrettyTable(
        headers, left_padding_width=1, right_padding_width=1
    )  # Определяем таблицу
    for item in candles:
        table.add_row(
            [
                item.name,
                item.price,
                item.quantity
            ]
        )
    await bot.send_message(
        message.from_id, f"<pre>{table}</pre>", parse_mode=types.ParseMode.HTML
    )
    await bot.send_message(
        message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE, reply_markup= kb_admin.kb_candle_item_commands
    )


# --------------------------------------CANDLE COMMAND LIST-----------------------------------
# /добавить_свечу, Отправляем название свечи
async def get_candle_command_list(message: types.Message):
    if (
        message.text.lower() in ["свечи", "/свечи"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await message.reply(
            MSG_WHICH_COMMAND_TO_EXECUTE,
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
    try:
        if message.text == kb_client.yes_str:
            await message.reply(
                "Сколько таких свечей у тебя есть? Напиши количество",
                reply_markup=kb_admin.kb_sizes,
            )
        elif message.text == kb_client.no_str or int(message.text) in kb_admin.sizes_lst:
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
    except ValueError as error:
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
            await bot.send_message(message.from_user.id, "⭕️ В базе пока нет свечей")
        else:
            await send_to_view_candle_items(message, candles)


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
        if candles == []:
            await bot.send_message(message.from_user.id, "В базе пока нет свечей")
            await bot.send_message(message.from_user.id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        else:
            kb_candles_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in candles:
                kb_candles_names.add(item.name)
            await FSM_Admin_get_info_candle_item.candle_name.set()
            await message.reply(
                "Какую свечу хочешь посмотреть?", reply_markup= kb_candles_names
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
        if item.photo in ["", "-"]:
            msg += f"- Без фото\n"
            await bot.send_message(message.from_user.id, msg)
        else:
            await bot.send_photo(message.from_user.id, item.photo, msg)

        await message.reply(
            MSG_DO_CLIENT_WANT_TO_DO_MORE, reply_markup=kb_admin.kb_candle_item_commands
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
        with Session(engine) as session:
            candles = session.scalars(select(CandleItems)
                .where(CandleItems.quantity != 0)).all()

        if candles == []:
            await bot.send_message(
                message.from_user.id, "У тебя пока нет купленных свечей в базе"
            )
        else:
            await send_to_view_candle_items(message, candles)
        


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
                "У тебя все свечи есть! Посмотри в таблице купленных свечей",
            )
        else:
            await send_to_view_candle_items(message, candles)


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
            await bot.send_message(message.from_user.id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        else:
            kb_candle_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in candles:
                kb_candle_names.add(KeyboardButton(item.name))
            kb_candle_names.add(kb_admin.home_btn)
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
            await message.reply(
                f"Готово! Свеча {message.text} удалена. {MSG_DO_CLIENT_WANT_TO_DO_MORE}", 
                reply_markup=kb_admin.kb_candle_item_commands
            )
            await state.finish()

    elif message.text in LIST_CANCEL_COMMANDS:
        await bot.send_message(
            message.from_user.id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )


#------------------------------CHANGE_CANDLE ---------------------------------------
class FSM_Admin_change_candle_item(StatesGroup):
    get_candle_item_name = State()  # 
    get_state_name = State()
    get_new_value = State()
    get_another_price = State()


async def get_command_change_candle_item(message: types.Message):
    if (
        message.text.lower() in ["изменить свечу", "/изменить_свечу"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            candles = session.scalars(select(CandleItems)).all()
            
        if candles == []:
            await bot.send_message(message.from_user.id, "В базе пока нет свечей")
            await bot.send_message(message.from_user.id, MSG_DO_CLIENT_WANT_TO_DO_MORE)
        else:
            kb_candles_names = ReplyKeyboardMarkup(resize_keyboard=True)
            for item in candles:
                kb_candles_names.add(KeyboardButton(item.name))
            await FSM_Admin_change_candle_item.get_candle_item_name.set()
            await message.reply(
                "❔ Какую свечу изменить?", reply_markup= kb_candles_names
            )


async def get_candle_item_name_to_change(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        candles = session.scalars(select(CandleItems)).all()
    kb_candles_names_lst= []
    kb_candles_names = ReplyKeyboardMarkup(resize_keyboard=True)
    for candle in candles:
        kb_candles_names_lst.append(candle.name)
        kb_candles_names.add(KeyboardButton(candle.name))
        
    if message.text in kb_candles_names_lst:
        async with state.proxy() as data:
            data['candle_name'] = message.text
            data['kb_candles_names'] = kb_candles_names
        await FSM_Admin_change_candle_item.next() # -> get_column_candle_item_name
        await bot.send_message(
            message.from_id, "❔ Что изменить?", reply_markup= kb_admin.kb_candle_item_columns
        )


async def get_column_candle_item_name(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.candle_item_columns.values()):
        async with state.proxy() as data:
            data['candle_column_name'] = message.text
            
        await FSM_Admin_change_candle_item.next() # -> get_new_value_candle_item
        
        if message.text == kb_admin.candle_item_columns['price']:
            await bot.send_message(
                message.from_id, "Выбери новую цену свечи", reply_markup= kb_admin.kb_price
            )
        elif message.text == kb_admin.candle_item_columns['note']:
            await bot.send_message(
                message.from_id, "Добавь новое описание свечи", reply_markup= kb_client.kb_cancel
            )
            
        elif message.text == kb_admin.candle_item_columns['photo']:
            await bot.send_message(
                message.from_id, "Отправь новое фото свечи", reply_markup= kb_client.kb_cancel
            )
        elif message.text == kb_admin.candle_item_columns['name']:
            await bot.send_message(
                message.from_id, "Какое будет новое название у свечи? Напиши в строке",
                reply_markup= kb_client.kb_back_cancel
            )
        elif message.text == kb_admin.candle_item_columns['quantity']:
            await bot.send_message(
                message.from_id, "Какое новое количество будет у этой свечи? Выбери из списка",
                reply_markup= kb_admin.kb_sizes
            )
            
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_candle_item_commands,
        )
    elif message.text in LIST_BACK_COMMANDS:
        await FSM_Admin_change_candle_item.previous() # -> get_command_change_candle_item
        async with state.proxy() as data:
            kb_candles_names = data['kb_candles_names']
        
        await message.reply(
            "❔ Какую свечу изменить?", reply_markup= kb_candles_names
        )
        
    else:
        await bot.send_message(message.from_id, MSG_NO_CORRECT_INFO_TO_SEND)


async def process_callback_set_price_from_line_candle(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 
        MSG_ADMIN_SET_ANOTHER_PRICE_FROM_LINE, reply_markup= kb_client.kb_cancel
    )


async def get_new_value_candle_item(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        candle_name = data['candle_name']
        candle_column_name = data['candle_column_name']
        
    if message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_candle_item_commands,
        )
    elif message.text in kb_admin.another_price_lst: # ["Другая цена"]
        await bot.send_message(
            message.from_id,
            MSG_ADMIN_SET_ANOTHER_PRICE,
            reply_markup=kb_admin.kb_another_price_full,
        )
        await bot.send_message(
            message.from_id, 
            MSG_ADMIN_CAN_SET_ANOTHER_PRICE,
            reply_markup= kb_admin.kb_set_another_price_from_line
        )
        await FSM_Admin_change_candle_item.next() #-> get_another_price_from_admin
    else:
        with Session(engine) as session: 
            item = session.scalars(select(CandleItems)
                    .where(CandleItems.name == candle_name)
                ).one()
            
            if candle_column_name == kb_admin.candle_item_columns['price'] and message.text.isdigit():
                item.price = int(message.text)
                
            elif message.content_type == 'photo' and kb_admin.candle_item_columns['photo']:
                item.photo = message.photo[0].file_id
            
            elif message.text.isdigit() and candle_column_name == kb_admin.candle_item_columns['quantity']:
                item.quantity = int(message.text)
                
            elif candle_column_name == kb_admin.candle_item_columns['note']:
                item.note = message.text
                
            elif candle_column_name == kb_admin.candle_item_columns['name']:
                item.name = message.text
                
            elif message.text in kb_admin.another_price_lst:
                await bot.send_message(
                    message.from_id,
                    MSG_ADMIN_SET_ANOTHER_PRICE,
                    reply_markup=kb_admin.kb_another_price_full,
                )
            
            session.commit()
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"🎉 Отлично, у свечи {candle_name} изменился параметр \"{candle_column_name}\"!"
        )
        await bot.send_message(
            message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE, reply_markup= kb_admin.kb_candle_item_commands
        )


async def get_another_price_from_admin(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        candle_name = data['candle_name']
        
    if message.text.isdigit():
        with Session(engine) as session:
            item = session.scalars(select(CandleItems)
                    .where(CandleItems.name == candle_name)
                ).one()
            item.price = int(message.text)
            session.commit()
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"🎉 Отлично, у свечи {candle_name} изменился параметр \"Цена\" на {message.text}!"
        )
        await bot.send_message(
            message.from_id, MSG_DO_CLIENT_WANT_TO_DO_MORE, reply_markup= kb_admin.kb_candle_item_commands
        )
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup= kb_admin.kb_candle_item_commands,
        )
    else:
        await bot.send_message(
            message.from_id, MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST
        )

def register_handlers_admin_candle(dp: Dispatcher):
    # -------------------------------------CANDLE--------------------------------------
    dp.register_message_handler(get_candle_command_list,
        commands=["свеча", kb_admin.commands_button['candles']], state=None)
    dp.register_message_handler(
        get_candle_command_list, Text(equals=kb_admin.commands_button['candles'], ignore_case=True), state=None
    )

    #---------------------------------add new candle----------------------
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
    
    #--------------------------view candles list -------------------------------
    dp.register_message_handler(
        command_get_info_candles, commands=["посмотреть_список_свечей"]
    )
    dp.register_message_handler(
        command_get_info_candles,
        Text(equals="посмотреть список свечей", ignore_case=True),
        state=None,
    )

    #--------------------------view having candles list -------------------------------
    dp.register_message_handler(
        command_get_info_candles_having, commands=["посмотреть_список_имеющихся_свечей"]
    )
    dp.register_message_handler(
        command_get_info_candles_having,
        Text(equals="посмотреть список имеющихся свечей", ignore_case=True),
        state=None,
    )

    #--------------------------view not having candles list -------------------------------
    dp.register_message_handler(
        command_get_info_candles_not_having,
        commands=["посмотреть_список_не_имеющихся_свечей"],
    )
    dp.register_message_handler(
        command_get_info_candles_not_having,
        Text(equals="посмотреть список не имеющихся свечей", ignore_case=True),
        state=None,
    )

    #--------------------------view candle -------------------------------
    dp.register_message_handler(command_get_info_candle, commands=["посмотреть_свечу"])
    dp.register_message_handler(
        command_get_info_candle,
        Text(equals="посмотреть свечу", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_candle_name_for_info, state=FSM_Admin_get_info_candle_item.candle_name
    )

    #--------------------------delete candle -------------------------------
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

    #-----------------------------CHANGE_CANDLE_ITEM-------------
    dp.register_message_handler(get_command_change_candle_item, commands=["изменить_свечу"])
    dp.register_message_handler(get_command_change_candle_item, 
        Text(equals="изменить свечу", ignore_case=True),
        state=None,
    )
    dp.register_message_handler(
        get_candle_item_name_to_change, state=FSM_Admin_change_candle_item.get_candle_item_name
    )
    dp.register_message_handler(
        get_column_candle_item_name, state=FSM_Admin_change_candle_item.get_state_name
    )
    
    dp.register_message_handler(
        get_new_value_candle_item, content_types= ['photo', 'text'],
        state=FSM_Admin_change_candle_item.get_new_value
    )
    
    dp.register_callback_query_handler(process_callback_set_price_from_line_candle,
        state=FSM_Admin_change_candle_item.get_another_price)

    dp.register_message_handler(get_another_price_from_admin,
        state=FSM_Admin_change_candle_item.get_another_price)