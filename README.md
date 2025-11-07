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
