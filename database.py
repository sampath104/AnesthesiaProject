# Database.py
import mysql.connector
from flask import session, flash
import bcrypt

# --- Database Connection ---
def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Use your MySQL username here
        password='',  # Use your MySQL password here
        database='anesthesia'  # The name of your MySQL database
    )

# --- Generic Query Handlers ---
def execute_select(query, params=None):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        return f"Select error: {str(e)}"

def execute_insert(query, params):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return f"Insert error: {str(e)}"

def execute_insert_return_id(query, params):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        insert_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return insert_id
    except Exception as e:
        return None

def execute_update(query, params):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False

def execute_delete(query, params):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        message = "Record deleted." if cursor.rowcount > 0 else "No record found to delete."
        cursor.close()
        conn.close()
        return message
    except Exception as e:
        return f"Delete error: {str(e)}"


# --- Login Utilities ---
def check_login(query, email, password_input):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        if bcrypt.checkpw(password_input.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['email'] = user['email']
            return True, "Login Successful", "success"  # Success message
        else:
            return False, "Invalid password", "danger"
    else:
        return False, "User not found", "danger"
