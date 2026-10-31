# Redactions

Proof logs under `proof/` were scrubbed before packaging. Originals stay on the test machine / private archive only.

## Scanned for

- Public IPs
- LAN IPs
- RustDesk peer / desktop IDs
- Hostnames other than generic `omarchy`
- Usernames and home paths (home directory path)
- Emails, phone numbers
- Real names (other than upstream author credit)
- Machine IDs / UUIDs (relay UUIDs, systemd Invocation)
- MAC addresses, hardware / monitor serials
- WayVNC config or passwords (none present in this proof set)
- Private keys / tokens / passwords
- Em dashes (U+2014) / en dashes (U+2013) - replaced with ASCII `-`

## Changed

| Pattern | Replacement | Notes |
|---------|-------------|-------|
| public peer IPs | `REDACTED_PUBLIC_IP` | proof 01-24 and 25-44 |
| LAN IPs (RFC1918) | `192.168.x.x` (or `10.x.x.x` / `172.16.x.x`) | |
| personal home directory path | `~` | |
| UUID v4 strings (relay / similar) | `REDACTED_UUID` | |
| systemd `Invocation:` 32-hex | `REDACTED_INVOCATION` | |
| WebRTC `sha-256` DTLS fingerprints | `REDACTED_WEBRTC_FINGERPRINT` | |
| Tester first name in proof RESULT notes | `tester` | |
| Gaming-PC product nickname | `gaming-pc` | |

## Excluded from the repo

- `xdph-before-fix02.bin` (1.5 MB binary)
- `RemoteDesktop.cpp.before-fix04` (intermediate full source dump)
- Proof `*.bak` script snapshots from intermediate hook edits
- WayVNC config / password: not present in the proof tarball

## Left as-is (intentional)

- Hostname `omarchy` in journal lines
- Connector name `HDMI-A-1` (not a monitor serial)
- PipeWire / D-Bus unique names (`:1.xxx`, pipewire-serial numbers)
- Public stun/relay hostnames (`stun.l.google.com`, `ovh-west1.rustdesk.com`)
- Upstream author name `keitheis` in docs
- `/home/builder/...` paths inside RustDesk Arch package debug symbols (not a personal home)
- Process IDs in logs

## Script path

`scripts/xdph-rd-on-lock` (and wait/on-unlock) log under `${XDG_STATE_HOME:-$HOME/.local/share}/xdph-rd/`.
As-tested copies are saved as `scripts/*.as-tested` and `proof/*.as-tested`.
