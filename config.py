"""Configuration settings for task journal application."""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Application configuration settings.

    Centralized configuration to avoid hardcoded values throughout the codebase.
    """
    # File system
    base_dir: Path = Path("~/tasks").expanduser()

    # Task limits
    max_indent_level: int = 5
    max_search_days: int = 365

    # Colors
    color_primary: str = "#0abdc6"  # Cyan - primary accent
    color_accent: str = "#ff006e"  # Pink - selection highlight
    color_secondary: str = "#8b5cf6"  # Purple - secondary accent
    color_bg_dark: str = "#1a1a2e"  # Dark background
    color_bg_medium: str = "#2d2d44"  # Medium background
    color_text: str = "#e2e8f0"  # Light text
    color_text_dim: str = "#ffffff"  # White text

    @classmethod
    def load(cls) -> 'Config':
        """
        Load configuration.

        Future: Could load from config file or environment variables.
        For now, returns default configuration.

        Returns:
            Config instance with default or loaded values
        """
        return cls()


# Global config instance
config = Config.load()
