from aiogram import Bot
from aiogram.dispatcher import Dispatcher
import os
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()


bot = Bot(token=os.environ["ID_DARA_TELEGRAM_BOT"])
dp = Dispatcher(bot, storage=storage)
