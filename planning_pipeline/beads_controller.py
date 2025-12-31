"""Python wrapper for beads CLI with JSON output support."""

import subprocess
import json
from pathlib import Path
from typing import Any, Optional


class BeadsController:
    """Python wrapper for beads CLI with JSON output support.

    Provides typed methods for common beads operations with
    structured return values.
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self._timeout = 30

    def _run_bd(self, *args, use_json: bool = True) -> dict[str, Any]:
        """Run bd command, optionally with --json flag."""
        cmd = ['bd'] + list(str(a) for a in args)
        if use_json:
            cmd.append('--json')

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=self._timeout
            )

            if result.returncode == 0:
                if use_json:
                    try:
                        return {"success": True, "data": json.loads(result.stdout)}
                    except json.JSONDecodeError:
                        return {"success": True, "data": result.stdout.strip()}
                return {"success": True, "output": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip() or result.stdout.strip()}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {self._timeout}s"}
        except FileNotFoundError:
            return {"success": False, "error": "bd command not found. Is beads installed?"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_issue(
        self,
        title: str,
        issue_type: str = "task",
        priority: int = 2
    ) -> dict[str, Any]:
        """Create a new beads issue."""
        return self._run_bd(
            'create',
            f'--title={title}',
            f'--type={issue_type}',
            f'--priority={priority}'
        )

    def create_epic(self, title: str, priority: int = 2) -> dict[str, Any]:
        """Create an epic issue."""
        return self.create_issue(title, issue_type="epic", priority=priority)

    def list_issues(self, status: Optional[str] = None) -> dict[str, Any]:
        """List beads issues, optionally filtered by status."""
        args = ['list']
        if status:
            args.append(f'--status={status}')
        return self._run_bd(*args)

    def close_issue(self, issue_id: str, reason: Optional[str] = None) -> dict[str, Any]:
        """Close a beads issue."""
        args = ['close', issue_id]
        if reason:
            args.append(f'--reason={reason}')
        return self._run_bd(*args)

    def add_dependency(self, issue_id: str, depends_on: str) -> dict[str, Any]:
        """Add dependency: issue_id depends on depends_on."""
        return self._run_bd('dep', 'add', issue_id, depends_on)

    def sync(self) -> dict[str, Any]:
        """Sync beads with git remote."""
        # sync may not support --json
        return self._run_bd('sync', use_json=False)
