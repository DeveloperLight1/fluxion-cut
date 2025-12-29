import subprocess
import time
import os
import csv

# Проверка прав
if os.geteuid() != 0:
    exit("Запусти с sudo!")

# 1. Включаем мониторинг
subprocess.run("sudo airmon-ng start wlan0", shell=True)
time.sleep(2)

# 2. Сканируем 7 секунд
print("Сканирование...")
output = subprocess.run(
    "timeout 7 sudo airodump-ng wlan0mon",
    shell=True, capture_output=True, text=True
).stdout

# 3. Извлекаем данные
networks = []
lines = output.split('\n')

for line in lines:
    # Ищем строки с сетями (содержат MAC и канал)
    if len(line) > 50 and ':' in line[:17]:
        parts = line.split()
        
        if len(parts) > 6:
            # Проверяем что 6-й элемент - канал (число)
            if parts[5].isdigit():
                bssid = parts[0]           # MAC адрес
                channel = parts[5]         # Канал
                # SSID - все что после 13-го элемента
                ssid = ' '.join(parts[13:]) if len(parts) > 13 else "HIDDEN"
                
                # Очищаем SSID
                ssid = ''.join(c for c in ssid if 32 <= ord(c) < 127)
                
                if ssid and bssid and channel:
                    networks.append([bssid, ssid, channel])

# 4. Сохраняем в CSV
with open('wifi_networks.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['№', 'BSSID', 'SSID', 'CHANNEL'])  # Заголовки
    
    for i, net in enumerate(networks, 1):
        writer.writerow([i, net[0], net[1], net[2]])

print(f"Найдено {len(networks)} сетей")
print("Данные в wifi_networks.csv")
print("\nФормат файла:")
print("№,BSSID,SSID,CHANNEL")
print("1,AA:BB:CC:DD:EE:FF,MyWiFi,6")
print("2,11:22:33:44:55:66,HomeNet,11")