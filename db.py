import sqlite3

DB_NAME = "voice_cloner.db"


def create_users_table():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("voice_cloner.db")

    # Create a cursor object
    cursor = conn.cursor()

    # Create the 'users' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Auto-incremented primary key
        chat_id INTEGER,                -- Telegram's unique user ID
        username TEXT,                         -- Optional Telegram username
        credits INTEGER DEFAULT 0,            -- Remaining free credits
        audio TEXT,                            -- Path or URL of the latest audio file
        refs INTEGER DEFAULT 0,               -- Number of invitations
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- User creation timestamp
    );
    """)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Users table created successfully.")


# Function to check if a user exists
def user_exists(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE chat_id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


# Function to create a new user
def create_user(chat_id, username=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (chat_id, username) 
        VALUES (?, ?)
    """,
        (chat_id, username),
    )
    conn.commit()
    conn.close()


def update_user_column(chat_id, column, value, increment=False):
    """
    Update a specific column for a user in the 'users' table.

    Args:
        chat_id (int): The chat_id of the user to update.
        column (str): The column to update.
        value: The value to set or increment the column by.
        increment (bool): If True, increments the column value; otherwise, sets it.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if increment:
        # Increment the column value
        query = f"UPDATE users SET {column} = {column} + ? WHERE chat_id = ?"
    else:
        # Set the column value
        query = f"UPDATE users SET {column} = ? WHERE chat_id = ?"

    cursor.execute(query, (value, chat_id))
    conn.commit()
    conn.close()


def get_users_columns(chat_id, columns):
    """
    Retrieve values from specific column(s) in the 'users' table for a given chat_id.

    Args:
        chat_id (int): The chat ID of the user.
        columns (list or str): Column name(s) to retrieve. Can be a single column or a list of columns.

    Returns:
        dict or None: A dictionary of column-value pairs if the user exists, otherwise None.
    """
    conn = sqlite3.connect("voice_cloner.db")
    cursor = conn.cursor()

    # Ensure columns is a list to handle both single and multiple columns
    if isinstance(columns, str):
        columns = [columns]

    # Convert columns list to a comma-separated string for the SQL query
    columns_str = ", ".join(columns)

    try:
        query = f"SELECT {columns_str} FROM users WHERE chat_id = ?"
        cursor.execute(query, (chat_id,))
        result = cursor.fetchone()

        if result:
            return dict(
                zip(columns, result)
            )  # Map columns to their corresponding values
        else:
            return None  # User not found
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()
