# fix_old_students.py
import pyodbc
import werkzeug.security
import os
from dotenv import load_dotenv

load_dotenv()

DB = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=DESKTOP-VM930UU;"
    "Database=SmartAttendanceDB;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(DB)
cursor = conn.cursor()

cursor.execute("""
    SELECT Id, Name, ParentPassword, StudentId
    FROM Users
    WHERE Role = N'طالب' AND IsActive = 1 AND PasswordHash IS NULL
""")

students = cursor.fetchall()
print(f"🔍 عدد الطلاب بحاجة لإصلاح: {len(students)}")

fixed = 0
for s in students:
    # اختر كلمة المرور
    if s.ParentPassword:  # hash موجود (PBKDF2)
        cursor.execute(
            "UPDATE Users SET PasswordHash = ? WHERE Id = ?",
            (s.ParentPassword, s.Id)
        )
    else:
        # استخدم رقم القيد
        pw = s.StudentId or s.Name
        pw_hash = werkzeug.security.generate_password_hash(pw)
        cursor.execute(
            "UPDATE Users SET PasswordHash = ? WHERE Id = ?",
            (pw_hash, s.Id)
        )
    fixed += 1
    print(f"✅ إصلاح: {s.Name}")

conn.commit()
conn.close()
print(f"\n🎉 تم إصلاح {fixed} طالب")
