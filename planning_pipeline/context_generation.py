"""Context generation for BAML-based project analysis.

This module provides functions to extract tech stack information and
analyze file groups from a project directory, generating context that
can be used by the planning pipeline.
"""

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ==============================================================================
# Custom Exceptions
# ==============================================================================


class ContextGenerationError(Exception):
    """Raised when context generation fails."""

    pass


# ==============================================================================
# Data Classes for Tech Stack
# ==============================================================================


@dataclass
class TechStackResult:
    """Result of tech stack extraction.

    Contains detected programming languages, frameworks, testing tools,
    and build systems from project configuration files.
    """

    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    testing_frameworks: List[str] = field(default_factory=list)
    build_systems: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "TechStackResult":
        """Create from dictionary."""
        return cls(
            languages=data.get("languages", []),
            frameworks=data.get("frameworks", []),
            testing_frameworks=data.get("testing_frameworks", []),
            build_systems=data.get("build_systems", []),
        )


# ==============================================================================
# Data Classes for File Groups
# ==============================================================================


@dataclass
class FileGroup:
    """A logical grouping of project files.

    Represents a feature module, directory, or related set of files
    that serve a common purpose.
    """

    name: str
    files: List[str] = field(default_factory=list)
    purpose: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class FileGroupAnalysis:
    """Result of file group analysis.

    Contains logical groupings of project files organized by
    feature or responsibility.
    """

    groups: List[FileGroup] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {"groups": [g.to_dict() for g in self.groups]}

    @classmethod
    def from_dict(cls, data: Dict) -> "FileGroupAnalysis":
        """Create from dictionary."""
        groups = [
            FileGroup(
                name=g.get("name", ""),
                files=g.get("files", []),
                purpose=g.get("purpose", ""),
            )
            for g in data.get("groups", [])
        ]
        return cls(groups=groups)


# ==============================================================================
# Constants for Tech Stack Detection
# ==============================================================================

# File indicators for each language
LANGUAGE_INDICATORS: Dict[str, List[str]] = {
    "Python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "*.py"],
    "TypeScript": ["tsconfig.json", "*.ts", "*.tsx"],
    "JavaScript": ["package.json", "*.js", "*.jsx"],
    "Rust": ["Cargo.toml", "*.rs"],
    "Go": ["go.mod", "go.sum", "*.go"],
    "Java": ["pom.xml", "build.gradle", "*.java"],
    "C#": ["*.csproj", "*.sln", "*.cs"],
    "Ruby": ["Gemfile", "*.rb", "Rakefile"],
    "PHP": ["composer.json", "*.php"],
}

# Framework indicators in package files
FRAMEWORK_INDICATORS: Dict[str, Dict[str, List[str]]] = {
    # Python frameworks
    "pyproject.toml": {
        "FastAPI": ["fastapi"],
        "Django": ["django"],
        "Flask": ["flask"],
        "Starlette": ["starlette"],
        "Pydantic": ["pydantic"],
        "SQLAlchemy": ["sqlalchemy"],
        "BAML": ["baml", "baml-py"],
    },
    "requirements.txt": {
        "FastAPI": ["fastapi"],
        "Django": ["django"],
        "Flask": ["flask"],
        "SQLAlchemy": ["sqlalchemy"],
        "Pydantic": ["pydantic"],
    },
    # Node.js/TypeScript frameworks
    "package.json": {
        "React": ["react"],
        "Next.js": ["next"],
        "Vue": ["vue"],
        "Angular": ["@angular/core"],
        "Express": ["express"],
        "NestJS": ["@nestjs/core"],
        "Fastify": ["fastify"],
    },
    # Rust frameworks
    "Cargo.toml": {
        "Tokio": ["tokio"],
        "Actix": ["actix", "actix-web"],
        "Axum": ["axum"],
        "Rocket": ["rocket"],
        "Serde": ["serde"],
    },
}

