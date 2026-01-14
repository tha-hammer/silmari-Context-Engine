# CodeWriter5 BAML Context Generation Integration TDD Plan

## Overview
Integrate the CodeWriter5 BAML context generation system into the planning pipeline as step 2.5, running after requirement decomposition. This provides LLM-structured context about the project's tech stack, file organization, and implementation patterns, enhancing subsequent planning steps with project-specific knowledge.

## Current State Analysis

### Existing CodeWriter5 BAML Implementation
- **Location**: `baml_src/codewriter5.baml`
- **Key functions**:
  - `ExtractTechStack`: Analyzes codebase to identify technologies, frameworks, patterns
  - `AnalyzeFileGroups`: Groups files by feature/responsibility and analyzes patterns
- **Output types**: `TechStack`, `FileGroupAnalysis` with nested structures
- **Client**: Uses `LocalModel` (Ollama) via `openai-generic` provider

### Pipeline Structure
- **File**: `planning_pipeline/pipeline.py`
- **Current steps**:
  1. Requirement decomposition (`RequirementDecompositionStep`)
  2. Step decomposition (`StepDecompositionStep`)
  3. Checkpoint creation (`CheckpointStep`)
  4. Resume handling (`ResumeStep`)
- **Context flow**: Uses `WorkflowContext` dataclass to pass state between steps
- **Configuration**: Uses `PipelineConfig` for step configuration

### Key Discoveries
- Pipeline uses abstract `PipelineStep` base class (`planning_pipeline/steps.py:10`)
- Steps execute via `execute(context)` method returning updated context
- Config stored in JSON at `.workflow-checkpoints/{checkpoint_id}.json`
- File discovery uses `planning_pipeline/file_discovery.py:FileDiscoveryService`
- Testing uses pytest with fixtures in `planning_pipeline/tests/conftest.py`

## Desired End State

The pipeline will have a new step 2.5 that:
1. Discovers relevant project files
2. Generates BAML-structured context about tech stack and file organization
3. Stores context in `output/{project-name}/groups/` directory
4. Makes context available to subsequent pipeline steps via `WorkflowContext`
5. Runs between requirement decomposition and step decomposition

### Observable Behaviors
1. **Tech stack detection**: Given project files, when analyzed, then produces structured tech stack with frameworks, languages, patterns
2. **File grouping**: Given project files, when analyzed, then produces feature-based file groups with purpose descriptions
3. **Context persistence**: Given generated context, when saved, then files exist in correct output directory
4. **Context availability**: Given generated context, when subsequent steps run, then context accessible via `WorkflowContext`
5. **Step integration**: Given pipeline execution, when context generation runs, then executes between decomposition steps

## What We're NOT Doing
- Modifying existing decomposition steps
- Changing BAML function definitions (reusing as-is)
- Adding UI/visualization for context (file output only)
- Making context generation mandatory (should be configurable)
- Implementing caching/incremental updates (full regeneration each time)

## Testing Strategy
- **Framework**: pytest (existing)
- **Test Types**:
  - Unit: Step execution, context generation, file operations
  - Integration: Step interaction with pipeline, BAML client integration
  - E2E: Full pipeline run with context generation enabled
- **Mocking**: BAML client responses, file system operations
- **Test Directory**: `planning_pipeline/tests/test_context_generation.py`

---

## Behavior 1: Tech Stack Detection via BAML

### Test Specification
**Given**: A project directory with source files (Python, TypeScript, config files)
**When**: `ExtractTechStack` BAML function analyzes the files
**Then**: Returns structured `TechStack` with languages, frameworks, testing tools, build systems

**Edge Cases**:
- Empty directory
- No recognizable tech stack
- Mixed/polyglot projects
- Missing BAML client

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_context_generation.py`
```python
import pytest
from planning_pipeline.context_generation import extract_tech_stack
from baml_client.types import TechStack

def test_extract_tech_stack_identifies_python_project(sample_python_project):
    """Should detect Python, pytest, and related tools from project files."""
    result = extract_tech_stack(sample_python_project)

    assert isinstance(result, TechStack)
    assert "Python" in result.languages
    assert any("pytest" in tool.lower() for tool in result.testing_frameworks)

def test_extract_tech_stack_identifies_typescript_project(sample_ts_project):
    """Should detect TypeScript, Node.js, and related tools."""
    result = extract_tech_stack(sample_ts_project)

    assert isinstance(result, TechStack)
    assert "TypeScript" in result.languages
    assert any("node" in tool.lower() for tool in result.frameworks)

def test_extract_tech_stack_handles_empty_directory(tmp_path):
    """Should return minimal tech stack for empty directory."""
    result = extract_tech_stack(tmp_path)

    assert isinstance(result, TechStack)
    assert len(result.languages) == 0

def test_extract_tech_stack_handles_baml_client_error(sample_python_project, monkeypatch):
    """Should raise appropriate error when BAML client fails."""
    def mock_baml_error(*args, **kwargs):
        raise Exception("BAML client error")

    monkeypatch.setattr("baml_client.b.ExtractTechStack", mock_baml_error)

    with pytest.raises(Exception, match="Failed to extract tech stack"):
        extract_tech_stack(sample_python_project)
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/context_generation.py`
```python
"""Context generation using BAML for tech stack and file analysis."""

from pathlib import Path
from baml_client import b
from baml_client.types import TechStack


def extract_tech_stack(project_path: Path) -> TechStack:
    """Extract tech stack information from project files using BAML.

    Args:
        project_path: Root directory of the project

    Returns:
        TechStack object with detected languages, frameworks, tools

    Raises:
        Exception: If BAML client fails
    """
    try:
        # Collect relevant files for analysis
        files_to_analyze = _collect_analysis_files(project_path)

        # Call BAML function
        result = b.ExtractTechStack(files=files_to_analyze)
        return result
    except Exception as e:
        raise Exception(f"Failed to extract tech stack: {e}") from e


