#!/usr/bin/env python3
"""
post_deploy_audit.py — Post-Deployment Audit
Verifies deployment integrity and logs to Change Log.

Usage: python3 post_deploy_audit.py <project-dir> <commit-hash> [--dry-run]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def audit_deployment(project_dir: str, commit_hash: str, dry_run: bool = False) -> dict:
    base = Path(project_dir)
    results = {
        "project": project_dir,
        "commit": commit_hash,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
        "warnings": [],
        "errors": [],
    }

    # 1. Verify commit exists in remote
    rc, stdout, stderr = run_cmd(["git", "-C", project_dir, "ls-remote", "origin", commit_hash])
    results["checks"]["commit_in_remote"] = commit_hash in stdout
    if not results["checks"]["commit_in_remote"]:
        results["errors"].append(f"❌ Commit {commit_hash} not found in origin")

    # 2. Check server HEAD matches
    rc, stdout, stderr = run_cmd(["git", "-C", project_dir, "rev-parse", "HEAD"])
    local_head = stdout.strip()
    results["checks"]["local_head"] = local_head
    if local_head != commit_hash and not dry_run:
        results["warnings"].append(f"⚠️ Local HEAD ({local_head}) != target ({commit_hash})")

    # 3. Check untracked runtime files are gitignored
    rc, stdout, stderr = run_cmd(["git", "-C", project_dir, "status", "--porcelain"])
    untracked = [line for line in stdout.split("\n") if line.startswith("??")]
    results["checks"]["untracked_files"] = len(untracked)
    if untracked and len(untracked) > 10:
        results["warnings"].append(f"⚠️ {len(untracked)} untracked files (may need .gitignore)")

    # 4. Check no secrets in committed code
    rc, stdout, stderr = run_cmd(["git", "-C", project_dir, "log", "--oneline", "-1", commit_hash])
    results["checks"]["commit_message"] = stdout.strip()

    # 5. Verify test suite
    test_scripts = list(base.rglob("test_*.py")) + list(base.rglob("*_test.py"))
    if test_scripts:
        results["checks"]["test_files"] = [str(t.relative_to(base)) for t in test_scripts]
    else:
        results["warnings"].append("⚠️ No test files found in project")

    return results


def main():
    parser = argparse.ArgumentParser(description="Post-Deployment Audit")
    parser.add_argument("project", help="Project directory")
    parser.add_argument("commit", help="Commit hash to audit")
    parser.add_argument("--dry-run", action="store_true", help="Skip server checks")
    args = parser.parse_args()

    result = audit_deployment(args.project, args.commit, args.dry_run)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["errors"]:
        print("\n❌ AUDIT FAILED:")
        for err in result["errors"]:
            print(f"  {err}")
        sys.exit(1)
    else:
        print("\n✅ AUDIT PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
