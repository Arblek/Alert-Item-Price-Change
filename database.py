import sqlite3

def get_connection(db_name: str) -> sqlite3.Connection:
    try:
        return sqlite3.connect(db_name)
    except Exception as e:
        print(f"Error: {e}")


def create_table(connection: sqlite3.Connection):
    query = """
            CREATE TABLE IF NOT EXISTS products_data(
                id INTEGER PRIMARY KEY,
                sku TEXT,
                title TEXT,
                price REAL,
                stock INTEGER
            )
    """

    try:
        with connection:
            connection.execute(query)
        print("Table was created")
    except Exception as e:
        print(f"Error: {e}")


def insert_product(connection: sqlite3.Connection, sku: str, title: str, price: float):
    query = """
            INSERT INTO products_data (sku, title, price) VALUES (?, ?, ?)
    """

    try:
        with connection:
            connection.execute(query, (sku, title, price))
    except Exception as e:
        print(f"Error: {e}")


def query_data(connection: sqlite3.Connection) -> list[tuple]:
    query = """
            SELECT * FROM products_data
    """

    try:
        with connection:
            rows = connection.execute(query).fetchall()
            return rows
    except Exception as e:
        print(f"Error: {e}")


def query_first(connection: sqlite3.Connection, sku: str):
    query = f"SELECT price FROM products_data WHERE sku = ? ORDER BY id DESC LIMIT 1 "

    try:
        with connection:
            rows = connection.execute(query, [sku]).fetchall()
            return rows
    except Exception as e:
        print(f"Error: {e}")


def delete_table(connection: sqlite3.Connection, table_name: str):
    query = f"DROP TABLE IF EXISTS {table_name}"
    
    try:
        with connection:
            connection.execute(query)
    except Exception as e:
        print(f"Error: {e}")