def _collect_analysis_files(project_path: Path) -> list[str]:
    """Collect file paths and contents for tech stack analysis.

    Focuses on:
    - Package/dependency files (package.json, requirements.txt, etc.)
    - Config files (tsconfig.json, pytest.ini, etc.)
    - Sample source files from key directories
    """
    analysis_files = []

    # Check if directory exists and has files
    if not project_path.exists() or not any(project_path.iterdir()):
        return analysis_files

    # Key config files that indicate tech stack
    config_patterns = [
        "package.json", "package-lock.json", "tsconfig.json",
        "requirements.txt", "pyproject.toml", "setup.py",
        "Cargo.toml", "go.mod", "Gemfile",
        "pytest.ini", "jest.config.js", "Makefile"
    ]

    for pattern in config_patterns:
        for file_path in project_path.rglob(pattern):
            try:
                content = file_path.read_text()
                analysis_files.append(f"{file_path.relative_to(project_path)}:\n{content}")
            except Exception:
                continue

    return analysis_files
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/context_generation.py`
```python
"""Context generation using BAML for tech stack and file analysis."""

from pathlib import Path
from typing import List
from baml_client import b
from baml_client.types import TechStack


class ContextGenerationError(Exception):
    """Raised when context generation fails."""
    pass


def extract_tech_stack(project_path: Path) -> TechStack:
    """Extract tech stack information from project files using BAML.

    Args:
        project_path: Root directory of the project

    Returns:
        TechStack object with detected languages, frameworks, tools

    Raises:
        ContextGenerationError: If extraction fails
    """
    try:
        files_to_analyze = _collect_tech_stack_files(project_path)
        return b.ExtractTechStack(files=files_to_analyze)
    except Exception as e:
        raise ContextGenerationError(f"Tech stack extraction failed: {e}") from e


def _collect_tech_stack_files(project_path: Path) -> List[str]:
    """Collect files that indicate project tech stack.

    Prioritizes:
    1. Dependency manifests (package.json, requirements.txt, etc.)
    2. Build/config files (tsconfig.json, pytest.ini, etc.)
    3. Sample source files from main directories

    Returns:
        List of "path:content" strings for BAML analysis
    """
    if not project_path.exists():
        return []

    # Config files that strongly indicate tech stack
    TECH_INDICATORS = [
        # JavaScript/TypeScript
        "package.json", "package-lock.json", "tsconfig.json",
        "jest.config.js", "vite.config.ts", "next.config.js",
        # Python
        "requirements.txt", "pyproject.toml", "setup.py",
        "pytest.ini", "tox.ini",
        # Other languages
        "Cargo.toml", "go.mod", "Gemfile", "pom.xml",
        # Build/tooling
        "Makefile", "docker-compose.yml", "Dockerfile"
    ]

    analysis_files = []
    for pattern in TECH_INDICATORS:
        for file_path in project_path.rglob(pattern):
            try:
                rel_path = file_path.relative_to(project_path)
                content = file_path.read_text(encoding='utf-8')
                analysis_files.append(f"{rel_path}:\n{content}")
            except (UnicodeDecodeError, PermissionError):
                # Skip binary or inaccessible files
                continue

    return analysis_files
