#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_NAME="kiwivm-hysteria2-subscription"
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="/etc/kiwivm-subscription"
APP_DIR="/usr/local/lib/kiwivm-subscription"
CLIENT_DIR="/root/kiwivm-hysteria2-client"
SERVICE_NAME="kiwivm-subscription.service"

VEID="${KIWIVM_VEID:-}"
API_KEY_FILE=""
SERVER_IP=""
DOMAIN=""
NODE_NAME="Bandwagon"
COUNTRY_EMOJI="🇺🇸"
FORCE_CADDY=0

usage() {
  cat <<'EOF'
Usage: sudo ./install.sh [options]

Options:
  --veid VALUE          KiwiVM VEID. Prompted when omitted.
  --api-key-file PATH   File containing the KiwiVM API key.
  --server-ip ADDRESS   Public IPv4 address. Auto-detected when omitted.
  --domain NAME         HTTPS name. Defaults to <dashed-ip>.sslip.io.
  --node-name NAME      Display name used in the subscription.
  --country-emoji FLAG  Optional flag prefix, for example 🇺🇸.
  --force-caddy         Back up and replace an existing Caddyfile.
  -h, --help            Show this help.

The API key is requested with hidden input unless --api-key-file is used.
EOF
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

while (($#)); do
  case "$1" in
    --veid) VEID="${2:?missing value}"; shift 2 ;;
    --api-key-file) API_KEY_FILE="${2:?missing value}"; shift 2 ;;
    --server-ip) SERVER_IP="${2:?missing value}"; shift 2 ;;
    --domain) DOMAIN="${2:?missing value}"; shift 2 ;;
    --node-name) NODE_NAME="${2:?missing value}"; shift 2 ;;
    --country-emoji) COUNTRY_EMOJI="${2-}"; shift 2 ;;
    --force-caddy) FORCE_CADDY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

[[ "${EUID}" -eq 0 ]] || die "run this installer as root"
command -v systemctl >/dev/null || die "systemd is required"
[[ -r /etc/os-release ]] || die "cannot identify the operating system"
# shellcheck source=/dev/null
source /etc/os-release
case "${ID:-}" in
  debian|ubuntu) ;;
  *) die "only Debian and Ubuntu are currently supported" ;;
esac

if [[ -z "$VEID" ]]; then
  read -rp "KiwiVM VEID: " VEID
fi
[[ "$VEID" =~ ^[0-9]+$ ]] || die "VEID must contain digits only"

if [[ -n "$API_KEY_FILE" ]]; then
  [[ -r "$API_KEY_FILE" ]] || die "cannot read API key file"
  API_KEY="$(tr -d '\r\n' < "$API_KEY_FILE")"
else
  read -rsp "KiwiVM API key (input hidden): " API_KEY
  printf '\n'