# Testing framework indicators
TESTING_INDICATORS: Dict[str, Dict[str, List[str]]] = {
    "pyproject.toml": {
        "pytest": ["pytest"],
        "unittest": ["unittest"],
        "hypothesis": ["hypothesis"],
    },
    "requirements.txt": {
        "pytest": ["pytest"],
    },
    "package.json": {
        "Jest": ["jest"],
        "Vitest": ["vitest"],
        "Mocha": ["mocha"],
        "Cypress": ["cypress"],
        "Playwright": ["@playwright/test", "playwright"],
    },
    "Cargo.toml": {
        "Rust Test": [],  # Built-in
    },
}

# Build system indicators
BUILD_SYSTEM_INDICATORS: Dict[str, str] = {
    "pyproject.toml": "pip/setuptools",
    "setup.py": "setuptools",
    "Pipfile": "pipenv",
    "poetry.lock": "Poetry",
    "package.json": "npm/yarn",
    "yarn.lock": "Yarn",
    "pnpm-lock.yaml": "pnpm",
    "Cargo.toml": "Cargo",
    "go.mod": "Go Modules",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "Makefile": "Make",
    "CMakeLists.txt": "CMake",
}

# Directories to exclude from analysis
DEFAULT_EXCLUDE_PATTERNS: Set[str] = {
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    ".env",
    "env",
    ".tox",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".eggs",
    "*.egg-info",
    ".idea",
    ".vscode",
    "target",  # Rust
    "vendor",  # Go, PHP
    "coverage",
    ".coverage",
    ".hypothesis",
    "htmlcov",
}

# Source file extensions to include
DEFAULT_SOURCE_EXTENSIONS: Set[str] = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".rs",
    ".go",
    ".java",
    ".cs",
    ".rb",
    ".php",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".swift",
    ".kt",
    ".scala",
    ".ml",
    ".hs",
    ".ex",
    ".exs",
    ".clj",
    ".erl",
    ".elm",
}


# ==============================================================================
# Tech Stack Extraction
# ==============================================================================


def extract_tech_stack(project_path: Path) -> TechStackResult:
    """Extract tech stack information from a project directory.

    Analyzes configuration files (pyproject.toml, package.json, Cargo.toml, etc.)
    to identify:
    - Programming languages used
    - Frameworks and libraries
    - Testing frameworks
    - Build systems

    Args:
        project_path: Path to the project directory to analyze

    Returns:
        TechStackResult with detected technologies

    Raises:
        ContextGenerationError: If analysis fails completely

    Example:
        >>> result = extract_tech_stack(Path("/my/project"))
        >>> print(result.languages)  # ['Python', 'TypeScript']
        >>> print(result.frameworks)  # ['FastAPI', 'React']
    """
    if not project_path.exists():
        logger.warning(f"Project path does not exist: {project_path}")
        return TechStackResult()

    try:
        languages = _detect_languages(project_path)
        frameworks = _detect_frameworks(project_path)
        testing_frameworks = _detect_testing_frameworks(project_path)
        build_systems = _detect_build_systems(project_path)

        result = TechStackResult(
            languages=list(set(languages)),
            frameworks=list(set(frameworks)),
            testing_frameworks=list(set(testing_frameworks)),
            build_systems=list(set(build_systems)),
        )

        logger.info(
            f"Extracted tech stack: {len(result.languages)} languages, "
            f"{len(result.frameworks)} frameworks"
        )
        return result

    except Exception as e:
        logger.error(f"Tech stack extraction failed: {e}")
        raise ContextGenerationError(f"Failed to extract tech stack: {e}") from e


def _detect_languages(project_path: Path) -> List[str]:
    """Detect programming languages from config files and file extensions."""
    languages = []

    for language, indicators in LANGUAGE_INDICATORS.items():
        for indicator in indicators:
            if indicator.startswith("*"):
                # Check for file extension
                ext = indicator[1:]  # Remove *
                if list(project_path.rglob(f"*{ext}"))[:1]:  # Check if any exist
                    # Exclude common generated/cache directories
                    for f in project_path.rglob(f"*{ext}"):
                        if not _is_excluded_path(f, DEFAULT_EXCLUDE_PATTERNS):
                            languages.append(language)
                            break
            else:
                # Check for specific config file
                if (project_path / indicator).exists():
                    languages.append(language)
                    break

    return languages


