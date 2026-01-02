"""Integrated orchestrator using beads for state and Claude for LLM calls."""

import json
from pathlib import Path
from typing import Any

from .beads_controller import BeadsController
from .claude_runner import run_claude_sync


class IntegratedOrchestrator:
    """Orchestrator using planning_pipeline and beads for state management."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.bd = BeadsController(project_path)

    def get_project_info(self) -> dict[str, Any]:
        """Detect project info from overview.md via LLM."""
        search_patterns = [
            "thoughts/**/plans/*-overview.md",
            "thoughts/**/plans/*-00-overview.md",
            "thoughts/**/plans/*.md",
            "README.md",
        ]

        content = ""
        for pattern in search_patterns:
            files = list(self.project_path.glob(pattern))
            if files:
                files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                content = files[0].read_text()[:5000]
                break

        if not content:
            return self._default_project_info()

        prompt = f"""Analyze this project documentation and extract:
1. Project name
2. Tech stack (language, framework, database)
3. Brief description (1-2 sentences)

Documentation:
{content}

Return ONLY valid JSON: {{"name": "...", "stack": "...", "description": "..."}}"""

        result = run_claude_sync(prompt=prompt, timeout=60, stream=False)

        if not result["success"]:
            return self._default_project_info()

        try:
            info = json.loads(result["output"])
            info["path"] = self.project_path
            info["model"] = "sonnet"
            return info
        except json.JSONDecodeError:
            return self._default_project_info()

    def _default_project_info(self) -> dict[str, Any]:
        """Return default project info when detection fails."""
        return {
            "name": self.project_path.name,
            "path": self.project_path,
            "stack": "Unknown",
            "description": "",
            "model": "sonnet"
        }

    def get_feature_status(self) -> dict[str, Any]:
        """Get feature status from beads issues."""
        all_result = self.bd.list_issues()
        open_result = self.bd.list_issues(status="open")
        closed_result = self.bd.list_issues(status="closed")

        if not all_result["success"]:
            return {"total": 0, "completed": 0, "remaining": 0, "blocked": 0, "features": []}

        all_issues = all_result.get("data", [])
        open_issues = open_result.get("data", []) if open_result["success"] else []
        closed_issues = closed_result.get("data", []) if closed_result["success"] else []

        # Build set of open issue IDs for dependency checking
        open_ids = {issue["id"] for issue in open_issues}

        # Count blocked: issues with any open dependency
        blocked = 0
        for issue in all_issues:
            for dep in issue.get("dependencies", []):
                if dep.get("depends_on_id") in open_ids:
                    blocked += 1
                    break

        return {
            "total": len(all_issues),
            "completed": len(closed_issues),
            "remaining": len(open_issues),
            "blocked": blocked,
            "features": all_issues
        }

    def get_next_feature(self) -> dict[str, Any] | None:
        """Get next ready issue from beads (no blockers, dependencies met)."""
        result = self.bd._run_bd('ready', '--limit=1')

        if not result["success"]:
            return None

        data = result.get("data")
        if not data:
            return None

        if isinstance(data, list):
            return data[0] if data else None
        elif isinstance(data, dict):
            return data

        return None

    def sync_features_with_git(self) -> int:
        """Sync beads with git remote."""
        result = self.bd.sync()
        return 0 if result["success"] else -1

    def create_phase_issues(
        self,
        phase_files: list[str],
        epic_title: str
    ) -> dict[str, Any]:
        """Create beads issues for phases with priority by order.

        Args:
            phase_files: List of phase file paths
            epic_title: Title for the epic issue

        Returns:
            Dictionary with epic_id and phase_issues list
        """
        # Separate overview from phase files
        actual_phases = []
        for f in phase_files:
            if "overview" not in f.lower() and "-00-" not in f:
                actual_phases.append(f)

        # Create epic
        epic_result = self.bd.create_epic(epic_title)
        epic_id = None
        if epic_result["success"] and isinstance(epic_result["data"], dict):
            epic_id = epic_result["data"].get("id")

        # Create issues with priority = phase order
        phase_issues = []
        for i, phase_file in enumerate(actual_phases, start=1):
            phase_name = Path(phase_file).stem.split('-', 2)[-1].replace('-', ' ').title()

            result = self.bd.create_issue(
                title=f"Phase {i}: {phase_name}",
                issue_type="task",
                priority=i  # Priority matches phase order
            )

            if result["success"] and isinstance(result["data"], dict):
                issue_id = result["data"].get("id")
                phase_issues.append({
                    "phase": i,
                    "file": phase_file,
                    "issue_id": issue_id,
                    "priority": i
                })

        # Link dependencies (each phase depends on previous)
        for i in range(1, len(phase_issues)):
            curr_id = phase_issues[i].get("issue_id")
            prev_id = phase_issues[i - 1].get("issue_id")
            if curr_id and prev_id and isinstance(curr_id, str) and isinstance(prev_id, str):
                self.bd.add_dependency(curr_id, prev_id)

        self.bd.sync()

        return {
            "success": True,
            "epic_id": epic_id,
            "phase_issues": phase_issues
        }

    def log_session(
        self,
        session_id: str,
        action: str,
        result: dict[str, Any]
    ) -> None:
        """Log session activity to .agent/sessions/.

        Args:
            session_id: Unique session identifier
            action: Action performed (e.g., "get_next_feature")
            result: Result dictionary from the action
        """
        from datetime import datetime

        sessions_dir = self.project_path / ".agent" / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "action": action,
            "result": result
        }

        # Write to session-specific file
        session_file = sessions_dir / f"{session_id}.json"

        # Append to existing or create new
        existing = []
        if session_file.exists():
            try:
                existing = json.loads(session_file.read_text())
                if not isinstance(existing, list):
                    existing = [existing]
            except json.JSONDecodeError:
                existing = []

        existing.append(log_entry)
        session_file.write_text(json.dumps(existing, indent=2, default=str))

    def discover_plans(self) -> list["PlanInfo"]:
        """Discover available plans from the thoughts directory.

        Returns:
            List of PlanInfo objects sorted by priority (1=highest).
        """
        search_patterns = [
            "thoughts/**/plans/*-00-overview.md",
            "thoughts/**/plans/*-overview.md",
        ]

        plans = []
        for pattern in search_patterns:
            for file_path in self.project_path.glob(pattern):
                # Extract priority from filename (e.g., 01-feature-x -> priority 1)
                name = file_path.stem
                parts = name.split("-")
                try:
                    priority = int(parts[0]) if parts[0].isdigit() else 50
                except (ValueError, IndexError):
                    priority = 50

                plans.append(PlanInfo(
                    path=str(file_path),
                    name=name,
                    priority=priority
                ))

        # Sort by priority (lower = higher priority)
        plans.sort(key=lambda p: p.priority)
        return plans

    def get_current_feature(self) -> dict[str, Any] | None:
        """Get the currently IN_PROGRESS feature, if any.

        Returns:
            Issue dict with status IN_PROGRESS, or None if no active feature.
        """
        result = self.bd.list_issues(status="in_progress")

        if not result["success"]:
            return None

        data = result.get("data", [])
        if isinstance(data, list) and data:
            return data[0]
        elif isinstance(data, dict):
            return data

        return None


class PlanInfo:
    """Information about a discovered plan."""

    def __init__(self, path: str, name: str, priority: int = 50):
        self.path = path
        self.name = name
        self.priority = priority

    def __repr__(self) -> str:
        return f"PlanInfo(path={self.path!r}, name={self.name!r}, priority={self.priority})"
