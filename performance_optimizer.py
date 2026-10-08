"""
🚀 Performance Optimizer - محسّن أداء نظام الحضور
"""

import os
import time
import threading
import numpy as np
import cv2
from collections import OrderedDict, deque


def setup_environment():
    os.environ['OMP_NUM_THREADS'] = '4'
    os.environ['OPENBLAS_NUM_THREADS'] = '4'
    os.environ['MKL_NUM_THREADS'] = '4'
    os.environ['NUMEXPR_NUM_THREADS'] = '4'
    os.environ['VECLIB_MAXIMUM_THREADS'] = '4'
    os.environ['ORT_LOGGING_LEVEL'] = '3'
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
        "rtsp_transport;tcp|max_delay;500000|stimeout;3000000|"
        "buffer_size;1024000|fflags;nobuffer|flags;low_delay"
    )
    try:
        cv2.setNumThreads(2)
        cv2.setUseOptimized(True)
    except Exception:
        pass
    print("⚙️ [Optimizer] تم إعداد البيئة", flush=True)


class FaceCache:
    def __init__(self, ttl_seconds=2.0, max_size=50):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache = OrderedDict()
        self._lock = threading.Lock()
        self.stats = {'hits': 0, 'misses': 0}
   
    def get(self, key):
        now = time.time()
        with self._lock:
            if key in self._cache:
                ts, faces = self._cache[key]
                if now - ts < self.ttl:
                    self._cache.move_to_end(key)
                    self.stats['hits'] += 1
                    return faces, True
                del self._cache[key]
            self.stats['misses'] += 1
            return None, False
   
    def set(self, key, faces):
        with self._lock:
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (time.time(), faces)
   
    def get_stats(self):
        total = self.stats['hits'] + self.stats['misses']
        rate = (self.stats['hits'] / total * 100) if total > 0 else 0
        return {'hits': self.stats['hits'], 'misses': self.stats['misses'],
                'hit_rate': f"{rate:.1f}%", 'size': len(self._cache)}


class MotionDetector:
    def __init__(self, threshold=3000):
        self.threshold = threshold
        self._prev_frames = {}
        self._counters = {}
        self._lock = threading.Lock()
        self.stats = {'skipped': 0, 'processed': 0}
   
    def has_motion(self, key, frame, force_check_interval=20):
        try:
            small = cv2.resize(frame, (160, 120))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
        except Exception:
            return True
        with self._lock:
            prev = self._prev_frames.get(key)
            counter = self._counters.get(key, 0)
            self._counters[key] = (counter + 1) % force_check_interval
            if prev is None or counter == 0:
                self._prev_frames[key] = gray
                self.stats['processed'] += 1
                return True
            diff = cv2.absdiff(prev, gray)
            _, thresh = cv2.threshold(diff, 20, 255, cv2.THRESH_BINARY)
            motion_pixels = cv2.countNonZero(thresh)
            self._prev_frames[key] = gray
            if motion_pixels > self.threshold:
                self.stats['processed'] += 1
                return True
            self.stats['skipped'] += 1
            return False
   
    def get_stats(self):
        total = self.stats['skipped'] + self.stats['processed']
        save_pct = (self.stats['skipped'] / total * 100) if total > 0 else 0
        return {'skipped': self.stats['skipped'],
                'processed': self.stats['processed'],
                'savings': f"{save_pct:.1f}%"}


class DetectorRotator:
    def __init__(self, num_slots=3):
        self.num_slots = num_slots
        self._positions = {}
        self._lock = threading.Lock()
   
    def get_slot(self, key):
        with self._lock:
            pos = self._positions.get(key, 0)
            self._positions[key] = (pos + 1) % self.num_slots
            return pos


class FrameThrottler:
    def __init__(self, target_fps=2.0):
        self.target_fps = target_fps
        self.min_interval = 1.0 / target_fps
        self._last = {}
        self._lock = threading.Lock()
   
    def should_process(self, key):
        now = time.time()
        with self._lock:
            last = self._last.get(key, 0)
            if now - last >= self.min_interval:
                self._last[key] = now
                return True
            return False


