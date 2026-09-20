#!/usr/bin/env python3
"""
pre_impl_checklist.py — Pre-Implementation Protocol Check
Validates that the 5-stage enterprise protocol is followed before code begins.

Usage: python3 pre_impl_checklist.py <project-dir> [--verbose]
"""

import argparse
import json
import os
import sys
from pathlib import Path


PROTOCOL_FILE = Path(__file__).parent.parent / "docs" / "enterprise-agentic-protocol.md"
REQUIRED_MARKERS = {
    "spec": ["SPEC.md", "specification.md", "tech_contract.md"],
    "tests_red": ["test_red.md", "failing_tests.md", ".worktrees/*/test_*.py"],
    "worktree": [".worktrees/"],
    "interview_notes": ["interview.md", "requirements.md"],
}


def check_file_exists(path: Path, patterns: list[str]) -> bool:
    """Check if any of the pattern files exist."""
    for pattern in patterns:
        if "*" in pattern:
            # Glob pattern
            matches = list(path.glob(pattern))
            if matches:
                return True
        else:
            if (path / pattern).exists():
                return True
    return False


def validate_protocol(project_dir: str, verbose: bool = False) -> dict:
    """Validate protocol compliance for a project directory."""
    base = Path(project_dir)
    results = {
        "project": project_dir,
        "compliant": True,
        "checks": {},
        "warnings": [],
        "errors": [],
    }

    # 1. Spec check
    spec_found = check_file_exists(base, REQUIRED_MARKERS["spec"])
    results["checks"]["spec"] = spec_found
    if not spec_found:
        results["errors"].append("❌ SPEC not found — must write Technical Contract before code")
        results["compliant"] = False
    elif verbose:
        results["warnings"].append("✅ Spec found")

    # 2. Interview notes check
    interview_found = check_file_exists(base, REQUIRED_MARKERS["interview_notes"])
    results["checks"]["interview"] = interview_found
    if not interview_found:
        results["warnings"].append("⚠️ No interview notes (recommended for complex tasks)")

    # 3. Worktree check
    worktree_found = any((base / p).exists() for p in [".worktrees"])
    results["checks"]["worktree"] = worktree_found
    if not worktree_found:
        results["warnings"].append("⚠️ No worktree directory (use for parallel tasks)")

    # 4. Test files check
    test_files = list(base.rglob("test_*.py")) + list(base.rglob("*_test.py"))
    results["checks"]["tests_exist"] = len(test_files) > 0
    if len(test_files) > 0:
        results["warnings"].append(f"✅ Found {len(test_files)} test file(s)")
    else:
        results["warnings"].append("⚠️ No test files found (TDD-Lock required)")

    return results


def main():
    parser = argparse.ArgumentParser(description="Pre-Implementation Protocol Check")
    parser.add_argument("project", help="Project directory to validate")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    if not os.path.isdir(args.project):
        print(f"ERROR: Directory not found: {args.project}")
        sys.exit(1)

    result = validate_protocol(args.project, args.verbose)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result["compliant"]:
        print("\n❌ PROTOCOL VIOLATION — Fix before proceeding:")
        for err in result["errors"]:
            print(f"  {err}")
        sys.exit(1)
    elif result["warnings"]:
        print("\n⚠️  Protocol warnings (fix recommended):")
        for w in result["warnings"]:
            print(f"  {w}")
        sys.exit(0)
    else:
        print("\n✅ Protocol compliant")
        sys.exit(0)


if __name__ == "__main__":
    main()
