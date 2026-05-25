import time
import subprocess
import sys
from pynput.keyboard import Controller, Key

keyboard = Controller()

class MacroManager:
    def __init__(self, i18n):
        self.i18n = i18n
        self.system_macros = {
            "hello_world": "text Hello, World!",
            "open_notepad": "shell notepad",
            "open_calculator": "shell calc"
        }

    def run_kpms_macro(self, macro_code):
        lines = macro_code.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
            parts = line.split(maxsplit=1)
            if not parts:
                continue
            command = parts[0].lower()
            argument = parts[1] if len(parts) > 1 else ""

            if command == "text":
                keyboard.type(argument)
            elif command == "key":
                self._press_key(argument)
            elif command == "wait":
                try:
                    time.sleep(float(argument))
                except ValueError:
                    pass
            elif command == "shell":
                subprocess.Popen(argument, shell=True)

    def _press_key(self, key_name):
        try:
            key = getattr(Key, key_name.lower())
            keyboard.press(key)
            keyboard.release(key)
        except AttributeError:
            keyboard.press(key_name)
            keyboard.release(key_name)

    def get_system_macros(self):
        return list(self.system_macros.keys())

    def run_system_macro(self, macro_name):
        macro_code = self.system_macros.get(macro_name, "")
        if macro_code:
            self.run_kpms_macro(macro_code)