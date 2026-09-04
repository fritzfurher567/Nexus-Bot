"""
economy_bank.py
Bank (safe-from-robbery storage), crime (higher risk/reward than work),
and heists (multiplayer buy-in event with a shared payout/bust outcome).
"""
import random
import datetime
import asyncio

import discord
from discord import app_commands
from discord.ext import commands

import database as db

CURRENCY = "£"
CRIME_COOLDOWN_MIN = 45
HEIST_WINDOW_SECONDS = 60


class HeistJoinView(discord.ui.View):
    def __init__(self, heist_id: int):
        super().__init__(timeout=HEIST_WINDOW_SECONDS)
        self.heist_id = heist_id
        self.join.custom_id = f"heist:join:{heist_id}"

    @discord.ui.button(label="Join Heist", style=discord.ButtonStyle.blurple)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        heist = await db.get_heist(self.heist_id)
        if not heist or heist["status"] != "open":
            await interaction.response.send_message("This heist isn't open anymore.", ephemeral=True)
            return
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        if row["balance"] < heist["buy_in"]:
            await interaction.response.send_message("You can't afford the buy-in.", ephemeral=True)
            return
        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] - heist["buy_in"])
        await db.join_heist(self.heist_id, interaction.user.id)
        await interaction.response.send_message(f"You're in for **{CURRENCY}{heist['buy_in']:,}**.", ephemeral=True)


class EconomyBank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="deposit", description="Move pounds from wallet to bank (safe from /rob)")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        if amount <= 0 or amount > row["balance"]:
            await interaction.response.send_message("Invalid amount.", ephemeral=True)
            return
        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] - amount)
        await db.set_bank(interaction.guild_id, interaction.user.id, (row.get("bank", 0) or 0) + amount)
        await interaction.response.send_message(f"Deposited **{CURRENCY}{amount:,}** to your bank.")

    @app_commands.command(name="withdraw", description="Move pounds from bank back to wallet")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        bank = row.get("bank", 0) or 0
        if amount <= 0 or amount > bank:
            await interaction.response.send_message("Invalid amount.", ephemeral=True)
            return
        await db.set_bank(interaction.guild_id, interaction.user.id, bank - amount)
        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] + amount)
        await interaction.response.send_message(f"Withdrew **{CURRENCY}{amount:,}** to your wallet.")

    @app_commands.command(name="crime", description="Commit a crime for a bigger (riskier) payout than /work")
    async def crime(self, interaction: discord.Interaction):
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        now = datetime.datetime.utcnow()
        last_crime = row.get("last_crime")
        if last_crime:
            last = datetime.datetime.fromisoformat(last_crime)
            if now - last < datetime.timedelta(minutes=CRIME_COOLDOWN_MIN):
                remaining = datetime.timedelta(minutes=CRIME_COOLDOWN_MIN) - (now - last)
                await interaction.response.send_message(f"Lay low a bit longer. Try again in {remaining.seconds // 60}m.", ephemeral=True)
                return

        await db.set_last_crime(interaction.guild_id, interaction.user.id, now.isoformat())
        success = random.random() < 0.55
        if success:
            earned = random.randint(200, 800)
            await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] + earned)
            await interaction.response.send_message(f"🕶️ The job went smooth. You earned **{CURRENCY}{earned:,}**.")
        else:
            fine = random.randint(100, 400)
            fine = min(fine, row["balance"])
            await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] - fine)
            await interaction.response.send_message(f"🚔 You got caught and fined **{CURRENCY}{fine:,}**.")

    @app_commands.command(name="heist-start", description="Start a multiplayer heist — others buy in, then it resolves")
    async def heist_start(self, interaction: discord.Interaction, buy_in: int):
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        if buy_in <= 0 or buy_in > row["balance"]:
            await interaction.response.send_message("Invalid buy-in.", ephemeral=True)
            return

        starts_at = (datetime.datetime.utcnow() + datetime.timedelta(seconds=HEIST_WINDOW_SECONDS)).isoformat()
        heist_id = await db.create_heist(interaction.guild_id, interaction.channel_id, interaction.user.id, buy_in, starts_at)

        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] - buy_in)
        await db.join_heist(heist_id, interaction.user.id)

        embed = discord.Embed(
            title="💰 Heist Starting!",
            description=f"Buy-in: **{CURRENCY}{buy_in:,}**\nOrganized by {interaction.user.mention}\n"
                        f"Resolves in {HEIST_WINDOW_SECONDS}s — click below to join.",
            color=discord.Color.dark_gold(),
        )
        view = HeistJoinView(heist_id)
        self.bot.add_view(view)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        await db.set_heist_message(heist_id, msg.id)
        asyncio.create_task(self._resolve_single_heist(heist_id))

    async def _resolve_single_heist(self, heist_id: int):
        await asyncio.sleep(HEIST_WINDOW_SECONDS)
        heist = await db.get_heist(heist_id)
        if not heist or heist["status"] != "open":
            return
        participants = await db.get_heist_participants(heist_id)
        guild = self.bot.get_guild(heist["guild_id"])
        channel = guild.get_channel(heist["channel_id"]) if guild else None

        success = random.random() < 0.5
        await db.close_heist(heist_id, "success" if success else "busted")

        if not channel:
            return

        if success:
            payout_each = int(heist["buy_in"] * random.uniform(1.5, 3.0))
            for uid in participants:
                row = await db.get_balance_data(heist["guild_id"], uid)
                await db.update_balance(heist["guild_id"], uid, row["balance"] + payout_each)
            mentions = ", ".join(f"<@{u}>" for u in participants)
            await channel.send(f"💰 Heist succeeded! Each of {mentions} received **{CURRENCY}{payout_each:,}**.")
        else:
            await channel.send(f"🚨 The heist got busted! All {len(participants)} participant(s) lost their buy-in.")


async def setup(bot):
    await bot.add_cog(EconomyBank(bot))
