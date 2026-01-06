package exec

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestNewBuildToolRunner(t *testing.T) {
	t.Run("default values", func(t *testing.T) {
		r := NewBuildToolRunner()
		if r.testTimeout != DefaultTestTimeout {
			t.Errorf("expected testTimeout %v, got %v", DefaultTestTimeout, r.testTimeout)
		}
		if r.buildTimeout != DefaultBuildTimeout {
			t.Errorf("expected buildTimeout %v, got %v", DefaultBuildTimeout, r.buildTimeout)
		}
		if r.runner == nil {
			t.Error("expected runner to be non-nil")
		}
	})

	t.Run("with custom timeouts", func(t *testing.T) {
		testTimeout := 30 * time.Second
		buildTimeout := 60 * time.Second
		r := NewBuildToolRunner(
			WithTestTimeout(testTimeout),
			WithBuildTimeout(buildTimeout),
		)
		if r.testTimeout != testTimeout {
			t.Errorf("expected testTimeout %v, got %v", testTimeout, r.testTimeout)
		}
		if r.buildTimeout != buildTimeout {
			t.Errorf("expected buildTimeout %v, got %v", buildTimeout, r.buildTimeout)
		}
	})
}

func TestDetectProjectType(t *testing.T) {
	r := NewBuildToolRunner()

	// Create a temp directory for testing
	tempDir, err := os.MkdirTemp("", "buildtools_test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	tests := []struct {
		name       string
		markerFile string
		expected   ProjectType
	}{
		{
			name:       "Rust project",
			markerFile: "Cargo.toml",
			expected:   ProjectTypeRust,
		},
		{
			name:       "Node.js project",
			markerFile: "package.json",
			expected:   ProjectTypeNode,
		},
		{
			name:       "Go project",
			markerFile: "go.mod",
			expected:   ProjectTypeGo,
		},
		{
			name:       "Python pyproject.toml project",
			markerFile: "pyproject.toml",
			expected:   ProjectTypePython,
		},
		{
			name:       "Makefile project",
			markerFile: "Makefile",
			expected:   ProjectTypeMake,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create project directory
			projectDir := filepath.Join(tempDir, tt.name)
			if err := os.MkdirAll(projectDir, 0755); err != nil {
				t.Fatalf("failed to create project dir: %v", err)
			}

			// Create marker file
			markerPath := filepath.Join(projectDir, tt.markerFile)
			if err := os.WriteFile(markerPath, []byte(""), 0644); err != nil {
				t.Fatalf("failed to create marker file: %v", err)
			}

			got := r.DetectProjectType(projectDir)
			if got != tt.expected {
				t.Errorf("expected %v, got %v", tt.expected, got)
			}
		})
	}

	t.Run("Python requirements.txt fallback", func(t *testing.T) {
		projectDir := filepath.Join(tempDir, "python_requirements")
		if err := os.MkdirAll(projectDir, 0755); err != nil {
			t.Fatalf("failed to create project dir: %v", err)
		}

		// Create requirements.txt (fallback marker)
		markerPath := filepath.Join(projectDir, "requirements.txt")
		if err := os.WriteFile(markerPath, []byte(""), 0644); err != nil {
			t.Fatalf("failed to create marker file: %v", err)
		}

		got := r.DetectProjectType(projectDir)
		if got != ProjectTypePython {
			t.Errorf("expected %v, got %v", ProjectTypePython, got)
		}
	})

	t.Run("unknown project type", func(t *testing.T) {
		projectDir := filepath.Join(tempDir, "unknown")
		if err := os.MkdirAll(projectDir, 0755); err != nil {
			t.Fatalf("failed to create project dir: %v", err)
		}

		got := r.DetectProjectType(projectDir)
		if got != ProjectTypeUnknown {
			t.Errorf("expected %v, got %v", ProjectTypeUnknown, got)
		}
	})
}

