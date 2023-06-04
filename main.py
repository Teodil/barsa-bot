

import asyncio
import logging
from asyncore import dispatcher

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command, callback_data, text
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from aiogram.fsm.storage.memory import MemoryStorage, MemoryStorageRecord

import sqllite_db

storage = MemoryStorage()
sqllite_db.sql_start()

# Bot token can be obtained via https://t.me/BotFather
TOKEN = "5946246038:AAH8gTJ-qnGIne8ihxmmp5X8eTjEp8IU_6w"

# All handlers should be attached to the Router (or Dispatcher)
router = Router()

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
menu = [
    [InlineKeyboardButton(text="💳 Товары", callback_data="menu"),
    InlineKeyboardButton(text="💰 Работа", callback_data="work")]#,
    #[InlineKeyboardButton(text="🔎 Связаться с техподдержкой", callback_data="chat")]
]

mainMenuForAdmin = [
    [InlineKeyboardButton(text="💳 Товары", callback_data="menu"),
    InlineKeyboardButton(text="💰 Работа", callback_data="work")],
    [InlineKeyboardButton(text="💳 Админка", callback_data="admin")]
    #[InlineKeyboardButton(text="🔎 Связаться с техподдержкой", callback_data="chat")]
]

menuAdmin = [
    [InlineKeyboardButton(text="Добавить товар", callback_data="addProduct"),
    InlineKeyboardButton(text="Список товаров", callback_data="menu")],
    #[InlineKeyboardButton(text="Заказы", callback_data="orders")],
    #[InlineKeyboardButton(text="Контакты", callback_data="contacts"),
    #InlineKeyboardButton(text="Менеджеры", callback_data="managers")]
]

menu = InlineKeyboardMarkup(inline_keyboard=menu)
menuForAdmin = InlineKeyboardMarkup(inline_keyboard=mainMenuForAdmin)
menuAdmin = InlineKeyboardMarkup(inline_keyboard=menuAdmin)
#exit_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="◀️ Выйти в меню")]], resize_keyboard=True)
#iexit_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Выйти в меню", callback_data="menu")]])
techGroupsIds = {
    "Orders": '-969494223',
    "Summary": '-981779049'
}

stikersObjects = {
    'NePovezlo': 'CAACAgIAAxkBAAIE42R6_Tj5x1J1quD7_EBXKWgPZaBoAAI9DAACYw8wSrSYEBTy63KjLwQ',
    'Povezlo': 'CAACAgIAAxkBAAIE5WR6_XTdg88MpPqwlecL9BOXneqTAALCCgACjmIwSrUl01DCl4aOLwQ'
}
'''
@router.message()
async def test(message: Message):
    print(message)
    #if(message.sticker):
    await bot.send_sticker(chat_id=message.chat.id,sticker='CAACAgIAAxkBAAIE3GR6_KL7gdPJ-kL3KnQiou5DIHiKAAJODAACIYswSsJu5MpDAAHYcS8E')
'''

async def check_is_in_ban_list(chat_id):
    print('is_in_ban_list action')
    if await is_in_ban_list(chat_id) == True:
        print('ЧС ветка')
        await bot.send_sticker(chat_id=chat_id,sticker=stikersObjects['NePovezlo'])
        await bot.send_message(chat_id=chat_id,text='Вы в чёрном списке')
        raise PermissionError('ЧС')

# =========================== Мидлваре КОНЕЦ ========================================

@router.message(Command(commands=["start"]))
async def command_start_handler(message: Message) -> None:
    await check_is_in_ban_list(message.chat.id)
    if not await is_in_contact(message.chat.id):
        await sqllite_db.sql_add_contact(message.from_user.username, message.chat.id)

    menuLocal = menu
    if await is_admin(message.chat.id):
        #print('test')
        menuLocal = menuForAdmin
    #print(menuLocal)
    await message.answer(f"Добро пожаловать в наш магазин. Здесь можно приобрести всякую всячину", reply_markup=menuLocal)


@router.message(Command(commands=["menu"]))
async def command_start_handler(message: Message) -> None:
    await check_is_in_ban_list(message.chat.id)

    if not await is_in_contact(message.chat.id):
        await sqllite_db.sql_add_contact(message.from_user.username, message.chat.id)

    menuLocal = menu
    if await is_admin(message.chat.id):
        menuLocal = menuForAdmin
    #print(menuLocal)
    await message.answer(f"======Меню=======", reply_markup=menuLocal)


