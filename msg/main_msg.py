LIST_CANCEL_COMMANDS = [
    "отмена",
    "/отмена",
    "/cancel",
    "cancel",
    "отмена ❌",
    "Отмена ❌",
]

LIST_BACK_COMMANDS = ["назад", "Назад", "назад 🔙", "Назад 🔄", "назад 🔄", "Назад 🔄"]

LIST_BACK_TO_HOME = ["Домой 🏚"]

MSG_BACK_TO_HOME = "🏚 Вы вернулись в меню. Хотите что-нибудь сделать?"

LIST_PHONE_NUMBER = [
    "+7(925) 885-07-87",
    "+7(925)885-07-87",
    "+7(@25)885-07-87" "8(925) 885-07-87",
    "8(925)885-07-87",
    "8-925-885-07-87",
    "+7(@25) 885-07-87",
]

MSG_NO_CORRECT_INFO_TO_SEND = (
    "❌ Вы ввели неверные данные. Пожалуйста, попробуйте еще раз."
)


MSG_START_TATTOO_ORDER = "🕸 Отлично, давай сделаем тебе тату! \n\n"

MSG_CLIENT_WANT_CURRENT_OR_NOT_TATTOO = "❔ Хотите постоянное тату или переводное?"

MSG_CLIENT_BACK_AND_WHICH_PHOTO_DO_CLIENT_WANT_TO_LOAD = (
    "🔄 Вы вернулись назад в меню выбора загрузки тату эскиза\n\n"
    "❔ Как хотите загрузить фотографию эскиза для своего тату?"
)

MSG_CLIENT_LOAD_PHOTO = (
    "📎 Загрузите изображение через файлы, пожалуйста. \n\n"
    "❕ Можно добавлять сразу несколько файлов."
)

MSG_SEND_ANOTHER_PHOTO = "📎 Загрузите еще изображения"

MSG_PHOTO_WAS_DELETED = 'Изображение было удалено!'

MSG_WHICH_PHOTO_DELETE = "❔ Какое фото/изображение удалить?"

MSG_ADMIN_ACCESS_ACTION = '❔ Подтверждаете данное действие?'

MSG_CLIENT_SUCCESS_CHOICE_PHOTO = (
    "📷 Отлично, вы выбрали фотографию эскиза для своего тату! \n\n"
)

MSG_DO_CLIENT_WANT_TO_CREATE_ORDER = "❔ Не желаете оформить какой-нибудь заказ?"

MSG_WHICH_COLOR_TYPE_WILL_BE_TATTOO = "❔ Это тату будет цветным или ч/б?"

MSG_WHICH_COLOR_WILL_BE_TATTOO = "❔ Какой цвет будет у тату?"

MSG_CLIENT_DONT_HAVE_ANY_ORDERS = (
    "⭕️ У вас пока нет тату для коррекции\n\n"
    f"{MSG_DO_CLIENT_WANT_TO_CREATE_ORDER}"
)

MSG_CLIENT_DONT_HAVE_SKETCH_ORDERS = (
    "⭕️ У вас пока нет заказов эскизов для оплаты.\n\n"
    f"{MSG_DO_CLIENT_WANT_TO_CREATE_ORDER}"
)

MSG_CLIENT_DONT_HAVE_GIFTBOX_ORDERS = (
    "⭕️ У вас пока нет гифтбоксов для оплаты.\n\n"
    f"{MSG_DO_CLIENT_WANT_TO_CREATE_ORDER}"
)

MSG_GET_PHOTO_FROM_USER = (
    "🌿 Если у вас нет идей для эскиза, вы можете выбрать из готовых тату эскизов, "
    "которые представлены в моей галерее. "
    'Для этого нужно нажать кнопку "Посмотреть галерею тату". \n\n'
    '🌿 Если хотите свой эскиз для тату, то нажми кнопку "Загрузить свою фотографию эскиза".\n\n'
    '🌿 Или вы можете нажать "У меня нет фотографии для эскиза", '
    "чтобы оставить выбор фотографии тату на потом.\n\n"
    '🌿 Чтобы вернуться в главное меню, необходимо нажать кнопку "Отмена"'
)

MSG_NOT_CORRECT_INFO_LETS_CHOICE_FROM_LIST = "❌ Пожалуйста, выберете вариант из списка."

CHECK_LIST = [
    "Чек по операции",
    "Перевод с карты на карту",
    "Платёж",
    "Платеж",
    "Перевод",
]

MSG_CANCEL_ACTION = "❌ Действие отменено. \n\n"

MSG_GET_CHECK = f"❔ Добавить чек к заказу?"

MSG_SUCCESS_GETTING_CHECK = "📃 Чек на оплату заказа"

MSG_CHECK_NOT_ADDED = "❌ Чек не добавлен"

