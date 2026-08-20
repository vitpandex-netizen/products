#!/usr/bin/env python3
"""
auto_upload.py — Скрипты для автоматической выгрузки записей из Zoom/Meet/Teams

Настройка:

## Zoom
1. Настройки → Запись → Автоматическая запись в облако
2. Настройки → Запись → Автоматическая загрузка в корзину облака
3. Или используй Zapier/Make для автоэкспорта в Dropbox/Google Drive
4. Установи Dropbox/Google Drive Desktop → синхронизация на /Volumes/External/recordings/

## Google Meet
1. Используй расширение Meet Transcript (или Tactiq) для экспорта транскриптов
2. Или через Google Drive → скачивание через rclone

## Microsoft Teams
1. Teams Admin → Meeting Recording → Auto-export to SharePoint
2. SharePoint → rclone sync → локальная папка
3. Или через Microsoft Power Automate → Dropbox → локальная синхронизация

## Универсальный способ: rclone
Установка: brew install rclone
Настройка: rclone config
Синхронизация: rclone sync remote:meetings /Volumes/External/recordings/ --progress
"""

import argparse
import subprocess
import sys
from pathlib import Path


def setup_rclone_auto_sync(source: str, dest: str, interval_minutes: int = 15):
    """Setup launchd for rclone auto-sync"""
    label = "com.user.rclone-meetings-sync"
    plist_path = Path.home() / f"Library/LaunchAgents/{label}.plist"
    
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/rclone</string>
        <string>sync</string>
        <string>{source}</string>
        <string>{dest}</string>
        <string>--progress</string>
    </array>
    <key>StartInterval</key>
    <integer>{interval_minutes * 60}</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/rclone-meetings.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/rclone-meetings.err</string>
</dict>
</plist>
"""
    plist_path.write_text(plist_content)
    subprocess.run(["launchctl", "load", str(plist_path)])
    print(f"✅ rclone auto-sync installed: {source} → {dest} (every {interval_minutes} min)")


def main():
    parser = argparse.ArgumentParser(description="Настройка авто-выгрузки записей встреч")
    subparsers = parser.add_subparsers(dest="command")
    
    rclone_parser = subparsers.add_parser("rclone", help="Настроить rclone sync")
    rclone_parser.add_argument("--source", required=True, help="rclone remote:path")
    rclone_parser.add_argument("--dest", default="/Volumes/External/recordings", help="Local destination")
    rclone_parser.add_argument("--interval", type=int, default=15, help="Sync interval (minutes)")
    
    args = parser.parse_args()
    
    if args.command == "rclone":
        Path(args.dest).mkdir(parents=True, exist_ok=True)
        setup_rclone_auto_sync(args.source, args.dest, args.interval)
    else:
        parser.print_help()
        print("\nПримеры:")
        print("  python3 auto_upload.py rclone --source gdrive:Meetings --dest /Volumes/External/recordings")
        print("  python3 auto_upload.py rclone --source dropbox:meetings --interval 10")


if __name__ == '__main__':
    main()
