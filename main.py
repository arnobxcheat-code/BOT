"""
PRIME NOX v3.3 - Single File Edition
- Single video link downloads only that video/audio (no accidental playlist/mix spam)
- Zero thumbnails (no thumbnail download or embedding)
- Improved PC audio codec/format compatibility via FFmpeg
- Bug fixes & cleanup improvements
"""
import ctypes
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.parse
import urllib.request
import webbrowser
import zipfile

try:
  import yt_dlp
except ImportError:
  print("Installing yt-dlp...")
  subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"])
  import yt_dlp

try:
  from PIL import Image, ImageDraw, ImageTk
  import pystray

  HAS_TRAY = True
except ImportError:
  HAS_TRAY = False

try:
  import winreg

  HAS_WINREG = True
except ImportError:
  HAS_WINREG = False


# ============================================================
# CONFIG
# ============================================================
APP_NAME = "PRIME NOX"
APP_VERSION = "3.3"
META_DIR = os.path.join(os.path.expanduser("~"), ".prime_nox")
EXT_DIR = os.path.join(META_DIR, "browser_extension")
STARTUP_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

THEMES = {
    "Midnight": {
        "primary": "#6366F1",
        "primary_hover": "#818CF8",
        "accent": "#8B5CF6",
        "accent_hover": "#A78BFA",
        "action": "#EC4899",
        "action_hover": "#F472B6",
        "success": "#10B981",
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "bg": "#08080D",
        "surface": "#12121C",
        "surface_2": "#1A1A29",
        "border": "#363654",
        "box_border": "#000000",
        "text": "#FFFFFF",
        "text_muted": "#9CA3AF",
        "progress": "#6366F1",
        "bar": "#10B981",
        "particles": ["#6366F1", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"],
    },
    "Black & White": {
        "primary": "#E4E4E7",
        "primary_hover": "#FFFFFF",
        "accent": "#A1A1AA",
        "accent_hover": "#D4D4D8",
        "action": "#F4F4F5",
        "action_hover": "#FFFFFF",
        "success": "#FFFFFF",
        "danger": "#A1A1AA",
        "warning": "#D4D4D8",
        "bg": "#050505",
        "surface": "#101010",
        "surface_2": "#1B1B1B",
        "border": "#52525B",
        "box_border": "#000000",
        "text": "#FFFFFF",
        "text_muted": "#A1A1AA",
        "progress": "#FFFFFF",
        "bar": "#E4E4E7",
        "particles": ["#FFFFFF", "#D4D4D8", "#A1A1AA", "#71717A"],
    },
    "Cyber": {
        "primary": "#FF0080",
        "primary_hover": "#FF4DA6",
        "accent": "#00FFFF",
        "accent_hover": "#66FFFF",
        "action": "#FF6B00",
        "action_hover": "#FF9933",
        "success": "#00FF88",
        "danger": "#FF0044",
        "warning": "#FFD700",
        "bg": "#08080D",
        "surface": "#12121C",
        "surface_2": "#1B1B2B",
        "border": "#4C2461",
        "box_border": "#000000",
        "text": "#FFFFFF",
        "text_muted": "#9CA3AF",
        "progress": "#00FFFF",
        "bar": "#FF0080",
        "particles": ["#FF0080", "#00FFFF", "#FF6B00", "#00FF88", "#FFD700"],
    },
    "Ocean": {
        "primary": "#0EA5E9",
        "primary_hover": "#38BDF8",
        "accent": "#2563EB",
        "accent_hover": "#3B82F6",
        "action": "#E91E63",
        "action_hover": "#F43F5E",
        "success": "#10B981",
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "bg": "#08080D",
        "surface": "#111622",
        "surface_2": "#182234",
        "border": "#2B4C7E",
        "box_border": "#000000",
        "text": "#FFFFFF",
        "text_muted": "#9CA3AF",
        "progress": "#38BDF8",
        "bar": "#00E676",
        "particles": ["#0EA5E9", "#38BDF8", "#34D399", "#F472B6", "#818CF8"],
    },
    "Emerald": {
        "primary": "#10B981",
        "primary_hover": "#34D399",
        "accent": "#059669",
        "accent_hover": "#34D399",
        "action": "#16A34A",
        "action_hover": "#4ADE80",
        "success": "#22C55E",
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "bg": "#080D0A",
        "surface": "#0E1A13",
        "surface_2": "#15291E",
        "border": "#27543B",
        "box_border": "#000000",
        "text": "#FFFFFF",
        "text_muted": "#9CA3AF",
        "progress": "#34D399",
        "bar": "#00E676",
        "particles": ["#10B981", "#34D399", "#2DD4BF", "#A3E635", "#38BDF8"],
    },
    "Matrix": {
        "primary": "#00FF41",
        "primary_hover": "#4DFF7A",
        "accent": "#39FF14",
        "accent_hover": "#6BFF4F",
        "action": "#00FF88",
        "action_hover": "#4DFFA8",
        "success": "#00FF41",
        "danger": "#FF0044",
        "warning": "#FFD700",
        "bg": "#000000",
        "surface": "#091409",
        "surface_2": "#102110",
        "border": "#255425",
        "box_border": "#000000",
        "text": "#00FF41",
        "text_muted": "#4D7A4D",
        "progress": "#00FF41",
        "bar": "#39FF14",
        "particles": ["#00FF41", "#39FF14", "#4DFF7A", "#00FF88", "#7FFF00"],
    },
}

DEFAULT_SETTINGS = {
    "theme": "Cyber",
    "dark_mode": True,
    "always_on_top": False,
    "particle_type": "Network",
    "run_at_startup": False,
    "extension_auto_prompt": True,
    "duplicate_guard": True,
    "auto_organize": False,
    "browser_cookies": "None",
    "notifications": True,
    "notifications_enabled": True,
    "button_animation": True,
    "glow_effect": True,
    "auto_update_ytdlp": True,
    "auto_retry": True,
    "clipboard_monitor": False,
    "sound_effects": True,
    "download_dir": "",
    "bandwidth_limit": 0,
    "max_media_limit": 0,
    "filename_template": "%(title).80s.%(ext)s",
    "auto_cleanup_days": 0,
    "proxy": "",
    "toast_notifications": True,
    "notification_position": "bottom-right",
    "concurrent_downloads": 1,
    "minimize_to_tray": True,
    "start_minimized": False,
    "embed_subtitles": False,
    "embed_thumbnail": False,
    "embed_metadata": True,
    "sponsorblock": False,
}

VIDEO_QUALITIES = ["Best", "4K", "2K", "1080p", "720p", "480p", "360p"]
AUDIO_QUALITIES = ["Best", "320k", "256k", "192k", "128k"]
VIDEO_FORMATS = ["MP4", "WEBM", "MKV"]
AUDIO_FORMATS = ["MP3", "M4A", "WAV", "FLAC", "MP4"]


# ============================================================
# UTILITIES
# ============================================================
def _no_console():
  if os.name != "nt":
    return
  try:
    h = ctypes.windll.kernel32.GetConsoleWindow()
    if h:
      ctypes.windll.user32.ShowWindow(h, 0)
  except Exception:
    pass
  orig = subprocess.Popen
  CNW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

  class NP(orig):

    def __init__(self, *a, **kw):
      kw["creationflags"] = kw.get("creationflags", 0) | CNW
      if "startupinfo" not in kw or kw["startupinfo"] is None:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kw["startupinfo"] = si
      super().__init__(*a, **kw)

  subprocess.Popen = NP


_no_console()


def ensure_meta():
  os.makedirs(META_DIR, exist_ok=True)


def path_settings():
  return os.path.join(META_DIR, ".settings.json")


def path_history():
  history_dir = r"D:\Downlod History"
  try:
    os.makedirs(history_dir, exist_ok=True)
    return os.path.join(history_dir, ".history.json")
  except Exception:
    ensure_meta()
    return os.path.join(META_DIR, ".history.json")


def path_favorites():
  return os.path.join(META_DIR, ".favorites.json")


def load_json(p, d=None):
  try:
    with open(p, "r", encoding="utf-8") as f:
      return json.load(f)
  except Exception:
    return d if d is not None else {}


def save_json(p, data):
  try:
    parent = os.path.dirname(p)
    if parent:
      os.makedirs(parent, exist_ok=True)
    tmp_path = p + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
      json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, p)
  except Exception:
    pass


def load_settings():
  cfg = dict(DEFAULT_SETTINGS)
  data = load_json(path_settings(), {})
  if isinstance(data, dict):
    for k, v in DEFAULT_SETTINGS.items():
      if k in data and isinstance(data[k], type(v)):
        cfg[k] = data[k]
    if data.get("theme") in THEMES:
      cfg["theme"] = data["theme"]
  cfg["embed_thumbnail"] = False
  return cfg


def save_settings(cfg):
  cfg["embed_thumbnail"] = False
  save_json(path_settings(), cfg)


def resolve_theme(settings):
  base = dict(THEMES.get(settings.get("theme", "Midnight"), THEMES["Midnight"]))
  base["box_border"] = "#000000"
  if settings.get("theme") == "Black & White":
    if not settings.get("dark_mode", True):
      base.update({
          "bg": "#F4F4F5",
          "surface": "#FFFFFF",
          "surface_2": "#E4E4E7",
          "border": "#3F3F46",
          "box_border": "#000000",
          "text": "#09090B",
          "text_muted": "#3F3F46",
          "primary": "#18181B",
          "primary_hover": "#27272A",
          "accent": "#27272A",
          "accent_hover": "#3F3F46",
          "action": "#09090B",
          "action_hover": "#27272A",
          "success": "#18181B",
          "danger": "#3F3F46",
          "warning": "#27272A",
          "progress": "#09090B",
          "bar": "#18181B",
          "particles": ["#09090B", "#27272A", "#52525B", "#71717A"],
      })
  elif not settings.get("dark_mode", True):
    base.update({
        "bg": "#F3F4F6",
        "surface": "#FFFFFF",
        "surface_2": "#E5E7EB",
        "border": "#6B7280",
        "box_border": "#000000",
        "text": "#111827",
        "text_muted": "#4B5563",
    })
  return base


def set_windows_startup(enabled):
  if os.name != "nt" or not HAS_WINREG:
    return False
  try:
    cmd = (
        f'"{sys.executable}" "{os.path.abspath(__file__)}" --background'
        if not getattr(sys, "frozen", False)
        else f'"{sys.executable}" --background'
    )
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, STARTUP_RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
      if enabled:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
      else:
        try:
          winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
          pass
    return True
  except Exception:
    return False


def ensure_extension_package():
  os.makedirs(EXT_DIR, exist_ok=True)
  manifest = {
      "manifest_version": 3,
      "name": "PRIME NOX Downloader Bridge",
      "version": "3.3",
      "description": "Send links directly to PRIME NOX local downloader",
      "permissions": ["contextMenus", "activeTab", "scripting"],
      "host_permissions": ["http://127.0.0.1:5678/*"],
      "background": {"service_worker": "background.js"},
      "action": {"default_title": "Send to PRIME NOX"},
  }
  bg_js = """
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "prime_nox_dl",
    title: "Download with PRIME NOX",
    contexts: ["link", "video", "audio", "page"]
  });
});

async function sendToPrimeNox(url) {
  try {
    await fetch("http://127.0.0.1:5678/download", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url})
    });
  } catch (e) {}
}

chrome.contextMenus.onClicked.addListener((info, tab) => {
  const target = info.linkUrl || info.srcUrl || info.pageUrl || (tab && tab.url);
  if (target) sendToPrimeNox(target);
});

chrome.action.onClicked.addListener((tab) => {
  if (tab && tab.url) sendToPrimeNox(tab.url);
});
"""
  with open(
      os.path.join(EXT_DIR, "manifest.json"), "w", encoding="utf-8"
  ) as f:
    json.dump(manifest, f, indent=2)
  with open(
      os.path.join(EXT_DIR, "background.js"), "w", encoding="utf-8"
  ) as f:
    f.write(bg_js.strip())
  return EXT_DIR


def get_download_dir(s):
  d = (s.get("download_dir") or "").strip()
  if d:
    try:
      os.makedirs(d, exist_ok=True)
      if os.path.isdir(d):
        return d
    except Exception:
      pass
  fallback = os.path.join(os.path.expanduser("~"), "Downloads", "PRIME_NOX")
  os.makedirs(fallback, exist_ok=True)
  return fallback


def get_mode_dir(base, mode):
  sub = "Audio" if (mode or "").lower() == "audio" else "Video"
  t = os.path.join(base, sub)
  os.makedirs(t, exist_ok=True)
  return t


def format_bytes(b):
  for u in ["B", "KB", "MB", "GB", "TB"]:
    if b < 1024:
      return f"{b:.1f} {u}"
    b /= 1024
  return f"{b:.1f} PB"


def free_space(p):
  try:
    return shutil.disk_usage(p).free
  except Exception:
    return 0


def hex_to_rgb(h):
  c = h.lstrip("#")
  return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
  return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"


def lerp(c1, c2, t):
  r1, g1, b1 = hex_to_rgb(c1)
  r2, g2, b2 = hex_to_rgb(c2)
  return rgb_to_hex(
      int(r1 + (r2 - r1) * t), int(g1 + (g2 - g1) * t), int(b1 + (b2 - b1) * t)
  )


def apply_dark_title(hwnd, dark=True):
  if os.name != "nt" or not hwnd:
    return
  try:
    dwm = ctypes.windll.dwmapi
    use_dark = ctypes.c_int(1 if dark else 0)
    for attr in (20, 19):
      try:
        if (
            dwm.DwmSetWindowAttribute(
                hwnd,
                ctypes.c_int(attr),
                ctypes.byref(use_dark),
                ctypes.sizeof(use_dark),
            )
            == 0
        ):
          break
      except Exception:
        continue
    if dark:
      black = ctypes.c_int(0x00000000)
      white = ctypes.c_int(0x00FFFFFF)
      for attr, color in ((35, black), (34, black), (36, white)):
        try:
          dwm.DwmSetWindowAttribute(
              hwnd,
              ctypes.c_int(attr),
              ctypes.byref(color),
              ctypes.sizeof(color),
          )
        except Exception:
          pass
    else:
      default_color = ctypes.c_int(0xFFFFFFFF)
      for attr in (35, 34, 36):
        try:
          dwm.DwmSetWindowAttribute(
              hwnd,
              ctypes.c_int(attr),
              ctypes.byref(default_color),
              ctypes.sizeof(default_color),
          )
        except Exception:
          pass
  except Exception:
    pass


def find_adb():
  p = shutil.which("adb")
  if p:
    return p
  la = os.environ.get("LOCALAPPDATA") or ""
  for c in [
      os.path.join(la, "Android", "Sdk", "platform-tools", "adb.exe"),
      r"C:\Android\platform-tools\adb.exe",
      r"C:\Program Files\Nox\bin\adb.exe",
      r"C:\Program Files\LDPlayer\LDPlayer9\adb.exe",
  ]:
    if c and os.path.isfile(c):
      return c
  return None


def find_ffmpeg_dir():
  ff = shutil.which("ffmpeg")
  if ff:
    return os.path.dirname(ff)
  candidates = [
      r"C:\ffmpeg\bin",
      r"C:\Program Files\ffmpeg\bin",
      os.path.join(os.path.expanduser("~"), "ffmpeg", "bin"),
  ]
  la = os.environ.get("LOCALAPPDATA") or ""
  winget_root = os.path.join(la, "Microsoft", "WinGet", "Packages")
  if os.path.isdir(winget_root):
    try:
      for root, _, files in os.walk(winget_root):
        if "ffmpeg.exe" in [f.lower() for f in files]:
          return root
    except Exception:
      pass
  for c in candidates:
    if c and os.path.isfile(os.path.join(c, "ffmpeg.exe")):
      return c
  return None


