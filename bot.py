"""Sentinel - moderation & security bot. Run with:  python bot.py"""
import logging
import traceback
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

import config
from database import Database
from utils import embeds
from utils.errors import ModError, PremiumRequired
from utils.modservice import ModService
from utils.premium import PremiumManager
from utils.settings import SettingsManager

log = logging.getLogger("sentinel")


class SentinelTree(app_commands.CommandTree):
    """Central error handling for every slash command."""

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        view = None
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        if isinstance(error, ModError):
            embed = embeds.error(str(error))
        elif isinstance(error, PremiumRequired):
            f = error.feature
            embed = embeds.make(
                f"**{f.name}** is a **{f.tier.title()}** feature.\n{f.description}\n\n"
                f"Use `/premium status` to see your plan, or `/premium redeem` if you have a code.",
                title="🔒 Premium feature", color=embeds.Colors.INFO,
            )
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Upgrade", url=config.PREMIUM_URL))
        elif isinstance(error, app_commands.MissingPermissions):
            need = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
            embed = embeds.error(f"You need the **{need}** permission (or the server's mod role) to use this.")
        elif isinstance(error, app_commands.BotMissingPermissions):
            need = ", ".join(p.replace("_", " ").title() for p in error.missing_permissions)
            embed = embeds.error(f"I'm missing the **{need}** permission.")
        elif isinstance(error, app_commands.NoPrivateMessage):
            embed = embeds.error("This command only works inside a server.")
        elif isinstance(error, app_commands.CommandOnCooldown):
            embed = embeds.error(f"Slow down! Try again in {error.retry_after:.0f}s.")
        elif isinstance(error, app_commands.CheckFailure):
            embed = embeds.error(str(error) or "You can't use this command.")
        elif isinstance(error, discord.Forbidden):
            embed = embeds.error("I don't have permission to do that. Check my role position and permissions.")
        else:
            name = interaction.command.qualified_name if interaction.command else "unknown"
            log.error("Unhandled error in /%s", name, exc_info=error)
            traceback.print_exception(type(error), error, error.__traceback__)
            embed = embeds.error("Something went wrong while running that command. The error was logged.")

        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(content=None, embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        except discord.HTTPException:
            pass


class Sentinel(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True            # privileged: joins, role changes, anti-raid
        intents.message_content = True    # privileged: automod, ticket transcripts
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            owner_ids=config.OWNER_IDS or None,
            help_command=None,
            tree_cls=SentinelTree,
            allowed_mentions=discord.AllowedMentions.none(),  # opt in per message where pings are wanted
            activity=discord.Activity(type=discord.ActivityType.watching, name="over the server"),
        )
        self.db = Database(config.DB_PATH)
        self.settings = SettingsManager(self.db)
        self.premium = PremiumManager(self.db)
        self.mod = ModService(self)

    async def setup_hook(self) -> None:
        await self.db.connect()

        for path in sorted(Path(__file__).parent.joinpath("cogs").glob("*.py")):
            if path.stem.startswith("_"):
                continue
            await self.load_extension(f"cogs.{path.stem}")
            log.info("Loaded cog: %s", path.stem)

        if config.SYNC_COMMANDS:
            if config.DEV_GUILD_ID:
                guild = discord.Object(id=config.DEV_GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                log.info("Synced %d commands to dev guild %s", len(synced), config.DEV_GUILD_ID)
            else:
                synced = await self.tree.sync()
                log.info("Synced %d global commands (can take up to an hour to appear everywhere)", len(synced))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (%s) in %d servers", self.user, self.user.id, len(self.guilds))

    async def close(self) -> None:
        await self.db.close()
        await super().close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not config.TOKEN:
        raise SystemExit("DISCORD_TOKEN is missing. Copy .env.example to .env and fill it in.")
    Sentinel().run(config.TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
