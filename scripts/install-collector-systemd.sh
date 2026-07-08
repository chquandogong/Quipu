#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dry_run=0
enable_timer=1

systemd_dir="${SYSTEMD_DIR:-/etc/systemd/system}"
config_dir="${CONFIG_DIR:-/etc/quipu}"
lib_dir="${LIB_DIR:-/usr/local/lib/quipu}"

usage() {
  cat <<'USAGE'
Usage: scripts/install-collector-systemd.sh [--dry-run] [--no-enable]

Installs Quipu collector systemd unit files, wrapper, and a sample config.
The collector Python package must already provide quipu-collector on the target
machine, or QUIPU_COLLECTOR_BIN must be set in /etc/quipu/collector.env.
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
    echo "This installer must run as root unless --dry-run is used." >&2
    exit 77
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=1
      shift
      ;;
    --no-enable)
      enable_timer=0
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

run install -D -m 0755 "${repo_root}/apps/collector/ops/bin/quipu-collector-run" "${lib_dir}/quipu-collector-run"
run install -D -m 0644 "${repo_root}/apps/collector/ops/systemd/quipu-collector.service" "${systemd_dir}/quipu-collector.service"
run install -D -m 0644 "${repo_root}/apps/collector/ops/systemd/quipu-collector.timer" "${systemd_dir}/quipu-collector.timer"

if [[ -f "${config_dir}/collector.env" ]]; then
  log "Keeping existing ${config_dir}/collector.env"
else
  run install -D -m 0600 "${repo_root}/apps/collector/ops/collector.env.example" "${config_dir}/collector.env"
fi

run systemctl daemon-reload

if [[ "${enable_timer}" -eq 1 ]]; then
  run systemctl enable --now quipu-collector.timer
else
  log "Timer enable skipped by --no-enable"
fi

log "Quipu collector systemd files installed."
log "Edit ${config_dir}/collector.env before relying on scheduled collection."
