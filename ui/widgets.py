"""Custom UI widgets for task journal."""
from textual.widgets import Static


class CenteredFooter(Static):
    """Custom footer with centered content."""

    def __init__(self):
        super().__init__()
        self.update("[dim]Press[/dim] [bold]H[/bold] [dim]for Help  •  [/dim][bold]Q[/bold] [dim]to Quit[/dim]")

    DEFAULT_CSS = """
    CenteredFooter {
        background: #0abdc6;
        color: #ffffff;
        dock: bottom;
        height: 1;
        text-align: center;
    }
    """
