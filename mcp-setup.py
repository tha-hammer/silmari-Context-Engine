#!/usr/bin/env python3
"""
Smart MCP Configurator
======================
Intelligently configures MCP servers for your project.

Features:
- Interactive setup asking what you need
- Auto-discovers MCPs from GitHub repos
- Parses `claude mcp add` commands
- Uses Claude Code to help configure complex MCPs
- Generates mcp-config.json automatically

Usage:
    python mcp-setup.py                           # Interactive mode
    python mcp-setup.py --add "github.com/org/mcp-server"
    python mcp-setup.py --add "claude mcp add --transport http ..."
    python mcp-setup.py --preset web              # Use preset for web projects
"""

import subprocess
import json
import os
import sys
import re
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

# ============================================================================
# Colors
# ============================================================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'═' * 60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'═' * 60}{Colors.END}\n")

def print_status(text: str, status: str = "info"):
    icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "working": "🔧"}
    colors = {"info": Colors.CYAN, "success": Colors.GREEN, "warning": Colors.YELLOW, "error": Colors.RED, "working": Colors.BLUE}
    print(f"{icons.get(status, 'ℹ️')} {colors.get(status, '')}{text}{Colors.END}")

# ============================================================================
# Known MCP Servers Database
# ============================================================================

KNOWN_MCPS = {
    # Official Anthropic MCPs
    "filesystem": {
        "name": "File System",
        "description": "Read/write files and directories",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "requires_path": True,
        "category": "core"
    },
    "postgres": {
        "name": "PostgreSQL",
        "description": "Query PostgreSQL databases",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres"],
        "env_vars": ["POSTGRES_URL"],
        "category": "database"
    },
    "sqlite": {
        "name": "SQLite",
        "description": "Query SQLite databases",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite"],
        "requires_path": True,
        "category": "database"
    },
    "fetch": {
        "name": "HTTP Fetch",
        "description": "Make HTTP requests",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-fetch"],
        "category": "core"
    },
    "github": {
        "name": "GitHub",
        "description": "Interact with GitHub API",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env_vars": ["GITHUB_TOKEN"],
        "category": "dev"
    },
    "memory": {
        "name": "Memory",
        "description": "Persistent key-value memory",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
        "category": "core"
    },
    "brave-search": {
        "name": "Brave Search",
        "description": "Web search via Brave API",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env_vars": ["BRAVE_API_KEY"],
        "category": "search"
    },
    "puppeteer": {
        "name": "Puppeteer",
        "description": "Browser automation",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        "category": "web"
    },
    "slack": {
        "name": "Slack",
        "description": "Interact with Slack",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env_vars": ["SLACK_BOT_TOKEN", "SLACK_TEAM_ID"],
        "category": "communication"
    },
    "google-drive": {
        "name": "Google Drive",
        "description": "Access Google Drive files",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-gdrive"],
        "env_vars": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
        "category": "storage"
    },
    # Documentation MCPs
    "ref": {
        "name": "Ref Documentation",
        "description": "Access up-to-date library/framework documentation (Rust, Python, JS, etc.)",
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://api.ref.tools/mcp"],
        "category": "docs"
    },
    "context7": {
        "name": "Context7 Docs",
        "description": "Alternative documentation provider with version-specific docs",
        "command": "npx",
        "args": ["-y", "mcp-remote", "https://mcp.context7.com/mcp"],
        "category": "docs"
    },
    # Community MCPs
    "kubernetes": {
        "name": "Kubernetes",
        "description": "Manage Kubernetes clusters",
        "command": "npx",
        "args": ["-y", "mcp-server-kubernetes"],
        "category": "infra"
    },
    "docker": {
        "name": "Docker",
        "description": "Manage Docker containers",
        "command": "npx",
        "args": ["-y", "mcp-server-docker"],
        "category": "infra"
    },
    "redis": {
        "name": "Redis",
        "description": "Redis operations",
        "command": "npx",
        "args": ["-y", "mcp-server-redis"],
        "env_vars": ["REDIS_URL"],
        "category": "database"
    },
}

