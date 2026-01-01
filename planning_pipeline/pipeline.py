"""Main planning pipeline with interactive checkpoints."""

from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from .beads_controller import BeadsController
from .steps import step_research, step_planning, step_phase_decomposition, step_beads_integration, step_memory_sync
from .checkpoints import interactive_checkpoint_research, interactive_checkpoint_plan


class PlanningPipeline:
    """Interactive planning pipeline with deterministic control.

    Orchestrates 5 steps:
    1. Research - Analyze codebase and create research document
    2. Planning - Create implementation plan from research
    3. Phase Decomposition - Split plan into phase files
    4. Beads Integration - Create issues and dependencies
    5. Memory Capture - Record session metadata
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.beads = BeadsController(project_path)

    def run(
        self,
        research_prompt: str,
        ticket_id: Optional[str] = None,
        auto_approve: bool = False
    ) -> dict[str, Any]:
        """Run the complete planning pipeline.

        Args:
            research_prompt: The initial research question or topic
            ticket_id: Optional ticket ID for tracking
            auto_approve: If True, skip interactive checkpoints

        Returns:
            Dictionary with keys:
            - success: bool
            - steps: dict with results from each step
            - plan_dir: path to plan directory
            - epic_id: ID of created epic
        """
        results = {
            "started": datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "steps": {}
        }

        # Step 1: Research (may loop on revise/restart)
        current_prompt = research_prompt
        additional_context = ""

        while True:
            print("\n" + "="*60)
            print("STEP 1/5: RESEARCH PHASE")
            print("="*60)

            research = step_research(self.project_path, current_prompt)
            results["steps"]["research"] = research

            if not research["success"]:
                results["success"] = False
                results["failed_at"] = "research"
                return results

            if auto_approve:
                break

            checkpoint = interactive_checkpoint_research(research)
            action = checkpoint.get("action", "continue")

            if action == "continue":
                additional_context = "\n".join(checkpoint.get("answers", []))
                break
            elif action == "revise":
                # Add revision context to prompt and re-run
                revision = checkpoint.get("revision_context", "")
                if revision:
                    current_prompt = f"{current_prompt}\n\nAdditional context:\n{revision}"
                print("\nRe-running research with additional context...")
            elif action == "restart":
                # Collect new prompt
                print("\nEnter new research prompt (empty line to finish):")
                lines = []
                while True:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                new_prompt = "\n".join(lines)
                if new_prompt.strip():
                    current_prompt = new_prompt
                print("\nRestarting research with new prompt...")
            else:  # action == "exit"
                results["success"] = False
                results["stopped_at"] = "research"
                return results

        # Memory sync between research and planning
        print("\n" + "="*60)
        print("MEMORY SYNC: Recording research & clearing context")
        print("="*60)

        session_id = f"research-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        memory_result = step_memory_sync(
            self.project_path,
            research["research_path"],
            session_id
        )
        results["steps"]["memory_sync"] = memory_result

        if memory_result.get("episode_recorded"):
            print("  ✓ Episodic memory recorded")
        if memory_result.get("context_compiled"):
            print("  ✓ Working context compiled")
        if memory_result.get("context_cleared"):
            print("  ✓ Claude context cleared")

        # Step 2: Planning (may loop on feedback)
        while True:
            print("\n" + "="*60)
            print("STEP 2/5: PLANNING PHASE")
            print("="*60)

            planning = step_planning(
                self.project_path,
                research["research_path"],
                additional_context
            )
            results["steps"]["planning"] = planning

            if not planning["success"]:
                results["success"] = False
                results["failed_at"] = "planning"
                return results

            if auto_approve:
                break
            else:
                plan_checkpoint = interactive_checkpoint_plan(planning)
                if plan_checkpoint["continue"]:
                    break
                additional_context = plan_checkpoint["feedback"]
                print("\nRe-running planning with feedback...")

        # Step 3: Phase Decomposition
        print("\n" + "="*60)
        print("STEP 3/5: PHASE DECOMPOSITION")
        print("="*60)

        decomposition = step_phase_decomposition(
            self.project_path,
            planning["plan_path"]
        )
        results["steps"]["decomposition"] = decomposition

        if not decomposition["success"]:
            results["success"] = False
            results["failed_at"] = "decomposition"
            return results

        print(f"\nCreated {len(decomposition['phase_files'])} phase files")

        # Step 4: Beads Integration
        print("\n" + "="*60)
        print("STEP 4/5: BEADS INTEGRATION")
        print("="*60)

        epic_title = f"Plan: {ticket_id}" if ticket_id else f"Plan: {datetime.now().strftime('%Y-%m-%d')}"
        beads = step_beads_integration(
            self.project_path,
            decomposition["phase_files"],
            epic_title
        )
        results["steps"]["beads"] = beads

        if beads["success"]:
            print(f"\nCreated epic: {beads.get('epic_id')}")
            print(f"Created {len(beads.get('phase_issues', []))} phase issues")

        # Step 5: Memory Capture (placeholder)
        print("\n" + "="*60)
        print("STEP 5/5: MEMORY CAPTURE")
        print("="*60)
        print("Memory capture: using existing hooks")
        results["steps"]["memory"] = {"success": True}

        # Complete
        results["success"] = True
        results["completed"] = datetime.now().isoformat()
        results["plan_dir"] = str(Path(decomposition["phase_files"][0]).parent) if decomposition["phase_files"] else None
        results["epic_id"] = beads.get("epic_id")

        print("\n" + "="*60)
        print("PIPELINE COMPLETE")
        print("="*60)
        print(f"\nPlan directory: {results['plan_dir']}")
        print(f"Epic ID: {results['epic_id']}")

        return results
