// Package build contains tests for installation functionality.
package build

import (
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// TestMakefileReleaseTarget tests the 'make release' target.
func TestMakefileReleaseTarget(t *testing.T) {
	if _, err := exec.LookPath("make"); err != nil {
		t.Skip("make not available")
	}

	if testing.Short() {
		t.Skip("skipping release in short mode")
	}

	goDir := getGoDir(t)

	cmd := exec.Command("make", "release")
	cmd.Dir = goDir
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("make release failed: %v\nOutput: %s", err, string(output))
	}

	// Verify all platform binaries exist
	buildDir := filepath.Join(goDir, "build")
	for _, plat := range platforms {
		binaryName := "context-engine" + plat.BinarySuffix
		path := filepath.Join(buildDir, binaryName)
		if _, err := os.Stat(path); os.IsNotExist(err) {
			t.Errorf("binary not created by make release: %s", binaryName)
		}
	}
}

// TestMakefileInstallUserTarget tests the 'make install-user' target.
func TestMakefileInstallUserTarget(t *testing.T) {
	if _, err := exec.LookPath("make"); err != nil {
		t.Skip("make not available")
	}

	goDir := getGoDir(t)

	// Use a temporary directory as HOME to avoid polluting actual ~/.local
	tempHome, err := os.MkdirTemp("", "test-home-*")
	if err != nil {
		t.Fatalf("failed to create temp home: %v", err)
	}
	defer os.RemoveAll(tempHome)

	cmd := exec.Command("make", "install-user")
	cmd.Dir = goDir
	cmd.Env = append(os.Environ(), "HOME="+tempHome)
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("make install-user failed: %v\nOutput: %s", err, string(output))
	}

	// Verify binaries were installed
	localBin := filepath.Join(tempHome, ".local", "bin")
	for _, binary := range []string{"context-engine", "loop-runner"} {
		path := filepath.Join(localBin, binary)
		info, err := os.Stat(path)
		if os.IsNotExist(err) {
			t.Errorf("binary not installed: %s", binary)
			continue
		}

		// Verify permissions are 755
		mode := info.Mode().Perm()
		if mode != 0755 {
			t.Errorf("incorrect permissions for %s: got %o, want 0755", binary, mode)
		}
	}

	// Verify output contains PATH instructions
	outputStr := string(output)
	if !strings.Contains(outputStr, ".local/bin") {
		t.Error("install-user output should mention .local/bin")
	}
	if !strings.Contains(outputStr, "PATH") {
		t.Error("install-user output should mention PATH")
	}
	if !strings.Contains(outputStr, ".bashrc") {
		t.Error("install-user output should mention .bashrc")
	}
	if !strings.Contains(outputStr, ".zshrc") {
		t.Error("install-user output should mention .zshrc")
	}
}

// TestMakefileInstallWithPrefix tests installation with custom PREFIX.
func TestMakefileInstallWithPrefix(t *testing.T) {
	if _, err := exec.LookPath("make"); err != nil {
		t.Skip("make not available")
	}

	goDir := getGoDir(t)

	// Use a temporary directory as PREFIX
	tempPrefix, err := os.MkdirTemp("", "test-prefix-*")
	if err != nil {
		t.Fatalf("failed to create temp prefix: %v", err)
	}
	defer os.RemoveAll(tempPrefix)

	cmd := exec.Command("make", "install", "PREFIX="+tempPrefix)
	cmd.Dir = goDir
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("make install failed: %v\nOutput: %s", err, string(output))
	}

	// Verify binaries were installed
	binDir := filepath.Join(tempPrefix, "bin")
	for _, binary := range []string{"context-engine", "loop-runner"} {
		path := filepath.Join(binDir, binary)
		info, err := os.Stat(path)
		if os.IsNotExist(err) {
			t.Errorf("binary not installed: %s", binary)
			continue
		}

		// Verify permissions are 755
		mode := info.Mode().Perm()
		if mode != 0755 {
			t.Errorf("incorrect permissions for %s: got %o, want 0755", binary, mode)
		}

		// Verify binary is executable and runs
		versionCmd := exec.Command(path, "--version")
		if _, err := versionCmd.Output(); err != nil {
			t.Errorf("installed binary %s failed to run --version: %v", binary, err)
		}
	}

	// Verify post-install messages
	outputStr := string(output)
	if !strings.Contains(outputStr, "Installed") {
		t.Error("install output should contain 'Installed' message")
	}
}

// TestMakefileUninstallUserTarget tests the 'make uninstall-user' target.
func TestMakefileUninstallUserTarget(t *testing.T) {
	if _, err := exec.LookPath("make"); err != nil {
		t.Skip("make not available")
	}

	goDir := getGoDir(t)

	// Use a temporary directory as HOME
	tempHome, err := os.MkdirTemp("", "test-home-uninstall-*")
	if err != nil {
		t.Fatalf("failed to create temp home: %v", err)
	}
	defer os.RemoveAll(tempHome)

	// First install
	installCmd := exec.Command("make", "install-user")
	installCmd.Dir = goDir
	installCmd.Env = append(os.Environ(), "HOME="+tempHome)
	if _, err := installCmd.CombinedOutput(); err != nil {
		t.Fatalf("make install-user failed: %v", err)
	}

	// Verify installation
	localBin := filepath.Join(tempHome, ".local", "bin")
	if _, err := os.Stat(filepath.Join(localBin, "context-engine")); os.IsNotExist(err) {
		t.Fatal("binary not installed before uninstall test")
	}

	// Now uninstall
	uninstallCmd := exec.Command("make", "uninstall-user")
	uninstallCmd.Dir = goDir
	uninstallCmd.Env = append(os.Environ(), "HOME="+tempHome)
	output, err := uninstallCmd.CombinedOutput()
	if err != nil {
		t.Fatalf("make uninstall-user failed: %v\nOutput: %s", err, string(output))
	}

	// Verify binaries were removed
	for _, binary := range []string{"context-engine", "loop-runner"} {
		path := filepath.Join(localBin, binary)
		if _, err := os.Stat(path); !os.IsNotExist(err) {
			t.Errorf("binary not uninstalled: %s", binary)
		}
	}
}

