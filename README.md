# xdph RemoteDesktop safeguards (PR #426 based)

User-local patches on top of [xdg-desktop-portal-hyprland PR #426](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/426) (head `0204ffbb`, now closed) that add practical privacy safeguards for RemoteDesktop on Hyprland, plus two bugfixes found while testing. The bugfixes are also present upstream in open [PR #448](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/448).

**Not a security audit.** These are practical safeguards for controlling your own machine. They do not claim to close every race or replace compositor-level lock enforcement.

## Prior art (RustDesk / RemoteDesktop on Hyprland already exists elsewhere)

Remote control of a Hyprland desktop via the xdg-desktop-portal RemoteDesktop interface is not unique to this repo. Working implementations and in-progress upstream work include:

- [xdg-desktop-portal-luminous](https://github.com/waycrate/xdg-desktop-portal-luminous) (waycrate) - a portal for wlroots-based compositors; commonly suggested for RustDesk on Omarchy.
- [spotdemo4/xdg-desktop-portal-hyprland](https://github.com/spotdemo4/xdg-desktop-portal-hyprland) - a fork with RemoteDesktop.
- Upstream xdph PRs (verified 2026-10-30 via `gh`):
  - [#402](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/402) (open) - RemoteDesktop with ConnectToEIS
  - [#426](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/426) (closed, not merged) - continue RemoteDesktop and ConnectToEIS; our tested base at `0204ffbb`
  - [#428](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/428) (open) - revive portal implementation
  - [#448](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/448) (open, head `84b03f2a`) - "Fundamental remotedesktop portal"; PR body states it includes related fixes from #428, #426, and #402, and lists fixes for EIS device cleanup, held-key release, vertical scroll direction, and polling dispatch. It effectively supersedes #426 for the RemoteDesktop feature set.
  - Also related: [#308](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/308), tracking [issue #252](https://github.com/hyprwm/xdg-desktop-portal-hyprland/issues/252)

This repo documents what we layered on top of #426 for our Omarchy + RustDesk setup, and how that compares to a live trial of #448.

## What this repo adds (on top of PR #426)

1. **Consent every session, no persist.** Restore tokens are ignored; persistence is not offered. Someone at the machine must pick a screen and approve each connect.
2. **One remote session at a time.** A second `CreateSession` is rejected while one exists. Exact log line: `[remotedesktop] rejecting CreateSession: another remote session already exists` ([proof/23-second-session-test.txt](proof/23-second-session-test.txt), [proof/24-control-session-test.txt](proof/24-control-session-test.txt)).
3. **Close on lock + reject while locked.** Via `hyprland_lock_notifier_v1`: releases held keys/buttons, drops virtual devices, emits `Session.Closed`, and refuses `CreateSession` while locked.
4. **Kill RustDesk on lock; restart only after unlock.** Hook scripts:
   - [`scripts/xdph-rd-on-lock`](scripts/xdph-rd-on-lock) - `SIGKILL` rustdesk; arm unlock waiter (no restart while locked)
   - [`scripts/xdph-rd-wait-unlock`](scripts/xdph-rd-wait-unlock) - poll `omarchy-hyprland-session-locked` until unlock
   - [`scripts/xdph-rd-on-unlock`](scripts/xdph-rd-on-unlock) - start rustdesk via `setsid` if not already running
5. **Bugfix: poll fd ordering** in `startEventLoop` ([patches/02-pollfd-order.patch](patches/02-pollfd-order.patch)). Now also present in #448 (fd-keyed dispatch).
6. **Bug fix: inverted vertical scroll** in PR #426 ([patches/05-scroll-direction.patch](patches/05-scroll-direction.patch)). Now also present in #448.

## Comparison: this build vs PR #448 (tested 2026-10-30)

Live trial of #448 head `84b03f2a` on the same Omarchy host (proof/25-37), then restore of this safeguarded build (proof/38-39).

| Behavior | This build | PR #448 (as tested) | Evidence |
|----------|------------|---------------------|----------|
| Connect + consent picker | Yes | Yes | [proof/34-pr448-live-test-RESULT.txt](proof/34-pr448-live-test-RESULT.txt) |
| Scroll direction | Correct (our fix) | Correct (upstreamed) | proof/34; [proof/22-fix04-RESULT.txt](proof/22-fix04-RESULT.txt) |
| Close session on lock | Yes | No - session survived lock; tester unlocked remotely while locked | proof/34 |
| Reject CreateSession while another session active | Yes | No - second CreateSession accepted | [proof/37-pr448-second-session-RESULT.txt](proof/37-pr448-second-session-RESULT.txt) vs proof/23 |
| Force no persist / consent every time | Yes (`persistMode=0`) | No - restore tokens can skip consent | [proof/31-pr448-prep-RESULT.txt](proof/31-pr448-prep-RESULT.txt) |
| Kill rustdesk on lock; restart only after unlock | Yes (hooks) | N/A (no lock-close) | [proof/43-RESULT.txt](proof/43-RESULT.txt), [proof/44-unlock-fix-RESULT.txt](proof/44-unlock-fix-RESULT.txt) |

Diff notes: [proof/27-pr448-vs-ours-SUMMARY.txt](proof/27-pr448-vs-ours-SUMMARY.txt), [proof/31-pr448-prep-RESULT.txt](proof/31-pr448-prep-RESULT.txt).

## Tested stack

| Component | Version |
|-----------|---------|
| Hyprland | 0.56.2 (commit efb50993) |
| xdg-desktop-portal-hyprland (stock) | 1.4.1 |
| xdg-desktop-portal | 1.22.1 |
| RustDesk (client) | 1.5.0 on Windows |
| RustDesk (server) | 1.5.0 on Omarchy |
| Host | Omarchy (Arch-based), Wayland / Hyprland |
| Our installed binary md5 | `27011044bd5770cf78bcacd9f5c18cf4` |

End-to-end: Windows gaming PC controlling Omarchy over RustDesk, with screen picker and consent on the Omarchy side.

## Test results

Times are America/Phoenix (UTC-7). Early results 2026-10-29; #448 trial and unlock-fix confirmation 2026-10-30.

| Test | Result | Evidence |
|------|--------|----------|
| Remote control (mouse + keyboard) | PASS | [proof/10-success.txt](proof/10-success.txt) |
| Consent / screen picker each connect | PASS | [proof/19-lock-test3-RESULT.txt](proof/19-lock-test3-RESULT.txt) |
| Lock closes portal remote session | PASS | [proof/16-lock-test2-portal.snapshot.log](proof/16-lock-test2-portal.snapshot.log) |
| Second CreateSession while one active | PASS (rejected) | [proof/24-control-session-test.txt](proof/24-control-session-test.txt) |
| Scroll direction | PASS after fix-04 | [proof/22-fix04-RESULT.txt](proof/22-fix04-RESULT.txt) |
| #448 live: connect, scroll OK; lock did not disconnect | Observed | [proof/34-pr448-live-test-RESULT.txt](proof/34-pr448-live-test-RESULT.txt) |
| #448: second CreateSession accepted | Observed | [proof/37-pr448-second-session-RESULT.txt](proof/37-pr448-second-session-RESULT.txt) |
| Unlock fix: lock drops viewer; reconnect fails while locked; unlock restarts rustdesk + picker | PASS | [proof/44-unlock-fix-RESULT.txt](proof/44-unlock-fix-RESULT.txt), [proof/lock-hook.log](proof/lock-hook.log) |

## Known limitations

- **Not atomic with the lock.** Small race between compositor lock and portal session close. Does not patch Hyprland's compositor queue.
- **Unlock waiter is Omarchy-specific.** `xdph-rd-wait-unlock` polls `omarchy-hyprland-session-locked` (and optionally `omarchy-shell lock status`). Omarchy's Quickshell lock does not use hypridle unlock hooks. Other distros need an equivalent unlock signal.
- **WebRTC / RustDesk 1.5.0:** killing rustdesk does not produce a clear "forcibly closed" TCP-style dialog on the viewer. Observed behavior is: viewer drops; reconnect fails while locked; after unlock + restart, Retry shows picker + approve again ([proof/42-root-cause.txt](proof/42-root-cause.txt), proof/44).
- **Attended only.** Someone at the PC must approve each session. No unattended / trusted-app allowlist.
- **RustDesk can keep a stale portal session** after viewer disconnect until restart. Upstream: [rustdesk/rustdesk#16178](https://github.com/rustdesk/rustdesk/pull/16178). The lock/unlock hooks are a stopgap, not a RustDesk patch.
- **User-local install only.** Does not overwrite `/usr`. See [INSTALL.md](INSTALL.md).
- **Dead code in the tree:** unused socket2 `setupLockWatch` / `onHyprlandIpcEvent` helpers remain in `full.diff`. Active lock path is `hyprland_lock_notifier_v1`.
- **Not a security audit.**

## Patches

See [patches/README.md](patches/README.md). Prefer `patches/full.diff` to reproduce exactly what was tested on Omarchy.

## Install / rollback

See [INSTALL.md](INSTALL.md). Prefix used in testing: `~/.local/opt/xdph-rd` (or `~/.local/libexec` for the binary) with user systemd unit and portal config under `~`. Install all three hook scripts under `~/.local/bin/`.

## License

xdg-desktop-portal-hyprland is BSD-3-Clause. Patches here are offered under the same license as upstream. See [LICENSE](LICENSE).

## Proof redaction

Proof logs under `proof/` were redacted before packaging. See [REDACTIONS.md](REDACTIONS.md).
