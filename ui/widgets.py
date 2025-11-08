"""Custom UI widgets for task journal."""
from textual.widgets import Static


class CenteredFooter(Static):
    """Custom footer with centered content."""

    def __init__(self):
        super().__init__()
        self.update("[dim]Press[/dim] [bold]H[/bold] [dim]for Help  •  [/dim][bold]Q[/bold] [dim]to Quit[/dim]")

    DEFAULT_CSS = """
    CenteredFooter {
        background: transparent;
        color: #0abdc6;
        dock: bottom;
        height: 1;
        text-align: center;
        border: thick #0abdc6;
    }
    """