# ===================== Админ Команды ================================

class FSMAdminCommands(StatesGroup):
    ban_user = State()
    unban_user = State()
    delete_worker = State()
    delete_manager = State()
    delete_admin = State()
    chat_all = State()

@router.message(Command(commands=["contacts"]))
async def command_start_handler(message: Message) -> None:
    if not await is_admin(message.chat.id) and not await is_manager(message.chat.id):
        return
    contacts = await sqllite_db.sql_get_contacts()
    for item in contacts:
        buttons = [[InlineKeyboardButton(text="Написать", callback_data=f"chat-{item['Chat_id']}")]]
        chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_message(chat_id=message.chat.id,
                               text=f"<b>UserName</b> @{item['Name']}\nChat_id: {item['Chat_id']}",
                               reply_markup=chatMenu)


@router.message(Command(commands=["chat-all"]))
async def command_chat_all_handler(message: Message, state=FSMContext) -> None:
    if not await is_admin(message.chat.id):
        return

    await state.set_state(FSMAdminCommands.chat_all)
    await message.reply('Отправленное ниже сообщение перешлёться всем контактам')


@router.message(FSMAdminCommands.chat_all)
async def command_chat_all_handler(message: Message, state=FSMContext) -> None:
    if not await is_admin(message.chat.id):
        return
    contacts = await sqllite_db.sql_get_contacts()
    for item in contacts:
        if (message.text):
            await bot.send_message(chat_id=item["Chat_id"], text=message.text)
        if message.photo:
            sendedPhotos = []
            for photoItem in message.photo:
                if photoItem.width > 100 or photoItem.height > 100:
                    continue
                if photoItem.file_unique_id not in sendedPhotos:
                    await bot.send_photo(chat_id=item["Chat_id"], photo=photoItem.file_id,
                                         caption=message.caption)
                    sendedPhotos.append(photoItem.file_unique_id)
        if message.location:
            await bot.send_location(chat_id=item["Chat_id"], longitude=message.location.longitude,
                                    latitude=message.location.latitude,
                                    horizontal_accuracy=message.location.horizontal_accuracy)
    await state.clear()
    await message.reply('Данное сообщение отправлено всем контактам')

@router.message(Command(commands=["workers"]))
async def command_start_handler(message: Message) -> None:

    if not await is_admin(message.chat.id) and not await is_manager(message.chat.id):
        return

    contacts = await sqllite_db.sql_get_workers()
    for item in contacts:
        buttons = [[InlineKeyboardButton(text="Написать", callback_data=f"chat-{item['Chat_id']}")],
                   [InlineKeyboardButton(text="Удалить", callback_data=f"delete-worker-{item['Chat_id']}")]]
        chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_message(chat_id=message.chat.id,
                               text=f"<b>UserName</b> @{item['Name']}\nChat_id: {item['Chat_id']}",
                               reply_markup=chatMenu)


@router.message(Command(commands=["admins"]))
async def command_start_handler(message: Message) -> None:

    if message.chat.id != 1134868684:
        return

    contacts = await sqllite_db.sql_get_admins()
    for item in contacts:
        buttons = [[InlineKeyboardButton(text="Написать", callback_data=f"chat-{item['Chat_id']}")],
                   [InlineKeyboardButton(text="Удалить", callback_data=f"delete-admin-{item['Chat_id']}")]]
        chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_message(chat_id=message.chat.id,
                               text=f"<b>UserName</b> @{item['Name']}\nChat_id: {item['Chat_id']}",
                               reply_markup=chatMenu)

@router.message(Command(commands=["managers"]))
async def command_start_handler(message: Message) -> None:
    if not await is_admin(message.chat.id):
        return

    contacts = await sqllite_db.sql_get_managers()
    for item in contacts:
        buttons = [[InlineKeyboardButton(text="Написать", callback_data=f"chat-{item['Chat_id']}")],
                   [InlineKeyboardButton(text="Удалить", callback_data=f"delete-manager-{item['Chat_id']}")]]
        chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_message(chat_id=message.chat.id,
                               text=f"<b>UserName</b> @{item['Name']}\nChat_id: {item['Chat_id']}",
                               reply_markup=chatMenu)


@router.message(Command(commands=["unban"]))
async def command_start_handler(message: Message, state=FSMContext):
    if not await is_admin(message.chat.id):
        return

    await state.set_state(FSMAdminCommands.unban_user)
    await message.reply('Введите chat_id пользователя которого хотите разбанить')

