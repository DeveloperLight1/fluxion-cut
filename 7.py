import subprocess
import time
import os

def run_command(command, description):
    """Выполняет команду и возвращает её вывод"""
    print(f"Выполняю: {description}")
    print(f"Команда: {command}")
    
    try:
        # Выполняем команду
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"Ошибка: {result.stderr}")
            return None
        
        print("Успешно выполнено!")
        return result.stdout
        
    except subprocess.TimeoutExpired:
        print("Таймаут выполнения команды")
        return None
    except Exception as e:
        print(f"Исключение: {e}")
        return None

def main():
    # Проверяем права sudo
    if os.geteuid() != 0:
        print("Для работы скрипта требуются права администратора!")
        print("Запустите скрипт с sudo:")
        print("sudo python3 wifi_scanner.py")
        exit(1)
    
    # Запрашиваем имя файла для сохранения
    filename = input("Введите имя файла для сохранения результатов (по умолчанию: scan_results.txt): ")
    if not filename:
        filename = "scan_results.txt"
    
    print("=" * 50)
    
    # 1. Запускаем airmon-ng для перевода интерфейса в режим мониторинга
    output1 = run_command(
        "sudo airmon-ng start wlan0", 
        "Перевод wlan0 в режим мониторинга"
    )
    
    if output1 is None:
        print("Не удалось выполнить первую команду. Завершаю работу.")
        return
    
    # Ждем немного, чтобы интерфейс поднялся
    print("Ожидание 5 секунд...")
    time.sleep(5)
    
    print("=" * 50)
    
    # 2. Запускаем airodump-ng для сканирования сетей
    # Запускаем на 30 секунд, чтобы собрать данные
    print("Начинаю сканирование WiFi сетей...")
    print("Сканирование займет 30 секунд. Пожалуйста, подождите...")
    
    try:
        # Запускаем airodump-ng с таймаутом
        with open(filename, 'w') as f:
            # Записываем результат первой команды
            f.write("=" * 50 + "\n")
            f.write("Результат airmon-ng start wlan0:\n")
            f.write("=" * 50 + "\n")
            f.write(output1 + "\n")
            
            # Записываем разделитель
            f.write("\n" + "=" * 50 + "\n")
            f.write("Результат airodump-ng wlan0mon (30 секунд):\n")
            f.write("=" * 50 + "\n")
            f.flush()  # Сбрасываем буфер
            
            # Запускаем вторую команду и записываем вывод в файл
            process = subprocess.Popen(
                "timeout 30 sudo airodump-ng wlan0mon",
                shell=True,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Ждем завершения процесса
            process.wait()
        
        print(f"\nСканирование завершено! Результаты сохранены в файл: {filename}")
        
        # Показываем первую часть результатов из файла
        print(f"\nПервые 20 строк результатов из файла {filename}:")
        print("=" * 50)
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                # Пропускаем первые записи airmon-ng и показываем airodump-ng
                for i, line in enumerate(lines):
                    if "Результат airodump-ng" in line:
                        # Показываем следующие 20 строк
                        start = i + 1
                        end = min(start + 20, len(lines))
                        for j in range(start, end):
                            print(lines[j], end='')
                        break
        except Exception as e:
            print(f"Не удалось прочитать файл: {e}")
            
    except KeyboardInterrupt:
        print("\nСканирование прервано пользователем")
    except Exception as e:
        print(f"Ошибка при выполнении airodump-ng: {e}")

if __name__ == "__main__":
    main()
