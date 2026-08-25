#!/usr/bin/env python3
"""
Forge Diary Automation Helper
Creates daily raw chronicle markdown files and synchronizes the master FORGE_DIARY.md navigation list.
"""

import os
import re
import sys
from datetime import datetime

DIARY_TEMPLATE = """# FORGE — {date}

## Daily Summary

## User Directives / Requirements

## Work Performed

## Architecture / Structure Changes

## Files Created

## Files Modified

## Files Deleted

## Tools & Subsystems

## Security Changes

## CLI / UI Changes

## Tests Performed & Test Results

## Bugs / Errors Discovered
### Bug #XX: [Title]
- Symptoms:
- Root Cause:
- Fix:
- Commit:
- Verification:

## Important Decisions

## Incidents / Misconfigurations

## Corrections to Earlier Information

## Git Commits

## Current End-of-Day State

## Next Planned Work
"""

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    diary_dir = "diary"
    diary_file = os.path.join(diary_dir, f"{today}.md")
    master_file = "FORGE_DIARY.md"

    if not os.path.exists(diary_dir):
        os.makedirs(diary_dir)
        print(f"Created directory: {diary_dir}")

    if not os.path.exists(diary_file):
        with open(diary_file, "w", encoding="utf-8") as f:
            f.write(DIARY_TEMPLATE.format(date=today))
        print(f"Created daily diary file: {diary_file}")
    else:
        print(f"Diary entry for today ({today}) already exists: {diary_file}")

    # Synchronize master index navigation
    if os.path.exists(master_file):
        with open(master_file, "r", encoding="utf-8") as f:
            content = f.read()

        nav_entry = f"- [{today}](diary/{today}.md)"
        if nav_entry not in content:
            # Pattern matching navigation list
            pattern = r"(## Diary Navigation\s*\n\s*A chronological list.*?\n\n)([\s\S]*?)(?=\n---)"
            match = re.search(pattern, content)
            if match:
                existing_entries = match.group(2).strip()
                updated_entries = f"{existing_entries}\n{nav_entry}".strip()
                new_nav_block = f"{match.group(1)}{updated_entries}\n\n"
                new_content = content[:match.start()] + new_nav_block + content[match.end():]
                with open(master_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {master_file} navigation with entry for {today}.")
            else:
                print(f"Warning: Could not automatically locate Diary Navigation section in {master_file}.")
        else:
            print(f"{master_file} already contains navigation link for {today}.")
    else:
        print(f"Warning: Master file {master_file} not found.")

    print("\n[Security Reminder] Ensure no secrets, tokens, or .env entries are placed in diary files.")

if __name__ == "__main__":
    main()
