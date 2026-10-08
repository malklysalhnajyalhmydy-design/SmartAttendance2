import os

def print_directory_tree(start_path, indent=""):
    """
    دالة لعرض هيكل المجلد بشكل متداخل (شجري).
    """
    try:
        # الحصول على قائمة بالعناصر داخل المجلد (ملفات ومجلدات)
        items = os.listdir(start_path)
    except PermissionError:
        print(f"{indent}⚠️ [لا يمكن الوصول: أذونات محظورة]")
        return
    except FileNotFoundError:
        print(f"{indent}❌ [المسار غير موجود]")
        return

    # فرز العناصر (المجلدات أولاً ثم الملفات، أو أبجدياً)
    items.sort()

    for i, item in enumerate(items):
        item_path = os.path.join(start_path, item)
        is_last = (i == len(items) - 1)
       
        # تحديد رمز الفروع (مثل الشجرة)
        connector = "└── " if is_last else "├── "
       
        # إذا كان مجلداً
        if os.path.isdir(item_path):
            print(f"{indent}{connector}📁 {item}/")
            # استدعاء الدالة نفسها بشكل متكرر (Recursive) لاستكشاف المجلد الداخلي
            # زيادة المسافة البادئة للمستوى التالي
            next_indent = indent + ("    " if is_last else "│   ")
            print_directory_tree(item_path, next_indent)
        else:
            # إذا كان ملفاً
            print(f"{indent}{connector}📄 {item}")

# ===== التشغيل الرئيسي =====
if __name__ == "__main__":
    print("=" * 60)
    print("🗂️  مستكشف المجلدات - أداة عرض الشجرة")
    print("=" * 60)
   
    # طلب المسار من المستخدم
    user_path = input("اكتب مسار المجلد (مثلاً: C:\\Users\\ABRAG Soft\\Desktop) أو اضغط Enter للاستخدام الحالي: ").strip()
   
    # إذا لم يكتب المستخدم شيئاً، نستخدم مجلد المشروع الحالي
    if not user_path:
        user_path = os.getcwd()
   
    print("\n" + "=" * 60)
    print(f"📂 محتويات: {user_path}")
    print("=" * 60)
   
    # عرض الشجرة
    print_directory_tree(user_path)
   
    print("\n✅ انتهى العرض!")
    input("اضغط Enter للخروج...")