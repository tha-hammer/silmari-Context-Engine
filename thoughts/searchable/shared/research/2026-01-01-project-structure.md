---
date: 2026-01-01T11:33:37-05:00
researcher: maceo
git_commit: ba5ab989c06e5980c935b605bcd16b946116aa23
branch: main
repository: silmari-Context-Engine
topic: "Project Structure Overview"
tags: [research, codebase, structure, directories]
status: complete
last_updated: 2026-01-01
last_updated_by: maceo
---

```
┌─────────────────────────────────────────────────────────┐
│           SILMARI CONTEXT ENGINE                        │
│           Project Structure Overview                    │
│           Status: Complete | 2026-01-01                 │
└─────────────────────────────────────────────────────────┘
```

# Research: Project Structure Overview

**Date**: 2026-01-01T11:33:37-05:00
**Researcher**: maceo
**Git Commit**: ba5ab989c06e5980c935b605bcd16b946116aa23
**Branch**: main
**Repository**: silmari-Context-Engine

## Research Question

What is the project structure? List main directories only.

## 📊 Summary

The silmari-Context-Engine project contains **7 main source directories** and **8 hidden configuration directories** at the root level.

## 🎯 Main Directories

| Directory | Purpose |
|-----------|---------|
| `agents/` | Agent configuration and definitions |
| `commands/` | CLI command implementations |
| `docs/` | Project documentation |
| `planning_pipeline/` | Planning and orchestration pipeline modules |
| `sprints/` | Sprint planning and tracking |
| `thoughts/` | Research documents, notes, and context |

## 🛠️ Configuration Directories (Hidden)

| Directory | Purpose |
|-----------|---------|
| `.agent/` | Agent runtime configuration |
| `.beads/` | Beads issue tracking system data |
| `.claude/` | Claude Code settings and configuration |
| `.cursor/` | Cursor IDE configuration |
| `.git/` | Git version control |
| `.pytest_cache/` | Pytest cache files |
| `.silmari/` | Silmari Oracle configuration |
| `.specstory/` | Spec story history |
| `.workflow-checkpoints/` | Workflow checkpoint storage |

## 📁 Root-Level Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Agent documentation |
| `CONTRIBUTING.md` | Contribution guidelines |
| `LICENSE` | Project license |
| `README.md` | Main project readme |
| `install.sh` | Installation script |
| `loop-runner.py` | Loop execution runner |
| `mcp-config.example.json` | MCP configuration example |
| `mcp-setup.py` | MCP setup script |
| `orchestrator.py` | Main orchestrator |
| `planning_orchestrator.py` | Planning orchestrator |
| `resume_pipeline.py` | Resume pipeline module |
| `resume_planning.py` | Resume planning entry point |
| `setup-context-engineered.sh` | Context-engineered setup |
| `setup-native-hooks.sh` | Native hooks setup |

## Code References

- Root directory: `/home/maceo/Dev/silmari-Context-Engine`
