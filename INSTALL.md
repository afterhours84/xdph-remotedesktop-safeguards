# Install (user-local)

Built from draft PR https://github.com/hyprwm/xdg-desktop-portal-hyprland/pull/426
(commit `0204ffbb`) plus the patches in `patches/`.

This does **not** replace the system xdph package by overwriting `/usr`. Everything
lands under your home directory and can be undone without pacman.

## Dependencies (Arch / Omarchy)

```bash
sudo pacman -S --needed base-devel meson ninja cmake pkgconf git \
  wayland wayland-protocols hyprland-protocols hyprwayland-scanner \
  hyprlang hyprutils libpipewire libdrm mesa libxkbcommon libei \
  sdbus-cpp qt6-base qt6-wayland qt6-tools util-linux-libs
```

## Get the PR tree and apply patches

```bash
git clone https://github.com/hyprwm/xdg-desktop-portal-hyprland.git
cd xdg-desktop-portal-hyprland
# fetch PR #426 head
git fetch origin pull/426/head:pr-426
git checkout 0204ffbb   # or the PR branch tip matching that commit

# Prefer the full tested diff:
git apply /path/to/this/repo/patches/full.diff

# Or apply pieces (see patches/README.md; 01+03 may conflict, full.diff is safer):
# git apply patches/01-safeguards.patch
# git apply patches/02-pollfd-order.patch
# git apply patches/03-lock-notify.patch
# git apply patches/05-scroll-direction.patch
```

## Build

```bash
PREFIX="$HOME/.local/opt/xdph-rd"
meson setup build-omarchy --prefix="$PREFIX" -Dsystemd=enabled
ninja -C build-omarchy
```

Binaries:

- `build-omarchy/src/xdg-desktop-portal-hyprland`
- `build-omarchy/hyprland-share-picker/hyprland-share-picker`

## User-level install

```bash
PREFIX="$HOME/.local/opt/xdph-rd"
mkdir -p "$PREFIX/libexec" "$HOME/.local/bin" \
  "$HOME/.local/share/xdg-desktop-portal/portals" \
  "$HOME/.local/share/dbus-1/services" \
  "$HOME/.config/systemd/user" \
  "$HOME/.config/xdg-desktop-portal"

install -m755 build-omarchy/src/xdg-desktop-portal-hyprland "$PREFIX/libexec/"
install -m755 build-omarchy/hyprland-share-picker/hyprland-share-picker "$HOME/.local/bin/"
# optional lock hook (RustDesk 1.5.0 workaround):
install -m755 /path/to/this/repo/scripts/xdph-rd-on-lock "$HOME/.local/bin/xdph-rd-on-lock"

install -m644 hyprland.portal \
  "$HOME/.local/share/xdg-desktop-portal/portals/hyprland.portal"

cat > "$HOME/.local/share/dbus-1/services/org.freedesktop.impl.portal.desktop.hyprland.service" <<EOT
[D-BUS Service]
Name=org.freedesktop.impl.portal.desktop.hyprland
Exec=$PREFIX/libexec/xdg-desktop-portal-hyprland
SystemdService=xdg-desktop-portal-hyprland.service
EOT

cat > "$HOME/.config/systemd/user/xdg-desktop-portal-hyprland.service" <<EOT
[Unit]
Description=Portal service (Hyprland, user-local RemoteDesktop build)
PartOf=graphical-session.target
After=graphical-session.target

[Service]
Type=dbus
BusName=org.freedesktop.impl.portal.desktop.hyprland
ExecStart=$PREFIX/libexec/xdg-desktop-portal-hyprland
Restart=on-failure
Slice=session.slice

[Install]
WantedBy=graphical-session.target
EOT

cat > "$HOME/.config/xdg-desktop-portal/hyprland-portals.conf" <<'EOT'
[preferred]
default=hyprland;gtk
org.freedesktop.impl.portal.RemoteDesktop=hyprland
org.freedesktop.impl.portal.ScreenCast=hyprland
org.freedesktop.impl.portal.Screenshot=hyprland
EOT

systemctl --user daemon-reload
systemctl --user stop xdg-desktop-portal-hyprland.service xdg-desktop-portal.service || true
systemctl --user start xdg-desktop-portal-hyprland.service
systemctl --user start xdg-desktop-portal.service
```

### Confirm

```bash
systemctl --user status xdg-desktop-portal-hyprland.service --no-pager
busctl --user introspect org.freedesktop.impl.portal.desktop.hyprland \
  /org/freedesktop/portal/desktop org.freedesktop.impl.portal.RemoteDesktop
journalctl --user -u xdg-desktop-portal-hyprland.service -b --no-pager | grep -i remotedesktop
```

You want `[remotedesktop] registered` and `[remotedesktop] watching hyprland_lock_notifier_v1 for lock events` in the journal, and a non-empty `AvailableDeviceTypes` (typically 3 = keyboard|pointer).

## Rollback

```bash
systemctl --user stop xdg-desktop-portal-hyprland.service || true
rm -f "$HOME/.local/opt/xdph-rd/libexec/xdg-desktop-portal-hyprland"
rm -f "$HOME/.local/bin/hyprland-share-picker"
rm -f "$HOME/.local/bin/xdph-rd-on-lock"
rm -f "$HOME/.local/share/xdg-desktop-portal/portals/hyprland.portal"
rm -f "$HOME/.local/share/dbus-1/services/org.freedesktop.impl.portal.desktop.hyprland.service"
rm -f "$HOME/.config/systemd/user/xdg-desktop-portal-hyprland.service"
rm -f "$HOME/.config/xdg-desktop-portal/hyprland-portals.conf"
systemctl --user daemon-reload
systemctl --user restart xdg-desktop-portal.service
# System package xdph (pacman) takes over again if it is still installed.
```

No `/usr` files are modified by this install path.

## Risks

- Replaces the **session** portal backend for Hyprland while the user unit is active. A bug can break ScreenCast/Screenshot/InputCapture as well as RemoteDesktop until you roll back.
- Lock close is not atomic with the compositor lock.
- Closing on lock only drops virtual devices and releases keys/buttons this portal tracked.
