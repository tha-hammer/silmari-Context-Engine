# Phase 05: The system must install compiled Go binaries to /u...

## Requirements

### REQ_004: The system must install compiled Go binaries to /usr/local/b

The system must install compiled Go binaries to /usr/local/bin via Makefile or install script with proper permissions and version embedding

#### REQ_004.1: Implement Makefile with build, install, uninstall, and relea

Implement Makefile with build, install, uninstall, and release targets for compiling Go binaries and managing installation lifecycle

##### Testable Behaviors

1. Makefile exists at project root with .PHONY declarations for all targets
2. build target compiles both context-engine and loop-runner binaries to bin/ directory
3. install target depends on build and copies binaries to $(PREFIX)/bin (default /usr/local)
4. uninstall target removes installed binaries from $(PREFIX)/bin
5. release target builds binaries for darwin/amd64, darwin/arm64, linux/amd64, linux/arm64, windows/amd64
6. clean target removes bin/ directory and all compiled artifacts
7. all target is default and runs build
8. Makefile uses $(BINDIR) = $(PREFIX)/bin pattern for consistent path handling
9. CGO_ENABLED=0 used for static binary compilation in release target
10. Makefile includes help target that documents all available targets

#### REQ_004.2: Embed version information via ldflags using git describe --t

Embed version information via ldflags using git describe --tags to compile version, commit, and build date into binary

##### Testable Behaviors

1. VERSION variable captures git describe --tags --always --dirty output
2. COMMIT variable captures git rev-parse --short HEAD output
3. BUILD_DATE variable captures current timestamp in ISO 8601 format
4. LDFLAGS embeds -X main.version=$(VERSION) for version string
5. LDFLAGS embeds -X main.commit=$(COMMIT) for commit hash
6. LDFLAGS embeds -X main.buildDate=$(BUILD_DATE) for build timestamp
7. main.go declares var version, commit, buildDate string at package level
8. CLI --version flag outputs formatted version info (e.g., 'context-engine v1.2.3 (abc1234) built 2026-01-06')
9. Version info accessible programmatically for logging and debugging
10. Dirty tag suffix appears when working directory has uncommitted changes

#### REQ_004.3: Install context-engine binary (orchestrator) to $(PREFIX)/bi

Install context-engine binary (orchestrator) to $(PREFIX)/bin with 755 permissions using install command

##### Testable Behaviors

1. Binary installed to $(PREFIX)/bin/context-engine (default: /usr/local/bin/context-engine)
2. File permissions set to 755 (rwxr-xr-x) via install -m 755
3. install -d $(BINDIR) creates directory if it doesn't exist
4. Installation fails gracefully with permission error message if user lacks write access
5. Binary is executable immediately after installation (no additional chmod needed)
6. Existing binary is overwritten during reinstall
7. Post-install message confirms installation path
8. which context-engine returns correct path after installation
9. context-engine --version runs successfully after installation

#### REQ_004.4: Install loop-runner binary to $(PREFIX)/bin with 755 permiss

Install loop-runner binary to $(PREFIX)/bin with 755 permissions using install command

##### Testable Behaviors

1. Binary installed to $(PREFIX)/bin/loop-runner (default: /usr/local/bin/loop-runner)
2. File permissions set to 755 (rwxr-xr-x) via install -m 755
3. install -d $(BINDIR) creates directory if it doesn't exist (shared with context-engine)
4. Installation fails gracefully with permission error message if user lacks write access
5. Binary is executable immediately after installation
6. Existing binary is overwritten during reinstall
7. Post-install message confirms installation path
8. which loop-runner returns correct path after installation
9. loop-runner --version runs successfully after installation
10. Both binaries installed atomically in single install target

#### REQ_004.5: Support user-local installation to ~/.local/bin without sudo

Support user-local installation to ~/.local/bin without sudo by allowing PREFIX override and providing shell configuration guidance

##### Testable Behaviors

1. PREFIX=~/.local make install installs to ~/.local/bin without sudo
2. PREFIX=$HOME/.local make install works (expanded path)
3. Installation creates ~/.local/bin if it doesn't exist
4. Post-install message includes PATH configuration instructions
5. Instructions provided for bash (~/.bashrc) and zsh (~/.zshrc)
6. Instructions show: export PATH="$HOME/.local/bin:$PATH"
7. make install-user target provided as shortcut for PREFIX=~/.local make install
8. User installation doesn't conflict with system installation
9. Both binaries installed to same user-local directory
10. Documentation includes troubleshooting for PATH not configured


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed