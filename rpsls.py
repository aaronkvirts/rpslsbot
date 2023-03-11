import discord
from discord.ext import tasks, commands
from discord.utils import get
import random
import logging
import datetime
import pytz

logging.basicConfig(level=logging.INFO)
timezone = pytz.timezone('Asia/Singapore')

token = open("token", "r").read() 

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    bot.add_view(RockPaperScissor())

class RockPaperScissor(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select( 
        placeholder = "Rock, Paper, Scissors, Lizards or Spock?!", 
        min_values = 1, 
        max_values = 1, 
        custom_id = "RockPaperScissorGame1",
        options = [
            discord.SelectOption(
                label="Rock",
                emoji="✊",
                value="rock",
            ),
            discord.SelectOption(
                label="Paper",
                emoji="🖐️",
                value="paper",
            ),
            discord.SelectOption(
                label="Scissors",
                emoji="✌️",
                value="scissors",
            ),
            discord.SelectOption(
                label="Lizard",
                emoji="🤌",
                value="lizard",
            ),
            discord.SelectOption(
                label="Spock",
                emoji="🖖",
                value="spock",
            )
        ]
    )

    async def select_callback(self, select, interaction):
        playerRPSDecision = select.values[0]
        player = interaction.user
        botChoices = ['rock', 'paper', 'scissors', 'lizard', 'spock']

        channel = bot.get_channel(1083002469593911327)

        roles = {
            'roleWin': interaction.guild.get_role(1083054156123738232),
            'roleLose': interaction.guild.get_role(1083054190512832552),
            'roleRaffler': interaction.guild.get_role(1083068650568814664), 
            'roleMember': interaction.guild.get_role(1083068673704599602)
        }

        gameRules = {
            'rock': {
                'scissors': 'smashes',
                'lizard': 'crushes'
            },
            'paper': {
                'rock': 'covers',
                'spock': 'disproves'
            },
            'scissors': {
                'paper': 'cuts',
                'lizard': 'decapitates'
            },
            'lizard': {
                'paper': 'eats',
                'spock': 'poisons'
            },
            'spock': {
                'rock': 'vaporizes',
                'scissors': 'smashes'
            }
        }

        gameMessage = {
            'win': 'You win!',
            'lose': 'You lose :(',
            'tie': "It's a tie!"
        }

        selectionEmoji = {
            'rock': '✊',
            'paper': '🖐️',
            'scissor': '✌️',
            'lizard': '🤌',
            'spock': '🖖'
        }

        IHopeThisIsRNGEnough = random.SystemRandom()
        botRPSDecision = botChoices[IHopeThisIsRNGEnough.randint(0, 4)]

        if roles["roleLose"] in player.roles:
            await interaction.response.send_message(f"Bruh you lost why you tryna cheat?", ephemeral=True)

        elif roles["roleRaffler"] in player.roles:
            await interaction.response.send_message(f"I'm sorry but you're not eligible to join this.", ephemeral=True)

        elif roles["roleWin"] or roles["roleMember"] in player.roles:
            await interaction.response.send_message(f"You: {selectionEmoji[playerRPSDecision]} {playerRPSDecision}!\nBot: {selectionEmoji[botRPSDecision]} {botRPSDecision}!", ephemeral=True)

            if playerRPSDecision == botRPSDecision:
                await interaction.followup.send(f"" + gameMessage['tie'], ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Tie \n Timestamp: {datetime.datetime.now(timezone)}")
            elif botRPSDecision in gameRules[playerRPSDecision]:
                action = gameRules[playerRPSDecision][botRPSDecision]
                await interaction.followup.send(f"{playerRPSDecision.title()} {action} {botRPSDecision}! " + gameMessage['win'], ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Win \n Timestamp: {datetime.datetime.now(timezone)}")
                await player.remove_roles(roles['roleLose'])
                await player.add_roles(roles['roleWin'])  
            else:
                action = gameRules[botRPSDecision][playerRPSDecision]
                await interaction.followup.send(f"{botRPSDecision.title()} {action} {playerRPSDecision}! " + gameMessage['lose'], ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Lose \n Timestamp: {datetime.datetime.now(timezone)}")
                await player.remove_roles(roles['roleWin'])
                await player.add_roles(roles['roleLose'])  

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def rps(ctx):
    await ctx.send(view=RockPaperScissor())

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def clear(ctx, amount = 5):
    await ctx.channel.purge(limit=amount)

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def RPSWinnerReset(ctx):
    roleWin = ctx.guild.get_role(1083054156123738232)
    if roleWin.members:
        for member in roleWin.members:
            await ctx.send(f"Removing <@{member.id}> from RPSWinner role...\n")
            await member.remove_roles(roleWin)
    else:
        await ctx.send(f"No one else has the winner role")

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def RPSResetAll(ctx):
    roleWin = ctx.guild.get_role(1083054156123738232)
    if roleWin.members:
        for member in roleWin.members:
            await ctx.send(f"Removing <@{member.id}> from RPSWinner role...\n")
            await member.remove_roles(roleWin)
    else:
        await ctx.send(f"No one else has the winner role")

    roleLose = ctx.guild.get_role(1083054190512832552)
    if roleLose.members:
        for member in roleLose.members:
            await ctx.send(f"Removing <@{member.id}> from RPSLoser role...\n")
            await member.remove_roles(roleLose)
    else:
        await ctx.send(f"No one else has the winner role")

bot.run(token)