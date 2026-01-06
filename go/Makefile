# Makefile for Context Engine Go binaries
# Supports cross-compilation for all major platforms

# Version information
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
GIT_COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_DATE ?= $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

# Build paths
MODULE := github.com/silmari/context-engine
CMD_DIR := ./cmd
BUILD_DIR := ./build
INTERNAL_CLI := $(MODULE)/go/internal/cli

# Ldflags for version information
LDFLAGS := -ldflags "-s -w \
	-X '$(INTERNAL_CLI).Version=$(VERSION)' \
	-X '$(INTERNAL_CLI).GitCommit=$(GIT_COMMIT)' \
	-X '$(INTERNAL_CLI).BuildDate=$(BUILD_DATE)'"

# Binary names
CONTEXT_ENGINE := context-engine
LOOP_RUNNER := loop-runner

# All platforms for cross-compilation
PLATFORMS := darwin-amd64 darwin-arm64 linux-amd64 linux-arm64 windows-amd64

# Default target
.PHONY: all
all: build

# Build for current platform
.PHONY: build
build: $(BUILD_DIR)/$(CONTEXT_ENGINE) $(BUILD_DIR)/$(LOOP_RUNNER)

$(BUILD_DIR)/$(CONTEXT_ENGINE):
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 go build $(LDFLAGS) -o $@ $(CMD_DIR)/context-engine

$(BUILD_DIR)/$(LOOP_RUNNER):
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 go build $(LDFLAGS) -o $@ $(CMD_DIR)/loop-runner

# Cross-compilation targets
# macOS Intel (x86-64)
.PHONY: build-darwin-amd64
build-darwin-amd64:
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(CONTEXT_ENGINE)-darwin-amd64 $(CMD_DIR)/context-engine
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(LOOP_RUNNER)-darwin-amd64 $(CMD_DIR)/loop-runner

# macOS Apple Silicon (ARM64)
.PHONY: build-darwin-arm64
build-darwin-arm64:
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(CONTEXT_ENGINE)-darwin-arm64 $(CMD_DIR)/context-engine
	CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(LOOP_RUNNER)-darwin-arm64 $(CMD_DIR)/loop-runner

# Linux x86-64
.PHONY: build-linux-amd64
build-linux-amd64:
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(CONTEXT_ENGINE)-linux-amd64 $(CMD_DIR)/context-engine
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(LOOP_RUNNER)-linux-amd64 $(CMD_DIR)/loop-runner

# Linux ARM64
.PHONY: build-linux-arm64
build-linux-arm64:
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(CONTEXT_ENGINE)-linux-arm64 $(CMD_DIR)/context-engine
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(LOOP_RUNNER)-linux-arm64 $(CMD_DIR)/loop-runner

# Windows x86-64
.PHONY: build-windows-amd64
build-windows-amd64:
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(CONTEXT_ENGINE)-windows-amd64.exe $(CMD_DIR)/context-engine
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o $(BUILD_DIR)/$(LOOP_RUNNER)-windows-amd64.exe $(CMD_DIR)/loop-runner

# Build all platforms
.PHONY: build-all
build-all: build-darwin-amd64 build-darwin-arm64 build-linux-amd64 build-linux-arm64 build-windows-amd64

# Run tests
.PHONY: test
test:
	go test -v ./...

# Run tests with coverage
.PHONY: test-coverage
test-coverage:
	go test -v -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# Release builds all platforms
.PHONY: release
release: build-all
	@echo "Release binaries built in $(BUILD_DIR)/"
	@ls -la $(BUILD_DIR)/

# Install to PREFIX (default /usr/local)
PREFIX ?= /usr/local
BINDIR := $(PREFIX)/bin

.PHONY: install
install: build
	@echo "Installing to $(BINDIR)..."
	install -d $(BINDIR)
	install -m 755 $(BUILD_DIR)/$(CONTEXT_ENGINE) $(BINDIR)/
	install -m 755 $(BUILD_DIR)/$(LOOP_RUNNER) $(BINDIR)/
	@echo ""
	@echo "✓ Installed $(CONTEXT_ENGINE) to $(BINDIR)/$(CONTEXT_ENGINE)"
	@echo "✓ Installed $(LOOP_RUNNER) to $(BINDIR)/$(LOOP_RUNNER)"
	@echo ""
	@echo "Run '$(CONTEXT_ENGINE) --version' to verify installation."

# Install to user local directory
.PHONY: install-user
install-user: build
	@echo "Installing to $(HOME)/.local/bin..."
	install -d $(HOME)/.local/bin
	install -m 755 $(BUILD_DIR)/$(CONTEXT_ENGINE) $(HOME)/.local/bin/
	install -m 755 $(BUILD_DIR)/$(LOOP_RUNNER) $(HOME)/.local/bin/
	@echo ""
	@echo "✓ Installed $(CONTEXT_ENGINE) to $(HOME)/.local/bin/$(CONTEXT_ENGINE)"
	@echo "✓ Installed $(LOOP_RUNNER) to $(HOME)/.local/bin/$(LOOP_RUNNER)"
	@echo ""
	@echo "Make sure $(HOME)/.local/bin is in your PATH."
	@echo ""
	@echo "For bash (~/.bashrc):"
	@echo '  export PATH="$$HOME/.local/bin:$$PATH"'
	@echo ""
	@echo "For zsh (~/.zshrc):"
	@echo '  export PATH="$$HOME/.local/bin:$$PATH"'
	@echo ""
	@echo "Then reload your shell or run: source ~/.bashrc (or ~/.zshrc)"

