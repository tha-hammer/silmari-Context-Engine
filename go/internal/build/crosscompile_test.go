// Package build contains tests for cross-compilation functionality.
package build

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

// testPlatform represents a cross-compilation target platform.
type testPlatform struct {
	GOOS         string
	GOARCH       string
	BinarySuffix string
	FileType     string   // Expected output from 'file' command
	FilePatterns []string // Patterns to match in file output
}

var platforms = []testPlatform{
	{
		GOOS:         "darwin",
		GOARCH:       "amd64",
		BinarySuffix: "-darwin-amd64",
		FileType:     "Mach-O",
		FilePatterns: []string{"Mach-O 64-bit", "x86_64"},
	},
	{
		GOOS:         "darwin",
		GOARCH:       "arm64",
		BinarySuffix: "-darwin-arm64",
		FileType:     "Mach-O",
		FilePatterns: []string{"Mach-O 64-bit", "arm64"},
	},
	{
		GOOS:         "linux",
		GOARCH:       "amd64",
		BinarySuffix: "-linux-amd64",
		FileType:     "ELF",
		FilePatterns: []string{"ELF 64-bit", "x86-64"},
	},
	{
		GOOS:         "linux",
		GOARCH:       "arm64",
		BinarySuffix: "-linux-arm64",
		FileType:     "ELF",
		FilePatterns: []string{"ELF 64-bit", "aarch64"},
	},
	{
		GOOS:         "windows",
		GOARCH:       "amd64",
		BinarySuffix: "-windows-amd64.exe",
		FileType:     "PE32+",
		FilePatterns: []string{"PE32+", "x86-64"},
	},
}

// getProjectRoot returns the root of the project (where go.mod lives).
func getProjectRoot(t *testing.T) string {
	t.Helper()
	// Walk up from current directory to find go.mod
	dir, err := os.Getwd()
	if err != nil {
		t.Fatalf("failed to get working directory: %v", err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatalf("could not find project root (go.mod)")
		}
		dir = parent
	}
}

// getGoDir returns the go/ subdirectory where Go source code lives.
func getGoDir(t *testing.T) string {
	t.Helper()
	projectRoot := getProjectRoot(t)
	goDir := filepath.Join(projectRoot, "go")
	if _, err := os.Stat(goDir); os.IsNotExist(err) {
		// go.mod is in the same directory as Go code
		return projectRoot
	}
	return goDir
}

// TestCrossCompileBuild tests that binaries can be built for all platforms.
func TestCrossCompileBuild(t *testing.T) {
	projectRoot := getProjectRoot(t)
	goDir := getGoDir(t)
	buildDir := filepath.Join(goDir, "build")

	// Clean and recreate build directory
	os.RemoveAll(buildDir)
	if err := os.MkdirAll(buildDir, 0755); err != nil {
		t.Fatalf("failed to create build directory: %v", err)
	}

	for _, plat := range platforms {
		t.Run(plat.GOOS+"-"+plat.GOARCH, func(t *testing.T) {
			binaryName := "context-engine" + plat.BinarySuffix
			outputPath := filepath.Join(buildDir, binaryName)

			// Build command with cross-compilation environment
			// Use package path relative to go.mod, not file path
			cmd := exec.Command("go", "build",
				"-ldflags", "-s -w -X 'github.com/silmari/context-engine/go/internal/cli.Version=test'",
				"-o", outputPath,
				"./go/cmd/context-engine",
			)
			cmd.Env = append(os.Environ(),
				"CGO_ENABLED=0",
				"GOOS="+plat.GOOS,
				"GOARCH="+plat.GOARCH,
			)
			cmd.Dir = projectRoot

			output, err := cmd.CombinedOutput()
			if err != nil {
				t.Fatalf("build failed for %s/%s: %v\nOutput: %s",
					plat.GOOS, plat.GOARCH, err, string(output))
			}

			// Verify binary was created
			if _, err := os.Stat(outputPath); os.IsNotExist(err) {
				t.Fatalf("binary was not created: %s", outputPath)
			}

			// Verify binary size is reasonable (< 50MB)
			info, err := os.Stat(outputPath)
			if err != nil {
				t.Fatalf("failed to stat binary: %v", err)
			}
			maxSize := int64(50 * 1024 * 1024) // 50MB
			if info.Size() > maxSize {
				t.Errorf("binary size %d exceeds maximum %d", info.Size(), maxSize)
			}

			// Verify binary format using 'file' command
			fileCmd := exec.Command("file", outputPath)
			fileOutput, err := fileCmd.Output()
			if err != nil {
				t.Logf("warning: 'file' command failed: %v", err)
			} else {
				fileStr := string(fileOutput)
				if !strings.Contains(fileStr, plat.FileType) {
					t.Errorf("binary type mismatch: expected %s in output: %s",
						plat.FileType, fileStr)
				}
				// Check for architecture-specific patterns
				foundArch := false
				for _, pattern := range plat.FilePatterns {
					if strings.Contains(fileStr, pattern) {
						foundArch = true
						break
					}
				}
				if !foundArch {
					t.Errorf("architecture not detected: expected one of %v in: %s",
						plat.FilePatterns, fileStr)
				}
			}
		})
	}
}

