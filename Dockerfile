# Dockerfile for running Claude Code in a container
FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3.11 \
    python3-pip \
    python3.11-venv \
    build-essential \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
# Claude Code CLI needs to be installed manually or via npm
# Option 1: If Claude provides a Linux installer script
RUN curl -fsSL https://cli.anthropic.com/install.sh 2>/dev/null | sh || \
    echo "⚠️  Claude CLI install script not available, will install via npm"

# Option 2: Install via npm (Claude Code may be available as npm package)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g @anthropic-ai/claude-code || \
    echo "⚠️  Claude Code npm package not found"

# Note: If neither method works, you'll need to:
# 1. Download Claude CLI binary manually and add to PATH
# 2. Or use the community Docker image: nezhar/claude-container
# 3. Or install Claude CLI on host and mount it

# Set up Python environment
RUN python3.11 -m pip install --upgrade pip setuptools wheel

# Create working directory
WORKDIR /workspace

# Copy project files
COPY . /workspace/

# Install Python dependencies if pyproject.toml exists
RUN if [ -f pyproject.toml ]; then \
        pip3 install -e .; \
    fi

# Install BAML CLI if needed
RUN pip3 install baml-py || echo "⚠️  BAML installation failed (may not be needed)"

# Create directory for Claude configuration
RUN mkdir -p /root/.config/claude

# Set up entrypoint
ENTRYPOINT ["/bin/bash"]