@router.message(Command(commands=["ban"]))
async def command_start_handler(message: Message, state=FSMContext):
    if not await is_admin(message.chat.id):
        return

    await state.set_state(FSMAdminCommands.ban_user)
    await message.reply('Введите chat_id пользователя которого хотите забанить')


@router.message(FSMAdminCommands.ban_user)
async def callback_query_add_to_ban_list(message: Message, state=FSMContext):
    if not await is_admin(message.chat.id):
        return
    contact = await sqllite_db.sql_get_contact_by_id(message.text)
    if not contact:
        await message.reply('Контакт с таким chat_id не найден')
        await state.clear()
        return
    if await is_in_ban_list(message.chat.id):
        await message.reply('Контакт с таким chat_id уже в бане')
        await state.clear()
        return

    await sqllite_db.sql_add_to_ban_list(contact['Chat_id'])
    await state.clear()
    await message.reply(f"Пользователь {contact['Name']} Chat_id {contact['Chat_id']} добавлен в ЧС")


@router.message(FSMAdminCommands.unban_user)
async def callback_query_add_to_ban_list(message: Message, state=FSMContext):
    if not await is_admin(message.chat.id):
        return
    contact = await sqllite_db.sql_get_contact_by_id(message.text)
    if not contact:
        await message.reply('Контакт с таким chat_id не найден')
        await state.clear()
        return
    if await is_in_ban_list(message.chat.id) == True:
        await message.reply('Контакт с таким chat_id не в ЧС')
        await state.clear()
        return

    await sqllite_db.sql_delete_from_ban_list(contact['Chat_id'])
    await state.clear()
    await message.reply(f"Пользователь {contact['Name']} Chat_id {contact['Chat_id']} удалён из ЧС")

@router.message(Command(commands=["banlist"]))
async def command_start_handler(message: Message) -> None:
    if not await is_admin(message.chat.id):
        return

    contacts = await sqllite_db.sql_get_ban_list()
    for item in contacts:
        buttons = [[InlineKeyboardButton(text="Разбанить", callback_data=f"unban-{item['Chat_id']}")]]
        chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_message(chat_id=message.chat.id,
                               text=f"<b>UserName</b> @{item['Name']}\n {item['Chat_id']}",
                               reply_markup=chatMenu)


@router.callback_query(F.data[0:6] == "unban-")
async def callback_unban_user(callback_query: types.CallbackQuery, state=None):
    if not is_admin(callback_query.message.chat.id):
        return
    unban_user_id = callback_query.data.replace('unban-','')
    if not await is_in_ban_list(unban_user_id):
        await bot.send_message(callback_query.message.chat.id, 'Пользователь не в чёрном списке')
        return

    await sqllite_db.sql_delete_from_ban_list(unban_user_id)
    await bot.send_message(callback_query.message.chat.id, f'Пользователь {unban_user_id} разбанен')


@router.callback_query(F.data[0:14] == "delete-worker-")
async def callback_unban_user(callback_query: types.CallbackQuery, state=None):
    if not await is_admin(callback_query.message.chat.id) and not await is_manager(callback_query.message.chat.id):
        return
    worker_id = callback_query.data.replace('delete-worker-','')
    if not await is_worker(worker_id):
        await bot.send_message(callback_query.message.chat.id, 'Пользователь не является сотрудником')
        return

    await sqllite_db.sql_delete_from_workers(worker_id)
    await bot.send_message(callback_query.message.chat.id, f'Пользователь {worker_id} удалён из сотрудников')


@router.callback_query(F.data[0:15] == "delete-manager-")
async def callback_unban_user(callback_query: types.CallbackQuery, state=None):
    if not await is_admin(callback_query.message.chat.id):
        return
    manager_id = callback_query.data.replace('delete-manager-','')
    if not await is_manager(manager_id):
        await bot.send_message(callback_query.message.chat.id, 'Пользователь не является менеджером')
        return

    await sqllite_db.sql_delete_from_managers(manager_id)
    await bot.send_message(callback_query.message.chat.id, f'Пользователь {manager_id} удалён из менеджеров')