def check_ytdlp_update():
  cur = getattr(yt_dlp.version, "__version__", "")
  try:
    req = urllib.request.Request(
        "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
        headers={"User-Agent": BROWSER_UA},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
      data = json.loads(r.read().decode("utf-8", errors="ignore"))
    tag = str(data.get("tag_name") or "").strip().lstrip("v")
    if not tag or tag == cur:
      return False, cur, tag or cur
    if not getattr(sys, "frozen", False):
      p = subprocess.run(
          [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
          capture_output=True,
          text=True,
          timeout=180,
      )
      if p.returncode == 0:
        return True, cur, tag
  except Exception:
    pass
  return False, cur, cur


def cleanup_old_files(directory, days):
  if days <= 0:
    return 0
  cutoff = time.time() - days * 86400
  removed = 0
  try:
    for root, _, files in os.walk(directory):
      for fn in files:
        fp = os.path.join(root, fn)
        try:
          if os.path.getmtime(fp) < cutoff:
            os.remove(fp)
            removed += 1
        except Exception:
          pass
  except Exception:
    pass
  return removed


def trigger_power_action(action):
  if os.name != "nt":
    return
  if action == "Shutdown":
    subprocess.Popen(["shutdown", "/s", "/t", "15"])
  elif action == "Sleep":
    subprocess.Popen(
        ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"]
    )


# ============================================================
# WIDGETS
# ============================================================
class ParticleBG(tk.Canvas):

  def __init__(self, parent, theme, ptype="Network"):
    super().__init__(parent, bg=theme["bg"], highlightthickness=0, bd=0)
    self.theme = theme
    self.ptype = ptype
    self.particles = []
    self._running = True
    self._job = None
    self._canvas_w = 540
    self._canvas_h = 560
    self.bind("<Configure>", self._resize)
    self._init(540, 560)
    self._tick()

  def set_theme(self, theme, ptype=None):
    self.theme = theme
    if ptype:
      self.ptype = ptype
    for p in self.particles:
      p["color"] = random.choice(theme["particles"])
    self.config(bg=theme["bg"])

  def _init(self, w, h):
    w = max(200, int(w))
    h = max(200, int(h))
    self._canvas_w = w
    self._canvas_h = h
    self.particles = []
    for _ in range(36):
      a = random.uniform(0, 2 * math.pi)
      s = random.uniform(0.35, 0.85)
      self.particles.append({
          "x": random.uniform(8, w - 8),
          "y": random.uniform(8, h - 8),
          "vx": math.cos(a) * s,
          "vy": math.sin(a) * s,
          "r": random.uniform(1.6, 3.1),
          "phase": random.uniform(0, 2 * math.pi),
          "color": random.choice(self.theme["particles"]),
      })

  def _resize(self, e):
    w, h = max(1, e.width), max(1, e.height)
    if w > 100 and h > 100:
      old_w = max(1, self._canvas_w)
      old_h = max(1, self._canvas_h)
      self._canvas_w = w
      self._canvas_h = h
      if not self.particles:
        self._init(w, h)
        return
      for p in self.particles:
        p["x"] = max(8.0, min(w - 8.0, (p["x"] / old_w) * w))
        p["y"] = max(8.0, min(h - 8.0, (p["y"] / old_h) * h))

  def _star(self, cx, cy, r, c):
    inner = max(0.8, r * 0.42)
    pts = []
    for i in range(10):
      a = -math.pi / 2 + i * (math.pi / 5)
      rad = r if i % 2 == 0 else inner
      pts.extend([cx + math.cos(a) * rad, cy + math.sin(a) * rad])
    self.create_polygon(pts, fill=c, outline="")

  def _tick(self):
    if not self._running:
      return
    self.delete("all")
    if self.ptype == "None":
      self._job = self.after(120, self._tick)
      return
    w = self.winfo_width()
    h = self.winfo_height()
    if w <= 1 or h <= 1:
      w, h = self._canvas_w, self._canvas_h
    for p in self.particles:
      p["x"] += p["vx"]
      p["y"] += p["vy"]
      p["phase"] += 0.06
      if p["x"] < 4:
        p["x"] = 4
        p["vx"] = abs(p["vx"])
      elif p["x"] > w - 4:
        p["x"] = w - 4
        p["vx"] = -abs(p["vx"])
      if p["y"] < 4:
        p["y"] = 4
        p["vy"] = abs(p["vy"])
      elif p["y"] > h - 4:
        p["y"] = h - 4
        p["vy"] = -abs(p["vy"])
    if self.ptype == "Network":
      md = 115.0
      n = len(self.particles)
      for i in range(n):
        p1 = self.particles[i]
        for j in range(i + 1, n):
          p2 = self.particles[j]
          d = math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])
          if d < md:
            alpha = 1 - d / md
            b = hex_to_rgb(self.theme["border"])
            c = hex_to_rgb(p1["color"])
            m = tuple(
                int(b[k] + (c[k] - b[k]) * alpha * 0.45) for k in range(3)
            )
            self.create_line(
                p1["x"], p1["y"], p2["x"], p2["y"], fill=rgb_to_hex(*m), width=1
            )
    for p in self.particles:
      pulse = 0.78 + 0.32 * math.sin(p["phase"])
      r = max(1.2, p["r"] * pulse)
      if self.ptype == "Stars":
        self._star(p["x"], p["y"], r * 1.5, p["color"])
      elif self.ptype == "Bubbles":
        self.create_oval(
            p["x"] - r * 2.1,
            p["y"] - r * 2.1,
            p["x"] + r * 2.1,
            p["y"] + r * 2.1,
            outline=p["color"],
            width=1,
        )
      else:
        self.create_oval(
            p["x"] - r,
            p["y"] - r,
            p["x"] + r,
            p["y"] + r,
            fill=p["color"],
            outline="",
        )
    self._job = self.after(35, self._tick)

  def stop(self):
    self._running = False
    if self._job:
      self.after_cancel(self._job)


class RoundedBtn(tk.Canvas):

  def __init__(
      self,
      parent,
      fill,
      outline,
      hover,
      radius=7,
      height=28,
      width=None,
      command=None,
      animate=True,
  ):
    kw = dict(
        bg=parent.cget("bg"), highlightthickness=0, bd=0, height=height
    )
    if width:
      kw["width"] = width
    super().__init__(parent, **kw)
    self.fill = fill
    self.default_fill = fill
    self.hover_fill = hover
    self.outline = outline
    self.radius = radius
    self.command = command
    self._enabled = True
    self._animate = animate
    self._anim_job = None
    self._label_widget = None

    self.bind("<Configure>", self._draw)
    if command:
      self.config(cursor="hand2")
      self.bind("<ButtonPress-1>", self._press)
      self.bind("<Enter>", self._enter)
      self.bind("<Leave>", self._leave)

  def attach_label(self, lbl):
    self._label_widget = lbl
    if self.command:
      lbl.config(cursor="hand2")
      lbl.bind("<ButtonPress-1>", self._press)
      lbl.bind("<Enter>", self._enter)
      lbl.bind("<Leave>", self._leave)

  def _enter(self, _=None):
    if self._enabled and self.command:
      self.fill = self.hover_fill
      self._draw()
      if self._label_widget:
        try:
          self._label_widget.config(bg=self.hover_fill)
        except Exception:
          pass

  def _leave(self, _=None):
    if self._enabled and self.command:
      self.fill = self.default_fill
      self._draw()
      if self._label_widget:
        try:
          self._label_widget.config(bg=self.default_fill)
        except Exception:
          pass

  def _press(self, _=None):
    if not self._enabled or not self.command:
      return "break"
    if self._animate:
      self._ripple()
    self.command()
    return "break"

  def _ripple(self):
    if self._anim_job:
      self.after_cancel(self._anim_job)
    self.delete("ripple")
    w, h = self.winfo_width(), self.winfo_height()
    if w < 5 or h < 5:
      return
    cx, cy = w / 2, h / 2
    max_r = max(w, h) * 0.65
    steps = 5

    def step(i):
      self.delete("ripple")
      if i > steps:
        self._anim_job = None
        return
      r = 3 + (max_r - 3) * (i / steps)
      c = "#FFFFFF" if i <= 2 else self.outline
      self.create_oval(
          cx - r,
          cy - r,
          cx + r,
          cy + r,
          outline=c,
          width=2 if i < steps else 1,
          tags="ripple",
      )
      self._anim_job = self.after(16, lambda: step(i + 1))

    step(1)

  def set_colors(self, fill=None, outline=None, hover=None, enabled=True):
    self._enabled = enabled
    if fill:
      self.fill = fill
      self.default_fill = fill
    if outline:
      self.outline = outline
    if hover:
      self.hover_fill = hover
    self.config(cursor="hand2" if (self.command and enabled) else "")
    if self._label_widget:
      self._label_widget.config(
          cursor="hand2" if (self.command and enabled) else "",
          bg=self.default_fill,
      )
    self._draw()

  def _rr(self, x1, y1, x2, y2, r):
    r = min(r, (x2 - x1) // 2, (y2 - y1) // 2)
    return [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]

  def _draw(self, _=None):
    self.delete("bg")
    w, h = self.winfo_width(), self.winfo_height()
    if w < 4 or h < 4:
      return
    pts = self._rr(1, 1, w - 1, h - 1, self.radius)
    self.create_polygon(
        pts,
        smooth=True,
        splinesteps=14,
        fill=self.fill,
        outline=self.outline,
        width=1,
        tags="bg",
    )
    self.tag_lower("bg")


class Toast:
  _active = []
  enabled = True
  position = "bottom-right"

  @classmethod
  def show(
      cls, root, title, msg, accent="#10B981", bg="#141420", duration=2400
  ):
    if not cls.enabled:
      return None
    try:
      w = tk.Toplevel(root)
      w.overrideredirect(True)
      w.attributes("-topmost", True)
      try:
        w.attributes("-alpha", 0.96)
      except Exception:
        pass
      root.update_idletasks()
      screen_w = root.winfo_screenwidth()
      screen_h = root.winfo_screenheight()
      pos = getattr(cls, "position", "bottom-right")
      x_right = max(0, screen_w - 286)
      x_left = 8
      y_top = 8 + (len(cls._active) * 66)
      y_bottom = max(0, screen_h - 72 - (len(cls._active) * 66))
      if pos == "top-left":
        rx, ry = x_left, y_top
      elif pos == "bottom-left":
        rx, ry = x_left, y_bottom
      elif pos == "top-right":
        rx, ry = x_right, y_top
      else:
        rx, ry = x_right, y_bottom
      w.geometry(f"278x62+{rx}+{ry}")
      w.configure(bg=bg)
      f = tk.Frame(w, bg=bg, padx=7, pady=5)
      f.pack(fill="both", expand=True)
      tk.Frame(f, bg=accent, width=3).pack(
          side="left", fill="y", padx=(0, 7)
      )
      t = tk.Frame(f, bg=bg)
      t.pack(side="left", fill="both", expand=True)
      tk.Label(
          t,
          text=title,
          font=("Segoe UI", 9, "bold"),
          bg=bg,
          fg=accent,
          anchor="w",
      ).pack(fill="x")
      tk.Label(
          t,
          text=clean_str(msg)[:55],
          font=("Segoe UI", 8),
          bg=bg,
          fg="#E5E7EB",
          anchor="w",
          wraplength=225,
          justify="left",
      ).pack(fill="x")
      cls._active.append(w)
      w.after(duration, lambda: cls._close(w))
    except Exception:
      pass

  @classmethod
  def _close(cls, w):
    try:
      w.destroy()
    except Exception:
      pass
    if w in cls._active:
      cls._active.remove(w)


class SpeedGraph(tk.Canvas):

  def __init__(self, parent, bg, color):
    super().__init__(parent, bg=bg, highlightthickness=0, bd=0, height=34)
    self.color = color
    self.data = []
    self.max_points = 60

  def add(self, mbps):
    self.data.append(mbps)
    if len(self.data) > self.max_points:
      self.data.pop(0)
    self._draw()

  def set_color(self, c):
    self.color = c
    self._draw()

  def _draw(self):
    self.delete("all")
    if not self.data:
      return
    w, h = self.winfo_width(), self.winfo_height()
    if w < 10 or h < 10:
      return
    canvas_bg = self.cget("bg")
    mx = max(self.data + [1.0])
    pts = []
    for i, v in enumerate(self.data):
      x = (i / max(1, self.max_points - 1)) * w
      y = h - (v / mx) * (h - 4) - 2
      pts.extend([x, y])
    if len(pts) >= 4:
      fill_pts = [0, h] + pts + [w, h]
      self.create_polygon(
          fill_pts, fill=lerp(self.color, canvas_bg, 0.7), outline=""
      )
      self.create_line(pts, fill=self.color, width=2, smooth=True)


# ============================================================
# QUEUE & ENGINE
# ============================================================
class QueueItem:

  def __init__(
      self,
      id,
      url,
      mode,
      quality,
      fmt,
      title="Fetching...",
      clip_range=None,
      noplaylist=True,
  ):
    self.id = id
    self.url = url
    self.mode = mode
    self.quality = quality
    self.format = fmt
    self.title = title
    self.clip_range = clip_range
    self.noplaylist = noplaylist
    self.status = "queued"
    self.progress = 0.0
    self.speed = ""
    self.eta = ""
    self.error = ""
    self.added_at = time.time()


class DownloadQueue:

  def __init__(self):
    self.items = []
    self.lock = threading.Lock()
    self._next_id = 1
    self.paused = False

  def add(
      self, url, mode, quality, fmt, clip_range=None, noplaylist=True
  ):
    with self.lock:
      item = QueueItem(
          self._next_id,
          url,
          mode,
          quality,
          fmt,
          clip_range=clip_range,
          noplaylist=noplaylist,
      )
      self._next_id += 1
      self.items.append(item)
      return item.id

  def update(self, id, **kw):
    with self.lock:
      for i in self.items:
        if i.id == id:
          for k, v in kw.items():
            setattr(i, k, v)
          break

  def remove(self, id):
    with self.lock:
      self.items = [i for i in self.items if i.id != id]

  def all(self):
    with self.lock:
      return list(self.items)

  def next_queued(self):
    with self.lock:
      for i in self.items:
        if i.status == "queued":
          return i
    return None

  def has_pending(self):
    with self.lock:
      return any(i.status in ("queued", "downloading") for i in self.items)

  def clear_done(self):
    with self.lock:
      self.items = [
          i for i in self.items if i.status not in ("completed", "failed")
      ]


def parse_time_sec(ts):
  ts = (ts or "").strip()
  if not ts:
    return None
  parts = ts.split(":")
  try:
    vals = [float(x) for x in parts]
    if len(vals) == 1:
      return vals[0]
    if len(vals) == 2:
      return vals[0] * 60 + vals[1]
    if len(vals) == 3:
      return vals[0] * 3600 + vals[1] * 60 + vals[2]
  except ValueError:
    return None
  return None


def clean_str(v, fb="--"):
  if not v:
    return fb
  c = re.sub(
      r"\x1b\[[0-9;]*m|\[\d+(?:;\d+)*m|\[\d+[A-Za-z]", "", str(v)
  ).strip()
  return c or fb


def build_ydl_opts(
    item, settings, download_dir, hook, safe_mode=False, has_ffmpeg=True
):
  target = get_mode_dir(download_dir, item.mode)
  if settings.get("auto_organize", False):
    tmpl = os.path.join(
        "%(uploader,channel|General).40s",
        settings.get("filename_template", "%(title).80s.%(ext)s"),
    )
  else:
    tmpl = settings.get("filename_template", "%(title).80s.%(ext)s")
  outtmpl = os.path.join(target, tmpl)

  is_audio = (item.mode or "").lower() == "audio"

  opts = {
      "outtmpl": outtmpl,
      "noplaylist": bool(getattr(item, "noplaylist", True)),
      "ignoreerrors": False,
      "progress_hooks": [hook],
      "concurrent_fragment_downloads": 2 if safe_mode else 4,
      "buffersize": 1024 * 1024,
      "http_chunk_size": 5 * 1024 * 1024 if safe_mode else 10 * 1024 * 1024,
      "retries": 4,
      "fragment_retries": 4,
      "skip_unavailable_fragments": True,
      "keepvideo": False,
      "writethumbnail": False,
      "embedthumbnail": False,
      "quiet": True,
      "no_warnings": True,
      "nocolor": True,
      "restrictfilenames": True,
      "windowsfilenames": True,
  }

  ff_dir = find_ffmpeg_dir()
  if ff_dir:
    opts["ffmpeg_location"] = ff_dir
    has_ffmpeg = True

  bw = settings.get("bandwidth_limit", 0)
  if bw > 0:
    opts["ratelimit"] = bw * 1024
  if settings.get("proxy"):
    opts["proxy"] = settings["proxy"]
  bc = settings.get("browser_cookies", "None")
  if bc and bc != "None":
    opts["cookiesfrombrowser"] = (bc.lower(),)

  fmt_upper = (item.format or ("MP3" if is_audio else "MP4")).upper()
  if is_audio and fmt_upper not in AUDIO_FORMATS:
    fmt_upper = "MP3"
  if not is_audio and fmt_upper not in VIDEO_FORMATS:
    fmt_upper = "MP4"

  target_ext = fmt_upper.lower()
  postprocessors = []

  if not safe_mode and has_ffmpeg:
    if settings.get("embed_subtitles", False) and not is_audio:
      opts["writesubtitles"] = True
      opts["subtitleslangs"] = ["en", "bn"]
      postprocessors.append({"key": "FFmpegEmbedSubtitle"})
    if settings.get("embed_metadata", True) and target_ext != "wav":
      postprocessors.append({"key": "FFmpegMetadata"})
    if settings.get("sponsorblock", False):
      postprocessors.append({
          "key": "ModifyChapters",
          "remove_sponsor_segments": ["sponsor", "selfpromo"],
      })

  if item.clip_range and has_ffmpeg:
    s_sec, e_sec = item.clip_range
    if s_sec is not None and e_sec is not None and e_sec > s_sec:
      opts["download_ranges"] = yt_dlp.utils.download_range_func(
          None, [(s_sec, e_sec)]
      )
      opts["force_keyframes_at_cuts"] = True

  if is_audio:
    bm = {"320k": "320", "256k": "256", "192k": "192", "128k": "128"}
    br = bm.get(item.quality) or "192"
    opts["format"] = (
        "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio[ext=webm]/bestaudio/best"
    )
    if has_ffmpeg:
      if fmt_upper in ("MP3", "M4A", "WAV", "FLAC"):
        pp = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": target_ext,
        }
        if target_ext in ("mp3", "m4a"):
          pp["preferredquality"] = br
        postprocessors.append(pp)
      elif fmt_upper == "MP4":
        # Standard AAC in M4A container plays reliably on PC audio players
        postprocessors.append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
            "preferredquality": br,
        })
    if postprocessors:
      opts["postprocessors"] = postprocessors
    return opts

  ext = target_ext
  audio_ext = "m4a" if ext in ("mp4", "mkv") else "webm"
  hm = {
      "4K": 2160,
      "2K": 1440,
      "1080p": 1080,
      "720p": 720,
      "480p": 480,
      "360p": 360,
  }

  if safe_mode:
    if item.quality in hm:
      h = hm[item.quality]
      opts["format"] = f"best[height<={h}]/best"
    else:
      opts["format"] = "best"
  else:
    if item.quality in hm:
      h = hm[item.quality]
      fmt = (
          f"bestvideo[height<={h}][ext={ext}]+bestaudio[ext={audio_ext}]/"
          f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
      )
    else:
      fmt = (
          f"bestvideo[ext={ext}]+bestaudio[ext={audio_ext}]/"
          f"best[ext={ext}]/best"
      )
    opts["format"] = fmt
    if has_ffmpeg:
      opts["merge_output_format"] = ext
      opts["postprocessor_args"] = {
          "ffmpeg": ["-threads", "0", "-c", "copy", "-movflags", "+faststart"]
      }

  if postprocessors:
    opts["postprocessors"] = postprocessors
  return opts


