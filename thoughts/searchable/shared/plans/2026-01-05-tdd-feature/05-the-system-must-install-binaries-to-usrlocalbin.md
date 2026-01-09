# Phase 05: The system must install binaries to /usr/local/bin...

## Requirements

### REQ_004: The system must install binaries to /usr/local/bin via Makef

The system must install binaries to /usr/local/bin via Makefile or install script with support for both system-wide and user-local installation

#### REQ_004.1: Implement Makefile with build, install, uninstall, and relea

Implement Makefile with build, install, uninstall, and release targets for Go binary compilation and distribution

##### Testable Behaviors

1. Makefile defines BINARY_NAME=context-engine and LOOP_BINARY=loop-runner constants
2. Build target compiles ./cmd/orchestrator to bin/$(BINARY_NAME)
3. Build target compiles ./cmd/loop-runner to bin/$(LOOP_BINARY)
4. Install target depends on build target and copies binaries to $(BINDIR)
5. Install target uses 'install -m 755' to set executable permissions
6. Install target creates destination directory with 'install -d $(BINDIR)'
7. Uninstall target removes both binaries from $(BINDIR)
8. Release target cross-compiles for darwin-amd64, darwin-arm64, linux-amd64, linux-arm64, windows-amd64
9. All public targets are marked as .PHONY
10. Build artifacts are placed in bin/ subdirectory
11. CGO_ENABLED=0 is used for static binary compilation in release target

#### REQ_004.2: Create install.sh script for simplified binary installation 

Create install.sh script for simplified binary installation with dependency checking and user feedback

##### Testable Behaviors

1. Script starts with #!/bin/bash shebang and set -e for error handling
2. Script checks for Go compiler presence and displays helpful error if missing
3. Script accepts PREFIX environment variable override
4. Script defaults PREFIX to /usr/local when not set
5. Script detects if sudo is required for installation (checks write permission to BINDIR)
6. Script displays progress messages during build and install phases
7. Script verifies binary existence after build completes
8. Script displays installed binary paths on completion
9. Script provides instructions for PATH configuration if not already set
10. Script exits with non-zero code on any failure
11. Script supports --help flag showing usage information
12. Script supports --prefix flag as alternative to environment variable

#### REQ_004.3: Support configurable PREFIX for installation directory defau

Support configurable PREFIX for installation directory defaulting to /usr/local with environment variable and command-line overrides

##### Testable Behaviors

1. PREFIX defaults to /usr/local when not specified
2. PREFIX can be overridden via environment variable export PREFIX=/custom/path
3. PREFIX can be overridden via make command: make PREFIX=/custom/path install
4. PREFIX can be overridden via install.sh: PREFIX=/custom/path ./install.sh
5. PREFIX can be overridden via install.sh flag: ./install.sh --prefix=/custom/path
6. BINDIR is always computed as $(PREFIX)/bin
7. All installation targets respect the PREFIX/BINDIR hierarchy
8. Uninstall target uses same PREFIX logic to find binaries to remove
9. Documentation clearly explains PREFIX customization options
10. Common prefix values documented: /usr/local, /usr, /opt, ~/.local

#### REQ_004.4: Support user-local installation to ~/.local/bin without sudo

Support user-local installation to ~/.local/bin without sudo requirements

##### Testable Behaviors

1. Installation to ~/.local/bin works without sudo
2. Script creates ~/.local/bin directory if it doesn't exist
3. Script detects if ~/.local/bin is in user's PATH
4. Script provides PATH configuration instructions when not in PATH
5. Makefile supports make PREFIX=~/.local install shorthand
6. install.sh supports ./install.sh --user flag for ~/.local installation
7. Documentation provides shell-specific PATH instructions for bash, zsh, fish
8. Uninstall correctly removes from ~/.local/bin when PREFIX matches
9. No sudo prompt appears for user-local installation
10. Binary permissions set correctly without sudo (755)

#### REQ_004.5: Include version embedding via LDFLAGS during build using git

Include version embedding via LDFLAGS during build using git tags and build metadata

##### Testable Behaviors

1. Version is extracted from git describe --tags --always --dirty
2. Version is embedded into binary via -ldflags "-X main.version=$(VERSION)"
3. Binary responds to --version flag showing embedded version
4. Dirty working directory appends '-dirty' suffix to version
5. Builds without git tags use short commit hash as version
6. VERSION can be manually overridden: make VERSION=1.0.0 build
7. Version includes tag name when building from tagged commit
8. Additional metadata can be embedded: build time, commit hash, go version
9. Version information accessible programmatically within application
10. Release builds include clean semantic version without dirty suffix


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed