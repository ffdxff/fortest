#!/bin/sh
set -e

echo "[INFO] Auto Japanese subtitle starting..."

# ---------- 自动判断 Ubuntu rootfs ----------
if [ -d /ubuntu/bin ]; then
    UB=/ubuntu
elif [ -d /root/ubuntu/bin ]; then
    UB=/root/ubuntu
else
    echo "[ERROR] Ubuntu rootfs not found"
    exit 1
fi
echo "[INFO] Ubuntu rootfs at $UB"

# ---------- bind hostroot ----------
mkdir -p "$UB/hostroot"
mountpoint -q "$UB/hostroot" || mount --bind /root "$UB/hostroot"

# ---------- bind system dirs ----------
mountpoint -q "$UB/dev"  || mount --bind /dev "$UB/dev"
mountpoint -q "$UB/proc" || mount -t proc proc "$UB/proc"
mountpoint -q "$UB/sys"  || mount -t sysfs sys "$UB/sys"

# ---------- 启动 GTK viewer ----------
export LANG=ja_JP.UTF-8
export LC_CTYPE=ja_JP.UTF-8

if ! pgrep -f jp-text-viewer >/dev/null; then
    jp-text-viewer &
    sleep 1
fi

# ---------- 启动实时字幕 ----------
echo "[INFO] Starting realtime VOSK subtitle..."

chroot "$UB" /bin/bash -c "
export LANG=ja_JP.UTF-8
python3 /root/test_microphone_jp_to_gtk.py --partial --keep-last-final -m ja
"

