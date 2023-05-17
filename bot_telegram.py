from aiogram.utils import executor
from create_bot import dp
from handlers import admins, client, client_tattoo_order, admin_price_list, admin_schedule,\
    admin_tattoo_item, admin_tattoo_order, admin_sketch
''' \
    admin_cert, admin_tattoo_order,\
    admin_candle, admin_giftbox_item, admin_giftbox_order, admin_clients_commands,\
    client_certificate_order, client_giftbox, client_sketch_order, client_payload, \
    admin_generate_ai_img '''
    

from db.db_create import *
from db.db_setter import *
from db.db_filling import *
import schedule
import time
from threading import Timer


async def on_startup(_):
    print("Bot is online")
    
# from handlers import admin

# schedule.every().day.at("10:30").do(await send_notification_schedule)
client.register_handlers_client(dp)
client_tattoo_order.register_handlers_client_tattoo_order(dp)
''' 

client_certificate_order.register_handlers_client_cert(dp)
client_giftbox.register_handlers_client_giftbox(dp)
client_sketch_order.register_handlers_client_sketch(dp)
client_payload.register_handlers_client_payload(dp)
'''

admins.register_handlers_admin(dp)
admin_price_list.register_handlers_admin_price_list(dp)
admin_schedule.register_handlers_admin_schedule(dp)
admin_tattoo_item.register_handlers_admin_tattoo_item(dp)
admin_tattoo_order.register_handlers_admin_tattoo_order(dp)
admin_sketch.register_handlers_admin_sketch(dp)
'''
admin_sketch.register_handlers_admin_sketch(dp)
admin_cert.register_handlers_admin_cert(dp)

admin_candle.register_handlers_admin_candle(dp)
admin_giftbox_item.register_handlers_admin_giftbox_item(dp)
admin_giftbox_order.register_handlers_admin_giftbox_order(dp)
admin_clients_commands.register_handlers_admin_client_commands(dp)
admin_generate_ai_img.register_handlers_admin_generate_img(dp) '''
#other.register_handlers_other(dp)




executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

''' 
t = Timer(86400, send_notification_schedule)
t.start() 
'''