@router.callback_query(F.data[0:13] == "delete-admin-")
async def callback_unban_user(callback_query: types.CallbackQuery, state=None):
    print('delete-admin')
    if not await is_admin(callback_query.message.chat.id):
        return
    admin_id = callback_query.data.replace('delete-admin-','')
    if not await is_admin(admin_id):
        await bot.send_message(callback_query.message.chat.id, 'Пользователь не является админом')
        return

    await sqllite_db.sql_delete_from_admins(admin_id)
    await bot.send_message(callback_query.message.chat.id, f'Пользователь {admin_id} удалён из админов')


# ================ Технические функции =======================
async def is_admin(chat_id):
    isAdmin = False
    admins = await sqllite_db.sql_get_admins()
    for item in admins:
        if item['Chat_id'] == str(chat_id):
            isAdmin = True
    return isAdmin


async def is_in_contact(chat_id):
    isContact = False
    contacts = await sqllite_db.sql_get_contacts()
    for item in contacts:
        if item['Chat_id'] == str(chat_id):
            isContact = True
    print(isContact)
    return isContact


async def is_manager(chat_id):
    isManager = False
    managers = await sqllite_db.sql_get_managers()
    for item in managers:
        if item['Chat_id'] == str(chat_id):
            isManager = True
    return isManager


async def is_worker(chat_id):
    isWorker = False
    workers = await sqllite_db.sql_get_workers()
    for item in workers:
        if item['Chat_id'] == str(chat_id):
            isWorker = True
    return isWorker


async def is_in_ban_list(chat_id):
    isInBanList = False
    baned = await sqllite_db.sql_get_ban_list()
    for item in baned:
        print(item)
        if item['Chat_id'] == str(chat_id):
            isInBanList = True
    print(isInBanList)
    return isInBanList


@router.message(Command(commands=["stop"]))
async def stop_action(message: Message, state=FSMContext):
    await state.clear()
    await message.reply(text="Операция отменена")

@router.message(Command(commands=["chat_id"]))
async def stop_action(message: Message, state=FSMContext):
    await bot.send_message(chat_id=message.chat.id, text = message.chat.id)


# ================================Админ панель==============================================
@router.callback_query(F.data == "admin")
async def callback_query_admin(callback_query: types.CallbackQuery, state=None):
    if not await is_admin(callback_query.message.chat.id):
        return
    await bot.send_message(chat_id=callback_query.message.chat.id, text=f"Админское меню",reply_markup=menuAdmin)

class FSMAddProduct(StatesGroup):
    photo_add = State()
    name_add = State()
    description_add = State()
    price_add = State()
    delete_product = State()

@router.callback_query(F.data == "addProduct")
async def callback_query_add_product(callback_query: types.CallbackQuery, state=FSMContext):
    if not await is_admin(callback_query.message.chat.id):
        return
    await state.update_data(actionType='Add')
    await state.set_state(FSMAddProduct.photo_add)
    await bot.send_message(chat_id=callback_query.message.chat.id, text='Загрузи фото. Для отмены операции введи /stop')


@router.message(FSMAddProduct.photo_add)
async def callback_query_add_product_photo(message: Message, state=FSMContext):
    #print('test1')
    if not await is_admin(message.chat.id):
        return
    if(message.photo == None or len(message.photo) == 0):
        await message.reply(text="Вы не загрузили фото. Давай ещё разок")
        return
    #print('test2')
    await state.update_data(photo=message.photo[0].file_id)
    #print('test3')
    #print(message.chat.id)
    await message.reply(text='Теперь введи название')
    #print('test4')
    await state.set_state(FSMAddProduct.name_add)


@router.message(FSMAddProduct.name_add)
async def callback_query_add_product_photo(message: Message, state=FSMContext):
    print('test5')
    if not await is_admin(message.chat.id):
        return
    print('test6')
    await state.update_data(name=message.text)
    await message.reply(text='Теперь введи описание')
    await state.set_state(FSMAddProduct.description_add)


@router.message(FSMAddProduct.description_add)
async def callback_query_add_product_photo(message: Message, state=FSMContext):
    if not await is_admin(message.chat.id):
        return
    await state.update_data(description=message.text)
    await message.reply(text='Теперь введи цену')
    await state.set_state(FSMAddProduct.price_add)


@router.message(FSMAddProduct.price_add)
async def callback_query_add_product_photo(message: Message, state=FSMContext):
    if not await is_admin(message.chat.id):
        return
    data = await state.update_data(price=message.text)
    if data['actionType'] == 'Add':
        await sqllite_db.sql_add_product(data)
    if data['actionType'] == 'Edit':
        await sqllite_db.sql_update_product(data)
    await message.reply(text='Данные загружены')
    await state.clear()

