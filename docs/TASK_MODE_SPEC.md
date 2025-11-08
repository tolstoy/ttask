# Task Mode Feature Specification

## Overview

### What is Task Mode?
Task Mode transforms tTask into a **Workflowy-style outliner** where you can rapidly create, edit, and organize tasks inline. Instead of entering a single task and returning to navigation mode, Task Mode keeps you in an active editing state for continuous task management.

### Why Task Mode?
- **Speed**: Capture thoughts quickly without repeated keystrokes
- **Flow**: Stay in "input mode" for brainstorming and planning sessions
- **Familiar**: Workflowy/Roam-style interaction that many users know and love
- **Efficiency**: Organize as you go with inline indent/move operations

### High-Level User Experience
1. Press `a` to enter Task Mode
2. The currently selected task becomes editable (cursor appears in text)
3. Navigate between tasks with arrow keys while editing
4. Press Enter to split current task and create new one below
5. Use Tab/Shift+Tab to adjust indentation
6. Use Shift+Up/Down to move tasks around
7. Press Escape to exit Task Mode (stay on current day)
8. Or press Shift+Left/Right to exit and navigate to different days

---

## User Interface Behavior

### Entering Task Mode
**Trigger**: Press `a` while in normal navigation mode

**What Happens**:
1. App enters Task Mode state
2. Input widget appears with current task's content
3. Input is focused (cursor appears)
4. Footer updates to show "TASK MODE" indicator
5. Selection remains on current task

**Visual Indicators**:
- Footer shows: `TASK MODE - Enter: Split  •  Esc: Exit`
- Input border color changes (distinct from normal input)
- Selected task remains highlighted

### Inline Editing
**Behavior**: Input always shows the content of the currently selected task

**Edit Flow**:
1. Type to modify current task content
2. Changes are auto-saved to the task (debounced)
3. Task list display updates in real-time
4. Checkbox state preserved

**Auto-Save**:
- Changes debounced (300ms delay)
- Prevents file I/O on every keystroke
- Flush on mode exit to ensure no data loss

### Navigation (Up/Down Arrows)
**Behavior**: Move selection between tasks while staying in edit mode

**Flow**:
1. User presses Up or Down arrow
2. Current input content saved to current task
3. Selection moves to next/previous visible task
4. Input content updates to show new task's content
5. Cursor position attempts to preserve column (if possible)

**Skipping**:
- Automatically skips folded (hidden) tasks
- Same visibility logic as normal navigation mode
- Wraps at top/bottom (stays at first/last task)

**Example**:
```
Task 1: "Buy milk"     ← Selected, input shows "Buy milk"
Task 2: "Call mom"
Task 3: "Write email"

[Press Down]

Task 1: "Buy milk"
Task 2: "Call mom"     ← Selected, input now shows "Call mom"
Task 3: "Write email"
```

### Creating Tasks (Enter Key)
**Behavior**: Workflowy-style splitting - breaks current task at cursor position

**Flow**:
1. User positions cursor in text: "Buy milk and eggs"
2. Cursor is after "milk": "Buy milk|and eggs"
3. Press Enter
4. Left part stays: "Buy milk" (current task)
5. Right part becomes new task: "and eggs" (inserted below)
6. Selection moves to new task
7. Input shows: "and eggs" with cursor at start

**Edge Cases**:
- **Cursor at start**: Empty string stays, full content moves to new task
- **Cursor at end**: Current task unchanged, empty task created below
- **Empty input**: Create empty task below, keep selection on it

**Indent Inheritance**:
- New task inherits indent level of split task
- Maintains outline structure

**Example Sequence**:
```
Before: "Buy groceries: milk, eggs, bread"
           cursor here ↑

After Enter:
Task 1: "Buy groceries:"
Task 2: " milk, eggs, bread"  ← cursor here, editing this
```

### Indentation (Tab/Shift+Tab)
**Behavior**: Adjust indent level of currently selected task

**Tab (Indent)**:
1. Increases indent level by 1 (max 5 levels)
2. Task becomes child of previous task at lower level
3. Input content unchanged
4. Cursor position preserved
5. Visual indent updates immediately

