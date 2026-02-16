# Revvel Skills Vault

A production-ready repository containing every skill needed for Revvel AI agents.

## Structure
- `/skills/custom/` - 58 custom-built expert skills (Forensics, Medical, Legal, etc.)
- `/skills/bundled/` - 53 core OpenClaw skills
- `/skills/community/` - 9,580 community-contributed skills from ClawHub
- `/tools/` - Skill loader/manager CLI
- `/spec/` - The `.skill` file format specification

## Usage
The `skill_manager.py` tool in `/tools` allows you to search, validate, and load skills.

```bash
# Search for a skill
python3 tools/skill_manager.py search "forensics"

# Show skill implementation
python3 tools/skill_manager.py show "cold_case_analysis"
```

## Total Skills: 9691
