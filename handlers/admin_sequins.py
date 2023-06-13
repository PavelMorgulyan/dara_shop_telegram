from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from prettytable import PrettyTable
from create_bot import dp, bot
from keyboards import kb_client, kb_admin
from aiogram.dispatcher.filters import Text
from handlers.client import ADMIN_NAMES

from handlers.other import *
from sqlalchemy.orm import Session
from sqlalchemy import select, ScalarResult
from db.sqlalchemy_base.db_classes import *

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup
from msg.main_msg import *


async def get_seq_command_list(message: types.Message):
    if (
        message.text.lower() in ["блестки", "/блестки"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await bot.send_message(message.from_id,
            "Какие команды с блестками хочешь выполнить?", reply_markup= kb_admin.kb_sequins_commands
        )


class FSM_Admin_create_seq_item(StatesGroup):
    get_seq_name = State()
    get_seq_price = State()
    get_seq_quantity = State()
    get_seq_photo = State()



# добавить блестки
async def command_create_seq_item(message: types.Message):
    if (
        message.text.lower() in ["добавить блестки", "/добавить_блестки"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        await FSM_Admin_create_seq_item.get_seq_name.set()
        await bot.send_message(message.from_id, "Напиши название блесток", reply_markup= kb_client.kb_cancel)


async def get_seq_name_new_item(message: types.Message, state: FSMContext):
    if message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_sequins_commands,
        )
        
    else:
        with Session(engine) as session:
            seqs = session.scalars(select(SequinsItems)).all()
        seq_names_lst = []
        for seq in seqs:
            seq_names_lst.append(seq.name)
            
        if message.text not in seq_names_lst:
            async with state.proxy() as data:
                data['seq_name'] = message.text
                
            await bot.send_message(
                message.from_id, 
                "По какой цене блестки?",
                reply_markup= kb_admin.kb_price)
            
            await FSM_Admin_create_seq_item.next() #-> get_seq_price
            
        elif message.text in seq_names_lst:
            await bot.send_message(
                message.from_id,
                f"Уже есть блестки с названием {message.text}. Введи другое название")


async def process_callback_set_price_from_line(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 
        MSG_ADMIN_SET_ANOTHER_PRICE_FROM_LINE, reply_markup= kb_client.kb_cancel
    )

async def get_seq_price(message: types.Message, state: FSMContext):
    if message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_sequins_commands,
        )
    elif message.text == kb_admin.get_price_from_line_str:
        await message.reply(
            MSG_ADMIN_SET_ANOTHER_PRICE_FROM_LINE, reply_markup= kb_client.kb_cancel
        )
    elif message.text in kb_admin.another_price_lst:
        await message.reply(
            MSG_ADMIN_SET_ANOTHER_PRICE, reply_markup=kb_admin.kb_another_price_full
        )
        await bot.send_message(
            message.from_id, 
            MSG_ADMIN_CAN_SET_ANOTHER_PRICE,
            reply_markup= kb_admin.kb_set_another_price_from_line
        )
    elif message.text.isdigit():
        async with state.proxy() as data:
            data['price'] = int(message.text)
        
        await bot.send_message(
            message.from_id, f"Теперь у блесток цена {message.text}"
        )
        await FSM_Admin_create_seq_item.next() #->get_seq_quantity
        await bot.send_message(
            message.from_id, 
            "Выбери количество блесток, которое у тебя есть в наличии", 
            reply_markup= kb_admin.kb_sizes
        )
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_seq_quantity(message: types.Message, state: FSMContext):
    try:
        if int(message.text) in kb_admin.sizes_lst:
            async with state.proxy() as data:
                data['seq_quantity'] = int(message.text)
                data["seq_photo"] = None
            await FSM_Admin_create_seq_item.next() #->set_new_seq_item
            await bot.send_message(
                message.from_id, 
                "Хочешь добавить фото для блесток?",
                reply_markup= kb_client.kb_yes_no
            )
        elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
            await state.finish()
            await bot.send_message(
                message.from_id,
                MSG_BACK_TO_HOME,
                reply_markup= kb_admin.kb_sequins_commands,
            )
        else:
            await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)
    except ValueError as error:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def set_new_seq_item(data:tuple, message: types.Message):
    with Session(engine) as session:
        new_seq_item = SequinsItems(
            name= data['seq_name'],
            price= data['price'],
            quantity=data['seq_quantity'],
            photo=data["seq_photo"],
        )
        session.add(new_seq_item)
        session.commit()
    await bot.send_message(
        message.from_id,
        f"Вы добавили новые блестки под названием {data['seq_name']}!\n"
        f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}",
        reply_markup= kb_admin.kb_sequins_commands,
    )


