// Package exec provides command execution infrastructure for external CLI tools.
package exec

import (
	"context"
	"os"
	"path/filepath"
	"time"
)

// Default timeouts for build tools.
const (
	DefaultTestTimeout  = 5 * time.Minute
	DefaultBuildTimeout = 10 * time.Minute
)

// ProjectType represents the detected project type.
type ProjectType string

const (
	ProjectTypeRust     ProjectType = "rust"
	ProjectTypeNode     ProjectType = "node"
	ProjectTypeGo       ProjectType = "go"
	ProjectTypePython   ProjectType = "python"
	ProjectTypeMake     ProjectType = "make"
	ProjectTypeUnknown  ProjectType = "unknown"
)

// MarkerFile maps project types to their marker files.
var MarkerFiles = map[ProjectType]string{
	ProjectTypeRust:   "Cargo.toml",
	ProjectTypeNode:   "package.json",
	ProjectTypeGo:     "go.mod",
	ProjectTypePython: "pyproject.toml",
	ProjectTypeMake:   "Makefile",
}

// FallbackMarkers for Python projects that might use requirements.txt instead.
var FallbackMarkers = map[ProjectType][]string{
	ProjectTypePython: {"requirements.txt"},
}

// BuildToolRunner detects project types and runs build/test commands.
type BuildToolRunner struct {
	testTimeout  time.Duration
	buildTimeout time.Duration
	runner       *Runner
}

// BuildToolOption is a functional option for configuring a BuildToolRunner.
type BuildToolOption func(*BuildToolRunner)

// NewBuildToolRunner creates a new BuildToolRunner with the given options.
func NewBuildToolRunner(opts ...BuildToolOption) *BuildToolRunner {
	r := &BuildToolRunner{
		testTimeout:  DefaultTestTimeout,
		buildTimeout: DefaultBuildTimeout,
		runner:       NewRunner(),
	}
	for _, opt := range opts {
		opt(r)
	}
	return r
}

// WithTestTimeout sets the timeout for test commands.
func WithTestTimeout(d time.Duration) BuildToolOption {
	return func(r *BuildToolRunner) {
		r.testTimeout = d
	}
}

// WithBuildTimeout sets the timeout for build commands.
func WithBuildTimeout(d time.Duration) BuildToolOption {
	return func(r *BuildToolRunner) {
		r.buildTimeout = d
	}
}

// WithBuildToolRunner sets a custom underlying runner.
func WithBuildToolRunner(runner *Runner) BuildToolOption {
	return func(r *BuildToolRunner) {
		r.runner = runner
	}
}

// DetectProjectType detects the project type by checking for marker files.
func (r *BuildToolRunner) DetectProjectType(projectPath string) ProjectType {
	// Check primary markers first
	for projectType, marker := range MarkerFiles {
		markerPath := filepath.Join(projectPath, marker)
		if _, err := os.Stat(markerPath); err == nil {
			return projectType
		}
	}

	// Check fallback markers
	for projectType, markers := range FallbackMarkers {
		for _, marker := range markers {
			markerPath := filepath.Join(projectPath, marker)
			if _, err := os.Stat(markerPath); err == nil {
				return projectType
			}
		}
	}

	return ProjectTypeUnknown
}

// DetectTestCommand returns the appropriate test command for the project type.
func (r *BuildToolRunner) DetectTestCommand(projectPath string) string {
	projectType := r.DetectProjectType(projectPath)
	switch projectType {
	case ProjectTypeRust:
		return "cargo test"
	case ProjectTypeNode:
		return "npm test"
	case ProjectTypeGo:
		return "go test ./..."
	case ProjectTypePython:
		return "pytest"
	case ProjectTypeMake:
		return "make test"
	default:
		return ""
	}
}

// DetectBuildCommand returns the appropriate build command for the project type.
func (r *BuildToolRunner) DetectBuildCommand(projectPath string) string {
	projectType := r.DetectProjectType(projectPath)
	switch projectType {
	case ProjectTypeRust:
		return "cargo build"
	case ProjectTypeNode:
		return "npm run build"
	case ProjectTypeGo:
		return "go build ./..."
	case ProjectTypePython:
		return "" // Python typically doesn't have a build step
	case ProjectTypeMake:
		return "make"
	default:
		return ""
	}
}

// RunTests runs the detected test command for the project.
func (r *BuildToolRunner) RunTests(ctx context.Context, projectPath string) (*CommandResult, error) {
	cmd := r.DetectTestCommand(projectPath)
	if cmd == "" {
		return &CommandResult{
			Success:  false,
			Error:    "unknown project type: could not detect test command",
			ExitCode: -1,
		}, nil
	}

	return r.runShellCommand(ctx, projectPath, cmd, r.testTimeout)
}

// RunBuild runs the detected build command for the project.
func (r *BuildToolRunner) RunBuild(ctx context.Context, projectPath string) (*CommandResult, error) {
	cmd := r.DetectBuildCommand(projectPath)
	if cmd == "" {
		// Python projects may not have a build command
		projectType := r.DetectProjectType(projectPath)
		if projectType == ProjectTypePython {
			return &CommandResult{
				Success:  true,
				Output:   "no build step required for Python project",
				ExitCode: 0,
			}, nil
		}
		return &CommandResult{
			Success:  false,
			Error:    "unknown project type: could not detect build command",
			ExitCode: -1,
		}, nil
	}

	return r.runShellCommand(ctx, projectPath, cmd, r.buildTimeout)
}

// RunCommand runs an arbitrary command in the project directory.
func (r *BuildToolRunner) RunCommand(ctx context.Context, projectPath, command string) (*CommandResult, error) {
	return r.runShellCommand(ctx, projectPath, command, r.testTimeout)
}

// runShellCommand executes a shell command with the given timeout.
func (r *BuildToolRunner) runShellCommand(ctx context.Context, projectPath, command string, timeout time.Duration) (*CommandResult, error) {
	// Create a runner with the project path and timeout
	runner := NewRunner(
		WithWorkingDir(projectPath),
		WithTimeout(timeout),
	)

	// Execute via shell to handle complex commands (e.g., "npm run build")
	return runner.Run(ctx, "sh", "-c", command)
}

// BuildResult extends CommandResult with additional build-specific information.
type BuildResult struct {
	*CommandResult
	ProjectType ProjectType `json:"project_type"`
	Command     string      `json:"command"`
}

// RunTestsWithInfo runs tests and returns a BuildResult with project info.
func (r *BuildToolRunner) RunTestsWithInfo(ctx context.Context, projectPath string) (*BuildResult, error) {
	projectType := r.DetectProjectType(projectPath)
	cmd := r.DetectTestCommand(projectPath)

	result, err := r.RunTests(ctx, projectPath)
	if err != nil {
		return nil, err
	}

	return &BuildResult{
		CommandResult: result,
		ProjectType:   projectType,
		Command:       cmd,
	}, nil
}

// RunBuildWithInfo runs build and returns a BuildResult with project info.
func (r *BuildToolRunner) RunBuildWithInfo(ctx context.Context, projectPath string) (*BuildResult, error) {
	projectType := r.DetectProjectType(projectPath)
	cmd := r.DetectBuildCommand(projectPath)

	result, err := r.RunBuild(ctx, projectPath)
	if err != nil {
		return nil, err
	}

	return &BuildResult{
		CommandResult: result,
		ProjectType:   projectType,
		Command:       cmd,
	}, nil
}
