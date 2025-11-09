"""Statistics screen showing time tracking performance metrics."""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import VerticalScroll
from textual.binding import Binding
from textual import events
from business_logic.scoring import DailyScore, ScoringSystem


class StatisticsScreen(Screen):
    """Modal screen showing time tracking statistics."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
    ]

    CSS = """
    StatisticsScreen {
        align: center middle;
        background: rgba(26, 26, 46, 0.9);
    }

    #stats_container {
        width: 80;
        height: auto;
        max-height: 90%;
        background: #2d2d44;
        border: thick #0abdc6;
        padding: 1 2;
    }

    #stats_title {
        text-align: center;
        text-style: bold;
        color: #0abdc6;
        margin-bottom: 1;
    }

    #stats_content {
        height: auto;
        overflow-y: auto;
        color: #e2e8f0;
    }
    """

    def __init__(self, daily_score: DailyScore, streak: int, scoring_system: ScoringSystem):
        """
        Initialize statistics screen.

        Args:
            daily_score: The daily score object with all statistics
            streak: Current streak of consecutive positive-score days
            scoring_system: The scoring system to get historical data
        """
        super().__init__()
        self.daily_score = daily_score
        self.streak = streak
        self.scoring_system = scoring_system

    def compose(self) -> ComposeResult:
        """Compose the statistics screen."""
        with VerticalScroll(id="stats_container"):
            yield Static("Time Tracking Statistics", id="stats_title")
            yield Static(self.get_stats_text(), id="stats_content")

    def get_stats_text(self) -> str:
        """Get formatted statistics text."""
        ds = self.daily_score

        # Score display with color
        score_display = f"{int(ds.total_score)}pts"
        if ds.total_score > 0:
            score_display = f"[green]{score_display}[/green]"
        elif ds.total_score < 0:
            score_display = f"[red]{score_display}[/red]"

        # Streak display
        streak_display = f"[yellow]{self.streak}[/yellow] day{'s' if self.streak != 1 else ''}"
        if self.streak == 0:
            streak_display = "[dim]0 days[/dim]"

        # Efficiency display (lower is better)
        efficiency_pct = int(ds.efficiency_ratio * 100) if ds.total_estimated_minutes > 0 else 100
        if efficiency_pct < 100:
            efficiency_display = f"[green]{efficiency_pct}%[/green] [dim](beat estimates!)[/dim]"
        elif efficiency_pct == 100:
            efficiency_display = f"{efficiency_pct}% [dim](on target)[/dim]"
        else:
            efficiency_display = f"[red]{efficiency_pct}%[/red] [dim](over estimates)[/dim]"

        # Average efficiency over last 7 days
        avg_efficiency_pct = int(self.scoring_system.get_average_efficiency(7) * 100)

        # Build the statistics text
        text = f"""[bold]Daily Summary[/bold]
Date:             {ds.date.strftime('%A, %B %d, %Y')}
Total Score:      {score_display}
Current Streak:   {streak_display}

[bold]Task Completion[/bold]
Tasks Completed:  {ds.tasks_completed}
Beat Estimate:    [green]{ds.tasks_beat_estimate}[/green]
Over Estimate:    [red]{ds.tasks_over_estimate}[/red]

[bold]Time Analysis[/bold]
Estimated Total:  {ds.total_estimated_minutes}m ({ds.total_estimated_minutes // 60}h {ds.total_estimated_minutes % 60}m)
Actual Total:     {ds.total_actual_minutes}m ({ds.total_actual_minutes // 60}h {ds.total_actual_minutes % 60}m)
Efficiency:       {efficiency_display}

[bold]Trends (Last 7 Days)[/bold]
Avg Efficiency:   {avg_efficiency_pct}%

[bold]Scoring System[/bold]
The efficiency multiplier rewards ambitious estimates:
• Formula: points = (estimate - actual) × (100 / (estimate + 10))
• Lower estimates = higher multiplier = more points
• Example: Beat 10m by 5m = 25pts
• Example: Beat 60m by 5m = 7pts

[dim]Press Esc to close this screen[/dim]"""

        return text

    def on_key(self, event: events.Key) -> None:
        """Handle key events - block all except Esc and arrow keys."""
        # Allow Esc (handled by binding) and arrow keys (for scrolling)
        if event.key not in ("escape", "up", "down"):
            event.prevent_default()
            event.stop()

    def action_dismiss(self) -> None:
        """Close the statistics screen."""
        self.dismiss()