GIFTBOX_DESCRIPTION = (
    " Отлично, давайте выберем гифтбокс.\n"
    "Как правило, мой гифтбокс состоит из следующих компонентов:  \n"
    "🕯- свечка с деревянным трескучим фитилём, пахнет так, будто упал лицом в морозную ёлку))) \n"
    "Объём- 90 мл, время горения - 15 часов \n"
    "✋🏻 - гипсовая ладошка, идеальна для пало-санто и конусных благовоний, \n"
    "а еще красиво хранит колечки и серёжки)\n"
    "✨- блёстки! От потрясающих ShinyBand, цвет примерно такой, как на картинке,"
    "  но точный оттенок будет для вас сюрпризом))\n"
    "🏞 - почтовая открытка из приятного плотного картона с рельефным покрытием, \n"
    "винтажная ботаническая или птичковая иллюстрация) \n"
    "🃏 - набор переводных татушек, пока в стадии отрисовки, возможно будет цветным. \n"
    "Темы - ботаника, лес, абстракция. \n"
    "Тату на восковой основе, смываются маслом, до 3-х дней держатся на сухой коже где нет трения."
)

MSG_INFO_ADMIN_CREATE_NEW_SCHEDULE_EVENT = (
    "❕ При выборе выбрать месяца и дня недели создаются даты с выбранным типом расписания. "
    "Например:\nвыбрав 2023 год, июнь и Понедельник в календарь заносятся следующие даты:\n"
    "05/06/2023, 12/06/2023, 19/06/2023, 26/06/2023\n"
    "Если какая-то из этих дат не подходит под твое расписание, или расписание изменилось, то "
    "можно либо удалить данную дату (кнопка \"удалить расписание\" в меню расписания),"
    " либо изменить расписание "
    "(кнопка \"изменить расписание\" в меню расписания)"
)

MSG_TO_CHOICE_CLIENT_PHONE = (
    "❕ Осталось только добавить свой телефон. \n\n "
    '☎️ Нажми кнопку "Отправить свой контакт ☎️", '
    "чтобы заказ никуда не потерялся, и у меня всегда была связь с вами!\n\n"
    "⭕️ Или вы можете не оставлять телефон. "
    'Для этого нажми кнопку "Не хочу оставлять свой телефон, только телеграм 💬"'
)

MSG_CLIENT_CHOICE_ADD_TATTOO_PHOTO_OR_BODY_PHOTO = (
    "❔ Добавить фотографию для эскиза или фотографию изображения тела?"
)

MSG_CLIENT_CHOICE_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY = (
    "❔ Добавить фото или видео/видео-заметки тела?"
)

MSG_ADD_ANOTHER_IMG_TO_ORDER = "📎 Добавьте еще фотографию через файлы."

MSG_Q_ADD_ANOTHER_IMG = "❔ Добавить еще изображение?"

MSG_PHOTO_WAS_ADDED_TO_ORDER = "❕ Фотографии эскиза успешно добавлены в заказ"

MSG_VIDEO_WAS_ADDED_TO_ORDER = "🎉 Видеозапись успешно добавлена в заказ!"

MSG_VIDEO_NOTE_WAS_ADDED_TO_ORDER = "🎉 Видео-заметка добавлена в заказ!"

MSG_NO_PRICE_LIST_IN_DB = (
    "❌ У вас пока нет прайс-листа.\n"
    "💬 Его необходимо заполнить c помощью функции "
    '"создать новый прайс-лист на тату". '
)

MSG_ADD_NEW_VIDEO_NOTE = "📎 Загрузите новую видео-записку тела через файлы"

MSG_ADD_NEW_VIDEO_BODY = "📎 Загрузите новую видеозапись тела через файлы"

MSG_ORDER_NOTE_WAS_UPDATED = f"🎉 Описание заказа было обновлено!"

MSG_TATTOO_SIZE_WAS_UPDATED = f"🎉 Размер тату было обновлено!"

MSG_TATTOO_NOTE_WAS_UPDATED = f"🎉 Описание тату было обновлено!"

MSG_TATTOO_NAME_WAS_UPDATED = f"🎉 Имя тату было обновлено!"

MSG_TATTOO_COLOR_WAS_UPDATED = f"🎉 Цвет тату был обновлен!"

MSG_TATTOO_BODYPLACE_WAS_UPDATED = f"🎉 Место для тату было обновлено!"

MSG_WHTCH_TATTOO_ANOTHER_SIZE_DO_CLIENT_WANT = "❔ Какой размер тату вы хотели бы?"

MSG_WHITCH_ORDER_WANT_TO_SEE_CLIENT = "❔ Какие заказы хотите посмотреть?"

MSG_BACK = "🔄 Вы вернулись назад. "

MSG_ABOUT_TATTOO_MASTER = (
    "Привет! ‌Меня зовут Дара, и я верю, что наша встреча не случайна)\n\n"
    "✨‌ Я работаю в прекрасной студии в центре Москвы, делаю ч/б татуировки в стиле графика и абстракция.\n\n"
    "✨Люблю создавать тату, которые смотрятся естественно, дополняют образ и вписываются в анатомию тела."
    " Медицинское образование помогает мне в этом)\n\n"
    "✨‌ Я обожаю вкладывать особый смысл в татуировку, "
    "так что при создании эскизов часто обращаюсь к таро или алхимическим трактатам 🌿\n\n"
    "🌿 ЛС тут: @dara_redwan \n\n"
    "🌿 Инста тут: https://www.instagram.com/dara.redwan/\n\n "
    "🌿 Инструкции тут: https://taplink.cc/dara_redwan"
)