@router.callback_query(F.data[0:13] == "product-edit-")
async def callback_query_edit_product(callback_query: types.CallbackQuery, state=FSMContext):
    if not await is_admin(callback_query.message.chat.id):
        return
    await state.update_data(actionType='Edit')
    await state.update_data(productId= callback_query.data.replace('product-edit-', ''))
    await state.set_state(FSMAddProduct.photo_add)
    await bot.send_message(chat_id=callback_query.message.chat.id, text='Загрузи фото. Для отмены операции введи /stop')


@router.callback_query(F.data[0:15] == "product-delete-")
async def callback_query_delete_product(callback_query: types.CallbackQuery, state=FSMContext):
    if not await is_admin(callback_query.message.chat.id):
        return
    await state.update_data(productId = callback_query.data.replace('product-delete-', ''))
    await state.set_state(FSMAddProduct.delete_product)
    await bot.send_message(chat_id=callback_query.message.chat.id, text='Для потверждения удалаения введите "да". Остальные вводы отменят удаление')


@router.message(FSMAddProduct.delete_product)
async def callback_query_add_product_photo(message: Message, state=FSMContext):
    if not await is_admin(message.chat.id):
        return
    if(message.text != "да"):
        await state.clear()
        await message.reply("Удаление отменено")
        return
    data = await state.get_data()
    await sqllite_db.sql_delete_product(data["productId"])
    await message.reply("Товар удалён")

@router.callback_query(F.data[0:15] == "product-delete-")
async def callback_query_delete_product(callback_query: types.CallbackQuery, state=FSMContext):
    if not await is_admin(callback_query.message.chat.id):
        return
    await state.update_data(productId= callback_query.data.replace('product-delete-', ''))
    await state.set_state(FSMAddProduct.delete_product)
    await bot.send_message(chat_id=callback_query.message.chat.id, text='Для потверждения удалаения введите "да". Остальные вводы отменят удаление')




#=================================Главное меню==============================================
@router.callback_query(F.data == "menu")
async def callback_query_menu(callback_query: types.CallbackQuery, state=None):
    await check_is_in_ban_list(callback_query.message.chat.id)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="========Товары========")
    products = await sqllite_db.sql_get_products()

    for product in products:
        text = ""
        text += f"<b>Товар</b>: {product['Name']}\n"
        text += f"<b>Описание</b>: {product['Description']}\n"
        text += f"<b>Цена</b>: {product['Price']}\n"
        buttons = [[InlineKeyboardButton(text="💳 Купить", callback_data=f"buy-{product['Id']}")]]
        if await is_admin(callback_query.message.chat.id):
            buttons.append([InlineKeyboardButton(text="Редактировать", callback_data=f"product-edit-{product['Id']}")])
            buttons.append([InlineKeyboardButton(text="Удалить", callback_data=f"product-delete-{product['Id']}")])
        buyMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
        if product['Photo'] is not None:
            await bot.send_photo(chat_id=callback_query.message.chat.id, photo=product['Photo'], caption=text,
                                 reply_markup=buyMenu)
        else:
            await bot.send_message(chat_id=callback_query.message.chat.id, text=text, reply_markup=buyMenu)

@router.callback_query(F.data == "chat")
async def callback_query_chat(callback_query: types.CallbackQuery, state=None):
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Хуй соси2")


@router.callback_query(F.data[0:4] == "buy-")
async def callback_query_buy(callback_query: types.CallbackQuery, state=None):
    await check_is_in_ban_list(callback_query.message.chat.id)
    data = {"productId": callback_query.data.replace('buy-', ''),
            "chat_id": callback_query.message.chat.id,
            "clientName": callback_query.from_user.username}
    productData = await sqllite_db.sql_get_product_by_id(callback_query.data.replace('buy-',''))
    orderId = await sqllite_db.sql_add_order(data)
    orderText = ""
    orderText += f"<b>Заказ №{orderId}</b>\n"
    orderText += f"<b>Товар {productData['Name']}</b>\n"
    orderText += f"<b>UserName @{callback_query.message.chat.username}</b>\n"
    orderText += f"<b>Chat_id {callback_query.message.chat.id}</b>\n"
    buttons = [[InlineKeyboardButton(text="Написать клиенту", callback_data=f"order-chat-{callback_query.message.chat.id}")]]
    orderChat = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id=techGroupsIds["Orders"], text=orderText,reply_markup=orderChat)
    await bot.send_message(chat_id=callback_query.message.chat.id, text=f"Ваш Заказ №{orderId}\nЗаказ отправлен менеджеру\nСкоро с вами свяжутся для уточнения деталей!")

