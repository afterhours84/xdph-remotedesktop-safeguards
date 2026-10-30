# xdph RemoteDesktop safeguards (PR #426 based)

User-local patches on top of draft [xdg-desktop-portal-hyprland PR #426](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/426) (head `0204ffbb`) that add a RemoteDesktop backend for Hyprland, plus practical privacy safeguards and two bugfixes found while testing.

**Status:** local writeup and proof only. Nothing here has been published. Review before posting.

**Not a security audit.** These are practical safeguards for controlling your own machine. They do not claim to close every race or replace compositor-level lock enforcement.

## Tested stack

| Component | Version |
|-----------|---------|
| Hyprland | 0.56.2 (commit efb50993) |
| xdg-desktop-portal-hyprland (stock) | 1.4.1 |
| xdg-desktop-portal | 1.22.1 |
| RustDesk (client) | 1.5.0 on Windows |
| RustDesk (server) | 1.5.0 on Omarchy |
| Host | Omarchy (Arch-based), Wayland / Hyprland |

End-to-end: Windows gaming PC controlling Omarchy over RustDesk, with screen picker and consent on the Omarchy side.

## What PR #426 already provides

- `org.freedesktop.impl.portal.RemoteDesktop`
- Virtual pointer (`zwlr_virtual_pointer_v1`) and virtual keyboard (`zwp_virtual_keyboard_v1`)
- `NotifyKeyboardKeysym` (needed by RustDesk)
- Device bitmask masking (RustDesk asks for 7; keyboard|pointer = 3 is granted)
- Consent UI via `hyprland-share-picker --remote-desktop`
- Combined RemoteDesktop + ScreenCast session
- libei `ConnectToEIS`
- `hyprland.portal` lists RemoteDesktop

## What we added

1. **Consent every session.** Restore tokens are ignored; persistence is not offered. Someone at the machine must pick a screen and approve each time.
2. **One remote session at a time.** A second `CreateSession` is rejected while one exists. Exact log line: `[remotedesktop] rejecting CreateSession: another remote session already exists` ([proof/23-second-session-test.txt](proof/23-second-session-test.txt), [proof/24-control-session-test.txt](proof/24-control-session-test.txt)).
3. **Close all sessions on screen lock** via `hyprland_lock_notifier_v1` (Hyprland socket2 has no `lock>>` event). Releases held keys/buttons, drops virtual devices, emits `Session.Closed`. Also refuses `CreateSession` while locked.
4. **Optional lock hook** `~/.local/bin/xdph-rd-on-lock` ([scripts/xdph-rd-on-lock](scripts/xdph-rd-on-lock)). After lock close, restarts RustDesk so the viewer gets a real disconnect. Workaround for RustDesk 1.5.0 keeping a stale portal session.
5. **Bugfix: poll fd ordering** in `startEventLoop`. Fds registered during portal construction shifted indices 0..2 (dbus/wayland/pipewire), causing ~156% CPU spin and CreateSession `NoReply`. See [patches/02-pollfd-order.patch](patches/02-pollfd-order.patch), [proof/04-install-verify.txt](proof/04-install-verify.txt), [proof/09-after-fix01.txt](proof/09-after-fix01.txt).
6. **Bugfix: inverted vertical scroll** in PR #426. The PR negated dy; RustDesk already sends the expected sign, so scrolling went the wrong way. See [patches/05-scroll-direction.patch](patches/05-scroll-direction.patch), [proof/22-fix04-RESULT.txt](proof/22-fix04-RESULT.txt).

## Test results

Times are America/Phoenix (UTC-7), 2026-10-29.

| Test | Result | Evidence |
|------|--------|----------|
| Remote control (mouse + keyboard) | PASS | [proof/10-success.txt](proof/10-success.txt) |
| Consent / screen picker each connect | PASS | Observed in session; reconnect after lock required fresh picker ([proof/19-lock-test3-RESULT.txt](proof/19-lock-test3-RESULT.txt)) |
| Lock closes portal remote session | PASS | `[remotedesktop] session locked: closing remote sessions` ([proof/16-lock-test2-portal.snapshot.log](proof/16-lock-test2-portal.snapshot.log)) |
| Lock hook restarts RustDesk; viewer reconnect needs fresh consent | PASS | [proof/lock-hook.log](proof/lock-hook.log), [proof/19-lock-test3-RESULT.txt](proof/19-lock-test3-RESULT.txt) |
| Second CreateSession while one active | PASS (rejected) | Exact reject line in [proof/24-control-session-test.txt](proof/24-control-session-test.txt); active session unaffected ([proof/23-second-session-test.txt](proof/23-second-session-test.txt)) |
| Control: CreateSession after RustDesk restart (no active session) | PASS | [proof/24-control-session-test.txt](proof/24-control-session-test.txt) |
| Scroll direction | PASS after fix-04 | [proof/22-fix04-RESULT.txt](proof/22-fix04-RESULT.txt) |

## Known limitations

- **Not atomic with the lock.** There is a small race between the compositor locking and the portal closing sessions. This does not patch Hyprland's compositor queue.
- **RustDesk 1.5.0 keeps its portal session** after the viewer disconnects (and after the portal closes the session, the viewer can freeze without a clean "disconnected" UI). That blocks new sessions until RustDesk is restarted. Upstream work: [rustdesk/rustdesk#16178](https://github.com/rustdesk/rustdesk/pull/16178); master also has `try_close_portal_session`. The lock hook is a stopgap, not a RustDesk patch.
- **Attended only.** Someone at the machine must approve. No unattended / trusted-app allowlist.
- **User-local install only.** Does not overwrite `/usr`. See [INSTALL.md](INSTALL.md).
- **Dead code in the tree:** unused socket2 `setupLockWatch` / `onHyprlandIpcEvent` helpers remain in `full.diff` from an earlier attempt. They are never called. Active lock path is `hyprland_lock_notifier_v1`.
- **Not a security audit.**

## Prior art

Credit where it is due. Basic RemoteDesktop on Hyprland has been pursued elsewhere; the safeguards and the two PR #426 bugfixes are what this writeup focuses on.

- [PR #426](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/426) by keitheis (our base)
- Related PRs: [#402](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/402), [#428](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/428), [#308](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/308)
- Tracking: [issue #252](https://github.com/hyprwm/xdg-desktop-portal-hyprland/issues/252)
- [spotdemo4/xdg-desktop-portal-hyprland](https://github.com/spotdemo4/xdg-desktop-portal-hyprland) fork with RemoteDesktop
- [xdg-desktop-portal-luminous](https://github.com/waycrate/xdg-desktop-portal-luminous) (common Omarchy suggestion for RustDesk)

## Patches

See [patches/README.md](patches/README.md). Prefer `patches/full.diff` to reproduce exactly what was tested on Omarchy.

## Install / rollback

See [INSTALL.md](INSTALL.md). Prefix used in testing: `~/.local/opt/xdph-rd` with user systemd unit and portal config under `~`.

## License

xdg-desktop-portal-hyprland is BSD-3-Clause. Patches here are offered under the same license as upstream. See [LICENSE](LICENSE).

## Proof redaction

Proof logs under `proof/` were redacted before packaging. See [REDACTIONS.md](REDACTIONS.md).
