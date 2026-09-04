"""
fun2.py
Lightweight fun commands: 8ball, rock-paper-scissors, trivia, would-you-
rather, number guessing game, jokes/facts, and a compatibility "ship"
command. All self-contained, no external APIs.
"""
import random

import discord
from discord import app_commands
from discord.ext import commands

EIGHT_BALL = ["Yes.", "No.", "Ask again later.", "Absolutely.", "Doubtful.", "It is decided.", "Signs point to yes.", "Signs point to no."]
JOKES = [
    "Why don't skeletons fight each other? They don't have the guts.",
    "I told my computer I needed a break, and it said no problem — it'll go to sleep too.",
    "Why did the scarecrow get an award? He was outstanding in his field.",
]
FACTS = [
    "Honey never spoils — archaeologists have found 3000-year-old honey that's still edible.",
    "Octopuses have three hearts.",
    "A group of flamingos is called a 'flamboyance'.",
]
WYR_PROMPTS = [
    ("have the ability to fly", "have the ability to turn invisible"),
    ("always be 10 minutes late", "always be 20 minutes early"),
    ("fight one horse-sized duck", "fight 100 duck-sized horses"),
]


class Fun2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._guess_sessions: dict[int, int] = {}  # user_id -> secret number

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        embed = discord.Embed(title="🎱 8-Ball", color=discord.Color.purple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=random.choice(EIGHT_BALL), inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rps", description="Play rock-paper-scissors against the bot")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock", value="rock"),
        app_commands.Choice(name="Paper", value="paper"),
        app_commands.Choice(name="Scissors", value="scissors"),
    ])
    async def rps(self, interaction: discord.Interaction, choice: app_commands.Choice[str]):
        bot_choice = random.choice(["rock", "paper", "scissors"])
        player = choice.value
        beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        if player == bot_choice:
            result = "It's a tie!"
        elif beats[player] == bot_choice:
            result = "You win!"
        else:
            result = "I win!"
        await interaction.response.send_message(f"You chose **{player}**, I chose **{bot_choice}**. {result}")

    @app_commands.command(name="trivia", description="Answer a quick true/false trivia question")
    async def trivia(self, interaction: discord.Interaction):
        questions = [
            ("The Great Wall of China is visible from space with the naked eye.", False),
            ("Bananas are berries, but strawberries aren't.", True),
            ("A day on Venus is longer than a year on Venus.", True),
        ]
        q, answer = random.choice(questions)
        view = discord.ui.View(timeout=30)
        for label, value in [("True", True), ("False", False)]:
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.blurple)

            async def cb(i: discord.Interaction, value=value):
                correct = value == answer
                await i.response.send_message("✅ Correct!" if correct else f"❌ Wrong — the answer was **{answer}**.", ephemeral=True)

            btn.callback = cb
            view.add_item(btn)
        await interaction.response.send_message(q, view=view)

    @app_commands.command(name="wouldyourather", description="Get a would-you-rather prompt")
    async def wouldyourather(self, interaction: discord.Interaction):
        a, b = random.choice(WYR_PROMPTS)
        await interaction.response.send_message(f"Would you rather **{a}** or **{b}**?")

    @app_commands.command(name="guess-start", description="Start a number guessing game (1-100)")
    async def guess_start(self, interaction: discord.Interaction):
        self._guess_sessions[interaction.user.id] = random.randint(1, 100)
        await interaction.response.send_message("I'm thinking of a number 1-100. Use `/guess-try` to guess!", ephemeral=True)

    @app_commands.command(name="guess-try", description="Guess the number from /guess-start")
    async def guess_try(self, interaction: discord.Interaction, number: int):
        secret = self._guess_sessions.get(interaction.user.id)
        if secret is None:
            await interaction.response.send_message("Start a game first with `/guess-start`.", ephemeral=True)
            return
        if number == secret:
            del self._guess_sessions[interaction.user.id]
            await interaction.response.send_message(f"🎉 Correct! It was **{secret}**.")
        elif number < secret:
            await interaction.response.send_message("Higher!", ephemeral=True)
        else:
            await interaction.response.send_message("Lower!", ephemeral=True)

    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        await interaction.response.send_message(random.choice(JOKES))

    @app_commands.command(name="fact", description="Get a random fact")
    async def fact(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"💡 {random.choice(FACTS)}")

    @app_commands.command(name="ship", description="Calculate compatibility between two members")
    async def ship(self, interaction: discord.Interaction, member1: discord.Member, member2: discord.Member):
        seed = (member1.id + member2.id) % 101
        embed = discord.Embed(title="💘 Ship Calculator", description=f"{member1.mention} + {member2.mention} = **{seed}%**", color=discord.Color.pink())
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun2(bot))
