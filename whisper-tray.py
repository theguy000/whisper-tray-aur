#!/usr/bin/env python
import gi
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import AppIndicator3 as appindicator, Gtk as gtk, GLib, Notify
from pynput import keyboard
from pynput.keyboard import GlobalHotKeys
import json
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import subprocess
import threading
import os
import tempfile
import urllib.request
import logging
import sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
USER_HOME = os.path.expanduser("~")
CONFIG_FILE = os.path.join(USER_HOME, ".config", "whisper-tray", "config.json")
HISTORY_FILE = os.path.join(os.path.dirname(CONFIG_FILE), "history.jsonl")
AUTOSTART_FILE = os.path.join(USER_HOME, ".config", "autostart", "whisper-tray.desktop")

LOG_FILE = os.path.join(os.path.dirname(CONFIG_FILE), "whisper-tray.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if os.path.exists("/usr/share/whisper-tray/icons"):
    ICON_DIR = "/usr/share/whisper-tray/icons"
else:
    ICON_DIR = SCRIPT_DIR

# Prefer /usr/share/whisper-tray/sounds/on.mp3 if it exists, else fallback to local
SOUND_ON_PATH = "/usr/share/whisper-tray/sounds/on.mp3"
if not os.path.exists(SOUND_ON_PATH):
    SOUND_ON_PATH = os.path.join(SCRIPT_DIR, "sounds", "on.mp3")

ICONS = {
    "idle": os.path.join(ICON_DIR, "icon-idle.svg"),
    "recording": os.path.join(ICON_DIR, "icon-recording.svg"),
    "processing": os.path.join(ICON_DIR, "icon-processing.svg"),
}

SOUNDS = {
    "on": SOUND_ON_PATH,
}

LANGUAGES = {
    "auto": "auto-detect",
    "en": "english", "zh": "chinese", "de": "german", "es": "spanish",
    "ru": "russian", "ko": "korean", "fr": "french", "ja": "japanese",
    "pt": "portuguese", "tr": "turkish", "pl": "polish", "ca": "catalan",
    "nl": "dutch", "ar": "arabic", "sv": "swedish", "it": "italian",
    "id": "indonesian", "hi": "hindi", "fi": "finnish", "vi": "vietnamese",
    "he": "hebrew", "uk": "ukrainian", "el": "greek", "ms": "malay",
    "cs": "czech", "ro": "romanian", "da": "danish", "hu": "hungarian",
    "ta": "tamil", "no": "norwegian", "th": "thai", "ur": "urdu",
    "hr": "croatian", "bg": "bulgarian", "lt": "lithuanian", "la": "latin",
    "mi": "maori", "ml": "malayalam", "cy": "welsh", "sk": "slovak",
    "te": "telugu", "fa": "persian", "lv": "latvian", "bn": "bengali",
    "sr": "serbian", "az": "azerbaijani", "sl": "slovenian", "kn": "kannada",
    "et": "estonian", "mk": "macedonian", "br": "breton", "eu": "basque",
    "is": "icelandic", "hy": "armenian", "ne": "nepali", "mn": "mongolian",
    "bs": "bosnian", "kk": "kazakh", "sq": "albanian", "sw": "swahili",
    "gl": "galician", "mr": "marathi", "pa": "punjabi", "si": "sinhala",
    "km": "khmer", "sn": "shona", "yo": "yoruba", "so": "somali",
    "af": "afrikaans", "oc": "occitan", "ka": "georgian", "be": "belarusian",
    "tg": "tajik", "sd": "sindhi", "gu": "gujarati", "am": "amharic",
    "yi": "yiddish", "lo": "lao", "uz": "uzbek", "fo": "faroese",
    "ht": "haitian creole", "ps": "pashto", "tk": "turkmen", "nn": "nynorsk",
    "mt": "maltese", "sa": "sanskrit", "lb": "luxembourgish", "my": "myanmar",
    "bo": "tibetan", "tl": "tagalog", "mg": "malagasy", "as": "assamese",
    "tt": "tatar", "haw": "hawaiian", "ln": "lingala", "ha": "hausa",
    "ba": "bashkir", "jw": "javanese", "su": "sundanese",
}

MODELS = {
    "tiny": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin", "disk": "75 MiB", "ram": "~150 MB"},
    "base": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin", "disk": "142 MiB", "ram": "~250 MB"},
    "small": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin", "disk": "466 MiB", "ram": "~600 MB"},
    "medium": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin", "disk": "1.5 GiB", "ram": "~1.8 GB"},
    "large-v1": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v1.bin", "disk": "2.9 GiB", "ram": "~3.2 GB"},
    "large-v2": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/hhmain/ggml-large-v2.bin", "disk": "2.9 GiB", "ram": "~3.2 GB"},
    "large-v3": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin", "disk": "2.9 GiB", "ram": "~3.2 GB"},
    "tiny.en": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin", "disk": "75 MiB", "ram": "~150 MB"},
    "base.en": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin", "disk": "142 MiB", "ram": "~250 MB"},
    "small.en": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin", "disk": "466 MiB", "ram": "~600 MB"},
    "medium.en": {"url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.en.bin", "disk": "1.5 GiB", "ram": "~1.8 GB"},
}

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f: json.dump(config, f, indent=4)

def load_config():
    default_config_dir = os.path.dirname(CONFIG_FILE)
    default_model_dir = os.path.join(USER_HOME, ".local", "share", "whisper_models")
    os.makedirs(default_config_dir, exist_ok=True)
    os.makedirs(default_model_dir, exist_ok=True)
    # Default hotkey is "meta+h" (normalized to "super" for Linux/Windows)
    default_config = {
        "executable": "whisper-tray-cli",
        "model_path": os.path.join(default_model_dir, "ggml-base.en.bin"),
        "model_dir": default_model_dir,
        "hotkey": "ctrl+alt+h",
        "language": "en"
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = default_config.copy()
            try:
                user_config = json.load(f)
                config.update(user_config)
            except json.JSONDecodeError:
                logging.warning(f"Invalid JSON in {CONFIG_FILE}. Using default config and recreating the file.")
                save_config(default_config)
            return config
    else:
        save_config(default_config)
        return default_config

class DownloadModelWindow(gtk.Window):
    def __init__(self, parent):
        if isinstance(parent, SettingsWindow): self.parent_app = parent.parent
        else: self.parent_app = parent
        super().__init__(title="Download Model", modal=True, transient_for=self.parent_app.settings_win)
        self.set_border_width(10); self.set_position(gtk.WindowPosition.CENTER)
        vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=6); self.add(vbox)
        vbox.pack_start(gtk.Label(label="Please select a model to download:"), False, False, 0)
        self.model_combo = gtk.ComboBoxText(); vbox.pack_start(self.model_combo, False, False, 5)
        ram_usage_label = gtk.Label(label="<i><small>RAM is used only during transcription.</small></i>")
        ram_usage_label.set_use_markup(True)
        vbox.pack_start(ram_usage_label, False, False, 0)
        self.progress_bar = gtk.ProgressBar(); vbox.pack_start(self.progress_bar, False, False, 5)
        hbox_buttons = gtk.Box(spacing=6)
        self.download_button = gtk.Button(label="Download"); self.download_button.connect("clicked", self.on_download_clicked)
        self.cancel_button = gtk.Button(label="Cancel"); self.cancel_button.connect("clicked", lambda w: self.destroy())
        hbox_buttons.pack_start(self.download_button, True, True, 0); hbox_buttons.pack_start(self.cancel_button, True, True, 0)
        vbox.pack_start(hbox_buttons, False, False, 0)
        model_dir = self.parent_app.config["model_dir"]
        downloaded_models = [f for f in os.listdir(model_dir) if f.endswith(".bin")] if os.path.exists(model_dir) else []
        available_models = {name: data for name, data in MODELS.items() if f"ggml-{name}.bin" not in downloaded_models}
        if not available_models:
            vbox.pack_start(gtk.Label(label="All models already downloaded!"), False, False, 0); self.download_button.set_sensitive(False)
        else:
            for name, data in available_models.items(): self.model_combo.append_text(f"{name} [Disk: {data['disk']}, RAM: {data['ram']}]")
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

class SettingsWindow(gtk.Window):
    def __init__(self, parent):
        super().__init__(title="Settings")
        self.parent = parent
        self.set_border_width(10); self.set_modal(True); self.set_position(gtk.WindowPosition.CENTER)
        vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10); self.add(vbox)
        # --- Autostart Checkbox ---
        self.autostart_check = gtk.CheckButton(label="Start Whisper Tray at login")
        self.autostart_check.set_active(self._is_autostart_enabled())
        vbox.pack_start(self.autostart_check, False, False, 0)

        # --- Notification Checkbox ---
        self.notifications_check = gtk.CheckButton(label="Enable Notifications")
        self.notifications_check.set_active(self.parent.config.get("enable_notifications", True))
        vbox.pack_start(self.notifications_check, False, False, 0)

        self.exec_entry = gtk.Entry(text=self.parent.config.get("executable", "whisper-tray-cli"))
        vbox.pack_start(self._create_setting_row("Executable Name:", self.exec_entry), False, False, 0)
        self.dir_entry = gtk.Entry(text=self.parent.config.get("model_dir"))
        self.dir_entry.connect("changed", lambda w: self.populate_models())
        vbox.pack_start(self._create_setting_row("Model Directory:", self.dir_entry), False, False, 0)
        self.model_combo = gtk.ComboBoxText(entry_text_column=0)
        download_button = gtk.Button(label="Download..."); download_button.connect("clicked", lambda w: DownloadModelWindow(self).show_all())
        model_box = gtk.Box(spacing=6); model_box.pack_start(self.model_combo, True, True, 0); model_box.pack_start(download_button, False, False, 0)
        vbox.pack_start(self._create_setting_row("Whisper Model:", model_box), False, False, 0)
        self.populate_models()
        if self.parent.config.get("model_path") and os.path.exists(self.parent.config["model_path"]):
            self.model_combo.set_active_id(self.parent.config["model_path"])

        self.lang_combo = gtk.ComboBoxText()
        self.lang_combo.remove_all()
        # Add "auto" at the top
        self.lang_combo.append("auto", "Auto-detect (auto)")
        # Add the rest sorted, skipping "auto"
        for lang_code, lang_name in sorted((k, v) for k, v in LANGUAGES.items() if k != "auto"):
            self.lang_combo.append(lang_code, f"{lang_name.capitalize()} ({lang_code})")
        # Default to "auto" if not set
        self.lang_combo.set_active_id(self.parent.config.get("language", "auto"))
        vbox.pack_start(self._create_setting_row("Language:", self.lang_combo), False, False, 0)

        self.hotkey_entry = gtk.Entry(text=self.parent.config.get("hotkey", "<ctrl>+<alt>+h"))
        self.record_button = gtk.Button(label="Record")
        self.record_button.connect("clicked", self.on_record_hotkey)
        hotkey_box = gtk.Box(spacing=6)
        hotkey_box.pack_start(self.hotkey_entry, True, True, 0)
        hotkey_box.pack_start(self.record_button, False, False, 0)
        vbox.pack_start(self._create_setting_row("Hotkey:", hotkey_box), False, False, 0)

        # --- Output Mode Combo Box ---
        self.output_mode_combo = gtk.ComboBoxText()
        self.output_mode_combo.append("clipboard", "Copy to Clipboard")
        self.output_mode_combo.append("type", "Type Automatically (Ctrl+V)")
        self.output_mode_combo.append("both", "Both (Clipboard & Type)")
        self.output_mode_combo.set_active_id(self.parent.config.get("output_mode", "clipboard"))
        vbox.pack_start(self._create_setting_row("Output Mode:", self.output_mode_combo), False, False, 0)

        save_button = gtk.Button(label="Save and Close"); save_button.connect("clicked", self.on_save_clicked)
        hbox_buttons = gtk.Box(spacing=6, margin_top=10); hbox_buttons.pack_end(save_button, False, False, 0)
        vbox.pack_start(hbox_buttons, False, False, 0)

    def on_record_hotkey(self, widget):
        self.record_button.set_label("Recording...")
        self.record_button.set_sensitive(False)
        self.hotkey_entry.set_text("Press a key combination...")
        self.hotkey_entry.set_sensitive(False)

        self.pressed_keys = set()
        self.listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.listener.start()

    def on_key_press(self, key):
        key_name = self.get_key_name(key)
        if key_name:
            self.pressed_keys.add(key_name)
            self.update_hotkey_entry()

    def on_key_release(self, key):
        self.listener.stop()
        self.record_button.set_label("Record")
        self.record_button.set_sensitive(True)
        self.hotkey_entry.set_sensitive(True)
        # If only modifiers were pressed, clear the entry
        if all(k.startswith('<') and k.endswith('>') for k in self.pressed_keys):
            self.hotkey_entry.set_text(self.parent.config.get("hotkey", "<ctrl>+<alt>+h"))
        return False

    def get_key_name(self, key):
        if isinstance(key, keyboard.Key):
            name = key.name.replace('_r', '').replace('_l', '')
            if name in ['ctrl', 'alt', 'shift', 'super', 'cmd']:
                return f'<{name}>'
            return name
        elif hasattr(key, 'char') and key.char:
            return key.char
        return None

    def update_hotkey_entry(self):
        if not self.pressed_keys:
            return

        modifiers = sorted([k for k in self.pressed_keys if k.startswith('<') and k.endswith('>')])
        regular_keys = sorted([k for k in self.pressed_keys if not (k.startswith('<') and k.endswith('>'))])

        hotkey_str = "+".join(modifiers + regular_keys)
        self.hotkey_entry.set_text(hotkey_str)

    def _create_setting_row(self, label_text, widget):
        box = gtk.Box(spacing=6); label = gtk.Label(label=label_text, xalign=0)
        box.pack_start(label, False, False, 0); box.pack_start(widget, True, True, 0)
        return box

    def populate_models(self):
        self.model_combo.remove_all()
        model_dir = self.dir_entry.get_text()
        if os.path.isdir(model_dir):
            for f in sorted(os.listdir(model_dir)):
                if f.endswith(".bin"):
                    model_path = os.path.join(model_dir, f); self.model_combo.append(model_path, f)

    def _is_autostart_enabled(self):
        return os.path.exists(AUTOSTART_FILE)

    def _set_autostart(self, enable):
        os.makedirs(os.path.dirname(AUTOSTART_FILE), exist_ok=True)
        if enable:
            exec_path = sys.argv[0]
            desktop_entry = f"""[Desktop Entry]
Type=Application
Exec={exec_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Whisper Tray
Comment=Start Whisper Tray at login
"""
            with open(AUTOSTART_FILE, "w") as f:
                f.write(desktop_entry)
        else:
            if os.path.exists(AUTOSTART_FILE):
                os.remove(AUTOSTART_FILE)

    def on_save_clicked(self, widget):
        model_path = self.model_combo.get_active_id()
        language = self.lang_combo.get_active_id()

        if language and language != "en" and model_path and ".en.bin" in model_path:
            dialog = gtk.MessageDialog(
                transient_for=self, flags=0, message_type=gtk.MessageType.ERROR,
                buttons=gtk.ButtonsType.OK, text="Configuration Error"
            )
            lang_name = LANGUAGES.get(language, language).capitalize()
            model_name = os.path.basename(model_path)
            dialog.format_secondary_text(
                f"The selected language '{lang_name}' will not work with the English-only model '{model_name}'.\n\n"
                "Please choose a multilingual model (e.g., 'base', 'small') or set the language to English."
            )
            dialog.run()
            dialog.destroy()
            return

        self.parent.config["executable"] = self.exec_entry.get_text()
        self.parent.config["model_dir"] = self.dir_entry.get_text()
        if model_path: self.parent.config["model_path"] = model_path
        if language: self.parent.config["language"] = language
        hotkey_text = self.hotkey_entry.get_text().lower()
        if any(key in hotkey_text for key in ["meta", "super", "win"]):
            dialog = gtk.MessageDialog(
                transient_for=self, flags=0, message_type=gtk.MessageType.WARNING,
                buttons=gtk.ButtonsType.OK, text="Hotkey Warning"
            )
            dialog.format_secondary_text(
                "Using the 'Meta' (Super/Windows) key is not recommended as it often "
                "conflicts with system shortcuts, especially on KDE Plasma.\n\n"
                "If the hotkey does not work, please try a combination using Ctrl, Alt, and/or Shift."
            )
            dialog.run()
            dialog.destroy()

        replacements = {"control": "ctrl", "super": "super", "meta": "super", "win": "super"}
        for old, new in replacements.items(): hotkey_text = hotkey_text.replace(old, new)
        parts = hotkey_text.split('+')
        for i, part in enumerate(parts):
            p = part.strip()
            if p in ["ctrl", "alt", "shift", "super"] and not (p.startswith('<') and p.endswith('>')):
                parts[i] = f'<{p}>'
        self.parent.config["hotkey"] = '+'.join(parts)
        self.parent.config["enable_notifications"] = self.notifications_check.get_active()
        self.parent.config["output_mode"] = self.output_mode_combo.get_active_id()
        save_config(self.parent.config)
        self.parent._setup_hotkey()
        # Handle autostart
        self._set_autostart(self.autostart_check.get_active())
        self.destroy(); self.parent.settings_win = None