MSG_SCRETH_DEV = (
    "💬 Индивидуальный эскиз готовится заранее. "
    "За несколько дней до сеанса я вам его показываю, вы к нему привыкаете, "
    "мы согласовываем все детали, добавляем/убираем по вашему желанию.\n\n"
    "❕ Не стесняйтесь просить - тату должна вам нравится на все 100%.\n\n "
    "❕ При записи на сеанс разработка эскиза бесплатна. "
    "Если вы хотите только эскиз или «примерить» будущую тату с "
    "помощью переводной татуировки — можно сделать заказ эскиза по кнопке \"Эскиз\" в главном меню, или "
    "напишите мне, стоимость составит от 1000р до 3500р."
)

MSG_CONTRAINDICATIONS = (
    "💬 Постоянные\n"
    "— Нарушения свертываемости крови\n"
    "— Заболевания крови и кроветворных органов\n"
    "— Тяжелые вирусные заболевания (гепатит, ВИЧ, СПИД)\n"
    "— Онкологические заболевания\n"
    "— Системные аутоиммунные заболевания\n"
    "— Психические расстройства и эпилепсия\n"
    "— Склонность к образованию келлоидных рубцов\n"
    "— Заболевания, связанные со значительным снижением иммунитета\n"
    "— Инсулинзависимый сахарный диабет\n"
    "— Туберкулёз\n\n"
    "⏱ Временные\n"
    "— Простудные заболевания, кишечные инфекции и повышенная температура\n"
    "— Периоды обострения хронических очагов\n"
    "— Воспалительные и аллергические заболевания кожи\n"
    "— Для женщин — период беременности, кормления грудью\n"
    "— Алкогольное и наркотическое опьянение\n"
    "— Возраст до 18 лет (разрешено в присутствии родителя или по письменному согласию)"
)

MSG_PREPARING_TATTOO_ORDER = (
    "💬 Подготовка к сеансу состоит из следующих действий:\n"
    "— За пару дней до сеанса воздержитесь от алкогольных напитков\n"
    "— Выспитесь и покушайте перед сеансом, чтобы чувствать себя максимально комфортно\n"
    "— Возьмите с собой перекус и что-нибудь посмотреть/послушать, так сеанс пройдет легче\n"
    "— Наденьте удобную одежду однотонного цвета, чтобы во время финальной фотосессии "
    "яркий принт не перетягивал внимание на себя, или возьмите с собой что-то переодеться, "
    "при этом учтите место нанесения тату\n"
    "— За день до сеанса рекомендуется пройтись по месту нанесения мягкой мочалкой, "
    "а также удалить волосы, даже лёгкий пушок\n"
    "— За неделю до сеанса исключите из уходовой косметики крема и масла в зоне будущей татуировки"
)

MSG_COUPLE_TATTOO = (
    "💬 Эскиз для парной/тройной/четверной/и т.д."
    " тату согласовывается со всеми участниками процесса.\n\n"
    "Для этого создаётся отдельный чат в удобном мессенджере."
)

MSG_TATTOO_CARE = (
    "💬 В конце сеанса я заклею вашу татуировку заживляющей плёнкой, "
    "с которой вам нужно будет ходить 4 дня. На это время нужно исключить "
    "кардионагрузки и алкоголь. Менять плёнку или чем-то мазать не нужно.\n\n"
    "Чтобы безболезненно снять плёнку, необходимо аккуратно оттянуть её за уголок"
    "в сторону параллельно коже, без резких движений. Затем промойте кожу с мылом от остатков клея и пигмента.\n\n"
    "После снятия плёнки нужно смазывать тату увлажняющим кремом ещё 2 недели, "
    "делать это рекомендуется каждые 2−3 часа. Для этого подойдут: детский увлажняющий крем,"
    " специальный крем для заживления татуировок.\n\n"
    "❕❕❕ ВАЖНО: после снятия плёнки тату будет шелушиться, именно поэтому её нужно тщательно увлажнять."
    "Нельзя снимать чешуйки, убирать шелушение скрабами и тд, а так же чесать татуировку.\n\n"
    "Через 3−4 недели после сеанса кожа полностью обновляется, и тату считается зажившей.\n\n"
    "В период заживления нельзя посещать любые водоёмы и распаривать кожу 🙏"
)

MSG_RESTICTIONS_AFTER_THE_SESSION = (
    "— 3 дня после сеанса нельзя пить алкогольные напитки\n"
    "— 4−5 дней не заниматься спортом\n"
    "— 2−3 недели не распаривать кожу в ванне/бане/сауне. Мыться можно, но не долго, "
    "а вода не должна быть сильно горячей\n"
    "— 2−3 недели не использовать скрабы/не тереть тату мочалкой/не чесать/не ковырять — "
    "исключить любые механические воздействия.\n"
    "— 2−3 недели не купаться в любых водоёмах (бассейны/река/озеро/пруд/ и т.д.)"
)

MSG_ADMIN_SET_ANOTHER_PRICE = "💬 Укажите другую цену"

MSG_ADMIN_CAN_SET_ANOTHER_PRICE = (
    "Или вы можете вписать цену."
    " Для этого необходимо нажать кнопку "
    "\"Написать цену самому\""
)

