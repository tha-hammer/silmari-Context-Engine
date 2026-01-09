# Docker Setup Guide for Claude Code

This guide walks you through setting up and running Claude Code in a Docker container locally.

## Prerequisites

1. **Docker Desktop** or **Docker Engine** installed
   - Download from: https://www.docker.com/products/docker-desktop/
   - Verify installation: `docker --version`

2. **Docker Compose** (usually included with Docker Desktop)
   - Verify: `docker-compose --version`

## Installation Methods

This project provides a custom Dockerfile, but you have several options:

### Method 1: Custom Dockerfile (This Project)
Build and use the provided Dockerfile (recommended for full control).

### Method 2: Community Docker Image
Use the pre-built `nezhar/claude-container` image (faster setup, less customization).

### Method 3: Docker Sandboxes (Docker Desktop 4.50+)
Use Docker's built-in sandbox feature: `docker sandbox run claude`

---

## Quick Start (Method 1: Custom Dockerfile)

### 1. Set Up Environment Variables

Create a `.env` file in the project root (optional, but recommended):

```bash
# .env
ANTHROPIC_API_KEY=your_api_key_here
```

**Note:** If you don't set the API key in `.env`, you'll need to authenticate inside the container.

### 2. Build and Start the Container

```bash
# Build the Docker image
docker-compose build

# Start the container (runs in background)
docker-compose up -d

# Or start and attach to terminal
docker-compose up
```

### 3. Access the Container

```bash
# Attach to running container
docker-compose exec claude-code bash

# Or use docker directly
docker exec -it claude-code-dev bash
```

### 4. Verify Installation

Inside the container, verify everything is installed:

```bash
# Check Claude CLI
claude --version

# Check Python
python3 --version

# Check Git
git --version

# Check BAML (if installed)
baml-cli --version
```

### 5. Authenticate Claude Code (First Time)

If you haven't set `ANTHROPIC_API_KEY` in `.env`, authenticate:

```bash
# Inside the container
claude auth login
# Follow the prompts to authenticate
```

### 6. Configure MCPs (Model Context Protocol)

MCPs are stored in the container's config directory (persisted via Docker volume):

```bash
# Inside the container
# Add documentation MCP (recommended)
claude mcp add context7

# Add Ref MCP (requires API key)
claude mcp add --transport http Ref https://api.ref.tools/mcp --header "x-ref-api-key: YOUR_KEY"

# Verify MCPs
claude mcp list
```

**Note:** MCP configuration persists in the `claude-config` Docker volume, so you only need to set this up once.

### 7. Run Claude Code

Now you can use Claude Code normally:

```bash
# Interactive mode
claude

# Run with a prompt
claude -p "Your prompt here"

# Run orchestrator
python3 orchestrator.py --new /workspace/my-project --model opus

# Run loop runner
python3 loop-runner.py /workspace/my-project --model opus
```

## Common Workflows

### Running a Single Session

```bash
# Enter container
docker-compose exec claude-code bash

# Run Claude Code with a prompt
claude -p "Implement feature X"
```

### Running the Autonomous Loop

```bash
# Enter container
docker-compose exec claude-code bash

# Initialize a new project (if needed)
python3 orchestrator.py --new /workspace/my-project --model opus

# Run the loop
python3 loop-runner.py /workspace/my-project --model opus
```

### Accessing Project Files

All project files are mounted at `/workspace` in the container. Changes made inside the container are reflected on your host machine and vice versa.

```bash
# Inside container
cd /workspace
ls -la  # See all project files
```

## Troubleshooting

### Claude CLI Not Found

If `claude --version` fails, Claude Code CLI may need to be installed differently. Try these options:

**Option 1: Install via npm (if available)**
```bash
# Inside container
npm install -g @anthropic-ai/claude-code
```

**Option 2: Use pre-built Docker image**
Instead of building from scratch, you can use the community image:
```bash
# Update docker-compose.yml to use:
# image: nezhar/claude-container:latest
# instead of build: context: .
```

**Option 3: Mount Claude CLI from host**
If you have Claude CLI installed on your host:
```yaml
# In docker-compose.yml, add to volumes:
- /usr/local/bin/claude:/usr/local/bin/claude:ro
# Adjust path to where Claude is installed on your host
```

**Option 4: Manual installation**
Check the [official installation guide](https://docs.anthropic.com/en/docs/claude-code/get-started/install-claude-code) for Linux installation instructions.

### MCPs Not Persisting

MCPs are stored in the Docker volume `claude-config`. If they're not persisting:

```bash
# Check volume exists
docker volume ls | grep claude-config

# Inspect volume
docker volume inspect claude-config
```

### Permission Issues

If you encounter permission issues with mounted files:

```bash
# Fix ownership (run on host, not in container)
sudo chown -R $USER:$USER .
```

### Python Dependencies Missing

If Python packages are missing:

```bash
# Inside container
cd /workspace
pip3 install -e .
```

### Git Configuration

To use git inside the container, you may want to configure it:

```bash
# Inside container
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Or mount your existing git config:

```bash
# In docker-compose.yml, add to volumes:
- ~/.gitconfig:/root/.gitconfig:ro
```

## Stopping and Cleaning Up

```bash
# Stop container
docker-compose down

# Stop and remove volumes (⚠️ deletes MCP config)
docker-compose down -v

# Rebuild from scratch
docker-compose build --no-cache
```

## Advanced Configuration

### Custom Dockerfile

You can customize the Dockerfile to add additional tools or dependencies:

```dockerfile
# Add to Dockerfile
RUN apt-get install -y \
    vim \
    htop \
    # ... other tools
```

Then rebuild:

```bash
docker-compose build
```

### Multiple Containers

To run multiple projects, use different compose files:

```bash
# docker-compose.project1.yml
docker-compose -f docker-compose.yml -f docker-compose.project1.yml up
```

### Resource Limits

Add resource limits in `docker-compose.yml`:

```yaml
services:
  claude-code:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

## Tips

1. **Keep container running**: The default command keeps the container running. Use `docker-compose exec` to access it anytime.

2. **Persistent MCP config**: MCPs are stored in a Docker volume, so they persist across container restarts.

3. **Project files**: All project files are mounted, so you can edit them from your host machine or inside the container.

4. **Multiple terminals**: You can open multiple terminals into the same container:
   ```bash
   docker-compose exec claude-code bash  # Terminal 1
   docker-compose exec claude-code bash  # Terminal 2
   ```

5. **Logs**: View container logs:
   ```bash
   docker-compose logs -f claude-code
   ```

## Alternative: Using Community Docker Image

If the custom Dockerfile doesn't work for Claude CLI installation, you can use the community image:

```bash
# Update docker-compose.yml to use:
# image: nezhar/claude-container:latest
# Comment out or remove the build: section

# Then run:
docker-compose up -d
docker-compose exec claude-code bash
```

Or use Docker directly:

```bash
docker run --rm -it \
  -v "$(pwd):/workspace" \
  -v claude-config:/root/.config/claude \
  -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  nezhar/claude-container:latest \
  bash
```

## Alternative: Docker Sandboxes (Docker Desktop 4.50+)

If you have Docker Desktop 4.50+, you can use the built-in sandbox feature:

```bash
# Run Claude Code in a sandbox
docker sandbox run claude

# With a prompt
docker sandbox run claude "Your prompt here"

# Continue previous conversation
docker sandbox run claude --continue
```

This is the simplest method but requires Docker Desktop 4.50+.

## Next Steps

- Read the main [README.md](README.md) for project usage
- Check [CLAUDE.md](CLAUDE.md) for Claude Code instructions
- Review [docs/](docs/) for architecture details

