#!/usr/bin/env python
import gi
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import AppIndicator3, Gtk, GLib, Notify
from pynput.keyboard import GlobalHotKeys
import json
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import subprocess
import threading
import os
import tempfile
import pyperclip
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
USER_HOME = os.path.expanduser("~")
CONFIG_FILE = os.path.join(USER_HOME, ".config", "whisper-tray", "config.json")
ICON_DIR = SCRIPT_DIR

ICONS = {
    "idle": os.path.join(ICON_DIR, "icon-idle.svg"),
    "recording": os.path.join(ICON_DIR, "icon-recording.svg"),
    "processing": os.path.join(ICON_DIR, "icon-processing.svg"),
}

MODELS = {
    "tiny.en": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin", "disk": "75 MiB"},
    "base.en": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin", "disk": "142 MiB"},
    "small.en": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin", "disk": "466 MiB"},
    "medium.en": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.en.bin", "disk": "1.5 GiB"},
}

def load_config():
    default_config_dir = os.path.dirname(CONFIG_FILE)
    default_model_dir = os.path.join(USER_HOME, ".local", "share", "whisper_models")
    os.makedirs(default_config_dir, exist_ok=True)
    os.makedirs(default_model_dir, exist_ok=True)
    default_config = {
        "executable": os.path.join(SCRIPT_DIR, "whisper-tray-cli"),
        "model_path": os.path.join(default_model_dir, "ggml-base.en.bin"),
        "model_dir": default_model_dir,
        "hotkey": "<ctrl>+<alt>+h"
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = default_config.copy(); config.update(json.load(f))
            return config
    return default_config

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f: json.dump(config, f, indent=4)

class DownloadModelWindow(Gtk.Window):
    def __init__(self, parent):
        if isinstance(parent, SettingsWindow): self.parent_app = parent.parent
        else: self.parent_app = parent
        super().__init__(title="Download Model", modal=True, transient_for=self.parent_app.settings_win)
        self.set_border_width(10); self.set_position(Gtk.WindowPosition.CENTER)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6); self.add(vbox)
        vbox.pack_start(Gtk.Label(label="Model not found or failed to load."), False, False, 0)
        vbox.pack_start(Gtk.Label(label="Please select a model to download:"), False, False, 0)
        self.model_combo = Gtk.ComboBoxText(); vbox.pack_start(self.model_combo, False, False, 5)
        self.progress_bar = Gtk.ProgressBar(); vbox.pack_start(self.progress_bar, False, False, 5)
        hbox_buttons = Gtk.Box(spacing=6)
        self.download_button = Gtk.Button(label="Download"); self.download_button.connect("clicked", self.on_download_clicked)
        self.cancel_button = Gtk.Button(label="Cancel"); self.cancel_button.connect("clicked", lambda w: self.destroy())
        hbox_buttons.pack_start(self.download_button, True, True, 0); hbox_buttons.pack_start(self.cancel_button, True, True, 0)
        vbox.pack_start(hbox_buttons, False, False, 0)
        model_dir = self.parent_app.config["model_dir"]
        downloaded_models = [f for f in os.listdir(model_dir) if f.endswith(".bin")] if os.path.exists(model_dir) else []
        available_models = {name: data for name, data in MODELS.items() if f"ggml-{name}.bin" not in downloaded_models}
        if not available_models:
            vbox.pack_start(Gtk.Label(label="All models already downloaded!"), False, False, 0); self.download_button.set_sensitive(False)
        else:
            for name, data in available_models.items(): self.model_combo.append_text(f"{name} [Disk: {data['disk']}]")
            self.model_combo.set_active(0)

    def on_download_clicked(self, widget):
        self.download_button.set_sensitive(False); self.cancel_button.set_sensitive(False)
        if not (selected_text := self.model_combo.get_active_text()): return
        model_name = selected_text.split(" ")[0]
        model_dir = self.parent_app.config["model_dir"]; os.makedirs(model_dir, exist_ok=True)
        self.destination_path = os.path.join(model_dir, f"ggml-{model_name}.bin")
        self.progress_bar.set_text(f"Downloading {model_name}..."); self.progress_bar.set_show_text(True)
        threading.Thread(target=self._download_thread, args=(MODELS[model_name]["url"],), daemon=True).start()

    def _download_thread(self, url):
        try:
            urllib.request.urlretrieve(url, self.destination_path, self._reporthook)
            GLib.idle_add(self.on_download_finished)
        except Exception as e: GLib.idle_add(self.on_download_failed, str(e))

    def _reporthook(self, blocknum, blocksize, totalsize):
        if totalsize > 0: GLib.idle_add(self.progress_bar.set_fraction, min((blocknum * blocksize) / totalsize, 1.0))

    def on_download_finished(self):
        self.progress_bar.set_text("Download Complete")
        self.parent_app.config["model_path"] = self.destination_path; save_config(self.parent_app.config)
        if self.parent_app.settings_win and self.parent_app.settings_win.get_visible():
            self.parent_app.settings_win.populate_models()
            self.parent_app.settings_win.model_combo.set_active_id(self.destination_path)
        self.destroy()

    def on_download_failed(self, error_msg):
        self.progress_bar.set_text(f"Error: {error_msg}"); self.cancel_button.set_sensitive(True)

