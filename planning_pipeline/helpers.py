"""Helper functions for planning pipeline."""

import re
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
    - thoughts/shared/plans/2025-01-01-feat/00-overview.md
    - thoughts/shared/plans/2025-01-01-feat/01-phase-1-name.md
    """
    if not output:
        return []
    pattern = r'(thoughts/[^\s]+/\d{2}-[^\s]+\.md)'
    return re.findall(pattern, output)