#=================================================Устройство на работу=========================================================


class FSMWork(StatesGroup):
    name = State()
    description = State()
    chat_id = State()
    add_admin = State()
    add_worker = State()
    add_manager = State()

@router.callback_query(F.data == "work")
async def callback_query_work(callback_query: types.CallbackQuery, state=FSMContext):
    await check_is_in_ban_list(callback_query.message.chat.id)
    await state.set_state(FSMWork.description)
    await bot.send_message(callback_query.message.chat.id,"Распишите о себе\nПочему хотите у нас работать и почему мы должны выбрать вас")

@router.message(FSMWork.description)
async def load_work_description(message: Message,state: FSMContext):
    await state.update_data(name = message.from_user.username)
    await state.update_data(description = message.text)
    data = await state.update_data(chat_id= message.chat.id)
    await bot.send_message(chat_id=techGroupsIds['Summary'], text="Новое рюзиме")
    buttons = [[InlineKeyboardButton(text="Написать", callback_data=f"summary-chat-{data['chat_id']}")],
               [InlineKeyboardButton(text="Сделать работником", callback_data=f"add-worker-{data['chat_id']}|{data['name']}")],
               [InlineKeyboardButton(text="Сделать менеджером", callback_data=f"add-manager-{data['chat_id']}|{data['name']}")],
               [InlineKeyboardButton(text="Сделать админом", callback_data=f"add-admin-{data['chat_id']}|{data['name']}")]]
    chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id=techGroupsIds['Summary'], text=f"<b>UserName</b> @{data['name']}\n {data['description']}\nChat_id = {data['chat_id']}",reply_markup=chatMenu)
    await bot.send_message(chat_id=message.chat.id, text="Ваше рюзиме отправленно менеджеру")
    await state.clear()


@router.callback_query(F.data[0:11] == "add-worker-")
async def callback_query_work(callback_query: types.CallbackQuery, state=FSMContext):
    if await is_admin(callback_query.from_user.id) == False and await is_admin(callback_query.from_user.id) == False:
        await bot.send_message(chat_id=callback_query.message.chat.id,
                               text=f"У пользователя {callback_query.from_user.username} нет прав на создание сотрудника")
        return
    chat_id, name = callback_query.data.replace('add-worker-', '').split('|')
    await state.set_state(FSMWork.add_worker)
    await state.update_data(name=name)
    await state.update_data(chat_id=chat_id)
    await bot.send_message(callback_query.message.chat.id,
                           f'Дать @{name} {chat_id} роль сотрудника\nПользователем {callback_query.from_user.username}\n Для потверждения создание введите "да". Остальные вводы <b>отменят</b> создание сотрудника')


@router.callback_query(F.data[0:12] == "add-manager-")
async def callback_query_work(callback_query: types.CallbackQuery, state=FSMContext):
    if await is_admin(callback_query.from_user.id) == False:
        await bot.send_message(chat_id=callback_query.message.chat.id,
                               text=f"У пользователя {callback_query.from_user.username} нет прав на создание менеджера")
        return
    chat_id, name = callback_query.data.replace('add-manager-','').split('|')
    await state.set_state(FSMWork.add_manager)
    await state.update_data(name=name)
    await state.update_data(chat_id=chat_id)
    await bot.send_message(callback_query.message.chat.id,
                           f'Дать @{name} {chat_id} роль менеджера\nПользователем {callback_query.from_user.username}\n Для потверждения создание введите "да". Остальные вводы <b>отменят</b> создание менеджера')


@router.callback_query(F.data[0:10] == "add-admin-")
async def callback_query_work(callback_query: types.CallbackQuery, state=FSMContext):
    if await is_admin(callback_query.from_user.id) == False:
        await bot.send_message(chat_id=callback_query.message.chat.id,
                               text=f"У пользователя {callback_query.from_user.username} нет прав на создание админа")
        return
    chat_id, name = callback_query.data.replace('add-admin-', '').split('|')
    await state.set_state(FSMWork.add_admin)
    await state.update_data(name=name)
    await state.update_data(chat_id=chat_id)
    await bot.send_message(callback_query.message.chat.id,
                           f'Дать @{name} {chat_id} роль админа\nПользователем {callback_query.from_user.username}\n Для потверждения создание введите "да". Остальные вводы <b>отменят</b> создание админа')


