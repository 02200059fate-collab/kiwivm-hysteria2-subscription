#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG_DIR="/etc/kiwivm-subscription"
PURGE_HYSTERIA=0

if [[ "${1-}" == "--purge-hysteria" ]]; then
  PURGE_HYSTERIA=1
elif (($#)); then
  printf 'Usage: sudo ./uninstall.sh [--purge-hysteria]\n' >&2
  exit 2
fi

[[ "${EUID}" -eq 0 ]] || { echo "Run as root." >&2; exit 1; }

systemctl disable --now kiwivm-subscription.service 2>/dev/null || true
rm -f /etc/systemd/system/kiwivm-subscription.service
rm -rf /usr/local/lib/kiwivm-subscription /var/lib/kiwivm-subscription

if [[ -r "$CONFIG_DIR/caddy_backup_path" ]]; then
  CADDY_BACKUP="$(cat "$CONFIG_DIR/caddy_backup_path")"
  if [[ -f "$CADDY_BACKUP" ]]; then
    cp -a "$CADDY_BACKUP" /etc/caddy/Caddyfile
    systemctl restart caddy || true
  fi
fi

rm -rf "$CONFIG_DIR"
userdel kiwisub 2>/dev/null || true
groupdel kiwisub 2>/dev/null || true
systemctl daemon-reload

if [[ "$PURGE_HYSTERIA" -eq 1 ]]; then
  bash <(curl -fsSL https://get.hy2.sh/) --remove
  rm -rf /etc/hysteria /root/kiwivm-hysteria2-client
fi

echo "KiwiVM subscription service removed."
if [[ "$PURGE_HYSTERIA" -eq 0 ]]; then
  echo "Hysteria and the private client credential file were kept."
fi
