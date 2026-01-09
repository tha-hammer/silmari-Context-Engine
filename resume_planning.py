#!/bin/bash
# Resume pipeline from planning step

from pathlib import Path
from planning_pipeline import step_planning, step_phase_decomposition, step_beads_integration

project_path = Path.cwd()
research_path = "/thoughts/searchable/research/2026-01-01-baml-integration-research.md"  # Update this

# Step 1: Planning
plan = step_planning(project_path, research_path)
print(f"Planning: {'✓' if plan['success'] else '✗'} {plan.get('plan_path', plan.get('error'))}")

# Step 2: Decomposition (only if planning succeeded)
if plan['success']:
    phases = step_phase_decomposition(project_path, plan['plan_path'])
    print(f"Decomposition: {'✓' if phases['success'] else '✗'} {len(phases.get('phase_files', []))} files")
    
    # Step 3: Beads (only if decomposition succeeded)
    if phases['success']:
        beads = step_beads_integration(project_path, phases['phase_files'], 'My Epic')
        print(f"Beads: {'✓' if beads['success'] else '✗'} Epic: {beads.get('epic_id')}")

