# Gaps / honesty notes

- `patches/01-safeguards.patch` and `03-lock-notify.patch` are best-effort splits. Prefer `patches/full.diff` to reproduce the tested tree. See `patches/README.md`.
- `full.diff` still contains unused socket2 IPC helpers (`setupLockWatch` / `onHyprlandIpcEvent`). They are never called. Active lock path is `hyprland_lock_notifier_v1`.
- Lock test 3 portal journal (`proof/18-lock-test3-portal.log`) was truncated when the portal was restarted for the scroll fix, so the exact `session locked: closing remote sessions` line for that run is not in that file. Evidence for test 3 is `proof/lock-hook.log` + `proof/19-lock-test3-RESULT.txt`. The same close line is present for an earlier lock run in `proof/16-lock-test2-portal.snapshot.log`.
- Control CreateSession after viewer disconnect still failed until RustDesk was restarted (session reuse). Documented as a known limitation.
- No unattended-access testing. No security audit.
- Nothing published: no git remote, no `gh` push, no PR comment posted.