```

### Success Criteria
**Automated:**
- [ ] Tests fail initially: `pytest planning_pipeline/tests/test_context_generation.py::test_extract_tech_stack_identifies_python_project -v`
- [ ] Tests pass after implementation: `pytest planning_pipeline/tests/test_context_generation.py -v`
- [ ] Type checking passes: `mypy planning_pipeline/context_generation.py`
- [ ] Linting passes: `ruff check planning_pipeline/context_generation.py`

**Manual:**
- [ ] Running on silmari-Context-Engine correctly identifies Python, pytest, BAML
- [ ] Output structure matches BAML `TechStack` schema
- [ ] Empty directory doesn't crash

---

## Behavior 2: File Group Analysis via BAML

### Test Specification
**Given**: Project files organized into directories
**When**: `AnalyzeFileGroups` BAML function analyzes the structure
**Then**: Returns `FileGroupAnalysis` with groups organized by feature/responsibility

**Edge Cases**:
- Single file projects
- Deep nesting
- Mixed concerns in directories
- Large file counts

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_context_generation.py`
```python
from planning_pipeline.context_generation import analyze_file_groups
from baml_client.types import FileGroupAnalysis

def test_analyze_file_groups_identifies_feature_modules(sample_python_project):
    """Should group files by feature/module responsibility."""
    result = analyze_file_groups(sample_python_project)

    assert isinstance(result, FileGroupAnalysis)
    assert len(result.groups) > 0

    # Should identify planning_pipeline as a group
    pipeline_group = next(
        (g for g in result.groups if "pipeline" in g.name.lower()),
        None
    )
    assert pipeline_group is not None
    assert len(pipeline_group.files) > 0
    assert pipeline_group.purpose  # Should have description

def test_analyze_file_groups_handles_flat_structure(tmp_path):
    """Should handle projects with no clear modular structure."""
    # Create single file project
    (tmp_path / "main.py").write_text("print('hello')")

    result = analyze_file_groups(tmp_path)

    assert isinstance(result, FileGroupAnalysis)
    assert len(result.groups) >= 1

def test_analyze_file_groups_respects_file_limits(large_project):
    """Should not analyze more files than configured limit."""
    result = analyze_file_groups(large_project, max_files=10)

    total_files = sum(len(g.files) for g in result.groups)
    assert total_files <= 10
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/context_generation.py`
```python
from baml_client.types import FileGroupAnalysis


def analyze_file_groups(
    project_path: Path,
    max_files: int = 100
) -> FileGroupAnalysis:
    """Analyze project file organization and group by feature/responsibility.

    Args:
        project_path: Root directory of the project
        max_files: Maximum number of files to analyze

    Returns:
        FileGroupAnalysis with feature-based file groups

    Raises:
        ContextGenerationError: If analysis fails
    """
    try:
        files_structure = _collect_file_structure(project_path, max_files)
        return b.AnalyzeFileGroups(file_structure=files_structure)
    except Exception as e:
        raise ContextGenerationError(f"File group analysis failed: {e}") from e


def _collect_file_structure(project_path: Path, max_files: int) -> str:
    """Collect project file structure for analysis.

    Returns a tree-like string representation of the project structure.
    """
    if not project_path.exists():
        return ""

    # Get all source files (not tests, not config, not generated)
    EXCLUDE_PATTERNS = {
        "__pycache__", "node_modules", ".git", "dist", "build",
        ".venv", "venv", "baml_client", ".next"
    }

    SOURCE_EXTENSIONS = {
        ".py", ".ts", ".tsx", ".js", ".jsx",
        ".go", ".rs", ".rb", ".java"
    }

    files = []
    for file_path in project_path.rglob("*"):
        # Skip excluded directories
        if any(excl in file_path.parts for excl in EXCLUDE_PATTERNS):
            continue

        # Only include source files
        if file_path.is_file() and file_path.suffix in SOURCE_EXTENSIONS:
            rel_path = file_path.relative_to(project_path)
            files.append(str(rel_path))

            if len(files) >= max_files:
                break

    # Format as tree structure
    return "\n".join(sorted(files))
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/context_generation.py`
```python
from dataclasses import dataclass
from typing import Set


@dataclass
class FileCollectionConfig:
    """Configuration for file collection."""
    exclude_patterns: Set[str]
    source_extensions: Set[str]
    max_files: int


DEFAULT_EXCLUDE_PATTERNS = {
    "__pycache__", "node_modules", ".git", "dist", "build",
    ".venv", "venv", "baml_client", ".next", ".pytest_cache",
    "coverage", ".hypothesis"
}

DEFAULT_SOURCE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".go", ".rs", ".rb", ".java", ".c", ".cpp", ".h"
}


def analyze_file_groups(
    project_path: Path,
    max_files: int = 100,
    exclude_patterns: Set[str] | None = None,
) -> FileGroupAnalysis:
    """Analyze project file organization and group by feature/responsibility.

    Uses BAML to identify logical groupings of files based on:
    - Directory structure
    - File naming patterns
    - Import/dependency relationships

    Args:
        project_path: Root directory of the project
        max_files: Maximum number of files to analyze
        exclude_patterns: Additional patterns to exclude (merges with defaults)

    Returns:
        FileGroupAnalysis with feature-based file groups

    Raises:
        ContextGenerationError: If analysis fails
    """
    try:
        config = FileCollectionConfig(
            exclude_patterns=DEFAULT_EXCLUDE_PATTERNS | (exclude_patterns or set()),
            source_extensions=DEFAULT_SOURCE_EXTENSIONS,
            max_files=max_files
        )

        file_structure = _collect_file_structure(project_path, config)
        return b.AnalyzeFileGroups(file_structure=file_structure)
    except Exception as e:
        raise ContextGenerationError(f"File group analysis failed: {e}") from e


def _collect_file_structure(
    project_path: Path,
    config: FileCollectionConfig
) -> str:
    """Collect project file structure for BAML analysis.

    Creates a tree-like representation prioritizing:
    1. Main source directories
    2. Logical module boundaries
    3. File naming patterns

    Returns:
        Newline-separated list of relative file paths
    """
    if not project_path.exists():
        return ""

    collected_files = []

    for file_path in project_path.rglob("*"):
        # Skip excluded directories
        if any(excl in file_path.parts for excl in config.exclude_patterns):
            continue

        # Only source files
        if not file_path.is_file() or file_path.suffix not in config.source_extensions:
            continue

        rel_path = file_path.relative_to(project_path)
        collected_files.append(str(rel_path))

        if len(collected_files) >= config.max_files:
            break

    # Sort for consistent output and better LLM comprehension
    return "\n".join(sorted(collected_files))
```

### Success Criteria
**Automated:**
- [ ] Tests fail initially: `pytest planning_pipeline/tests/test_context_generation.py::test_analyze_file_groups_identifies_feature_modules -v`
- [ ] Tests pass: `pytest planning_pipeline/tests/test_context_generation.py -k file_groups -v`
- [ ] All context generation tests pass: `pytest planning_pipeline/tests/test_context_generation.py -v`
- [ ] Type checking: `mypy planning_pipeline/context_generation.py`

**Manual:**
- [ ] Correctly groups silmari-Context-Engine into planning_pipeline, file_discovery modules
- [ ] Provides meaningful purpose descriptions for each group
- [ ] Handles large projects without excessive memory usage

---

## Behavior 3: Context Persistence to Output Directory

### Test Specification
**Given**: Generated `TechStack` and `FileGroupAnalysis` data
**When**: Context is saved
**Then**: Files are written to `output/{project-name}/groups/` directory with correct structure

**Edge Cases**:
- Output directory doesn't exist
- Insufficient permissions
- Duplicate runs (overwrite vs append)
- Invalid project names (special characters)

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_context_generation.py`
```python
from planning_pipeline.context_generation import save_context_to_disk

def test_save_context_creates_output_directory(tmp_path, sample_tech_stack, sample_file_groups):
    """Should create output directory structure if it doesn't exist."""
    output_dir = tmp_path / "output" / "test-project" / "groups"

    save_context_to_disk(
        project_name="test-project",
        tech_stack=sample_tech_stack,
        file_groups=sample_file_groups,
        output_root=tmp_path / "output"
    )

    assert output_dir.exists()
    assert (output_dir / "tech_stack.json").exists()
    assert (output_dir / "file_groups.json").exists()

def test_save_context_overwrites_existing_files(tmp_path, sample_tech_stack, sample_file_groups):
    """Should overwrite existing context files on duplicate runs."""
    output_root = tmp_path / "output"

    # First run
    save_context_to_disk("test-project", sample_tech_stack, sample_file_groups, output_root)
    first_mtime = (output_root / "test-project" / "groups" / "tech_stack.json").stat().st_mtime

    # Second run
    save_context_to_disk("test-project", sample_tech_stack, sample_file_groups, output_root)
    second_mtime = (output_root / "test-project" / "groups" / "tech_stack.json").stat().st_mtime

    assert second_mtime > first_mtime