// TestMakefileHelp tests that help shows all expected targets.
func TestMakefileHelp(t *testing.T) {
	if _, err := exec.LookPath("make"); err != nil {
		t.Skip("make not available")
	}

	goDir := getGoDir(t)

	cmd := exec.Command("make", "help")
	cmd.Dir = goDir
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("make help failed: %v\nOutput: %s", err, string(output))
	}

	outputStr := string(output)

	// Check all expected targets are documented
	expectedTargets := []string{
		"all",
		"build",
		"build-all",
		"release",
		"test",
		"test-coverage",
		"verify-builds",
		"install",
		"install-user",
		"uninstall",
		"uninstall-user",
		"clean",
		"version",
		"help",
	}

	for _, target := range expectedTargets {
		if !strings.Contains(outputStr, target) {
			t.Errorf("help output missing target: %s", target)
		}
	}

	// Check variables are shown
	if !strings.Contains(outputStr, "VERSION=") {
		t.Error("help output missing VERSION variable")
	}
	if !strings.Contains(outputStr, "PREFIX=") {
		t.Error("help output missing PREFIX variable")
	}
	if !strings.Contains(outputStr, "BINDIR=") {
		t.Error("help output missing BINDIR variable")
	}
}

// TestMakefileHasPhonyDeclarations tests that all targets have .PHONY declarations.
func TestMakefileHasPhonyDeclarations(t *testing.T) {
	goDir := getGoDir(t)
	makefilePath := filepath.Join(goDir, "Makefile")

	content, err := os.ReadFile(makefilePath)
	if err != nil {
		t.Fatalf("failed to read Makefile: %v", err)
	}

	makefileStr := string(content)

	// Extract all .PHONY declarations
	phonyRe := regexp.MustCompile(`\.PHONY:\s+(\S+)`)
	matches := phonyRe.FindAllStringSubmatch(makefileStr, -1)

	phonyTargets := make(map[string]bool)
	for _, m := range matches {
		phonyTargets[m[1]] = true
	}

	// Check expected targets have .PHONY
	expectedPhony := []string{
		"all",
		"build",
		"build-all",
		"release",
		"test",
		"install",
		"install-user",
		"uninstall",
		"uninstall-user",
		"clean",
		"help",
	}

	for _, target := range expectedPhony {
		if !phonyTargets[target] {
			t.Errorf("target %s missing .PHONY declaration", target)
		}
	}
}

// TestVersionVariableUsesGitDescribe tests VERSION variable format.
func TestVersionVariableUsesGitDescribe(t *testing.T) {
	goDir := getGoDir(t)
	makefilePath := filepath.Join(goDir, "Makefile")

	content, err := os.ReadFile(makefilePath)
	if err != nil {
		t.Fatalf("failed to read Makefile: %v", err)
	}

	makefileStr := string(content)

	// Check git describe is used
	if !strings.Contains(makefileStr, "git describe --tags --always --dirty") {
		t.Error("Makefile should use 'git describe --tags --always --dirty' for VERSION")
	}

	// Check git rev-parse is used for commit
	if !strings.Contains(makefileStr, "git rev-parse --short HEAD") {
		t.Error("Makefile should use 'git rev-parse --short HEAD' for GIT_COMMIT")
	}

	// Check date format is ISO 8601
	if !strings.Contains(makefileStr, "%Y-%m-%dT%H:%M:%SZ") {
		t.Error("Makefile should use ISO 8601 date format")
	}
}

// TestCGODisabledForStaticBuilds tests CGO_ENABLED=0 is used.
func TestCGODisabledForStaticBuilds(t *testing.T) {
	goDir := getGoDir(t)
	makefilePath := filepath.Join(goDir, "Makefile")

	content, err := os.ReadFile(makefilePath)
	if err != nil {
		t.Fatalf("failed to read Makefile: %v", err)
	}

	makefileStr := string(content)

	// Count CGO_ENABLED=0 occurrences - should be used in all build commands
	count := strings.Count(makefileStr, "CGO_ENABLED=0")
	if count < 10 { // At least for: build(2) + darwin(2) + linux(2) + arm64(2) + windows(2)
		t.Errorf("CGO_ENABLED=0 used only %d times, expected at least 10 for static builds", count)
	}
}

// TestBINDIRVariable tests that BINDIR follows $(PREFIX)/bin pattern.
func TestBINDIRVariable(t *testing.T) {
	goDir := getGoDir(t)
	makefilePath := filepath.Join(goDir, "Makefile")

	content, err := os.ReadFile(makefilePath)
	if err != nil {
		t.Fatalf("failed to read Makefile: %v", err)
	}

	makefileStr := string(content)

	// Check BINDIR definition
	if !strings.Contains(makefileStr, "BINDIR := $(PREFIX)/bin") {
		t.Error("Makefile should define BINDIR := $(PREFIX)/bin")
	}
}
