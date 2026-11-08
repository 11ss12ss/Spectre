"""
Premium feature registry  --  THIS IS THE FILE YOU EDIT TO ADD PAID FEATURES.

1. Register the feature here (name, minimum tier, description).
2. Gate a slash command with  @premium_required("your_key")  (see cogs/premium.py -> /modstats),
   or check in code with     await bot.premium.has_feature(guild_id, "your_key").
3. For numeric limits (e.g. "free servers get 25 filter words, premium gets 250") add a LIMITS entry
   and read it with          await bot.premium.limit(guild_id, "your_key").

Tiers are ordered lowest -> highest. Add or rename tiers in TIERS if you want more plans.
"""
from dataclasses import dataclass

TIERS = ["free", "premium", "pro"]


def tier_rank(tier: str) -> int:
    return TIERS.index(tier) if tier in TIERS else 0


@dataclass(frozen=True)
class Feature:
    name: str
    tier: str          # minimum tier required
    description: str


FEATURES: dict[str, Feature] = {
    "ticket_transcripts": Feature(
        "Ticket transcripts", "premium",
        "A full text transcript is saved to your ticket log channel and DMed to the user when a ticket closes.",
    ),
    "mod_analytics": Feature(
        "Moderation analytics", "premium",
        "`/modstats` shows action breakdowns, top moderators and trends for your server.",
    ),
}

# Numeric limits per tier. Any tier not listed falls back to the "free" value.
LIMITS: dict[str, dict[str, int]] = {
    "filter_words":     {"free": 25, "premium": 250, "pro": 1000},   # custom profanity-filter words
    "open_tickets":     {"free": 1,  "premium": 3,   "pro": 5},      # open tickets per user
    "ticket_types":     {"free": 3,  "premium": 10,  "pro": 25},     # ticket categories
    "escalation_rules": {"free": 3,  "premium": 10,  "pro": 10},     # warning auto-escalation rules
}