fi
[[ ${#API_KEY} -ge 16 ]] || die "API key looks too short"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl openssl python3 gpg debian-keyring \
  debian-archive-keyring apt-transport-https

if [[ -z "$SERVER_IP" ]]; then
  SERVER_IP="$(curl -4fsSL --max-time 15 https://api.ipify.org || true)"
fi
[[ "$SERVER_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] \
  || die "could not determine a valid public IPv4 address; use --server-ip"

if [[ -z "$DOMAIN" ]]; then
  DOMAIN="${SERVER_IP//./-}.sslip.io"
fi
[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || die "domain contains unsupported characters"

umask 077
install -d -m 0700 "$CLIENT_DIR"

if command -v caddy >/dev/null 2>&1; then
  CADDY_WAS_INSTALLED=1
  [[ "$FORCE_CADDY" -eq 1 ]] \
    || die "Caddy already exists. Review its config, then rerun with --force-caddy."
else
  CADDY_WAS_INSTALLED=0
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    > /etc/apt/sources.list.d/caddy-stable.list
  chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  chmod o+r /etc/apt/sources.list.d/caddy-stable.list
  apt-get update
  apt-get install -y caddy
fi

if ! command -v hysteria >/dev/null 2>&1; then
  bash <(curl -fsSL https://get.hy2.sh/)
fi
command -v hysteria >/dev/null || die "Hysteria installation failed"

install -d -m 0750 -o hysteria -g hysteria /etc/hysteria
hysteria cert \
  --host "$SERVER_IP" \
  --valid-for 87600h \
  --cert /etc/hysteria/server.crt \
  --key /etc/hysteria/server.key \
  --overwrite \
  >"$CLIENT_DIR/certificate-generation.txt"

AUTH_SECRET="$(openssl rand -hex 32)"
CERT_PIN="$(openssl x509 -noout -fingerprint -sha256 -in /etc/hysteria/server.crt | cut -d= -f2)"
CERT_PIN_URI="${CERT_PIN//:/%3A}"

cat >/etc/hysteria/config.yaml <<EOF
listen: :443

tls:
  cert: /etc/hysteria/server.crt
  key: /etc/hysteria/server.key
  sniGuard: disable

auth:
  type: password
  password: ${AUTH_SECRET}

masquerade:
  type: string
  string:
    content: "<!doctype html><html><head><title>Welcome</title></head><body><h1>Welcome</h1></body></html>"
    headers:
      content-type: "text/html; charset=utf-8"
    statusCode: 200
EOF

chown root:hysteria /etc/hysteria/config.yaml
chown hysteria:hysteria /etc/hysteria/server.crt /etc/hysteria/server.key
chmod 0640 /etc/hysteria/config.yaml /etc/hysteria/server.crt /etc/hysteria/server.key
systemctl enable --now hysteria-server.service
systemctl restart hysteria-server.service

NODE_URI="hysteria2://${AUTH_SECRET}@${SERVER_IP}:443/?insecure=1&pinSHA256=${CERT_PIN_URI}"
SUBSCRIPTION_TOKEN="$(openssl rand -hex 32)"

getent group kiwisub >/dev/null || groupadd --system kiwisub
id kiwisub >/dev/null 2>&1 \
  || useradd --system --gid kiwisub --home-dir /nonexistent --shell /usr/sbin/nologin kiwisub
install -d -m 0750 -o root -g kiwisub "$CONFIG_DIR"
install -d -m 0755 "$APP_DIR"
install -m 0755 "$PROJECT_ROOT/server/app.py" "$APP_DIR/app.py"
install -m 0644 "$PROJECT_ROOT/server/kiwivm-subscription.service" \
  "/etc/systemd/system/$SERVICE_NAME"

printf '%s\n' "$VEID" >"$CONFIG_DIR/veid"
printf '%s\n' "$API_KEY" >"$CONFIG_DIR/api_key"
printf '%s\n' "$NODE_URI" >"$CONFIG_DIR/node_uri"
printf '%s\n' "$SUBSCRIPTION_TOKEN" >"$CONFIG_DIR/token"
printf '%s\n' "$NODE_NAME" >"$CONFIG_DIR/node_name"
printf '%s\n' "$COUNTRY_EMOJI" >"$CONFIG_DIR/country_emoji"
chown root:kiwisub "$CONFIG_DIR"/*
chmod 0640 "$CONFIG_DIR"/*

if [[ -f /etc/caddy/Caddyfile ]]; then
  CADDY_BACKUP="/etc/caddy/Caddyfile.${PROJECT_NAME}.$(date +%Y%m%d%H%M%S).bak"
  cp -a /etc/caddy/Caddyfile "$CADDY_BACKUP"
  printf '%s\n' "$CADDY_BACKUP" >"$CONFIG_DIR/caddy_backup_path"
fi
printf '%s\n' "$CADDY_WAS_INSTALLED" >"$CONFIG_DIR/caddy_was_installed"
chown root:kiwisub "$CONFIG_DIR"/caddy_*
chmod 0640 "$CONFIG_DIR"/caddy_*

cat >/etc/caddy/Caddyfile <<EOF
{
    auto_https disable_redirects
    servers :443 {
        protocols h1 h2
    }
}

${DOMAIN} {
    encode zstd gzip
    header {
        -Server
        X-Content-Type-Options nosniff
        Referrer-Policy no-referrer
    }
    reverse_proxy 127.0.0.1:18080
}
EOF

caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME" caddy

if command -v ufw >/dev/null 2>&1 && ufw status | grep -q '^Status: active'; then
  ufw allow 22/tcp comment 'SSH'
  ufw allow 443/udp comment 'Hysteria 2'
  ufw allow 443/tcp comment 'Private subscription HTTPS'
fi

SUBSCRIPTION_URL="https://${DOMAIN}/sub/${SUBSCRIPTION_TOKEN}"
cat >"$CLIENT_DIR/credentials.txt" <<EOF
Server IP: ${SERVER_IP}
Hysteria 2 URI: ${NODE_URI}
Shadowrocket subscription: ${SUBSCRIPTION_URL}

Keep this file private. It contains live credentials.
EOF
chmod 0600 "$CLIENT_DIR/credentials.txt"

for _attempt in {1..20}; do
  if curl -fsS "http://127.0.0.1:18080/sub/${SUBSCRIPTION_TOKEN}" >/dev/null; then
    break
  fi
  sleep 1
done
curl -fsS "http://127.0.0.1:18080/sub/${SUBSCRIPTION_TOKEN}" >/dev/null \
  || die "the private subscription service did not pass its local health check"

systemctl is-active --quiet hysteria-server.service
systemctl is-active --quiet "$SERVICE_NAME"
systemctl is-active --quiet caddy

printf '\nInstallation completed.\n'
printf 'Private client details: %s\n' "$CLIENT_DIR/credentials.txt"
printf 'Read them with: sudo cat %q\n' "$CLIENT_DIR/credentials.txt"
printf 'Do not publish that file or its contents.\n'
