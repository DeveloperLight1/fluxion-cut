import subprocess
import time
import os
import re

# Функция для запуска команды
def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout
    except:
        return ""

# Проверка прав
if os.geteuid() != 0:
    print("Запусти с sudo: sudo python3 scan.py")
    exit()

# 1. Включаем режим мониторинга
print("Включаю режим мониторинга...")
print(run_cmd("sudo airmon-ng start wlan0"))
time.sleep(2)

# 2. Сканируем и сохраняем во временный файл
print("Сканирую WiFi (7 сек)...")
run_cmd("timeout 7 sudo airodump-ng wlan0mon --output-format csv -w temp_scan 2>/dev/null")
time.sleep(1)

# 3. Читаем CSV файл
wifi_dict = {}  # Используем словарь для устранения дубликатов по BSSID

# Ищем созданный файл
csv_file = None
for file in os.listdir('.'):
    if file.startswith('temp_scan-') and file.endswith('.csv'):
        csv_file = file
        break

if csv_file:
    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Разделяем на строки и парсим
            lines = content.strip().split('\n')
            
            for line in lines:
                # Ищем строки с сетями (не клиентами)
                if line and not line.startswith('Station MAC'):
                    parts = line.split(',')
                    
                    # Проверяем, что это строка с сетью (должна содержать BSSID и канал)
                    if len(parts) > 13 and ':' in parts[0] and parts[0] not in wifi_dict:
                        bssid = parts[0].strip()
                        channel = parts[3].strip() if parts[3] else "0"
                        
                        # SSID может быть в разных позициях
                        ssid = ""
                        for i in range(13, len(parts)):
                            if parts[i] and not parts[i].isdigit():
                                ssid = parts[i].strip()
                                break
                        
                        if not ssid or ssid == " ":
                            ssid = "<скрытый>"
                        
                        # Чистим SSID от непечатаемых символов
                        ssid = ''.join(c for c in ssid if c.isprintable() and ord(c) < 128)
                        
                        if bssid and channel:
                            wifi_dict[bssid] = {
                                'BSSID': bssid,
                                'SSID': ssid[:32],  # Ограничиваем длину SSID
                                'CHANNEL': channel
                            }
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
    
    # Удаляем временный файл
    os.remove(csv_file)

# 4. Сохраняем в файл
wifi_list = list(wifi_dict.values())

with open('wifi_scan.txt', 'w', encoding='utf-8') as f:
    f.write("№ | SSID | BSSID | CHANNEL\n")
    f.write("="*50 + "\n")
    
    for i, wifi in enumerate(wifi_list, 1):
        f.write(f"{i} | {wifi['SSID']} | {wifi['BSSID']} | {wifi['CHANNEL']}\n")

# 5. Показываем результат
print(f"\nНайдено {len(wifi_list)} WiFi сетей:")
print("="*60)
for i, wifi in enumerate(wifi_list, 1):
    ssid_display = wifi['SSID'] if len(wifi['SSID']) <= 20 else wifi['SSID'][:17] + "..."
    print(f"{i:3}. {ssid_display:20} | {wifi['BSSID']:17} | CH{wifi['CHANNEL']:>3}")

print(f"\nРезультат сохранен в wifi_scan.txt")

# 6. Выключаем режим мониторинга
print("\nВыключаю режим мониторинга...")
print(run_cmd("sudo airmon-ng stop wlan0mon"))