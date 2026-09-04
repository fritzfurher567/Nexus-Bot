"""
lottery.py
Server-wide lottery: members buy tickets with pounds, an admin draws a
winner who takes the whole pot.
"""
import random
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db

CURRENCY = "£"
TICKET_PRICE = 100


class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lottery-buy", description=f"Buy a lottery ticket ({CURRENCY}{TICKET_PRICE} each)")
    async def lottery_buy(self, interaction: discord.Interaction):
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        if row["balance"] < TICKET_PRICE:
            await interaction.response.send_message(f"You need {CURRENCY}{TICKET_PRICE} for a ticket.", ephemeral=True)
            return
        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] - TICKET_PRICE)
        await db.buy_lottery_ticket(interaction.guild_id, interaction.user.id, datetime.datetime.utcnow().isoformat())
        tickets = await db.get_lottery_tickets(interaction.guild_id)
        await interaction.response.send_message(f"🎟️ Ticket bought! Pot is now **{CURRENCY}{len(tickets) * TICKET_PRICE:,}**.")

    @app_commands.command(name="lottery-draw", description="[Admin] Draw the lottery winner and reset the pot")
    @app_commands.checks.has_permissions(administrator=True)
    async def lottery_draw(self, interaction: discord.Interaction):
        tickets = await db.get_lottery_tickets(interaction.guild_id)
        if not tickets:
            await interaction.response.send_message("No tickets have been sold yet.", ephemeral=True)
            return
        winner_id = random.choice(tickets)
        pot = len(tickets) * TICKET_PRICE
        row = await db.get_balance_data(interaction.guild_id, winner_id)
        await db.update_balance(interaction.guild_id, winner_id, row["balance"] + pot)
        await db.clear_lottery_tickets(interaction.guild_id)
        await interaction.response.send_message(f"🎉 <@{winner_id}> won the lottery and takes home **{CURRENCY}{pot:,}**!")


async def setup(bot):
    await bot.add_cog(Lottery(bot))