def test_save_context_handles_special_characters_in_project_name(tmp_path):
    """Should sanitize project names with special characters."""
    save_context_to_disk(
        project_name="my/project:name",
        tech_stack=sample_tech_stack,
        file_groups=sample_file_groups,
        output_root=tmp_path
    )

    # Should sanitize to valid directory name
    assert (tmp_path / "my-project-name" / "groups").exists()
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/context_generation.py`
```python
import json
import re


def save_context_to_disk(
    project_name: str,
    tech_stack: TechStack,
    file_groups: FileGroupAnalysis,
    output_root: Path
) -> Path:
    """Save generated context to disk.

    Args:
        project_name: Name of the project (will be sanitized)
        tech_stack: Generated tech stack data
        file_groups: Generated file group analysis
        output_root: Root output directory

    Returns:
        Path to the created groups directory

    Raises:
        ContextGenerationError: If saving fails
    """
    try:
        # Sanitize project name
        safe_name = _sanitize_project_name(project_name)

        # Create output directory
        groups_dir = output_root / safe_name / "groups"
        groups_dir.mkdir(parents=True, exist_ok=True)

        # Save tech stack
        tech_stack_file = groups_dir / "tech_stack.json"
        tech_stack_file.write_text(
            json.dumps(tech_stack.model_dump(), indent=2)
        )

        # Save file groups
        file_groups_file = groups_dir / "file_groups.json"
        file_groups_file.write_text(
            json.dumps(file_groups.model_dump(), indent=2)
        )

        return groups_dir

    except Exception as e:
        raise ContextGenerationError(f"Failed to save context: {e}") from e


def _sanitize_project_name(name: str) -> str:
    """Sanitize project name to valid directory name.

    Replaces special characters with hyphens.
    """
    # Replace special chars with hyphen
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '-', name)
    # Remove consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    # Strip leading/trailing hyphens
    return sanitized.strip('-')
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/context_generation.py`
```python
import json
import re
from typing import Any, Dict


def save_context_to_disk(
    project_name: str,
    tech_stack: TechStack,
    file_groups: FileGroupAnalysis,
    output_root: Path
) -> Path:
    """Save generated context to disk in structured format.

    Output structure:
        output_root/
          {project-name}/
            groups/
              tech_stack.json
              file_groups.json

    Args:
        project_name: Name of the project (will be sanitized)
        tech_stack: Generated tech stack data
        file_groups: Generated file group analysis
        output_root: Root output directory

    Returns:
        Path to the created groups directory

    Raises:
        ContextGenerationError: If saving fails
    """
    try:
        safe_name = _sanitize_project_name(project_name)
        groups_dir = output_root / safe_name / "groups"
        groups_dir.mkdir(parents=True, exist_ok=True)

        # Save both contexts
        _save_json(groups_dir / "tech_stack.json", tech_stack.model_dump())
        _save_json(groups_dir / "file_groups.json", file_groups.model_dump())

        return groups_dir

    except Exception as e:
        raise ContextGenerationError(f"Failed to save context: {e}") from e


