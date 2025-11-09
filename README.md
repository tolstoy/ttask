# tTask

A terminal-based daily task management system with outline support.

## Features

- **Daily Journal View**: Each day has its own task list
- **Outline/Nesting**: Indent and organize tasks hierarchically
- **Folding**: Collapse/expand nested task groups for better focus
- **Task Reordering**: Move tasks up/down with their children
- **Auto-scrolling**: Automatically scrolls to keep selected task visible
- **Navigate History**: Browse any day's tasks with arrow keys
- **Move Tasks**: Transfer tasks between days
- **Markdown Storage**: Tasks stored as readable `.md` files in `~/tasks/`

## Installation

```bash
git clone https://github.com/tolstoy/ttask.git
cd ttask

# Run the install script (will ask for sudo password to create global command)
./install.sh
```

The installer will:
- Create a Python virtual environment
- Install dependencies
- Create a global `ttask` command in `/usr/local/bin/`

## Usage

```bash
# Run from anywhere after installation
ttask

# Or run directly from the project directory
./taskjournal
```

## Keyboard Shortcuts

### Navigation
- `↑/↓` or `j/k` - Move selection up/down
- `←/→` or `h/l` - Previous/next day
- `Shift+←/→` - Previous/next day with tasks (skip empty days)
- `t` - Jump to today

### Task Operations
- `a` - Add new task
  - If on child task (indented): adds sibling right below at same indent
  - If on parent task: adds new parent at bottom of list
- `e` - Edit selected task
- `Space` or `x` - Toggle task completion
- `d` - Delete selected task
- `Tab` - Indent task (nest under previous)
- `Shift+Tab` - Unindent task

### Organization
- `f` - Toggle fold/unfold (collapse/expand child tasks)
- `Shift+↑` - Move task and children up (swaps with sibling at same level)
- `Shift+↓` - Move task and children down (swaps with sibling at same level)
  - Note: Child tasks only swap with siblings, staying under their parent

### Advanced
- `m` - Move task to another day
  - Natural language: `tomorrow`, `yesterday`, `monday`, `next week`, `nov 10`
  - Relative offset: `+1`, `-1`, `+7`
  - ISO format: `YYYY-MM-DD`
- `q` - Quit

## Storage

Tasks are stored as markdown files in `~/tasks/`:
- File format: `YYYY-MM-DD.md`
- Tasks use checkbox syntax: `- [ ]` or `- [x]`
- Completed tasks are shown with strikethrough
- Indentation represents nesting (2 spaces per level)

## Example

```markdown
# 2025-11-07

▼ [ ] Review pull requests
    [ ] PR #123 - Auth changes
    [x] ~~PR #124 - Bug fix~~
  [x] ~~Team meeting~~
▼ [ ] Write documentation
    [ ] API reference
    [ ] Getting started guide
```

When folded:
```markdown
▶ [ ] Review pull requests
  [x] ~~Team meeting~~
▶ [ ] Write documentation
```

## Architecture

The codebase follows a **layered architecture** with clear separation of concerns:

**Data Layer** (`models.py`)
- Core data structures: `Task` and `DailyTaskList`
- Handles task properties: completion, indentation, time tracking
- Serialization to markdown format

**Storage Layer** (`markdown_handler.py`)
- File I/O operations for markdown persistence
- Parses markdown into task objects
- Handles time metadata parsing (est:5m, actual:10m, etc.)
- Graceful error handling for missing/corrupted files

**Business Logic Layer** (`business_logic/`)
- `date_navigator.py`: Date parsing and navigation (natural language support)
- `task_operations.py`: Hierarchical task operations (parent/child groups, siblings)
- `time_tracker.py`: Active timer management and time accumulation
- `scoring.py`: Gamified scoring system with efficiency multiplier

**Presentation Layer** (`ui/`)
- `task_list_widget.py`: Renders task list with visual hierarchy
- `help_screen.py`: Help modal with keyboard shortcuts
- `widgets.py`: Reusable UI components

## Development

### Project Structure
```
tTask/
├── app.py                      # Main application
├── models.py                   # Data layer: Task models
├── markdown_handler.py         # Storage layer: File I/O
├── config.py                   # Centralized configuration
├── business_logic/             # Business logic layer
│   ├── date_navigator.py       # Date parsing (natural language)
│   ├── task_operations.py      # Hierarchical task operations
│   ├── time_tracker.py         # Active timer & time tracking
│   └── scoring.py              # Gamified scoring system
├── ui/                         # Presentation layer
│   ├── help_screen.py          # Help modal
│   ├── task_list_widget.py     # Task list rendering
│   └── widgets.py              # Reusable UI components
└── tests/                      # Test suite (63+ tests)
    ├── test_task_operations.py
    ├── test_date_parser.py
    └── test_task_list_widget.py
```

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_task_list_widget.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Code Quality
- **Type hints**: Full type annotations throughout
- **Layered architecture**: Clear separation of data, storage, business logic, and UI
- **Comprehensive tests**: 63+ tests covering edge cases and core functionality
- **Comprehensive docstrings**: Google-style docstrings with examples
- **Clean code**: Proper error handling, consistent style, no technical debt
