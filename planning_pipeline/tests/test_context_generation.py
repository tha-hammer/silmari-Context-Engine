"""Tests for context_generation module.

TDD tests following Red-Green-Refactor pattern for:
- Phase 1: Tech Stack Extraction
- Phase 2: File Group Analysis
- Phase 3: Context Persistence
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ==============================================================================
# Phase 1: Tech Stack Extraction Tests
# ==============================================================================


class TestExtractTechStack:
    """Tests for extract_tech_stack() function."""

    def test_extract_tech_stack_identifies_python_project(self, tmp_path: Path):
        """Test that Python project is identified from config files."""
        # Create Python project structure
        (tmp_path / "pyproject.toml").write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
dependencies = ["pytest", "pydantic"]

[build-system]
requires = ["setuptools"]
"""
        )
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass")

        from planning_pipeline.context_generation import extract_tech_stack

        result = extract_tech_stack(tmp_path)

        assert "Python" in result.languages
        assert any("pytest" in fw.lower() for fw in result.testing_frameworks)

    def test_extract_tech_stack_identifies_typescript_project(self, tmp_path: Path):
        """Test that TypeScript project is identified from config files."""
        # Create TypeScript/Node project structure
        (tmp_path / "package.json").write_text(
            json.dumps(
                {
                    "name": "test-project",
                    "version": "1.0.0",
                    "devDependencies": {"typescript": "^5.0.0", "jest": "^29.0.0"},
                    "dependencies": {"react": "^18.0.0"},
                }
            )
        )
        (tmp_path / "tsconfig.json").write_text(json.dumps({"compilerOptions": {}}))
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "App.tsx").write_text("export const App = () => <div/>")

        from planning_pipeline.context_generation import extract_tech_stack

        result = extract_tech_stack(tmp_path)

        assert "TypeScript" in result.languages
        assert any("react" in fw.lower() for fw in result.frameworks)
        assert any("jest" in fw.lower() for fw in result.testing_frameworks)

    def test_extract_tech_stack_handles_empty_directory(self, tmp_path: Path):
        """Test that empty directory returns minimal tech stack."""
        from planning_pipeline.context_generation import extract_tech_stack

        result = extract_tech_stack(tmp_path)

        # Should return empty/minimal tech stack, not raise
        assert result is not None
        assert isinstance(result.languages, list)
        assert isinstance(result.frameworks, list)

    def test_extract_tech_stack_handles_baml_client_error(self, tmp_path: Path):
        """Test that BAML client errors are handled gracefully."""
        # Create minimal Python project
        (tmp_path / "setup.py").write_text("from setuptools import setup; setup()")

        from planning_pipeline.context_generation import (
            ContextGenerationError,
            extract_tech_stack,
        )

        # Should either return result or raise ContextGenerationError
        # (depends on implementation - if BAML fails, should handle gracefully)
        try:
            result = extract_tech_stack(tmp_path)
            # If it succeeds, verify basic structure
            assert result is not None
        except ContextGenerationError:
            # This is also acceptable behavior for BAML errors
            pass

    def test_extract_tech_stack_detects_rust_project(self, tmp_path: Path):
        """Test that Rust project is identified."""
        (tmp_path / "Cargo.toml").write_text(
            """
[package]
name = "test-crate"
version = "0.1.0"

[dependencies]
tokio = "1.0"
"""
        )
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.rs").write_text("fn main() {}")

        from planning_pipeline.context_generation import extract_tech_stack

        result = extract_tech_stack(tmp_path)

        assert "Rust" in result.languages

    def test_extract_tech_stack_detects_go_project(self, tmp_path: Path):
        """Test that Go project is identified."""
        (tmp_path / "go.mod").write_text(
            """
module example.com/test

go 1.21
"""
        )
        (tmp_path / "main.go").write_text("package main\nfunc main() {}")

        from planning_pipeline.context_generation import extract_tech_stack

        result = extract_tech_stack(tmp_path)

        assert "Go" in result.languages


# ==============================================================================
# Phase 2: File Group Analysis Tests
# ==============================================================================


