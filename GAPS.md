# Gaps / honesty notes

- `patches/01-safeguards.patch` and `03-lock-notify.patch` are best-effort splits. Prefer `patches/full.diff` to reproduce the tested tree. See `patches/README.md`.
- `full.diff` still contains unused socket2 IPC helpers (`setupLockWatch` / `onHyprlandIpcEvent`). They are never called. Active lock path is `hyprland_lock_notifier_v1`.
- Lock test 3 portal journal (`proof/18-lock-test3-portal.log`) was truncated when the portal was restarted for the scroll fix, so the exact `session locked: closing remote sessions` line for that run is not in that file. Evidence for test 3 is `proof/lock-hook.log` + `proof/19-lock-test3-RESULT.txt`. The same close line is present for an earlier lock run in `proof/16-lock-test2-portal.snapshot.log`.
- Control CreateSession after viewer disconnect still failed until RustDesk was restarted (session reuse). Documented as a known limitation.
- Unlock waiter depends on Omarchy's `omarchy-hyprland-session-locked` (and optionally `omarchy-shell lock status`). Not portable to non-Omarchy Hyprland setups without a replacement unlock signal.
- WebRTC / RustDesk 1.5.0: SIGKILL does not produce a clear TCP-style "forcibly closed" dialog on the viewer (proof/40-42). Confirmed working behavior is drop + reject while locked + restart after unlock (proof/43-44).
- PR #448 live trial (2026-10-30): lock did not disconnect; second CreateSession accepted; restore tokens can skip consent (proof/34, 37, 31). Those are intentional differences vs this safeguarded build, not bugs in #448.
- No unattended-access testing. No security audit.
- Basic RemoteDesktop on Hyprland already exists elsewhere (luminous, spotdemo4 fork, xdph PRs #402/#426/#428/#448). This repo does not claim to be first; it documents the safeguards and two bugfixes (now upstreamed into #448) for our Omarchy + RustDesk setup.
