"""
config.py
Shared constants used across the bot. Safe to edit freely.
"""

# Embed color scheme
COLOR_SUCCESS = 0x57F287
COLOR_ERROR = 0xED4245
COLOR_WARNING = 0xFEE75C
COLOR_INFO = 0x5865F2
COLOR_DEFAULT = 0x2B2D31

# Credit line shown in embed footers, /credits, and bot presence.
# This is intentionally centralized here so it can't be missed when editing the code.
BOT_CREDIT = "Made by Fritz"

# Ticket system options
TICKET_CATEGORIES = ["General Support", "Technical Issue", "Billing", "Report a User", "Other"]
TICKET_PRIORITIES = ["Low", "Medium", "High", "Urgent"]

PRIORITY_EMOJI = {
    "Low": "🟢",
    "Medium": "🟡",
    "High": "🟠",
    "Urgent": "🔴",
}

# Leveling
XP_MIN_PER_MESSAGE = 15
XP_MAX_PER_MESSAGE = 25
XP_MESSAGE_COOLDOWN_SECONDS = 60


def xp_for_level(level: int) -> int:
    """Cumulative XP required to reach a given level (MEE6-style curve)."""
    return 5 * (level ** 2) + 50 * level + 100


# Economy
DAILY_REWARD = 200
WORK_MIN_REWARD = 50
WORK_MAX_REWARD = 150
WORK_COOLDOWN_SECONDS = 3600
DAILY_COOLDOWN_SECONDS = 86400
CURRENCY_NAME = "coins"
CURRENCY_EMOJI = "🪙"

# Social alerts polling interval (minutes)
YOUTUBE_CHECK_INTERVAL_MINUTES = 5
TWITCH_CHECK_INTERVAL_MINUTES = 3
