#!/bin/bash
# Скрипт для быстрой установки зависимостей на Raspberry Pi

echo "=========================================="
echo "  Установка зависимостей Fluxion"
echo "  для Raspberry Pi"
echo "=========================================="
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Ошибка: Запустите скрипт с sudo!"
    echo "   Использование: sudo ./install_on_pi.sh"
    exit 1
fi

# Определение дистрибутива
if [ -f /etc/debian_version ]; then
    DISTRO="debian"
    echo "✅ Обнаружен Debian-based дистрибутив"
elif [ -f /etc/arch-release ]; then
    DISTRO="arch"
    echo "✅ Обнаружен Arch-based дистрибутив"
else
    DISTRO="unknown"
    echo "⚠️  Неизвестный дистрибутив, попытка установки для Debian"
fi

echo ""
echo "📦 Обновление списка пакетов..."
apt update

echo ""
echo "📦 Установка основных зависимостей..."

# Основные зависимости
apt install -y \
    aircrack-ng \
    bc \
    awk \
    curl \
    cowpatty \
    isc-dhcp-server \
    p7zip \
    hostapd \
    lighttpd \
    iw \
    macchanger \
    mdk4 \
    dsniff \
    nmap \
    openssl \
    php-cgi \
    xterm \
    rfkill \
    unzip \
    net-tools \
    psmisc \
    python3 \
    python3-pip

echo ""
echo "📦 Установка Python зависимостей..."
pip3 install pyric

echo ""
echo "📦 Установка словарей (wordlists)..."
apt install -y wordlists || echo "⚠️  wordlists не найден в репозиториях"

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Проверка установленных пакетов..."
echo ""

# Проверка критических пакетов
CRITICAL_PACKAGES=("aircrack-ng" "hostapd" "lighttpd" "iw" "mdk4")

for pkg in "${CRITICAL_PACKAGES[@]}"; do
    if command -v $pkg &> /dev/null; then
        echo "  ✅ $pkg - установлен"
    else
        echo "  ❌ $pkg - НЕ установлен!"
    fi
done

echo ""
echo "=========================================="
echo "  Следующие шаги:"
echo "  1. Подключите USB Wi-Fi адаптер"
echo "  2. Проверьте интерфейс: iwconfig"
echo "  3. Запустите: sudo ./fluxion.sh"
echo "=========================================="

