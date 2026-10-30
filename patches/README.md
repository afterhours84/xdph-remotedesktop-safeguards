# Patches

Base: [xdg-desktop-portal-hyprland PR #426](https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/426) head `0204ffbb`.

| File | What |
|------|------|
| `full.diff` | Authoritative. Entire tree vs PR #426 as tested on Omarchy (includes all of the below). Prefer this to reproduce. |
| `01-safeguards.patch` | Best-effort: consent every session, one session at a time, refuse while locked, release held input, `closeAllSessions`, optional lock hook call. Still carries unused socket2 IPC helpers; see note in the file. |
| `02-pollfd-order.patch` | Clean. Fixes event-loop poll fd index assumption (156% CPU spin / CreateSession NoReply). |
| `03-lock-notify.patch` | Best-effort: bind `hyprland_lock_notifier_v1`, close sessions on lock/unlock. Needs `closeAllSessions` from 01/full. |
| `04-lock-hook.NOTES.txt` | Notes only. Script is `scripts/xdph-rd-on-lock`. |
| `05-scroll-direction.patch` | Clean. Stops inverting vertical scroll (PR #426 sign flip fights RustDesk). |

Splitting 01/03 cleanly is unreliable because `closeAllSessions`, held-input tracking, and lock wiring landed in the same files. If `git apply` of 01+03 conflicts, use `full.diff` alone, then you already have 02 and 05 inside it.
