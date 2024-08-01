import sqlite3


def create_database():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        brand TEXT NOT NULL,
        price REAL NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quotation_counter (
        id INTEGER PRIMARY KEY,
        counter INTEGER
    )
    ''')

    cursor.execute(
        'INSERT OR IGNORE INTO quotation_counter (id, counter) VALUES (1, 0)')

    conn.commit()
    conn.close()