# Presets for common project types
PRESETS = {
    "web": {
        "description": "Web development (API testing, database, file access)",
        "mcps": ["filesystem", "fetch", "postgres"]
    },
    "fullstack": {
        "description": "Full-stack development",
        "mcps": ["filesystem", "fetch", "postgres", "github", "puppeteer"]
    },
    "data": {
        "description": "Data analysis and processing",
        "mcps": ["filesystem", "postgres", "sqlite", "fetch"]
    },
    "devops": {
        "description": "DevOps and infrastructure",
        "mcps": ["filesystem", "kubernetes", "docker", "github"]
    },
    "minimal": {
        "description": "Minimal setup (files + HTTP)",
        "mcps": ["filesystem", "fetch"]
    },
    "rust": {
        "description": "Rust development with up-to-date docs",
        "mcps": ["filesystem", "fetch", "ref", "postgres"]
    },
    "python": {
        "description": "Python development with docs",
        "mcps": ["filesystem", "fetch", "ref", "postgres"]
    },
    "node": {
        "description": "Node.js/TypeScript development with docs",
        "mcps": ["filesystem", "fetch", "ref", "postgres", "github"]
    },
    "docs": {
        "description": "Any project with documentation access",
        "mcps": ["filesystem", "fetch", "ref", "context7"]
    }
}

# ============================================================================
# MCP Configuration Builder
# ============================================================================

class MCPConfigurator:
    def __init__(self, project_path: Path = None):
        self.project_path = Path(project_path or Path.cwd()).expanduser().resolve()
        self.config = {"mcpServers": {}}
        self.config_file = self.project_path / "mcp-config.json"
    
    def load_existing(self):
        """Load existing MCP config if present."""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    self.config = json.load(f)
                print_status(f"Loaded existing config with {len(self.config.get('mcpServers', {}))} servers", "info")
            except:
                pass
    
    def save(self):
        """Save config to file."""
        # Ensure parent directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)
        print_status(f"Saved config to {self.config_file}", "success")
    
    def add_known_mcp(self, mcp_id: str, **kwargs) -> bool:
        """Add a known MCP server."""
        if mcp_id not in KNOWN_MCPS:
            print_status(f"Unknown MCP: {mcp_id}", "error")
            return False
        
        mcp = KNOWN_MCPS[mcp_id]
        server_config = {
            "command": mcp["command"],
            "args": mcp["args"].copy()
        }
        
        # Handle path requirements
        if mcp.get("requires_path"):
            path = kwargs.get("path", ".")
            server_config["args"].append(path)
        
        # Handle environment variables
        if mcp.get("env_vars"):
            env = {}
            for var in mcp["env_vars"]:
                value = kwargs.get(var) or os.environ.get(var)
                if value:
                    env[var] = value
                else:
                    # Placeholder
                    env[var] = f"${{{var}}}"
            if env:
                server_config["env"] = env
        
        self.config["mcpServers"][mcp_id] = server_config
        print_status(f"Added {mcp['name']} MCP", "success")
        return True
    
    def add_from_github(self, repo_url: str) -> bool:
        """Add MCP from GitHub repo URL."""
        # Extract repo info
        match = re.search(r'github\.com[/:]([^/]+)/([^/\s]+)', repo_url)
        if not match:
            print_status(f"Could not parse GitHub URL: {repo_url}", "error")
            return False
        
        org, repo = match.groups()
        repo = repo.replace('.git', '')
        
        # Try to determine package name
        package_name = f"@{org}/{repo}" if org != repo else repo
        
        # Check if it's an npm package
        server_config = {
            "command": "npx",
            "args": ["-y", package_name]
        }
        
        mcp_id = repo.replace("mcp-server-", "").replace("-mcp", "")
        self.config["mcpServers"][mcp_id] = server_config
        
        print_status(f"Added {repo} from GitHub", "success")
        print_status(f"Note: You may need to configure env vars manually", "warning")
        return True
    
    def add_from_claude_command(self, command: str) -> bool:
        """Parse and add MCP from 'claude mcp add' command."""
        # Parse command like: claude mcp add --transport http Ref https://api.ref.tools/mcp --header "x-ref-api-key: xxx"
        
        parts = command.split()
        
        # Find the MCP name and URL
        mcp_name = None
        url = None
        transport = "stdio"
        headers = {}
        env_vars = {}
        
        i = 0
        while i < len(parts):
            part = parts[i]
            
            if part == "--transport" and i + 1 < len(parts):
                transport = parts[i + 1]
                i += 2
                continue
            elif part == "--header" and i + 1 < len(parts):
                header = parts[i + 1].strip('"\'')
                if ':' in header:
                    key, value = header.split(':', 1)
                    headers[key.strip()] = value.strip()
                i += 2
                continue
            elif part == "--env" and i + 1 < len(parts):
                env = parts[i + 1].strip('"\'')
                if '=' in env:
                    key, value = env.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                i += 2
                continue
            elif part.startswith("http://") or part.startswith("https://"):
                url = part
                i += 1
                continue
            elif part not in ["claude", "mcp", "add", "-y", "--scope", "project", "user"]:
                if not mcp_name:
                    mcp_name = part
            
            i += 1
        
        if not mcp_name:
            mcp_name = "custom-mcp"
        
        mcp_name = mcp_name.lower().replace(" ", "-")
        
        # Build config based on transport
        if transport == "http" and url:
            server_config = {
                "command": "npx",
                "args": ["-y", "mcp-remote", url]
            }
            if headers:
                # Pass headers as args
                for key, value in headers.items():
                    server_config["args"].extend(["--header", f"{key}: {value}"])
        else:
            # Assume stdio with npx
            server_config = {
                "command": "npx",
                "args": ["-y", mcp_name]
            }
        
        if env_vars:
            server_config["env"] = env_vars
        
        self.config["mcpServers"][mcp_name] = server_config
        print_status(f"Added {mcp_name} from command", "success")
        return True
    
    def add_custom(self, name: str, command: str, args: List[str], env: Dict[str, str] = None):
        """Add a custom MCP configuration."""
        server_config = {
            "command": command,
            "args": args
        }
        if env:
            server_config["env"] = env
        
        self.config["mcpServers"][name] = server_config
        print_status(f"Added custom MCP: {name}", "success")

