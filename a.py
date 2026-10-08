# -*- coding: utf-8 -*-
import os, shutil, sys
from datetime import datetime

print("=" * 60)
print("  🔍 البحث عن app.py تلقائياً")
print("=" * 60)
print()

# البحث عن app.py في السطح المكتب
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
found = []

print(f"🔎 البحث في: {desktop}")
print("   (قد يأخذ 10-30 ثانية)...\n")

for root, dirs, files in os.walk(desktop):
    # تجاهل مجلدات النظام
    dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'venv', '.venv']]
    
    if "app.py" in files:
        full = os.path.join(root, "app.py")
        # تحقق أنه ملف المشروع وليس ملف آخر
        try:
            with open(full, "r", encoding="utf-8", errors="ignore") as f:
                head = f.read(5000)
            if "from flask import" in head or "Flask(__name__)" in head or "insightface" in head:
                found.append(full)
        except Exception:
            pass

print(f"\n{'=' * 60}")
if not found:
    print("❌ لم أجد app.py على سطح المكتب!")
    print("\n💡 جرّب واحداً من هذه الحلول:")
    print("   1. ابحث يدوياً في File Explorer عن app.py")
    print("   2. انسخ مساره الكامل هنا")
    input("\nاضغط Enter للخروج...")
    sys.exit(1)

print(f"✅ وجدت {len(found)} ملف app.py:\n")
for i, path in enumerate(found, 1):
    size = os.path.getsize(path)
    print(f"   [{i}] {path}")
    print(f"       الحجم: {size:,} بايت")

print(f"\n{'=' * 60}")

if len(found) == 1:
    target = found[0]
    print(f"✅ سأستخدم: {target}")
else:
    choice = input(f"\nاختر رقم الملف الصحيح (1-{len(found)}): ").strip()
    try:
        idx = int(choice) - 1
        target = found[idx]
    except Exception:
        print("❌ اختيار غير صحيح!")
        input("اضغط Enter للخروج...")
        sys.exit(1)

# نسخ fix.py إلى مجلد app.py
project_dir = os.path.dirname(target)
print(f"\n📁 مجلد المشروع: {project_dir}")

# هل fix.py موجود في نفس المجلد؟
fix_src = os.path.join(os.getcwd(), "fix.py")
fix_dst = os.path.join(project_dir, "fix.py")

if os.path.exists(fix_src) and os.path.abspath(fix_src) != os.path.abspath(fix_dst):
    print(f"\n📋 نسخ fix.py إلى مجلد المشروع...")
    shutil.copy(fix_src, fix_dst)
    print(f"   ✅ تم")

# شغّل fix.py
print(f"\n{'=' * 60}")
print(f"🚀 تشغيل fix.py من مجلد المشروع...")
print(f"{'=' * 60}\n")

os.chdir(project_dir)
os.system(f'python "{fix_dst}"')

input("\nاضغط Enter للخروج...")