# Phase 01: The system must rewrite core Python logic in Go in...

## Requirements

### REQ_000: The system must rewrite core Python logic in Go including su

The system must rewrite core Python logic in Go including subprocess management, JSON handling, and CLI parsing for a complete language port

#### REQ_000.1: Port subprocess management from Python subprocess module to 

Port subprocess management from Python subprocess module to Go os/exec package, implementing command execution with timeout support, working directory control, environment variable handling, and both synchronous and streaming output capture

##### Testable Behaviors

1. Go struct CommandResult mirrors Python dict with success, output, and error fields
2. Timeout support via context.WithTimeout with configurable duration up to 1 hour (3600 seconds)
3. Working directory (cwd) parameter maps to cmd.Dir in Go
4. capture_output=True maps to cmd.Output() or cmd.CombinedOutput()
5. text=True behavior is default in Go (string output)
6. Streaming output via subprocess.Popen maps to cmd.StdoutPipe() with goroutine readers
7. Environment variable inheritance via cmd.Env = append(os.Environ(), custom...)
8. Return code access via cmd.ProcessState.ExitCode()
9. Handle all 60+ subprocess.run calls identified in codebase
10. Handle subprocess.Popen streaming pattern from claude_runner.py
11. Support shell=True equivalent via exec.Command('bash', '-c', command)
12. Error handling differentiates timeout, exit code, and execution errors

#### REQ_000.2: Convert JSON parsing/serialization from Python json module t

Convert JSON parsing/serialization from Python json module to Go encoding/json, implementing struct marshaling with proper field tags, custom type handling, and file I/O operations

##### Testable Behaviors

1. All dataclass models from planning_pipeline/models.py have Go struct equivalents with json tags
2. RequirementNode struct includes all 11 fields with proper json tag annotations
3. Feature struct matches feature_list.json schema with optional fields using omitempty
4. json.load(f) pattern maps to json.NewDecoder(file).Decode(&target)
5. json.dump(data, f, indent=2) maps to json.MarshalIndent with 2-space indent
6. json.loads(string) maps to json.Unmarshal([]byte(string), &target)
7. json.dumps(object, indent=2) maps to json.MarshalIndent(object, '', '  ')
8. Handle 80+ JSON operations identified across codebase
9. Support ensure_ascii=False behavior (Go encoding/json handles UTF-8 natively)
10. Pointer types for optional fields (Optional[str] maps to *string)
11. Slice types for list fields (list[str] maps to []string)
12. Nested struct types for complex objects (ImplementationComponents)
13. Custom time.Time marshaling for datetime fields

#### REQ_000.3: Transform CLI argument parsing from Python argparse to Go co

Transform CLI argument parsing from Python argparse to Go cobra framework, implementing multi-command CLI with flags, subcommands, validation, and help text generation

##### Testable Behaviors

1. orchestrator.py 11 arguments map to cobra flags with same short/long names
2. loop-runner.py 10 arguments map to cobra flags preserving behavior
3. mcp-setup.py 6 arguments map to cobra flags for MCP configuration
4. Positional arguments (project path) handled via cobra Args
5. type=Path arguments validate path existence or create as needed
6. action='store_true' maps to BoolVar flags
7. choices=[...] maps to custom validation functions
8. default values preserved from Python implementation
9. Mutually exclusive flags (--project vs --new) handled with PreRunE validation
10. Help text matches original argparse descriptions
11. Short flags (-p, -m, -c, -s, -d, -i, -n, -l, -o) preserved
12. Subcommands for orchestrator, loop-runner, mcp-setup if building unified binary
13. Environment variable binding for CONTEXT_ENGINE_PATH equivalent
14. Version flag injection at build time via ldflags

#### REQ_000.4: Migrate file system path operations from Python pathlib.Path

Migrate file system path operations from Python pathlib.Path to Go path/filepath, implementing cross-platform path manipulation, file existence checks, directory traversal, and path resolution

##### Testable Behaviors

1. Path(path).expanduser() maps to os.UserHomeDir() + string replacement
2. Path(path).resolve() maps to filepath.Abs()
3. Path(path).exists() maps to os.Stat() error check
4. Path(path).is_file() maps to os.Stat() + !IsDir()
5. Path(path).is_dir() maps to os.Stat() + IsDir()
6. Path(path).mkdir(parents=True) maps to os.MkdirAll()
7. Path(path).read_text() maps to os.ReadFile() + string conversion
8. Path(path).write_text(content) maps to os.WriteFile() with 0644 permissions
9. Path(path).parent maps to filepath.Dir()
10. Path(path).name maps to filepath.Base()
11. Path(path).stem maps to custom function stripping extension
12. Path(path).suffix maps to filepath.Ext()
13. Path(path) / 'subpath' maps to filepath.Join()
14. Handle 150+ pathlib operations identified across codebase
15. Cross-platform path separator handling (os.PathSeparator)
16. Symlink resolution via filepath.EvalSymlinks()


## Success Criteria

- [ ] All tests pass
- [ ] All behaviors implemented
- [ ] Code reviewed