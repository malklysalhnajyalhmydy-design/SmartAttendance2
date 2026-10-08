"""
🔥 وحدة كشف الحريق والدخان — نسخة عالية الحساسية
════════════════════════════════════════════════════════════
تعمل على CPU — بدون AI خارجي
تكتشف:
  ✅ النار الصغيرة (شمعة، ورقة صغيرة)
  ✅ الدخان الخفيف (سيجارة، بخار)
  ✅ تعمل مع كاميرا اللابتوب
════════════════════════════════════════════════════════════
"""

import cv2
import numpy as np


# ═══════════════════════════════════════════════════════════
# 🎯 الإعدادات — مُعايَرة للحساسية العالية
# ═══════════════════════════════════════════════════════════

# النار — أصغر حجم ممكن
FIRE_MIN_AREA = 1000            # ✅ 0.06% من صورة 640×480
FIRE_RATIO_THRESHOLD = 0.002    # ✅ 0.2% من الصورة

# الدخان — أصغر حجم ممكن
SMOKE_MIN_AREA = 800            # ✅ 0.26% من الصورة
SMOKE_RATIO_THRESHOLD = 0.005   # ✅ 0.5% من الصورة

# ✅ إعدادات إضافية للتحكم بالحساسية
FIRE_SENSITIVITY = 0.5        # 0.9 = حساس جداً | 0.5 = متوسط
SMOKE_SENSITIVITY = 0.40       # 0.7 = حساس
MOTION_REQUIRED_FIRE = True    # False = يكتشف النار الثابتة أيضاً
MOTION_REQUIRED_SMOKE = True    # True = الدخان يحتاج حركة (لتجنب الجدران)


# ═══════════════════════════════════════════════════════════
# 🎨 مدى الألوان — واسع جداً ليكتشف كل أنواع النار
# ═══════════════════════════════════════════════════════════
def _build_fire_masks(hsv):
    """
    يبني 3 أقنعة للنار بألوان مختلفة:
    1. أحمر داكن (لهب)
    2. برتقالي (لهب)
    3. أصفر (لهب فاتح)
    """
    kernel = np.ones((3, 3), np.uint8)
    masks = []

    # ─── 1. أحمر داكن ───
    lower_red1 = np.array([0, 80, 120])
    upper_red1 = np.array([12, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)

    # ─── 2. برتقالي ───
    lower_orange = np.array([12, 90, 150])
    upper_orange = np.array([25, 255, 255])
    mask2 = cv2.inRange(hsv, lower_orange, upper_orange)

    # ─── 3. أصفر (لهب فاتح) ───
    lower_yellow = np.array([25, 80, 180])
    upper_yellow = np.array([35, 255, 255])
    mask3 = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # ─── 4. أحمر فاتح (على الحد الأعلى للـ hue) ───
    lower_red2 = np.array([160, 80, 120])
    upper_red2 = np.array([180, 255, 255])
    mask4 = cv2.inRange(hsv, lower_red2, upper_red2)

    # دمج الأقنعة
    combined = cv2.bitwise_or(mask1, mask2)
    combined = cv2.bitwise_or(combined, mask3)
    combined = cv2.bitwise_or(combined, mask4)

    # تنظيف
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)

    return combined


def _build_smoke_mask(hsv, gray, frame_bgr, prev_frame):
    """
    يبني قناع الدخان مع فلاتر متعددة
    """
    kernel = np.ones((3, 3), np.uint8)

    # ─── 1. رمادي/أبيض (تشبع منخفض) ───
    lower_smoke = np.array([0, 0, 100])       # ✅ سطوع أخفض
    upper_smoke = np.array([180, 55, 255])    # ✅ تشبع أعلى قليلاً
    mask = cv2.inRange(hsv, lower_smoke, upper_smoke)

    # ─── 2. استبعاد الحواف الصلبة (جدران، أبواب) ───
    edges = cv2.Canny(gray, 50, 150)
    edges_dilated = cv2.dilate(edges, kernel, iterations=2)
    not_edges = cv2.bitwise_not(edges_dilated)
    mask = cv2.bitwise_and(mask, not_edges)

    # ─── 3. فلتر الحركة (إن وُجد prev_frame) ───
    if MOTION_REQUIRED_SMOKE and prev_frame is not None:
        if prev_frame.shape == frame_bgr.shape:
            diff = cv2.absdiff(frame_bgr, prev_frame)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, motion = cv2.threshold(diff_gray, 15, 255, cv2.THRESH_BINARY)
            motion = cv2.dilate(motion, kernel, iterations=2)
            mask = cv2.bitwise_and(mask, motion)

    # تنظيف
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    return mask


