import subprocess
import time
import os

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

# 2. Сканируем 7 секунд
print("Сканирую WiFi (7 сек)...")
result = run_cmd("timeout 7 sudo airodump-ng wlan0mon")

# 3. Парсим результат
wifi_list = []
lines = result.strip().split('\n')

for line in lines:
    # Ищем строки с MAC-адресом (BSSID)
    if len(line) > 50 and ':' in line[:17]:
        parts = line.split()
        
        # Проверяем что это строка с сетью (есть CH)
        if len(parts) > 6 and parts[5].isdigit():
            bssid = parts[0]
            channel = parts[5]
            
            # SSID находится в конце строки после технических полей
            # Примерное количество полей до SSID: около 13
            if len(parts) > 13:
                ssid = ' '.join(parts[13:])
            else:
                ssid = "<скрытый>"
            
            # Чистим SSID от мусора
            ssid = ''.join(c for c in ssid if c.isprintable())
            
            if ssid and bssid and channel:
                wifi_list.append({
                    'BSSID': bssid,
                    'SSID': ssid,
                    'CHANNEL': channel
                })

# 4. Сохраняем в файл
with open('wifi_scan.txt', 'w') as f:
    f.write("№ | SSID | BSSID | CHANNEL\n")
    f.write("="*50 + "\n")
    
    for i, wifi in enumerate(wifi_list, 1):
        f.write(f"{i} | {wifi['SSID']} | {wifi['BSSID']} | {wifi['CHANNEL']}\n")

# 5. Показываем результат
print(f"\nНайдено {len(wifi_list)} WiFi сетей:")
print("="*50)
for i, wifi in enumerate(wifi_list, 1):
    print(f"{i}. {wifi['SSID']} | {wifi['BSSID']} | CH{wifi['CHANNEL']}")

print(f"\nРезультат сохранен в wifi_scan.txt")