async def get_seq_photo(message: types.Message, state: FSMContext):
    
    if message.content_type== 'text':
        if message.text == kb_client.yes_str:
            await bot.send_message(
                message.from_id,
                "📎 Добавь фото блесток. Можно отправить только одну фотографию (через 📎)",
                reply_markup= kb_client.kb_cancel)
            
        elif message.text == kb_client.no_str:
            async with state.proxy() as data:
                await set_new_seq_item(data, message)
            await state.finish()
            
        elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
            await state.finish()
            await bot.send_message(
                message.from_id,
                MSG_BACK_TO_HOME,
                reply_markup=kb_admin.kb_sequins_commands,
            )
            
    elif message.content_type == 'photo':
        async with state.proxy() as data:
            data["seq_photo"] = message.photo[0].file_id
            await set_new_seq_item(data, message)


#--------------------------------------------------------VIEW SEQ------------------------------

async def command_view_seq_item(message: types.Message):
    if (
        message.text.lower() in ["посмотреть блестки", "/посмотреть_блестки"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        with Session(engine) as session:
            seqs = session.scalars(select(SequinsItems)).all()
        if seqs == []:
            await bot.send_message(message.from_id, '⭕️ Нет блесток в базе данных')
        else:
            headers = ['№', 'Название', 'Кол.', 'Цена']
            photo_lst = []
            for item in seqs:
                table = PrettyTable(
                    headers, left_padding_width=1, right_padding_width=1
                )  # Определяем таблицу
                photo_lst.append(item.photo)
                table.add_row(
                    [
                        item.id,
                        item.name,
                        item.quantity,
                        item.price
                    ]
                )
                await bot.send_message(
                    message.from_id, f"<pre>{table}</pre>", 
                    parse_mode=types.ParseMode.HTML,
                    reply_markup=kb_admin.kb_sequins_commands,
                )
                
            # TODO сделать media вывод фотографий 

#--------------------------------------------------------DELETE SEQ------------------------------
class FSM_Admin_delete_seq_item(StatesGroup):
    get_seq_name = State()


async def command_delete_seq_item(message: types.Message):
    if (
        message.text.lower() in ["удалить блестки", "/удалить_блестки"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        kb= ReplyKeyboardMarkup(resize_keyboard= True)
        with Session(engine) as session:
            seqs = session.scalars(select(SequinsItems)).all()
        
        for item in seqs:
            kb.add(KeyboardButton(item.name))
        kb.add(kb_admin.kb_back_home)
        
        await FSM_Admin_delete_seq_item.get_seq_name.set()
        
        await bot.send_message(
            message.from_id,
            "Какие блестки удалить?",
            reply_markup= kb
        )


async def get_seq_name_to_delete(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        seqs = session.scalars(select(SequinsItems)).all()
    seq_names = []
    for item in seqs:
        seq_names.append(item.name)
    
    if message.text in seq_names:
        with Session(engine) as session:
            seq = session.scalars(select(SequinsItems).where(SequinsItems.name == message.text)).one()
            session.delete(seq)
            session.commit()
            
        await state.finish()
        await bot.send_message(
            message.from_id,
            f"Блестки {message.text} удалены"
        )
        await bot.send_message(
            message.from_id,
            MSG_DO_CLIENT_WANT_TO_DO_MORE,
            reply_markup=kb_admin.kb_sequins_commands,
        )
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_sequins_commands,
        )
        
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)

#--------------------------------------------------------CHANGE SEQ------------------------------
class FSM_Admin_change_seq_item(StatesGroup):
    get_seq_name = State()
    get_seq_column_name = State()
    get_seq_new_value = State()


async def command_change_seq_item(message: types.Message):
    if (
        message.text.lower() in ["изменить блестки", "/изменить_блестки"]
        and str(message.from_user.username) in ADMIN_NAMES
    ):
        kb= ReplyKeyboardMarkup(resize_keyboard= True)
        with Session(engine) as session:
            seqs = session.scalars(select(SequinsItems)).all()
        
        for item in seqs:
            kb.add(KeyboardButton(item.name))
        kb.add(kb_admin.back_btn)
        
        await FSM_Admin_change_seq_item.get_seq_name.set()
        
        await bot.send_message(
            message.from_id,
            "Какие блестки изменить?",
            reply_markup= kb
        )


async def get_seq_name_to_change(message: types.Message, state: FSMContext):
    with Session(engine) as session:
        seqs = session.scalars(select(SequinsItems.name)).all()

    if message.text in seqs:
        with Session(engine) as session:
            seq_id = session.scalars(select(SequinsItems)
                    .where(SequinsItems.name == message.text)).one().id
        async with state.proxy() as data:
            data["seq_name"] = message.text
            data["seq_id"] = seq_id
            
        await FSM_Admin_change_seq_item.next() #-> get_seq_column_name_to_change
        await bot.send_message(message.from_id, "Что изменить?", reply_markup= kb_admin.kb_seq_columns)
        
    elif message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_sequins_commands,
        )
        
    else:
        await message.reply(MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST)


async def get_seq_column_name_to_change(message: types.Message, state: FSMContext):
    if message.text in list(kb_admin.seq_columns.keys()):
        async with state.proxy() as data:
            data["column_to_change"] = kb_admin.seq_columns[message.text]
            
        await FSM_Admin_change_seq_item.next() #-> get_new_value_to_column_seq
        
        messages = {
            "Фото":         {"msg":"Добавь новую фотографию блесток", "kb": kb_client.kb_cancel},
            "Цена":         {"msg": MSG_ADMIN_SET_ANOTHER_PRICE, "kb": kb_admin.kb_another_price_full},
            "Название":     {"msg":"Напиши другое название для блестки", "kb": kb_client.kb_cancel},
            "Количество":   {"msg":"Выбери новое количество таких блесток", "kb": kb_admin.kb_sizes},
        }
        
        await bot.send_message(
            message.from_id, messages[message.text]["msg"],
            reply_markup= messages[message.text]["kb"]
        )
        if message.text == "Цена":
            await bot.send_message(
                message.from_id, 
                "Добавь новую цену для блесток",
                reply_markup= kb_admin.kb_set_another_price_from_line
            )


async def process_callback_set_price_from_line(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 
        MSG_ADMIN_SET_ANOTHER_PRICE_FROM_LINE, reply_markup= kb_client.kb_cancel
    )


async def get_new_value_to_column_seq(message: types.Message, state: FSMContext):
    if message.text in LIST_BACK_TO_HOME + LIST_CANCEL_COMMANDS:
        await state.finish()
        await bot.send_message(
            message.from_id,
            MSG_BACK_TO_HOME,
            reply_markup=kb_admin.kb_sequins_commands,
        )
        
    else:
        async with state.proxy() as data:
            seq_id = data['seq_id']
            seq_name = data['seq_name']
            column_to_change = data["column_to_change"]
        
        with Session(engine) as session:
            seq = session.get(SequinsItems, seq_id)
            """ column = {
                "name": seq.name,
                "price": seq.price,
                "quantity": seq.quantity,
                "photo": seq.photo
            } """
            
            if message.content_type == 'photo':
                seq.photo = message.photo[0].file_id
                
            elif message.text.isdigit():
                if column_to_change == "price":
                    seq.price = int(message.text)
                elif column_to_change == "quantity":
                    seq.quantity = int(message.text)
                    
            else:
                seq.name = message.text
                
            session.commit()
            await state.finish()
            
            await bot.send_message(
                message.from_id, (f"🎉 Блестки {seq_name} изменены!\n\n "
                f"{MSG_DO_CLIENT_WANT_TO_DO_MORE}"),
                reply_markup= kb_admin.kb_sequins_commands
            )


def register_handlers_admin_sequins(dp: Dispatcher):
    dp.register_message_handler(
        get_seq_command_list, commands=["блестки"]
    )
    dp.register_message_handler(
        get_seq_command_list,
        Text(equals="Блестки", ignore_case=True),
        state=None,
    )
    
    dp.register_message_handler(command_create_seq_item,
        Text(equals=kb_admin.sequins_commands["create"], ignore_case=True),
        state=None
    )
    dp.register_message_handler(get_seq_name_new_item,
        state=FSM_Admin_create_seq_item.get_seq_name)
    dp.register_message_handler(get_seq_price,
        state=FSM_Admin_create_seq_item.get_seq_price)
    
    dp.register_callback_query_handler(process_callback_set_price_from_line,
        state=FSM_Admin_create_seq_item.get_seq_price)
    
    dp.register_message_handler(get_seq_quantity,
        state=FSM_Admin_create_seq_item.get_seq_quantity)
    dp.register_message_handler(get_seq_photo,
        content_types=["photo", "text"],
        state=FSM_Admin_create_seq_item.get_seq_photo)
    
    dp.register_message_handler(command_view_seq_item,
        Text(equals=kb_admin.sequins_commands["view"], ignore_case=True),
        state=None
    )
    
    dp.register_message_handler(command_delete_seq_item,
        Text(equals=kb_admin.sequins_commands["delete"], ignore_case=True),
        state=None
    )
    dp.register_message_handler(get_seq_name_to_delete,
        state=FSM_Admin_delete_seq_item.get_seq_name)
    
    dp.register_message_handler(command_change_seq_item,
        Text(equals=kb_admin.sequins_commands["change"], ignore_case=True),
        state=None
    )
    
    dp.register_message_handler(get_seq_name_to_change,
        state=FSM_Admin_change_seq_item.get_seq_name)
    dp.register_message_handler(get_seq_column_name_to_change,
        state=FSM_Admin_change_seq_item.get_seq_column_name)
    dp.register_callback_query_handler(process_callback_set_price_from_line,
        state=FSM_Admin_change_seq_item.get_seq_new_value)
    dp.register_message_handler(get_new_value_to_column_seq,
        content_types=["photo", "text"],
        state=FSM_Admin_change_seq_item.get_seq_new_value)