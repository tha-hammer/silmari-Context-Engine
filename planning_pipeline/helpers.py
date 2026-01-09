"""Helper functions for planning pipeline."""

import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


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
        file_type: "research" or "plans"

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