def parse_pct(d):
  tot = d.get("total_bytes") or d.get("total_bytes_estimate")
  dl = d.get("downloaded_bytes")
  if tot and dl is not None and tot > 0:
    return max(0.0, min(100.0, (dl / tot) * 100.0))
  s = clean_str(d.get("_percent_str", "")).replace("%", "").strip()
  try:
    return max(0.0, min(100.0, float(s)))
  except ValueError:
    return 0.0


def get_video_info(url):
  try:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "nocolor": True,
        "noplaylist": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
      info = ydl.extract_info(url, download=False)
    return {
        "title": info.get("title", "Unknown"),
        "thumbnail": info.get("thumbnail", ""),
        "duration": info.get("duration", 0),
        "uploader": info.get("uploader", ""),
        "view_count": info.get("view_count", 0),
        "formats": len(info.get("formats", [])),
        "size_estimate": info.get("filesize")
        or info.get("filesize_approx")
        or 0,
        "url": url,
    }
  except Exception as e:
    return {"error": clean_str(str(e))}


NOTIFICATIONS_ENABLED = True


def safe_showinfo(*args, **kwargs):
  if NOTIFICATIONS_ENABLED:
    return messagebox.showinfo(*args, **kwargs)
  return None


def safe_showwarning(*args, **kwargs):
  if NOTIFICATIONS_ENABLED:
    return messagebox.showwarning(*args, **kwargs)
  return None


def safe_showerror(*args, **kwargs):
  if NOTIFICATIONS_ENABLED:
    return messagebox.showerror(*args, **kwargs)
  return None


