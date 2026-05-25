import json
import os
import base64

# === ПРОСТОЕ ШИФРОВАНИЕ БЕЗ ВНЕШНИХ БИБЛИОТЕК ===
# Используем XOR с ключом, который хранится в том же файле.
# Никакой cryptography, только встроенный base64.

def simple_encrypt(data: str, password: str = "windusik_default_key_2025") -> str:
    """Шифрование строки с помощью XOR и base64. Без сторонних библиотек."""
    key_bytes = password.encode('utf-8')
    data_bytes = data.encode('utf-8')
    encrypted_bytes = bytearray()
    
    for i, byte in enumerate(data_bytes):
        key_byte = key_bytes[i % len(key_bytes)]
        encrypted_bytes.append(byte ^ key_byte)
    
    # Кодируем в base64 для безопасного хранения
    return base64.b64encode(encrypted_bytes).decode('utf-8')

def simple_decrypt(encrypted_data: str, password: str = "windusik_default_key_2025") -> str:
    """Расшифровка строки. Пароль должен совпадать с тем, что использовался при шифровании."""
    try:
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        key_bytes = password.encode('utf-8')
        decrypted_bytes = bytearray()
        
        for i, byte in enumerate(encrypted_bytes):
            key_byte = key_bytes[i % len(key_bytes)]
            decrypted_bytes.append(byte ^ key_byte)
        
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"Decryption error: {e}")
        return ""

class I18n:
    def __init__(self):
        self.translations = {}
        self.current_lang = "en"
    
    def load_language(self, lang_code: str):
        """Загружает язык из .lang (JSON) или .langcryp (зашифрованный JSON)."""
        self.current_lang = lang_code
        lang_file = f"i18n/{lang_code}.lang"
        cryp_file = f"i18n/{lang_code}.langcryp"
        
        # Пробуем загрузить зашифрованный файл
        if os.path.exists(cryp_file):
            try:
                with open(cryp_file, 'r', encoding='utf-8') as f:
                    encrypted_content = f.read()
                decrypted_content = simple_decrypt(encrypted_content)
                self.translations = json.loads(decrypted_content)
                return
            except Exception as e:
                print(f"Failed to load encrypted language file: {e}")
        
        # Если зашифрованного нет, пробуем обычный .lang
        if os.path.exists(lang_file):
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        else:
            self.translations = {}
    
    def tr(self, key: str) -> str:
        """Возвращает перевод ключа или сам ключ, если перевода нет."""
        return self.translations.get(key, key)
    
    def encrypt_lang(self, lang_code: str):
        """Шифрует .lang в .langcryp. Запускается отдельно при необходимости."""
        lang_file = f"i18n/{lang_code}.lang"
        cryp_file = f"i18n/{lang_code}.langcryp"
        
        if not os.path.exists(lang_file):
            print(f"Source file {lang_file} not found.")
            return
        
        with open(lang_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        encrypted_content = simple_encrypt(content)
        
        with open(cryp_file, 'w', encoding='utf-8') as f:
            f.write(encrypted_content)
        
        print(f"Encrypted language file created: {cryp_file}")

# Пример использования (для ручного шифрования)
if __name__ == "__main__":
    # Если запустить этот файл напрямую, он зашифрует en.lang в en.langcryp
    i18n = I18n()
    i18n.encrypt_lang("en")
    i18n.encrypt_lang("ru")