MSG_ADMIN_SET_ANOTHER_PRICE_FROM_LINE = (
    f"{MSG_ADMIN_SET_ANOTHER_PRICE}. Необходимо указать цену без пробелов, только числа"
)

MSG_CORRECTION = (
    "💬 При заживлении всегда выходит какое-то количество пигмента, этого не нужно пугаться.\n"
    "В случае, если пигмента вышло слишком много, делается коррекция. \n"
    "В течение года с даты сеанса коррекция проводится бесплатно.\n\n"
    "💬 На заживление влияют:\n"
    "— соблюдение правил заживления, которые я описала выше\n"
    "— место нанесения\n"
    "— особенности кожи (сухость, рыхлость, пористость и тд)\n"
    "— состояние здоровья и особенности организма\n"
    "— прием лекарственных препаратов, алкогольных и наркотических средств\n"
    "— гормональный фон\n"
    "— техника нанесения татуировки"
)

# MSG_START_MEN
MSG_DO_CLIENT_WANT_TO_ADD_BODYPLACE = "❔ Хотите указать место, где будет располагаться тату?"

MSG_INFO_START_ORDER = (
    "💬 Диалог построен на том, что бот задает ряд вопросов, а вы отвечаете на них.\n"
    "💬 В ходе диалога с этим ботом необходимо отвечать на вопросы лишь в рамках ответов,"
    " которые предлагаются на "
    "нижней панели для кнопок. Все другие ответы не будут восприниматься ботом,"
    " или бот будет отвечать, что "
    "полученная информация для него не в рамках заданного вопроса."
)

MSG_INFO_SKETCH_ORDER = (
    "❕ Данный диалог дает вам возможность сделать заказ у Дары на эскиз для вашего будущего тату."
)

MSG_WHICH_USERNAME_IN_ORDER = (
    '💬 Введи телеграм пользователя (с символом "@") или ссылку с "https://t.me/".\n\n'
)

MSG_NOT_CORRECT_USER_PHONE = "❌ Номер некорректен, пожалуйста, введи номер заново"

MSG_ADD_USER_PHONE_TO_DB = "❔ Добавить телефон клиента?"

MSG_WHICH_USERNAME_PHONE_IN_ORDER = (
    '💬 Введи телефон клиента в формате: +7-000-000-00-00\n\n'
    '🤷🏻‍♂️ Или нажми на кнопку \"Я не знаю его телефона\"'
)

MSG_USER_WILL_BE_WITHOUT_PHONE = "Пользователь будет без телефона"

MSG_INFO_TATTOO_ORDER = (
    "❕ Данный диалог дает вам возможность сделать заказ у Дары на постоянное или переводное тату."
)

MSG_NO_USERS_IN_DB = "⭕️ Нет пользователей в таблице"

MSG_INFO_GIFTBOX_ORDER = (
    "❕ Данный диалог дает вам возможность сделать заказ у Дары на гифтбокс."
)

MSG_INFO_START_CERT_ORDER = (
    "❕ Данный диалог дает вам возможность заказать у Дары на сертификат"
)

MSG_START_CLIENT_TATTOO_ORDER = "🌿 Давай подберем уникальную татуировку!"

MSG_ADDRESS = (
    "Студия находится в творческом кластере «Vernissage by Flacon» "
    "на территории Измайловского Кремля \n\nИзмайловское шоссе, 73Ж, стр. 8.\n\n"
    "🖇 Ссылка на google.maps: "
    "https://www.google.com/maps?q="
    "%D0%98%D0%B7%D0%BC%D0%B0%D0%B9%D0%BB%D0%BE%D0%B2%D1%81%D0%BA%D0%"
    "BE%D0%B5+%D1%88%D0%BE%D1%81%D1%81%D0%B5,+73%D0%96,+%D1%81%D1%82%D1%8"
    "0.+8&rlz=1C1GCEU_enRU1025RU1025&um=1&ie=UTF-8&sa=X&ved=2ahUKEwjn_6_1yJ_"
    "9AhXxlosKHehVAbsQ_AUoAXoECAEQAw"
)

MSG_BANNED_CLIENT = (
    "❌ Уважаемый Клиент! Вы были забанены администратором.\n"
    "❗️ Вы не сможете делать заказы, пока вы находитесь в данном статусе. \n"
    "❗️ Ожидайте, пока администратор изменит ваш статус!"
)

MSG_COOPERATION = (
    "💬 Я открыта для сотрудничества, "
    "по всем вопросам пишите в личные сообщения в инстаграм или телеграм, "
    "ссылки все доступны по команде \"about_master\" "
    'или кнопка в главном меню "О тату мастере"🌿'
)

MSG_NO_DATE_IN_SCHEDULE = (
    "❌ К сожалению, но на этот месяц пока нет свободных дат\n"
    "💬 Не переживайте, позже я с вами свяжусь!"
)

MSG_WHICH_INFO_DO_CLIENT_WANT_TO_GET = "❔ Какую ещё информацию хотите получить?"

MSG_DO_CLIENT_WANT_TO_DO_MORE = "❔ Хотите сделать что-нибудь еще?"

