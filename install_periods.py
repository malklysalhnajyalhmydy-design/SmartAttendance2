# -*- coding: utf-8 -*-
"""
🔧 تثبيت نظام جدول الحصص — يعدّل app.py + ينشئ صفحة الحصص
شغّله مرة واحدة فقط
"""
import os, shutil, sys
from datetime import datetime

APP = "app.py"
if not os.path.exists(APP):
    print("❌ ملف app.py غير موجود في هذا المجلد!")
    print(f"📁 المجلد الحالي: {os.getcwd()}")
    input("اضغط Enter للخروج...")
    sys.exit(1)

backup = f"app.py.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy(APP, backup)
print(f"💾 نسخة احتياطية: {backup}\n")

with open(APP, "r", encoding="utf-8") as f:
    code = f.read()

original_size = len(code)
changes = []

# ═══════════════════════════════════════════════════════════════
# [1] إضافة دوال الحصص + استبدال is_within_attendance_time
# ═══════════════════════════════════════════════════════════════
print("[1/6] إضافة دوال الحصص...")
old1 = '''def is_within_attendance_time():
    settings = load_settings()
    if settings.get('is_24h_mode', False):
        return True
    now = datetime.now().strftime("%H:%M")
    start = settings.get("start_time", "08:00")
    end = settings.get("end_time", "12:00")
    if start <= end:
        return start <= now <= end
    else:
        return now >= start or now <= end'''

new1 = '''# ═══════════════════════════════════════════════════════════════
# 🆕 [Multi-Period] نظام الحضور المتعدد بالحصص
# ═══════════════════════════════════════════════════════════════
PERIOD_GRACE_BEFORE = 5
PERIOD_GRACE_AFTER  = 15


def get_current_period():
    """الحصة الحالية (أو None) — نافذة التسجيل: 5د قبل + 15د بعد"""
    try:
        periods = get_periods()
        if not periods:
            return None
        now = datetime.now()
        now_min = now.hour * 60 + now.minute
        for p in periods:
            if p.get('is_break'):
                continue
            try:
                h, m = map(int, p['start'].split(':'))
                sm = h * 60 + m
                if (sm - PERIOD_GRACE_BEFORE) <= now_min <= (sm + PERIOD_GRACE_AFTER):
                    return {'id': p['id'], 'number': p['number'],
                            'name': p['name'], 'start': p['start'], 'end': p['end']}
            except Exception:
                continue
        return None
    except Exception as e:
        print(f"WARN get_current_period: {e}", flush=True)
        return None


def has_period_attendance_today(user_id, today, period_number):
    """هل سجّل المستخدم هذه الحصة اليوم؟"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Attendance WHERE UserId=? AND AttendanceDate=? AND PeriodNumber=?",
                       (user_id, today, period_number))
        c = cursor.fetchone()[0]
        conn.close()
        return c > 0
    except Exception:
        return False


def get_period_attendance_summary(user_id, today):
    """ملخص الحضور في كل الحصص"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT PeriodNumber, CheckInTime, Status FROM Attendance WHERE UserId=? AND AttendanceDate=? AND PeriodNumber IS NOT NULL ORDER BY PeriodNumber",
                       (user_id, today))
        rows = cursor.fetchall()
        conn.close()
        return {r.PeriodNumber: {'time': str(r.CheckInTime), 'status': r.Status} for r in rows}
    except Exception:
        return {}


def is_within_attendance_time():
    """✅ نافذة التسجيل لكل حصة"""
    settings = load_settings()
    if settings.get('is_24h_mode', False):
        return True
    if get_current_period() is not None:
        return True
    now = datetime.now().strftime("%H:%M")
    start = settings.get("start_time", "08:00")
    end = settings.get("end_time", "12:00")
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end'''

if "def get_current_period()" in code:
    print("   ⏭️ مُطبّق مسبقاً")
    changes.append("⏭️ [1]")
elif old1 in code:
    code = code.replace(old1, new1, 1)
    print("   ✅ تم")
    changes.append("✅ [1]")
else:
    print("   ⚠️ لم أجد الدالة القديمة")
    changes.append("❌ [1]")

