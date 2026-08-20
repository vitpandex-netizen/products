#!/usr/bin/env python3
"""
watch_service.py — Наблюдает за папкой и автоматически обрабатывает новые аудиофайлы

Использование:
  python3 watch_service.py --dir /Volumes/External/recordings/ [--meeting-service http://localhost:8001]
  python3 watch_service.py --dir ~/Downloads/zoom-recordings/ --recursive
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [watch] %(levelname)s %(message)s")
log = logging.getLogger("watch-service")

AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.webm', '.mp4', '.m4v', '.mov', '.avi', '.mkv'}
MEETING_SERVICE_URL = "http://localhost:8001"


def process_file(file_path: Path, service_url: str):
    """Send file to meeting-pipeline service"""
    log.info(f"Processing new file: {file_path.name}")
    
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", f"{service_url}/process-audio",
         "-H", "Content-Type: application/json",
         "-d", json.dumps({
             "audio_path": str(file_path.resolve()),
             "title": file_path.stem,
         })],
        capture_output=True, text=True, timeout=900
    )
    
    try:
        resp = json.loads(result.stdout)
        if resp.get("status") == "ok":
            log.info(f"✅ {file_path.name} → {resp.get('notion_url', 'Notion')}")
        else:
            log.error(f"❌ {file_path.name}: {resp.get('message', result.stdout[:200])}")
    except json.JSONDecodeError:
        log.error(f"❌ {file_path.name}: {result.stdout[:200]}")


def watch_directory(watch_dir: Path, service_url: str, recursive: bool = False, 
                    poll_interval: int = 10):
    """Watch a directory for new files and process them automatically"""
    log.info(f"👀 Watching {watch_dir} (recursive={recursive}, poll={poll_interval}s)")
    log.info(f"   Service: {service_url}")
    
    seen = set()
    
    while True:
        # Find all audio files
        if recursive:
            current = {f for f in watch_dir.rglob("*") if f.suffix.lower() in AUDIO_EXTENSIONS and f.is_file()}
        else:
            current = {f for f in watch_dir.iterdir() if f.suffix.lower() in AUDIO_EXTENSIONS and f.is_file()}
        
        new = current - seen
        
        # Process newest first (by mtime)
        for f in sorted(new, key=lambda x: x.stat().st_mtime, reverse=True):
            # Wait a bit to ensure file is fully written
            size_before = f.stat().st_size
            time.sleep(3)
            size_after = f.stat().st_size
            
            if size_before == size_after:
                process_file(f, service_url)
                seen.add(f)
            else:
                log.info(f"  {f.name} still being written, will retry")
        
        seen = current
        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Watch folder for new audio files → auto-process")
    parser.add_argument("--dir", "-d", required=True, help="Directory to watch")
    parser.add_argument("--service", "-s", default=MEETING_SERVICE_URL, help="Meeting pipeline URL")
    parser.add_argument("--recursive", "-r", action="store_true", help="Watch subdirectories")
    parser.add_argument("--interval", "-i", type=int, default=10, help="Poll interval (seconds)")
    
    args = parser.parse_args()
    watch_dir = Path(args.dir)
    
    if not watch_dir.is_dir():
        print(f"❌ Directory not found: {watch_dir}")
        sys.exit(1)
    
    watch_directory(watch_dir, args.service, args.recursive, args.interval)


if __name__ == '__main__':
    main()