class SettingsWindow(Gtk.Window):
    def __init__(self, parent):
        super().__init__(title="Settings")
        self.parent = parent
        self.set_border_width(10); self.set_modal(True); self.set_position(Gtk.WindowPosition.CENTER)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10); self.add(vbox)
        self.exec_entry = Gtk.Entry(text=self.parent.config.get("executable", "whisper-cli"))
        vbox.pack_start(self._create_setting_row("Executable Name:", self.exec_entry), False, False, 0)
        self.dir_entry = Gtk.Entry(text=self.parent.config.get("model_dir"))
        self.dir_entry.connect("changed", lambda w: self.populate_models())
        vbox.pack_start(self._create_setting_row("Model Directory:", self.dir_entry), False, False, 0)
        self.model_combo = Gtk.ComboBoxText(entry_text_column=0)
        download_button = Gtk.Button(label="Download..."); download_button.connect("clicked", lambda w: DownloadModelWindow(self).show_all())
        model_box = Gtk.Box(spacing=6); model_box.pack_start(self.model_combo, True, True, 0); model_box.pack_start(download_button, False, False, 0)
        vbox.pack_start(self._create_setting_row("Whisper Model:", model_box), False, False, 0)
        self.populate_models()
        if self.parent.config.get("model_path") and os.path.exists(self.parent.config["model_path"]):
            self.model_combo.set_active_id(self.parent.config["model_path"])
        self.hotkey_entry = Gtk.Entry(text=self.parent.config.get("hotkey", "<ctrl>+<alt>+h"))
        vbox.pack_start(self._create_setting_row("Hotkey:", self.hotkey_entry), False, False, 0)
        save_button = Gtk.Button(label="Save and Close"); save_button.connect("clicked", self.on_save_clicked)
        hbox_buttons = Gtk.Box(spacing=6, margin_top=10); hbox_buttons.pack_end(save_button, False, False, 0)
        vbox.pack_start(hbox_buttons, False, False, 0)

    def _create_setting_row(self, label_text, widget):
        box = Gtk.Box(spacing=6); label = Gtk.Label(label=label_text, xalign=0)
        box.pack_start(label, False, False, 0); box.pack_start(widget, True, True, 0)
        return box

    def populate_models(self):
        self.model_combo.remove_all()
        model_dir = self.dir_entry.get_text()
        if os.path.isdir(model_dir):
            for f in sorted(os.listdir(model_dir)):
                if f.endswith(".bin"):
                    model_path = os.path.join(model_dir, f); self.model_combo.append(model_path, f)

    def on_save_clicked(self, widget):
        self.parent.config["executable"] = self.exec_entry.get_text()
        self.parent.config["model_dir"] = self.dir_entry.get_text()
        if active_id := self.model_combo.get_active_id(): self.parent.config["model_path"] = active_id
        hotkey_text = self.hotkey_entry.get_text().lower()
        replacements = {"control": "ctrl", "super": "super", "meta": "super", "win": "super"}
        for old, new in replacements.items(): hotkey_text = hotkey_text.replace(old, new)
        parts = hotkey_text.split('+')
        for i, part in enumerate(parts):
            p = part.strip()
            if p in ["ctrl", "alt", "shift", "super"] and not (p.startswith('<') and p.endswith('>')):
                parts[i] = f'<{p}>'
        self.parent.config["hotkey"] = '+'.join(parts)
        save_config(self.parent.config)
        self.parent._setup_hotkey()
        self.destroy(); self.parent.settings_win = None

