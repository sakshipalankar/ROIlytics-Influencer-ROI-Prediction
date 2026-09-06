import pymysql
import sys

passwords = [
    '', 'root', 'admin', 'password', '1234', '123456', '12345678', '123456789', '12345',
    'mysql', 'mysql123', 'root123', 'root1234', 'Root@123', 'Root@1234', 'Admin@123', 'Admin@1234',
    'sakshi', 'Sakshi', 'sakshi123', 'Sakshi123', 'Sakshi@123', 'sakshi@123', 'Sakshi#123',
    'palankar', 'Palankar', 'sakshipalankar', 'SakshiPalankar',
    'loq', 'LOQ', 'lenovo', 'Lenovo', 'Lenovo@123', 'loq123', 'LOQ123',
    'roilytics', 'ROIlytics', 'Roilytics@123', 'Roilytics123', 'Password123!', 'Password@123',
    'toor', 'manager', 'qwerty', 'welcome', 'Welcome@1', 'Welcome@123', 'mysql@123', 'dbpassword'
]

print(f"Testing {len(passwords)} candidate passwords...")
found = None
for p in passwords:
    try:
        conn = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password=p,
            connect_timeout=1
        )
        print(f"FOUND PASSWORD: '{p}'")
        found = p
        conn.close()
        break
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1045:
            continue
        print(f"Other error for '{p}': {e}")
    except Exception as e:
        print(f"Error for '{p}': {e}")

if found is not None:
    with open("scripts/found_pwd.txt", "w") as f:
        f.write(found)
    print(f"SUCCESS: Saved password '{found}'")
else:
    print("Not found in quick list.")