@router.message(FSMWork.add_admin)
async def add_spec_user_handler(message: Message, state: FSMContext):
    print('test')
    stateValue = await state.get_state()
    if(message.text == 'да'):
        data = await state.get_data()
        if await is_admin(data['chat_id']) == False:
            await sqllite_db.sql_add_admin(data['name'],data['chat_id'])
            await message.reply(f"Пользователь {data['name']} теперь админ")
            await state.clear()
        else:
            await message.reply(f"Пользователь {data['name']} уже является админом")
    else:
        await state.clear()
        await bot.send_message(chat_id=message.chat.id,text=f'Операция пользователя {message.from_user.username} отменена')

@router.message(FSMWork.add_manager)
async def add_spec_user_handler(message: Message, state: FSMContext):
    print('test')
    stateValue = await state.get_state()
    if(message.text == 'да'):
        data = await state.get_data()
        if await is_manager(data['chat_id']) == False:
            await sqllite_db.sql_add_manager(data['name'], data['chat_id'])
            await message.reply(f"Пользователь {data['name']} теперь менеджер")
            await state.clear()
        else:
            await message.reply(f"Пользователь {data['name']} уже является менеджером")
    else:
        await state.clear()
        await bot.send_message(chat_id=message.chat.id,text=f'Операция пользователя {message.from_user.username} отменена')


@router.message(FSMWork.add_worker)
async def add_spec_user_handler(message: Message, state: FSMContext):
    print('test')
    stateValue = await state.get_state()
    if(message.text == 'да'):
        data = await state.get_data()
        if await is_worker(data['chat_id']) == False:
            await sqllite_db.sql_add_worker(data['name'], data['chat_id'])
            await message.reply(f"Пользователь {data['name']} теперь сотрудник")
            await state.clear()
        else:
            await message.reply(f"Пользователь {data['name']} уже является сотрудником")
    else:
        await state.clear()
        await bot.send_message(chat_id=message.chat.id,text=f'Операция пользователя {message.from_user.username} отменена')


##==========================================Чат между менеджером и клиентом============================================================
class FSMChat(StatesGroup):
    chat_id_client = State()
    chat_id_manager = State()

# Начало чата по рюзиме
@router.callback_query(F.data[0:13] == 'summary-chat-')
async def manager_start_chat(callback_query: types.CallbackQuery, state=FSMContext):
    print('summary-chat- action')
    if await is_admin(callback_query.from_user.id) == False and await is_manager(callback_query.from_user.id) == False:
        await bot.send_message(chat_id=callback_query.message.chat.id,
                               text=f"У пользователя {callback_query.from_user.username} нет прав на начало чата")
        return

    await state.update_data(chat_id_client=callback_query.data.replace('summary-chat-',''))
    buttons = [
        [InlineKeyboardButton(text="Написать", callback_data=f"chat-{callback_query.data.replace('summary-chat-', '')}")]]
    chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id=callback_query.from_user.id, text='Начать диалог по резюме', reply_markup=chatMenu)

@router.callback_query(F.data[0:5] == "chat-")
async def manager_start_chat(callback_query: types.CallbackQuery, state=FSMContext):
    await check_is_in_ban_list(callback_query.message.chat.id)
    await state.set_state(FSMChat.chat_id_manager)
    print('chat action')
    print(callback_query.data)
    print(callback_query.data[0:5])
    await state.update_data(chat_id_client=callback_query.data.replace('chat-',''))
    print('test')
    await bot.send_message(callback_query.from_user.id, text=f"Начат чат с пользователём {callback_query.data.replace('chat-','')}")
    print('test')
    await bot.send_message(callback_query.from_user.id, text=f"Всё что вы напишите ниже будет отправленно данному пользователю\n Для отмены чата напишите /stopChat")

#Хэндлер начала разговора клиента с менеджером
@router.callback_query(F.data[0:12] == "client-chat-")
async def manager_start_chat(callback_query: types.CallbackQuery, state=FSMContext):
    await check_is_in_ban_list(callback_query.message.chat.id)
    print('client-chat- action ')
    await state.set_state(FSMChat.chat_id_client)
    await state.update_data(chat_id_manager=callback_query.data.replace('client-chat-',''))
    await bot.send_message(callback_query.message.chat.id, text=f"Начат чат с менеджером")
    await bot.send_message(callback_query.message.chat.id, text=f"Всё что вы напишите ниже будет отправленно менеджеру\n Для отмены чата напишите /stopChat")