def _detect_frameworks(project_path: Path) -> List[str]:
    """Detect frameworks from package/config files."""
    frameworks = []

    for config_file, framework_map in FRAMEWORK_INDICATORS.items():
        config_path = project_path / config_file
        if not config_path.exists():
            continue

        try:
            content = config_path.read_text(errors="ignore").lower()

            for framework, indicators in framework_map.items():
                for indicator in indicators:
                    if indicator.lower() in content:
                        frameworks.append(framework)
                        break
        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Could not read {config_file}: {e}")

    return frameworks


def _detect_testing_frameworks(project_path: Path) -> List[str]:
    """Detect testing frameworks from package/config files."""
    testing = []

    for config_file, test_map in TESTING_INDICATORS.items():
        config_path = project_path / config_file
        if not config_path.exists():
            continue

        try:
            content = config_path.read_text(errors="ignore").lower()

            for framework, indicators in test_map.items():
                if not indicators:
                    # Built-in testing (e.g., Rust)
                    continue
                for indicator in indicators:
                    if indicator.lower() in content:
                        testing.append(framework)
                        break
        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Could not read {config_file}: {e}")

    # Also check for test directories as hints
    if (project_path / "tests").exists() or (project_path / "test").exists():
        # If Python project without explicit pytest, might still use pytest
        if (project_path / "pyproject.toml").exists() or (
            project_path / "setup.py"
        ).exists():
            if "pytest" not in testing:
                # Check for pytest.ini or conftest.py
                if (project_path / "pytest.ini").exists() or (
                    project_path / "conftest.py"
                ).exists():
                    testing.append("pytest")
                elif list(project_path.rglob("conftest.py"))[:1]:
                    testing.append("pytest")

    return testing


def _detect_build_systems(project_path: Path) -> List[str]:
    """Detect build systems from config files."""
    build_systems = []

    for config_file, build_system in BUILD_SYSTEM_INDICATORS.items():
        if (project_path / config_file).exists():
            build_systems.append(build_system)

    return build_systems


def _is_excluded_path(path: Path, exclude_patterns: Set[str]) -> bool:
    """Check if a path should be excluded based on patterns."""
    parts = path.parts
    for pattern in exclude_patterns:
        if pattern.startswith("*"):
            # Glob-style pattern
            suffix = pattern[1:]
            for part in parts:
                if part.endswith(suffix):
                    return True
        else:
            if pattern in parts:
                return True
    return False


# ==============================================================================
# File Group Analysis
# ==============================================================================


@dataclass
class FileCollectionConfig:
    """Configuration for file collection."""

    max_files: int = 100
    exclude_patterns: Set[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS)
    include_extensions: Set[str] = field(
        default_factory=lambda: DEFAULT_SOURCE_EXTENSIONS
    )


def analyze_file_groups(
    project_path: Path,
    max_files: int = 100,
    exclude_patterns: Optional[Set[str]] = None,
) -> FileGroupAnalysis:
    """Analyze project files and group them by feature/responsibility.

    Scans the project directory to identify logical groupings of files
    based on directory structure and naming conventions.

    Args:
        project_path: Path to the project directory
        max_files: Maximum number of files to analyze
        exclude_patterns: Additional directory patterns to exclude

    Returns:
        FileGroupAnalysis with file groups

    Raises:
        ContextGenerationError: If analysis fails completely

    Example:
        >>> result = analyze_file_groups(Path("/my/project"), max_files=50)
        >>> for group in result.groups:
        ...     print(f"{group.name}: {len(group.files)} files")
    """
    if not project_path.exists():
        logger.warning(f"Project path does not exist: {project_path}")
        return FileGroupAnalysis()

    try:
        # Merge exclude patterns
        all_excludes = DEFAULT_EXCLUDE_PATTERNS.copy()
        if exclude_patterns:
            all_excludes.update(exclude_patterns)

        config = FileCollectionConfig(
            max_files=max_files,
            exclude_patterns=all_excludes,
        )

        # Collect files
        files = _collect_source_files(project_path, config)

        # Group files by directory
        groups = _group_files_by_directory(project_path, files)

        result = FileGroupAnalysis(groups=groups)
        logger.info(f"Analyzed file groups: {len(result.groups)} groups found")
        return result

    except Exception as e:
        logger.error(f"File group analysis failed: {e}")
        raise ContextGenerationError(f"Failed to analyze file groups: {e}") from e