class TrayApp:
    def __init__(self):
        self.config = load_config(); self.audio_frames = []; self.samplerate = 16000
        self.thread = None; self.settings_win = None; self.hotkey_listener = None
        self.indicator = AppIndicator3.Indicator.new("whisper-tray", ICONS["idle"], AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        Notify.init("Whisper Tray")
        self.menu = self._build_menu(); self.indicator.set_menu(self.menu)
        self._setup_hotkey(); self._change_state("idle")

    def _build_menu(self):
        menu = Gtk.Menu()
        self.record_item = Gtk.MenuItem.new_with_label("Record"); self.record_item.connect("activate", self.toggle_recording); menu.append(self.record_item)
        settings_item = Gtk.MenuItem.new_with_label("Settings"); settings_item.connect("activate", self.open_settings); menu.append(settings_item)
        quit_item = Gtk.MenuItem.new_with_label("Quit"); quit_item.connect("activate", self.quit_app); menu.append(quit_item)
        menu.show_all(); return menu

    def _send_notification(self, title, message, icon_name="whisper-tray"):
        """Helper to send a desktop notification using libnotify."""
        notification = Notify.Notification.new(title, message, icon_name)
        notification.show()
        print(f"[{title}] {message}")

    def _change_state(self, new_state):
        self.state = new_state
        state_map = {
            "idle":       {"icon": ICONS["idle"],       "label": "Record",         "sensitive": True},
            "recording":  {"icon": ICONS["recording"],  "label": "Stop Recording", "sensitive": True},
            "processing": {"icon": ICONS["processing"], "label": "Processing...",  "sensitive": False}
        }
        config = state_map.get(self.state, state_map["idle"])
        GLib.idle_add(lambda: self.indicator.set_icon_full(config["icon"], self.state.capitalize()))
        GLib.idle_add(lambda: self.record_item.set_label(config["label"]))
        GLib.idle_add(lambda: self.record_item.set_sensitive(config["sensitive"]))

    def open_settings(self, *args):
        if not self.settings_win or not self.settings_win.get_visible():
            self.settings_win = SettingsWindow(self)
            self.settings_win.show_all(); self.settings_win.present()

    def _setup_hotkey(self):
        if self.hotkey_listener and self.hotkey_listener.is_alive(): self.hotkey_listener.stop()
        if not (hotkey_str := self.config.get("hotkey")): return
        try:
            self.hotkey_listener = GlobalHotKeys({hotkey_str: lambda: GLib.idle_add(self.toggle_recording)})
            self.hotkey_listener.start()
        except Exception:
            msg = "The Super/Meta key is often reserved by the OS. Try a Ctrl/Alt combo." if "<super>" in hotkey_str else "In use by another app?"
            self._send_notification("Hotkey Error", f"Could not register '{hotkey_str}'. {msg}", "dialog-warning")

    def toggle_recording(self, *args):
        if self.state == "idle": self.start_recording()
        elif self.state == "recording": self.stop_recording_and_transcribe()

    def start_recording(self):
        self._change_state("recording"); self.audio_frames = []
        self.thread = threading.Thread(target=self._record_audio_thread, daemon=True); self.thread.start()

    def _record_audio_thread(self):
        try:
            with sd.InputStream(samplerate=self.samplerate, channels=1, dtype='int16') as stream:
                while self.state == "recording":
                    data, _ = stream.read(self.samplerate // 10)
                    if self.state == "recording": self.audio_frames.append(data)
        except Exception as e:
            self._send_notification("Audio Error", f"Could not open microphone: {e}", "dialog-error")
            GLib.idle_add(self._change_state, "idle")

    def stop_recording_and_transcribe(self):
        if self.state != "recording": return
        self._change_state("processing")
        if self.thread and self.thread.is_alive(): self.thread.join(timeout=0.2)
        if not self.audio_frames: self._change_state("idle"); return
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            self.temp_wav_path = tmp.name
            write(self.temp_wav_path, self.samplerate, np.concatenate(self.audio_frames, axis=0))
        self._send_notification("Whisper", "Transcribing audio...", ICONS["processing"])
        threading.Thread(target=self._transcribe_thread, daemon=True).start()

    def _transcribe_thread(self):
        try:
            if not os.path.exists(model_path := self.config["model_path"]): raise FileNotFoundError(f"Model file not found: {model_path}")
            executable = self.config.get("executable", "whisper-cli")
            cmd = [executable, "-m", model_path, "-f", self.temp_wav_path, "-nt", "-otxt"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
            pyperclip.copy(result.stdout.strip())
            self._send_notification("Transcription Complete", "Text copied to clipboard.")
        except FileNotFoundError:
            self._send_notification("Error", f"Executable '{self.config.get('executable')}' not found or model missing.", "dialog-error")
            GLib.idle_add(lambda: DownloadModelWindow(self).show_all())
        except subprocess.CalledProcessError as e:
            msg = e.stderr.strip()
            self._send_notification("Transcription Error", msg, "dialog-error")
            if "failed to load model" in msg: GLib.idle_add(lambda: DownloadModelWindow(self).show_all())
        except Exception as e:
            self._send_notification("Unexpected Error", str(e), "dialog-error")
        finally:
            if hasattr(self, 'temp_wav_path') and os.path.exists(self.temp_wav_path): os.remove(self.temp_wav_path)
            GLib.idle_add(self._change_state, "idle")

    def quit_app(self, *args):
        if self.hotkey_listener: self.hotkey_listener.stop()
        Notify.uninit()
        Gtk.main_quit()

if __name__ == "__main__":
    app = TrayApp()
    Gtk.main()