# ═══════════════════════════════════════════════════════════════
# [2] استبدال mark_attendance
# ═══════════════════════════════════════════════════════════════
print("[2/6] استبدال mark_attendance...")

import re
pattern = re.compile(r'def mark_attendance\(user_id, name\):.*?(?=\ndef get_last_attendance\()', re.DOTALL)

new_mark = '''def mark_attendance(user_id, name):
    """تسجيل الحضور — يدعم الحضور المتعدد بالحصص"""
    user_id = int(user_id)
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%I:%M %p")

    current_period = get_current_period()
    period_number = current_period['number'] if current_period else None
    period_name = current_period['name'] if current_period else 'حضور عام'

    if not is_within_attendance_time():
        print(f"OUT {name} - خارج وقت الحضور", flush=True)
        return

    role_check = None
    for u in users_cache:
        if u['id'] == user_id:
            role_check = u.get('role')
            break

    if role_check == 'معلم':
        if not is_teacher_working_day(user_id, today):
            print(f"SKIP {name} (معلم) - ليس يوم دوامه", flush=True)
            return

    if is_holiday(today, user_id):
        print(f"SKIP {name} - عطلة", flush=True)
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    if period_number is not None:
        if has_period_attendance_today(user_id, today, period_number):
            conn.close()
            print(f"OK {name} - مسجل في {period_name}", flush=True)
            return
    else:
        cursor.execute("SELECT MAX(CheckInTime) FROM Attendance WHERE UserId=? AND AttendanceDate=? AND PeriodNumber IS NULL",
                       (user_id, today))
        last_ci = cursor.fetchone()[0]
        if last_ci:
            try:
                last_dt = datetime.strptime(str(last_ci), "%H:%M:%S")
                now_dt = datetime.strptime(current_time, "%H:%M:%S")
                if (now_dt - last_dt).total_seconds() / 60 < 30:
                    conn.close()
                    return
            except Exception:
                pass

    cursor.execute("SELECT COUNT(*) FROM Attendance WHERE UserId=? AND AttendanceDate=?", (user_id, today))
    is_first = cursor.fetchone()[0] == 0

    chat_id = None
    if is_first:
        for u in users_cache:
            if u['id'] == user_id:
                chat_id = u.get('telegram_chat_id')
                break
        if not chat_id:
            cursor.execute("SELECT TelegramChatID FROM Users WHERE Id=?", (user_id,))
            row = cursor.fetchone()
            chat_id = row.TelegramChatID if row else None

    conn.close()

    attendance_queue.put((user_id, name, today, current_time, period_number))
    print(f"SAVE {name} -> {period_name} ({current_time})", flush=True)

    if is_first and not has_notification_been_sent(user_id, 'attendance', today):
        if chat_id:
            role = ''
            for u in users_cache:
                if u['id'] == user_id:
                    role = u.get('role', '')
                    break
            labels = {'طالب': 'الطالب', 'معلم': 'المعلم', 'مشرف': 'المشرف', 'حارس': 'الحارس'}
            label = labels.get(role, 'المستخدم')
            msg = "✅ <b>تأكيد الحضور</b>\\n\\n" + label + ": " + name + "\\n📅 " + date_str + "\\n⏰ " + time_str
            send_telegram(chat_id, msg)
            mark_notification_sent(user_id, 'attendance')


'''

if "period_number = current_period['number']" in code:
    print("   ⏭️ مُطبّق مسبقاً")
    changes.append("⏭️ [2]")
else:
    m = pattern.search(code)
    if m:
        code = code[:m.start()] + new_mark + code[m.end():]
        print("   ✅ تم")
        changes.append("✅ [2]")
    else:
        print("   ⚠️ لم أجد mark_attendance")
        changes.append("❌ [2]")

# ═══════════════════════════════════════════════════════════════
# [3] تعديل INSERT في process_attendance_queue
# ═══════════════════════════════════════════════════════════════
print("[3/6] تعديل INSERT في الطابعة...")
old3 = """INSERT INTO Attendance (UserId, Name, AttendanceDate, CheckInTime, Status)
                VALUES (?, ?, ?, ?, N'حاضر')"""