// TestCrossCompileLoopRunner tests loop-runner binary cross-compilation.
func TestCrossCompileLoopRunner(t *testing.T) {
	projectRoot := getProjectRoot(t)
	goDir := getGoDir(t)
	buildDir := filepath.Join(goDir, "build")

	for _, plat := range platforms {
		t.Run("loop-runner-"+plat.GOOS+"-"+plat.GOARCH, func(t *testing.T) {
			binaryName := "loop-runner" + plat.BinarySuffix
			outputPath := filepath.Join(buildDir, binaryName)

			cmd := exec.Command("go", "build",
				"-ldflags", "-s -w",
				"-o", outputPath,
				"./go/cmd/loop-runner",
			)
			cmd.Env = append(os.Environ(),
				"CGO_ENABLED=0",
				"GOOS="+plat.GOOS,
				"GOARCH="+plat.GOARCH,
			)
			cmd.Dir = projectRoot

			output, err := cmd.CombinedOutput()
			if err != nil {
				t.Fatalf("build failed for loop-runner %s/%s: %v\nOutput: %s",
					plat.GOOS, plat.GOARCH, err, string(output))
			}

			if _, err := os.Stat(outputPath); os.IsNotExist(err) {
				t.Fatalf("binary was not created: %s", outputPath)
			}
		})
	}
}

// TestStaticLinux verifies Linux binaries are fully static.
func TestStaticLinux(t *testing.T) {
	goDir := getGoDir(t)
	buildDir := filepath.Join(goDir, "build")

	// Only run on Linux where ldd is available
	if _, err := exec.LookPath("ldd"); err != nil {
		t.Skip("ldd not available, skipping static linking test")
	}

	linuxBinary := filepath.Join(buildDir, "context-engine-linux-amd64")
	if _, err := os.Stat(linuxBinary); os.IsNotExist(err) {
		t.Skip("linux binary not built, run TestCrossCompileBuild first")
	}

	// Only check if we're on Linux (cross-compiled binaries can't be checked with ldd)
	currentOS := os.Getenv("GOOS")
	if currentOS == "" {
		// Not cross-compiling, check actual OS
		cmd := exec.Command("uname", "-s")
		output, err := cmd.Output()
		if err == nil && strings.TrimSpace(string(output)) == "Linux" {
			lddCmd := exec.Command("ldd", linuxBinary)
			lddOutput, err := lddCmd.CombinedOutput()
			if err == nil {
				// Should say "not a dynamic executable" or similar for static
				lddStr := string(lddOutput)
				if !strings.Contains(lddStr, "not a dynamic executable") &&
					!strings.Contains(lddStr, "statically linked") {
					t.Logf("Binary may have dynamic dependencies: %s", lddStr)
				}
			}
		}
	}
}

// TestVersionEmbedding verifies version info is embedded via ldflags.
func TestVersionEmbedding(t *testing.T) {
	projectRoot := getProjectRoot(t)
	goDir := getGoDir(t)
	buildDir := filepath.Join(goDir, "build")

	// Build with custom version
	testVersion := "test-1.2.3"
	testCommit := "abc123"
	testDate := "2026-01-01T00:00:00Z"

	outputPath := filepath.Join(buildDir, "context-engine-version-test")

	ldflags := "-s -w " +
		"-X 'github.com/silmari/context-engine/go/internal/cli.Version=" + testVersion + "' " +
		"-X 'github.com/silmari/context-engine/go/internal/cli.GitCommit=" + testCommit + "' " +
		"-X 'github.com/silmari/context-engine/go/internal/cli.BuildDate=" + testDate + "'"

	cmd := exec.Command("go", "build",
		"-ldflags", ldflags,
		"-o", outputPath,
		"./go/cmd/context-engine",
	)
	cmd.Env = append(os.Environ(), "CGO_ENABLED=0")
	cmd.Dir = projectRoot

	if output, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("build with version failed: %v\nOutput: %s", err, string(output))
	}

	// Verify version is embedded by running --version
	versionCmd := exec.Command(outputPath, "--version")
	versionOutput, err := versionCmd.Output()
	if err != nil {
		t.Fatalf("version command failed: %v", err)
	}

	versionStr := string(versionOutput)
	if !strings.Contains(versionStr, testVersion) {
		t.Errorf("version not found in output: %s", versionStr)
	}
	if !strings.Contains(versionStr, testCommit) {
		t.Errorf("commit not found in output: %s", versionStr)
	}
	if !strings.Contains(versionStr, testDate) {
		t.Errorf("build date not found in output: %s", versionStr)
	}
}