class RequestCoalescer:
    def __init__(self, min_interval=3.0):
        self.min_interval = min_interval
        self._last = {}
        self._lock = threading.Lock()
        self.stats = {'accepted': 0, 'rejected': 0}
   
    def accept(self, key):
        now = time.time()
        with self._lock:
            last = self._last.get(key, 0)
            if now - last >= self.min_interval:
                self._last[key] = now
                self.stats['accepted'] += 1
                return True
            self.stats['rejected'] += 1
            return False
   
    def get_stats(self):
        total = self.stats['accepted'] + self.stats['rejected']
        rate = (self.stats['rejected'] / total * 100) if total > 0 else 0
        return {'accepted': self.stats['accepted'],
                'rejected': self.stats['rejected'],
                'rejection_rate': f"{rate:.1f}%"}


class PerformanceMonitor:
    def __init__(self, report_interval=120):
        self.report_interval = report_interval
        self.metrics = {}
        self._lock = threading.Lock()
        self._start_time = time.time()
   
    def record(self, name, value_ms):
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=100)
            self.metrics[name].append(value_ms)
   
    def get_report(self):
        with self._lock:
            report = {}
            for name, values in self.metrics.items():
                if values:
                    arr = list(values)
                    report[name] = {
                        'avg_ms': round(sum(arr) / len(arr), 1),
                        'min_ms': round(min(arr), 1),
                        'max_ms': round(max(arr), 1),
                        'samples': len(arr)
                    }
            return report
   
    def print_report(self):
        report = self.get_report()
        if not report:
            return
        uptime = time.time() - self._start_time
        print(f"\n{'═'*60}", flush=True)
        print(f"📊 [Performance] uptime={uptime/60:.1f} min", flush=True)
        print(f"{'═'*60}", flush=True)
        for name, data in sorted(report.items()):
            print(f"   {name:25s} avg={data['avg_ms']:7.1f}ms "
                  f"min={data['min_ms']:6.1f} max={data['max_ms']:8.1f} "
                  f"n={data['samples']}", flush=True)
        print(f"{'═'*60}\n", flush=True)
   
    def start_auto_report(self):
        def _loop():
            while True:
                time.sleep(self.report_interval)
                try:
                    self.print_report()
                except Exception:
                    pass
        t = threading.Thread(target=_loop, daemon=True, name="PerfMonitor")
        t.start()


class Timer:
    def __init__(self, monitor, name):
        self.monitor = monitor
        self.name = name
        self.start = 0
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, *args):
        elapsed = (time.time() - self.start) * 1000
        if self.monitor:
            self.monitor.record(self.name, elapsed)


# ═══ Singletons ═══
motion_detector = None
detector_rotator = None
frame_throttler = None
exam_request_coalescer = None
exam_perf_monitor = None


def init_optimizers():
    global motion_detector, detector_rotator, frame_throttler
    global exam_request_coalescer, exam_perf_monitor
    motion_detector = MotionDetector(threshold=3000)
    detector_rotator = DetectorRotator(num_slots=3)
    frame_throttler = FrameThrottler(target_fps=2.0)
    exam_request_coalescer = RequestCoalescer(min_interval=4.0)
    exam_perf_monitor = PerformanceMonitor(report_interval=120)
    exam_perf_monitor.start_auto_report()
    print("✅ [Optimizer] تم تهيئة المحسّنات", flush=True)


def get_optimizer_stats():
    stats = {}
    if motion_detector:
        stats['motion'] = motion_detector.get_stats()
    if exam_request_coalescer:
        stats['coalescer'] = exam_request_coalescer.get_stats()
    if exam_perf_monitor:
        stats['performance'] = exam_perf_monitor.get_report()
    return stats