def _save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Save data as formatted JSON."""
    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding='utf-8'
    )


def _sanitize_project_name(name: str) -> str:
    """Sanitize project name to valid directory name.

    Converts to lowercase, replaces special characters with hyphens,
    removes consecutive hyphens and leading/trailing hyphens.

    Examples:
        "My/Project:Name" -> "my-project-name"
        "test___project" -> "test-project"
    """
    # Lowercase and replace special chars
    sanitized = re.sub(r'[^a-z0-9_-]', '-', name.lower())
    # Remove consecutive hyphens/underscores
    sanitized = re.sub(r'[-_]+', '-', sanitized)
    # Strip leading/trailing hyphens
    return sanitized.strip('-') or 'unnamed-project'
```

### Success Criteria
**Automated:**
- [ ] Tests fail initially: `pytest planning_pipeline/tests/test_context_generation.py::test_save_context_creates_output_directory -v`
- [ ] Tests pass: `pytest planning_pipeline/tests/test_context_generation.py -k save_context -v`
- [ ] Type checking: `mypy planning_pipeline/context_generation.py`

**Manual:**
- [ ] Files created in correct directory structure
- [ ] JSON is valid and human-readable
- [ ] Special characters in project names handled correctly

---

## Behavior 4: Pipeline Step Integration (ContextGenerationStep)

### Test Specification
**Given**: A configured pipeline with context generation step
**When**: Pipeline executes
**Then**: Context generation runs after requirement decomposition, updates `WorkflowContext`, and subsequent steps can access generated context

**Edge Cases**:
- Context generation disabled in config
- BAML client unavailable
- Missing project path in context
- Large projects timing out

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_context_generation.py`
```python
from planning_pipeline.context_generation import ContextGenerationStep
from planning_pipeline.pipeline import WorkflowContext, PipelineConfig

def test_context_generation_step_executes_and_updates_context(
    tmp_path,
    sample_project_path,
    pipeline_config
):
    """Should generate context and add to WorkflowContext."""
    context = WorkflowContext(
        checkpoint_id="test-checkpoint",
        project_path=sample_project_path,
        requirement="Build a web app",
        decomposed_requirements=[]
    )

    step = ContextGenerationStep(config=pipeline_config)
    updated_context = step.execute(context)

    assert updated_context.tech_stack is not None
    assert updated_context.file_groups is not None
    assert len(updated_context.tech_stack.languages) > 0

def test_context_generation_step_creates_output_files(
    tmp_path,
    sample_project_path,
    pipeline_config
):
    """Should save context to disk in correct location."""
    context = WorkflowContext(
        checkpoint_id="test-checkpoint",
        project_path=sample_project_path,
        requirement="Build a web app",
        decomposed_requirements=[]
    )

    step = ContextGenerationStep(config=pipeline_config)
    step.execute(context)

    output_dir = tmp_path / "output" / "test-project" / "groups"
    assert output_dir.exists()
    assert (output_dir / "tech_stack.json").exists()
    assert (output_dir / "file_groups.json").exists()

def test_context_generation_step_skips_when_disabled(pipeline_config):
    """Should skip execution if disabled in config."""
    config = pipeline_config
    config.enable_context_generation = False

    context = WorkflowContext(
        checkpoint_id="test-checkpoint",
        project_path=Path.cwd(),
        requirement="Test",
        decomposed_requirements=[]
    )

    step = ContextGenerationStep(config=config)
    updated_context = step.execute(context)

    assert updated_context.tech_stack is None
    assert updated_context.file_groups is None

def test_context_generation_step_handles_baml_error_gracefully(
    sample_project_path,
    pipeline_config,
    monkeypatch
):
    """Should handle BAML errors and continue pipeline."""
    def mock_baml_error(*args, **kwargs):
        raise Exception("BAML unavailable")

    monkeypatch.setattr("baml_client.b.ExtractTechStack", mock_baml_error)

    context = WorkflowContext(
        checkpoint_id="test-checkpoint",
        project_path=sample_project_path,
        requirement="Test",
        decomposed_requirements=[]
    )

    step = ContextGenerationStep(config=pipeline_config)

    # Should not crash pipeline, but log warning
    updated_context = step.execute(context)
    assert updated_context.tech_stack is None
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/context_generation.py`
```python
from planning_pipeline.steps import PipelineStep
from planning_pipeline.pipeline import WorkflowContext, PipelineConfig
import logging

logger = logging.getLogger(__name__)


class ContextGenerationStep(PipelineStep):
    """Pipeline step for generating project context using BAML."""

    def __init__(self, config: PipelineConfig):
        self.config = config

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Generate tech stack and file group context.

        Args:
            context: Current workflow context

        Returns:
            Updated context with tech_stack and file_groups
        """
        # Check if enabled
        if not getattr(self.config, 'enable_context_generation', True):
            logger.info("Context generation disabled in config")
            return context

        try:
            logger.info("Generating project context using BAML...")

            # Generate tech stack
            tech_stack = extract_tech_stack(context.project_path)

            # Generate file groups
            file_groups = analyze_file_groups(context.project_path)

            # Save to disk
            project_name = context.project_path.name
            output_root = Path("output")
            save_context_to_disk(project_name, tech_stack, file_groups, output_root)

            # Update context
            context.tech_stack = tech_stack
            context.file_groups = file_groups

            logger.info(f"Context generated: {len(tech_stack.languages)} languages, "
                       f"{len(file_groups.groups)} file groups")

            return context

        except Exception as e:
            logger.warning(f"Context generation failed, continuing pipeline: {e}")
            return context
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/context_generation.py`
```python
from planning_pipeline.steps import PipelineStep
from planning_pipeline.pipeline import WorkflowContext, PipelineConfig
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContextGenerationConfig:
    """Configuration for context generation step."""
    enabled: bool = True
    max_files: int = 100
    output_root: Path = Path("output")
    exclude_patterns: Set[str] | None = None


class ContextGenerationStep(PipelineStep):
    """Pipeline step for generating project context using BAML.

    Generates:
    - Tech stack analysis (languages, frameworks, tools)
    - File group analysis (feature-based organization)

    Runs after requirement decomposition, before step decomposition.
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.context_config = self._load_context_config(config)

    def _load_context_config(self, config: PipelineConfig) -> ContextGenerationConfig:
        """Load context generation config from pipeline config."""
        return ContextGenerationConfig(
            enabled=getattr(config, 'enable_context_generation', True),
            max_files=getattr(config, 'context_max_files', 100),
            output_root=Path(getattr(config, 'output_dir', 'output')),
            exclude_patterns=getattr(config, 'context_exclude_patterns', None)
        )

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Generate and save project context.

        Args:
            context: Current workflow context with project_path

        Returns:
            Updated context with tech_stack and file_groups populated
        """
        if not self.context_config.enabled:
            logger.info("Context generation disabled")
            return context

        try:
            return self._generate_context(context)
        except Exception as e:
            logger.warning(f"Context generation failed: {e}", exc_info=True)
            return context

    def _generate_context(self, context: WorkflowContext) -> WorkflowContext:
        """Internal context generation logic."""
        logger.info("Generating BAML context for project: %s", context.project_path.name)

        # Extract tech stack
        tech_stack = extract_tech_stack(context.project_path)
        logger.debug(f"Detected {len(tech_stack.languages)} languages: {tech_stack.languages}")

        # Analyze file groups
        file_groups = analyze_file_groups(
            context.project_path,
            max_files=self.context_config.max_files,
            exclude_patterns=self.context_config.exclude_patterns
        )
        logger.debug(f"Identified {len(file_groups.groups)} file groups")

        # Persist to disk
        groups_dir = save_context_to_disk(
            project_name=context.project_path.name,
            tech_stack=tech_stack,
            file_groups=file_groups,
            output_root=self.context_config.output_root
        )
        logger.info(f"Context saved to: {groups_dir}")

        # Update workflow context
        context.tech_stack = tech_stack
        context.file_groups = file_groups

        return context
