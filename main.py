import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import threading
import time
import json
import os
import sys
import webbrowser

from pynput.keyboard import Key, Controller as KeyboardController, Listener
from i18n_utils import I18n  # Исправленный импорт
from macros import MacroManager

# --- Конфиг ---
APP_NAME = "KeyPresser"
VERSION = "1.1"
REPO_OWNER = "windusik"
REPO_NAME = "key-presser"
GITHUB_RELEASES_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

keyboard_ctrl = KeyboardController()
running = False
press_thread = None
current_hotkey = []
settings_file = "settings.json"

MODE_HOLD = "hold"
MODE_INTERVAL = "interval"
MODE_SPAM = "spam"

current_mode = MODE_HOLD
target_key = "a"
interval_ms = 1000

class KeyPresserApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("650x500")
        self.root.resizable(False, False)

        # --- Инициализация локализации ---
        self.i18n = I18n()
        self.current_lang = "en"

        # --- Инициализация менеджера макросов ---
        self.macro_manager = MacroManager(self.i18n)

        # --- Меню ---
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=self.i18n.tr("GitHub"), command=self.open_github)
        file_menu.add_command(label=self.i18n.tr("Check for Updates"), command=self.check_update)
        file_menu.add_separator()
        file_menu.add_command(label=self.i18n.tr("Exit"), command=self.on_closing)
        menubar.add_cascade(label=self.i18n.tr("Menu"), menu=file_menu)

        lang_menu = tk.Menu(menubar, tearoff=0)
        lang_menu.add_command(label="English", command=lambda: self.set_language("en"))
        lang_menu.add_command(label="Русский", command=lambda: self.set_language("ru"))
        menubar.add_cascade(label=self.i18n.tr("Language"), menu=lang_menu)

        self.root.config(menu=menubar)

        # --- Тема по умолчанию (тёмная) ---
        self.dark_mode = True
        self.style = ttk.Style()
        self.custom_bg = "#2b2b2b"
        self.custom_fg = "white"
        self.set_theme()

        # --- Создание вкладок ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.modes_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.modes_tab, text=self.i18n.tr("Modes"))

        self.macros_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.macros_tab, text=self.i18n.tr("Macros"))

        self.bindings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.bindings_tab, text=self.i18n.tr("Bindings"))

        self.themes_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.themes_tab, text=self.i18n.tr("Theme"))

        # --- Заполнение вкладок ---
        self.setup_modes_tab()
        self.setup_macros_tab()
        self.setup_bindings_tab()
        self.setup_themes_tab()

        # --- Загрузка настроек и прослушивание ---
        self.load_settings()
        self.listener = Listener(on_press=self.on_hotkey_press)
        self.listener.start()

    # --- Методы локализации ---
    def set_language(self, lang_code):
        self.current_lang = lang_code
        self.i18n.load_language(lang_code)
        self.refresh_ui_texts()

    def refresh_ui_texts(self):
        self.notebook.tab(0, text=self.i18n.tr("Modes"))
        self.notebook.tab(1, text=self.i18n.tr("Macros"))
        self.notebook.tab(2, text=self.i18n.tr("Bindings"))
        self.notebook.tab(3, text=self.i18n.tr("Theme"))

    # --- Методы темы ---
    def set_theme(self):
        if self.dark_mode:
            bg = self.custom_bg
            fg = self.custom_fg
        else:
            bg = self.custom_bg if self.custom_bg else "#f0f0f0"
            fg = self.custom_fg if self.custom_fg else "black"
        self.root.configure(bg=bg)
        self.style.theme_use('clam')
        self.style.configure('TLabel', background=bg, foreground=fg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('TButton', background=bg)
        self.style.configure('TRadiobutton', background=bg, foreground=fg)
        self.style.configure('TNotebook', background=bg)
        self.style.configure('TNotebook.Tab', background=bg, foreground=fg)

    def set_dark_theme(self):
        self.dark_mode = True
        self.set_theme()

    def set_light_theme(self):
        self.dark_mode = False
        self.set_theme()

    # --- Методы режимов ---
    def setup_modes_tab(self):
        frame = self.modes_tab
        tk.Label(frame, text=self.i18n.tr("Target Key:")).pack(pady=(10, 0))
        self.key_entry = tk.Entry(frame, width=10)
        self.key_entry.insert(0, target_key)
        self.key_entry.pack(pady=(0, 10))
        self.key_entry.bind("<KeyRelease>", self.on_key_entry_change)

        tk.Label(frame, text=self.i18n.tr("Mode:")).pack()
        self.mode_var = tk.StringVar(value=MODE_HOLD)
        mode_frame = tk.Frame(frame)
        mode_frame.pack(pady=(0, 10))
        tk.Radiobutton(mode_frame, text=self.i18n.tr("Hold"), variable=self.mode_var, value=MODE_HOLD, command=self.on_mode_change).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text=self.i18n.tr("Interval (ms)"), variable=self.mode_var, value=MODE_INTERVAL, command=self.on_mode_change).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text=self.i18n.tr("Spam"), variable=self.mode_var, value=MODE_SPAM, command=self.on_mode_change).pack(side=tk.LEFT, padx=5)

        self.interval_frame = tk.Frame(frame)
        self.interval_frame.pack(pady=(0, 10))
        tk.Label(self.interval_frame, text=self.i18n.tr("Interval (ms):")).pack(side=tk.LEFT)
        self.interval_entry = tk.Entry(self.interval_frame, width=10)
        self.interval_entry.insert(0, str(interval_ms))
        self.interval_entry.pack(side=tk.LEFT, padx=(5, 0))

        self.start_stop_btn = tk.Button(frame, text=self.i18n.tr("START"), command=self.toggle_action, bg="green", fg="white", font=("Arial", 12, "bold"))
        self.start_stop_btn.pack(pady=20)

    def on_key_entry_change(self, event):
        global target_key
        val = self.key_entry.get().strip().lower()
        if val:
            target_key = val

    def on_mode_change(self):
        global current_mode
        current_mode = self.mode_var.get()
        if current_mode == MODE_INTERVAL:
            self.interval_frame.pack(pady=(0, 10))
        else:
            self.interval_frame.pack_forget()

    # --- Методы макросов ---
    def setup_macros_tab(self):
        frame = self.macros_tab
        tk.Label(frame, text=self.i18n.tr("KPMS Macro Editor")).pack(pady=5)
        self.macro_editor = tk.Text(frame, height=5, width=50)
        self.macro_editor.pack(pady=5, padx=10)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text=self.i18n.tr("Run Macro"), command=self.run_macro).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text=self.i18n.tr("Open Macro File"), command=self.open_macro_file).pack(side=tk.LEFT, padx=5)

        tk.Label(frame, text=self.i18n.tr("System Macros")).pack(pady=5)
        self.system_macros_listbox = tk.Listbox(frame, height=4)
        self.system_macros_listbox.pack(pady=5, padx=10, fill='x')
        for macro_name in self.macro_manager.get_system_macros():
            self.system_macros_listbox.insert('end', macro_name)

        tk.Button(frame, text=self.i18n.tr("Run System Macro"), command=self.run_system_macro).pack(pady=5)

        tk.Label(frame, text=self.i18n.tr("Learn more about macros")).pack(pady=5)
        tk.Button(frame, text="Wiki", command=self.open_macro_wiki).pack(pady=5)

    def run_macro(self):
        macro_code = self.macro_editor.get("1.0", 'end-1c')
        self.macro_manager.run_kpms_macro(macro_code)

    def open_macro_file(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(filetypes=[("Macro files", "*.txt")])
        if filepath:
            with open(filepath, 'r') as f:
                macro_code = f.read()
            self.macro_editor.delete("1.0", 'end')
            self.macro_editor.insert("1.0", macro_code)

    def run_system_macro(self):
        selection = self.system_macros_listbox.curselection()
        if selection:
            macro_name = self.system_macros_listbox.get(selection[0])
            self.macro_manager.run_system_macro(macro_name)

    def open_macro_wiki(self):
        webbrowser.open("https://github.com/windusik/key-presser/wiki/Macroses")

    # --- Методы биндов ---
    def setup_bindings_tab(self):
        frame = self.bindings_tab
        tk.Label(frame, text=self.i18n.tr("Start/Stop Hotkey (click to set):")).pack(pady=(10, 0))
        self.hotkey_btn = tk.Button(frame, text=self.i18n.tr("Not set"), command=self.set_hotkey)
        self.hotkey_btn.pack(pady=(0, 10))
        self.waiting_for_hotkey = False

    def set_hotkey(self):
        self.hotkey_btn.config(text=self.i18n.tr("Press a key..."))
        self.waiting_for_hotkey = True

    # --- Методы темы (цвета) ---
    def setup_themes_tab(self):
        frame = self.themes_tab
        tk.Label(frame, text=self.i18n.tr("Preset Themes")).pack(pady=10)
        tk.Button(frame, text=self.i18n.tr("Dark Theme"), command=self.set_dark_theme).pack(pady=5)
        tk.Button(frame, text=self.i18n.tr("Light Theme"), command=self.set_light_theme).pack(pady=5)

        tk.Label(frame, text=self.i18n.tr("Custom Colors")).pack(pady=10)
        tk.Button(frame, text=self.i18n.tr("Background Color"), command=self.choose_bg_color).pack(pady=5)
        tk.Button(frame, text=self.i18n.tr("Text Color"), command=self.choose_fg_color).pack(pady=5)

    def choose_bg_color(self):
        color_code = colorchooser.askcolor(title=self.i18n.tr("Choose background color"))[1]
        if color_code:
            self.custom_bg = color_code
            self.set_theme()

    def choose_fg_color(self):
        color_code = colorchooser.askcolor(title=self.i18n.tr("Choose text color"))[1]
        if color_code:
            self.custom_fg = color_code
            self.set_theme()

    # --- Методы горячих клавиш и действий ---
    def on_hotkey_press(self, key):
        if self.waiting_for_hotkey:
            try:
                if hasattr(key, 'char') and key.char:
                    hotkey_str = key.char
                elif hasattr(key, 'name'):
                    hotkey_str = key.name
                else:
                    hotkey_str = str(key)
                global current_hotkey
                current_hotkey = [hotkey_str]
                self.hotkey_btn.config(text=f"Hotkey: {hotkey_str}")
                self.waiting_for_hotkey = False
                self.save_settings()
            except Exception as e:
                print(f"Hotkey error: {e}")
                self.waiting_for_hotkey = False
            return True

        if current_hotkey:
            try:
                pressed = False
                if hasattr(key, 'char') and key.char and key.char == current_hotkey[0]:
                    pressed = True
                elif hasattr(key, 'name') and key.name == current_hotkey[0]:
                    pressed = True
                if pressed:
                    self.root.after(0, self.toggle_action)
            except:
                pass
        return True

    def press_action(self):
        global running
        while running:
            if current_mode == MODE_HOLD:
                keyboard_ctrl.press(target_key)
                time.sleep(0.05)
            elif current_mode == MODE_INTERVAL:
                interval = self.get_interval()
                keyboard_ctrl.press(target_key)
                keyboard_ctrl.release(target_key)
                time.sleep(interval / 1000.0)
            elif current_mode == MODE_SPAM:
                keyboard_ctrl.press(target_key)
                keyboard_ctrl.release(target_key)
        if current_mode == MODE_HOLD:
            keyboard_ctrl.release(target_key)

    def get_interval(self):
        try:
            return max(1, int(self.interval_entry.get()))
        except:
            return 1000

    def toggle_action(self):
        global running, press_thread
        if not running:
            global current_mode, target_key
            current_mode = self.mode_var.get()
            target_key = self.key_entry.get().strip().lower()
            if not target_key:
                messagebox.showerror(self.i18n.tr("Error"), self.i18n.tr("Target key is empty!"))
                return
            running = True
            self.start_stop_btn.config(text=self.i18n.tr("STOP"), bg="red")
            press_thread = threading.Thread(target=self.press_action, daemon=True)
            press_thread.start()
        else:
            running = False
            if press_thread and press_thread.is_alive():
                press_thread.join(timeout=0.5)
            self.start_stop_btn.config(text=self.i18n.tr("START"), bg="green")

    def save_settings(self):
        settings = {
            "target_key": target_key,
            "mode": current_mode,
            "interval_ms": self.get_interval() if current_mode == MODE_INTERVAL else 1000,
            "hotkey": current_hotkey,
            "dark_mode": self.dark_mode,
            "custom_bg": self.custom_bg,
            "custom_fg": self.custom_fg,
            "language": self.current_lang
        }
        try:
            with open(settings_file, "w") as f:
                json.dump(settings, f, indent=4)
        except:
            pass

    def load_settings(self):
        global target_key, current_mode, interval_ms, current_hotkey
        try:
            if os.path.exists(settings_file):
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                target_key = settings.get("target_key", "a")
                current_mode = settings.get("mode", MODE_HOLD)
                interval_ms = settings.get("interval_ms", 1000)
                current_hotkey = settings.get("hotkey", [])
                self.dark_mode = settings.get("dark_mode", True)
                self.custom_bg = settings.get("custom_bg", "#2b2b2b")
                self.custom_fg = settings.get("custom_fg", "white")
                self.current_lang = settings.get("language", "en")
                self.key_entry.delete(0, tk.END)
                self.key_entry.insert(0, target_key)
                self.mode_var.set(current_mode)
                self.interval_entry.delete(0, tk.END)
                self.interval_entry.insert(0, str(interval_ms))
                if current_hotkey:
                    self.hotkey_btn.config(text=f"Hotkey: {current_hotkey[0]}")
                self.i18n.load_language(self.current_lang)
                self.set_theme()
                self.on_mode_change()
                self.refresh_ui_texts()
        except:
            pass

    def check_update(self):
        try:
            import requests
            response = requests.get(GITHUB_RELEASES_URL)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("tag_name", "").lstrip("v")
                if latest_version > VERSION:
                    if messagebox.askyesno(self.i18n.tr("Update Available"), self.i18n.tr(f"New version {latest_version} is available. Open GitHub releases page?")):
                        webbrowser.open(f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/latest")
                else:
                    messagebox.showinfo(self.i18n.tr("No Updates"), self.i18n.tr("You are using the latest version."))
            else:
                messagebox.showerror(self.i18n.tr("Error"), self.i18n.tr("Failed to check for updates."))
        except Exception as e:
            messagebox.showerror(self.i18n.tr("Error"), self.i18n.tr(f"Update check failed: {e}"))

    def open_github(self):
        webbrowser.open(f"https://github.com/{REPO_OWNER}/{REPO_NAME}")

    def on_closing(self):
        global running
        running = False
        if press_thread and press_thread.is_alive():
            press_thread.join(timeout=0.5)
        self.save_settings()
        self.root.destroy()
        if hasattr(self, 'listener') and self.listener:
            self.listener.stop()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = KeyPresserApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()