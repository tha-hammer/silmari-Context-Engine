"""Helper functions for planning pipeline."""

import json
import logging
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Union

logger = logging.getLogger(__name__)


def extract_file_path(output: str, file_type: str) -> Optional[str]:
    """Extract file path containing file_type from Claude output.

    Args:
        output: Text output from Claude
        file_type: Substring to match in path (e.g., "research", "plan")

    Returns:
        Matched file path or None if not found
    """
    if not output:
        return None
    pattern = rf'(thoughts/[^\s]+{re.escape(file_type)}[^\s]*\.md)'
    match = re.search(pattern, output, re.IGNORECASE)
    return match.group(1) if match else None


def extract_open_questions(output: str) -> list[str]:
    """Extract open questions from Claude research output.

    Looks for "Open Questions" section and extracts bullet/numbered items
    until the next heading or end of text.
    """
    if not output:
        return []

    questions = []
    in_questions = False
    bullet_pattern = re.compile(r'^[-*]\s*(.+)$')
    numbered_pattern = re.compile(r'^\d+\.\s*(.+)$')

    for line in output.split('\n'):
        stripped = line.strip()

        if 'open question' in stripped.lower():
            in_questions = True
            continue

        if in_questions:
            if stripped.startswith('#'):
                break

            for pattern in (bullet_pattern, numbered_pattern):
                match = pattern.match(stripped)
                if match:
                    questions.append(match.group(1).strip())
                    break

    return questions


def extract_phase_files(output: str) -> list[str]:
    """Extract phase file paths from Claude output.

    Matches paths like:
    - thoughts/searchable/plans/2025-01-01-feat/00-overview.md
    - thoughts/searchable/plans/2025-01-01-feat/01-phase-1-name.md
    """
    if not output:
        return []
    pattern = r'(thoughts/[^\s]+/\d{2}-[^\s]+\.md)'
    return re.findall(pattern, output)


def resolve_file_path(
    project_path: Path,
    path_input: str,
    file_type: str
) -> Optional[Path]:
    """Resolve a file path from various input formats.

    Accepts:
    - Absolute paths: /home/user/project/thoughts/searchable/research/file.md
    - Relative paths: thoughts/searchable/research/file.md
    - Just filename: 2026-01-02-my-research.md
    - Partial filename: my-research.md (fuzzy match)

    Args:
        project_path: Root project directory
        path_input: User-provided path string
        file_type: "research", "plans", or "hierarchy" (REQ_005.4)

    Returns:
        Resolved absolute Path or None if not found
    """
    if not path_input:
        return None

    input_path = Path(path_input).expanduser()

    # Case 1: Absolute path exists
    if input_path.is_absolute() and input_path.exists():
        return input_path

    # Case 2: Relative path from project root
    relative_from_project = project_path / input_path
    if relative_from_project.exists():
        return relative_from_project.resolve()

    # Case 3: Just a filename - search in thoughts directories
    thoughts_dir = project_path / "thoughts"

    # For hierarchy files, search in plans directories for .json files
    if file_type == "hierarchy":
        search_dirs = [
            thoughts_dir / "searchable" / "shared" / "plans",
            thoughts_dir / "shared" / "plans",
        ]

        filename = input_path.name

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Search for hierarchy files in plan subdirectories
            for plan_subdir in search_dir.iterdir():
                if not plan_subdir.is_dir():
                    continue

                # Check if the path contains this subdirectory name
                if str(input_path).startswith(plan_subdir.name) or \
                   plan_subdir.name in str(input_path):
                    # Look for the hierarchy file in this subdirectory
                    hierarchy_path = plan_subdir / filename
                    if hierarchy_path.exists():
                        return hierarchy_path.resolve()

                # Also search for exact filename match in subdirectories
                exact_match = plan_subdir / filename
                if exact_match.exists():
                    return exact_match.resolve()

        return None

    # Original behavior for research/plans
    search_dirs = [
        thoughts_dir / "searchable" / "shared" / file_type,
        thoughts_dir / "shared" / file_type,
    ]

    filename = input_path.name

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        # Exact filename match
        exact_match = search_dir / filename
        if exact_match.exists():
            return exact_match.resolve()

        # Fuzzy match: filename is a suffix of an existing file
        for f in search_dir.glob("*.md"):
            if f.name == filename or f.name.endswith(f"-{filename}"):
                return f.resolve()

            # Match if input is a substring of the filename (after date prefix)
            if len(f.stem) >= 10:
                name_part = f.stem[11:]  # Skip YYYY-MM-DD-
                if filename.replace(".md", "") in name_part:
                    return f.resolve()

    return None


def discover_thoughts_files(
    project_path: Path,
    file_type: str,
    days_back: int = 7
) -> list[Path]:
    """Discover research or plan files from thoughts directory.

    Args:
        project_path: Root project directory
        file_type: "research" or "plans"
        days_back: How many days back to search (0 = today only)

    Returns:
        List of matching file paths sorted alphabetically by filename
    """
    thoughts_dir = Path(project_path) / "thoughts"

    # Try both direct and searchable paths
    search_dirs = [
        thoughts_dir / "shared" / file_type,
        thoughts_dir / "searchable" / "shared" / file_type,
    ]

    search_dir = None
    for d in search_dirs:
        if d.exists():
            search_dir = d
            break

    if search_dir is None:
        return []

    cutoff_date = datetime.now() - timedelta(days=days_back)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d')

    files = []
    for f in search_dir.glob("*.md"):
        # Files are named YYYY-MM-DD-description.md
        if len(f.stem) >= 10:
            date_part = f.stem[:10]
            if date_part >= cutoff_str:
                files.append(f)

    # Sort alphabetically by filename
    return sorted(files, key=lambda f: f.name)


# ==============================================================================
# REQ_005: Auto-detection and file resolution functions
# ==============================================================================

# Hierarchy file names to search for, in priority order
HIERARCHY_FILE_NAMES = [
    "requirement_hierarchy.json",
    "requirements_hierarchy.json",
    "hierarchy.json",
]


def detect_file_type(path: Union[Path, str]) -> str:
    """Detect the type of a file based on its extension.

    REQ_005.1: Returns file type based on extension.

    Args:
        path: Path to the file (Path object or string)

    Returns:
        'markdown' for .md files (case-insensitive)
        'json' for .json files (case-insensitive)
        'unknown' for other extensions

    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path = Path(path)

    # Validate file existence
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get extension and normalize to lowercase
    extension = file_path.suffix.lower()

    if extension == ".md":
        return "markdown"
    elif extension == ".json":
        return "json"
    else:
        return "unknown"


def _is_valid_hierarchy_json(file_path: Path) -> bool:
    """Check if a JSON file is a valid RequirementHierarchy structure.

    Args:
        file_path: Path to the JSON file

    Returns:
        True if the JSON is valid and has a 'requirements' field, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Check for required 'requirements' field
        return isinstance(data, dict) and "requirements" in data
    except (json.JSONDecodeError, IOError, OSError):
        return False


def find_sibling_hierarchy(plan_path: Path) -> Optional[Path]:
    """Find a sibling hierarchy JSON file for a given markdown plan file.

    REQ_005.2: Search for hierarchy JSON files in the same directory.

    Searches for these files in order of preference:
    - requirement_hierarchy.json
    - requirements_hierarchy.json
    - hierarchy.json

    Args:
        plan_path: Path to a markdown plan file (e.g., 00-overview.md)

    Returns:
        Absolute Path to the hierarchy JSON file, or None if not found
    """
    plan_dir = plan_path.parent

    for hierarchy_name in HIERARCHY_FILE_NAMES:
        hierarchy_path = plan_dir / hierarchy_name

        if hierarchy_path.exists():
            logger.debug(f"Found hierarchy file candidate: {hierarchy_path}")

            # Validate the JSON structure
            if _is_valid_hierarchy_json(hierarchy_path):
                logger.info(f"Valid hierarchy file found: {hierarchy_path}")
                return hierarchy_path.resolve()
            else:
                logger.debug(f"Invalid hierarchy structure in: {hierarchy_path}")

    logger.debug(f"No valid hierarchy file found in: {plan_dir}")
    return None


def is_sibling_pair_valid(dir_path: Path) -> bool:
    """Check if a directory contains a valid sibling pair of overview and hierarchy.

    REQ_005.5: Validates that both requirement_hierarchy.json and 00-overview.md
    exist in the directory.

    Args:
        dir_path: Path to the directory to check

    Returns:
        True if both files exist and are valid, False otherwise
    """
    # Check directory exists
    if not dir_path.exists() or not dir_path.is_dir():
        return False

    # Check for 00-overview.md
    overview_path = dir_path / "00-overview.md"
    if not overview_path.exists():
        return False

    # Check for any valid hierarchy file
    for hierarchy_name in HIERARCHY_FILE_NAMES:
        hierarchy_path = dir_path / hierarchy_name
        if hierarchy_path.exists():
            if _is_valid_hierarchy_json(hierarchy_path):
                return True

    return False