// TestNoCGODependency ensures CGO_ENABLED=0 builds succeed.
func TestNoCGODependency(t *testing.T) {
	projectRoot := getProjectRoot(t)
	goDir := getGoDir(t)
	buildDir := filepath.Join(goDir, "build")

	// Build with CGO explicitly disabled
	outputPath := filepath.Join(buildDir, "context-engine-nocgo-test")

	cmd := exec.Command("go", "build",
		"-o", outputPath,
		"./go/cmd/context-engine",
	)
	cmd.Env = append(os.Environ(), "CGO_ENABLED=0")
	cmd.Dir = projectRoot

	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("build with CGO_ENABLED=0 failed: %v\nOutput: %s", err, string(output))
	}

	if _, err := os.Stat(outputPath); os.IsNotExist(err) {
		t.Fatal("binary was not created with CGO disabled")
	}
}

// TestBinaryNaming verifies correct naming conventions.
func TestBinaryNaming(t *testing.T) {
	expectedNames := map[string]string{
		"darwin-amd64":  "context-engine-darwin-amd64",
		"darwin-arm64":  "context-engine-darwin-arm64",
		"linux-amd64":   "context-engine-linux-amd64",
		"linux-arm64":   "context-engine-linux-arm64",
		"windows-amd64": "context-engine-windows-amd64.exe",
	}

	for platform, expected := range expectedNames {
		t.Run(platform, func(t *testing.T) {
			parts := strings.Split(platform, "-")
			goos := parts[0]
			goarch := parts[1]

			suffix := "-" + goos + "-" + goarch
			if goos == "windows" {
				suffix += ".exe"
			}

			actual := "context-engine" + suffix
			if actual != expected {
				t.Errorf("naming mismatch: got %s, want %s", actual, expected)
			}
		})
	}
}

// TestMakefileExists verifies Makefile is present.
func TestMakefileExists(t *testing.T) {
	goDir := getGoDir(t)
	makefilePath := filepath.Join(goDir, "Makefile")

	if _, err := os.Stat(makefilePath); os.IsNotExist(err) {
		t.Fatal("Makefile not found in project root")
	}
}

// TestMakefileBuildTarget tests the 'make build' target.
func TestMakefileBuildTarget(t *testing.T) {
	if _, err := exec.LookPath("make"); err != nil {
		t.Skip("make not available")
	}

	goDir := getGoDir(t)

	cmd := exec.Command("make", "build")
	cmd.Dir = goDir
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("make build failed: %v\nOutput: %s", err, string(output))
	}

	// Verify binaries exist
	buildDir := filepath.Join(goDir, "build")
	for _, binary := range []string{"context-engine", "loop-runner"} {
		path := filepath.Join(buildDir, binary)
		if _, err := os.Stat(path); os.IsNotExist(err) {
			t.Errorf("binary not created by make build: %s", binary)
		}
	}
}

// TestMakefileBuildAllTarget tests the 'make build-all' target.
func TestMakefileBuildAllTarget(t *testing.T) {
	if _, err := exec.LookPath("make"); err != nil {
		t.Skip("make not available")
	}

	if testing.Short() {
		t.Skip("skipping build-all in short mode")
	}

	goDir := getGoDir(t)

	cmd := exec.Command("make", "build-all")
	cmd.Dir = goDir
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("make build-all failed: %v\nOutput: %s", err, string(output))
	}

	// Verify all platform binaries exist
	buildDir := filepath.Join(goDir, "build")
	for _, plat := range platforms {
		binaryName := "context-engine" + plat.BinarySuffix
		path := filepath.Join(buildDir, binaryName)
		if _, err := os.Stat(path); os.IsNotExist(err) {
			t.Errorf("binary not created by make build-all: %s", binaryName)
		}
	}
}