new3 = """INSERT INTO Attendance (UserId, Name, AttendanceDate, CheckInTime, Status, PeriodNumber)
                VALUES (?, ?, ?, ?, N'حاضر', ?)"""

if "Status, PeriodNumber)" in code and "VALUES (?, ?, ?, ?, N'حاضر', ?)" in code:
    print("   ⏭️ مُطبّق مسبقاً")
    changes.append("⏭️ [3]")
elif old3 in code:
    code = code.replace(old3, new3, 1)
    print("   ✅ تم")
    changes.append("✅ [3]")
else:
    print("   ⚠️ لم أجد INSERT")
    changes.append("❌ [3]")

# ═══════════════════════════════════════════════════════════════
# [4] إضافة route /periods
# ═══════════════════════════════════════════════════════════════
print("[4/6] إضافة route /periods...")
m4 = """@app.route('/schedule')
def schedule_page():"""

new4 = '''@app.route('/periods')
def periods_page():
    if 'user_id' not in session or session.get('role') not in ['مدير', 'مشرف']:
        return redirect(url_for('index'))
    return render_template('periods_page.html')


''' + m4

if "@app.route('/periods')" in code:
    print("   ⏭️ مُطبّق مسبقاً")
    changes.append("⏭️ [4]")
elif m4 in code:
    code = code.replace(m4, new4, 1)
    print("   ✅ تم")
    changes.append("✅ [4]")
else:
    print("   ⚠️ لم أجد /schedule")
    changes.append("❌ [4]")

# ═══════════════════════════════════════════════════════════════
# [5] تعديل عملية INSERT في api_periods للتأكد من الترقيم
# ═══════════════════════════════════════════════════════════════
print("[5/6] تحسين api_periods...")
old5 = '''        cursor.execute("SELECT MAX(PeriodNumber) FROM Periods")
        mx = cursor.fetchone()[0] or 0; new_num = mx + 1
        cursor.execute("""INSERT INTO Periods (PeriodNumber, StartTime, EndTime, Name, IsBreak, IsActive)
                          VALUES (?, ?, ?, ?, ?, 1)""",
                       (new_num, data.get('start','08:00'), data.get('end','08:45'),
                        data.get('name', f'الحصة {new_num}'), 1 if data.get('is_break') else 0))
        conn.commit(); conn.close(); return jsonify({"success": True, "message": "✅ تم إضافة الحصة"})'''

new5 = '''        cursor.execute("SELECT MAX(PeriodNumber) FROM Periods")
        mx = cursor.fetchone()[0] or 0; new_num = mx + 1
        start_time = data.get('start', '08:00').strip()
        end_time = data.get('end', '08:45').strip()
        if start_time >= end_time:
            conn.close()
            return jsonify({"success": False, "message": "⚠️ وقت الانتهاء يجب أن يكون بعد البدء"}), 400
        cursor.execute("""INSERT INTO Periods (PeriodNumber, StartTime, EndTime, Name, IsBreak, IsActive)
                          VALUES (?, ?, ?, ?, ?, 1)""",
                       (new_num, start_time, end_time,
                        data.get('name', f'الحصة {new_num}'), 1 if data.get('is_break') else 0))
        conn.commit(); conn.close(); return jsonify({"success": True, "message": "✅ تم إضافة الحصة"})'''

if old5 in code:
    code = code.replace(old5, new5, 1)
    print("   ✅ تم")
    changes.append("✅ [5]")
else:
    print("   ⏭️ تخطي (لم أجد النص الأصلي)")
    changes.append("⏭️ [5]")

# ═══════════════════════════════════════════════════════════════
# حفظ app.py
# ═══════════════════════════════════════════════════════════════
with open(APP, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\n✅ تم حفظ app.py ({original_size:,} → {len(code):,})")

# ═══════════════════════════════════════════════════════════════
# [6] إنشاء صفحة الحصص HTML
# ═══════════════════════════════════════════════════════════════
print("[6/6] إنشاء templates/periods_page.html...")
os.makedirs("templates", exist_ok=True)
html_path = os.path.join("templates", "periods_page.html")

html = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>إدارة الحصص</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',Tahoma,sans-serif}
body{background:#f0f2f5;padding:20px;direction:rtl}
.c{max-width:1050px;margin:0 auto}
.card{background:#fff;border-radius:12px;padding:25px;box-shadow:0 2px 10px rgba(0,0,0,.08);margin-bottom:20px}
h1{color:#2c3e50;margin-bottom:8px;font-size:24px}
h3{color:#2c3e50;margin-bottom:15px;font-size:18px}
.sub{color:#7f8c8d;margin-bottom:20px;font-size:14px}
.btn{padding:11px 22px;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600}
.ok{background:#27ae60;color:#fff}
.ok:hover{background:#229954}
.del{background:#e74c3c;color:#fff;padding:6px 14px;font-size:13px;border:none;border-radius:6px;cursor:pointer}
.edit{background:#f39c12;color:#fff;padding:6px 14px;font-size:13px;border:none;border-radius:6px;cursor:pointer;margin-left:5px}
table{width:100%;border-collapse:collapse;margin-top:15px}
th,td{padding:12px;text-align:right;border-bottom:1px solid #ecf0f1}
th{background:#34495e;color:#fff;font-size:14px}
tr:hover{background:#f8f9fa}
.row{display:grid;grid-template-columns:1fr 1fr 1.5fr 1fr auto;gap:10px;align-items:end}
.fg label{display:block;margin-bottom:6px;font-size:13px;color:#555;font-weight:600}
.fg input,.fg select{width:100%;padding:11px;border:1px solid #ddd;border-radius:8px;font-size:14px;background:#fff}
.empty{text-align:center;padding:40px;color:#95a5a6}
.alert{padding:14px;border-radius:8px;margin-bottom:18px;display:none;font-weight:600}
.alert.s{background:#d4edda;color:#155724;display:block}
.alert.e{background:#f8d7da;color:#721c24;display:block}
.badge{display:inline-block;padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600}
.b-blue{background:#d6eaf8;color:#2874a6}
.b-gray{background:#ecf0f1;color:#7f8c8d}
.tbox{font-family:monospace;background:#ecf0f1;padding:4px 10px;border-radius:5px;font-size:13px}
a{color:#3498db;text-decoration:none;font-size:14px}
</style>
</head>
<body>
<div class="c">
<a href="/admin">← رجوع للوحة التحكم</a>

<div class="card">
<h1>📅 إدارة جدول الحصص</h1>
<p class="sub">أضف الحصص يدوياً — سيتم تسجيل الحضور تلقائياً في كل حصة</p>
<div id="alert" class="alert"></div>

<h3>➕ إضافة حصة جديدة</h3>
<div class="row">
<div class="fg"><label>وقت البدء</label><input type="time" id="st" value="07:30"></div>
<div class="fg"><label>وقت الانتهاء</label><input type="time" id="en" value="08:15"></div>
<div class="fg"><label>اسم الحصة</label><input type="text" id="nm" placeholder="مثلاً: الحصة الأولى"></div>
<div class="fg"><label>النوع</label><select id="br"><option value="0">حصة دراسية</option><option value="1">فسحة / استراحة</option></select></div>
<button class="btn ok" onclick="add()">➕ إضافة</button>
</div>

<div style="margin-top:30px">
<h3>📋 الحصص الحالية</h3>
<table>
<thead><tr><th style="width:50px">#</th><th>الاسم</th><th>البدء</th><th>الانتهاء</th><th>النوع</th><th style="width:160px">إجراءات</th></tr></thead>
<tbody id="tb"></tbody>
</table>
<div class="empty" id="emp" style="display:none">📭 لا توجد حصص — أضف حصة من النموذج أعلاه</div>
</div>
</div>

<div class="card" style="background:#fff8e1;border-right:4px solid #f39c12">
<h3 style="color:#e67e22">💡 كيف يعمل النظام؟</h3>
<ul style="color:#555;line-height:1.9;padding-right:20px">
<li>✅ يُفتح التسجيل <b>5 دقائق قبل</b> بداية كل حصة</li>
<li>✅ يستمر <b>15 دقيقة</b> بعد بدايتها</li>
<li>✅ كل حصة تُسجَّل منفصلة — الطالب قد يحضر حصة ويغيب أخرى</li>
<li>✅ مثال: حصة 07:30 → النافذة من 07:25 إلى 07:45</li>
</ul>
</div>
</div>

<script>
function msg(t,s){var e=document.getElementById('alert');e.className='alert '+(s?'s':'e');e.textContent=t;setTimeout(function(){e.className='alert'},4000);}

function load(){
  fetch('/api/periods').then(function(r){return r.json()}).then(function(d){show(d)}).catch(function(e){msg('خطأ: '+e.message,0)});
}

function show(ps){
  var tb=document.getElementById('tb'),emp=document.getElementById('emp');
  tb.innerHTML='';
  if(!ps||ps.length===0){emp.style.display='block';return;}
  emp.style.display='none';
  ps.forEach(function(p){
    var tr=document.createElement('tr');
    var typeBadge = p.is_break?'<span class="badge b-gray">فسحة</span>':'<span class="badge b-blue">دراسية</span>';
    tr.innerHTML='<td><b>'+p.number+'</b></td>'+
      '<td>'+(p.name||('الحصة '+p.number))+'</td>'+
      '<td><span class="tbox">'+p.start+'</span></td>'+
      '<td><span class="tbox">'+p.end+'</span></td>'+
      '<td>'+typeBadge+'</td>'+
      '<td><button class="edit" onclick="ed('+p.id+',\\''+p.start+'\\',\\''+p.end+'\\',\\''+(p.name||'').replace(/'/g,'')+'\\','+(p.is_break?1:0)+')">✏️</button> '+
      '<button class="del" onclick="del('+p.id+')">🗑️</button></td>';
    tb.appendChild(tr);
  });
}

function add(){
  var st=document.getElementById('st').value,en=document.getElementById('en').value,nm=document.getElementById('nm').value.trim(),br=document.getElementById('br').value==='1';
  if(!st||!en){msg('⚠️ أدخل الأوقات',0);return;}
  if(st>=en){msg('⚠️ وقت الانتهاء يجب أن يكون بعد البدء',0);return;}
  fetch('/api/periods',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({start:st,end:en,name:nm,is_break:br})})
  .then(function(r){return r.json()}).then(function(d){
    if(d.success){msg('✅ '+d.message,1);document.getElementById('nm').value='';load();}
    else msg('❌ '+(d.message||'فشل'),0);
  }).catch(function(e){msg('خطأ: '+e.message,0)});
}

function ed(id,st,en,nm,br){
  var ns=prompt('وقت البدء:',st);if(ns===null)return;
  var ne=prompt('وقت الانتهاء:',en);if(ne===null)return;
  var nn=prompt('اسم الحصة:',nm);if(nn===null)return;
  var nb=confirm('هل هذه فسحة؟ (موافق=فسحة، إلغاء=حصة دراسية)');
  if(ns>=ne){msg('⚠️ وقت الانتهاء بعد البدء',0);return;}
  fetch('/api/periods/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({start:ns,end:ne,name:nn,is_break:nb})})
  .then(function(r){return r.json()}).then(function(d){
    if(d.success){msg('✅ تم التعديل',1);load();}
    else msg('❌ '+(d.message||'فشل'),0);
  }).catch(function(e){msg('خطأ',0)});
}

function del(id){
  if(!confirm('هل أنت متأكد من حذف هذه الحصة؟'))return;
  fetch('/api/periods',{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})})
  .then(function(r){return r.json()}).then(function(d){
    if(d.success){msg('✅ تم الحذف',1);load();}
    else msg('❌ '+(d.message||'فشل'),0);
  }).catch(function(e){msg('خطأ',0)});
}

load();
</script>
</body>
</html>'''

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"   ✅ تم إنشاء: {html_path}")
changes.append("✅ [6]")

# ═══════════════════════════════════════════════════════════════
# النتيجة
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("📊 ملخص التعديلات:")
for c in changes:
    print(f"   {c}")
print(f"{'='*60}")
print("\n🎉 اكتمل!")
print(f"💾 نسخة احتياطية: {backup}")
print("\n📌 الخطوات التالية:")
print("   1. شغّل: python app.py")
print("   2. افتح: http://localhost:5000/periods")
print("   3. أضف الحصص يدوياً من الصفحة")
print()
input("اضغط Enter للخروج...")