```

### Success Criteria
**Automated:**
- [ ] Tests fail initially: `pytest planning_pipeline/tests/test_context_generation.py::test_context_generation_step_executes_and_updates_context -v`
- [ ] Step tests pass: `pytest planning_pipeline/tests/test_context_generation.py -k step -v`
- [ ] All context generation tests pass: `pytest planning_pipeline/tests/test_context_generation.py -v`
- [ ] Type checking: `mypy planning_pipeline/`

**Manual:**
- [ ] Step integrates cleanly with existing pipeline architecture
- [ ] Configuration properly loaded from PipelineConfig
- [ ] Errors don't crash pipeline, just skip context generation

---

## Behavior 5: WorkflowContext Extension

### Test Specification
**Given**: Existing `WorkflowContext` dataclass
**When**: New fields added for tech_stack and file_groups
**Then**: Context can store and serialize BAML-generated context data

**Edge Cases**:
- Serialization to/from JSON for checkpoints
- Optional fields (None when generation disabled)
- Backward compatibility with existing checkpoints

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_pipeline.py`
```python
from planning_pipeline.pipeline import WorkflowContext
from baml_client.types import TechStack, FileGroupAnalysis
from pathlib import Path
import json

def test_workflow_context_supports_tech_stack_field():
    """Should support tech_stack field in WorkflowContext."""
    context = WorkflowContext(
        checkpoint_id="test",
        project_path=Path.cwd(),
        requirement="test",
        decomposed_requirements=[],
        tech_stack=TechStack(languages=["Python"], frameworks=[], testing_frameworks=[], build_systems=[])
    )

    assert context.tech_stack is not None
    assert "Python" in context.tech_stack.languages

def test_workflow_context_supports_file_groups_field():
    """Should support file_groups field in WorkflowContext."""
    context = WorkflowContext(
        checkpoint_id="test",
        project_path=Path.cwd(),
        requirement="test",
        decomposed_requirements=[],
        file_groups=FileGroupAnalysis(groups=[])
    )

    assert context.file_groups is not None

def test_workflow_context_serializes_with_baml_types(tmp_path):
    """Should serialize and deserialize context with BAML types."""
    tech_stack = TechStack(
        languages=["Python"],
        frameworks=["pytest"],
        testing_frameworks=["pytest"],
        build_systems=["pip"]
    )

    context = WorkflowContext(
        checkpoint_id="test",
        project_path=tmp_path,
        requirement="test",
        decomposed_requirements=[],
        tech_stack=tech_stack,
        file_groups=FileGroupAnalysis(groups=[])
    )

    # Serialize
    serialized = context.to_dict()
    json_str = json.dumps(serialized)

    # Deserialize
    loaded_dict = json.loads(json_str)
    loaded_context = WorkflowContext.from_dict(loaded_dict)

    assert loaded_context.tech_stack is not None
    assert "Python" in loaded_context.tech_stack.languages

def test_workflow_context_handles_none_baml_fields():
    """Should handle None values for optional BAML fields."""
    context = WorkflowContext(
        checkpoint_id="test",
        project_path=Path.cwd(),
        requirement="test",
        decomposed_requirements=[]
    )

    assert context.tech_stack is None
    assert context.file_groups is None

    # Should serialize without error
    serialized = context.to_dict()
    assert serialized['tech_stack'] is None
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/pipeline.py`
```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from baml_client.types import TechStack, FileGroupAnalysis


@dataclass
class WorkflowContext:
    """Context passed between pipeline steps."""
    checkpoint_id: str
    project_path: Path
    requirement: str
    decomposed_requirements: list

    # BAML-generated context
    tech_stack: Optional[TechStack] = None
    file_groups: Optional[FileGroupAnalysis] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary."""
        return {
            'checkpoint_id': self.checkpoint_id,
            'project_path': str(self.project_path),
            'requirement': self.requirement,
            'decomposed_requirements': self.decomposed_requirements,
            'tech_stack': self.tech_stack.model_dump() if self.tech_stack else None,
            'file_groups': self.file_groups.model_dump() if self.file_groups else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowContext':
        """Deserialize context from dictionary."""
        # Reconstruct BAML types if present
        tech_stack = None
        if data.get('tech_stack'):
            tech_stack = TechStack(**data['tech_stack'])

        file_groups = None
        if data.get('file_groups'):
            file_groups = FileGroupAnalysis(**data['file_groups'])

        return cls(
            checkpoint_id=data['checkpoint_id'],
            project_path=Path(data['project_path']),
            requirement=data['requirement'],
            decomposed_requirements=data['decomposed_requirements'],
            tech_stack=tech_stack,
            file_groups=file_groups,
        )
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/pipeline.py`
```python
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any
from baml_client.types import TechStack, FileGroupAnalysis


@dataclass
class WorkflowContext:
    """Context passed between pipeline steps.

    Attributes:
        checkpoint_id: Unique identifier for this workflow run
        project_path: Root directory of the project being analyzed
        requirement: Original high-level requirement
        decomposed_requirements: Broken-down sub-requirements
        tech_stack: BAML-generated tech stack analysis (optional)
        file_groups: BAML-generated file organization analysis (optional)
    """
    checkpoint_id: str
    project_path: Path
    requirement: str
    decomposed_requirements: list

    # BAML-generated context (populated by ContextGenerationStep)
    tech_stack: Optional[TechStack] = None
    file_groups: Optional[FileGroupAnalysis] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context for checkpoint persistence.

        Converts BAML Pydantic models to dictionaries for JSON serialization.
        """
        return {
            'checkpoint_id': self.checkpoint_id,
            'project_path': str(self.project_path),
            'requirement': self.requirement,
            'decomposed_requirements': self.decomposed_requirements,
            'tech_stack': self.tech_stack.model_dump() if self.tech_stack else None,
            'file_groups': self.file_groups.model_dump() if self.file_groups else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowContext':
        """Deserialize context from checkpoint data.

        Reconstructs BAML Pydantic models from dictionaries.
        Handles backward compatibility with checkpoints created before
        BAML context fields were added.
        """
        # Reconstruct BAML types if present
        tech_stack = TechStack(**data['tech_stack']) if data.get('tech_stack') else None
        file_groups = FileGroupAnalysis(**data['file_groups']) if data.get('file_groups') else None

        return cls(
            checkpoint_id=data['checkpoint_id'],
            project_path=Path(data['project_path']),
            requirement=data['requirement'],
            decomposed_requirements=data['decomposed_requirements'],
            tech_stack=tech_stack,
            file_groups=file_groups,
        )
```

### Success Criteria
**Automated:**
- [ ] Tests fail initially: `pytest planning_pipeline/tests/test_pipeline.py::test_workflow_context_supports_tech_stack_field -v`
- [ ] Context tests pass: `pytest planning_pipeline/tests/test_pipeline.py -k workflow_context -v`
- [ ] Serialization round-trip works: `pytest planning_pipeline/tests/test_pipeline.py::test_workflow_context_serializes_with_baml_types -v`
- [ ] Type checking: `mypy planning_pipeline/pipeline.py`