MSG_DELETE_FUNCTION_NOTE = "❗️❗️❗️ Данная функция полностью удаляет запись из базы"

MSG_THANK_FOR_ORDER = (
    "🎉 Спасибо, что сделали заказ!\n💬 "
    "Я обязательно свяжусь с вами в ближайшее время!"
)

MSG_ADMIN_ADD_NEW_CORRECTION_EVENT_TO_CLIENT_TATTOO_ORDER = (
    "🎉 Отлично, теперь у клиента появилась запись на коррекцию!"
)

MSG_NO_CORRECTION_EVENTS = "⭕️ Пока у вас нет сеансов коррекции"

MSG_SUCCESS_CHANGING = "🎉 Изменение успешно!"

MSG_TATTOO_ORDER_CLIENT_CHOICE_BODY_LATER = (
    "➡️ Определим место для тату позже."
)

MSG_CLIENT_WANT_TO_FILL_ORDER_NOTE = (
    "❔ Хотите чего-нибудь добавить к описанию своего заказа?"
)

CLIENT_WANT_TO_CHANGE_MORE = (
    "❔ Хотите что-нибудь еще изменить в этом тату?\n\n"
    'Если ничего менять не хотите, необходимо нажать кнопку "Ничего не хочу менять ➡️" для продолжения'
)

MSG_NO_ORDER_IN_TABLE = "⭕️ Пока у вас нет заказов"

MSG_NO_CERT_TO_PAY = (
    "⭕️ У вас пока нет сертификатов для оплаты.\n\n"
    "❔ Не хотите ли оформить какой-нибудь заказ?"
)

MSG_WHICH_ORDER_DO_CLIENT_WANT_TO_PAY = "❔ Какие заказы хотите оплатить?"

MSG_WHICH_ORDER_DO_CLIENT_WANT_TO_SEE = "❔ Какой заказ хотите посмотреть?"

MSG_NO_TATTOO_IN_TABLE = "⭕️ У вас еще нет тату в таблице."

MSG_NO_SCHEDULE_IN_TABLE_IN_STATUS = (
    "⭕️ У вас еще нет сеансов в расписании в таблице в этом статусе."
)

MSG_NO_SCHEDULE_IN_TABLE = (
    "⭕️ У вас еще нет сеансов в расписании в таблице."
)

MSG_NO_SCHEDULE_PHOTO_IN_TABLE = (
    "⭕️ У вас еще нет фотографий расписания в таблице."
)

MSG_TO_GET_SCHEDULE = (
    "🗓 Мое расписание появилось выше.\n❕ Выберите дату из расписания, пожалуйста. "
)

MSG_HOW_TO_VIEW_THE_DATA = "❔ Как показать данные?"

MSG_TO_NO_SCHEDULE = (
    "⭕️ Пока свободных дат для тату в этом месяце нет, "
    "но мы можем обсудить дату для тату в следующем месяце уже лично.\n\n"
    'Нажмите кнопку "Далее ➡️"'
)

MSG_GET_TATTOO_NOTE_FROM_USER = (
    f"🌿 А теперь введите что-нибудь о своем тату!\n"
    "Чем подробнее описание тату, тем лучше!\n"
    "Здесь вы можете описать детали тату, расцветку и другие подробности.\n\n"
    f"➡️ Или нажмите \"Мне нечего добавить 🙅‍♂️\" для продолжения, "
    "если вам нечего на данный момент добавить по тату."
)

MSG_CLIENT_NO_DATE_IN_TATTOO_ORDER = (
    "💬 Уважаемый клиент %s! Ваше посещение тату салона по заказу №%s теперь имеет неопределенную дату. "
    'Дата %s на данный момент аннулирована администратором, заказ перешел в статус "Отложен".'
    "Не волнуйтесь, скоро будет новая дата для вашего заказа!\n\n"
    "По всем вопросам обращайтесь к https://t.me/dara_redwan"
)

MSG_CLIENT_HAVE_NEW_DATE_IN_TATTOO_ORDER = (
    '💬 "Уважаемый клиент %s! Ваше сеанс по заказу №%s теперь имеет другую дату и время!'
    "Дата поменялась с %s на %s, а время начала с %s на %s, "
    "а время окончания с %s на %s! Жду вас на сеансе!\n\n"
    "По всем вопросам обращайтесь к https://t.me/dara_redwan"
)

MSG_CLIENT_HAVE_NEW_DATE_IN_TATTOO_ORDER_WITH_NO_OLD_SCHEDULE = (
    '💬 "Уважаемый клиент %s! Ваш сеанс в заказе №%s теперь имеет новую дату! '
    "Теперь ваше посещение тату салона будет в %s до %s. "
    "Обязательно жду в назначенное время!\n\n"
    "Если по какой-либо причине вы не успевайте на сеанс в данное время, "
    'выберете кнопку "Перенести заказ" в меню "Мои заказы".\n\n'
    'Если вы хотите отменить заказ, перейдите в меню "Мои заказы" и выберите "Отменить заказ"\n\n'
    "По всем вопросам обращайтесь к https://t.me/dara_redwan"
)

