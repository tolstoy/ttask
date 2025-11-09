# Contributing to tTask

Thanks for your interest in contributing! This guide will help you get started with development.

## Development Setup

### Prerequisites
- Python 3.10+
- Git

### Installation
```bash
git clone https://github.com/tolstoy/ttask.git
cd ttask

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# For development with mypy
pip install mypy
```

### Running the Application
```bash
# From the project directory with venv activated
python app.py

# Or use the taskjournal script
./taskjournal
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Test File
```bash
pytest tests/test_task_operations.py -v
```

### With Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### Watch Mode (requires pytest-watch)
```bash
pip install pytest-watch
ptw tests/
```

## Code Structure

The codebase follows a **layered architecture** for maintainability:

### Layers

**Data Layer** (`models.py`)
- Define data structures here
- Add validation logic to model methods
- Keep serialization simple (use `to_markdown()` / `to_dict()` methods)

**Storage Layer** (`markdown_handler.py`)
- Handle all file I/O
- Parse/serialize markdown
- Gracefully handle errors (missing files, corruption)

**Business Logic** (`business_logic/`)
- Core algorithms and operations
- No direct file I/O (use MarkdownHandler)
- No UI code (use Presentation layer for output)
- Examples:
  - `date_navigator.py`: Date parsing and navigation
  - `task_operations.py`: Hierarchical task algorithms
  - `time_tracker.py`: Timer management
  - `scoring.py`: Scoring algorithms

**Presentation Layer** (`ui/`, `app.py`)
- Terminal UI rendering
- User input handling
- Call business logic, don't implement algorithms here

### Import Guidelines
```
Good:
  business_logic/time_tracker.py → models.py, markdown_handler.py
  app.py → business_logic/, ui/
  ui/ → models.py, business_logic/

Avoid:
  models.py → business_logic/ (circular imports)
  ui/ → business_logic/ (tight coupling)
  markdown_handler.py → app.py (reversed dependency)
```

## Adding New Features

### Example: Adding a "due date" Field to Tasks

1. **Data Layer** - Update models
   ```python
   # models.py
   @dataclass
   class Task:
       due_date: Optional[date] = None

       def to_markdown(self) -> str:
           # Include due_date in markdown output
   ```

2. **Storage Layer** - Update markdown handling
   ```python
   # markdown_handler.py
   def load_tasks(self, task_date: date):
       # Parse due_date from markdown comments
       due_date_match = re.search(r'due:(\d{4}-\d{2}-\d{2})', ...)
   ```

3. **Business Logic** - Add operations
   ```python
   # business_logic/task_operations.py (or new file)
   def get_overdue_tasks(tasks: List[Task]) -> List[Task]:
       return [t for t in tasks if t.due_date and t.due_date < date.today()]
   ```

4. **Presentation** - Add UI
   ```python
   # ui/task_list_widget.py
   def _format_task_line(self, task: Task) -> str:
       # Show visual indicator if task is overdue
   ```

5. **Tests** - Add coverage
   ```python
   # tests/test_task_operations.py
   def test_get_overdue_tasks():
       ...
   ```

## Code Quality Standards

### Type Hints
- All functions must have type hints
- Use `Optional[T]` for nullable types
- Use `List[T]`, `Dict[K, V]` from typing module

### Docstrings
- Google-style docstrings for all public functions
- Include: description, args, returns, examples
- Add notes for important behaviors

```python
def my_function(arg1: str, arg2: int) -> bool:
    """Short description.

    Longer description explaining the function behavior,
    edge cases, or important notes.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Example:
        >>> my_function("test", 5)
        True
    """
```

### Testing
- Aim for >80% coverage
- Test edge cases and error conditions
- Use descriptive test names: `test_<function>_<scenario>`

## Type Checking with mypy

### Run Type Check
```bash
mypy .
```

### Configuration
Type checking is configured in `mypy.ini` with reasonable strictness:
- Catches most type errors
- Allows some flexibility for dynamic code

### Common Issues
```python
# Type: ignore comment for deliberate type violations
x = some_untyped_function()  # type: ignore

# Optional chaining
if obj and obj.property:  # Check for None
    use(obj.property)
```

## Code Review Guidelines

When submitting a PR:
1. Ensure tests pass: `pytest tests/ -v`
2. Run type check: `mypy .`
3. Write clear commit messages
4. Update docstrings if behavior changes
5. Include tests for new functionality
6. Keep changes focused (one feature per PR)

## Project Philosophy

- **User-centric**: Changes should improve user experience
- **Maintainability**: Code should be easy to understand and modify
- **Reliability**: Comprehensive tests and error handling
- **Documentation**: Code should explain itself
- **Modularity**: Decoupled layers and single responsibility

## Getting Help

- Check existing issues on GitHub
- Review tests for usage examples
- Read docstrings for function behavior
- Ask questions in issues before starting major work
