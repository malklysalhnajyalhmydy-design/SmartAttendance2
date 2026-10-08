# -*- coding: utf-8 -*-
"""
run_server.py
يشغّل attendance_server.py ويعرض كل الأخطاء بألوان واضحة في PowerShell
- يُلوّن الأخطاء بالأحمر، التحذيرات بالأصفر، النجاح بالأخضر
- يحفظ كل شيء في ملف log
- يعرض ملخص في النهاية
"""

import os
import sys
import subprocess
import io
import re
from datetime import datetime
from collections import Counter

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    # ✅ تفعيل ANSI colors على Windows
    os.system('')

# ==================== ألوان ANSI ====================
class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_RED = '\033[41m'
    BG_YELLOW = '\033[43m'

# ==================== كلمات التصنيف ====================
ERROR_KEYWORDS = [
    '❌', 'Error', 'error:', 'ERROR', 'Traceback',
    'Exception', 'raise ', 'failed', 'FAILED',
    'FAIL', 'critical', 'CRITICAL', 'فشل', 'خطأ',
    'exception', 'يوجد خطأ', '🚨 خطأ', '💥',
    '🛑 خطأ', 'TypeError', 'ValueError', 'KeyError',
    'AttributeError', 'ImportError', 'ModuleNotFound',
    'FileNotFound', 'IndexError', 'NameError',
    'RuntimeError', 'OSError', 'ConnectionError',
    'TimeoutError', 'PermissionError'
]

WARNING_KEYWORDS = [
    '⚠️', 'Warning', 'WARNING', 'warn', 'WARN',
    'تحذير', 'deprecated', 'DeprecationWarning',
    'تعذر', 'تخطي', 'لن يتم', 'غير متوفر',
    'غير مثبت', 'غير متوافقة', 'فشل جزئي'
]

SUCCESS_KEYWORDS = [
    '✅', 'Success', 'SUCCESS', 'نجح', 'تم بنجاح',
    'Successfully', 'OK', 'ok:', 'جاهز', 'ready'
]

INFO_KEYWORDS = [
    'ℹ️', 'INFO', 'Info', 'info:', 'بدء', 'Starting',
    'Loading', 'تحميل', 'تشغيل', 'بدأ', 'معلومات'
]

DEBUG_KEYWORDS = [
    '🔍', 'DEBUG', 'Debug', 'debug:'
]

# ==================== الملفات ====================
LOG_DIR = 'logs'
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'server_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
ERRORS_FILE = os.path.join(LOG_DIR, f'errors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')