@router.message(Command(commands=["stopChat"]))
async def manager_chat_handler(message: Message,state: FSMContext):
    #await bot.send_message(message.chat.id,text=f"test")
    stateLocal = await state.get_state()
    #await bot.send_message(message.chat.id,text=stateLocal)
    if(stateLocal == FSMChat.chat_id_manager):
        data = await state.get_data()
        await bot.send_message(message.chat.id,text=f"Отправка сообщений пользователю {data['chat_id_client']} прекращена")
        await state.clear()
    elif (stateLocal == FSMChat.chat_id_client):
        await bot.send_message(message.chat.id, text=f"Отправка сообщений менеджеру прекращена")
        await state.clear()


@router.message(FSMChat.chat_id_manager)
async def manager_chat_handler(message: Message,state: FSMContext):
    data = await state.get_data()
    buttons = [[InlineKeyboardButton(text="Ответить", callback_data=f"client-chat-{message.chat.id}")]]
    print('FSMChat.chat_id_manager')
    print(data)
    chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
    if(message.text):
        await bot.send_message(chat_id=data["chat_id_client"], text=f'Сообщение от менеджера:\n{message.text}', reply_markup=chatMenu)
    if message.photo:
        sendedPhotos = []
        for photoItem in message.photo:
            if photoItem.width > 100 or photoItem.height > 100:
                continue
            if photoItem.file_unique_id not in sendedPhotos:
                await bot.send_photo(chat_id=data["chat_id_client"], photo=photoItem.file_id, caption=message.caption)
                sendedPhotos.append(photoItem.file_unique_id)
    if message.location:
        await bot.send_location(chat_id=data["chat_id_client"],longitude=message.location.longitude,latitude=message.location.latitude,
                                horizontal_accuracy=message.location.horizontal_accuracy)


@router.message(FSMChat.chat_id_client)
async def client_chat_handler(message: Message,state: FSMContext):
    data = await state.get_data()
    buttons = [[InlineKeyboardButton(text="Ответить", callback_data=f"chat-{message.chat.id}")]]
    chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
    print('FSMChat.chat_id_client')
    print(data)
    #await bot.send_message(chat_id=data["chat_id_client"], text=str(message.photo), reply_markup=chatMenu)
    contact = await sqllite_db.sql_get_contact_by_id(chat_id=message.chat.id)
    if(message.text):
        await bot.send_message(chat_id=data["chat_id_manager"],text=f"Сообщение от @{contact['Name']} chat_id: {message.chat.id}:\n{message.text}", reply_markup=chatMenu)
    if message.photo:
        sendedPhotos = []

        for photoItem in message.photo:
            if photoItem.width > 100 or photoItem.height > 100:
                continue
            if photoItem.file_id not in sendedPhotos:
                await bot.send_photo(chat_id=data["chat_id_manager"], photo=photoItem.file_id, caption=message.caption)
                sendedPhotos.append(photoItem.file_id)
    if message.location:
        await bot.send_location(chat_id=data["chat_id_manager"],longitude=message.location.longitude,latitude=message.location.latitude,
                                horizontal_accuracy=message.location.horizontal_accuracy)

@router.callback_query(F.data[0:11] == 'order-chat-')
async def client_chat_order_handler(callback_query: types.CallbackQuery, state=FSMContext):
    print('order-chat action')
    if await is_admin(callback_query.from_user.id) == False and await is_manager(callback_query.from_user.id) == False:
        await bot.send_message(chat_id=callback_query.message.chat.id,
                               text=f"У пользователя {callback_query.from_user.username} нет прав на начало чата")
        return

    buttons = [[InlineKeyboardButton(text="Написать", callback_data=f"chat-{callback_query.data.replace('order-chat-','')}")]]
    chatMenu = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id=callback_query.from_user.id, text='Начать диалог по заказу',reply_markup=chatMenu)

##==========================================Чат между менеджером и клиентом КОНЕЦ============================================================



async def main() -> None:
    # Dispatcher is a root router
    dp = Dispatcher(storage=storage)
    #router.message.middleware(BigBrother)
    # ... and all other routers should be attached to Dispatcher
    dp.include_router(router)
    global bot
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode="HTML")
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())