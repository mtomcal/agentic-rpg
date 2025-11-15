# Claude Agent Instructions

## Development Quality Rules

**CRITICAL: These rules must be followed at all times**

### 1. Test-Driven Development (TDD)

**Always write tests first, then implement the code.**

Workflow:
1. Write a failing test that describes the expected behavior
2. Run the test to confirm it fails
3. Write the minimal code to make the test pass
4. Run the test to confirm it passes
5. Refactor if needed while keeping tests green
6. Repeat for next feature

Example:
```bash
# 1. Create test file first
# Write test in tests/unit/test_models/test_character.py

# 2. Run test (should fail)
poetry run pytest tests/unit/test_models/test_character.py -v

# 3. Implement the code in src/agentic_rpg/models/character.py

# 4. Run test again (should pass)
poetry run pytest tests/unit/test_models/test_character.py -v

# 5. Log progress
./readyq.py update <task-id> --log "Implemented Character model with TDD - tests passing"
```

**Never implement functionality without a test first.**

### 2. Interface Stability

**Do not change any interface without explicit permission.**

Rules:
- **Only make non-breaking changes** to existing interfaces
- **Ask the human before making any breaking change**
- Breaking changes include:
  - Changing function signatures (parameters, return types)
  - Removing or renaming public methods/functions
  - Changing data model field names or types
  - Modifying API endpoint paths or request/response structures
  - Altering Protocol definitions or abstract base classes

Non-breaking changes (allowed):
- Adding new optional parameters with defaults
- Adding new methods to classes
- Adding new fields to data models (with defaults)
- Improving documentation
- Refactoring internal implementation (same interface)

Example conversation when breaking change is needed:
```
Agent: "I need to change the StateManager.load_state() signature from
       load_state(session_id: str) to load_state(session_id: str, version: str).
       This is a breaking change. Should I proceed?"
```

**When in doubt, ask before changing any public interface.**

---

## Task Management with readyq

This project uses **readyq** for task tracking and dependency management. readyq is a JSONL-based task tracker that helps maintain context across work sessions.

### Core Commands

#### View Tasks
```bash
./readyq.py list          # List all tasks
./readyq.py ready         # List only unblocked, actionable tasks
./readyq.py show <task-id> # Show detailed task info with session logs
```

#### Create Tasks
```bash
./readyq.py new "Task title"
./readyq.py new "Task title" --description "Detailed description"
./readyq.py new "Task title" --blocked-by <task-id>  # Create blocked task
```

#### Update Tasks
```bash
./readyq.py update <task-id> --status [open|in_progress|done|blocked]
./readyq.py update <task-id> --log "What I learned or accomplished"
./readyq.py update <task-id> --title "New title" --description "New desc"
./readyq.py update <task-id> --add-blocks <task-id>      # Add task this blocks
./readyq.py update <task-id> --add-blocked-by <task-id>  # Add blocker
```

#### Delete Tasks
```bash
./readyq.py delete <task-id>
./readyq.py update <task-id> --delete-log <index>  # Delete session log entry
```

#### Web Interface
```bash
./readyq.py web  # Launch web UI at http://localhost:8000
```

### Best Practices for AI Agents

1. **Always check ready tasks before starting new work**
   ```bash
   ./readyq.py ready
   ```

2. **Mark tasks as in_progress when starting**
   ```bash
   ./readyq.py update <task-id> --status in_progress
   ```

3. **Use session logs frequently to maintain context**
   ```bash
   ./readyq.py update <task-id> --log "Created backend models with Pydantic validation"
   ./readyq.py update <task-id> --log "All unit tests passing"
   ```

4. **Mark tasks as done when complete**
   ```bash
   ./readyq.py update <task-id> --status done
   ```
   When marked done, all tasks it blocks are automatically unblocked.

5. **Use partial IDs for faster typing**
   - Full ID: `c4a0f2e8b1d34567890abcdef1234567`
   - Short ID: `c4a0f2e8` (first 8 chars works for most commands)

### Task Statuses

- **open** - Ready to start (no active blockers)
- **in_progress** - Currently being worked on
- **blocked** - Waiting on dependencies
- **done** - Completed

### Dependency Management

Tasks can have dependencies:
- **blocks** - Tasks that this task prevents from starting
- **blocked_by** - Tasks that must complete before this can start

Example workflow:
```bash
# Create foundation task
./readyq.py new "Setup backend project structure"
TASK1=$(./readyq.py list | tail -1 | awk '{print $1}')

# Create dependent task
./readyq.py new "Implement data models" --blocked-by $TASK1

# Work on first task
./readyq.py update $TASK1 --status in_progress
./readyq.py update $TASK1 --log "Created Poetry project and directory structure"

# Complete first task (automatically unblocks next)
./readyq.py update $TASK1 --status done

# Check what's ready now
./readyq.py ready  # Now shows "Implement data models"
```

### Database Location

- File: `.readyq.jsonl` (git-tracked)
- Format: JSONL (one JSON task per line)
- File locking prevents race conditions during concurrent access

### Integration with Development

When implementing features (following TDD):

1. Check for ready tasks: `./readyq.py ready`
2. Start a task: `./readyq.py update <id> --status in_progress`
3. **Write test first** (TDD):
   - Create test file in appropriate directory
   - Write failing test
   - Run test to confirm failure
4. **Implement code** to pass the test:
   - Write minimal code to make test pass
   - Run test to confirm success
5. Log progress regularly:
   - After tests pass
   - After creating files
   - When encountering issues
   - When discovering important architecture details
6. Refactor if needed (keep tests green)
7. Mark complete: `./readyq.py update <id> --status done`

### Example Session (with TDD)

```bash
# See what's ready to work on
./readyq.py ready

# Start working on a task
./readyq.py update c4a0 --status in_progress

# TDD: Write test first
# Create tests/unit/test_models/test_character.py with failing tests
poetry run pytest tests/unit/test_models/test_character.py -v
# Test fails as expected

# Log progress
./readyq.py update c4a0 --log "Created test for Character model - currently failing"

# Implement the code
# Create src/agentic_rpg/models/character.py
poetry run pytest tests/unit/test_models/test_character.py -v
# Test passes!

# Log progress as you work
./readyq.py update c4a0 --log "Implemented Character model - tests passing"
./readyq.py update c4a0 --log "Added CharacterStats and validation - all tests green"
./readyq.py update c4a0 --log "Generated JSON schemas successfully"

# Complete the task
./readyq.py update c4a0 --status done

# Check next ready task
./readyq.py ready
```

### Viewing Task Details

```bash
# See full task details including all session logs
./readyq.py show <task-id>
```

This shows:
- Task ID, title, status
- Full description
- Creation and update timestamps
- Dependency relationships (blocks/blocked_by)
- All session logs with timestamps

### Tips

- Session logs help maintain context between work sessions
- Use descriptive task titles (appears in task lists)
- Use descriptions for detailed context and requirements
- Web UI (`./readyq.py web`) provides visual task management
- Partial IDs work for all commands (e.g., 'c4a0' instead of full UUID)

---

## Summary of Critical Rules

1. **TDD Always**: Write test first → Run (fails) → Implement → Run (passes) → Log
2. **No Breaking Changes**: Ask permission before changing any public interface
3. **Log Frequently**: Use `--log` to maintain context across sessions
4. **Check Ready Tasks**: Start each session with `./readyq.py ready`
