#!/usr/bin/env python3
"""
flush_notion.py — Отправляет очередь Notion-записей в базу данных
Запускается из Interpreter (где доступен MCP)

Использование:
  python3 flush_notion.py                    # обработать всю очередь
  python3 flush_notion.py --watch            # режим наблюдения
  python3 flush_notion.py --once             # обработать один раз и выйти
"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [flush] %(levelname)s %(message)s")
log = logging.getLogger("flush-notion")

QUEUE_DIR = Path("/tmp/meeting_pipeline/notion_queue")
NOTION_DATA_SOURCE = "e3fb4445-2bd8-47ce-ae00-f8247dd9b145"
PROCESSED_DIR = QUEUE_DIR / "processed"


def process_queue_file(file_path: Path) -> bool:
    """Process one queue file via Notion MCP"""
    try:
        payload = json.loads(file_path.read_text(encoding='utf-8'))
        
        log.info(f"📋 Creating Notion page: {payload.get('pages', [{}])[0].get('properties', {}).get('Meeting Title', 'unknown')}")
        
        # Call Notion MCP
        result = subprocess.run(
            ["interpreter-app", "tools", "notion", "notion-create-pages", "--json",
             json.dumps(payload)],
            capture_output=True, text=True, timeout=30
        )
        
        # Parse result
        try:
            resp = json.loads(result.stdout)
            page_url = resp.get("pages", [{}])[0].get("url", "unknown")
            log.info(f"✅ Created: {page_url}")
            
            # Move to processed
            PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
            file_path.rename(PROCESSED_DIR / file_path.name)
            return True
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            log.error(f"❌ Failed to create: {result.stdout[:300]}")
            # Move to error
            error_dir = QUEUE_DIR / "error"
            error_dir.mkdir(exist_ok=True)
            file_path.rename(error_dir / file_path.name)
            return False
            
    except Exception as e:
        log.error(f"❌ Error processing {file_path.name}: {e}")
        return False


def flush_queue(watch: bool = False, interval: int = 10):
    """Process all pending queue files"""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    if watch:
        log.info(f"👀 Watching for new Notion payloads in {QUEUE_DIR}")
        seen = set()
        
        while True:
            current = set(QUEUE_DIR.glob("*.json"))
            new = current - seen
            
            for f in sorted(new, key=lambda x: x.stat().st_mtime):
                process_queue_file(f)
            
            seen = current
            time.sleep(interval)
    else:
        files = sorted(QUEUE_DIR.glob("*.json"))
        if not files:
            log.info("📭 Queue is empty")
            return
        
        log.info(f"📦 Processing {len(files)} pending items...")
        success = 0
        for f in files:
            if process_queue_file(f):
                success += 1
        
        log.info(f"✅ Done: {success}/{len(files)} processed")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Flush Notion queue")
    parser.add_argument("--watch", "-w", action="store_true", help="Watch mode")
    parser.add_argument("--interval", "-i", type=int, default=10, help="Poll interval")
    parser.add_argument("--once", "-o", action="store_true", help="Process once and exit")
    
    args = parser.parse_args()
    
    if args.watch:
        flush_queue(watch=True, interval=args.interval)
    else:
        flush_queue(watch=False)


if __name__ == '__main__':
    main()