func TestDetectTestCommand(t *testing.T) {
	r := NewBuildToolRunner()

	// Create a temp directory for testing
	tempDir, err := os.MkdirTemp("", "buildtools_test_cmd")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	tests := []struct {
		name         string
		markerFile   string
		expectedCmd  string
	}{
		{"Rust", "Cargo.toml", "cargo test"},
		{"Node.js", "package.json", "npm test"},
		{"Go", "go.mod", "go test ./..."},
		{"Python", "pyproject.toml", "pytest"},
		{"Make", "Makefile", "make test"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			projectDir := filepath.Join(tempDir, "test_cmd_"+tt.name)
			if err := os.MkdirAll(projectDir, 0755); err != nil {
				t.Fatalf("failed to create project dir: %v", err)
			}

			markerPath := filepath.Join(projectDir, tt.markerFile)
			if err := os.WriteFile(markerPath, []byte(""), 0644); err != nil {
				t.Fatalf("failed to create marker file: %v", err)
			}

			got := r.DetectTestCommand(projectDir)
			if got != tt.expectedCmd {
				t.Errorf("expected %q, got %q", tt.expectedCmd, got)
			}
		})
	}

	t.Run("unknown project returns empty string", func(t *testing.T) {
		projectDir := filepath.Join(tempDir, "unknown_test_cmd")
		if err := os.MkdirAll(projectDir, 0755); err != nil {
			t.Fatalf("failed to create project dir: %v", err)
		}

		got := r.DetectTestCommand(projectDir)
		if got != "" {
			t.Errorf("expected empty string, got %q", got)
		}
	})
}

func TestDetectBuildCommand(t *testing.T) {
	r := NewBuildToolRunner()

	// Create a temp directory for testing
	tempDir, err := os.MkdirTemp("", "buildtools_build_cmd")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	tests := []struct {
		name        string
		markerFile  string
		expectedCmd string
	}{
		{"Rust", "Cargo.toml", "cargo build"},
		{"Node.js", "package.json", "npm run build"},
		{"Go", "go.mod", "go build ./..."},
		{"Python", "pyproject.toml", ""}, // Python has no build step
		{"Make", "Makefile", "make"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			projectDir := filepath.Join(tempDir, "build_cmd_"+tt.name)
			if err := os.MkdirAll(projectDir, 0755); err != nil {
				t.Fatalf("failed to create project dir: %v", err)
			}

			markerPath := filepath.Join(projectDir, tt.markerFile)
			if err := os.WriteFile(markerPath, []byte(""), 0644); err != nil {
				t.Fatalf("failed to create marker file: %v", err)
			}

			got := r.DetectBuildCommand(projectDir)
			if got != tt.expectedCmd {
				t.Errorf("expected %q, got %q", tt.expectedCmd, got)
			}
		})
	}
}

func TestRunCommand(t *testing.T) {
	r := NewBuildToolRunner()

	t.Run("successful command", func(t *testing.T) {
		tempDir, err := os.MkdirTemp("", "buildtools_run")
		if err != nil {
			t.Fatalf("failed to create temp dir: %v", err)
		}
		defer os.RemoveAll(tempDir)

		ctx := context.Background()
		result, err := r.RunCommand(ctx, tempDir, "echo hello")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if !result.Success {
			t.Errorf("expected success, got failure: %s", result.Error)
		}
		if result.Output != "hello\n" {
			t.Errorf("expected output 'hello\\n', got %q", result.Output)
		}
	})

	t.Run("failed command", func(t *testing.T) {
		tempDir, err := os.MkdirTemp("", "buildtools_run_fail")
		if err != nil {
			t.Fatalf("failed to create temp dir: %v", err)
		}
		defer os.RemoveAll(tempDir)

		ctx := context.Background()
		result, err := r.RunCommand(ctx, tempDir, "exit 1")
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if result.Success {
			t.Error("expected failure, got success")
		}
		if result.ExitCode != 1 {
			t.Errorf("expected exit code 1, got %d", result.ExitCode)
		}
	})
}