MSG_CLIENT_HAVE_NEW_CORRECTION_DATE_IN_TATTOO_ORDER_WITH_NO_OLD_SCHEDULE = (
    '💬 "Уважаемый клиент %s! Ваш сеанс в заказе №%s теперь имеет новую дату коррекции! '
    "Теперь ваше посещение тату салона будет в %s до %s. "
    "Обязательно жду в назначенное время!\n\n"
    "Если по какой-либо причине вы не успевайте на сеанс в данное время, "
    'выберете кнопку "Перенести заказ" в меню "Мои заказы".\n\n'
    'Если вы хотите отменить заказ, перейдите в меню "Мои заказы" и выберите "Отменить заказ"\n\n'
    "По всем вопросам обращайтесь к https://t.me/dara_redwan"
)

MSG_WHICH_COMMAND_TO_EXECUTE = "❔ Какую команду выполнить?"

MSG_CHANGE_SCHEDULE_STATUS_ACTIONS_INFO = (
    "💬 При смене статуса календаря идет оповещение пользователя.\n"
    'Если статус календаря меняется с "Занят" на "Свободен", то, если у клиента есть заказ в этот день,'
    "администратор имеет три варианта изменения заказа: \n"
    "1) Поставить неизвестную дату в заказе (обнулить дату). "
    "После этого администратор получает возможность оповестить пользователя."
    "В этом случае, если админ выбирает оповещение, "
    "то Клиенту приходит уведомление следующего характера:\n"
    '"Уважаемый клиент <имя>! '
    "Ваше посещение тату салона по заказу <номер заказа> теперь имеет неопределенную дату. "
    "Дата <прошлая дата заказа> аннулирована администратором. "
    'Статус заказа обновился на "Отложен".'
    "Не волнуйтесь, скоро будет новая дата для вашего заказа!\n\n"
    "По всем вопросам обращайтесь к https://t.me/dara_redwan \n\n"
    "2) Поставить другую дату из календаря.\n"
    "3) Создать новую дату в календарь и выставить ее в данном заказе\n"
    "В 2 и 3 вариантах, если админ выбирает оповещение, к клиенту приходит следующее сообщение:"
    '"Уважаемый клиент <имя>! Ваше посещение тату салона по заказу <номер заказа> '
    "теперь имеет другую дату и время!"
    "Дата поменялась с <старая дата> на <новая дата>, а время с <старое время> на <новое время>!"
    "По всем вопросам обращайтесь к https://t.me/dara_redwan\n\n"
    'Если статус календаря меняется с "Свободен" на "Занят", то, администратору предлагается выбор:\n'
    "1) Добавить новый заказ в этот календарь\n"
    '2) Выбрать заказы из тех, которые имеют неизвестную дату - имеют статус "Отложен""\n'
    "3) Оставить данный календарь занятым, но без заказов\n"
    "В 1 и 2 случаях, если админ выбирает оповещение, клиент получаент следующее сообщение: \n"
    '"Уважаемый клиент <имя>! Ваш заказ <номер заказа> теперь имеет новую дату заказа! '
    "Теперь ваше посещение тату салона будет в <новое время> <новая дата>. "
    "Обязательно жду в назначенное время!\n\n"
    "Если по какой-либо причине вы не успевайте на заказ в данное время, "
    'выберете кнопку "Перенести заказ" в меню "Мои заказы".\n\n'
    'Если вы хотите отменить заказ, перейдите в меню "Мои заказы" и выберите "Отменить заказ"\n'
    "По всем вопросам обращайтесь к https://t.me/dara_redwan"
)

MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT = (
    "❔ Оповестить пользователя об изменении в расписании?"
)

MSG_DO_ADMIN_WANT_TO_NOTIFY_CLIENT_ABOUT_CHANGING_ORDER_STATE = (
    "❔ Оповестить пользователя о смене статуса заказа?"
)

MSG_PLS_SEND_TATTOO_PHOTO_OR_CANCEL_ACTION = (
    "📎 Пожалуйста, загрузите фотографию тату через файлы или отмените действие"
)

MSG_CLIENT_DO_WANT_ADD_ANOTHER_PHOTO_OR_VIDEO_BODY = (
    "❔ Добавить еще фотографию или видео?"
)

MSG_CLIENT_GO_BACK = "🔄 Вы вернулись назад\n\n"

MSG_MY_FREE_CALENDAR_DATES = "📅 Свободные даты в этом месяце:\n"

MSG_CLIENT_CHOICE_TATTOO_SIZE = "📏 Выбери примерный размер тату, пожалуйста."

MSG_WHICH_ORDER_COLUMN_NAME_WILL_CHANGING = "❔ Что изменить в заказе?"

MSG_CLIENT_CHOICE_TATTOO_NAME = (
    "❔ Напиши, какое имя было бы у твоего тату?\n\n"
    "❕ Имя тату должно быть коротким - не более 2-3 слов."
)

MSG_WHITH_ORDER_STATE_ADMIN_WANT_TO_SEE = (
    "❔ В каком статусе хотите посмотреть заказы?"
)

MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT = (
    "💬 Попробуем создать эскиз тату из твоего описания.\n\n"
)

MSG_GET_DESCRIPTION_TATTOO_FROM_ADMIN = (
    "💬 Попробуем создать изображение модели девушки из твоего описания.\n\n"
)

