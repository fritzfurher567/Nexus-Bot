"""
polls_multi.py
Multiple-choice poll (up to 5 options) using numbered emoji reactions —
distinct from any simple yes/no poll elsewhere.
"""
import discord
from discord import app_commands
from discord.ext import commands

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]


class PollsMulti(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll-multi", description="Create a multiple-choice poll (up to 5 options)")
    async def poll_multi(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None, option5: str = None):
        options = [o for o in [option1, option2, option3, option4, option5] if o]
        embed = discord.Embed(title=f"📊 {question}", color=discord.Color.blue())
        for i, opt in enumerate(options):
            embed.add_field(name=NUMBER_EMOJIS[i], value=opt, inline=False)
        embed.set_footer(text=f"Poll by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        for i in range(len(options)):
            await msg.add_reaction(NUMBER_EMOJIS[i])


async def setup(bot):
    await bot.add_cog(PollsMulti(bot))
