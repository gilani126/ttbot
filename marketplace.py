import sqlite3
conn = sqlite3.connect('marketplace.db')
cursor = conn.cursor()

class DatabaseManager:
    def __init__(self, db_name='marketplace.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS subcategories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER,
                FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
            );
        ''')
        self.conn.commit()

    def close(self):
        self.conn.close()

class Category:
    def __init__(self, db):
        self.db = db

    def create(self, name):
        self.db.cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        self.db.conn.commit()

    def delete(self, category_id):
        self.db.cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        self.db.conn.commit()

    def rename(self, category_id, new_name):
        self.db.cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
        self.db.conn.commit()

    def get_all(self):
        return self.db.cursor.execute("SELECT * FROM categories").fetchall()

class Subcategory:
    def __init__(self, db):
        self.db = db

    def create(self, name, category_id):
        self.db.cursor.execute("INSERT INTO subcategories (name, category_id) VALUES (?, ?)", (name, category_id))
        self.db.conn.commit()

    def delete(self, subcategory_id):
        self.db.cursor.execute("DELETE FROM subcategories WHERE id = ?", (subcategory_id,))
        self.db.conn.commit()

    def rename(self, subcategory_id, new_name):
        self.db.cursor.execute("UPDATE subcategories SET name = ? WHERE id = ?", (new_name, subcategory_id))
        self.db.conn.commit()

# Использование
db_manager = DatabaseManager()
category = Category(db_manager)
subcategory = Subcategory(db_manager)

category.create("Movies")
subcategory.create("Action", 1)
category.rename(1, "Films")
print(category.get_all())
db_manager.close()