class ServerRunner:
    def __init__(self):
        self.counts = Counter()
        self.errors_captured = []
        self.warnings_captured = []
        self.start_time = datetime.now()
        self.log_file = open(LOG_FILE, 'w', encoding='utf-8')
        self.errors_file = open(ERRORS_FILE, 'w', encoding='utf-8')
        self.in_traceback = False
        self.traceback_lines = []

    def classify_line(self, line):
        """يحدد نوع السطر"""
        line_lower = line.lower()

        # في وسط Traceback
        if self.in_traceback:
            if line.startswith(('  File ', '    ', 'Traceback', 'During handling',
                                'The above exception', 'Exception')):
                return 'error'
            else:
                self.in_traceback = False

        # بداية Traceback
        if 'Traceback (most recent call last)' in line:
            self.in_traceback = True
            return 'error'

        # فحص الكلمات المفتاحية
        for kw in ERROR_KEYWORDS:
            if kw.lower() in line_lower:
                return 'error'

        for kw in WARNING_KEYWORDS:
            if kw.lower() in line_lower:
                return 'warning'

        for kw in SUCCESS_KEYWORDS:
            if kw.lower() in line_lower:
                return 'success'

        for kw in DEBUG_KEYWORDS:
            if kw.lower() in line_lower:
                return 'debug'

        for kw in INFO_KEYWORDS:
            if kw.lower() in line_lower:
                return 'info'

        return 'normal'

    def format_line(self, line, kind):
        """يُنسّق السطر حسب نوعه"""
        ts = datetime.now().strftime('%H:%M:%S')
        timestamp = f"{C.DIM}[{ts}]{C.RESET}"

        if kind == 'error':
            return f"{C.RED}{C.BOLD}{timestamp} ❌ {line}{C.RESET}"
        elif kind == 'warning':
            return f"{C.YELLOW}{timestamp} ⚠️  {line}{C.RESET}"
        elif kind == 'success':
            return f"{C.GREEN}{timestamp} {line}{C.RESET}"
        elif kind == 'info':
            return f"{C.CYAN}{timestamp} ℹ️  {line}{C.RESET}"
        elif kind == 'debug':
            return f"{C.MAGENTA}{timestamp} 🔍 {line}{C.RESET}"
        else:
            return f"{timestamp} {line}"

    def process_line(self, line):
        """يعالج سطراً واحداً"""
        line = line.rstrip('\n\r')
        if not line.strip():
            # طباعة السطور الفارغة لتنسيق أفضل
            print()
            self.log_file.write('\n')
            return

        kind = self.classify_line(line)
        self.counts[kind] += 1

        # حفظ في الملفات
        plain_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_file.write(f"[{plain_ts}] [{kind.upper()}] {line}\n")
        self.log_file.flush()

        if kind == 'error':
            self.errors_captured.append(line)
            self.errors_file.write(f"[{plain_ts}] {line}\n")
            self.errors_file.flush()
        elif kind == 'warning':
            self.warnings_captured.append(line)

        # عرض في PowerShell
        print(self.format_line(line, kind), flush=True)

    def print_banner(self):
        """يطبع بانر البداية"""
        print(f"\n{C.BOLD}{C.CYAN}{'='*70}{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}  🚀 تشغيل نظام الحضور الذكي مع مراقبة الأخطاء{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}  📁 سجل: {LOG_FILE}{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}  📁 الأخطاء فقط: {ERRORS_FILE}{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}{'='*70}{C.RESET}\n")

    def print_summary(self):
        """يطبع ملخص في النهاية"""
        duration = (datetime.now() - self.start_time).total_seconds()
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        print(f"\n{C.BOLD}{C.CYAN}{'='*70}{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}  📊 ملخص التشغيل{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}{'='*70}{C.RESET}")
        print(f"  ⏱️  المدة: {minutes} دقيقة و {seconds} ثانية")
        print(f"  {C.RED}❌ أخطاء: {self.counts['error']}{C.RESET}")
        print(f"  {C.YELLOW}⚠️  تحذيرات: {self.counts['warning']}{C.RESET}")
        print(f"  {C.GREEN}✅ نجاح: {self.counts['success']}{C.RESET}")
        print(f"  {C.CYAN}ℹ️  معلومات: {self.counts['info']}{C.RESET}")
        print(f"  {C.MAGENTA}🔍 تفاصيل: {self.counts['debug']}{C.RESET}")
        print(f"  📝 إجمالي: {self.counts['normal'] + sum(self.counts.values()) - self.counts['normal']}")
        print(f"{C.BOLD}{C.CYAN}{'='*70}{C.RESET}")

        # عرض أهم الأخطاء
        if self.errors_captured:
            print(f"\n{C.BOLD}{C.RED}  🚨 الأخطاء المكتشفة ({len(self.errors_captured)}):{C.RESET}")
            print(f"{C.RED}{'─'*70}{C.RESET}")
            for i, err in enumerate(self.errors_captured[-20:], 1):  # آخر 20 خطأ
                short = err[:120] + ('...' if len(err) > 120 else '')
                print(f"  {C.RED}{i:>2}. {short}{C.RESET}")
            if len(self.errors_captured) > 20:
                print(f"  {C.DIM}... و {len(self.errors_captured) - 20} خطأ آخر في الملف{C.RESET}")
            print(f"{C.RED}{'─'*70}{C.RESET}")
        else:
            print(f"\n  {C.GREEN}✅ لم يتم اكتشاف أي أخطاء!{C.RESET}")

        print(f"\n  📁 السجل الكامل: {C.CYAN}{LOG_FILE}{C.RESET}")
        if self.errors_captured:
            print(f"  📁 الأخطاء فقط:  {C.CYAN}{ERRORS_FILE}{C.RESET}")
        print(f"{C.BOLD}{C.CYAN}{'='*70}{C.RESET}\n")

    def close(self):
        try:
            self.log_file.close()
            self.errors_file.close()
        except Exception:
            pass

    def run(self, command):
        """يشغّل الأمر ويعالج كل مخرجاته"""
        self.print_banner()

        try:
            # ✅ تشغيل مع إخراج بدون تخزين مؤقت
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                env=env,
            )

            # قراءة السطور واحداً واحداً
            for line in iter(process.stdout.readline, ''):
                if line:
                    self.process_line(line)
                if process.poll() is not None and not line:
                    break

            process.wait()
            return process.returncode

        except KeyboardInterrupt:
            print(f"\n\n{C.YELLOW}🛑 تم الإيقاف بواسطة المستخدم (Ctrl+C){C.RESET}")
            try:
                process.terminate()
                process.wait(timeout=5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
            return 130

        except FileNotFoundError:
            print(f"{C.RED}❌ لم يتم العثور على: {command[0]}{C.RESET}")
            return 1

        except Exception as e:
            print(f"{C.RED}❌ خطأ في run_server.py: {e}{C.RESET}")
            import traceback
            traceback.print_exc()
            return 1

        finally:
            self.print_summary()
            self.close()


def main():
    # فحص وجود الملف
    if not os.path.exists('attendance_server.py'):
        print(f"{C.RED}❌ attendance_server.py غير موجود!{C.RESET}")
        print(f"   شغّل السكربت من داخل مجلد المشروع")
        return 1

    # فحص Python
    print(f"{C.CYAN}🐍 Python: {sys.executable}{C.RESET}")
    print(f"{C.CYAN}📂 المجلد: {os.getcwd()}{C.RESET}")

    # تشغيل السيرفر
    cmd = [sys.executable, '-u', 'attendance_server.py']
    runner = ServerRunner()
    return runner.run(cmd)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}🛑 تم الإيقاف{C.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"{C.RED}❌ خطأ فادح: {e}{C.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)