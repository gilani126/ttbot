import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('marketplace.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц, если они еще не созданы
cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS subcategories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    );
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        subcategory_id INTEGER,
        status TEXT DEFAULT 'pending',
        FOREIGN KEY(subcategory_id) REFERENCES subcategories(id)
    );
''')

# Функции для работы с базой данных
def create_category(name):
    cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    conn.commit()

def delete_category(id):
    cursor.execute("DELETE FROM categories WHERE id = ?", (id,))
    conn.commit()

def create_subcategory(name, category_id):
    cursor.execute("INSERT INTO subcategories (name, category_id) VALUES (?, ?)", (name, category_id))
    conn.commit()

def delete_subcategory(id):
    cursor.execute("DELETE FROM subcategories WHERE id = ?", (id,))
    conn.commit()

def create_item(name, description, price, subcategory_id):
    cursor.execute("INSERT INTO items (name, description, price, subcategory_id) VALUES (?, ?, ?, ?)", 
                   (name, description, price, subcategory_id))
    conn.commit()

def delete_item(id):
    cursor.execute("DELETE FROM items WHERE id = ?", (id,))
    conn.commit()

def get_categories():
    return cursor.execute("SELECT * FROM categories").fetchall()

def get_subcategories(category_id):
    return cursor.execute("SELECT * FROM subcategories WHERE category_id = ?", (category_id,)).fetchall()

def get_items(subcategory_id):
    return cursor.execute("SELECT * FROM items WHERE subcategory_id = ?", (subcategory_id,)).fetchall()

def get_category_by_id(id):
    return cursor.execute("SELECT * FROM categories WHERE id = ?", (id,)).fetchone()

def get_subcategory_by_id(id):
    return cursor.execute("SELECT * FROM subcategories WHERE id = ?", (id,)).fetchone()

def get_item_by_id(id):
    return cursor.execute("SELECT * FROM items WHERE id = ?", (id,)).fetchone()

# Экспортируем cursor и conn, чтобы другие файлы могли ими пользоваться
__all__ = ['cursor', 'conn']
