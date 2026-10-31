#!/usr/bin/env python3
"""Second RemoteDesktop session probe against live portal (proof/23-style).
Creates a frontend org.freedesktop.portal.RemoteDesktop session while another
(RustDesk) session is expected to be open. Waits up to TIMEOUT_S for Response
signals (tester may need to approve a picker on Start).
"""
import os
import sys
import time
import traceback

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

TOKEN = os.environ.get("PROOF_TOKEN", "proof448s2")
TIMEOUT_S = int(os.environ.get("PROOF_TIMEOUT", "60"))
# KEYBOARD | POINTER | TOUCHSCREEN
DEVICE_TYPES = 7

DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
loop = GLib.MainLoop()

portal = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
rd = dbus.Interface(portal, "org.freedesktop.portal.RemoteDesktop")
sc = dbus.Interface(portal, "org.freedesktop.portal.ScreenCast")
sender = bus.get_unique_name().replace(":", "").replace(".", "_")

results = {
    "create": None,
    "select": None,
    "select_sources": None,
    "start": None,
    "errors": [],
    "session_path": None,
    "closed": False,
}

def log(msg):
    print(msg, flush=True)

def wait_response(request_path, label, timeout=TIMEOUT_S):
    box = {"done": False, "response": None}

    def on_response(response, results_dict):
        box["done"] = True
        box["response"] = (int(response), dict(results_dict))
        log(f"[{label}] Response code={response} results_keys={list(results_dict.keys())}")
        # decode a few common keys
        for k, v in results_dict.items():
            try:
                log(f"[{label}]   {k}={v}")
            except Exception:
                log(f"[{label}]   {k}=<?>")
        loop.quit()

    req = bus.get_object("org.freedesktop.portal.Desktop", request_path)
    req.connect_to_signal("Response", on_response, dbus_interface="org.freedesktop.portal.Request")
    log(f"[{label}] waiting up to {timeout}s on {request_path}")
    GLib.timeout_add_seconds(timeout, lambda: (loop.quit(), False)[1] if not box["done"] else False)
    loop.run()
    if not box["done"]:
        log(f"[{label}] TIMEOUT after {timeout}s")
        try:
            dbus.Interface(req, "org.freedesktop.portal.Request").Close()
        except Exception as e:
            log(f"[{label}] Request.Close after timeout: {e}")
        return None
    return box["response"]

def close_session(session_path):
    if not session_path:
        return
    try:
        sess = bus.get_object("org.freedesktop.portal.Desktop", session_path)
        dbus.Interface(sess, "org.freedesktop.portal.Session").Close()
        results["closed"] = True
        log(f"[cleanup] Session.Close {session_path}")
    except Exception as e:
        log(f"[cleanup] Session.Close failed: {e}")
        results["errors"].append(f"close:{e}")

def main():
    log(f"start token={TOKEN} timeout={TIMEOUT_S}s unique={bus.get_unique_name()}")
    # 1) CreateSession
    opts = {
        "handle_token": dbus.String(TOKEN),
        "session_handle_token": dbus.String(TOKEN + "s"),
    }
    try:
        req_path = rd.CreateSession(opts)
        log(f"[create] request={req_path}")
    except Exception as e:
        log(f"[create] CALL FAILED: {e}")
        results["errors"].append(f"create_call:{e}")
        traceback.print_exc()
        return 2

    resp = wait_response(str(req_path), "create", timeout=15)
    results["create"] = resp
    if resp is None:
        return 3
    code, res = resp
    if code != 0:
        log(f"[create] NONZERO response code={code} (rejected/cancelled/failed)")
        # Attempt cleanup of any partial session path if present
        sp = res.get("session_handle")
        if sp:
            close_session(str(sp))
        return 0  # expected path under one-session guard

    session_path = str(res.get("session_handle") or "")
    # Some portals return session_handle as object path variant already string
    if not session_path:
        # reconstruct conventional path
        session_path = f"/org/freedesktop/portal/desktop/session/{sender}/{TOKEN}s"
        log(f"[create] no session_handle in results; trying conventional {session_path}")
    results["session_path"] = session_path
    log(f"[create] session_path={session_path}")

    # 2) SelectDevices
    sel_opts = {
        "handle_token": dbus.String(TOKEN + "d"),
        "types": dbus.UInt32(DEVICE_TYPES),
        # persist_mode 0 = do not persist (still may prompt)
        "persist_mode": dbus.UInt32(0),
    }
    try:
        req_path = rd.SelectDevices(dbus.ObjectPath(session_path), sel_opts)
        log(f"[select] request={req_path}")
    except Exception as e:
        log(f"[select] CALL FAILED: {e}")
        results["errors"].append(f"select_call:{e}")
        close_session(session_path)
        return 4

    resp = wait_response(str(req_path), "select", timeout=15)
    results["select"] = resp
    if resp is None or resp[0] != 0:
        log(f"[select] failed/timeout/nonzero: {resp}")
        close_session(session_path)
        return 0

    # 2b) ScreenCast.SelectSources on same session (RustDesk does this; needed for combined RD)
    src_opts = {
        "handle_token": dbus.String(TOKEN + "src"),
        "types": dbus.UInt32(1),  # MONITOR
        "multiple": dbus.Boolean(False),
        "cursor_mode": dbus.UInt32(2),  # embedded
    }
    try:
        req_path = sc.SelectSources(dbus.ObjectPath(session_path), src_opts)
        log(f"[select_sources] request={req_path}")
        resp = wait_response(str(req_path), "select_sources", timeout=TIMEOUT_S)
        results["select_sources"] = resp
        if resp is None or resp[0] != 0:
            log(f"[select_sources] failed/timeout/nonzero: {resp} (continuing to Start anyway)")
    except Exception as e:
        log(f"[select_sources] CALL FAILED (continuing): {e}")
        results["errors"].append(f"select_sources:{e}")

    # 3) Start (consent / picker likely here)
    start_opts = {
        "handle_token": dbus.String(TOKEN + "t"),
    }
    try:
        req_path = rd.Start(dbus.ObjectPath(session_path), "", start_opts)
        log(f"[start] request={req_path}  (approve picker on omarchy if shown; timeout {TIMEOUT_S}s)")
    except Exception as e:
        log(f"[start] CALL FAILED: {e}")
        results["errors"].append(f"start_call:{e}")
        close_session(session_path)
        return 5

    resp = wait_response(str(req_path), "start", timeout=TIMEOUT_S)
    results["start"] = resp
    if resp is None:
        log("[start] timeout; cleaning up")
        close_session(session_path)
        return 0
    code, res = resp
    if code == 0:
        log("[start] GRANTED (concurrent session with RustDesk likely)")
    else:
        log(f"[start] NOT granted code={code}")

    # Always close our test session so we do not leave a second controller hanging
    time.sleep(0.5)
    close_session(session_path)
    log("done")
    return 0

if __name__ == "__main__":
    try:
        rc = main()
    except Exception:
        traceback.print_exc()
        rc = 99
    # summary line for the log file
    log(f"SUMMARY create={results['create']} select={results['select']} "
        f"select_sources={results['select_sources']} start={results['start']} "
        f"session={results['session_path']} closed={results['closed']} errors={results['errors']}")
    sys.exit(rc)
