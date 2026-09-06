import pymysql
import os

passwords_to_try = ['', 'root', 'admin', 'password', '1234', '123456', '12345678', 'mysql', 'loq', 'sakshi', 'Sakshi@123', 'root123', 'Password123!']

print("Testing MySQL connections on localhost:3306...")
found = False
for pwd in passwords_to_try:
    try:
        conn = pymysql.connect(host='localhost', port=3306, user='root', password=pwd, connect_timeout=1)
        print(f"✅ SUCCESS connecting to MySQL as root with password: '{pwd}'")
        with conn.cursor() as cur:
            cur.execute("SHOW DATABASES;")
            dbs = [r[0] for r in cur.fetchall()]
            print("Databases:", dbs)
        conn.close()
        found = pwd
        break
    except Exception as e:
        # print(f"Failed with '{pwd}': {e}")
        pass

if found is not False:
    print(f"Working password is: '{found}'")
else:
    print("❌ None of the standard passwords connected to MySQL.")