**Shift+Tab (Unindent)**:
1. Decreases indent level by 1 (min 0)
2. Task becomes sibling of parent
3. Input content unchanged
4. Cursor position preserved
5. Visual indent updates immediately

**Limitations**:
- Cannot indent beyond level 5
- Cannot unindent below level 0
- Indent validation same as normal mode

**Example**:
```
Before Tab:
  Task 1
  Task 2        ← Selected in task mode
  Task 3

After Tab:
  Task 1
    Task 2      ← Now indented, still selected
  Task 3
```

### Moving Tasks (Shift+Up/Down)
**Behavior**: Move currently selected task (and children) up/down within same level

**Shift+Up**:
1. Swaps current task with previous sibling at same indent
2. Moves task group (task + all children)
3. Input content unchanged
4. Selection follows task to new position
5. Cursor position preserved

**Shift+Down**:
1. Swaps current task with next sibling at same indent
2. Moves task group (task + all children)
3. Input content unchanged
4. Selection follows task to new position
5. Cursor position preserved

**Limitations**:
- Only moves within same indent level (sibling swapping)
- Cannot move if no sibling in that direction
- Respects hierarchy (parent/child structure maintained)

**Usage in Task Mode**:
- Allows real-time organization while brainstorming
- No need to exit task mode to reorganize
- Smooth workflow for capturing and structuring thoughts

### Exiting Task Mode

#### Option 1: Escape (Stay on Current Day)
**Trigger**: Press `Escape` while in Task Mode

**Behavior**:
1. Save current input content to task (flush debounced save)
2. Remove input widget
3. Exit Task Mode, return to normal navigation
4. Selection remains on last edited task
5. Stay on current date
6. Footer returns to normal: "Press H for Help • Q to Quit"

**Use Case**: Done adding tasks, want to review or navigate

#### Option 2: Shift+Left (Previous Non-Empty Day)
**Trigger**: Press `Shift+Left` while in Task Mode

**Behavior**:
1. Save current input content to task (flush debounced save)
2. Exit Task Mode
3. Navigate to previous day with incomplete tasks
4. Selection resets to first task of that day
5. Normal navigation mode active

**Use Case**: Finished with today, want to review yesterday's tasks

#### Option 3: Shift+Right (Next Non-Empty Day)
**Trigger**: Press `Shift+Right` while in Task Mode

**Behavior**:
1. Save current input content to task (flush debounced save)
2. Exit Task Mode
3. Navigate to next day with incomplete tasks
4. Selection resets to first task of that day
5. Normal navigation mode active

**Use Case**: Quickly jump to future date to add tasks

---

## Detailed Key Bindings

### Task Mode Key Bindings (when Input is focused)

| Key | Action | Description |
|-----|--------|-------------|
| **Text Input** | Any character | Edit current task content |
| **Enter** | Split & Create | Split at cursor, create task with right part |
| **Up** | Previous Task | Save current, select previous, load content |
| **Down** | Next Task | Save current, select next, load content |
| **Left** | Cursor Left | Move cursor left (native Input behavior) |
| **Right** | Cursor Right | Move cursor right (native Input behavior) |
| **Tab** | Indent | Increase indent level of current task |
| **Shift+Tab** | Unindent | Decrease indent level of current task |
| **Shift+Up** | Move Task Up | Swap task group with previous sibling |
| **Shift+Down** | Move Task Down | Swap task group with next sibling |
| **Shift+Left** | Exit & Prev Day | Save, exit task mode, go to previous day |
| **Shift+Right** | Exit & Next Day | Save, exit task mode, go to next day |
| **Escape** | Exit Task Mode | Save and return to normal navigation |
| **Backspace** | Delete Char | Delete character before cursor |
| **Delete** | Delete Char | Delete character after cursor |
| **Home** | Cursor Home | Move cursor to start of line |
| **End** | Cursor End | Move cursor to end of line |
| **Ctrl+A** | Select All | Select all text (native Input) |

### Normal Mode Key Bindings (for comparison)

