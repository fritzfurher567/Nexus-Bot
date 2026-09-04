"""
economy.py
In-game currency (pounds) economy: balance, daily/work, shop, inventory,
rob, blackjack, bounties, pay, leaderboard.
"""
import random
import datetime

import discord
from discord import app_commands
from discord.ext import commands

import database as db

CURRENCY = "£"
DAILY_AMOUNT = 500
WORK_MIN, WORK_MAX = 50, 250
ROB_COOLDOWN_MIN = 30


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your (or someone's) balance")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        row = await db.get_balance_data(interaction.guild_id, member.id)
        embed = discord.Embed(
            title=f"{member.display_name}'s Wallet",
            description=f"**{CURRENCY}{row['balance']:,}**",
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily pounds")
    async def daily(self, interaction: discord.Interaction):
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        now = datetime.datetime.utcnow()
        if row["last_daily"]:
            last = datetime.datetime.fromisoformat(row["last_daily"])
            if now - last < datetime.timedelta(hours=24):
                remaining = datetime.timedelta(hours=24) - (now - last)
                await interaction.response.send_message(
                    f"Already claimed. Try again in {remaining.seconds // 3600}h {(remaining.seconds % 3600) // 60}m.",
                    ephemeral=True,
                )
                return
        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] + DAILY_AMOUNT)
        await db.set_last_daily(interaction.guild_id, interaction.user.id, now.isoformat())
        await interaction.response.send_message(f"You claimed your daily **{CURRENCY}{DAILY_AMOUNT}**!")

    @app_commands.command(name="work", description="Work for some pounds (1hr cooldown)")
    async def work(self, interaction: discord.Interaction):
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        now = datetime.datetime.utcnow()
        if row["last_work"]:
            last = datetime.datetime.fromisoformat(row["last_work"])
            if now - last < datetime.timedelta(hours=1):
                remaining = datetime.timedelta(hours=1) - (now - last)
                await interaction.response.send_message(f"You're tired. Try again in {remaining.seconds // 60}m.", ephemeral=True)
                return
        earned = random.randint(WORK_MIN, WORK_MAX)
        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] + earned)
        await db.set_last_work(interaction.guild_id, interaction.user.id, now.isoformat())
        await interaction.response.send_message(f"You worked a shift and earned **{CURRENCY}{earned}**!")

    @app_commands.command(name="pay", description="Give pounds to another member")
    async def pay(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if member.id == interaction.user.id:
            await interaction.response.send_message("You can't pay yourself.", ephemeral=True)
            return
        sender = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        if amount <= 0 or amount > sender["balance"]:
            await interaction.response.send_message("Invalid amount.", ephemeral=True)
            return
        receiver = await db.get_balance_data(interaction.guild_id, member.id)
        await db.update_balance(interaction.guild_id, interaction.user.id, sender["balance"] - amount)
        await db.update_balance(interaction.guild_id, member.id, receiver["balance"] + amount)
        await interaction.response.send_message(f"Sent **{CURRENCY}{amount:,}** to {member.mention}.")

    @app_commands.command(name="pounds-leaderboard", description="Top balances in this server")
    async def leaderboard(self, interaction: discord.Interaction):
        rows = await db.get_economy_leaderboard(interaction.guild_id)
        lines = []
        for i, r in enumerate(rows, 1):
            member = interaction.guild.get_member(r["user_id"])
            name = member.display_name if member else f"User {r['user_id']}"
            lines.append(f"**{i}.** {name} — {CURRENCY}{r['balance']:,}")
        embed = discord.Embed(title="💰 Leaderboard", description="\n".join(lines) or "No data yet.", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    # ---- Shop / inventory ----

    @app_commands.command(name="shop-add", description="[Admin] Add an item to the shop")
    @app_commands.checks.has_permissions(administrator=True)
    async def shop_add(self, interaction: discord.Interaction, item_name: str, price: int, role: discord.Role = None):
        await db.add_shop_item(interaction.guild_id, item_name, price, role.id if role else None)
        await interaction.response.send_message(f"Added **{item_name}** to the shop for {CURRENCY}{price:,}.", ephemeral=True)

    @app_commands.command(name="shop", description="View the shop")
    async def shop(self, interaction: discord.Interaction):
        items = await db.get_shop_items(interaction.guild_id)
        if not items:
            await interaction.response.send_message("The shop is empty.", ephemeral=True)
            return
        embed = discord.Embed(title="🛒 Shop", color=discord.Color.blurple())
        for item in items:
            embed.add_field(name=item["item_name"], value=f"{CURRENCY}{item['price']:,}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Buy an item from the shop")
    async def buy(self, interaction: discord.Interaction, item_name: str):
        item = await db.get_shop_item(interaction.guild_id, item_name)
        if not item:
            await interaction.response.send_message("That item doesn't exist.", ephemeral=True)
            return
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        if row["balance"] < item["price"]:
            await interaction.response.send_message("You can't afford that.", ephemeral=True)
            return
        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] - item["price"])
        await db.add_inventory_item(interaction.guild_id, interaction.user.id, item["item_name"], 1)
        if item["role_id"]:
            role = interaction.guild.get_role(item["role_id"])
            if role:
                await interaction.user.add_roles(role, reason="Purchased from shop")
        await interaction.response.send_message(f"Bought **{item['item_name']}** for {CURRENCY}{item['price']:,}!")

    @app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        items = await db.get_inventory(interaction.guild_id, member.id)
        if not items:
            await interaction.response.send_message(f"{member.display_name}'s inventory is empty.", ephemeral=True)
            return
        embed = discord.Embed(title=f"🎒 {member.display_name}'s Inventory", color=discord.Color.blurple())
        for it in items:
            embed.add_field(name=it["item_name"], value=f"x{it['quantity']}", inline=True)
        await interaction.response.send_message(embed=embed)

    # ---- Rob ----

    @app_commands.command(name="rob", description="Attempt to rob another member's wallet")
    async def rob(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            await interaction.response.send_message("You can't rob yourself.", ephemeral=True)
            return
        target = await db.get_balance_data(interaction.guild_id, member.id)
        if target["balance"] < 100:
            await interaction.response.send_message(f"{member.display_name} is too broke to rob.", ephemeral=True)
            return

        robber = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        success = random.random() < 0.4  # 40% success rate
        if success:
            stolen = random.randint(1, min(target["balance"], 500))
            await db.update_balance(interaction.guild_id, member.id, target["balance"] - stolen)
            await db.update_balance(interaction.guild_id, interaction.user.id, robber["balance"] + stolen)
            await interaction.response.send_message(
                f"💰 You robbed **{CURRENCY}{stolen:,}** from {member.mention}!"
            )
        else:
            fine = random.randint(50, 200)
            fine = min(fine, robber["balance"])
            await db.update_balance(interaction.guild_id, interaction.user.id, robber["balance"] - fine)
            await interaction.response.send_message(
                f"🚨 You got caught trying to rob {member.mention} and paid a **{CURRENCY}{fine:,}** fine."
            )

    # ---- Blackjack (single-hand, vs dealer, no splitting) ----

    @app_commands.command(name="blackjack", description="Play a hand of blackjack against the bot")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        if bet <= 0 or bet > row["balance"]:
            await interaction.response.send_message("Invalid bet.", ephemeral=True)
            return

        def draw():
            return random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11])

        def hand_value(cards):
            total = sum(cards)
            aces = cards.count(11)
            while total > 21 and aces:
                total -= 10
                aces -= 1
            return total

        player = [draw(), draw()]
        dealer = [draw(), draw()]

        while hand_value(dealer) < 17:
            dealer.append(draw())
        while hand_value(player) < 17:
            player.append(draw())

        p_val, d_val = hand_value(player), hand_value(dealer)

        if p_val > 21:
            result, delta = "Bust! You lose.", -bet
        elif d_val > 21 or p_val > d_val:
            result, delta = "You win!", bet
        elif p_val == d_val:
            result, delta = "Push — bet returned.", 0
        else:
            result, delta = "Dealer wins.", -bet

        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] + delta)

        embed = discord.Embed(title="🃏 Blackjack", color=discord.Color.green() if delta > 0 else discord.Color.red())
        embed.add_field(name="Your hand", value=f"{player} = {p_val}", inline=False)
        embed.add_field(name="Dealer hand", value=f"{dealer} = {d_val}", inline=False)
        embed.add_field(name="Result", value=f"{result} ({CURRENCY}{delta:+,})", inline=False)
        await interaction.response.send_message(embed=embed)

    # ---- Bounties ----

    @app_commands.command(name="bounty-place", description="Place a pound bounty on a member")
    async def bounty_place(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        row = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        if amount <= 0 or amount > row["balance"]:
            await interaction.response.send_message("Invalid amount.", ephemeral=True)
            return
        await db.update_balance(interaction.guild_id, interaction.user.id, row["balance"] - amount)
        await db.add_bounty(interaction.guild_id, member.id, amount, interaction.user.id, datetime.datetime.utcnow().isoformat())
        await interaction.response.send_message(f"🎯 Bounty of **{CURRENCY}{amount:,}** placed on {member.mention}!")

    @app_commands.command(name="bounties", description="View open bounties")
    async def bounties(self, interaction: discord.Interaction):
        rows = await db.get_open_bounties(interaction.guild_id)
        if not rows:
            await interaction.response.send_message("No open bounties.", ephemeral=True)
            return
        embed = discord.Embed(title="🎯 Open Bounties", color=discord.Color.dark_red())
        for r in rows:
            target = interaction.guild.get_member(r["target_id"])
            name = target.display_name if target else f"User {r['target_id']}"
            embed.add_field(name=f"#{r['id']} — {name}", value=f"{CURRENCY}{r['amount']:,}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bounty-claim", description="Claim a bounty (won via a game against the target, honor system)")
    async def bounty_claim(self, interaction: discord.Interaction, bounty_id: int):
        rows = await db.get_open_bounties(interaction.guild_id)
        match = next((r for r in rows if r["id"] == bounty_id), None)
        if not match:
            await interaction.response.send_message("Bounty not found or already claimed.", ephemeral=True)
            return
        claimed = await db.claim_bounty(bounty_id, interaction.user.id)
        if not claimed:
            await interaction.response.send_message("Bounty not found or already claimed.", ephemeral=True)
            return
        payer = await db.get_balance_data(interaction.guild_id, interaction.user.id)
        await db.update_balance(interaction.guild_id, interaction.user.id, payer["balance"] + match["amount"])
        await interaction.response.send_message(f"🎯 Bounty #{bounty_id} claimed! You received **{CURRENCY}{match['amount']:,}**.")


async def setup(bot):
    await bot.add_cog(Economy(bot))
