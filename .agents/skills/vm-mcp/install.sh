# ratios: loc_comments=115:18 imports_exports=0:0 calls_definitions=2:0
#!/usr/bin/env bash
set -euo pipefail

# Install canonical vm-mcp on a Linux VM.
#
# Usage:
#   sudo VM_MCP_ROOT=/srv/vm-mcp/workspace bash vm-mcp/install.sh
#   sudo VM_MCP_PROFILE=personal-console \
#        VM_MCP_ROOT=/srv/vm-mcp/workspace bash vm-mcp/install.sh
#
# Profiles:
#   read-only        read tools only (default)
#   workspace        workspace write tools + confined shell_exec
#   personal-console workspace tools plus brokered user_exec/admin_exec
#
# The MCP HTTP service always binds to 127.0.0.1. personal-console starts a
# separate root Unix-socket broker; it does not make the MCP service root.

if [[ ${EUID} -ne 0 ]]; then
  echo "ERROR: run as root (sudo ... bash vm-mcp/install.sh)" >&2
  exit 2
fi

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="${VM_MCP_INSTALL_ROOT:-/opt/vm-mcp}"
WORK_ROOT="${VM_MCP_ROOT:-/srv/vm-mcp/workspace}"
PROFILE="${VM_MCP_PROFILE:-read-only}"
PORT="${VM_MCP_PORT:-8765}"
SERVICE_USER="${VM_MCP_SERVICE_USER:-vmmcp}"
SERVICE_GROUP="$SERVICE_USER"
ADMIN_SOCKET="${VM_MCP_ADMIN_SOCKET:-/run/vm-mcp/admin.sock}"
NOLOGIN="$(command -v nologin || true)"
[[ -n "$NOLOGIN" ]] || NOLOGIN=/bin/false

case "$PROFILE" in
  read-only|workspace|personal-console) ;;
  *) echo "ERROR: VM_MCP_PROFILE must be read-only, workspace, or personal-console" >&2; exit 3 ;;
esac
case "$WORK_ROOT" in
  /*) ;;
  *) echo "ERROR: VM_MCP_ROOT must be an absolute path" >&2; exit 3 ;;
esac
case "$WORK_ROOT" in
  *$'\n'*|*$'\r'*) echo "ERROR: VM_MCP_ROOT must not contain newlines" >&2; exit 3 ;;
esac

install_python() {
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq python3 python3-venv ca-certificates >/dev/null
  elif command -v dnf >/dev/null 2>&1; then
    dnf install -y python3 ca-certificates >/dev/null
  elif command -v yum >/dev/null 2>&1; then
    yum install -y python3 ca-certificates >/dev/null
  fi
  command -v python3 >/dev/null 2>&1 || {
    echo "ERROR: python3 is required and no supported package manager installed it" >&2
    exit 4
  }
}

systemd_quote() {
  local value=$1
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  printf '"%s"' "$value"
}

install_python

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --home "$WORK_ROOT/.vm-mcp-home" --shell "$NOLOGIN" "$SERVICE_USER"
else
  usermod --home "$WORK_ROOT/.vm-mcp-home" "$SERVICE_USER"
fi

# Existing application directories retain their existing ownership. This fixes
# the dangerous first-release behavior where selecting an existing VM_MCP_ROOT
# could transfer ownership of that directory to vmmcp.
if [[ ! -e "$WORK_ROOT" ]]; then
  install -d -o "$SERVICE_USER" -g "$SERVICE_GROUP" -m 0750 "$WORK_ROOT"
elif [[ ! -d "$WORK_ROOT" ]]; then
  echo "ERROR: VM_MCP_ROOT exists but is not a directory: $WORK_ROOT" >&2
  exit 5
fi
install -d -o "$SERVICE_USER" -g "$SERVICE_GROUP" -m 0700 "$WORK_ROOT/.vm-mcp-home"
install -d -o root -g root -m 0755 "$INSTALL_ROOT" "$INSTALL_ROOT/systemd"

for file in server.py policy.py admin_client.py admin_broker.py requirements.txt; do
  install -m 0644 "$SOURCE_ROOT/$file" "$INSTALL_ROOT/$file"
done
install -m 0644 "$SOURCE_ROOT/systemd/vm-mcp.service" "$INSTALL_ROOT/systemd/vm-mcp.service"
install -m 0644 "$SOURCE_ROOT/systemd/vm-mcp-admin.service" "$INSTALL_ROOT/systemd/vm-mcp-admin.service"

SOURCE_COMMIT=hmmm
if command -v git >/dev/null 2>&1 && git -C "$SOURCE_ROOT" rev-parse HEAD >/dev/null 2>&1; then
  SOURCE_COMMIT="$(git -C "$SOURCE_ROOT" rev-parse HEAD)"
fi
printf '%s\n' "$SOURCE_COMMIT" > "$INSTALL_ROOT/SOURCE_COMMIT"
chmod 0644 "$INSTALL_ROOT/SOURCE_COMMIT"

if [[ ! -x "$INSTALL_ROOT/.venv/bin/python" ]]; then
  python3 -m venv "$INSTALL_ROOT/.venv"
fi
"$INSTALL_ROOT/.venv/bin/python" -m pip install --upgrade pip >/dev/null
"$INSTALL_ROOT/.venv/bin/python" -m pip install -r "$INSTALL_ROOT/requirements.txt"

install -m 0644 "$SOURCE_ROOT/systemd/vm-mcp.service" /etc/systemd/system/vm-mcp.service
install -m 0644 "$SOURCE_ROOT/systemd/vm-mcp-admin.service" /etc/systemd/system/vm-mcp-admin.service
cat > /etc/vm-mcp.env <<EOF
VM_MCP_ROOT=$(systemd_quote "$WORK_ROOT")
VM_MCP_PROFILE=$PROFILE
VM_MCP_PORT=$PORT
VM_MCP_ADMIN_SOCKET=$(systemd_quote "$ADMIN_SOCKET")
EOF
chmod 0600 /etc/vm-mcp.env

install -d -m 0755 /etc/systemd/system/vm-mcp.service.d
cat > /etc/systemd/system/vm-mcp.service.d/workspace.conf <<EOF
[Service]
ReadWritePaths=
ReadWritePaths=$WORK_ROOT
EOF
chmod 0644 /etc/systemd/system/vm-mcp.service.d/workspace.conf

systemctl daemon-reload
if [[ "$PROFILE" == personal-console ]]; then
  systemctl enable --now vm-mcp-admin.service
  systemctl restart vm-mcp-admin.service
else
  systemctl disable --now vm-mcp-admin.service >/dev/null 2>&1 || true
fi
systemctl enable --now vm-mcp.service
systemctl restart vm-mcp.service

printf '\nvm-mcp installed\n'
printf '  source commit: %s\n' "$SOURCE_COMMIT"
printf '  endpoint:      http://127.0.0.1:%s/mcp\n' "$PORT"
printf '  workspace:     %s\n' "$WORK_ROOT"
printf '  profile:       %s\n' "$PROFILE"
if [[ "$PROFILE" == personal-console ]]; then
  printf '  root broker:   %s\n' "$ADMIN_SOCKET"
  printf '  user_exec:     enabled\n'
  printf '  admin_exec:    enabled (root)\n'
else
  printf '  root broker:   disabled\n'
fi
systemctl --no-pager --full status vm-mcp.service | sed -n '1,14p'
# ratios: loc_comments=115:18 imports_exports=0:0 calls_definitions=2:0
