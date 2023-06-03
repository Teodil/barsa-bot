import sqlite3
import sqlite3 as sql


def sql_start():
    global base, cur
    base = sqlite3.connect('barsaBD.db')
    cur = base.cursor()
    if (base):
        print("Data base connected")
    # base.execute('CREATE TABLE IF NOT EXISTS menu(img TEXT, name TEXT PRIMARY KEY, description TEXT, price float)')
    # base.commit()

def sql_close():
    #global base, cur
    #base = sqlite3.connect('barsaBD.db')
    #cur = base.cursor()
    if(base):
        base.close()
        print('Соеденение закрыто')
    #if (base):
    #    print("Data base connected")
    # base.execute('CREATE TABLE IF NOT EXISTS menu(img TEXT, name TEXT PRIMARY KEY, description TEXT, price float)')
    # base.commit()

# =========== Добавление объектов ==================


async def sql_add_product(data):
    sql_start()
    cur.execute('INSERT INTO Products(Photo,Name,Description,Price) VALUES(?,?,?,?)', [data['photo'],
                                                                                       data['name'],
                                                                                       data['description'],
                                                                                       data['price']])
    base.commit()
    sql_close()



async def sql_add_order(data):
    sql_start()
    cur.execute('INSERT INTO Orders(Product_id,Chat_id,ClientName) VALUES(?,?,?)', [data['productId'], data['chat_id'], data['clientName']])
    id = cur.lastrowid
    base.commit()
    sql_close()
    return id

# =======================Добавление пользователей==========================

async def sql_add_contact(username, chat_id):
    sql_start()
    cur.execute('INSERT into Contacts (Name,Chat_id) VALUES (?,?)', [username, chat_id])
    base.commit()
    sql_close()


async def sql_add_manager(username, chat_id):
    sql_start()
    cur.execute('INSERT into Managers (Name,Chat_id) VALUES (?,?)', [username, chat_id])
    base.commit()
    sql_close()


async def sql_add_worker(username, chat_id):
    sql_start()
    cur.execute('INSERT into Workers (Name,Chat_id) VALUES (?,?)', [username, chat_id])
    base.commit()
    sql_close()

async def sql_add_admin(username, chat_id):
    sql_start()
    cur.execute('INSERT into Admins (Name,Chat_id) VALUES (?,?)', [username, chat_id])
    base.commit()
    sql_close()


async def sql_add_to_ban_list(chat_id):
    sql_start()
    cur.execute('INSERT into BanList (Chat_id) VALUES (?)', [chat_id])
    base.commit()
    sql_close()

# ====================== Получение данных =============================
async def sql_get_admins():
    sql_start()
    data = cur.execute('SELECT Id,Name,Chat_id FROM ADMINS').fetchall()
    admins = []
    for item in data:
        admins.append({'Id': item[0], "Name": item[1], "Chat_id": item[2]})
    sql_close()
    return admins


async def sql_get_contacts():
    sql_start()
    data = cur.execute('SELECT Id,Name,Chat_id FROM CONTACTS').fetchall()
    contacts = []
    for item in data:
        contacts.append({'Id': item[0], "Name": item[1], "Chat_id": item[2]})
    sql_close()
    return contacts


async def sql_get_contact_by_id(chat_id):
    sql_start()
    data = cur.execute('SELECT Id,Name,Chat_id FROM CONTACTS WHERE Chat_id = ?', [chat_id]).fetchall()
    contact = None
    for item in data:
        contact = {'Id': item[0], "Name": item[1], "Chat_id": item[2]}
    sql_close()
    return contact

async def sql_get_workers():
    sql_start()
    data = cur.execute('SELECT Id,Name,Chat_id FROM WORKERS').fetchall()
    contacts = []
    for item in data:
        contacts.append({'Id': item[0], "Name": item[1], "Chat_id": item[2]})
    sql_close()
    return contacts

async def sql_get_managers():
    sql_start()
    data = cur.execute('SELECT Id,Name,Chat_id FROM Managers').fetchall()
    admins = []
    for item in data:
        admins.append({'Id': item[0], "Name": item[1], "Chat_id": item[2]})
    sql_close()
    return admins


async def sql_get_products():
    sql_start()
    data = cur.execute('SELECT * FROM PRODUCTS').fetchall()
    products = []
    for item in data:
        print(item)
        products.append({'Id': item[0], "Name": item[1], "Description": item[2], "Price": item[3], "Photo": item[4]})
    sql_close()
    return products


async def sql_get_ban_list():
    sql_start()
    data = cur.execute('select Id,Name,Chat_id from Contacts where Chat_id in (SELECT Chat_id from BanList)').fetchall()
    banList = []
    for item in data:
        print(item)
        banList.append({'Id': item[0], "Name": item[1], "Chat_id": item[2]})
    sql_close()
    return banList

async def sql_get_product_by_id(Id):
    sql_start()
    data = cur.execute('SELECT * FROM PRODUCTS WHERE ID = ?',[Id]).fetchall()
    product = None
    for item in data:
        print(item)
        product = {'Id': item[0], "Name": item[1], "Description": item[2], "Price": item[3], "Photo": item[4]}
    sql_close()
    return product



# ====================== Обновление данных ================================================
async def sql_update_product(data):
    sql_start()
    cur.execute('UPDATE Products SET Photo = ?, Name = ?,Description = ?,Price = ?  WHERE Id = ?', [data['photo'],
                                                                                                    data['name'],
                                                                                                    data['description'],
                                                                                                    data['price'],
                                                                                                    data['productId']])
    base.commit()
    sql_close()

# ===================== Удаление данных ====================================================
async def sql_delete_product(Id):
    sql_start()
    cur.execute('DELETE FROM PRODUCTS WHERE ID = ?', [Id])
    base.commit()
    sql_close()


async def sql_delete_from_ban_list(chat_id):
    sql_start()
    cur.execute('DELETE FROM BanList WHERE Chat_id = ?', [chat_id])
    base.commit()
    sql_close()


async def sql_delete_from_workers(chat_id):
    sql_start()
    cur.execute('DELETE FROM Workers WHERE Chat_id = ?', [chat_id])
    base.commit()
    sql_close()


async def sql_delete_from_managers(chat_id):
    sql_start()
    cur.execute('DELETE FROM Managers WHERE Chat_id = ?', [chat_id])
    base.commit()
    sql_close()


async def sql_delete_from_admins(chat_id):
    sql_start()
    cur.execute('DELETE FROM Admins WHERE Chat_id = ?', [chat_id])
    base.commit()
    sql_close()