| Key | Action | Description |
|-----|--------|-------------|
| **a** | Enter Task Mode | Enter Workflowy-style editing mode |
| **e** | Edit Task | One-off edit (traditional mode) |
| **Up/Down** | Navigate | Move selection between tasks |
| **Tab** | Indent | Indent selected task |
| **Shift+Tab** | Unindent | Unindent selected task |
| **Shift+Up/Down** | Move Task | Move task up/down in list |
| **Space/x** | Toggle Complete | Mark task complete/incomplete |
| **d** | Delete Task | Remove selected task |
| **f** | Fold/Unfold | Collapse/expand children |
| **m** | Move to Date | Move task to another day |
| **Left/Right** | Change Day | Navigate to prev/next day |
| **Shift+Left/Right** | Skip Days | Jump to prev/next non-empty day |
| **t** | Today | Jump to today's date |
| **h** | Help | Show keyboard shortcuts |
| **q** | Quit | Exit application |

### Disabled in Task Mode
The following normal mode keys are **disabled** when Task Mode is active (Input has focus):
- `e` (edit) - already editing
- `Space`/`x` (toggle complete) - would interfere with typing
- `d` (delete) - use Backspace/Delete for text
- `f` (fold) - disabled for simplicity
- `m` (move to date) - disabled for simplicity
- `Left`/`Right` without Shift - used for cursor movement
- `h` (help) - disabled (could add Ctrl+H if needed)
- `q` (quit) - disabled (use Escape then q)
- `t` (today) - disabled

---

## Technical Implementation

### Architecture Overview

```
TaskJournalApp
├── task_mode: bool (state flag)
├── task_mode_input: TaskModeInput | None (widget reference)
├── action_add_task() → Enters task mode
├── exit_task_mode() → Cleans up and returns to normal
└── TaskModeInput (custom widget)
    ├── Intercepts special keys
    ├── Emits custom messages for app to handle
    └── Manages cursor position
```

### Custom Widget: TaskModeInput

```python
class TaskModeInput(Input):
    """Custom Input widget that intercepts task mode keys."""

    BINDINGS = [
        Binding("up", "navigate_up", "Previous Task", show=False),
        Binding("down", "navigate_down", "Next Task", show=False),
        Binding("enter", "split_task", "Split & Create", show=False),
        Binding("tab", "indent_task", "Indent", show=False),
        Binding("shift+tab", "unindent_task", "Unindent", show=False),
        Binding("shift+up", "move_task_up", "Move Up", show=False),
        Binding("shift+down", "move_task_down", "Move Down", show=False),
        Binding("shift+left", "exit_and_prev_day", "Exit & Prev Day", show=False),
        Binding("shift+right", "exit_and_next_day", "Exit & Next Day", show=False),
        Binding("escape", "exit_task_mode", "Exit", show=False),
    ]

    def action_navigate_up(self):
        """Navigate to previous task."""
        self.post_message(TaskModeNavigate(direction=-1))

    def action_navigate_down(self):
        """Navigate to next task."""
        self.post_message(TaskModeNavigate(direction=1))

    def action_split_task(self):
        """Split task at cursor position."""
        cursor_pos = self.cursor_position
        self.post_message(TaskModeSplit(cursor_position=cursor_pos))

    # ... other action methods
```

### State Management

```python
class TaskJournalApp(App):
    def __init__(self):
        # ... existing init
        self.task_mode = False
        self.task_mode_input = None

    def action_add_task(self):
        """Enter task mode (new behavior)."""
        if self.task_mode:
            return  # Already in task mode

        # Enter task mode
        self.task_mode = True

        # Get current task
        task_widget = self.query_one(TaskListWidget)
        task = task_widget.get_selected_task()

        # Create and mount input
        container = self.query_one("#input_container")
        self.task_mode_input = TaskModeInput(
            value=task.content if task else "",
            placeholder="Enter tasks... (Esc to exit)"
        )
        container.mount(self.task_mode_input)
        self.task_mode_input.focus()

        # Update footer
        self.update_footer_for_task_mode()

    def exit_task_mode(self):
        """Exit task mode and return to normal navigation."""
        if not self.task_mode:
            return

        # Save current content
        self.save_current_input_to_task()

        # Remove input widget
        if self.task_mode_input:
            self.task_mode_input.remove()
            self.task_mode_input = None

        # Exit state
        self.task_mode = False

        # Restore footer
        self.update_footer_normal()

        # Flush any pending saves
        self.save_current_tasks()
```

