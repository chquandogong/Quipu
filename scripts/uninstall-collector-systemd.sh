#!/usr/bin/env bash
set -euo pipefail

dry_run=0
purge_config=0

systemd_dir="${SYSTEMD_DIR:-/etc/systemd/system}"
config_dir="${CONFIG_DIR:-/etc/quipu}"
lib_dir="${LIB_DIR:-/usr/local/lib/quipu}"

usage() {
  cat <<'USAGE'
Usage: scripts/uninstall-collector-systemd.sh [--dry-run] [--purge-config]

Removes Quipu collector systemd files. The config file is preserved unless
--purge-config is passed.
USAGE
}

log() {
  printf '%s\n' "$*"
}

run() {
  if [[ "${dry_run}" -eq 1 ]]; then
    log "DRY RUN: $*"
  else
    "$@"
  fi
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "This uninstaller must run as root unless --dry-run is used." >&2
    exit 77
  fi
}

remove_file() {
  local path="$1"
  if [[ "${dry_run}" -eq 1 ]]; then
    log "DRY RUN: rm -f ${path}"
  else
    rm -f "${path}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=1
      shift
      ;;
    --purge-config)
      purge_config=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if [[ "${dry_run}" -ne 1 ]]; then
  require_root
fi

run systemctl disable --now quipu-collector.timer
remove_file "${systemd_dir}/quipu-collector.timer"
remove_file "${systemd_dir}/quipu-collector.service"
remove_file "${lib_dir}/quipu-collector-run"

if [[ "${purge_config}" -eq 1 ]]; then
  remove_file "${config_dir}/collector.env"
else
  log "Keeping ${config_dir}/collector.env"
fi

run systemctl daemon-reload

log "Quipu collector systemd files removed."
