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

## Changed

| Pattern | Replacement | Count (approx) |
|---------|-------------|----------------|
| public peer IP | `REDACTED_PUBLIC_IP` | 48 |
| LAN IP | `192.168.x.x` | 12 |
| home directory path | `~` | 18 |
| UUID v4 strings (relay / similar) | `REDACTED_UUID` | 7 |
| systemd `Invocation:` 32-hex | `REDACTED_INVOCATION` | 1 |
| WebRTC `sha-256` DTLS fingerprints | `REDACTED_WEBRTC_FINGERPRINT` | 29 |
| Tester first name in proof RESULT notes | `tester` | ~3 |

## Excluded from the repo

- `xdph-before-fix02.bin` (1.5 MB binary)
- `RemoteDesktop.cpp.before-fix04` (intermediate full source dump)
- WayVNC config / password: not present in the proof tarball

## Left as-is (intentional)

- Hostname `omarchy` in journal lines
- Connector name `HDMI-A-1` (not a monitor serial)
- PipeWire / D-Bus unique names (`:1.xxx`, pipewire-serial numbers)
- Public stun/relay hostnames (`stun.l.google.com`, `ovh-west1.rustdesk.com`)
- Upstream author name `keitheis` in docs
- `/home/builder/...` paths inside RustDesk Arch package debug symbols (not a personal home)

## Script path

`scripts/xdph-rd-on-lock` was generalized to log under `$XDG_STATE_HOME/xdph-rd/` instead of a hard-coded `~/Projects/xdph-rd/proof/` path. The as-tested script is saved as `proof/xdph-rd-on-lock.as-tested` (with `~` redaction only).