### Input Content Synchronization

```python
def on_task_mode_navigate(self, event: TaskModeNavigate):
    """Handle navigation in task mode."""
    # Save current input to current task
    self.save_current_input_to_task()

    # Move selection
    task_widget = self.query_one(TaskListWidget)
    task_widget.move_selection(event.direction)

    # Load new task content into input
    task = task_widget.get_selected_task()
    if task:
        self.task_mode_input.value = task.content
        # Try to preserve cursor position (or move to end)
        self.task_mode_input.cursor_position = len(task.content)

    # Scroll to keep selected task visible
    task_widget.scroll_to_selected()

def save_current_input_to_task(self):
    """Save input content back to currently selected task."""
    if not self.task_mode or not self.task_mode_input:
        return

    task_widget = self.query_one(TaskListWidget)
    task = task_widget.get_selected_task()

    if task:
        task.content = self.task_mode_input.value
        # Debounced save (don't write to disk immediately)
        self.save_manager.mark_dirty()
        # Refresh display
        self.refresh_task_list()
```

### Enter Key Splitting Logic

```python
def on_task_mode_split(self, event: TaskModeSplit):
    """Split current task at cursor position."""
    cursor_pos = event.cursor_position
    current_text = self.task_mode_input.value

    # Split text
    left_part = current_text[:cursor_pos]
    right_part = current_text[cursor_pos:]

    # Update current task with left part
    task_widget = self.query_one(TaskListWidget)
    task = task_widget.get_selected_task()
    if task:
        task.content = left_part

    # Create new task with right part
    insert_index = task_widget.selected_index + 1
    indent_level = task.indent_level if task else 0

    self.daily_list.add_task(
        right_part,
        indent_level=indent_level,
        index=insert_index
    )

    # Move selection to new task
    task_widget.selected_index = insert_index

    # Update input to show new task (right part)
    self.task_mode_input.value = right_part
    self.task_mode_input.cursor_position = 0  # Cursor at start

    # Save and refresh
    self.save_manager.mark_dirty()
    self.refresh_task_list()
```

### Save/Refresh Behavior

**Debounced Saves**:
- Input changes trigger `mark_dirty()` on save manager
- Save manager waits 300ms before writing to disk
- If another change happens within 300ms, timer resets
- Prevents excessive file I/O during rapid typing

**Flush on Exit**:
- When exiting task mode, call `save_manager.flush()`
- Ensures no unsaved changes lost
- Immediate write to disk

**Refresh Strategy**:
- After every task modification, call `refresh_task_list()`
- Updates visual display in real-time
- Does not trigger file I/O (only UI update)

---

## Edge Cases & Behavior

### Empty Task Handling

**Creating Empty Tasks**:
- Pressing Enter with empty input creates empty task below
- Selection moves to new empty task
- Allows rapid structure creation (indents without content)

**Deleting All Content**:
- Backspace in empty task does NOT delete the task
- Task remains with empty content
- Use normal mode `d` key to delete tasks

**Navigation Through Empty Tasks**:
- Up/Down arrows navigate through empty tasks normally
- Empty tasks are valid placeholders

### First/Last Task Navigation

**At First Task**:
- Up arrow does nothing (stays on first task)
- No wrap-around to last task
- Prevents accidental jumps

**At Last Task**:
- Down arrow does nothing (stays on last task)
- No wrap-around to first task
- Consistent with up behavior

### Indent Limits

**Maximum Indent (5)**:
- Tab key does nothing when indent is 5
- Visual feedback: border flash or subtle indication
- Prevents deeply nested structures

**Minimum Indent (0)**:
- Shift+Tab does nothing when indent is 0
- Already at root level
- Prevents negative indent

### Cursor Position Preservation

**Between Tasks**:
- When navigating Up/Down, try to preserve cursor column
- If new task shorter, move to end
- If new task longer, keep same column position

**After Split**:
- New task: cursor at start (position 0)
- Makes sense - you just created content from split

**After Move (Shift+Up/Down)**:
- Cursor position unchanged
- Content unchanged
- Only visual position in list changes

### Unsaved Changes

