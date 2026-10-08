# -*- coding: utf-8 -*-
"""
fix_hand.py
إصلاح دالة detect_hand_raised فقط — باستخدام Regex ذكي
"""

import re
import os
import shutil
import sys
import io
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_FILE = 'attendance_server.py'

# ==================== الإصلاح ====================
NEW_FUNCTION = '''def detect_hand_raised(image_bgr, faces=None):
    """🖐️ كشف رفع اليد فوق الرأس — نسخة محسّنة"""
    results = []
    if not MP_AVAILABLE or MP_HANDS is None:
        return results
    try:
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        h, w = image_rgb.shape[:2]
        mp_result = MP_HANDS.process(image_rgb)
        if not mp_result.multi_hand_landmarks:
            return results
        if not faces:
            try:
                faces = face_app.get(image_bgr)
            except Exception:
                return results
        if not faces or len(faces) == 0:
            return results
        try:
            head_top = min([f.bbox[1] for f in faces if hasattr(f, 'bbox')])
        except (ValueError, AttributeError):
            return results

        for hand_lms in mp_result.multi_hand_landmarks:
            try:
                middle_tip_y = hand_lms.landmark[12].y * h
                if middle_tip_y < head_top:
                    results.append({
                        'type': 'hand_raised',
                        'severity': 'medium',
                        'description': '🖐️ رفع اليد فوق مستوى الرأس',
                        'confidence': 0.75
                    })
                    break
            except (IndexError, AttributeError):
                continue
    except Exception as e:
        print(f"⚠️ MediaPipe: {e}", flush=True)
    return results
'''


def main():
    print("=" * 70)
    print(f"  🔧 إصلاح detect_hand_raised — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not os.path.exists(TARGET_FILE):
        print(f"❌ الملف {TARGET_FILE} غير موجود!")
        return 1

    # نسخة احتياطية
    os.makedirs('backups', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = f'backups/{TARGET_FILE}.{ts}.bak'
    shutil.copy2(TARGET_FILE, backup)
    print(f"✅ نسخة احتياطية: {backup}\n")

    # قراءة
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    original_len = len(content)

    # ===== البحث عن الدالة =====
    # يبحث عن def detect_hand_raised ثم يلتقط حتى نهاية return results
    # (نبحث عن "def detect_hand_raised" حتى نجد أول "def " أو "@app.route" بعدها)
    pattern = re.compile(
        r'(def detect_hand_raised\s*\([^)]*\):.*?return results\s*\n)',
        re.DOTALL
    )

    matches = pattern.findall(content)
    print(f"🔍 عدد مرات وجود الدالة: {len(matches)}")

    if not matches:
        print("❌ لم أجد الدالة detect_hand_raised في الملف!")
        print("💡 تحقق أن اسم الدالة مكتوب بهذا الشكل بالضبط.")
        return 1

    if len(matches) > 1:
        print(f"⚠️  تحذير: الدالة موجودة {len(matches)} مرة — سيتم استبدال الأولى فقط")

    old_func = matches[0]
    print(f"\n📏 طول الدالة الأصلية: {len(old_func):,} حرف")
    print(f"📏 طول الدالة الجديدة: {len(NEW_FUNCTION):,} حرف")

    # فحص إذا الإصلاح مطبّق مسبقاً
    if 'try:\n                faces = face_app.get(image_bgr)\n            except Exception:' in old_func:
        print("\n⏭️  الإصلاح مطبّق مسبقاً — لا حاجة للتعديل")
        return 0

    # استبدال
    new_content = content.replace(old_func, NEW_FUNCTION, 1)

    # كتابة
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\n✅ تم التعديل بنجاح!")
    print(f"📊 الفرق: {len(new_content) - original_len:+,} حرف")
    print(f"\n{'='*70}")
    print(f"  🔍 الخطوات التالية:")
    print(f"     1. راجع الملف: notepad {TARGET_FILE}")
    print(f"     2. اختبر: python {TARGET_FILE}")
    print(f"     3. للتراجع: copy {backup} {TARGET_FILE}")
    print(f"{'='*70}")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 تم الإلغاء")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)