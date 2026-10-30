Thanks for the RemoteDesktop work in this PR, keitheis. We tested head `0204ffbb` on Hyprland 0.56.2 with RustDesk 1.5.0 (Windows client to an Omarchy host) and got end-to-end mouse and keyboard control after applying a couple of small fixes.

**Bugs found while integrating**

1. **Poll fd ordering in `startEventLoop`.** The dispatch loop assumes indices 0..2 are dbus, wayland, and pipewire. When a portal registers an extra fd during construction (before those three are added), the indices shift. On our build that showed up as ~156% CPU at idle and CreateSession hanging / NoReply. Fix: snapshot any early fds, register the three core fds (plus wake), then append the early ones. Patch: `patches/02-pollfd-order.patch` in the writeup linked below.

2. **Vertical scroll sign.** `NotifyPointerAxis` / discrete / EIS paths negate dy (and discrete steps). RustDesk already sends the sign Hyprland expects, so wheel scrolling ran backwards. Removing the negation fixed it with RustDesk. Patch: `patches/05-scroll-direction.patch`.

**Optional safeguards we layered on for our own use** (happy to trim or rework if useful upstream):

- Consent every session (ignore restore tokens; do not offer persist).
- One RemoteDesktop session at a time.
- On screen lock, close remote sessions via `hyprland_lock_notifier_v1` (Hyprland socket2 does not emit `lock>>`), release held keys/buttons, and refuse CreateSession while locked.
- Optional `~/.local/bin/xdph-rd-on-lock` hook: we use it to restart RustDesk 1.5.0 so the viewer gets a clean disconnect (RustDesk currently keeps a stale portal session; upstream has related work on master / PR 16178).

Writeup, patches, and redacted proof logs (local draft, not published until you are happy with them):

REPO_URL_PLACEHOLDER

Happy to open follow-up PRs or drop just the two bugfix patches if you would rather keep safeguards out of this PR.
