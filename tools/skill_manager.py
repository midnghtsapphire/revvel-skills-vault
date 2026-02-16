#!/usr/bin/env python3
"""
Revvel Skill Manager CLI
A tool to load, search, validate, and manage .skill files.
"""

import os
import yaml
import json
import argparse
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

class SkillManager:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.skills_path = self.vault_path / "skills"
        self.categories = ["custom", "bundled", "community"]

    def _load_skill_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix == '.json':
                    return json.load(f)
                else:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def validate_skill(self, skill_data: Dict[str, Any]) -> List[str]:
        errors = []
        required_fields = ["name", "title", "version", "description", "metadata", "implementation", "schema_version"]
        for field in required_fields:
            if field not in skill_data:
                errors.append(f"Missing required field: {field}")
        
        if "metadata" in skill_data:
            meta = skill_data["metadata"]
            for field in ["author", "category", "tags"]:
                if field not in meta:
                    errors.append(f"Missing metadata field: {field}")
        
        if "implementation" in skill_data:
            impl = skill_data["implementation"]
            for field in ["type", "language", "content"]:
                if field not in impl:
                    errors.append(f"Missing implementation field: {field}")
        
        return errors

    def search_skills(self, query: str = None, category: str = None, tag: str = None) -> List[Dict[str, Any]]:
        results = []
        search_dirs = [self.skills_path / c for c in self.categories if (self.skills_path / c).exists()]
        
        for s_dir in search_dirs:
            for file_path in s_dir.glob("*.skill.yml"):
                skill = self._load_skill_file(file_path)
                if not skill:
                    continue
                
                match = True
                if category and skill.get("metadata", {}).get("category", "").lower() != category.lower():
                    match = False
                if tag and tag.lower() not in [t.lower() for t in skill.get("metadata", {}).get("tags", [])]:
                    match = False
                if query:
                    q = query.lower()
                    content_to_search = f"{skill.get('name', '')} {skill.get('title', '')} {skill.get('description', '')}".lower()
                    if q not in content_to_search:
                        match = False
                
                if match:
                    results.append({
                        "name": skill.get("name"),
                        "title": skill.get("title"),
                        "category": skill.get("metadata", {}).get("category"),
                        "author": skill.get("metadata", {}).get("author"),
                        "path": str(file_path)
                    })
        return results

    def get_skill_content(self, skill_name: str) -> Optional[str]:
        # Search in all subdirs
        for c in self.categories:
            pattern = f"*{skill_name}.skill.yml"
            matches = list((self.skills_path / c).glob(pattern))
            if matches:
                skill = self._load_skill_file(matches[0])
                if skill:
                    return skill.get("implementation", {}).get("content")
        return None

def main():
    parser = argparse.ArgumentParser(description="Revvel Skill Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for skills")
    search_parser.add_argument("query", nargs="?", help="Search query")
    search_parser.add_argument("--category", help="Filter by category")
    search_parser.add_argument("--tag", help="Filter by tag")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show skill content")
    show_parser.add_argument("name", help="Skill name")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a skill file")
    validate_parser.add_argument("path", help="Path to .skill file")

    args = parser.parse_args()
    
    # Default vault path (relative to this tool)
    vault_path = Path(__file__).parent.parent
    manager = SkillManager(str(vault_path))

    if args.command == "search":
        results = manager.search_skills(args.query, args.category, args.tag)
        print(f"Found {len(results)} skills:")
        for r in results[:20]:
            print(f"- {r['title']} ({r['name']}) by {r['author']} [{r['category']}]")
        if len(results) > 20:
            print(f"... and {len(results) - 20} more.")

    elif args.command == "show":
        content = manager.get_skill_content(args.name)
        if content:
            print(content)
        else:
            print(f"Skill '{args.name}' not found.")

    elif args.command == "validate":
        skill = manager._load_skill_file(Path(args.path))
        if skill:
            errors = manager.validate_skill(skill)
            if errors:
                print("Validation failed:")
                for e in errors:
                    print(f"  - {e}")
            else:
                print("Skill is valid.")
        else:
            print("Could not load file.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