**On Exit**:
- All changes flushed to disk immediately
- No confirmation dialog needed
- Auto-save ensures no data loss

**On Day Navigation**:
- Current task saved before navigating
- New day loads fresh tasks
- Previous day changes persisted

**On App Crash**:
- Recent changes may be lost if within debounce window (300ms)
- Acceptable trade-off for performance
- Could add periodic background saves if needed

---

## Visual Design

### Footer Updates

**Normal Mode**:
```
Press H for Help  •  Q to Quit
```

**Task Mode**:
```
TASK MODE  •  Enter: Split  •  ↑↓: Navigate  •  Tab: Indent  •  Esc: Exit
```

Or more compact:
```
TASK MODE - Enter: Split  •  Esc: Exit  •  H: Help
```

### Input Styling

**Normal Input** (edit, move, add):
```css
Input {
    border: tall #8b5cf6;  /* Purple */
}

Input:focus {
    border: tall #0abdc6;  /* Cyan */
}
```

**Task Mode Input**:
```css
TaskModeInput {
    border: tall #0abdc6;  /* Always cyan */
    background: #2d2d44;   /* Darker to distinguish */
}

TaskModeInput:focus {
    border: thick #0abdc6;  /* Thicker border */
    background: #3d3d54;    /* Slightly lighter */
}
```

### Selection Highlighting

**Normal Mode**:
- Selected task highlighted with reverse colors
- Clear visual indicator

**Task Mode**:
- Selected task highlighted same way
- Input content matches selected task
- Both input and selection are same task (double reinforcement)

---

## Implementation Phases

### Phase 1: Basic Inline Editing
**Goal**: Get basic task mode working with navigation

**Tasks**:
1. Create TaskModeInput widget with Up/Down bindings
2. Add task_mode flag to app state
3. Modify action_add_task() to enter task mode
4. Implement on_task_mode_navigate() handler
5. Save input to task on navigation
6. Load task content into input on navigation
7. Add Escape binding to exit task mode

**Acceptance Criteria**:
- Press `a` to enter task mode
- Type to edit current task
- Up/Down navigates between tasks, updating input
- Escape exits task mode
- Changes are saved

**Estimated Effort**: 4-6 hours

### Phase 2: Enter Splitting
**Goal**: Implement Workflowy-style Enter behavior

**Tasks**:
1. Add Enter binding to TaskModeInput
2. Capture cursor position on Enter
3. Implement split logic (left/right parts)
4. Create new task with right part
5. Move selection to new task
6. Update input content

**Acceptance Criteria**:
- Enter splits task at cursor
- Left part stays in original task
- Right part becomes new task below
- Cursor moves to start of new task
- Works with empty input (creates empty task)

**Estimated Effort**: 3-4 hours

### Phase 3: Full Key Binding Support
**Goal**: Add all remaining task mode operations

**Tasks**:
1. Add Tab/Shift+Tab bindings for indent/unindent
2. Add Shift+Up/Down bindings for move task
3. Add Shift+Left/Right bindings for day navigation + exit
4. Implement handlers for each operation
5. Ensure cursor position preserved appropriately

**Acceptance Criteria**:
- Tab/Shift+Tab adjusts indent while editing
- Shift+Up/Down moves tasks while editing
- Shift+Left/Right exits and navigates days
- All operations maintain input content
- Cursor position handled correctly

**Estimated Effort**: 4-5 hours

### Phase 4: Polish & Edge Cases
**Goal**: Handle edge cases and improve UX

**Tasks**:
1. Implement debounced save manager
2. Add footer status updates
3. Test and fix edge cases (first/last task, indent limits, empty tasks)
4. Add visual styling for task mode input
5. Optimize performance (if needed)
6. Add error handling
7. Update help documentation

**Acceptance Criteria**:
- No performance issues during rapid typing
- All edge cases handled gracefully
- Visual feedback clear
- Help text updated
- No data loss scenarios

**Estimated Effort**: 5-6 hours

### Total Estimated Effort
**16-21 hours** for full task mode implementation

---

## Dependencies & Prerequisites

### Required Refactorings
Before implementing task mode, these refactorings are **highly recommended**:

