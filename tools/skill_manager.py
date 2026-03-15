#!/usr/bin/env python3
"""
Revvel Skill Manager CLI
A tool to load, search, validate, and manage .skill files.
"""

import os
import yaml
import json
import argparse
import shutil
import sys
import zipfile
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

    def download_skills(
        self,
        output: str,
        name: str = None,
        query: str = None,
        category: str = None,
        tag: str = None,
        as_zip: bool = False,
    ) -> int:
        """Copy matching skill files to *output* (directory) or a ZIP archive.

        Returns the number of files downloaded.
        """
        # Collect matching file paths
        if name:
            # Partial name match across all categories
            matched_paths: List[Path] = []
            for c in self.categories:
                pattern = f"*{name}*.skill.yml"
                matched_paths.extend((self.skills_path / c).glob(pattern))
        else:
            # Use search_skills to filter, then resolve paths
            results = self.search_skills(query=query, category=category, tag=tag)
            matched_paths = [Path(r["path"]) for r in results]

        if not matched_paths:
            print("No skills matched the given criteria.")
            return 0

        output_path = Path(output)

        if as_zip:
            zip_path = output_path if output_path.suffix == ".zip" else output_path.with_suffix(".zip")
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for src in matched_paths:
                    # Preserve category subdirectory to avoid name collisions
                    arcname = f"{src.parent.name}/{src.name}"
                    zf.write(src, arcname)
            print(f"Downloaded {len(matched_paths)} skill(s) to {zip_path}")
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            for src in matched_paths:
                # Preserve category subdirectory to avoid name collisions
                category_dir = output_path / src.parent.name
                category_dir.mkdir(exist_ok=True)
                dest = category_dir / src.name
                shutil.copy2(src, dest)
            print(f"Downloaded {len(matched_paths)} skill(s) to {output_path}/")

        return len(matched_paths)

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

    # Download command
    download_parser = subparsers.add_parser("download", help="Download skill files to a local directory or ZIP archive")
    download_parser.add_argument("output", help="Destination directory or ZIP file path (use --zip for archive)")
    download_parser.add_argument("--name", help="Download skill(s) whose filename contains this string (partial match)")
    download_parser.add_argument("--query", help="Filter by search query")
    download_parser.add_argument("--category", help="Filter by category")
    download_parser.add_argument("--tag", help="Filter by tag")
    download_parser.add_argument("--zip", dest="as_zip", action="store_true", help="Package downloaded skills into a ZIP archive; output path will use .zip extension")

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

    elif args.command == "download":
        manager.download_skills(
            output=args.output,
            name=args.name,
            query=args.query,
            category=args.category,
            tag=args.tag,
            as_zip=args.as_zip,
        )

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
