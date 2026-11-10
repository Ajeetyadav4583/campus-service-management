from database import get_db_connection

try:
    db = get_db_connection()
    print("Database Connected Successfully!")
    print("Database:", db.database)
    db.close()
except Exception as e:
    print("Error:", e)