def _collect_source_files(
    project_path: Path, config: FileCollectionConfig
) -> List[Path]:
    """Collect source files from project, respecting limits and exclusions."""
    files = []

    for ext in config.include_extensions:
        for file_path in project_path.rglob(f"*{ext}"):
            if _is_excluded_path(file_path, config.exclude_patterns):
                continue

            files.append(file_path)

            if len(files) >= config.max_files:
                logger.debug(f"Reached max files limit: {config.max_files}")
                return files

    return files


def _group_files_by_directory(
    project_path: Path, files: List[Path]
) -> List[FileGroup]:
    """Group files by their parent directory."""
    # Group files by their immediate parent directory relative to project root
    dir_groups: Dict[str, List[str]] = {}

    for file_path in files:
        try:
            rel_path = file_path.relative_to(project_path)
            rel_str = str(rel_path)

            # Determine group name from directory structure
            parts = rel_path.parts
            if len(parts) > 1:
                # Use first directory level as group
                group_name = parts[0]
                if len(parts) > 2:
                    # For nested structures, use first two levels
                    group_name = f"{parts[0]}/{parts[1]}"
            else:
                # Root level files
                group_name = "root"

            if group_name not in dir_groups:
                dir_groups[group_name] = []
            dir_groups[group_name].append(rel_str)

        except ValueError:
            # File not relative to project path
            continue

    # Convert to FileGroup objects
    groups = []
    for name, group_files in sorted(dir_groups.items()):
        purpose = _infer_group_purpose(name, group_files)
        groups.append(
            FileGroup(
                name=name,
                files=group_files,
                purpose=purpose,
            )
        )

    return groups


def _infer_group_purpose(name: str, files: List[str]) -> str:
    """Infer the purpose of a file group from its name and contents."""
    name_lower = name.lower()

    # Common directory purposes
    purposes = {
        "src": "Main source code",
        "lib": "Library code",
        "tests": "Test files",
        "test": "Test files",
        "docs": "Documentation",
        "api": "API definitions and handlers",
        "models": "Data models",
        "views": "View components",
        "controllers": "Request controllers",
        "services": "Business logic services",
        "utils": "Utility functions",
        "helpers": "Helper functions",
        "components": "UI components",
        "hooks": "React/custom hooks",
        "config": "Configuration files",
        "scripts": "Utility scripts",
        "migrations": "Database migrations",
        "auth": "Authentication and authorization",
        "core": "Core functionality",
        "common": "Shared/common code",
        "root": "Root-level files",
    }

    # Check for exact match
    for key, purpose in purposes.items():
        if key in name_lower:
            return purpose

    # Default purpose based on file count
    return f"Module containing {len(files)} files"


# ==============================================================================
# Context Persistence
# ==============================================================================


def save_context_to_disk(
    tech_stack: TechStackResult,
    file_groups: FileGroupAnalysis,
    output_dir: Path,
) -> None:
    """Save generated context to disk as JSON files.

    Creates:
    - tech_stack.json: Language, framework, and tool information
    - file_groups.json: Logical file groupings

    Args:
        tech_stack: Tech stack analysis result
        file_groups: File group analysis result
        output_dir: Directory to write output files

    Raises:
        ContextGenerationError: If saving fails
    """
    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save tech stack
        tech_stack_path = output_dir / "tech_stack.json"
        tech_stack_path.write_text(
            json.dumps(tech_stack.to_dict(), indent=2, ensure_ascii=False)
        )
        logger.info(f"Saved tech stack to: {tech_stack_path}")

        # Save file groups
        file_groups_path = output_dir / "file_groups.json"
        file_groups_path.write_text(
            json.dumps(file_groups.to_dict(), indent=2, ensure_ascii=False)
        )
        logger.info(f"Saved file groups to: {file_groups_path}")

    except Exception as e:
        logger.error(f"Failed to save context: {e}")
        raise ContextGenerationError(f"Failed to save context to disk: {e}") from e


