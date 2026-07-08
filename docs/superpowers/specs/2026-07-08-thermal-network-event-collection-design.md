# Thermal And Network Event Collection

> Date: 2026-07-08
> Status: implementation track
> Release target: v0.4.0

## Problem

Quipu v0.3.3 has UI slots for future telemetry, but thermal throttling and
network reconnect history are still mostly demo data. The product needs to turn
those slots into real signals without making the collector heavy or unsafe.

## Chosen Design

Implement two event collectors in the existing one-shot collector:

- Kernel thermal events: identify thermal throttling, package temperature
  threshold, CPU clock throttling, and critical thermal messages.
- Network reconnect events: identify NetworkManager, supplicant, carrier,
  disconnect, reconnect, DHCP, and link-state changes.

Collector output remains the existing `events` array. It sends only compact
summaries, source labels, timestamps, and stable fingerprints. It does not send
raw logs.

## Collection Strategy

Use a best-effort, read-only approach:

- In real runs, try short `journalctl` reads for kernel and NetworkManager
  windows.
- If `journalctl` is unavailable or not permitted, continue without failing the
  observation.
- For tests and lightweight local fixtures, parse small log excerpt files under
  the selected root.

## Server Analysis

Extend rule-based findings so specific events are not only generic warnings:

- Thermal throttling event -> `Thermal throttling reported`
- Network reconnect/disconnect event -> `Network reconnect reported`

Existing investigation queue/detail contracts stay unchanged.

## UI

Extend the Telemetry Matrix with direct tiles:

- `Thermal Throttling`
- `Reconnect History`

These tiles sit beside Memory, Network Events, Kernel Warnings, and Agent
Freshness. They show whether the slot is live and how many warning events were
observed.

## Boundaries

- No daemon yet.
- No remote repair command.
- No full raw-log upload.
- No privileged-only fan or SMART collection in this slice.
- No API schema migration.

## Verification

- Collector test must prove log excerpts become event summaries.
- Server tests must prove event-specific findings and queue titles.
- Web test must prove Telemetry Matrix shows thermal throttling and reconnect
  history.
- Full verification must include collector, server, web tests, web build, and
  whitespace check.