MSG_SEND_ORDER_STATE_INFO = (
    "💬 Бот поддерживает следующие статусы заказа:\n"
    "Открыт —  заказ был создан, он уже есть в базе данных, покупатель ожидает ответ.\n"
    "Обработан — заказ одобрен админом, заказ не оплачен\n"
    "Оплачен - заказ одобрен админом, и оплата была получена.\n"
    "Выполняется - заказ в стадии выполнения.\n"
    "Выполнен — вся работа по заказу завершена.\n"
    "Отклонен — заказ отклонен админом.\n"
    "Отложен — заказ ещё не обработан, так как в нём содержатся товары, которых нет в наличии."
    " Или ожидается информация о заказе со стороны клиента.\n"
    "Аннулирован — заказ был отменён покупателем.\n"
)

MSG_WHICH_TATTOO_WANT_TO_CHOOSE = "❔ Какое тату хотите выбрать?"

MSG_GET_DESCRIPTION_ABOUT_WORDS = "💬 В данной функции при генерации изображения из текста доступно '\
    'множество описательных слов"

MSG_START_INSTRUCTION_OF_GENERATING_AI_IMGS = (
    "💬 Для того, чтобы правильно сгенерировать изображение, "
    "необходимо сделать следующее:"
)

MSG_GET_DESCRIPTION_WOMAN_MODEL_FROM_ADMIN_CONCEPTS = (
    "Если не сильно углубляться, то стоит лишь написать те детали, которые хочешь увидеть на модели: часы, чокер, виснушки. Пример: woman with frills and a watch on her hand.\n\nЕсли хочешь добавить несколько разных элементов, то ставь запятую.\n\n Если хочешь больше разнообразия, то стоит делать это:\n1) Опиши основную концепцию модели женщины. Какая у нее грудь, живот, руки, позиция тела, куда смотрит ее лицо, какие у нее глаза, волосы, плечи, ноги. \n2) Для каждой детали опиши ее вид - большая, маленькая, тонкая, элегантная, стильная.\n3) Опиши цвет каждой важной детали\n\nВ данной функции при генерации изображения из текста доступно множество описательных слов. Подробнее о них ты можешь ознакомиться здесь: promptomania.com/stable-diffusion-prompt-builder !!! Важно: все слова должны быть на английском. Перевод слов с русского на английский я сделаю позже\n\n"
)

MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT_CONCEPTS = (
    "💬 Опиши свое тату очень детально: \n\n"
    "1) Опиши основную концепцию. Будет ли тату состоять из одной большой детали, "
    "или это будет какое-либо множество мелких деталей\n\n"
    "2) Для каждой детали опиши ее вид - большая, маленькая, круглая, квадратная\n\n"
    "3) Опиши цвет каждой важной детали, если тату будет цветной\n\n"
    'Ты можешь вдохновиться моими рисунками по кнопке \n"📃 Посмотреть галерею"'
)


MSG_GET_DESCRIPTION_TATTOO_FROM_CLIENT_CONCEPTS_MANY_FUNCTIONS = (
    "💬 В данной функции при генерации изображения из текста доступно множество описательных слов. \n"
    "Подробнее о них ты можешь ознакомиться здесь: "
    "https://promptomania.com/stable-diffusion-prompt-builder/"
)

# a) chromatic palettes\nb) monochomatic palettes\n'\'c) contrast\n d) motion picture process
MSG_STYLES_CHROMATIC_PALETTES = (
    "💬 Например, вот список цветового окружения, которое вы можете добавить в свой текст:\n\n"
    "chromatic palettes:\n - Warm Color palette\n - Cool\n - Colofur\n"
    "- Rainbow\n- Spectral\n- Inverted\n- Chroma\n- Dichromatism\n- Tetrachromacy\n- Saturated\n- Neon"
    "Electric\n- Tonal\n- Complimentary\n- Split-Complimentary-\n- Supplementary\n- Analogous\n- Triadic"
    "Tetradic\n- Polychromatic\n- Light\n- Dark\n- Light Mode\n- Dark Mode\n- Tones of Black"
    "Tones of Black in Background\n- Light Blue Background\n- Light Blue Foreground\n- Light Blue"
)

MSG_STYLES_MONOCHROMATIC_PALETTES = (
    "monochomatic palettes:\n -Monochrome\n- Black and White\n- Desaturated\n- Sepia"
)

MSG_STYLES_CONTRAST = "contrast:\n- High Contrast\n- Low Contrast"

MSG_MOTION_PICTURE_PROCESS = "motion picture process:\n- Technicolo\n- Kinemacolor\n- Kodachrome\n- Cinecolor\n- Agfacolor"

