"""
giveaways.py
Button-entry giveaways with a background task that ends them and picks
winners, plus a manual reroll command.
"""
import random
import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

import database as db


def parse_duration(text: str) -> datetime.timedelta:
    """Parse strings like '10m', '2h', '1d' into a timedelta."""
    unit = text[-1].lower()
    amount = int(text[:-1])
    return {
        "s": datetime.timedelta(seconds=amount),
        "m": datetime.timedelta(minutes=amount),
        "h": datetime.timedelta(hours=amount),
        "d": datetime.timedelta(days=amount),
    }[unit]


class GiveawayEnterView(discord.ui.View):
    def __init__(self, giveaway_id: int):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        # custom_id must be static+unique so it survives restarts; encode the id in it
        self.enter.custom_id = f"giveaway:enter:{giveaway_id}"

    @discord.ui.button(label="🎉 Enter", style=discord.ButtonStyle.blurple)
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await db.add_giveaway_entry(self.giveaway_id, interaction.user.id)
        await interaction.response.send_message("You're entered! Good luck 🍀", ephemeral=True)


class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @app_commands.command(name="giveaway-start", description="Start a giveaway")
    async def giveaway_start(self, interaction: discord.Interaction, prize: str, duration: str, winners: int = 1):
        try:
            delta = parse_duration(duration)
        except (ValueError, KeyError, IndexError):
            await interaction.response.send_message("Duration must look like `10m`, `2h`, or `1d`.", ephemeral=True)
            return

        ends_at = datetime.datetime.utcnow() + delta
        giveaway_id = await db.create_giveaway(
            interaction.guild_id, interaction.channel_id, prize, winners, ends_at.isoformat(), interaction.user.id
        )

        embed = discord.Embed(
            title=f"🎉 Giveaway: {prize}",
            description=f"Winners: **{winners}**\nEnds: <t:{int(ends_at.timestamp())}:R>\nHosted by {interaction.user.mention}",
            color=discord.Color.blurple(),
        )
        view = GiveawayEnterView(giveaway_id)
        self.bot.add_view(view)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        await db.set_giveaway_message(giveaway_id, msg.id)

    @app_commands.command(name="giveaway-reroll", description="Reroll winners for an ended giveaway")
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        giveaway = await db.get_giveaway_by_message(int(message_id))
        if not giveaway or giveaway["status"] != "ended":
            await interaction.response.send_message("That giveaway isn't finished (or doesn't exist).", ephemeral=True)
            return

        entries = await db.get_giveaway_entries(giveaway["id"])
        if not entries:
            await interaction.response.send_message("No one entered this giveaway.", ephemeral=True)
            return

        new_winners = random.sample(entries, min(giveaway["winner_count"], len(entries)))
        await db.finish_giveaway(giveaway["id"], new_winners)
        mentions = ", ".join(f"<@{w}>" for w in new_winners)
        await interaction.response.send_message(f"🎉 New winner(s) for **{giveaway['prize']}**: {mentions}")

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        due = await db.get_due_giveaways(datetime.datetime.utcnow().isoformat())
        for g in due:
            channel = self.bot.get_channel(g["channel_id"])
            entries = await db.get_giveaway_entries(g["id"])
            winners = random.sample(entries, min(g["winner_count"], len(entries))) if entries else []
            await db.finish_giveaway(g["id"], winners)

            if channel:
                if winners:
                    mentions = ", ".join(f"<@{w}>" for w in winners)
                    await channel.send(f"🎉 Giveaway for **{g['prize']}** ended! Winner(s): {mentions}")
                else:
                    await channel.send(f"Giveaway for **{g['prize']}** ended with no entries.")

    @check_giveaways.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Giveaways(bot))