# ============================================================================
# Interactive Setup
# ============================================================================

def interactive_setup(project_path: Path = None) -> MCPConfigurator:
    """Interactive MCP setup wizard."""
    print_header("MCP Configuration Wizard")
    
    configurator = MCPConfigurator(project_path)
    configurator.load_existing()
    
    # Ask about preset or custom
    print(f"{Colors.BOLD}How would you like to configure MCPs?{Colors.END}")
    print("  1. Use a preset (recommended for new projects)")
    print("  2. Select individual MCPs")
    print("  3. Add from GitHub repo URL")
    print("  4. Add from 'claude mcp add' command")
    print("  5. Let Claude Code figure it out (smart mode)")
    
    choice = input(f"\n{Colors.CYAN}Select [1-5]:{Colors.END} ").strip()
    
    if choice == "1":
        # Preset selection
        print(f"\n{Colors.BOLD}Available Presets:{Colors.END}")
        for i, (preset_id, preset) in enumerate(PRESETS.items(), 1):
            print(f"  {i}. {preset_id}: {preset['description']}")
            print(f"     MCPs: {', '.join(preset['mcps'])}")
        
        preset_choice = input(f"\n{Colors.CYAN}Select preset [1-{len(PRESETS)}]:{Colors.END} ").strip()
        try:
            preset_id = list(PRESETS.keys())[int(preset_choice) - 1]
            preset = PRESETS[preset_id]
            
            for mcp_id in preset["mcps"]:
                configure_mcp_interactive(configurator, mcp_id)
        except:
            print_status("Invalid selection", "error")
    
    elif choice == "2":
        # Individual selection
        print(f"\n{Colors.BOLD}Available MCPs:{Colors.END}")
        
        categories = {}
        for mcp_id, mcp in KNOWN_MCPS.items():
            cat = mcp.get("category", "other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((mcp_id, mcp))
        
        for cat, mcps in sorted(categories.items()):
            print(f"\n  {Colors.BOLD}{cat.upper()}{Colors.END}")
            for mcp_id, mcp in mcps:
                print(f"    - {mcp_id}: {mcp['description']}")
        
        print(f"\n{Colors.CYAN}Enter MCP IDs to add (comma-separated):{Colors.END}")
        selected = input("> ").strip()
        
        for mcp_id in [m.strip() for m in selected.split(",")]:
            if mcp_id:
                configure_mcp_interactive(configurator, mcp_id)
    
    elif choice == "3":
        # GitHub URL
        print(f"\n{Colors.CYAN}Enter GitHub repo URL:{Colors.END}")
        url = input("> ").strip()
        configurator.add_from_github(url)
        
        # Ask for more
        while True:
            more = input(f"\n{Colors.CYAN}Add another GitHub repo? [y/N]:{Colors.END} ").strip().lower()
            if more != 'y':
                break
            url = input(f"{Colors.CYAN}GitHub URL:{Colors.END} ").strip()
            configurator.add_from_github(url)
    
    elif choice == "4":
        # Claude mcp add command
        print(f"\n{Colors.CYAN}Paste your 'claude mcp add' command:{Colors.END}")
        command = input("> ").strip()
        configurator.add_from_claude_command(command)
        
        # Ask for more
        while True:
            more = input(f"\n{Colors.CYAN}Add another command? [y/N]:{Colors.END} ").strip().lower()
            if more != 'y':
                break
            command = input(f"{Colors.CYAN}Command:{Colors.END} ").strip()
            configurator.add_from_claude_command(command)
    
    elif choice == "5":
        # Smart mode - use Claude Code
        smart_mcp_setup(configurator)
    
    # Save config
    configurator.save()
    
    # Show result
    print(f"\n{Colors.BOLD}Final Configuration:{Colors.END}")
    print(json.dumps(configurator.config, indent=2))
    
    return configurator

def configure_mcp_interactive(configurator: MCPConfigurator, mcp_id: str):
    """Configure a single MCP interactively."""
    if mcp_id not in KNOWN_MCPS:
        print_status(f"Unknown MCP: {mcp_id}", "warning")
        return
    
    mcp = KNOWN_MCPS[mcp_id]
    kwargs = {}
    
    # Ask for path if required
    if mcp.get("requires_path"):
        default = "." if mcp_id == "filesystem" else f"./{mcp_id}.db"
        path = input(f"  {Colors.CYAN}{mcp['name']} path [{default}]:{Colors.END} ").strip() or default
        kwargs["path"] = path
    
    # Ask for env vars
    if mcp.get("env_vars"):
        for var in mcp["env_vars"]:
            existing = os.environ.get(var, "")
            if existing:
                print(f"  {Colors.GREEN}✓{Colors.END} {var} found in environment")
                kwargs[var] = existing
            else:
                value = input(f"  {Colors.CYAN}{var}:{Colors.END} ").strip()
                if value:
                    kwargs[var] = value
    
    configurator.add_known_mcp(mcp_id, **kwargs)

def smart_mcp_setup(configurator: MCPConfigurator):
    """Use Claude Code to intelligently configure MCPs."""
    print_status("Starting smart MCP configuration...", "working")
    
    # Gather project context
    project_path = configurator.project_path
    context = []
    
    # Check for common files
    if (project_path / "package.json").exists():
        context.append("Node.js project")
    if (project_path / "Cargo.toml").exists():
        context.append("Rust project")
    if (project_path / "requirements.txt").exists() or (project_path / "pyproject.toml").exists():
        context.append("Python project")
    if (project_path / "docker-compose.yml").exists():
        context.append("Docker Compose found")
    if (project_path / "kubernetes").exists() or (project_path / "k8s").exists():
        context.append("Kubernetes manifests found")
    
    # Check for database references
    for file in project_path.glob("**/*.env*"):
        try:
            content = file.read_text()
            if "POSTGRES" in content or "postgresql" in content:
                context.append("PostgreSQL database")
            if "REDIS" in content:
                context.append("Redis")
            if "MONGO" in content:
                context.append("MongoDB")
        except:
            pass
    
    print(f"\n{Colors.BOLD}Detected project context:{Colors.END}")
    for c in context:
        print(f"  - {c}")
    
    # Ask Claude Code for recommendations
    prompt = f"""Analyze this project and recommend MCP servers.

Project context:
{chr(10).join(f'- {c}' for c in context)}

Available MCPs:
{chr(10).join(f'- {mcp_id}: {mcp["description"]}' for mcp_id, mcp in KNOWN_MCPS.items())}

Respond with ONLY a JSON array of MCP IDs to enable, like:
["filesystem", "postgres", "fetch"]

Consider what would be most useful for this project."""

    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Parse response
        response = result.stdout.strip()
        # Extract JSON array from response
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            recommended = json.loads(match.group())
            print(f"\n{Colors.BOLD}Claude recommends:{Colors.END}")
            for mcp_id in recommended:
                if mcp_id in KNOWN_MCPS:
                    print(f"  - {mcp_id}: {KNOWN_MCPS[mcp_id]['description']}")
            
            confirm = input(f"\n{Colors.CYAN}Add these MCPs? [Y/n]:{Colors.END} ").strip().lower()
            if confirm != 'n':
                for mcp_id in recommended:
                    configure_mcp_interactive(configurator, mcp_id)
    except Exception as e:
        print_status(f"Smart setup failed: {e}", "error")
        print_status("Falling back to manual selection", "info")
        
        # Fallback to minimal preset
        for mcp_id in PRESETS["minimal"]["mcps"]:
            configure_mcp_interactive(configurator, mcp_id)

# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Smart MCP Configurator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mcp-setup.py                              # Interactive wizard
  python mcp-setup.py --preset web                 # Use web preset
  python mcp-setup.py --add postgres               # Add known MCP
  python mcp-setup.py --add "github.com/org/repo"  # Add from GitHub
  python mcp-setup.py --add "claude mcp add ..."   # Parse claude command
  python mcp-setup.py --list                       # List available MCPs
        """
    )
    
    parser.add_argument("--project", "-p", type=Path, default=Path.cwd(), help="Project path")
    parser.add_argument("--preset", choices=PRESETS.keys(), help="Use a preset configuration")
    parser.add_argument("--add", action="append", help="Add MCP (ID, GitHub URL, or claude command)")
    parser.add_argument("--list", "-l", action="store_true", help="List available MCPs")
    parser.add_argument("--smart", "-s", action="store_true", help="Use Claude to recommend MCPs")
    parser.add_argument("--output", "-o", type=Path, help="Output config file path")
    
    args = parser.parse_args()
    
    # List MCPs
    if args.list:
        print_header("Available MCP Servers")
        categories = {}
        for mcp_id, mcp in KNOWN_MCPS.items():
            cat = mcp.get("category", "other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((mcp_id, mcp))
        
        for cat, mcps in sorted(categories.items()):
            print(f"\n{Colors.BOLD}{cat.upper()}{Colors.END}")
            for mcp_id, mcp in mcps:
                print(f"  {Colors.CYAN}{mcp_id}{Colors.END}: {mcp['description']}")
                if mcp.get("env_vars"):
                    print(f"    Requires: {', '.join(mcp['env_vars'])}")
        
        print(f"\n{Colors.BOLD}PRESETS{Colors.END}")
        for preset_id, preset in PRESETS.items():
            print(f"  {Colors.CYAN}{preset_id}{Colors.END}: {preset['description']}")
        
        return
    
    # Create configurator with absolute path
    project_path = Path(args.project).expanduser().resolve()
    configurator = MCPConfigurator(project_path)
    configurator.load_existing()
    
    if args.output:
        configurator.config_file = Path(args.output).expanduser().resolve()
    
    # Handle preset
    if args.preset:
        preset = PRESETS[args.preset]
        print_status(f"Using preset: {args.preset}", "info")
        for mcp_id in preset["mcps"]:
            configure_mcp_interactive(configurator, mcp_id)
        configurator.save()
        return
    
    # Handle --add
    if args.add:
        for item in args.add:
            if item in KNOWN_MCPS:
                configure_mcp_interactive(configurator, item)
            elif "github.com" in item or "github:" in item:
                configurator.add_from_github(item)
            elif "claude" in item or "mcp add" in item:
                configurator.add_from_claude_command(item)
            else:
                # Try as MCP ID
                configure_mcp_interactive(configurator, item)
        configurator.save()
        return
    
    # Smart mode
    if args.smart:
        smart_mcp_setup(configurator)
        configurator.save()
        return
    
    # Interactive mode
    interactive_setup(project_path)

if __name__ == "__main__":
    main()