# ==============================================================================
# Pipeline Step Function (matches existing step_* pattern)
# ==============================================================================


def step_context_generation(
    project_path: Path,
    output_dir: Optional[Path] = None,
    max_files: int = 100,
    exclude_patterns: Optional[Set[str]] = None,
    enabled: bool = True,
) -> Dict[str, Any]:
    """Execute context generation step of the pipeline.

    Generates BAML context by:
    1. Extracting tech stack information
    2. Analyzing file groups
    3. Saving context to disk

    This step is designed to run after research/requirement decomposition
    and before planning, providing context for better plan generation.

    Args:
        project_path: Root path of the project
        output_dir: Directory for output files (default: project_path/output/groups)
        max_files: Maximum files to analyze
        exclude_patterns: Additional exclude patterns
        enabled: If False, skips execution and returns success

    Returns:
        Dictionary with keys:
        - success: bool
        - tech_stack: TechStackResult or None
        - file_groups: FileGroupAnalysis or None
        - output_dir: Path where files were saved
        - error: Error message if failed
    """
    if not enabled:
        logger.info("Context generation skipped (disabled)")
        return {
            "success": True,
            "tech_stack": None,
            "file_groups": None,
            "output_dir": None,
            "skipped": True,
        }

    project_path = Path(project_path).resolve()

    # Default output directory
    if output_dir is None:
        output_dir = project_path / "output" / project_path.name / "groups"

    try:
        # 1. Extract tech stack
        logger.info(f"Extracting tech stack from: {project_path}")
        tech_stack = extract_tech_stack(project_path)

        # 2. Analyze file groups
        logger.info(f"Analyzing file groups (max_files={max_files})")
        file_groups = analyze_file_groups(
            project_path,
            max_files=max_files,
            exclude_patterns=exclude_patterns,
        )

        # 3. Save to disk
        logger.info(f"Saving context to: {output_dir}")
        save_context_to_disk(tech_stack, file_groups, output_dir)

        return {
            "success": True,
            "tech_stack": tech_stack,
            "file_groups": file_groups,
            "output_dir": str(output_dir),
        }

    except ContextGenerationError as e:
        logger.error(f"Context generation failed: {e}")
        return {
            "success": False,
            "tech_stack": None,
            "file_groups": None,
            "output_dir": None,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error in context generation: {e}")
        return {
            "success": False,
            "tech_stack": None,
            "file_groups": None,
            "output_dir": None,
            "error": f"Unexpected error: {e}",
        }


# ==============================================================================
# Pipeline Step Class (for future step-based architecture)
# ==============================================================================


@dataclass
class ContextGenerationConfig:
    """Configuration for context generation step."""

    enabled: bool = True
    max_files: int = 100
    exclude_patterns: Optional[Set[str]] = None
    output_dir: Optional[Path] = None


class ContextGenerationStep:
    """Pipeline step for BAML context generation.

    This class provides an execute() method compatible with step-based
    pipeline architectures. It wraps the step_context_generation function.

    Example:
        >>> config = ContextGenerationConfig(enabled=True, max_files=50)
        >>> step = ContextGenerationStep(config, project_path=Path.cwd())
        >>> result = step.execute()
        >>> print(result["tech_stack"].languages)
    """

    def __init__(
        self,
        config: Optional[ContextGenerationConfig] = None,
        project_path: Optional[Path] = None,
    ):
        """Initialize context generation step.

        Args:
            config: Configuration for context generation
            project_path: Project path (can also be passed to execute)
        """
        self.config = config or ContextGenerationConfig()
        self.project_path = Path(project_path) if project_path else None

    def execute(
        self,
        project_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Execute the context generation step.

        Args:
            project_path: Override project path from initialization

        Returns:
            Dictionary with step results (same as step_context_generation)
        """
        path = project_path or self.project_path
        if path is None:
            return {
                "success": False,
                "error": "No project_path provided",
                "tech_stack": None,
                "file_groups": None,
                "output_dir": None,
            }

        return step_context_generation(
            project_path=path,
            output_dir=self.config.output_dir,
            max_files=self.config.max_files,
            exclude_patterns=self.config.exclude_patterns,
            enabled=self.config.enabled,
        )