1. **Debounced Save Manager** (CRITICAL)
   - Task mode will save on every keystroke
   - Need debouncing to prevent performance issues
   - 300ms delay recommended

2. **State Machine** (HIGHLY RECOMMENDED)
   - Adding `task_mode` flag to existing boolean flags is messy
   - State enum makes mode management cleaner
   - Easier to reason about valid state transitions

3. **Input Handler Extraction** (RECOMMENDED)
   - Task mode adds another input submission path
   - Extracting to separate handler makes code cleaner
   - Not blocking but makes maintenance easier

### Optional Refactorings
Nice to have but not blocking:

1. **Task Operations Manager**
   - Cleaner save/refresh abstraction
   - Batching support
   - Not critical for task mode

2. **Selection Manager**
   - Task mode reuses existing selection logic
   - Extraction would be cleaner but not required

---

## Testing Strategy

### Manual Testing Checklist

**Basic Operations**:
- [ ] Enter task mode with `a`
- [ ] Edit current task content
- [ ] Navigate with Up/Down
- [ ] Input updates to match selected task
- [ ] Exit with Escape
- [ ] Changes are saved

**Enter Splitting**:
- [ ] Split in middle of text
- [ ] Split at start (cursor at position 0)
- [ ] Split at end (cursor at end)
- [ ] Split empty task
- [ ] New task inherits indent
- [ ] Cursor moves to new task

**Indentation**:
- [ ] Tab increases indent
- [ ] Shift+Tab decreases indent
- [ ] Cannot exceed indent 5
- [ ] Cannot go below indent 0
- [ ] Input content preserved
- [ ] Cursor position preserved

**Task Movement**:
- [ ] Shift+Up moves task up
- [ ] Shift+Down moves task down
- [ ] Only moves within same level
- [ ] Cannot move at boundaries
- [ ] Children move with parent
- [ ] Input content preserved

**Day Navigation**:
- [ ] Shift+Left exits and goes to previous day
- [ ] Shift+Right exits and goes to next day
- [ ] Changes saved before navigation
- [ ] Loads tasks from new day

**Edge Cases**:
- [ ] First task: Up does nothing
- [ ] Last task: Down does nothing
- [ ] Empty task handling
- [ ] Folded tasks skipped
- [ ] Very long task content
- [ ] Special characters in content
- [ ] Unicode support

### Unit Testing (Future)

**Components to Test**:
1. Cursor position splitting logic
2. Task insertion at index
3. Indent validation
4. Movement constraints
5. Save debouncing
6. State transitions

---

## Open Questions & Future Enhancements

### Open Questions
1. Should we support **multi-line tasks** in task mode?
   - Would require TextArea widget instead of Input
   - More complex cursor handling
   - Defer to future iteration

2. Should **delete key behavior** be special in task mode?
   - Ctrl+D to delete entire task?
   - Backspace at position 0 to merge with previous?
   - Keep simple for v1

3. Should we add **undo/redo** support?
   - Complex to implement
   - Very valuable for editing
   - Defer to future enhancement

### Future Enhancements
1. **Rich Text Support**
   - Bold, italic, links
   - Would need markdown rendering in Input
   - Complex but powerful

2. **Search in Task Mode**
   - Ctrl+F to search tasks
   - Navigate between matches
   - Stay in edit mode

3. **Batch Operations**
   - Select multiple tasks
   - Bulk indent/move/delete
   - Would need selection model

4. **Keyboard Macros**
   - Record and replay sequences
   - Speed up repetitive tasks

5. **Task Templates**
   - Quick insertion of common structures
   - Project templates
   - Daily routine templates

6. **Smart Auto-Complete**
   - Suggest completions based on history
   - Tag auto-complete
   - Date shortcuts

---

## Success Metrics

How will we know task mode is successful?

1. **User Adoption**: Users prefer task mode over traditional `a` add
2. **Speed**: Can add 10+ tasks in under 30 seconds
3. **Stability**: No crashes or data loss
4. **Performance**: No lag during typing or navigation
5. **User Feedback**: Positive comments about Workflowy-style UX

---

## Document History

- **2025-11-08**: Initial specification created
- **Version**: 1.0
- **Status**: Planning / Pre-Implementation
- **Author**: Claude Code (with user collaboration)