# ============================================================
# MAIN APP
# ============================================================
class App:
  WIN_W, WIN_H, PROG_H = 430, 455, 520
  SPEED_DURATION_SEC = 30 * 60

  def __init__(self, root):
    self.root = root
    self.root.title(f"{APP_NAME} v{APP_VERSION}")
    self.root.geometry(f"{self.WIN_W}x{self.WIN_H}")
    self.root.resizable(False, False)

    ensure_meta()
    self.settings = load_settings()
    if self.settings.get("theme") == "Midnight":
      self.settings["theme"] = "Cyber"
      save_settings(self.settings)
    global NOTIFICATIONS_ENABLED
    NOTIFICATIONS_ENABLED = bool(
        self.settings.get(
            "notifications_enabled", self.settings.get("notifications", True)
        )
    )
    self.settings["notifications_enabled"] = NOTIFICATIONS_ENABLED
    self.settings["notifications"] = NOTIFICATIONS_ENABLED
    Toast.enabled = NOTIFICATIONS_ENABLED
    Toast.position = self.settings.get("notification_position", "bottom-right")
    self.theme = resolve_theme(self.settings)
    self.root.configure(bg=self.theme["bg"])
    self.root.attributes(
        "-topmost", bool(self.settings.get("always_on_top", False))
    )
    self.history = load_json(path_history(), [])
    self.favorites = load_json(path_favorites(), [])
    self.download_dir = get_download_dir(self.settings)

    self.queue = DownloadQueue()
    self._queue_processing_lock = threading.Lock()
    self.search_stop = threading.Event()
    self.search_running = False
    self.speed_testing = False
    self.speed_stop = threading.Event()
    self.installer_running = False
    self.active_page = "home"
    self.total_downloads = 0
    self.tray_icon = None
    self._display_speed = 0.0
    self._ext_prompt_open = False
    self._seen_browsers = set()
    self._bordered_boxes = []
    self.power_after_var = tk.StringVar(value="None")

    self.mode_var = tk.StringVar(value="video")
    self.quality_var = tk.StringVar(value="Best")
    self.format_var = tk.StringVar(value="MP4")

    self.bg = ParticleBG(root, self.theme, self.settings["particle_type"])
    self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)

    self._build_ui()
    self._apply_theme()
    self._refresh_dir()
    self._refresh_ready()
    self._refresh_queue_list()
    self._refresh_history_list()
    self._refresh_favorites_list()

    self.root.update_idletasks()
    self.bg._init(self.root.winfo_width(), self.root.winfo_height())
    try:
      apply_dark_title(
          self.root.winfo_id(), self.settings.get("dark_mode", True)
      )
    except Exception:
      pass

    self._bind_shortcuts()
    self._start_clipboard_monitor()
    self._start_browser_watcher()
    self._start_http_server()
    self._start_tray()

    if "--background" in sys.argv:
      self.root.withdraw()

    self.root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
    threading.Thread(target=self._queue_worker, daemon=True).start()
    threading.Thread(target=self._auto_update_worker, daemon=True).start()
    threading.Thread(target=self._cleanup_worker, daemon=True).start()

  def _register_box(self, box_widget, bg_key="surface"):
    self._bordered_boxes.append((box_widget, bg_key))
    return box_widget

  def _build_ui(self):
    t = self.theme
    self.top_bar = tk.Frame(self.root, bg=t["bg"])
    self.top_bar.pack(fill="x", padx=6, pady=(4, 3))

    self.logo_canvas = tk.Canvas(
        self.top_bar,
        width=28,
        height=28,
        bg=t["bg"],
        highlightthickness=0,
        bd=0,
    )
    self.logo_canvas.pack(side="left", padx=(0, 6))
    self._redraw_logo()

    self.title_lbl = tk.Label(
        self.top_bar,
        text=f"{APP_NAME} v{APP_VERSION}",
        font=("Segoe UI", 11, "bold"),
        bg=t["bg"],
        fg=t["text"],
    )
    self.title_lbl.pack(side="left")

    self.notification_btn = self._btn(
        self.top_bar,
        t["surface_2"],
        t["border"],
        t["surface"],
        self._toggle_notifications,
        width=32,
        height=26,
    )
    self.notification_btn.pack(side="right", padx=(0, 4))
    self.notification_lbl = self._lbl(
        self.notification_btn,
        "🔔" if NOTIFICATIONS_ENABLED else "🔕",
        t["surface_2"],
        9,
    )

    self.settings_btn = self._btn(
        self.top_bar,
        t["surface_2"],
        t["border"],
        t["surface"],
        lambda: self._switch_page("settings"),
        width=32,
        height=26,
    )
    self.settings_btn.pack(side="right")
    self.settings_lbl = self._lbl(self.settings_btn, "⚙", t["surface_2"], 9)

    self.speed_btn = self._btn(
        self.top_bar,
        t["success"],
        t["border"],
        "#059669",
        self._toggle_speed_page,
        width=32,
        height=26,
    )
    self.speed_btn.pack(side="right", padx=(0, 4))
    self.speed_lbl = self._lbl(self.speed_btn, "⚡", t["success"], 9)

    self.pin_btn = self._btn(
        self.top_bar,
        t["surface_2"],
        t["border"],
        t["surface"],
        self._toggle_pin,
        width=32,
        height=26,
    )
    self.pin_btn.pack(side="right", padx=(0, 4))
    self.pin_lbl = self._lbl(self.pin_btn, "📌", t["surface_2"], 9)

    self.counter_lbl = tk.Label(
        self.top_bar,
        text="📥 0",
        font=("Segoe UI", 9, "bold"),
        bg=t["bg"],
        fg=t["success"],
    )
    self.counter_lbl.pack(side="right", padx=(0, 8))

    self.tabs_bar = tk.Frame(self.root, bg=t["bg"])
    self.tabs_bar.pack(fill="x", padx=6, pady=(0, 3))

    self.tab_btns = {}
    for key, label in [
        ("home", "⬇ Home"),
        ("queue", "📋 Queue"),
        ("history", "📜 History"),
        ("favorites", "⭐ Favs"),
        ("tools", "🧰 Tools"),
        ("apk", "📦 APK"),
    ]:
      btn = self._btn(
          self.tabs_bar,
          t["surface"],
          t["border"],
          t["surface_2"],
          lambda k=key: self._switch_page(k),
          height=26,
          width=82,
      )
      btn.pack(side="left", padx=(0, 4))
      lbl = self._lbl(btn, label, t["surface"], 8)
      self.tab_btns[key] = (btn, lbl)

    self.container = tk.Frame(self.root, bg=t["bg"])
    self.container.pack(fill="both", expand=True, padx=6)

    self.pages = {
        "home": self._build_home(),
        "queue": self._build_queue(),
        "history": self._build_history(),
        "favorites": self._build_favorites(),
        "tools": self._build_tools_page(),
        "apk": self._build_apk(),
        "settings": self._build_settings_page(),
    }
    for p in self.pages.values():
      p.pack_forget()
    self.pages["home"].pack(fill="both", expand=True)
    self._update_tabs("home")

    self.progress_card = self._register_box(
        tk.Frame(
            self.root,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
        ),
        "surface",
    )
    pin = tk.Frame(self.progress_card, bg=t["surface"], padx=8, pady=6)
    pin.pack(fill="x")

    r1 = tk.Frame(pin, bg=t["surface"])
    r1.pack(fill="x", pady=(0, 3))
    self.status_var = tk.StringVar()
    tk.Label(
        r1,
        textvariable=self.status_var,
        font=("Segoe UI", 8, "bold"),
        bg=t["surface"],
        fg=t["success"],
        anchor="w",
    ).pack(side="left", fill="x", expand=True)
    self.percent_var = tk.StringVar(value="0.0%")
    tk.Label(
        r1,
        textvariable=self.percent_var,
        font=("Segoe UI", 9, "bold"),
        bg=t["surface"],
        fg=t["progress"],
    ).pack(side="right")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "PN.Horizontal.TProgressbar",
        troughcolor=t["surface_2"],
        background=t["bar"],
        bordercolor=t["border"],
        lightcolor=t["bar"],
        darkcolor=t["bar"],
        thickness=8,
    )
    self.progress_bar = ttk.Progressbar(
        pin,
        style="PN.Horizontal.TProgressbar",
        orient="horizontal",
        mode="determinate",
        maximum=100,
        value=0,
    )
    self.progress_bar.pack(fill="x")

    self.detail_var = tk.StringVar()
    tk.Label(
        pin,
        textvariable=self.detail_var,
        font=("Segoe UI", 7),
        bg=t["surface"],
        fg=t["text_muted"],
        anchor="w",
    ).pack(fill="x", pady=(3, 0))

    self.speed_graph = SpeedGraph(pin, bg=t["surface"], color=t["bar"])
    self.speed_graph.pack(fill="x", pady=(3, 0))

    self.bottom_bar = tk.Frame(self.root, bg=t["surface"], height=34)
    self.bottom_bar.pack(side="bottom", fill="x")
    self.bottom_bar.pack_propagate(False)

    bi = tk.Frame(self.bottom_bar, bg=t["surface"], padx=10, pady=4)
    bi.pack(fill="both", expand=True)

    self.dir_label = tk.Label(
        bi,
        text="",
        font=("Segoe UI", 7),
        bg=t["surface"],
        fg=t["text_muted"],
        anchor="w",
    )
    self.dir_label.pack(side="left", fill="x", expand=True)

    change_btn = self._btn(
        bi,
        t["surface_2"],
        t["border"],
        t["surface"],
        self._choose_folder,
        width=32,
        height=22,
    )
    change_btn.pack(side="right")
    self._lbl(change_btn, "📁", t["surface_2"], 8)

    self.ready_var = tk.StringVar()
    tk.Label(
        bi,
        textvariable=self.ready_var,
        font=("Segoe UI", 7, "bold"),
        bg=t["surface"],
        fg=t["success"],
        anchor="w",
    ).pack(side="right", padx=(0, 8))

  def _redraw_logo(self):
    t = self.theme
    self.logo_canvas.config(bg=t["bg"])
    self.logo_canvas.delete("all")
    self.logo_canvas.create_oval(
        1,
        1,
        27,
        27,
        fill=t["surface_2"],
        outline=t.get("accent", "#00FFFF"),
        width=2,
    )
    self.logo_canvas.create_polygon(
        7,
        7,
        14,
        4,
        21,
        7,
        21,
        18,
        14,
        23,
        7,
        18,
        fill=t["surface"],
        outline=t["primary"],
        width=1,
    )
    self.logo_canvas.create_text(
        14,
        13,
        text="P",
        font=("Segoe UI", 8, "bold"),
        fill=t.get("accent", "#00FFFF"),
    )
    self.logo_canvas.create_line(
        8, 23, 20, 23, fill=t.get("action", "#FF0080"), width=2
    )

  def _btn(self, parent, fill, outline, hover, command, width=None, height=28):
    return RoundedBtn(
        parent,
        fill=fill,
        outline=outline,
        hover=hover,
        radius=6,
        height=height,
        width=width,
        command=command,
        animate=self.settings.get("button_animation", True),
    )

  def _lbl(self, box, text, bg, size=8):
    lbl = tk.Label(
        box,
        text=text,
        font=("Segoe UI", size, "bold"),
        bg=bg,
        fg="#FFFFFF",
    )
    lbl.place(relx=0.5, rely=0.5, anchor="center")
    box.attach_label(lbl)
    return lbl

  def _build_home(self):
    t = self.theme
    p = tk.Frame(self.container, bg=t["bg"])

    row = tk.Frame(p, bg=t["bg"])
    row.pack(fill="x", pady=(2, 6))

    self.video_btn = self._btn(
        row,
        t["accent"],
        t["border"],
        t["accent_hover"],
        lambda: self._set_mode("video"),
        width=72,
        height=26,
    )
    self.video_btn.pack(side="left", padx=(0, 4))
    self.video_lbl = self._lbl(self.video_btn, "🎬 Video", t["accent"], 8)

    self.audio_btn = self._btn(
        row,
        t["surface_2"],
        t["border"],
        t["surface"],
        lambda: self._set_mode("audio"),
        width=72,
        height=26,
    )
    self.audio_btn.pack(side="left", padx=(0, 10))
    self.audio_lbl = self._lbl(self.audio_btn, "🎵 Audio", t["surface_2"], 8)

    tk.Label(
        row,
        text="Qual:",
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["text_muted"],
    ).pack(side="left", padx=(0, 3))
    self.quality_combo = ttk.Combobox(
        row,
        textvariable=self.quality_var,
        values=VIDEO_QUALITIES,
        state="readonly",
        width=7,
        font=("Segoe UI", 8),
    )
    self.quality_combo.pack(side="left", padx=(0, 8))
    self.quality_combo.bind(
        "<<ComboboxSelected>>", lambda _: self._refresh_ready()
    )

    tk.Label(
        row,
        text="Fmt:",
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["text_muted"],
    ).pack(side="left", padx=(0, 3))
    self.format_combo = ttk.Combobox(
        row,
        textvariable=self.format_var,
        values=VIDEO_FORMATS,
        state="readonly",
        width=7,
        font=("Segoe UI", 8),
    )
    self.format_combo.pack(side="left")
    self.format_combo.bind(
        "<<ComboboxSelected>>", lambda _: self._refresh_ready()
    )

    self.url_entry, self.dl_btn, self.dl_lbl = self._entry_row(
        p,
        title="Direct Link",
        guide="Paste single video/audio or file URL -> downloads single item",
        command=self._download_url,
        btn_text="⬇ DL",
        fill=t["action"],
        hover=t["action_hover"],
        btn_width=76,
        show_preview=True,
    )

    self.search_entry, self.search_btn, self.search_lbl = self._entry_row(
        p,
        title="Search",
        guide="Type song/video keywords -> finds & queues YouTube matches",
        command=self._search_download,
        btn_text="🔍 Find",
        fill=t["primary"],
        hover=t["primary_hover"],
        btn_width=76,
    )

    self.site_entry, self.site_btn, self.site_lbl = self._entry_row(
        p,
        title="Page Scan",
        guide="Paste webpage/playlist URL -> scans & queues found media",
        command=self._site_download,
        btn_text="🌐 Scan",
        fill=t["accent"],
        hover=t["accent_hover"],
        btn_width=76,
    )

    self.preview_frame = self._register_box(
        tk.Frame(
            p,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
        ),
        "surface",
    )

    return p

  def _entry_row(
      self,
      parent,
      title,
      guide,
      command,
      btn_text,
      fill,
      hover,
      btn_width=76,
      show_preview=False,
  ):
    t = self.theme
    block = tk.Frame(parent, bg=t["bg"])
    block.pack(fill="x", pady=(0, 6))

    tk.Label(
        block,
        text=f"{title}: {guide}",
        font=("Segoe UI", 7),
        bg=t["bg"],
        fg=t["text_muted"],
        anchor="w",
    ).pack(fill="x", pady=(0, 2))

    f = tk.Frame(block, bg=t["bg"])
    f.pack(fill="x")

    w = self._register_box(
        tk.Frame(
            f,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
        ),
        "surface",
    )
    w.pack(side="left", fill="x", expand=True, padx=(0, 4))

    entry = tk.Entry(
        w,
        font=("Segoe UI", 9),
        bg=t["surface"],
        fg=t["text"],
        insertbackground=t["text"],
        relief="flat",
        bd=0,
    )
    entry.pack(fill="x", padx=8, pady=4)
    if show_preview:
      entry.bind(
          "<<Paste>>", lambda _e: self.root.after(350, self._preview_url)
      )
      entry.bind(
          "<Control-v>", lambda _e: self.root.after(350, self._preview_url)
      )
      entry.bind(
          "<Control-V>", lambda _e: self.root.after(350, self._preview_url)
      )
      entry.bind("<KeyRelease>", self._schedule_auto_preview)

    pb = self._btn(
        f,
        t["surface_2"],
        t["border"],
        t["surface"],
        lambda: self._paste(entry),
        width=32,
        height=26,
    )
    pb.pack(side="left", padx=(0, 4))
    self._lbl(pb, "📋", t["surface_2"], 8)

    if show_preview:
      pv = self._btn(
          f,
          t["surface_2"],
          t["border"],
          t["surface"],
          lambda: self._preview_url(),
          width=32,
          height=26,
      )
      pv.pack(side="left", padx=(0, 4))
      self._lbl(pv, "👁", t["surface_2"], 8)

    ab = self._btn(
        f, fill, t["border"], hover, command, width=btn_width, height=26
    )
    ab.pack(side="right")
    albl = self._lbl(ab, btn_text, fill, 8)

    entry.bind("<Return>", lambda _: command())
    return entry, ab, albl

  def _build_tools_page(self):
    t = self.theme
    p = tk.Frame(self.container, bg=t["bg"])

    tk.Label(
        p,
        text="Tools: Batch links, Time-Range Clip, Local Converter & Power Timer",
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["text_muted"],
        anchor="w",
    ).pack(fill="x", pady=(2, 4))

    bcard = self._register_box(
        tk.Frame(
            p,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
            padx=8,
            pady=6,
        ),
        "surface",
    )
    bcard.pack(fill="x", pady=(0, 6))
    tk.Label(
        bcard,
        text="Batch URLs (one link per line):",
        font=("Segoe UI", 8, "bold"),
        bg=t["surface"],
        fg=t["text"],
        anchor="w",
    ).pack(fill="x")
    self.batch_text = tk.Text(
        bcard,
        height=3,
        font=("Consolas", 8),
        bg=t["surface_2"],
        fg=t["text"],
        insertbackground=t["text"],
        relief="flat",
        bd=1,
    )
    self.batch_text.pack(fill="x", pady=(3, 4))
    bb_row = tk.Frame(bcard, bg=t["surface"])
    bb_row.pack(fill="x")
    b_add = self._btn(
        bb_row,
        t["primary"],
        t["border"],
        t["primary_hover"],
        self._enqueue_batch,
        width=115,
        height=24,
    )
    b_add.pack(side="left")
    self._lbl(b_add, "⬇ Queue All", t["primary"], 8)

    tk.Label(
        bb_row,
        text="After Queue:",
        font=("Segoe UI", 8, "bold"),
        bg=t["surface"],
        fg=t["text_muted"],
    ).pack(side="left", padx=(14, 4))
    ttk.Combobox(
        bb_row,
        textvariable=self.power_after_var,
        values=["None", "Shutdown", "Sleep"],
        state="readonly",
        width=10,
        font=("Segoe UI", 8),
    ).pack(side="left")

    ccard = self._register_box(
        tk.Frame(
            p,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
            padx=8,
            pady=6,
        ),
        "surface",
    )
    ccard.pack(fill="x", pady=(0, 6))
    tk.Label(
        ccard,
        text="Clip Downloader (uses Direct Link URL):",
        font=("Segoe UI", 8, "bold"),
        bg=t["surface"],
        fg=t["text"],
        anchor="w",
    ).pack(fill="x", pady=(0, 3))
    crow = tk.Frame(ccard, bg=t["surface"])
    crow.pack(fill="x")
    tk.Label(
        crow,
        text="Start (MM:SS):",
        font=("Segoe UI", 8),
        bg=t["surface"],
        fg=t["text_muted"],
    ).pack(side="left")
    self.clip_start_var = tk.StringVar(value="00:00")
    sb_box, _ = self._boxed_entry(crow, self.clip_start_var, width=8)
    sb_box.pack(side="left", padx=(4, 10))
    tk.Label(
        crow,
        text="End (MM:SS):",
        font=("Segoe UI", 8),
        bg=t["surface"],
        fg=t["text_muted"],
    ).pack(side="left")
    self.clip_end_var = tk.StringVar(value="01:00")
    eb_box, _ = self._boxed_entry(crow, self.clip_end_var, width=8)
    eb_box.pack(side="left", padx=(4, 10))
    c_btn = self._btn(
        crow,
        t["action"],
        t["border"],
        t["action_hover"],
        self._download_clip,
        width=98,
        height=24,
    )
    c_btn.pack(side="right")
    self._lbl(c_btn, "✂ DL Clip", t["action"], 8)

    mcard = self._register_box(
        tk.Frame(
            p,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
            padx=8,
            pady=6,
        ),
        "surface",
    )
    mcard.pack(fill="x")
    tk.Label(
        mcard,
        text="Local Media Converter & Compressor (FFmpeg):",
        font=("Segoe UI", 8, "bold"),
        bg=t["surface"],
        fg=t["text"],
        anchor="w",
    ).pack(fill="x", pady=(0, 3))
    mrow = tk.Frame(mcard, bg=t["surface"])
    mrow.pack(fill="x")
    self.conv_target_var = tk.StringVar(value="Compress MP4")
    ttk.Combobox(
        mrow,
        textvariable=self.conv_target_var,
        values=["Compress MP4", "Extract MP3", "Convert MKV"],
        state="readonly",
        width=15,
        font=("Segoe UI", 8),
    ).pack(side="left", padx=(0, 8))
    m_btn = self._btn(
        mrow,
        t["success"],
        t["border"],
        "#059669",
        self._convert_local_file,
        width=130,
        height=24,
    )
    m_btn.pack(side="left")
    self._lbl(m_btn, "🔄 Pick & Convert", t["success"], 8)

    return p

  def _enqueue_batch(self):
    raw = self.batch_text.get("1.0", tk.END).strip()
    if not raw:
      safe_showwarning("Empty", "Paste one or more URLs first.")
      return
    urls = [line.strip() for line in raw.splitlines() if line.strip()]
    cap = self._media_limit()
    if cap > 0:
      urls = urls[:cap]
    for u in urls:
      self._enqueue(u, noplaylist=True)
    self.batch_text.delete("1.0", tk.END)
    Toast.show(
        self.root,
        "Batch Queued",
        f"{len(urls)} links added",
        accent=self.theme["success"],
    )

  def _download_clip(self):
    u = self.url_entry.get().strip()
    if not u:
      safe_showwarning(
          "No URL", "Paste a URL into Home -> Direct Link first."
      )
      return
    s = parse_time_sec(self.clip_start_var.get())
    e = parse_time_sec(self.clip_end_var.get())
    if s is None or e is None or e <= s:
      safe_showwarning(
          "Invalid Time", "Enter valid Start and End times (MM:SS)."
      )
      return
    self.url_entry.delete(0, tk.END)
    self._enqueue(u, clip_range=(s, e), noplaylist=True)

  def _convert_local_file(self):
    fp = filedialog.askopenfilename(
        title="Select Video/Audio File",
        filetypes=[
            ("Media", "*.mp4;*.mkv;*.webm;*.avi;*.mov;*.m4a;*.wav;*.mp3")
        ],
    )
    if not fp:
      return
    mode = self.conv_target_var.get()
    base, _ = os.path.splitext(fp)
    ff_dir = find_ffmpeg_dir()
    ff_exe = os.path.join(ff_dir, "ffmpeg.exe") if ff_dir else "ffmpeg"
    if mode == "Extract MP3":
      out = base + "_converted.mp3"
      cmd = [
          ff_exe,
          "-y",
          "-i",
          fp,
          "-vn",
          "-acodec",
          "libmp3lame",
          "-ab",
          "192k",
          out,
      ]
    elif mode == "Convert MKV":
      out = base + "_converted.mkv"
      cmd = [ff_exe, "-y", "-i", fp, "-c", "copy", out]
    else:
      out = base + "_compressed.mp4"
      cmd = [
          ff_exe,
          "-y",
          "-i",
          fp,
          "-vcodec",
          "libx264",
          "-crf",
          "26",
          "-preset",
          "fast",
          "-acodec",
          "aac",
          "-b:a",
          "128k",
          out,
      ]
    self._show_progress(
        25, f"Converting: {os.path.basename(fp)[:28]}", mode
    )

    def run():
      try:
        subprocess.run(cmd, check=True, capture_output=True)
        if not os.path.isfile(out) or os.path.getsize(out) == 0:
          raise RuntimeError("Output file is empty.")
        self.root.after(0, self._hide_progress)
        self.root.after(
            0,
            lambda: Toast.show(
                self.root,
                "Converted",
                os.path.basename(out)[:45],
                accent=self.theme["success"],
            ),
        )
      except Exception as err:
        try:
          if os.path.isfile(out) and os.path.getsize(out) == 0:
            os.remove(out)
        except Exception:
          pass
        self.root.after(0, self._hide_progress)
        self.root.after(
            0,
            lambda: Toast.show(
                self.root,
                "FFmpeg Error",
                clean_str(str(err))[:45],
                accent=self.theme["danger"],
            ),
        )

    threading.Thread(target=run, daemon=True).start()

  def _build_queue(self):
    t = self.theme
    p = tk.Frame(self.container, bg=t["bg"])
    tk.Label(
        p,
        text="Queue: Manage pending, active, and finished downloads",
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["text_muted"],
        anchor="w",
    ).pack(fill="x", pady=(2, 4))

    wrap = self._register_box(
        tk.Frame(
            p,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
        ),
        "surface",
    )
    wrap.pack(fill="both", expand=True)

    sb = tk.Scrollbar(wrap)
    sb.pack(side="right", fill="y")

    self.queue_list = tk.Listbox(
        wrap,
        bg=t["surface"],
        fg=t["text"],
        selectbackground=t["primary"],
        selectforeground="#FFFFFF",
        font=("Consolas", 8),
        bd=0,
        highlightthickness=0,
        yscrollcommand=sb.set,
    )
    self.queue_list.pack(side="left", fill="both", expand=True, padx=6, pady=6)
    sb.config(command=self.queue_list.yview)

    br = tk.Frame(p, bg=t["bg"])
    br.pack(fill="x", pady=(6, 2))

    self.pause_btn = self._btn(
        br,
        t["warning"],
        t["border"],
        "#D97706",
        self._toggle_pause,
        width=92,
        height=26,
    )
    self.pause_btn.pack(side="left", padx=(0, 4))
    self.pause_lbl = self._lbl(self.pause_btn, "⏸ Pause", t["warning"], 8)

    del_btn = self._btn(
        br,
        t["danger"],
        t["border"],
        "#DC2626",
        self._delete_queue_item,
        width=78,
        height=26,
    )
    del_btn.pack(side="left", padx=(0, 4))
    self._lbl(del_btn, "🗑 Delete", t["danger"], 8)

    clear_btn = self._btn(
        br,
        t["danger"],
        t["border"],
        "#DC2626",
        self._clear_queue_done,
        width=96,
        height=26,
    )
    clear_btn.pack(side="left")
    self._lbl(clear_btn, "🧹 Clear Done", t["danger"], 8)

    return p

  def _build_history(self):
    t = self.theme
    p = tk.Frame(self.container, bg=t["bg"])
    tk.Label(
        p,
        text="History: Search past downloads or open output folder",
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["text_muted"],
        anchor="w",
    ).pack(fill="x", pady=(2, 4))

    sr = tk.Frame(p, bg=t["bg"])
    sr.pack(fill="x", pady=(0, 6))
    sw = self._register_box(
        tk.Frame(
            sr,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
        ),
        "surface",
    )
    sw.pack(side="left", fill="x", expand=True)
    self.hist_search = tk.Entry(
        sw,
        font=("Segoe UI", 8),
        bg=t["surface"],
        fg=t["text"],
        insertbackground=t["text"],
        relief="flat",
        bd=0,
    )
    self.hist_search.pack(fill="x", padx=8, pady=4)
    self.hist_search.bind(
        "<KeyRelease>", lambda _: self._refresh_history_list()
    )

    wrap = self._register_box(
        tk.Frame(
            p,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
        ),
        "surface",
    )
    wrap.pack(fill="both", expand=True)

    sb = tk.Scrollbar(wrap)
    sb.pack(side="right", fill="y")

    self.history_list = tk.Listbox(
        wrap,
        bg=t["surface"],
        fg=t["text"],
        selectbackground=t["primary"],
        selectforeground="#FFFFFF",
        font=("Consolas", 8),
        bd=0,
        highlightthickness=0,
        yscrollcommand=sb.set,
    )
    self.history_list.pack(side="left", fill="both", expand=True, padx=6, pady=6)
    sb.config(command=self.history_list.yview)

    br = tk.Frame(p, bg=t["bg"])
    br.pack(fill="x", pady=(6, 2))

    clr = self._btn(
        br,
        t["danger"],
        t["border"],
        "#DC2626",
        self._clear_history,
        width=92,
        height=26,
    )
    clr.pack(side="left", padx=(0, 4))
    self._lbl(clr, "🗑 Clear All", t["danger"], 8)

    op = self._btn(
        br,
        t["primary"],
        t["border"],
        t["primary_hover"],
        self._open_folder,
        width=102,
        height=26,
    )
    op.pack(side="left")
    self._lbl(op, "📂 Folder", t["primary"], 8)

    return p

  def _build_favorites(self):
    t = self.theme
    p = tk.Frame(self.container, bg=t["bg"])
    tk.Label(
        p,
        text="Favorites: Put URL in Direct Link -> Add -> select & DL",
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["text_muted"],
        anchor="w",
    ).pack(fill="x", pady=(2, 4))

    wrap = self._register_box(
        tk.Frame(
            p,
            bg=t["surface"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
        ),
        "surface",
    )
    wrap.pack(fill="both", expand=True)

    sb = tk.Scrollbar(wrap)
    sb.pack(side="right", fill="y")

    self.fav_list = tk.Listbox(
        wrap,
        bg=t["surface"],
        fg=t["text"],
        selectbackground=t["primary"],
        selectforeground="#FFFFFF",
        font=("Consolas", 8),
        bd=0,
        highlightthickness=0,
        yscrollcommand=sb.set,
    )
    self.fav_list.pack(side="left", fill="both", expand=True, padx=6, pady=6)
    sb.config(command=self.fav_list.yview)

    br = tk.Frame(p, bg=t["bg"])
    br.pack(fill="x", pady=(6, 2))

    add_btn = self._btn(
        br,
        t["success"],
        t["border"],
        "#059669",
        self._add_favorite,
        width=80,
        height=26,
    )
    add_btn.pack(side="left", padx=(0, 4))
    self._lbl(add_btn, "➕ Add", t["success"], 8)

    dl_btn = self._btn(
        br,
        t["primary"],
        t["border"],
        t["primary_hover"],
        self._download_favorite,
        width=88,
        height=26,
    )
    dl_btn.pack(side="left", padx=(0, 4))
    self._lbl(dl_btn, "⬇ DL", t["primary"], 8)

    del_btn = self._btn(
        br,
        t["danger"],
        t["border"],
        "#DC2626",
        self._remove_favorite,
        width=82,
        height=26,
    )
    del_btn.pack(side="left")
    self._lbl(del_btn, "🗑 Remove", t["danger"], 8)

    return p

  def _build_apk(self):
    t = self.theme
    p = tk.Frame(self.container, bg=t["bg"])
    pr = tk.Frame(p, bg=t["bg"])
    pr.pack(fill="x", pady=(0, 1))
    pw = self._register_box(
        tk.Frame(
            pr,
            bg=t["surface"],
            highlightbackground=t["border"],
            highlightcolor=t["border"],
            highlightthickness=1,
        ),
        "surface",
    )
    pw.pack(side="left", fill="x", expand=True, padx=(0, 2))
    self.apk_var = tk.StringVar()
    apk_entry = tk.Entry(
        pw,
        textvariable=self.apk_var,
        font=("Segoe UI", 7),
        bg=t["surface"],
        fg=t["text"],
        insertbackground=t["text"],
        relief="flat",
        bd=0,
    )
    apk_entry.pack(fill="x", padx=3, pady=1)

    bb = self._btn(
        pr,
        t["primary"],
        t["border"],
        t["primary_hover"],
        self._pick_install,
        width=42,
        height=19,
    )
    bb.pack(side="right", padx=(0, 2))
    self._lbl(bb, "📂 Pick", t["primary"], 6)

    ib = self._btn(
        pr,
        t["success"],
        t["border"],
        "#059669",
        self._run_install,
        width=55,
        height=19,
    )
    ib.pack(side="right")
    self._lbl(ib, "📲 Install", t["success"], 6)
    return p

  def _build_speed_page(self):
    if hasattr(self, "speed_page") and self.speed_page.winfo_exists():
      return self.speed_page
    t = self.theme
    p = tk.Frame(self.container, bg=t["bg"])
    self.speed_page = p

    tk.Label(
        p,
        text=(
            "Speed Test (30m): Smooth ramp-up meter • Ping, Download & Upload"
        ),
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["text_muted"],
        anchor="w",
    ).pack(fill="x", pady=(2, 6))

    top = tk.Frame(p, bg=t["bg"])
    top.pack(fill="x")

    gp = tk.Frame(top, bg=t["bg"])
    gp.pack(side="left", padx=(0, 12))

    self.gauge = tk.Canvas(
        gp, width=180, height=104, bg=t["bg"], highlightthickness=0, bd=0
    )
    self.gauge.pack()
    gcx, gcy, grad = 90, 92, 66
    self._gauge_center = (gcx, gcy, grad)
    self.gauge.create_arc(
        gcx - grad,
        gcy - grad,
        gcx + grad,
        gcy + grad,
        start=0,
        extent=180,
        style="arc",
        outline=t["border"],
        width=10,
    )
    self._gauge_arc = self.gauge.create_arc(
        gcx - grad,
        gcy - grad,
        gcx + grad,
        gcy + grad,
        start=180,
        extent=0,
        style="arc",
        outline=t["success"],
        width=10,
    )
    self._gauge_needle = self.gauge.create_line(
        gcx, gcy, gcx - grad + 10, gcy, fill=t["danger"], width=3
    )
    self.gauge.create_oval(
        gcx - 5, gcy - 5, gcx + 5, gcy + 5, fill=t["text"], outline=""
    )

    self.speed_big = tk.Label(
        gp,
        text="0.00 Mbps",
        font=("Segoe UI", 12, "bold"),
        bg=t["bg"],
        fg=t["text"],
    )
    self.speed_big.pack()

    info = tk.Frame(top, bg=t["bg"])
    info.pack(side="left", fill="both", expand=True)

    self.phase_lbl = tk.Label(
        info,
        text="Idle (30:00 max)",
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["primary"],
        anchor="w",
    )
    self.phase_lbl.pack(fill="x", pady=(2, 4))

    self.ping_var = tk.StringVar(value="Ping: -- ms")
    self.dl_var = tk.StringVar(value="Download: -- Mbps")
    self.ul_var = tk.StringVar(value="Upload: -- Mbps")
    tk.Label(
        info,
        textvariable=self.ping_var,
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["primary"],
        anchor="w",
    ).pack(fill="x", pady=1)
    tk.Label(
        info,
        textvariable=self.dl_var,
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["success"],
        anchor="w",
    ).pack(fill="x", pady=1)
    tk.Label(
        info,
        textvariable=self.ul_var,
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["accent"],
        anchor="w",
    ).pack(fill="x", pady=(1, 8))

    self.go_btn = self._btn(
        info,
        t["success"],
        t["border"],
        "#059669",
        self._run_speed_test,
        width=92,
        height=26,
    )
    self.go_btn.pack(side="left")
    self.go_lbl = self._lbl(self.go_btn, "▶ GO 30m", t["success"], 8)

    back = self._btn(
        info,
        t["surface_2"],
        t["border"],
        t["surface"],
        lambda: self._switch_page("home"),
        width=70,
        height=26,
    )
    back.pack(side="left", padx=(6, 0))
    self._lbl(back, "⬅ Back", t["surface_2"], 8)

    return p

  def _boxed_entry(self, parent, textvariable, width=10):
    t = self.theme
    box = self._register_box(
        tk.Frame(
            parent,
            bg=t["surface_2"],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
        ),
        "surface_2",
    )
    ent = tk.Entry(
        box,
        textvariable=textvariable,
        font=("Segoe UI", 8, "bold"),
        bg=t["surface_2"],
        fg=t["text"],
        insertbackground=t["text"],
        relief="flat",
        bd=0,
        width=width,
    )
    ent.pack(padx=5, pady=2)
    return box, ent

  def _build_settings_page(self):
    t = self.theme
    p = tk.Frame(self.container, bg=t["bg"])

    hdr = tk.Frame(p, bg=t["bg"])
    hdr.pack(fill="x", pady=(2, 4))
    tk.Label(
        hdr,
        text="SETTINGS  /  Customize PRIME NOX",
        font=("Segoe UI", 8, "bold"),
        bg=t["bg"],
        fg=t["text_muted"],
        anchor="w",
    ).pack(side="left")
    back_b = self._btn(
        hdr,
        t["surface_2"],
        t["border"],
        t["surface"],
        lambda: self._switch_page("home"),
        width=62,
        height=22,
    )
    back_b.pack(side="right")
    self._lbl(back_b, "← Back", t["surface_2"], 8)

    canvas = self._register_box(
        tk.Canvas(
            p,
            bg=t["surface"],
            highlightbackground=t["border"],
            highlightcolor=t["border"],
            highlightthickness=1,
            bd=0,
        ),
        "surface",
    )
    sb = tk.Scrollbar(p, orient="vertical", command=canvas.yview)
    card = tk.Frame(canvas, bg=t["surface"], padx=6, pady=6)
    card.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((0, 0), window=card, anchor="nw")
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def section(title):
      outer = tk.Frame(
          card,
          bg=t["surface_2"],
          highlightbackground=t["border"],
          highlightthickness=1,
          padx=5,
          pady=4,
      )
      outer.pack(fill="x", pady=(0, 5))
      tk.Label(
          outer,
          text=title.upper(),
          font=("Segoe UI", 8, "bold"),
          bg=t["surface_2"],
          fg=t["primary"],
          anchor="w",
      ).pack(fill="x", pady=(0, 3))
      inner = tk.Frame(outer, bg=t["surface_2"])
      inner.pack(fill="x")
      return inner

    def checkbox(parent, variable, label, col=0, row=0):
      tk.Checkbutton(
          parent,
          text=label,
          variable=variable,
          font=("Segoe UI", 8),
          bg=t["surface_2"],
          fg=t["text"],
          selectcolor=t["surface"],
          activebackground=t["surface_2"],
          activeforeground=t["text"],
          bd=0,
          highlightthickness=0,
          command=self._save_inline_settings,
      ).grid(row=row, column=col, sticky="w", padx=(0, 5), pady=1)

    def combo_row(parent, label, var, values, width=12, callback=True):
      row = tk.Frame(parent, bg=t["surface_2"])
      row.pack(fill="x", pady=1)
      tk.Label(
          row,
          text=label,
          font=("Segoe UI", 8),
          bg=t["surface_2"],
          fg=t["text_muted"],
          width=12,
          anchor="w",
      ).pack(side="left")
      cb = ttk.Combobox(
          row,
          textvariable=var,
          values=values,
          state="readonly",
          width=width,
          font=("Segoe UI", 8),
      )
      cb.pack(side="left", fill="x", expand=True)
      if callback:
        cb.bind("<<ComboboxSelected>>", self._save_inline_settings)
      return cb

    self._dark_var = tk.BooleanVar(value=self.settings.get("dark_mode", True))
    self._startup_var = tk.BooleanVar(
        value=self.settings.get("run_at_startup", False)
    )
    self._ext_prompt_var = tk.BooleanVar(
        value=self.settings.get("extension_auto_prompt", True)
    )
    self._top_var = tk.BooleanVar(
        value=self.settings.get("always_on_top", False)
    )

    quick = section("Quick Controls")
    quick.grid_columnconfigure(0, weight=1)
    quick.grid_columnconfigure(1, weight=1)
    for i, (var, label) in enumerate([
        (self._dark_var, "Dark Mode"),
        (self._startup_var, "Run at Startup"),
        (self._ext_prompt_var, "Extension Helper"),
        (self._top_var, "Always on Top"),
    ]):
      checkbox(quick, var, label, col=i % 2, row=i // 2)

    self._set_vars = {}
    behavior = section("Download & Automation")
    behavior.grid_columnconfigure(0, weight=1)
    behavior.grid_columnconfigure(1, weight=1)
    checks = [
        ("duplicate_guard", "Duplicate Guard"),
        ("auto_organize", "Auto Folder"),
        ("embed_subtitles", "Subtitles"),
        ("notifications", "Notifications"),
        ("button_animation", "Button Animation"),
        ("toast_notifications", "Toast Alerts"),
        ("auto_update_ytdlp", "Update yt-dlp"),
        ("auto_retry", "Auto Retry"),
        ("clipboard_monitor", "Clipboard Monitor"),
        ("sound_effects", "Sound Effects"),
        ("embed_metadata", "Embed Metadata"),
        ("sponsorblock", "SponsorBlock"),
    ]
    for i, (key, label) in enumerate(checks):
      self._set_vars[key] = tk.BooleanVar(
          value=self.settings.get(key, False)
      )
      checkbox(behavior, self._set_vars[key], label, col=i % 2, row=i // 2)

    appearance = section("Appearance")
    self._theme_var = tk.StringVar(value=self.settings["theme"])
    combo_row(
        appearance, "Theme", self._theme_var, list(THEMES.keys()), width=14
    )
    self._particle_var = tk.StringVar(value=self.settings["particle_type"])
    combo_row(
        appearance,
        "Particles",
        self._particle_var,
        ["Network", "Dots", "Stars", "Bubbles", "None"],
        width=12,
    )

    browser = section("Browser & Extension")
    self._cookies_var = tk.StringVar(
        value=self.settings.get("browser_cookies", "None")
    )
    combo_row(
        browser,
        "Cookies From",
        self._cookies_var,
        ["None", "chrome", "edge", "firefox", "brave"],
        width=12,
    )

    notify = section("Notifications")
    self._notification_position_var = tk.StringVar(
        value=self.settings.get("notification_position", "bottom-right")
    )
    combo_row(
        notify,
        "Screen Corner",
        self._notification_position_var,
        ["bottom-right", "top-right", "bottom-left", "top-left"],
        width=14,
    )

    limits = section("Download Limits")
    limit_row = tk.Frame(limits, bg=t["surface_2"])
    limit_row.pack(fill="x")
    tk.Label(
        limit_row,
        text="Speed KB/s",
        font=("Segoe UI", 8),
        bg=t["surface_2"],
        fg=t["text_muted"],
    ).pack(side="left")
    self._bw_var = tk.StringVar(
        value=str(self.settings.get("bandwidth_limit", 0))
    )
    bw_box, bw_entry = self._boxed_entry(limit_row, self._bw_var, width=6)
    bw_box.pack(side="left", padx=(3, 10))
    bw_entry.bind("<FocusOut>", self._save_inline_settings)
    bw_entry.bind("<Return>", self._save_inline_settings)
    tk.Label(
        limit_row,
        text="Max Media (0=all)",
        font=("Segoe UI", 8),
        bg=t["surface_2"],
        fg=t["text_muted"],
    ).pack(side="left")
    self._max_media_var = tk.StringVar(
        value=str(self.settings.get("max_media_limit", 0))
    )
    mm_box, mm_entry = self._boxed_entry(limit_row, self._max_media_var, width=5)
    mm_box.pack(side="left", padx=(3, 0))
    mm_entry.bind("<FocusOut>", self._save_inline_settings)
    mm_entry.bind("<Return>", self._save_inline_settings)

    network = section("Network / Proxy")
    proxy_row = tk.Frame(network, bg=t["surface_2"])
    proxy_row.pack(fill="x")
    tk.Label(
        proxy_row,
        text="Proxy",
        font=("Segoe UI", 8),
        bg=t["surface_2"],
        fg=t["text_muted"],
    ).pack(side="left")
    self._proxy_var = tk.StringVar(value=self.settings.get("proxy", ""))
    pr_box, proxy_entry = self._boxed_entry(proxy_row, self._proxy_var, width=19)
    pr_box.pack(side="left", padx=(4, 5), fill="x", expand=True)
    proxy_entry.bind("<FocusOut>", self._save_inline_settings)
    proxy_entry.bind("<Return>", self._save_inline_settings)
    ext_btn = self._btn(
        proxy_row,
        self.theme["primary"],
        self.theme["border"],
        self.theme["primary_hover"],
        self._install_extension_now,
        width=96,
        height=22,
    )
    ext_btn.pack(side="right")
    self._lbl(ext_btn, "🧩 Add Extension", self.theme["primary"], 8)

    tk.Label(
        card,
        text="✓ Changes save and apply automatically",
        font=("Segoe UI", 8, "bold"),
        bg=t["surface"],
        fg=t["success"],
        anchor="w",
    ).pack(anchor="w", pady=(1, 0))
    return p

  def _toggle_notifications(self):
    global NOTIFICATIONS_ENABLED
    NOTIFICATIONS_ENABLED = not NOTIFICATIONS_ENABLED
    Toast.enabled = NOTIFICATIONS_ENABLED
    self.settings["notifications_enabled"] = NOTIFICATIONS_ENABLED
    self.settings["notifications"] = NOTIFICATIONS_ENABLED
    if "notifications" in self._set_vars:
      self._set_vars["notifications"].set(NOTIFICATIONS_ENABLED)
    if hasattr(self, "notification_lbl"):
      self.notification_lbl.config(
          text="🔔" if NOTIFICATIONS_ENABLED else "🔕"
      )
    save_settings(self.settings)

  def _toggle_pin(self):
    cur = not self.settings.get("always_on_top", False)
    self.settings["always_on_top"] = cur
    if hasattr(self, "_top_var"):
      self._top_var.set(cur)
    self.root.attributes("-topmost", cur)
    save_settings(self.settings)
    Toast.show(
        self.root,
        "Pinned" if cur else "Unpinned",
        "Always on top enabled" if cur else "Always on top disabled",
        accent=self.theme["primary"],
    )

  def _save_inline_settings(self, event=None):
    global NOTIFICATIONS_ENABLED
    for k, v in self._set_vars.items():
      self.settings[k] = bool(v.get())
    self.settings["embed_thumbnail"] = False
    self.settings["dark_mode"] = bool(self._dark_var.get())
    self.settings["run_at_startup"] = bool(self._startup_var.get())
    self.settings["extension_auto_prompt"] = bool(self._ext_prompt_var.get())
    self.settings["always_on_top"] = bool(self._top_var.get())
    self.settings["theme"] = self._theme_var.get()
    self.settings["particle_type"] = self._particle_var.get()
    self.settings["browser_cookies"] = self._cookies_var.get()
    try:
      self.settings["bandwidth_limit"] = max(0, int(self._bw_var.get()))
    except ValueError:
      self.settings["bandwidth_limit"] = 0
    try:
      self.settings["max_media_limit"] = max(0, int(self._max_media_var.get()))
    except ValueError:
      self.settings["max_media_limit"] = 0
    self.settings["proxy"] = self._proxy_var.get().strip()

    NOTIFICATIONS_ENABLED = bool(self.settings.get("notifications", True))
    self.settings["notifications_enabled"] = NOTIFICATIONS_ENABLED
    Toast.enabled = NOTIFICATIONS_ENABLED
    if hasattr(self, "notification_lbl"):
      self.notification_lbl.config(
          text="🔔" if NOTIFICATIONS_ENABLED else "🔕"
      )

    self.settings["notification_position"] = (
        self._notification_position_var.get()
    )
    Toast.position = self.settings["notification_position"]

    self.root.attributes("-topmost", self.settings["always_on_top"])
    set_windows_startup(self.settings["run_at_startup"])
    save_settings(self.settings)
    self.theme = resolve_theme(self.settings)
    self._apply_theme()
    try:
      apply_dark_title(self.root.winfo_id(), self.settings["dark_mode"])
    except Exception:
      pass
    Toast.show(
        self.root, "Saved", "Settings applied", accent=self.theme["success"]
    )

  def _install_extension_now(self, browser_name="Google Chrome"):
    ext_path = ensure_extension_package()
    extension_page = {
        "Google Chrome": "chrome://extensions/",
        "Microsoft Edge": "edge://extensions/",
        "Brave": "brave://extensions/",
        "Mozilla Firefox": "about:addons",
    }.get(browser_name, "chrome://extensions/")
    try:
      webbrowser.open(extension_page)
    except Exception:
      pass
    try:
      os.startfile(ext_path)
    except Exception:
      pass
    safe_showinfo(
        "PRIME NOX Extension Setup",
        f"Extension folder opened:\n{ext_path}\n\n"
        f"In {browser_name}, enable Developer mode (if available), then choose "
        "Load unpacked / Load Temporary Add-on and select the opened folder.\n"
        "Browser security requires this final confirmation.\n"
        "Local bridge: http://127.0.0.1:5678",
    )

  def _start_browser_watcher(self):
    browsers = {
        "chrome.exe": "Google Chrome",
        "msedge.exe": "Microsoft Edge",
        "firefox.exe": "Mozilla Firefox",
        "brave.exe": "Brave",
    }

    def watch():
      while True:
        try:
          if os.name == "nt" and self.settings.get(
              "extension_auto_prompt", True
          ):
            out = subprocess.check_output(
                ["tasklist", "/FO", "CSV", "/NH"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            running_names = {
                line.split(",")[0].strip('"').lower()
                for line in out.splitlines()
                if line.strip()
            }
            for exe, bname in browsers.items():
              if exe in running_names and bname not in self._seen_browsers:
                self._seen_browsers.add(bname)
                self.root.after(
                    0,
                    lambda bn=bname: Toast.show(
                        self.root,
                        "Extension Ready",
                        f"{bn} detected · Add extension in Settings",
                        accent=self.theme["primary"],
                    ),
                )
          time.sleep(5)
        except Exception:
          time.sleep(6)

    threading.Thread(target=watch, daemon=True).start()

  def _switch_page(self, name):
    if name == "speed":
      sp = self._build_speed_page()
      self.pages["speed"] = sp
    if name != "speed" and self.speed_testing:
      self.speed_stop.set()
    for p in self.pages.values():
      p.pack_forget()
    if name in self.pages:
      self.pages[name].pack(fill="both", expand=True)
    self.active_page = name
    self._update_tabs(name)
    if name == "queue":
      self._refresh_queue_list()
    elif name == "history":
      self._refresh_history_list()
    elif name == "favorites":
      self._refresh_favorites_list()

  def _update_tabs(self, active):
    for k, (btn, lbl) in self.tab_btns.items():
      if k == active:
        btn.set_colors(
            fill=self.theme["primary"],
            outline=self.theme["border"],
            hover=self.theme["primary_hover"],
        )
        lbl.config(bg=self.theme["primary"], fg="#FFFFFF")
      else:
        btn.set_colors(
            fill=self.theme["surface"],
            outline=self.theme["border"],
            hover=self.theme["surface_2"],
        )
        lbl.config(bg=self.theme["surface"], fg=self.theme["text_muted"])

  def _toggle_speed_page(self):
    self._switch_page("home" if self.active_page == "speed" else "speed")

  def _apply_theme(self):
    t = self.theme
    self.bg.set_theme(t, self.settings["particle_type"])
    self.root.configure(bg=t["bg"])
    self.top_bar.config(bg=t["bg"])
    self.tabs_bar.config(bg=t["bg"])
    self.container.config(bg=t["bg"])
    self.title_lbl.config(bg=t["bg"], fg=t["text"])
    self.counter_lbl.config(bg=t["bg"], fg=t["success"])
    self.bottom_bar.config(bg=t["surface"])
    self.dir_label.config(bg=t["surface"], fg=t["text_muted"])
    for box, bg_key in self._bordered_boxes:
      if box.winfo_exists():
        box.config(
            bg=t[bg_key],
            highlightbackground="#000000",
            highlightcolor="#000000",
            highlightthickness=2,
        )
    self._redraw_logo()

    style = ttk.Style()
    style.configure(
        "PN.Horizontal.TProgressbar",
        troughcolor=t["surface_2"],
        background=t["bar"],
        bordercolor=t["border"],
        lightcolor=t["bar"],
        darkcolor=t["bar"],
    )
    self.settings_btn.set_colors(
        fill=t["surface_2"], outline=t["border"], hover=t["surface"]
    )
    self.settings_lbl.config(bg=t["surface_2"], fg=t["text"])
    self.pin_btn.set_colors(
        fill=t["surface_2"], outline=t["border"], hover=t["surface"]
    )
    self.pin_lbl.config(bg=t["surface_2"], fg=t["text"])
    self.speed_btn.set_colors(
        fill=t["success"], outline=t["border"], hover="#059669"
    )
    self.speed_lbl.config(bg=t["success"], fg="#FFFFFF")
    self._set_mode(self.mode_var.get())
    self.speed_graph.set_color(t["bar"])
    self._update_tabs(self.active_page)
    self._refresh_ready()

  def _set_mode(self, mode):
    if mode not in ("video", "audio"):
      return
    self.mode_var.set(mode)
    t = self.theme
    if mode == "video":
      self.video_btn.set_colors(
          fill=t["accent"], outline=t["border"], hover=t["accent_hover"]
      )
      self.video_lbl.config(bg=t["accent"], fg="#FFFFFF")
      self.audio_btn.set_colors(
          fill=t["surface_2"], outline=t["border"], hover=t["surface"]
      )
      self.audio_lbl.config(bg=t["surface_2"], fg=t["text_muted"])
      self.quality_combo.config(values=VIDEO_QUALITIES)
      if self.quality_var.get() not in VIDEO_QUALITIES:
        self.quality_var.set("Best")
      self.format_combo.config(values=VIDEO_FORMATS)
      if self.format_var.get().upper() not in VIDEO_FORMATS:
        self.format_var.set("MP4")
    else:
      self.audio_btn.set_colors(
          fill=t["success"], outline=t["border"], hover="#059669"
      )
      self.audio_lbl.config(bg=t["success"], fg="#FFFFFF")
      self.video_btn.set_colors(
          fill=t["surface_2"], outline=t["border"], hover=t["surface"]
      )
      self.video_lbl.config(bg=t["surface_2"], fg=t["text_muted"])
      self.quality_combo.config(values=AUDIO_QUALITIES)
      if self.quality_var.get() not in AUDIO_QUALITIES:
        self.quality_var.set("Best")
      self.format_combo.config(values=AUDIO_FORMATS)
      if self.format_var.get().upper() not in AUDIO_FORMATS:
        self.format_var.set("MP3")
    self._refresh_dir()
    self._refresh_ready()

  def _summary(self):
    return (
        f"{self.mode_var.get().upper()} • {self.quality_var.get()} •"
        f" {self.format_var.get().upper()}"
    )

  def _refresh_ready(self):
    self.ready_var.set(f"● Ready • {self._summary()}")

  def _refresh_dir(self):
    sub = "Audio" if self.mode_var.get() == "audio" else "Video"
    free = format_bytes(free_space(self.download_dir))
    self.dir_label.config(text=f"📁 {self.download_dir}\\{sub} • {free}")

  def _paste(self, entry):
    try:
      t = self.root.clipboard_get()
      if t:
        entry.delete(0, tk.END)
        entry.insert(0, str(t).strip())
        entry.focus_set()
        if entry is getattr(self, "url_entry", None):
          self.root.after(350, self._preview_url)
    except Exception:
      pass

  def _schedule_auto_preview(self, _event=None):
    pending = getattr(self, "_auto_preview_after_id", None)
    if pending:
      try:
        self.root.after_cancel(pending)
      except Exception:
        pass
    self._auto_preview_after_id = self.root.after(900, self._preview_url)

  def _bind_shortcuts(self):
    try:
      self.root.bind_all("<Control-d>", lambda e: self._download_url())
      self.root.bind_all(
          "<Control-s>", lambda e: self._switch_page("settings")
      )
      self.root.bind_all("<Control-q>", lambda e: self._switch_page("queue"))
      self.root.bind_all("<Control-h>", lambda e: self._switch_page("history"))
      self.root.bind_all("<Control-p>", lambda e: self._preview_url())
      self.root.bind_all("<F5>", lambda e: self._run_speed_test())
      self.root.bind_all("<Escape>", lambda e: self._switch_page("home"))
    except Exception:
      pass

  def _start_clipboard_monitor(self):
    def monitor():
      last = ""
      while True:
        try:
          if self.settings.get("clipboard_monitor"):
            cur = self.root.clipboard_get()
            if cur and cur != last and (
                "youtube.com" in cur or "youtu.be" in cur
            ):
              last = cur
              self.root.after(0, lambda c=cur: self._auto_fill(c))
          time.sleep(1.5)
        except Exception:
          time.sleep(2)

    threading.Thread(target=monitor, daemon=True).start()

  def _auto_fill(self, url):
    if self.active_page == "home":
      self.url_entry.delete(0, tk.END)
      self.url_entry.insert(0, url)
      self.root.after(350, self._preview_url)
      Toast.show(
          self.root,
          "Link Detected",
          url[:50],
          accent=self.theme["primary"],
      )

  def _preview_url(self):
    url = self.url_entry.get().strip()
    if not url:
      return
    Toast.show(
        self.root,
        "Fetching",
        "Loading media info...",
        accent=self.theme["primary"],
    )
    threading.Thread(
        target=self._preview_worker, args=(url,), daemon=True
    ).start()

  def _preview_worker(self, url):
    info = get_video_info(url)
    self.root.after(0, lambda: self._show_preview(info))

  def _show_preview(self, info):
    t = self.theme
    if "error" in info:
      Toast.show(
          self.root,
          "Preview Failed",
          clean_str(info["error"])[:50],
          accent=t["danger"],
      )
      return
    for w in self.preview_frame.winfo_children():
      w.destroy()
    self.preview_frame.pack(fill="x", pady=(4, 0))
    inner = tk.Frame(self.preview_frame, bg=t["surface"], padx=8, pady=6)
    inner.pack(fill="x")

    txt = tk.Frame(inner, bg=t["surface"])
    txt.pack(side="left", fill="both", expand=True)

    tk.Label(
        txt,
        text=info.get("title", "Unknown")[:52],
        font=("Segoe UI", 8, "bold"),
        bg=t["surface"],
        fg=t["text"],
        anchor="w",
        wraplength=340,
        justify="left",
    ).pack(fill="x")
    dur = info.get("duration", 0)
    mins, secs = divmod(int(dur), 60)
    size = (
        format_bytes(info.get("size_estimate", 0))
        if info.get("size_estimate")
        else "?"
    )
    tk.Label(
        txt,
        text=(
            f"{info.get('uploader', '')[:24]} • {mins}:{secs:02d} • {size} •"
            f" {info.get('formats', 0)} fmt"
        ),
        font=("Segoe UI", 7),
        bg=t["surface"],
        fg=t["text_muted"],
        anchor="w",
    ).pack(fill="x", pady=(2, 0))

    close_btn = tk.Label(
        inner,
        text="✕",
        font=("Segoe UI", 10, "bold"),
        bg=t["surface"],
        fg=t["text_muted"],
        cursor="hand2",
    )
    close_btn.pack(side="right")
    close_btn.bind(
        "<ButtonPress-1>", lambda _: self.preview_frame.pack_forget()
    )

  def _download_url(self):
    u = self.url_entry.get().strip()
    if not u:
      safe_showwarning("No URL", "Paste a URL into Direct Link first.")
      return
    self.url_entry.delete(0, tk.END)
    self.preview_frame.pack_forget()
    self._enqueue(u, noplaylist=True)

  def _enqueue(
      self,
      url,
      mode=None,
      quality=None,
      fmt=None,
      clip_range=None,
      noplaylist=True,
  ):
    url = (url or "").strip()
    if not url:
      return
    if self.settings.get("duplicate_guard", True) and not clip_range:
      already = any(
          h.get("url") == url and h.get("status") == "completed"
          for h in self.history
      )
      if already:
        if not messagebox.askyesno(
            "Duplicate Detected",
            "This URL was already downloaded.\nDownload it again?",
        ):
          return

    m = (mode or self.mode_var.get()).lower()
    if m not in ("video", "audio"):
      m = "video"
    vq = AUDIO_QUALITIES if m == "audio" else VIDEO_QUALITIES
    q = quality or self.quality_var.get()
    if q not in vq:
      q = "Best"
    vf = AUDIO_FORMATS if m == "audio" else VIDEO_FORMATS
    default_f = "MP3" if m == "audio" else "MP4"
    cur_f = (fmt or self.format_var.get() or default_f).upper()
    f = cur_f if cur_f in vf else default_f

    self.queue.add(
        url, m, q, f, clip_range=clip_range, noplaylist=noplaylist
    )
    self.total_downloads += 1
    self.counter_lbl.config(text=f"📥 {self.total_downloads}")
    Toast.show(
        self.root,
        "Queued",
        f"{m.upper()} • {q} • {f}",
        accent=self.theme["primary"],
    )
    self._refresh_queue_list()

  def _queue_worker(self):
    while True:
      try:
        if not self.queue.paused:
          item = self.queue.next_queued()
          if item:
            with self._queue_processing_lock:
              self.queue.update(item.id, status="downloading")
              self.root.after(0, self._refresh_queue_list)
              self._process_item(item)
            if not self.queue.has_pending():
              act = self.power_after_var.get()
              if act in ("Shutdown", "Sleep"):
                self.root.after(0, lambda: self.power_after_var.set("None"))
                trigger_power_action(act)
        time.sleep(0.4)
      except Exception:
        time.sleep(1)

  def _process_item(self, item):
    try:
      title = self._download_single(item)
      self.queue.update(
          item.id, status="completed", progress=100.0, title=title
      )
      self.history.append({
          "title": title,
          "url": item.url,
          "mode": item.mode,
          "quality": item.quality,
          "format": item.format,
          "status": "completed",
          "time": time.time(),
      })
      save_json(path_history(), self.history[-500:])
      self.root.after(0, self._refresh_queue_list)
      self.root.after(0, self._refresh_history_list)
      self.root.after(
          0,
          lambda t=title: Toast.show(
              self.root, "Complete", t[:50], accent=self.theme["success"]
          ),
      )
      self.root.after(0, self._hide_progress)
      if self.settings.get("sound_effects"):
        try:
          import winsound

          winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
          pass
    except Exception as e:
      err_msg = clean_str(str(e), "Skipped / Failed")
      self.queue.update(item.id, status="failed", error=err_msg)
      self.history.append({
          "title": item.title if item.title != "Fetching..." else item.url[:40],
          "url": item.url,
          "mode": item.mode,
          "status": "failed",
          "time": time.time(),
      })
      save_json(path_history(), self.history[-500:])
      self.root.after(0, self._refresh_queue_list)
      self.root.after(0, self._refresh_history_list)
      self.root.after(
          0,
          lambda m=err_msg: Toast.show(
              self.root, "Skipped", m[:60], accent=self.theme["danger"]
          ),
      )
      self.root.after(0, self._hide_progress)

  def _download_direct_file(self, item, hook):
    parsed = urllib.parse.urlparse(item.url)
    if parsed.scheme.lower() not in ("http", "https"):
      return None

    request = urllib.request.Request(
        item.url, headers={"User-Agent": BROWSER_UA}
    )
    try:
      response = urllib.request.urlopen(request, timeout=25)
    except Exception:
      return None
    content_type = (
        (response.headers.get("Content-Type") or "")
        .split(";", 1)[0]
        .strip()
        .lower()
    )
    disposition = response.headers.get("Content-Disposition", "")
    url_name = os.path.basename(urllib.parse.unquote(parsed.path))
    direct_ext = os.path.splitext(url_name)[1].lower()
    file_exts = {
        ".apk",
        ".xapk",
        ".zip",
        ".rar",
        ".7z",
        ".exe",
        ".msi",
        ".pdf",
        ".mp3",
        ".mp4",
        ".mkv",
        ".webm",
        ".m4a",
        ".wav",
        ".flac",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".csv",
        ".iso",
        ".torrent",
    }
    is_file = (
        direct_ext in file_exts
        or "attachment" in disposition.lower()
        or content_type.startswith(
            ("application/", "audio/", "video/", "image/")
        )
    )
    if not is_file or content_type in ("text/html", "application/xhtml+xml"):
      response.close()
      return None

    name = ""
    m = re.search(r"filename\*?=(?:UTF-8\'\')?([^;]+)", disposition, re.I)
    if m:
      name = urllib.parse.unquote(m.group(1).strip().strip('"'))
    if not name:
      name = url_name
    if not name or name in ("", ".", ".."):
      name = "downloaded_file"
    if not os.path.splitext(name)[1]:
      mime_map = {
          "application/vnd.android.package-archive": ".apk",
          "application/zip": ".zip",
          "application/pdf": ".pdf",
          "video/mp4": ".mp4",
          "audio/mpeg": ".mp3",
          "image/jpeg": ".jpg",
          "image/png": ".png",
      }
      name += mime_map.get(content_type, ".bin")
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    folder = get_mode_dir(self.download_dir, item.mode)
    os.makedirs(folder, exist_ok=True)
    part_path = os.path.join(folder, f"{name}.noxpart")
    final_path = os.path.join(folder, name)
    if os.path.exists(final_path):
      stem, ext = os.path.splitext(name)
      final_path = os.path.join(folder, f"{stem}_{int(time.time())}{ext}")
      name = os.path.basename(final_path)

    total = int(response.headers.get("Content-Length") or 0)
    downloaded = 0
    started = time.time()
    try:
      with open(part_path, "wb") as f:
        while True:
          while self.queue.paused:
            time.sleep(0.3)
          chunk = response.read(256 * 1024)
          if not chunk:
            break
          f.write(chunk)
          downloaded += len(chunk)
          if total:
            pct = downloaded / total * 100
            speed = downloaded / max(time.time() - started, 0.1)
            eta = max(0, total - downloaded) / max(speed, 1)
            self.queue.update(
                item.id,
                progress=pct,
                speed=f"{format_bytes(speed)}/s",
                eta=f"{int(eta)}s",
            )
            self.root.after(
                0,
                lambda p=pct, n=name: self._show_progress(
                    p, f"Downloading {n[:30]}", "Direct file download"
                ),
            )
      if downloaded == 0 or not os.path.isfile(part_path):
        raise RuntimeError("Empty file received.")
      os.replace(part_path, final_path)
      if not os.path.isfile(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError("Saved file is empty.")
    except Exception:
      for p_clean in (part_path, final_path):
        try:
          if os.path.exists(p_clean):
            os.remove(p_clean)
        except OSError:
          pass
      raise
    finally:
      response.close()
    return name

  def _collect_saved_files(self, info, folder):
    saved = []
    if isinstance(info, dict):
      req_dl = info.get("requested_downloads") or []
      for rd in req_dl:
        fp = rd.get("filepath")
        if fp and os.path.isfile(fp) and os.path.getsize(fp) > 0:
          saved.append(fp)
      if info.get("entries"):
        for e in info["entries"]:
          if e:
            saved.extend(self._collect_saved_files(e, folder))
    return list(dict.fromkeys(saved))

  def _cleanup_leftovers(self, folder):
    img_exts = (".jpg", ".jpeg", ".png", ".webp", ".avif")
    try:
      for root, _, files in os.walk(folder):
        for fn in files:
          fp = os.path.join(root, fn)
          lower = fn.lower()
          if lower.endswith((".part", ".ytdl", ".temp", ".noxpart")):
            try:
              if os.path.isfile(fp):
                os.remove(fp)
            except Exception:
              pass
          elif lower.endswith(img_exts):
            try:
              if os.path.isfile(fp):
                os.remove(fp)
            except Exception:
              pass
          else:
            try:
              if os.path.isfile(fp) and os.path.getsize(fp) == 0:
                os.remove(fp)
            except Exception:
              pass
    except Exception:
      pass

  def _download_single(self, item):
    def hook(d):
      while self.queue.paused:
        time.sleep(0.3)
      info_dict = d.get("info_dict") or {}
      if info_dict.get("title") and item.title == "Fetching...":
        item.title = str(info_dict["title"])
        self.queue.update(item.id, title=item.title)
      st = d.get("status")
      if st == "downloading":
        pct = parse_pct(d)
        sp = clean_str(d.get("_speed_str"))
        eta = clean_str(d.get("_eta_str"))
        self.queue.update(item.id, progress=pct, speed=sp, eta=eta)
        try:
          mbps = 0.0
          if sp and sp != "--":
            val = float(sp.split()[0])
            mbps = val
            if "K" in sp:
              mbps /= 1000
            elif "G" in sp:
              mbps *= 1000
        except Exception:
          mbps = 0
        self.root.after(
            0,
            lambda p=pct, s=sp, e=eta, m=mbps: (
                self._show_progress(
                    p,
                    f"Downloading {item.title[:30]}",
                    f"Speed: {s} | ETA: {e}",
                ),
                self.speed_graph.add(m),
            ),
        )
      elif st == "finished":
        self.root.after(
            0, lambda: self._show_progress(99.0, "Saving...", "Finalizing...")
        )

    direct_title = self._download_direct_file(item, hook)
    if direct_title:
      return direct_title

    has_ffmpeg = bool(find_ffmpeg_dir())
    target_folder = get_mode_dir(self.download_dir, item.mode)
    info = None
    last_err = None

    try:
      for safe_mode in (False, True):
        opts = build_ydl_opts(
            item,
            self.settings,
            self.download_dir,
            hook,
            safe_mode=safe_mode,
            has_ffmpeg=has_ffmpeg,
        )
        try:
          with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(item.url, download=True)
          if info is not None:
            break
        except Exception as err:
          last_err = clean_str(str(err))
          if safe_mode:
            raise RuntimeError(last_err) from err
    finally:
      self._cleanup_leftovers(target_folder)

    if info is None:
      raise RuntimeError(last_err or "No media found.")

    saved_files = self._collect_saved_files(info, target_folder)
    if not saved_files:
      recent_files = []
      for root, _, files in os.walk(target_folder):
        for fn in files:
          fp = os.path.join(root, fn)
          if (
              os.path.isfile(fp)
              and os.path.getsize(fp) > 0
              and not fn.lower().endswith((
                  ".part",
                  ".ytdl",
                  ".temp",
                  ".noxpart",
                  ".jpg",
                  ".jpeg",
                  ".png",
                  ".webp",
              ))
              and os.path.getmtime(fp) >= item.added_at - 5
          ):
            recent_files.append(fp)
      if not recent_files:
        raise RuntimeError(last_err or "File could not be verified on storage.")

    if isinstance(info, dict) and info.get("title"):
      return str(info["title"])
    if saved_files:
      return os.path.splitext(os.path.basename(saved_files[0]))[0]
    return item.title if item.title != "Fetching..." else "Media"

  def _show_progress(self, pct, status, detail):
    if not self.progress_card.winfo_ismapped():
      self.progress_card.pack(fill="x", padx=10, pady=(0, 4))
      self.root.geometry(f"{self.WIN_W}x{self.PROG_H}")
    v = max(0, min(100, float(pct)))
    self.progress_bar["value"] = v
    self.percent_var.set(f"{v:.1f}%")
    self.status_var.set(status)
    self.detail_var.set(detail)

  def _hide_progress(self):
    if self.progress_card.winfo_ismapped():
      self.progress_card.pack_forget()
      self.root.geometry(f"{self.WIN_W}x{self.WIN_H}")

  def _refresh_queue_list(self):
    try:
      self.queue_list.delete(0, tk.END)
      icons = {
          "queued": "⏳",
          "downloading": "⬇",
          "completed": "✔",
          "failed": "✖",
          "paused": "⏸",
      }
      for it in self.queue.all():
        ic = icons.get(it.status, "•")
        line = (
            f"{ic} [{it.progress:5.1f}%] {it.title[:34]} "
            f" ({it.mode.upper()} {it.quality})"
        )
        self.queue_list.insert(tk.END, line)
        if it.status == "completed":
          self.queue_list.itemconfig(tk.END, fg=self.theme["success"])
        elif it.status == "failed":
          self.queue_list.itemconfig(tk.END, fg=self.theme["danger"])
        elif it.status == "downloading":
          self.queue_list.itemconfig(tk.END, fg=self.theme["primary"])
    except Exception:
      pass

  def _toggle_pause(self):
    self.queue.paused = not self.queue.paused
    if self.queue.paused:
      self.pause_lbl.config(text="▶ Resume", bg=self.theme["success"])
      self.pause_btn.set_colors(
          fill=self.theme["success"],
          outline=self.theme["border"],
          hover="#059669",
      )
      Toast.show(
          self.root, "Paused", "Queue paused", accent=self.theme["warning"]
      )
    else:
      self.pause_lbl.config(text="⏸ Pause", bg=self.theme["warning"])
      self.pause_btn.set_colors(
          fill=self.theme["warning"],
          outline=self.theme["border"],
          hover="#D97706",
      )
      Toast.show(
          self.root, "Resumed", "Queue running", accent=self.theme["success"]
      )

  def _delete_queue_item(self):
    sel = self.queue_list.curselection()
    if not sel:
      return
    items = self.queue.all()
    if sel[0] < len(items):
      self.queue.remove(items[sel[0]].id)
      self._refresh_queue_list()

  def _clear_queue_done(self):
    self.queue.clear_done()
    self._refresh_queue_list()

  def _refresh_history_list(self):
    try:
      self.history_list.delete(0, tk.END)
      query = (
          self.hist_search.get().lower().strip()
          if hasattr(self, "hist_search")
          else ""
      )
      for h in reversed(self.history[-300:]):
        title = h.get("title", "?")
        if query and query not in title.lower():
          continue
        st = h.get("status", "?")
        ic = "✔" if st == "completed" else "✖"
        mode = h.get("mode", "").upper()
        self.history_list.insert(tk.END, f"{ic} {title[:44]} [{mode}]")
        self.history_list.itemconfig(
            tk.END,
            fg=(
                self.theme["success"]
                if st == "completed"
                else self.theme["danger"]
            ),
        )
    except Exception:
      pass

  def _clear_history(self):
    if messagebox.askyesno("Clear History", "Delete all download history?"):
      self.history = []
      save_json(path_history(), [])
      self._refresh_history_list()

  def _open_folder(self):
    try:
      os.startfile(self.download_dir)
    except Exception as e:
      safe_showerror("Error", str(e))

  def _choose_folder(self):
    d = filedialog.askdirectory(initialdir=self.download_dir)
    if d:
      self.download_dir = d
      self.settings["download_dir"] = d
      save_settings(self.settings)
      self._refresh_dir()

  def _refresh_favorites_list(self):
    try:
      self.fav_list.delete(0, tk.END)
      for fav in self.favorites:
        self.fav_list.insert(
            tk.END, f"⭐ {fav.get('title', fav.get('url', '?'))[:48]}"
        )
    except Exception:
      pass

  def _add_favorite(self):
    url = self.url_entry.get().strip()
    if not url:
      safe_showwarning(
          "No URL", "Paste a URL in Direct Link first, then click Add."
      )
      return
    title = url[:50]
    try:
      info = get_video_info(url)
      if "title" in info:
        title = info["title"]
    except Exception:
      pass
    self.favorites.append({"url": url, "title": title, "time": time.time()})
    save_json(path_favorites(), self.favorites)
    self._refresh_favorites_list()
    Toast.show(
        self.root, "Added", title[:45], accent=self.theme["success"]
    )

  def _download_favorite(self):
    sel = self.fav_list.curselection()
    if not sel:
      return
    if sel[0] < len(self.favorites):
      self._enqueue(self.favorites[sel[0]]["url"], noplaylist=True)

  def _remove_favorite(self):
    sel = self.fav_list.curselection()
    if not sel:
      return
    if sel[0] < len(self.favorites):
      self.favorites.pop(sel[0])
      save_json(path_favorites(), self.favorites)
      self._refresh_favorites_list()

  def _media_limit(self):
    try:
      return max(0, int(self.settings.get("max_media_limit", 0)))
    except Exception:
      return 0

  def _search_download(self):
    if self.search_running:
      self.search_stop.set()
      self.search_lbl.config(text="🔍 Find")
      return
    q = self.search_entry.get().strip()
    if not q:
      safe_showwarning("No Query", "Enter search keywords first.")
      return
    self.search_stop.clear()
    self.search_running = True
    self.search_lbl.config(text="⏹ Stop")
    m, ql, f = (
        self.mode_var.get(),
        self.quality_var.get(),
        self.format_var.get(),
    )
    cap = self._media_limit()
    self._show_progress(
        0, f"Searching: {q}", f"Limit: {cap if cap > 0 else 'Unlimited'}"
    )
    threading.Thread(
        target=self._search_worker, args=(q, m, ql, f, cap), daemon=True
    ).start()

  def _search_worker(self, query, mode, quality, fmt, cap):
    try:
      done = 0
      rank = 1
      empty = 0
      while not self.search_stop.is_set() and (cap <= 0 or done < cap):
        opts = {
            "extract_flat": True,
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "nocolor": True,
            "playliststart": rank,
            "playlistend": rank,
        }
        try:
          with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(
                f"ytsearch{rank}:{query}", download=False
            )
        except Exception:
          empty += 1
          if empty >= 3:
            break
          rank += 1
          time.sleep(0.5)
          continue
        rank += 1
        entries = (
            [e for e in (result.get("entries") or []) if e]
            if isinstance(result, dict)
            else []
        )
        if not entries:
          empty += 1
          if empty >= 3:
            break
          time.sleep(0.5)
          continue
        empty = 0
        item = entries[-1]
        vu = item.get("webpage_url") or item.get("url") or ""
        if not vu:
          vid = item.get("id", "")
          if vid:
            vu = f"https://www.youtube.com/watch?v={vid}"
        if not vu:
          continue
        title = item.get("title", "Song")
        done += 1
        self.root.after(
            0,
            lambda t=title, n=done: self._show_progress(
                0,
                f"Search #{n}/{cap if cap > 0 else '∞'}: {t[:24]}",
                "Queued",
            ),
        )
        self._enqueue(vu, mode, quality, fmt, noplaylist=True)
        time.sleep(0.3)
      self.root.after(0, self._hide_progress)
      self.root.after(
          0,
          lambda d=done: Toast.show(
              self.root,
              "Search Done",
              f"{d} items queued",
              accent=self.theme["success"],
          ),
      )
    except Exception as e:
      self.root.after(0, self._hide_progress)
      self.root.after(
          0,
          lambda err=clean_str(str(e)): Toast.show(
              self.root, "Search Failed", err[:50], accent=self.theme["danger"]
          ),
      )
    finally:
      self.search_running = False
      self.root.after(0, lambda: self.search_lbl.config(text="🔍 Find"))

  def _site_download(self):
    u = self.site_entry.get().strip()
    if not u:
      safe_showwarning("No URL", "Enter a webpage URL first.")
      return
    if not u.startswith(("http://", "https://")):
      u = "https://" + u
    m, q, f = self.mode_var.get(), self.quality_var.get(), self.format_var.get()
    cap = self._media_limit()
    self._show_progress(
        0,
        f"Scanning ({cap if cap > 0 else 'Unlimited'})...",
        u[:45],
    )
    threading.Thread(
        target=self._site_worker, args=(u, m, q, f, cap), daemon=True
    ).start()

  def _site_worker(self, url, mode, quality, fmt, cap):
    try:
      opts = {
          "extract_flat": "in_playlist",
          "skip_download": True,
          "quiet": True,
          "no_warnings": True,
          "nocolor": True,
      }
      items = []
      try:
        with yt_dlp.YoutubeDL(opts) as ydl:
          info = ydl.extract_info(url, download=False)
        if isinstance(info, dict):
          if info.get("entries"):
            for e in info["entries"]:
              if e:
                vu = e.get("webpage_url") or e.get("url")
                if vu:
                  items.append(vu)
          else:
            vu = info.get("webpage_url") or info.get("url") or url
            items.append(vu)
      except Exception:
        items.append(url)
      if cap > 0:
        items = items[:cap]
      for i, vu in enumerate(items, 1):
        self.root.after(
            0,
            lambda i=i, n=len(items): self._show_progress(
                0, f"Site {i}/{n}", "Queued"
            ),
        )
        self._enqueue(vu, mode, quality, fmt, noplaylist=True)
        time.sleep(0.3)
      self.root.after(0, self._hide_progress)
      self.root.after(
          0,
          lambda n=len(items): Toast.show(
              self.root,
              "Scan Done",
              f"{n} queued",
              accent=self.theme["success"],
          ),
      )
    except Exception as e:
      self.root.after(0, self._hide_progress)
      self.root.after(
          0,
          lambda err=clean_str(str(e)): Toast.show(
              self.root, "Scan Failed", err[:50], accent=self.theme["danger"]
          ),
      )

  def _measure_ping(self):
    try:
      req = urllib.request.Request(
          "https://speed.cloudflare.com/__down?bytes=1",
          headers={"User-Agent": BROWSER_UA},
      )
      t = time.perf_counter()
      with urllib.request.urlopen(req, timeout=6) as r:
        r.read(64)
      return (time.perf_counter() - t) * 1000.0
    except Exception:
      return 0.0

  def _measure_dl_burst(self):
    total = 0
    t0 = time.perf_counter()
    try:
      req = urllib.request.Request(
          "https://speed.cloudflare.com/__down?bytes=6000000",
          headers={"User-Agent": BROWSER_UA},
      )
      with urllib.request.urlopen(req, timeout=8) as r:
        while not self.speed_stop.is_set():
          chunk = r.read(131072)
          if not chunk:
            break
          total += len(chunk)
          el = time.perf_counter() - t0
          if el >= 1.2 or total >= 6_000_000:
            break
    except Exception:
      pass
    el = max(0.05, time.perf_counter() - t0)
    return (total * 8.0) / (el * 1e6)

  def _measure_ul_burst(self):
    try:
      payload = os.urandom(1_000_000)
      req = urllib.request.Request(
          "https://speed.cloudflare.com/__up",
          data=payload,
          headers={
              "User-Agent": BROWSER_UA,
              "Content-Type": "application/octet-stream",
          },
          method="POST",
      )
      t = time.perf_counter()
      with urllib.request.urlopen(req, timeout=8) as r:
        r.read()
      el = max(0.05, time.perf_counter() - t)
      return (len(payload) * 8.0) / (el * 1e6)
    except Exception:
      return None

  def _run_speed_test(self):
    if self.speed_testing:
      self.speed_stop.set()
      return
    self.speed_testing = True
    self.speed_stop.clear()
    self._display_speed = 0.0
    self._set_gauge(0.0, self.theme["success"])
    self.go_btn.set_colors(
        fill=self.theme["danger"],
        outline=self.theme["border"],
        hover="#DC2626",
        enabled=True,
    )
    self.go_lbl.config(text="⏹ STOP", bg=self.theme["danger"])

    def smooth_ramp(target_mbps, color, steps=18, step_delay=0.06):
      for i in range(1, steps + 1):
        if self.speed_stop.is_set():
          return
        frac = 1.0 - ((1.0 - (i / steps)) ** 3)
        val = self._display_speed + (target_mbps - self._display_speed) * frac
        self._display_speed = val
        self.root.after(0, lambda v=val, c=color: self._set_gauge(v, c))
        time.sleep(step_delay)

    def worker():
      start_ts = time.monotonic()
      deadline = start_ts + self.SPEED_DURATION_SEC
      last_ul_ts = 0.0
      final_ul = None
      try:
        while not self.speed_stop.is_set() and time.monotonic() < deadline:
          rem = max(0, int(deadline - time.monotonic()))
          rem_str = f"{rem // 60:02d}:{rem % 60:02d}"

          self.root.after(
              0,
              lambda r=rem_str: self.phase_lbl.config(
                  text=f"Ping • Left {r}", fg=self.theme["primary"]
              ),
          )
          ping = self._measure_ping()
          if self.speed_stop.is_set():
            break
          self.root.after(
              0, lambda p=ping: self.ping_var.set(f"Ping: {p:.0f} ms")
          )

          self.root.after(
              0,
              lambda r=rem_str: self.phase_lbl.config(
                  text=f"Download • Left {r}", fg=self.theme["success"]
              ),
          )
          dl = self._measure_dl_burst()
          smooth_ramp(dl, self.theme["success"])
          if self.speed_stop.is_set():
            break
          self.root.after(
              0, lambda d=dl: self.dl_var.set(f"Download: {d:.2f} Mbps")
          )

          now = time.monotonic()
          if now - last_ul_ts >= 15.0 or final_ul is None:
            last_ul_ts = now
            self.root.after(
                0,
                lambda r=rem_str: self.phase_lbl.config(
                    text=f"Upload • Left {r}", fg=self.theme["accent"]
                ),
            )
            ul = self._measure_ul_burst()
            if ul is not None:
              final_ul = ul
              smooth_ramp(ul, self.theme["accent"], steps=14, step_delay=0.055)
              self.root.after(
                  0, lambda u=ul: self.ul_var.set(f"Upload: {u:.2f} Mbps")
              )
            else:
              self.root.after(0, lambda: self.ul_var.set("Upload: N/A"))

          time.sleep(0.25)

        tot_min = int((time.monotonic() - start_ts) // 60)
        self.root.after(
            0,
            lambda m=tot_min: self.phase_lbl.config(
                text=f"Finished ({m}m)", fg=self.theme["success"]
            ),
        )
      except Exception as e:
        self.root.after(
            0,
            lambda err=e: self.phase_lbl.config(
                text=str(err)[:45], fg=self.theme["danger"]
            ),
        )
      finally:
        self.speed_testing = False
        self.root.after(
            0,
            lambda: (
                self.go_btn.set_colors(
                    fill=self.theme["success"],
                    outline=self.theme["border"],
                    hover="#059669",
                    enabled=True,
                ),
                self.go_lbl.config(text="▶ GO 30m", bg=self.theme["success"]),
            ),
        )

    threading.Thread(target=worker, daemon=True).start()

  def _set_gauge(self, mbps, color):
    if not hasattr(self, "_gauge_center"):
      return
    gcx, gcy, grad = self._gauge_center
    cap = max(0.0, min(100.0, float(mbps)))
    frac = cap / 100.0
    self.gauge.itemconfig(self._gauge_arc, extent=-180 * frac, outline=color)
    ang = math.pi * (1 - frac)
    nx = gcx + math.cos(ang) * (grad - 10)
    ny = gcy - math.sin(ang) * (grad - 10)
    self.gauge.coords(self._gauge_needle, gcx, gcy, nx, ny)
    self.speed_big.config(text=f"{mbps:.2f} Mbps", fg=color)

  def _pick_install(self):
    sel = filedialog.askopenfilename(
        title="Select file",
        filetypes=[
            ("Android Packages", "*.apk;*.xapk"),
            ("APK Files", "*.apk"),
            ("XAPK Files", "*.xapk"),
        ],
    )
    if sel:
      self.apk_var.set(sel)

  def _run_install(self):
    if self.installer_running:
      return
    fp = self.apk_var.get().strip().strip('"')
    if not fp or not os.path.isfile(fp):
      safe_showwarning("Missing File", "Select a valid file first.")
      return
    self.installer_running = True
    self._show_progress(
        0, f"Installing: {os.path.basename(fp)[:32]}", "Preparing..."
    )
    threading.Thread(
        target=self._install_worker, args=(fp,), daemon=True
    ).start()

  def _install_worker(self, fp):
    fn = os.path.basename(fp)
    ext = os.path.splitext(fp)[1].lower()
    try:
      if ext in (".apk", ".xapk"):
        adb = find_adb()
        if not adb:
          raise RuntimeError("ADB not found")
        if ext == ".xapk":
          tmp = tempfile.mkdtemp(prefix="nox_xapk_")
          try:
            with zipfile.ZipFile(fp, "r") as zf:
              zf.extractall(tmp)
            apks = []
            for root, _, files in os.walk(tmp):
              for f in files:
                if f.lower().endswith(".apk"):
                  apks.append(os.path.join(root, f))
            if not apks:
              raise RuntimeError("No APK inside XAPK")
            cmd = [adb, "install-multiple", "-r"] + sorted(apks)
          finally:
            pass
        else:
          tmp = None
          cmd = [adb, "install", "-r", fp]
        try:
          p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
          out = (p.stdout or "") + (p.stderr or "")
          if p.returncode != 0 or "Failure" in out:
            raise RuntimeError(out.strip() or "ADB install failed")
        finally:
          if tmp and os.path.isdir(tmp):
            shutil.rmtree(tmp, ignore_errors=True)
      else:
        raise RuntimeError("Only .APK and .XAPK files are supported")
      self.installer_running = False
      self.root.after(0, self._hide_progress)
      self.root.after(
          0,
          lambda: Toast.show(
              self.root, "Done", fn[:50], accent=self.theme["success"]
          ),
      )
    except Exception as e:
      self.installer_running = False
      self.root.after(0, self._hide_progress)
      self.root.after(
          0,
          lambda err=clean_str(str(e)): Toast.show(
              self.root, "Failed", err[:50], accent=self.theme["danger"]
          ),
      )

  def _start_tray(self):
    if not HAS_TRAY:
      return
    try:
      img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
      d = ImageDraw.Draw(img)
      d.ellipse([4, 4, 60, 60], fill="#10121C", outline="#00E5FF", width=3)
      d.ellipse([10, 10, 54, 54], outline="#FF2D95", width=2)
      d.polygon(
          [(18, 18), (30, 12), (46, 18), (46, 44), (30, 52), (18, 44)],
          fill="#191B2A",
          outline="#00E5FF",
      )
      d.text((20, 21), "PN", fill="#FFFFFF")

      def show(icon, item):
        self.root.after(0, self._restore)

      def quit_app(icon, item):
        self.root.after(0, self._exit_app)

      menu = pystray.Menu(
          pystray.MenuItem("Open PRIME NOX", show, default=True),
          pystray.MenuItem("Exit PRIME NOX", quit_app),
      )
      self.tray_icon = pystray.Icon("prime_nox", img, APP_NAME, menu)
      threading.Thread(target=self.tray_icon.run, daemon=True).start()
    except Exception:
      self.tray_icon = None

  def _restore(self):
    self.root.deiconify()
    self.root.lift()
    self.root.focus_force()

  def _start_http_server(self):
    app = self

    class H(BaseHTTPRequestHandler):

      def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

      def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

      def do_GET(self):
        if self.path in ("/", "/status"):
          self.send_response(200)
          self._cors()
          self.send_header("Content-Type", "application/json")
          self.end_headers()
          items = [
              {"title": i.title, "status": i.status, "progress": i.progress}
              for i in app.queue.all()
          ]
          self.wfile.write(json.dumps({"ok": True, "queue": items}).encode())
        else:
          self.send_response(404)
          self._cors()
          self.end_headers()

      def do_POST(self):
        if self.path != "/download":
          self.send_response(404)
          self._cors()
          self.end_headers()
          return
        try:
          n = int(self.headers.get("Content-Length", 0))
          data = json.loads(self.rfile.read(n).decode("utf-8"))
          url = (data.get("url") or "").strip()
          if not url:
            self.send_response(400)
            self._cors()
            self.end_headers()
            self.wfile.write(b'{"ok":false}')
            return
          app.root.after(
              0,
              lambda: app._enqueue(
                  url,
                  data.get("mode"),
                  data.get("quality"),
                  data.get("format"),
                  noplaylist=True,
              ),
          )
          self.send_response(200)
          self._cors()
          self.send_header("Content-Type", "application/json")
          self.end_headers()
          self.wfile.write(b'{"ok":true}')
        except Exception as e:
          self.send_response(500)
          self._cors()
          self.send_header("Content-Type", "application/json")
          self.end_headers()
          self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

      def log_message(self, *a):
        return

    try:
      self.server = HTTPServer(("127.0.0.1", 5678), H)
      threading.Thread(target=self.server.serve_forever, daemon=True).start()
    except Exception as e:
      print(f"HTTP error: {e}")

  def _auto_update_worker(self):
    try:
      updated, old, new = check_ytdlp_update()
      if updated:
        self.root.after(
            0,
            lambda: Toast.show(
                self.root,
                "yt-dlp Updated",
                f"{old} -> {new}",
                accent=self.theme["success"],
            ),
        )
    except Exception:
      pass

  def _cleanup_worker(self):
    try:
      days = self.settings.get("auto_cleanup_days", 0)
      if days > 0:
        removed = cleanup_old_files(self.download_dir, days)
        if removed > 0:
          self.root.after(
              0,
              lambda: Toast.show(
                  self.root,
                  "Cleanup",
                  f"{removed} removed",
                  accent=self.theme["warning"],
              ),
          )
    except Exception:
      pass

  def _hide_to_tray(self):
    if HAS_TRAY and self.tray_icon:
      self.root.withdraw()
      try:
        Toast.show(
            self.root,
            "PRIME NOX",
            "Running in background · Tray menu to exit",
            accent=self.theme.get("accent", "#00E5FF"),
            duration=2200,
        )
      except Exception:
        pass
    else:
      self.root.iconify()

  def _exit_app(self):
    self._on_close()

  def _on_close(self):
    self.search_stop.set()
    self.speed_stop.set()
    self.bg.stop()
    if hasattr(self, "server") and self.server:
      try:
        self.server.shutdown()
        self.server.server_close()
      except Exception:
        pass
    if self.tray_icon:
      try:
        self.tray_icon.stop()
      except Exception:
        pass
    self.root.destroy()


if __name__ == "__main__":
  try:
    root = tk.Tk()
    App(root)
    root.mainloop()
  except Exception:
    import traceback

    traceback.print_exc()
    input("Press Enter to exit...")