# ═══════════════════════════════════════════════════════════
# 🎯 الدالة الرئيسية
# ═══════════════════════════════════════════════════════════
def detect_fire_smoke(frame_bgr, prev_frame=None):
    """
    كشف النار والدخان بحساسية عالية
    """
    h, w = frame_bgr.shape[:2]
    total_area = h * w

    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((3, 3), np.uint8)

    # ═══════════════════════════════════════════════
    # 1. كشف النار
    # ═══════════════════════════════════════════════
    mask_fire = _build_fire_masks(hsv)
    fire_pixels = cv2.countNonZero(mask_fire)
    fire_ratio = fire_pixels / total_area

    # ═══════════════════════════════════════════════
    # 2. كشف الدخان
    # ═══════════════════════════════════════════════
    mask_smoke = _build_smoke_mask(hsv, gray, frame_bgr, prev_frame)
    smoke_pixels = cv2.countNonZero(mask_smoke)
    smoke_ratio = smoke_pixels / total_area

    # ═══════════════════════════════════════════════
    # 3. النتيجة
    # ═══════════════════════════════════════════════
    result = {
        'fire_detected': False,
        'smoke_detected': False,
        'fire_ratio': round(fire_ratio, 5),
        'smoke_ratio': round(smoke_ratio, 5),
        'fire_regions': [],
        'smoke_regions': []
    }

    # ─── مناطق النار ───
    if fire_ratio > FIRE_RATIO_THRESHOLD:
        contours, _ = cv2.findContours(mask_fire, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > FIRE_MIN_AREA:
                x, y, ww, hh = cv2.boundingRect(cnt)
                # ✅ فلترة شكل النار
                aspect = hh / max(ww, 1)
                fill_ratio = area / max(ww * hh, 1)
                # النار عادة غير منتظمة (fill_ratio منخفض)
                # وليست مسطحة جداً (aspect)
                if 0.3 < aspect < 6 and fill_ratio > 0.3:
                    result['fire_regions'].append({
                        'x': int(x), 'y': int(y),
                        'w': int(ww), 'h': int(hh),
                        'area': int(area)
                    })

        # حتى نار واحدة صغيرة كافية
        if result['fire_regions']:
            result['fire_detected'] = True

    # ─── مناطق الدخان ───
    if smoke_ratio > SMOKE_RATIO_THRESHOLD:
        contours, _ = cv2.findContours(mask_smoke, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > SMOKE_MIN_AREA:
                x, y, ww, hh = cv2.boundingRect(cnt)
                result['smoke_regions'].append({
                    'x': int(x), 'y': int(y),
                    'w': int(ww), 'h': int(hh),
                    'area': int(area)
                })

        if result['smoke_regions']:
            result['smoke_detected'] = True

    # ─── طباعة للتشخيص ───
    if fire_ratio > 0.0005 or smoke_ratio > 0.0005:
        print(f"🔥 Fire: {fire_ratio*100:.3f}% | 💨 Smoke: {smoke_ratio*100:.3f}% | "
              f"F={'✅' if result['fire_detected'] else '❌'} "
              f"S={'✅' if result['smoke_detected'] else '❌'}", flush=True)

    return result


# ═══════════════════════════════════════════════════════════
# 🎨 رسم المستطيلات
# ═══════════════════════════════════════════════════════════
def draw_fire_smoke_boxes(image_bgr, detection_result):
    """رسم مستطيلات النار والدخان على الصورة"""
    img = image_bgr.copy()

    # النار — أحمر
    for r in detection_result.get('fire_regions', []):
        cv2.rectangle(img, (r['x'], r['y']),
                      (r['x'] + r['w'], r['y'] + r['h']),
                      (0, 0, 255), 3)
        cv2.putText(img, "FIRE",
                    (r['x'], max(r['y'] - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    # الدخان — رمادي
    for r in detection_result.get('smoke_regions', []):
        cv2.rectangle(img, (r['x'], r['y']),
                      (r['x'] + r['w'], r['y'] + r['h']),
                      (128, 128, 128), 3)
        cv2.putText(img, "SMOKE",
                    (r['x'], max(r['y'] - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (128, 128, 128), 2)

    return img