MSG_ADD_SYMBOLS_FOR_GETTING_STRONGER_WORD = (
    "💬 Ставь слова в скобки, если хочешь усилить или "
    "уменьшить мощность слова.\n\n"
    "Например:\n"
    " ● (word)- увеличить внимание в word 1,1 раза\n"
    " ● ((word))- увеличить внимание в word 1,21 раза (= 1,1 * 1,1)\n"
    " ● [word]- уменьшить внимание в word 1,1 раза\n"
    " ● (word:1.5)- увеличить внимание в word 1,5 раза\n"
    " ● (word:0.25)- уменьшить внимание в word 4 раза (= 1 / 0,25)\n"
)
MSG_TEXT_EXAMPLES_LINKS = (
    "💬 Вот некоторые сайты, которые помогут с примерами текста:\n\n"
    "● https://openart.ai/ - есть закладки, есть разделения по нейросетям, раздел с пресетами!"
    " ● https://prompthero.com/ - есть закладки, есть разделения по нейросетям\n"
    " ● https://lexica.art/ - есть закладки, только Stable Diffusion\n"
    " ● https://libraire.ai/ - промты\n"
    " ● https://promptbase.com/ - здесь уже даже продают промты(!), однако они"
    " постепенно появляются здесь: https://openart.ai/presets\n"
)

MSG_CLIENT_ALREADY_HAVE_OPEN_ORDER = (
    "💬 Уважаемый Клиент, у вас уже есть открытый заказ. "
    "Сделать новый заказ возможно только после подтверждения администратора и "
    "его завершении. "
    "После этого к вам придет сообщение от бота о том, что статус заказа изменился, "
    "а также даст возможность создать новый заказ.\n\n"
    '❕ Посмотреть заказ можно в меню "Мои заказы 📃"'
)


WOMAN_BOHO_STYLE_DESC = (
    "a long-range realistic photo of %s (open shoulders:1.6), (open belly:1.1), standing sideways, short haircut,"
    " (photorealistic pale skin:1.5), slim body, background is modern home in boho style, (high detailed skin:1.3), 8k uhd, "
    " natural soft lighting, high quality, film grain --steps 100 --H 512 --W 512"
    "  --scale 11.0 "
)

# <hypernetworkForProject_hypernetworkForProject:1.5><hypernet:dara_body_121_linear_normal_1-3200:1.0>

MSG_ANSWER_ABOUT_RESULT_TATTOO_FROM_AI = (
    "📷 Вот фотография.\n "
    "❔ Хотите попробовать еще? Или данное изображение вас устраивает?"
)

MSG_NOT_CORRECT_DATE_NOW_LESS_CHOICEN = (
    "❌ Выбранная дата стоит раньше нынешнего дня.\n\n"
)

MSG_LET_CHOICE_NORMAL_DATE = "⏱ Выберите подходящую дату"

MSG_FILL_TEXT_OR_CHOICE_VARIANT = (
    "💬 Введите текст для изображения или выбери вариант, пожалуйста."
)

MSG_ERROR_CHECK_VALIDATE_ADMIN_NAME = (
    "Кажется, вы отправили не тому человеку, "
    "т.к. имя получателя не совпадает.\n\n"
    "📎 Пожалуйста, отправьте сумму на указанный телефон. "
    "Там должно стоять имя \"Дария Редван Э\""
)

MSG_ERROR_CHECK_VALIDATE_ORDER_PRICE = (
    "Кажется, вы отправили чек не на ту сумму, "
    "т.к. сумма в этом чеке не совпадает.\n\n"
    "📎 Пожалуйста, отправьте чек на сумму %s"
)

MSG_ERROR_CHECK_VALIDATE_NOT_CORRECT_ADMIN_PHONE_NUMBER = (
    "Кажется, вы отправили чек не на тот мобильный номер, "
    "т.к. номер в этом чеке не совпадает с моим.\n\n"
    "📎 Пожалуйста, отправьте чек на сумму %s на номер телефона +7(925)885-07-87"
)

MSG_NO_CANDLE_IN_DB = "⭕️ Нет свечей в базе"

MSG_ADMIN_HAVE_TO_ADD_NEW_CANDLE_TO_GIFTBOX_ITEM = "❕ Необходимо добавить новую свечу в гифтбокс"

MSG_ERROR_CHECK_VALIDATE_NOT_CORRECT_CHECK_DOCUMENT = (
    "Кажется, это изображение очень похоже на чек, "
    "но чеком не является - нет необходимых полей для чека.\n\n"
    "📎 Пожалуйста, отправьте именно чек о переводе на сумму %s на номер телефона +7(925)885-07-87"
)

MSG_ADMIN_GET_CHECK_TO_ORDER = (
    "📎 Приложи чек, пожалуйста. Для этого надо в файлах отправить документ с чеком."
)

MSG_WHICH_TATTOO_SEND_TO_VIEW = f"❔ Какое тату показать?"

MSG_WHICH_ADMIN_ORDER_WANT_TO_SEE = "❔ Какой заказ посмотреть?"

MSG_WHICH_ADMIN_ORDER_WANT_TO_CHANGE = "❔ Какой заказ изменить?"

MSG_WHICH_ADMIN_ORDER_WANT_TO_DELETE = "❔ Какой заказ удалить?"

MSG_DO_CLIENT_WILL_GET_MSG_ABOUT_CHANGING_STATUS = "❔ Оповестить пользователя о смене статуса?"

MSG_CONTINUE_VIEW_GALERY_OR_GET_ORDER_FROM_GALERY = (
    '❔ Продолжить просмотр галерии? Или хотите выбрать для себя тату из галереи?'
)