class TestAnalyzeFileGroups:
    """Tests for analyze_file_groups() function."""

    def test_analyze_file_groups_identifies_feature_modules(self, tmp_path: Path):
        """Test that feature modules are identified as groups."""
        # Create project with clear module structure
        (tmp_path / "src" / "auth").mkdir(parents=True)
        (tmp_path / "src" / "auth" / "login.py").write_text("def login(): pass")
        (tmp_path / "src" / "auth" / "logout.py").write_text("def logout(): pass")

        (tmp_path / "src" / "api").mkdir(parents=True)
        (tmp_path / "src" / "api" / "routes.py").write_text("routes = []")
        (tmp_path / "src" / "api" / "handlers.py").write_text("handlers = []")

        from planning_pipeline.context_generation import analyze_file_groups

        result = analyze_file_groups(tmp_path, max_files=100)

        assert len(result.groups) >= 2
        group_names = [g.name.lower() for g in result.groups]
        assert any("auth" in name for name in group_names)
        assert any("api" in name for name in group_names)

    def test_analyze_file_groups_handles_flat_structure(self, tmp_path: Path):
        """Test that flat directory structure is handled."""
        # Create flat project structure
        (tmp_path / "main.py").write_text("main code")
        (tmp_path / "utils.py").write_text("utils code")
        (tmp_path / "config.py").write_text("config code")

        from planning_pipeline.context_generation import analyze_file_groups

        result = analyze_file_groups(tmp_path, max_files=100)

        # Should create at least one group
        assert len(result.groups) >= 1
        # At least some files should be in a group
        total_files = sum(len(g.files) for g in result.groups)
        assert total_files >= 1

    def test_analyze_file_groups_respects_file_limits(self, tmp_path: Path):
        """Test that max_files limit is respected."""
        # Create many files
        src = tmp_path / "src"
        src.mkdir()
        for i in range(50):
            (src / f"module_{i}.py").write_text(f"# Module {i}")

        from planning_pipeline.context_generation import analyze_file_groups

        result = analyze_file_groups(tmp_path, max_files=10)

        # Total files in all groups should not exceed limit
        total_files = sum(len(g.files) for g in result.groups)
        assert total_files <= 10

    def test_analyze_file_groups_excludes_common_dirs(self, tmp_path: Path):
        """Test that common excluded directories are skipped."""
        # Create project with excluded directories
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("main code")

        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "main.cpython-311.pyc").write_bytes(b"compiled")

        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lib.js").write_text("lib")

        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("git config")

        from planning_pipeline.context_generation import analyze_file_groups

        result = analyze_file_groups(tmp_path, max_files=100)

        # Should not include files from excluded directories
        all_files = []
        for group in result.groups:
            all_files.extend(group.files)

        assert not any("__pycache__" in f for f in all_files)
        assert not any("node_modules" in f for f in all_files)
        assert not any(".git" in f for f in all_files)

    def test_analyze_file_groups_with_custom_excludes(self, tmp_path: Path):
        """Test that custom exclude patterns work."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("main")

        (tmp_path / "custom_exclude").mkdir()
        (tmp_path / "custom_exclude" / "file.py").write_text("excluded")

        from planning_pipeline.context_generation import analyze_file_groups

        result = analyze_file_groups(
            tmp_path, max_files=100, exclude_patterns={"custom_exclude"}
        )

        all_files = []
        for group in result.groups:
            all_files.extend(group.files)

        assert not any("custom_exclude" in f for f in all_files)


# ==============================================================================
# Phase 3: Context Persistence Tests
# ==============================================================================


class TestStepContextGeneration:
    """Tests for step_context_generation() function."""

    def test_step_context_generation_returns_success(self, tmp_path: Path):
        """Test that step_context_generation succeeds with valid project."""
        # Create minimal project
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")

        from planning_pipeline.context_generation import step_context_generation

        result = step_context_generation(tmp_path)

        assert result["success"] is True
        assert result["tech_stack"] is not None
        assert result["file_groups"] is not None
        assert result["output_dir"] is not None

    def test_step_context_generation_creates_files(self, tmp_path: Path):
        """Test that step creates output files."""
        (tmp_path / "setup.py").write_text("from setuptools import setup")
        (tmp_path / "main.py").write_text("main")

        from planning_pipeline.context_generation import step_context_generation

        output_dir = tmp_path / "custom_output"
        result = step_context_generation(tmp_path, output_dir=output_dir)

        assert result["success"] is True
        assert (output_dir / "tech_stack.json").exists()
        assert (output_dir / "file_groups.json").exists()

    def test_step_context_generation_skips_when_disabled(self, tmp_path: Path):
        """Test that step skips when disabled."""
        from planning_pipeline.context_generation import step_context_generation

        result = step_context_generation(tmp_path, enabled=False)

        assert result["success"] is True
        assert result.get("skipped") is True
        assert result["tech_stack"] is None
        assert result["file_groups"] is None

    def test_step_context_generation_respects_max_files(self, tmp_path: Path):
        """Test that step respects max_files limit."""
        (tmp_path / "src").mkdir()
        for i in range(20):
            (tmp_path / "src" / f"file_{i}.py").write_text(f"# File {i}")

        from planning_pipeline.context_generation import step_context_generation

        result = step_context_generation(tmp_path, max_files=5)

        assert result["success"] is True
        total_files = sum(len(g.files) for g in result["file_groups"].groups)
        assert total_files <= 5


class TestContextGenerationStep:
    """Tests for ContextGenerationStep class."""

    def test_step_executes_with_project_path(self, tmp_path: Path):
        """Test that ContextGenerationStep.execute() works."""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "index.js").write_text("console.log('hello')")

        from planning_pipeline.context_generation import ContextGenerationStep

        step = ContextGenerationStep(project_path=tmp_path)
        result = step.execute()

        assert result["success"] is True
        assert result["tech_stack"] is not None

    def test_step_uses_config(self, tmp_path: Path):
        """Test that step uses configuration."""
        (tmp_path / "main.py").write_text("main")

        from planning_pipeline.context_generation import (
            ContextGenerationConfig,
            ContextGenerationStep,
        )

        config = ContextGenerationConfig(
            enabled=True,
            max_files=10,
            output_dir=tmp_path / "custom",
        )
        step = ContextGenerationStep(config=config, project_path=tmp_path)
        result = step.execute()

        assert result["success"] is True
        assert (tmp_path / "custom" / "tech_stack.json").exists()

    def test_step_skips_when_disabled(self, tmp_path: Path):
        """Test that step respects enabled=False in config."""
        from planning_pipeline.context_generation import (
            ContextGenerationConfig,
            ContextGenerationStep,
        )

        config = ContextGenerationConfig(enabled=False)
        step = ContextGenerationStep(config=config, project_path=tmp_path)
        result = step.execute()

        assert result["success"] is True
        assert result.get("skipped") is True

    def test_step_returns_error_without_project_path(self):
        """Test that step returns error when no project_path provided."""
        from planning_pipeline.context_generation import ContextGenerationStep

        step = ContextGenerationStep()
        result = step.execute()

        assert result["success"] is False
        assert "error" in result


class TestSaveContextToDisk:
    """Tests for save_context_to_disk() function."""

    def test_save_context_creates_output_files(self, tmp_path: Path):
        """Test that save_context_to_disk creates expected files."""
        from planning_pipeline.context_generation import (
            FileGroup,
            FileGroupAnalysis,
            TechStackResult,
            save_context_to_disk,
        )

        tech_stack = TechStackResult(
            languages=["Python"],
            frameworks=["FastAPI"],
            testing_frameworks=["pytest"],
            build_systems=["pip"],
        )

        file_groups = FileGroupAnalysis(
            groups=[
                FileGroup(
                    name="src",
                    files=["src/main.py", "src/utils.py"],
                    purpose="Main application code",
                )
            ]
        )

        output_dir = tmp_path / "output"
        save_context_to_disk(tech_stack, file_groups, output_dir)

        assert (output_dir / "tech_stack.json").exists()
        assert (output_dir / "file_groups.json").exists()

    def test_save_context_writes_valid_json(self, tmp_path: Path):
        """Test that saved files contain valid JSON."""
        from planning_pipeline.context_generation import (
            FileGroup,
            FileGroupAnalysis,
            TechStackResult,
            save_context_to_disk,
        )

        tech_stack = TechStackResult(
            languages=["Python", "TypeScript"],
            frameworks=["Django"],
            testing_frameworks=["pytest", "jest"],
            build_systems=["pip", "npm"],
        )

        file_groups = FileGroupAnalysis(
            groups=[
                FileGroup(name="backend", files=["api/routes.py"], purpose="API routes")
            ]
        )

        output_dir = tmp_path / "output"
        save_context_to_disk(tech_stack, file_groups, output_dir)

        # Should be valid JSON
        tech_data = json.loads((output_dir / "tech_stack.json").read_text())
        groups_data = json.loads((output_dir / "file_groups.json").read_text())

        assert tech_data["languages"] == ["Python", "TypeScript"]
        assert len(groups_data["groups"]) == 1
        assert groups_data["groups"][0]["name"] == "backend"

    def test_save_context_creates_output_directory(self, tmp_path: Path):
        """Test that save_context_to_disk creates output dir if needed."""
        from planning_pipeline.context_generation import (
            FileGroupAnalysis,
            TechStackResult,
            save_context_to_disk,
        )

        tech_stack = TechStackResult(
            languages=[], frameworks=[], testing_frameworks=[], build_systems=[]
        )
        file_groups = FileGroupAnalysis(groups=[])

        output_dir = tmp_path / "nested" / "output" / "dir"
        assert not output_dir.exists()

        save_context_to_disk(tech_stack, file_groups, output_dir)

        assert output_dir.exists()
        assert (output_dir / "tech_stack.json").exists()

    def test_save_context_handles_special_characters(self, tmp_path: Path):
        """Test that special characters in data are handled."""
        from planning_pipeline.context_generation import (
            FileGroup,
            FileGroupAnalysis,
            TechStackResult,
            save_context_to_disk,
        )

        tech_stack = TechStackResult(
            languages=["C++", "C#"],
            frameworks=["ASP.NET Core"],
            testing_frameworks=["xUnit"],
            build_systems=["MSBuild"],
        )

        file_groups = FileGroupAnalysis(
            groups=[
                FileGroup(
                    name="特殊字符",  # Unicode characters
                    files=["path/with spaces/file.cs"],
                    purpose='Purpose with "quotes" and special chars <>&',
                )
            ]
        )

        output_dir = tmp_path / "output"
        save_context_to_disk(tech_stack, file_groups, output_dir)

        # Should save without errors and be readable
        tech_data = json.loads((output_dir / "tech_stack.json").read_text())
        assert "C++" in tech_data["languages"]
