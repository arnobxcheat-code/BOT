import os
import threading
import yt_dlp
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.utils import platform


def get_android_download_dir():
  candidates = [
      "/storage/emulated/0/Download/PRIME_NOX",
      "/sdcard/Download/PRIME_NOX",
      os.path.join(os.path.expanduser("~"), "Downloads", "PRIME_NOX"),
      ".",
  ]
  for path in candidates:
    try:
      os.makedirs(path, exist_ok=True)
      if os.access(path, os.W_OK):
        return path
    except Exception:
      continue
  return "."


class PrimeNoxLayout(BoxLayout):

  def __init__(self, **kwargs):
    super().__init__(orientation="vertical", padding=16, spacing=10, **kwargs)

    self.add_widget(
        Label(
            text="PRIME NOX Downloader (Android)",
            font_size="20sp",
            bold=True,
            size_hint_y=None,
            height=44,
        )
    )

    self.url_input = TextInput(
        hint_text="Paste video or audio URL here...",
        multiline=False,
        size_hint_y=None,
        height=46,
    )
    self.add_widget(self.url_input)

    opt_row = BoxLayout(
        orientation="horizontal", spacing=10, size_hint_y=None, height=42
    )
    self.mode_spinner = Spinner(
        text="video",
        values=("video", "audio"),
        size_hint_x=0.5,
    )
    self.quality_spinner = Spinner(
        text="Best",
        values=("Best", "720p", "480p", "360p"),
        size_hint_x=0.5,
    )
    opt_row.add_widget(self.mode_spinner)
    opt_row.add_widget(self.quality_spinner)
    self.add_widget(opt_row)

    self.dl_btn = Button(
        text="Download Now",
        size_hint_y=None,
        height=50,
    )
    self.dl_btn.bind(on_press=self.on_download_press)
    self.add_widget(self.dl_btn)

    self.status_label = Label(
        text="Ready",
        font_size="14sp",
    )
    self.add_widget(self.status_label)

    if platform == "android":
      try:
        from android.permissions import Permission, request_permissions

        request_permissions([
            Permission.INTERNET,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
        ])
      except Exception:
        pass

  def set_status(self, text):
    Clock.schedule_once(lambda dt: setattr(self.status_label, "text", text), 0)

  def on_download_press(self, _instance):
    url = (self.url_input.text or "").strip()
    if not url.startswith(("http://", "https://")):
      self.set_status("Enter a valid http/https URL.")
      return

    self.dl_btn.disabled = True
    self.set_status("Starting download...")
    mode = self.mode_spinner.text
    quality = self.quality_spinner.text
    threading.Thread(
        target=self._download_worker, args=(url, mode, quality), daemon=True
    ).start()

  def _hook(self, d):
    if d.get("status") == "downloading":
      pct = (d.get("_percent_str") or "").strip()
      spd = (d.get("_speed_str") or "").strip()
      self.set_status(f"Downloading: {pct} | {spd}")
    elif d.get("status") == "finished":
      self.set_status("Saving file...")

  def _download_worker(self, url, mode, quality):
    try:
      out_dir = get_android_download_dir()
      outtmpl = os.path.join(out_dir, "%(title).60s.%(ext)s")

      opts = {
          "outtmpl": outtmpl,
          "noplaylist": True,
          "progress_hooks": [self._hook],
          "quiet": True,
          "no_warnings": True,
          "writethumbnail": False,
          "embedthumbnail": False,
      }

      if mode == "audio":
        opts["format"] = "bestaudio/best"
      else:
        q_map = {"720p": 720, "480p": 480, "360p": 360}
        if quality in q_map:
          h = q_map[quality]
          opts["format"] = f"best[height<={h}]/best"
        else:
          opts["format"] = "best"

      with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = (
            info.get("title") if isinstance(info, dict) else "Downloaded Media"
        )

      self.set_status(f"Done: {title[:40]}")
    except Exception as e:
      self.set_status(f"Error: {str(e)[:60]}")
    finally:
      Clock.schedule_once(lambda dt: setattr(self.dl_btn, "disabled", False), 0)


class PrimeNoxAndroidApp(App):

  def build(self):
    return PrimeNoxLayout()


if __name__ == "__main__":
  PrimeNoxAndroidApp().run()
