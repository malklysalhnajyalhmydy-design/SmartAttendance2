# -*- coding: utf-8 -*-
"""
سكربت تعديل اسم المشروع تلقائياً
SmartFace AI  →  AI Smart Classroom Monitoring System
"""

import os
import re
import shutil
from datetime import datetime

# ===================== الإعدادات =====================
OLD_NAME_FULL = "SmartFace AI"
OLD_NAME_PRO = "SmartFace AI Pro"
NEW_NAME_FULL = "AI Smart Classroom Monitoring System"
NEW_NAME_SHORT = "AI Smart Classroom"

# المسار (المجلد الذي يحتوي على ملفات HTML)
TEMPLATES_DIR = "templates"

# مجلد النسخ الاحتياطي
BACKUP_DIR = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ===================== التصميم الجديد للشريط الجانبي =====================
NEW_BRAND_HTML = '''<h4 style="font-size:1.05rem; font-weight:900; margin:0;">AI Smart Classroom</h4>
                <h6 style="color:rgba(255,255,255,0.6); font-size:0.7rem; margin:4px 0 0; letter-spacing:1px;">MONITORING SYSTEM</h6>'''

# ===================== دالة النسخ الاحتياطي =====================
def backup_file(src_path):
    """ينشئ نسخة احتياطية من الملف قبل التعديل"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    filename = os.path.basename(src_path)
    dst = os.path.join(BACKUP_DIR, filename)
    shutil.copy2(src_path, dst)


# ===================== دالة التعديل =====================
def process_file(filepath):
    """يعدل ملف HTML واحد"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
   
    original = content
    changes = []
   
    # ============ 1. تعديل <title> ============
    # SmartFace AI Pro → AI Smart Classroom Monitoring System
    if OLD_NAME_PRO in content:
        content = content.replace(OLD_NAME_PRO, NEW_NAME_FULL)
        changes.append("✅ title (Pro)")
   
    # SmartFace AI → AI Smart Classroom Monitoring System
    if OLD_NAME_FULL in content:
        content = content.replace(OLD_NAME_FULL, NEW_NAME_FULL)
        changes.append("✅ title (regular)")
   
    # ============ 2. تعديل الشريط الجانبي ============
    # أنماط مختلفة محتملة للسطر القديم
    patterns = [
        # النمط الشائع
        r'<h4>SmartFace <span style="color:var\(--secondary\)">AI</span></h4>',
        # نمط مع مسافات مختلفة
        r'<h4>\s*SmartFace\s*<span\s*style="color:var\(--secondary\)"\s*>\s*AI\s*</span>\s*</h4>',
        # نمط بدون span
        r'<h4>SmartFace AI</h4>',
    ]
   
    for pattern in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, NEW_BRAND_HTML, content)
            changes.append("✅ Sidebar brand")
            break
   
    # ============ 3. تعديل عنوان login.html ============
    # في صفحة تسجيل الدخول يوجد <h3>SmartFace AI</h3>
    login_pattern = r'<h3>SmartFace AI</h3>'
    if re.search(login_pattern, content):
        new_login = '''<h3 style="font-size:1.2rem;">AI Smart Classroom</h3>
            <p style="color:var(--text-muted); font-size:0.85rem; margin-top:5px;">Monitoring System</p>'''
        content = re.sub(login_pattern, new_login, content)
        changes.append("✅ Login title")
   
    # ============ 4. أي ذِكر آخر باقي ============
    # استبدال أي "SmartFace AI" متبقية في نصوص
    if "SmartFace" in content:
        content = content.replace("SmartFace AI", NEW_NAME_FULL)
        content = content.replace("SmartFace", NEW_NAME_SHORT)
        changes.append("✅ remaining mentions")
   
    # ============ الحفظ ============
    if content != original:
        backup_file(filepath)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes
    return None


# ===================== البرنامج الرئيسي =====================
def main():
    print("=" * 60)
    print("🚀 بدء تعديل اسم المشروع")
    print("=" * 60)
    print(f"📁 المجلد: {os.path.abspath(TEMPLATES_DIR)}")
    print(f"💾 النسخ الاحتياطي: {os.path.abspath(BACKUP_DIR)}")
    print()
   
    if not os.path.exists(TEMPLATES_DIR):
        print(f"❌ خطأ: المجلد '{TEMPLATES_DIR}' غير موجود!")
        print("   تأكد من تشغيل السكربت من مجلد المشروع الصحيح.")
        return
   
    html_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.html')]
   
    if not html_files:
        print("⚠️  لا توجد ملفات HTML في المجلد.")
        return
   
    print(f"📄 عدد الملفات: {len(html_files)}")
    print()
   
    processed = 0
    skipped = 0
    errors = 0
   
    for i, filename in enumerate(html_files, 1):
        filepath = os.path.join(TEMPLATES_DIR, filename)
       
        try:
            changes = process_file(filepath)
           
            if changes:
                processed += 1
                print(f"[{i}/{len(html_files)}] ✅ {filename}")
                for c in changes:
                    print(f"      └─ {c}")
            else:
                skipped += 1
                print(f"[{i}/{len(html_files)}] ⏭️  {filename} (لا توجد تغييرات)")
       
        except Exception as e:
            errors += 1
            print(f"[{i}/{len(html_files)}] ❌ {filename} — خطأ: {e}")
   
    print()
    print("=" * 60)
    print("📊 ملخص النتائج")
    print("=" * 60)
    print(f"✅ تم تعديل: {processed} ملف")
    print(f"⏭️  تم تخطي: {skipped} ملف")
    print(f"❌ أخطاء: {errors}")
    print()
    print(f"💾 النسخ الاحتياطية محفوظة في: {BACKUP_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()