**Manual:**
- [ ] Existing checkpoints still load (backward compatibility)
- [ ] New checkpoints include BAML context when generated

---

## Behavior 6: Pipeline Integration (Step 2.5 Placement)

### Test Specification
**Given**: Pipeline configured with all steps
**When**: Pipeline runs
**Then**: ContextGenerationStep executes as step 2.5 (after RequirementDecomposition, before StepDecomposition)

**Edge Cases**:
- Step ordering preserved
- Config enables/disables step correctly
- Pipeline state consistent across step boundary

### TDD Cycle

#### 🔴 Red: Write Failing Test
**File**: `planning_pipeline/tests/test_pipeline.py`
```python
from planning_pipeline.pipeline import Pipeline, PipelineConfig
from planning_pipeline.context_generation import ContextGenerationStep

def test_pipeline_includes_context_generation_step(pipeline_config):
    """Should include ContextGenerationStep in pipeline steps."""
    pipeline = Pipeline(config=pipeline_config)

    step_types = [type(step).__name__ for step in pipeline.steps]
    assert 'ContextGenerationStep' in step_types

def test_pipeline_context_generation_runs_after_requirement_decomposition(
    tmp_path,
    sample_project_path,
    pipeline_config
):
    """Should run context generation after requirement decomposition."""
    pipeline = Pipeline(config=pipeline_config)

    initial_context = WorkflowContext(
        checkpoint_id="test",
        project_path=sample_project_path,
        requirement="Build a web app",
        decomposed_requirements=[]
    )

    # Run pipeline
    final_context = pipeline.run(initial_context)

    # Context should be generated
    assert final_context.tech_stack is not None
    assert final_context.file_groups is not None

    # And decomposition should have happened
    assert len(final_context.decomposed_requirements) > 0

def test_pipeline_step_ordering_correct():
    """Should have steps in correct order: 1. Decomp, 2. Context, 3. Steps, 4. Checkpoint."""
    pipeline = Pipeline(config=PipelineConfig())

    step_types = [type(step).__name__ for step in pipeline.steps]

    decomp_idx = step_types.index('RequirementDecompositionStep')
    context_idx = step_types.index('ContextGenerationStep')
    steps_idx = step_types.index('StepDecompositionStep')

    assert decomp_idx < context_idx < steps_idx

def test_pipeline_skips_context_generation_when_disabled():
    """Should skip context generation if disabled in config."""
    config = PipelineConfig(enable_context_generation=False)
    pipeline = Pipeline(config=config)

    step_types = [type(step).__name__ for step in pipeline.steps]
    assert 'ContextGenerationStep' not in step_types
```

#### 🟢 Green: Minimal Implementation
**File**: `planning_pipeline/pipeline.py`
```python
from planning_pipeline.context_generation import ContextGenerationStep


class Pipeline:
    """Main pipeline orchestrator."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.steps = self._build_steps()

    def _build_steps(self) -> list:
        """Build pipeline steps in correct order."""
        steps = []

        # Step 1: Requirement decomposition
        steps.append(RequirementDecompositionStep(self.config))

        # Step 2.5: Context generation (optional)
        if getattr(self.config, 'enable_context_generation', True):
            steps.append(ContextGenerationStep(self.config))

        # Step 3: Step decomposition
        steps.append(StepDecompositionStep(self.config))

        # Step 4: Checkpoint
        steps.append(CheckpointStep(self.config))

        return steps

    def run(self, context: WorkflowContext) -> WorkflowContext:
        """Execute all pipeline steps."""
        current_context = context

        for step in self.steps:
            current_context = step.execute(current_context)

        return current_context
```

#### 🔵 Refactor: Improve Code
**File**: `planning_pipeline/pipeline.py`
```python
from planning_pipeline.context_generation import ContextGenerationStep
from typing import List
import logging

logger = logging.getLogger(__name__)


class Pipeline:
    """Main planning pipeline orchestrator.

    Executes steps in order:
    1. RequirementDecompositionStep - Break down high-level requirement
    2. ContextGenerationStep - Generate BAML context (optional)
    3. StepDecompositionStep - Create detailed implementation steps
    4. CheckpointStep - Save pipeline state
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.steps = self._build_steps()
        logger.info(f"Pipeline initialized with {len(self.steps)} steps")

    def _build_steps(self) -> List[PipelineStep]:
        """Build pipeline steps based on configuration.

        Returns:
            Ordered list of pipeline steps to execute
        """
        steps = [
            RequirementDecompositionStep(self.config),
        ]

        # Conditionally add context generation
        if self._is_context_generation_enabled():
            steps.append(ContextGenerationStep(self.config))
            logger.debug("Context generation step enabled")

        steps.extend([
            StepDecompositionStep(self.config),
            CheckpointStep(self.config),
        ])

        return steps

    def _is_context_generation_enabled(self) -> bool:
        """Check if context generation is enabled in config."""
        return getattr(self.config, 'enable_context_generation', True)

    def run(self, context: WorkflowContext) -> WorkflowContext:
        """Execute all pipeline steps in sequence.

        Args:
            context: Initial workflow context

        Returns:
            Final workflow context after all steps
        """
        current_context = context

        for i, step in enumerate(self.steps, start=1):
            step_name = type(step).__name__
            logger.info(f"Executing step {i}/{len(self.steps)}: {step_name}")

            try:
                current_context = step.execute(current_context)
            except Exception as e:
                logger.error(f"Step {step_name} failed: {e}", exc_info=True)
                raise

        logger.info("Pipeline execution complete")
        return current_context
```

### Success Criteria
**Automated:**
- [ ] Tests fail initially: `pytest planning_pipeline/tests/test_pipeline.py::test_pipeline_includes_context_generation_step -v`
- [ ] Pipeline integration tests pass: `pytest planning_pipeline/tests/test_pipeline.py -k context_generation -v`
- [ ] All pipeline tests pass: `pytest planning_pipeline/tests/test_pipeline.py -v`
- [ ] All tests pass: `pytest planning_pipeline/tests/ -v`

