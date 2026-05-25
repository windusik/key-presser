import base64
import os

# === ПРОСТОЕ ШИФРОВАНИЕ С ПОМОЩЬЮ XOR (БЕЗ СТОРОННИХ БИБЛИОТЕК) ===

def simple_encrypt(data: str, password: str = "windusik_secret_key") -> str:
    """Шифрование строки с помощью XOR."""
    key_bytes = password.encode('utf-8')
    data_bytes = data.encode('utf-8')
    result = bytearray()
    
    for i, byte in enumerate(data_bytes):
        result.append(byte ^ key_bytes[i % len(key_bytes)])
    
    return base64.b64encode(result).decode('utf-8')

def simple_decrypt(encrypted_data: str, password: str = "windusik_secret_key") -> str:
    """Расшифровка строки."""
    try:
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        key_bytes = password.encode('utf-8')
        result = bytearray()
        
        for i, byte in enumerate(encrypted_bytes):
            result.append(byte ^ key_bytes[i % len(key_bytes)])
        
        return result.decode('utf-8')
    except Exception as e:
        print(f"Decryption failed: {e}")
        return ""

def encrypt_file(content: str, output_file: str, password: str = "windusik_secret_key"):
    """Шифрует содержимое и сохраняет в файл."""
    encrypted = simple_encrypt(content, password)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(encrypted)

def decrypt_file(encrypted_file: str, password: str = "windusik_secret_key") -> str:
    """Расшифровывает файл и возвращает содержимое."""
    with open(encrypted_file, 'r', encoding='utf-8') as f:
        encrypted_content = f.read()
    return simple_decrypt(encrypted_content, password)