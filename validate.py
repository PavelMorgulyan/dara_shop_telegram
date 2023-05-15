import cv2
import pytesseract
from PIL import Image
import fitz
from aiogram import types
from create_bot import bot
from msg.main_msg import CHECK_LIST, LIST_PHONE_NUMBER, MSG_ERROR_CHECK_VALIDATE_ADMIN_NAME,\
    MSG_ERROR_CHECK_VALIDATE_ORDER_PRICE, MSG_ERROR_CHECK_VALIDATE_NOT_CORRECT_ADMIN_PHONE_NUMBER,\
    MSG_ERROR_CHECK_VALIDATE_NOT_CORRECT_CHECK_DOCUMENT



async def check_pdf_document_payment(user_id: int, price: str, file_name: str, file_id) -> dict[str, bool|str]:
    receiver_name_bool, price_check_bool, phone_number_bool, \
        check_header_bool = False, False, False, False
        
    files = await bot.get_file(file_id)
    src = 'C:\\files\\checks\\' + str(user_id) + '\\'  +  \
        files.file_path.split(".")[0] + '_' + file_name
    # file_info = await bot.get_file(file_id) # await file_info.download(src) 
    await bot.download_file_by_id(file_id, src)
    price_lst = []
    
    if ' ' in price:
        price_lst = [price, price.replace(' ', '.'), price.replace(' ', '.') + ',00', 
            price.replace(' ', '.') + '.00', price.replace(' ', '')]
        
    else:
        price_lst = [price, price.replace('000', '.000'), price.replace('000', '.000') + ',00', 
            price.replace('000', '.000') + '.00']

    if ',' not in price:
        price_lst = [price, price + ',00'] # '5 000,00'
    
    receiver_name_str = 'Дария Редван Э'
    
    pdf_document = fitz.open(src)
    for current_page in range(len(pdf_document)):  
        page = pdf_document.load_page(current_page)
        if page.search_for(receiver_name_str):
            receiver_name_bool = True
            
        for price_check_str in price_lst:
            if page.search_for(price_check_str):
                price_check_bool = True
                break
            
        for check_header in CHECK_LIST:
            if page.search_for(check_header):
                check_header_bool = True
                break
            
        for phone_number in LIST_PHONE_NUMBER:
            if page.search_for(phone_number):
                phone_number_bool = True
                break
    
    if not receiver_name_bool:
        return {"result": False, "report_msg": MSG_ERROR_CHECK_VALIDATE_ADMIN_NAME}
            
    elif not price_check_bool:
        return {"result": False, "report_msg":  MSG_ERROR_CHECK_VALIDATE_ORDER_PRICE % price}
            
    elif not phone_number_bool:
        return {"result": False, "report_msg": MSG_ERROR_CHECK_VALIDATE_NOT_CORRECT_ADMIN_PHONE_NUMBER % price}
            
    elif not check_header_bool:
        return {"result": False, "report_msg": MSG_ERROR_CHECK_VALIDATE_NOT_CORRECT_CHECK_DOCUMENT  % price}
            
    return {"result": True, "report_msg": "COMPLETE"}


# document - message.document, message.document.file_name, message.document.file_id
async def check_photo_payment(message:types.Message, user_id: int, price: str, file_name: str, file_id) -> dict[str, bool|str]:

    # file_info = await bot.get_file(file_id)
    # await file_info.download(src)
    file = await bot.get_file(file_id)
    src = 'C:\\files\\checks\\' + str(user_id) + '\\'  +  \
        file.file_path.split(".")[0] + '_' + file_name
    # await bot.download_file_by_id(file_id = file_id, destination_dir= src )
    await message.photo[-1].download(src)

    price_lst = [price]
    
    if ' ' in price:
        price_lst = [price, price.replace(' ', '.'), price.replace(' ', '.') + ',00', 
            price.replace(' ', '.') + '.00', price.replace(' ', '')]
        
    else:
        price_lst = [price, price.replace('000', '.000'), price.replace('000', '.000') + ',00', 
            price.replace('000', '.000') + '.00']

    if ',' not in price:
        price_lst.append(price + ',00') # '5 000,00'
    
    img_format_lst = ['JPEG', 'PNG', 'GIF', 'BMP']
    with Image.open(src) as img:
        # Check if image file is in a supported format
        if img.format not in img_format_lst:
            return {
                "result": False, 
                "report_msg": "Изображение не имеет необходимый формат. "\
                    f"Пожалуйста, отправь изображение в формате {', '.join([value for value in img_format_lst])}"
            }
    
    img = cv2.imread(src)# Read image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # Convert image to grayscale

    # В докере требуется установка
    text = pytesseract.image_to_string(gray, 'rus') # Use pytesseract to extract text from the image
    
    if "Дария Редван Э" not in text:
        return {"result": False, "report_msg": MSG_ERROR_CHECK_VALIDATE_ADMIN_NAME}
        
    if not any(str(price) in text for price in price_lst):
        return {"result": False, "report_msg":  MSG_ERROR_CHECK_VALIDATE_ORDER_PRICE % price}
    
    if not any(str(phone) in text for phone in LIST_PHONE_NUMBER):
        return {"result": False, "report_msg": MSG_ERROR_CHECK_VALIDATE_NOT_CORRECT_ADMIN_PHONE_NUMBER % price}
        
    if not any(str(check) in text for check in CHECK_LIST):
        return {"result": False, "report_msg": MSG_ERROR_CHECK_VALIDATE_NOT_CORRECT_CHECK_DOCUMENT  % price}
    
    return {"result": True, "report_msg": "COMPLETE"}