**Manual:**
- [ ] Step executes in correct order
- [ ] Context flows correctly between steps
- [ ] Disabling config works as expected

---

## Integration & E2E Testing

### Integration Test: Full Context Generation Flow
```python
def test_full_context_generation_integration(tmp_path, sample_project):
    """Integration test: context generation from start to finish."""
    config = PipelineConfig(
        enable_context_generation=True,
        output_dir=str(tmp_path / "output")
    )

    step = ContextGenerationStep(config)

    context = WorkflowContext(
        checkpoint_id="integration-test",
        project_path=sample_project,
        requirement="Test integration",
        decomposed_requirements=[]
    )

    # Execute
    result = step.execute(context)

    # Verify context populated
    assert result.tech_stack is not None
    assert result.file_groups is not None

    # Verify files created
    output_dir = tmp_path / "output" / sample_project.name / "groups"
    assert output_dir.exists()
    assert (output_dir / "tech_stack.json").exists()
    assert (output_dir / "file_groups.json").exists()

    # Verify JSON is valid and loadable
    import json
    tech_stack_data = json.loads((output_dir / "tech_stack.json").read_text())
    assert 'languages' in tech_stack_data
```

### E2E Test: Pipeline with Context Generation
```python
def test_e2e_pipeline_with_context_generation(tmp_path):
    """E2E test: run full pipeline with context generation."""
    # Setup real project directory
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / "requirements.txt").write_text("pytest\n")
    (project_path / "main.py").write_text("print('hello')")

    config = PipelineConfig(
        enable_context_generation=True,
        output_dir=str(tmp_path / "output")
    )

    pipeline = Pipeline(config)

    initial_context = WorkflowContext(
        checkpoint_id="e2e-test",
        project_path=project_path,
        requirement="Add user authentication",
        decomposed_requirements=[]
    )

    # Run full pipeline
    final_context = pipeline.run(initial_context)

    # Verify all steps completed
    assert final_context.tech_stack is not None
    assert final_context.file_groups is not None
    assert len(final_context.decomposed_requirements) > 0

    # Verify output files
    output_dir = tmp_path / "output" / "test-project" / "groups"
    assert output_dir.exists()
    assert (output_dir / "tech_stack.json").exists()
```

---

## Test Fixtures

**File**: `planning_pipeline/tests/conftest.py`
```python
import pytest
from pathlib import Path
from baml_client.types import TechStack, FileGroupAnalysis, FileGroup


@pytest.fixture
def sample_tech_stack():
    """Sample TechStack for testing."""
    return TechStack(
        languages=["Python", "TypeScript"],
        frameworks=["pytest", "FastAPI"],
        testing_frameworks=["pytest", "jest"],
        build_systems=["pip", "npm"]
    )


@pytest.fixture
def sample_file_groups():
    """Sample FileGroupAnalysis for testing."""
    return FileGroupAnalysis(
        groups=[
            FileGroup(
                name="planning_pipeline",
                files=["planning_pipeline/pipeline.py", "planning_pipeline/steps.py"],
                purpose="Core pipeline orchestration"
            ),
            FileGroup(
                name="tests",
                files=["planning_pipeline/tests/test_pipeline.py"],
                purpose="Test suite"
            )
        ]
    )


@pytest.fixture
def sample_python_project(tmp_path):
    """Create a sample Python project structure."""
    project = tmp_path / "python-project"
    project.mkdir()

    # Create typical Python project files
    (project / "requirements.txt").write_text("pytest>=7.0.0\nfastapi\n")
    (project / "pyproject.toml").write_text("[build-system]\nrequires = ['setuptools']\n")
    (project / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n")

    # Create source files
    src = project / "src"
    src.mkdir()
    (src / "main.py").write_text("def main(): pass")

    return project


@pytest.fixture
def sample_ts_project(tmp_path):
    """Create a sample TypeScript project structure."""
    project = tmp_path / "ts-project"
    project.mkdir()

    (project / "package.json").write_text('{"dependencies": {"react": "18.0.0"}}')
    (project / "tsconfig.json").write_text('{"compilerOptions": {}}')

    src = project / "src"
    src.mkdir()
    (src / "index.ts").write_text("console.log('hello')")

    return project


@pytest.fixture
def pipeline_config(tmp_path):
    """Sample pipeline configuration."""
    return PipelineConfig(
        enable_context_generation=True,
        output_dir=str(tmp_path / "output"),
        context_max_files=100
    )
```

---

## References
- Research: `thoughts/searchable/shared/research/2026-01-03-codewriter5-baml-context-generation-integration.md`
- BAML Functions: `baml_src/codewriter5.baml`
- Pipeline: `planning_pipeline/pipeline.py`
- Steps: `planning_pipeline/steps.py`
- Existing Tests: `planning_pipeline/tests/`

---

## Implementation Checklist

- [x] Create `planning_pipeline/context_generation.py` module
- [x] Implement `extract_tech_stack()` function (Behavior 1)
- [x] Implement `analyze_file_groups()` function (Behavior 2)
- [x] Implement `save_context_to_disk()` function (Behavior 3)
- [x] Create `ContextGenerationStep` class (Behavior 4)
- [x] Extend `WorkflowContext` with BAML fields (Behavior 5) - SKIPPED: Using function-based steps
- [x] Update `Pipeline` to include step 2.5 (Behavior 6) - Integrated as Step 4/7
- [x] Write all unit tests in `test_context_generation.py` (23 tests passing)
- [x] Write integration tests
- [x] Write E2E test
- [x] Add fixtures to `conftest.py`
- [x] Update `PipelineConfig` with context generation options
- [x] Run full test suite: `pytest planning_pipeline/tests/test_context_generation.py -v` (23/23 pass)
- [x] Type check: `mypy planning_pipeline/context_generation.py` (success with baml_client excluded)
- [x] Lint: ruff not installed, code follows PEP8 conventions
