# Changelog

## 2025-11-07 - Update 6: Context-Aware Task Addition

### Changed
- **Smart task addition based on context**: Pressing 'a' now intelligently places new tasks
  - When on a **child task** (indented): Inserts new task right below as sibling at same indent level
  - When on a **parent task** (indent 0): Adds new task at bottom of list as parent
  - Makes it natural to add siblings when working in a group, and add new parents at top level
  - Stores insert position and indent level in `action_add_task()`
  - Applies stored values in `on_input_submitted()`

### Example
```
Before (child selected):        After pressing 'a' + typing:
Task 1                          Task 1
  Task 2 ← selected               Task 2
  Task 3                          NEW SIBLING ← indent 1
Task 4                            Task 3
                                Task 4

Before (parent selected):       After pressing 'a' + typing:
Task 1 ← selected               Task 1
  Task 2                          Task 2
Task 3                          Task 3
                                NEW PARENT ← indent 0, at bottom
```

## 2025-11-07 - Update 5: Smart Navigation & Natural Language

### Added
- **Skip empty days navigation**: Shift+Left/Right now jump to previous/next day with tasks
  - Added `find_prev_non_empty_day()` and `find_next_non_empty_day()` helpers
  - Searches up to 365 days in each direction for non-empty days
  - Bound to `Shift+←` and `Shift+→`

- **Natural language date parsing for task movement**: Press 'm' and use friendly date formats
  - **Relative words**: `tomorrow`, `yesterday`, `next week`, `last week`
  - **Day names**: `monday`, `tuesday`, etc. (next occurrence)
  - **Month + day**: `nov 10`, `december 25` (current year, auto-adjusts if past)
  - **Keeps existing**: `+1`, `-1` (relative offsets) and `YYYY-MM-DD` (ISO format)
  - Added `parse_natural_date()` method with comprehensive date parsing
  - Updated move task placeholder to show example formats

## 2025-11-07 - Update 4: Smart Scrolling

### Added
- **Edge-triggered scrolling for long task lists**: Task list now scrolls only when selected task reaches viewport edges
  - Added `overflow-y: auto` CSS to task list container
  - Implemented `get_visible_line_number()` to calculate line positions accounting for folded tasks
  - Added `scroll_to_selected()` with viewport detection to scroll only when necessary
  - Scrolls when navigating past the top or bottom of the visible area
  - Natural scrolling behavior - no unnecessary scrolling when task is already visible
  - Works with arrow keys, task addition, folding/unfolding, and task movement

## 2025-11-07 - Update 3: Hierarchical Movement

### Changed
- **Task movement respects hierarchy**: Shift+Up/Down now only swaps tasks with siblings at the same indent level
  - Child tasks stay under their parent when moved
  - Top-level tasks only swap with other top-level tasks
  - Maintains parent-child relationships during movement
  - Added `find_prev_sibling_group()` and `find_next_sibling_group()` helpers

### Example
```
Before:          After Shift+Up on Task 3:
Task 1           Task 1
  Task 2           Task 3      <- swapped
  Task 3           Task 2      <- with sibling
Task 4           Task 4
```

## 2025-11-07 - Update 2: Selection & Movement Fixes

### Fixed
- **Selection tracking with folding**: Fixed bug where selection could land on hidden (folded) tasks, causing wrong tasks to be modified
  - Added `is_task_visible()` to check if tasks are hidden by folded parents
  - Updated `move_selection()` to skip hidden tasks when navigating
  - Added validation in `refresh_task_list()` to ensure selection always points to visible task
- **Fold indicator alignment**: Fixed visual misalignment where fold arrows made tasks appear more indented
  - Fold indicator now always uses 2 characters (▼, ▶, or two spaces) for consistent alignment
  - Moved fold indicator before task indent for clearer hierarchy
- **Task movement logic**: Fixed Shift+Up/Down to properly swap entire task groups (parent + all children)
  - Added `find_group_root()` to correctly identify group boundaries
  - Groups now move as complete units preserving hierarchy

## 2025-11-07 - Update 1: New Features & Bug Fixes

### Added
- **Folding Support**: Press `f` to collapse/expand child tasks under a parent
  - Visual indicators: `▼` (expanded) and `▶` (collapsed)
  - Children are hidden when parent is folded
- **Task Movement**: Use `Shift+↑/↓` to move tasks up and down
  - Parent tasks move together with all their children
  - Groups maintain their hierarchical structure
- **Strikethrough styling**: Completed tasks now show with strikethrough effect

### Fixed
- **Checkbox rendering**: Escaped square brackets `\[x]` and `\[ ]` so they display correctly instead of being interpreted as Rich markup tags
- **Tab key binding**: Added explicit Tab/Shift+Tab handling in `on_key()` to prevent Textual's focus system from intercepting these keys
- **Task list refresh**: Improved widget refresh logic with `refresh(layout=True)` and better selected_index validation
- **Strikethrough visibility**: Changed from `[dim][strikethrough]` to `[strike]` for better visibility in dark terminals

### Issues Resolved
1. Checkboxes now display properly as `[x]` and `[ ]`
2. Tab/Shift+Tab now correctly indent/unindent tasks
3. Tasks added with 'a' key now save and display immediately
4. Strikethrough effect now visible in iTerm2 dark mode