class TrayApp:
    def __init__(self):
        self.config = load_config(); self.audio_frames = []; self.samplerate = 16000
        self.thread = None; self.settings_win = None; self.hotkey_listener = None
        self.keyboard_controller = keyboard.Controller()
        self.indicator = appindicator.Indicator.new("whisper-tray", ICONS["idle"], appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        Notify.init("Whisper Tray")
        self.menu = self._build_menu(); self.indicator.set_menu(self.menu)
        self._setup_hotkey(); self._change_state("idle")

    def _build_menu(self):
        menu = gtk.Menu()
        self.record_item = gtk.MenuItem.new_with_label("Record"); self.record_item.connect("activate", self.toggle_recording); menu.append(self.record_item)
        history_item = gtk.MenuItem.new_with_label("History"); history_item.connect("activate", self.open_history); menu.append(history_item)
        clear_history_item = gtk.MenuItem.new_with_label("Clear History"); clear_history_item.connect("activate", self.clear_history); menu.append(clear_history_item)
        settings_item = gtk.MenuItem.new_with_label("Settings"); settings_item.connect("activate", self.open_settings); menu.append(settings_item)
        quit_item = gtk.MenuItem.new_with_label("Quit"); quit_item.connect("activate", self.quit_app); menu.append(quit_item)
        menu.show_all(); return menu

    def _send_notification(self, title, message, icon_name="whisper-tray"):
        """Helper to send a desktop notification using libnotify."""
        if self.config.get("enable_notifications", True):
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
        icon_path = config["icon"]
        if not os.path.exists(icon_path):
            logging.error(f"Tray icon file not found: {icon_path}")
        try:
            GLib.idle_add(lambda: self.indicator.set_icon_full(icon_path, self.state.capitalize()))
        except Exception as e:
            logging.error(f"Failed to set tray icon: {icon_path} ({e})")
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
        self._send_notification("Recording", "Voice recording started. Speak now!", ICONS["recording"])
        # Play starting sound (MP3 support via ffplay)
        if os.path.exists(SOUNDS["on"]):
            try:
                subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", SOUNDS["on"]],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except FileNotFoundError:
                logging.warning("ffplay not found. Cannot play recording start sound.")
                GLib.idle_add(
                    lambda: self._send_notification(
                        "Sound Playback Unavailable",
                        "Could not play start sound. Please install 'ffmpeg' (ffplay) for MP3 support.",
                        "dialog-warning"
                    )
                )
            except Exception as e:
                logging.error(f"Error playing sound with ffplay: {e}")
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
                executable = self.config.get("executable", "whisper-tray-cli")
                cmd = [executable, "-m", model_path, "-f", self.temp_wav_path, "-nt", "-otxt"]
                language = self.config.get("language")
                if language and language != "auto":
                    cmd.extend(["-l", language])
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
                transcribed_text = result.stdout.strip()

                output_mode = self.config.get("output_mode", "clipboard")

                if output_mode == "type":
                    # First, copy to clipboard, then type
                    subprocess.run(['xclip', '-selection', 'clipboard'], input=transcribed_text, text=True)
                    GLib.idle_add(self._type_text, transcribed_text)
                    # Removed notification for "Text typed automatically."
                elif output_mode == "clipboard":
                    subprocess.run(['xclip', '-selection', 'clipboard'], input=transcribed_text, text=True)
                    self._send_notification("Transcription Complete", "Text copied to clipboard.")
                elif output_mode == "both":
                    subprocess.run(['xclip', '-selection', 'clipboard'], input=transcribed_text, text=True)
                    GLib.idle_add(self._type_text, transcribed_text)
                    self._send_notification("Transcription Complete", "Text copied to clipboard and typed.")
                else: # Default to clipboard if unknown mode
                    subprocess.run(['xclip', '-selection', 'clipboard'], input=transcribed_text, text=True)
                    self._send_notification("Transcription Complete", "Text copied to clipboard.")

                # --- Transcription History ---
                try:
                    import datetime
                    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
                    with open(HISTORY_FILE, "a") as hf:
                        entry = {
                            "timestamp": datetime.datetime.now().isoformat(),
                            "text": transcribed_text,
                            "language": language,
                        }
                        hf.write(json.dumps(entry, ensure_ascii=False) + "\n")
                except Exception as hist_e:
                    logging.error(f"Failed to write transcription history: {hist_e}")
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

    def open_history(self, *args):
        # Simple GTK window to show history
        win = gtk.Window(title="Transcription History")
        win.set_default_size(600, 400)
        vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=6)
        win.add(vbox)
        sw = gtk.ScrolledWindow()
        vbox.pack_start(sw, True, True, 0)
        textview = gtk.TextView()
        textview.set_editable(False)
        sw.add(textview)
        buf = textview.get_buffer()
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r") as hf:
                    lines = hf.readlines()[-100:]  # Show last 100 entries
                entries = [json.loads(line) for line in lines]
                history_text = ""
                for entry in entries:
                    ts = entry.get("timestamp", "")
                    lang = entry.get("language", "")
                    txt = entry.get("text", "")
                    history_text += f"[{ts}] ({lang})\n{txt}\n{'-'*40}\n"
                buf.set_text(history_text)
            else:
                buf.set_text("No transcription history found.")
        except Exception as e:
            buf.set_text(f"Failed to load history: {e}")
        win.show_all()

    def clear_history(self, *args):
        dialog = gtk.MessageDialog(
            transient_for=None,
            flags=gtk.DialogFlags.MODAL | gtk.DialogFlags.DESTROY_WITH_PARENT,
            message_type=gtk.MessageType.QUESTION,
            buttons=gtk.ButtonsType.YES_NO,
            text="Clear Transcription History"
        )
        dialog.format_secondary_text("Are you sure you want to clear all transcription history? This action cannot be undone.")
        response = dialog.run()
        dialog.destroy()

        if response == gtk.ResponseType.YES:
            try:
                if os.path.exists(HISTORY_FILE):
                    os.remove(HISTORY_FILE)
                    self._send_notification("History Cleared", "Transcription history has been cleared.")
                else:
                    self._send_notification("History", "No history file to clear.", "dialog-information")
            except Exception as e:
                self._send_notification("Error", f"Failed to clear history: {e}", "dialog-error")

    def _type_text(self, text):
        # Simulate Ctrl+V to paste the text
        # This requires the text to be in the clipboard first
        # Ensure xclip is used to put text into clipboard before calling this
        self.keyboard_controller.press(keyboard.Key.ctrl_l)
        self.keyboard_controller.press('v')
        self.keyboard_controller.release('v')
        self.keyboard_controller.release(keyboard.Key.ctrl_l)

    def quit_app(self, *args):
        if self.hotkey_listener: self.hotkey_listener.stop()
        Notify.uninit()
        gtk.main_quit()

if __name__ == "__main__":
    logging.info("Application starting up...")
    try:
        app = TrayApp()
        gtk.main()
    except Exception as e:
        logging.error("Critical error during application startup: %s", e, exc_info=True)
        # Fallback to show a GTK error dialog if possible
        try:
            dialog = gtk.MessageDialog(
                transient_for=None,
                flags=0,
                message_type=gtk.MessageType.ERROR,
                buttons=gtk.ButtonsType.OK,
                text="Whisper Tray Startup Error"
            )
            dialog.format_secondary_text(
                f"A critical error occurred. Please see the log file for details:\n{LOG_FILE}"
            )
            dialog.run()
            dialog.destroy()
        except Exception as dialog_e:
            logging.error("Failed to show GTK error dialog: %s", dialog_e, exc_info=True)
        sys.exit(1)
