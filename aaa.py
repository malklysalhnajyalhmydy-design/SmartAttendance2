"""
🔧 إصلاح InsightFace - الرجوع إلى buffalo_l مع الحفاظ على كل التحسينات
"""

import os
import re
import shutil
from datetime import datetime

MAIN_FILE = "attendance_server.py"

def log(msg, icon="ℹ️"):
    print(f"{icon} {msg}", flush=True)

def main():
    print("\n" + "═" * 60, flush=True)
    print("🔧 إصلاح InsightFace — الرجوع إلى buffalo_l", flush=True)
    print("═" * 60 + "\n", flush=True)
   
    if not os.path.exists(MAIN_FILE):
        log(f"الملف {MAIN_FILE} غير موجود!", "❌")
        return
   
    # نسخة احتياطية
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{MAIN_FILE}.insightface_fix_{timestamp}.bak"
    shutil.copy2(MAIN_FILE, backup)
    log(f"نسخة احتياطية: {backup}", "✅")
   
    with open(MAIN_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
   
    original = content
    changes = []
   
    # ═══════════════════════════════════════════════════════
    # التعديل 1: استبدال buffalo_sc بـ buffalo_l مع fallback ذكي
    # ═══════════════════════════════════════════════════════
   
    # النص الحالي المتوقع
    old_text = """try:
    # 🚀 [Optimizer] نموذج أخف (3-4x أسرع)
    face_app = FaceAnalysis(name='buffalo_sc', providers=['CPUExecutionProvider'])
    face_app.prepare(ctx_id=0, det_size=(320, 320))
    print("✅ InsightFace buffalo_sc @ 320x320 (سريع)", flush=True)"""
   
    new_text = """try:
    # 🚀 [Optimizer] استخدام buffalo_l (موجود محلياً)
    # ملاحظة: buffalo_l أكبر قليلاً لكن det_size=320 يسرّعه كثيراً
    _insightface_model = 'buffalo_l'
   
    # التحقق من وجود buffalo_l محلياً
    _insightface_root = os.path.join(os.path.expanduser('~'), '.insightface', 'models')
    if not os.path.exists(os.path.join(_insightface_root, 'buffalo_l')):
        # محاولة buffalo_sc إن وُجد، وإلا buffalo_l
        if os.path.exists(os.path.join(_insightface_root, 'buffalo_sc')):
            _insightface_model = 'buffalo_sc'
   
    face_app = FaceAnalysis(
        name=_insightface_model,
        providers=['CPUExecutionProvider']
    )
    # det_size=320 يسرّع الكشف ~4x مقارنة بـ 640x640
    face_app.prepare(ctx_id=0, det_size=(320, 320))
    print(f"✅ InsightFace {_insightface_model} @ 320x320 (وضع سريع)", flush=True)"""
   
    if old_text in content:
        content = content.replace(old_text, new_text, 1)
        changes.append("استبدال buffalo_sc → buffalo_l (مع fallback ذكي)")
    else:
        # محاولة استبدال بديل (في حال اختلف النص قليلاً)
        pattern = re.compile(
            r"face_app\s*=\s*FaceAnalysis\(name='buffalo_sc'[^\n]*\n"
            r"\s*face_app\.prepare\(ctx_id=0,\s*det_size=\(320,\s*320\)\)\n"
            r"\s*print\([^\n]*\)",
            re.MULTILINE
        )
        if pattern.search(content):
            content = pattern.sub(new_text, content, count=1)
            changes.append("استبدال buffalo_sc → buffalo_l (regex)")
        else:
            # بحث عن أي استخدام لـ buffalo_sc
            if "buffalo_sc" in content:
                content = content.replace("name='buffalo_sc'", "name='buffalo_l'")
                content = content.replace('name="buffalo_sc"', 'name="buffalo_l"')
                changes.append("استبدال جميع buffalo_sc → buffalo_l")
            else:
                log("لم يتم العثور على buffalo_sc — ربما تم الإصلاح مسبقاً", "⚠️")
   
    # ═══════════════════════════════════════════════════════
    # التعديل 2: إذا كانت هناك محاولة تحميل buffalo_sc أخرى
    # ═══════════════════════════════════════════════════════
    # نحذف أي إشارة متبقية
    if "buffalo_sc" in content:
        content = content.replace("buffalo_sc", "buffalo_l")
        changes.append("تنظيف كل إشارات buffalo_sc")
   
    # ═══════════════════════════════════════════════════════
    # حفظ
    # ═══════════════════════════════════════════════════════
    if content != original:
        with open(MAIN_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        log("تم حفظ التعديلات", "✅")
        print()
        for c in changes:
            log(f"  • {c}", "✅")
    else:
        log("لا توجد تغييرات مطلوبة", "⚠️")
   
    # ═══════════════════════════════════════════════════════
    # التحقق من الصحة النحوية
    # ═══════════════════════════════════════════════════════
    print()
    log("التحقق من الصحة النحوية...", "🔧")
    try:
        import ast
        with open(MAIN_FILE, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        log("✅ الملف صحيح نحوياً", "✅")
    except SyntaxError as e:
        log(f"❌ خطأ نحوي: السطر {e.lineno} — {e.msg}", "❌")
        log(f"استعد من: {backup}", "⚠️")
        return
   
    # ═══════════════════════════════════════════════════════
    # التحقق من وجود buffalo_l محلياً
    # ═══════════════════════════════════════════════════════
    print()
    log("التحقق من النماذج المتوفرة محلياً...", "🔧")
    models_dir = os.path.join(os.path.expanduser('~'), '.insightface', 'models')
    if os.path.exists(models_dir):
        models = os.listdir(models_dir)
        for m in models:
            marker = "✅" if os.path.isdir(os.path.join(models_dir, m)) else "📄"
            print(f"   {marker} {m}", flush=True)
        if 'buffalo_l' in models:
            log("buffalo_l موجود محلياً", "✅")
        else:
            log("buffalo_l غير موجود! تأكد من التحميل المسبق", "⚠️")
    else:
        log(f"مجلد النماذج غير موجود: {models_dir}", "⚠️")
   
    print()
    print("═" * 60, flush=True)
    print("🎉 اكتمل الإصلاح", flush=True)
    print("═" * 60, flush=True)
    print(f"\n📌 الخطوة التالية:", flush=True)
    print(f"   python {MAIN_FILE}", flush=True)
    print(f"\n⚠️ لاستعادة النسخة الأصلية:", flush=True)
    print(f'   copy "{backup}" {MAIN_FILE}', flush=True)
    print()


if __name__ == "__main__":
    main()