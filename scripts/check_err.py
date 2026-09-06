import pymysql

try:
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='', connect_timeout=2)
    print("Connected with empty password!")
    conn.close()
except Exception as e:
    print(f"Error connecting: {type(e).__name__} - {e}")