# Uninstall from PREFIX
.PHONY: uninstall
uninstall:
	@echo "Uninstalling from $(BINDIR)..."
	rm -f $(BINDIR)/$(CONTEXT_ENGINE)
	rm -f $(BINDIR)/$(LOOP_RUNNER)
	@echo "✓ Uninstalled $(CONTEXT_ENGINE) and $(LOOP_RUNNER)"

# Uninstall from user local directory
.PHONY: uninstall-user
uninstall-user:
	@echo "Uninstalling from $(HOME)/.local/bin..."
	rm -f $(HOME)/.local/bin/$(CONTEXT_ENGINE)
	rm -f $(HOME)/.local/bin/$(LOOP_RUNNER)
	@echo "✓ Uninstalled $(CONTEXT_ENGINE) and $(LOOP_RUNNER) from user directory"

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
	rm -f coverage.out coverage.html

# Show version information
.PHONY: version
version:
	@echo "Version: $(VERSION)"
	@echo "Git Commit: $(GIT_COMMIT)"
	@echo "Build Date: $(BUILD_DATE)"

# Verify builds for all platforms (checks binaries exist and have correct format)
.PHONY: verify-builds
verify-builds: build-all
	@echo "Verifying builds..."
	@# macOS Intel
	@file $(BUILD_DIR)/$(CONTEXT_ENGINE)-darwin-amd64 | grep -q "Mach-O 64-bit" && echo "✓ darwin-amd64: OK" || echo "✗ darwin-amd64: FAILED"
	@# macOS ARM64
	@file $(BUILD_DIR)/$(CONTEXT_ENGINE)-darwin-arm64 | grep -q "Mach-O 64-bit" && echo "✓ darwin-arm64: OK" || echo "✗ darwin-arm64: FAILED"
	@# Linux x86-64
	@file $(BUILD_DIR)/$(CONTEXT_ENGINE)-linux-amd64 | grep -q "ELF 64-bit" && echo "✓ linux-amd64: OK" || echo "✗ linux-amd64: FAILED"
	@# Linux ARM64
	@file $(BUILD_DIR)/$(CONTEXT_ENGINE)-linux-arm64 | grep -q "ELF 64-bit" && echo "✓ linux-arm64: OK" || echo "✗ linux-arm64: FAILED"
	@# Windows
	@file $(BUILD_DIR)/$(CONTEXT_ENGINE)-windows-amd64.exe | grep -q "PE32+" && echo "✓ windows-amd64: OK" || echo "✗ windows-amd64: FAILED"

# Help
.PHONY: help
help:
	@echo "Context Engine Makefile"
	@echo ""
	@echo "Build targets:"
	@echo "  all                Default target, same as build"
	@echo "  build              Build for current platform"
	@echo "  build-all          Build for all platforms"
	@echo "  release            Build release binaries for all platforms"
	@echo "  build-darwin-amd64 Build for macOS Intel"
	@echo "  build-darwin-arm64 Build for macOS Apple Silicon"
	@echo "  build-linux-amd64  Build for Linux x86-64"
	@echo "  build-linux-arm64  Build for Linux ARM64"
	@echo "  build-windows-amd64 Build for Windows x86-64"
	@echo ""
	@echo "Test targets:"
	@echo "  test               Run all tests"
	@echo "  test-coverage      Run tests with coverage report"
	@echo "  verify-builds      Build all and verify binary formats"
	@echo ""
	@echo "Install targets:"
	@echo "  install            Install to PREFIX (default /usr/local)"
	@echo "  install-user       Install to ~/.local/bin (no sudo required)"
	@echo "  uninstall          Remove from PREFIX/bin"
	@echo "  uninstall-user     Remove from ~/.local/bin"
	@echo ""
	@echo "Other targets:"
	@echo "  clean              Remove build artifacts"
	@echo "  version            Show version information"
	@echo "  help               Show this help"
	@echo ""
	@echo "Variables:"
	@echo "  VERSION=$(VERSION)"
	@echo "  PREFIX=$(PREFIX)"
	@echo "  BINDIR=$(BINDIR)"
	@echo ""
	@echo "Examples:"
	@echo "  make build                  # Build for current platform"
	@echo "  make install-user           # Install to ~/.local/bin (no sudo)"
	@echo "  make install                # Install to /usr/local/bin (needs sudo)"
	@echo "  PREFIX=/opt make install    # Install to /opt/bin"