func TestRunTests(t *testing.T) {
	r := NewBuildToolRunner()

	t.Run("unknown project type", func(t *testing.T) {
		tempDir, err := os.MkdirTemp("", "buildtools_test_unknown")
		if err != nil {
			t.Fatalf("failed to create temp dir: %v", err)
		}
		defer os.RemoveAll(tempDir)

		ctx := context.Background()
		result, err := r.RunTests(ctx, tempDir)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if result.Success {
			t.Error("expected failure for unknown project type")
		}
		if result.ExitCode != -1 {
			t.Errorf("expected exit code -1, got %d", result.ExitCode)
		}
	})
}

func TestRunBuild(t *testing.T) {
	r := NewBuildToolRunner()

	t.Run("unknown project type", func(t *testing.T) {
		tempDir, err := os.MkdirTemp("", "buildtools_build_unknown")
		if err != nil {
			t.Fatalf("failed to create temp dir: %v", err)
		}
		defer os.RemoveAll(tempDir)

		ctx := context.Background()
		result, err := r.RunBuild(ctx, tempDir)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if result.Success {
			t.Error("expected failure for unknown project type")
		}
	})

	t.Run("Python project returns success without build", func(t *testing.T) {
		tempDir, err := os.MkdirTemp("", "buildtools_build_python")
		if err != nil {
			t.Fatalf("failed to create temp dir: %v", err)
		}
		defer os.RemoveAll(tempDir)

		// Create pyproject.toml marker
		markerPath := filepath.Join(tempDir, "pyproject.toml")
		if err := os.WriteFile(markerPath, []byte(""), 0644); err != nil {
			t.Fatalf("failed to create marker file: %v", err)
		}

		ctx := context.Background()
		result, err := r.RunBuild(ctx, tempDir)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if !result.Success {
			t.Error("expected success for Python project (no build step)")
		}
		if result.ExitCode != 0 {
			t.Errorf("expected exit code 0, got %d", result.ExitCode)
		}
	})
}

func TestBuildResult(t *testing.T) {
	r := NewBuildToolRunner()

	t.Run("RunTestsWithInfo returns project info", func(t *testing.T) {
		tempDir, err := os.MkdirTemp("", "buildtools_info")
		if err != nil {
			t.Fatalf("failed to create temp dir: %v", err)
		}
		defer os.RemoveAll(tempDir)

		ctx := context.Background()
		result, err := r.RunTestsWithInfo(ctx, tempDir)
		if err != nil {
			t.Fatalf("unexpected error: %v", err)
		}
		if result.ProjectType != ProjectTypeUnknown {
			t.Errorf("expected ProjectTypeUnknown, got %v", result.ProjectType)
		}
		if result.Command != "" {
			t.Errorf("expected empty command, got %q", result.Command)
		}
	})
}

func TestMarkerFiles(t *testing.T) {
	// Verify all expected marker files are configured
	expectedMarkers := map[ProjectType]string{
		ProjectTypeRust:   "Cargo.toml",
		ProjectTypeNode:   "package.json",
		ProjectTypeGo:     "go.mod",
		ProjectTypePython: "pyproject.toml",
		ProjectTypeMake:   "Makefile",
	}

	for projectType, expectedMarker := range expectedMarkers {
		if marker, ok := MarkerFiles[projectType]; !ok {
			t.Errorf("missing marker file for %v", projectType)
		} else if marker != expectedMarker {
			t.Errorf("expected marker %q for %v, got %q", expectedMarker, projectType, marker)
		}
	}
}

func TestDefaultTimeouts(t *testing.T) {
	if DefaultTestTimeout != 5*time.Minute {
		t.Errorf("expected DefaultTestTimeout to be 5 minutes, got %v", DefaultTestTimeout)
	}
	if DefaultBuildTimeout != 10*time.Minute {
		t.Errorf("expected DefaultBuildTimeout to be 10 minutes, got %v", DefaultBuildTimeout)
	}
}
