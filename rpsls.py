import discord
from discord.ext import tasks, commands
from discord.utils import get
import random
import logging
import datetime
import pytz
import os
import asyncio
import motor.motor_asyncio

logging.basicConfig(level=logging.INFO)
timezone = pytz.timezone('Asia/Singapore')

async def get_server_info():
    conn_str = "mongodb://mongo:cLpDSAhrE8vJDJrPeZL3@containers-us-west-153.railway.app:5519"
    # set a 5-second connection timeout
    client = motor.motor_asyncio.AsyncIOMotorClient(conn_str, serverSelectionTimeoutMS=5000)
    try:
        print(await client.server_info())
    except Exception:
        print("Unable to connect to the server.")
    return client

async def do_insert_testCollection(document):
    loop = asyncio.get_event_loop()
    client = loop.run_until_complete(get_server_info())
    result = await client.rpsDatabase_log.testCollection.insert_one(document)
    print('result %s' % repr(result.inserted_id))

async def generate_document(discordID, playerChoice, botChoice, result, timestamp):
    document = {
        'Discord ID': discordID,
        'Player Choice': playerChoice,
        'Bot Choice': botChoice,
        'Result': result,
        'Timestamp': timestamp
    }
    return document

botToken = os.environ.get("botToken")
logChannel = int(os.environ.get("logChannel"))
RPSWinner = int(os.environ.get("RPSWinner"))
RPSLoser = int(os.environ.get("RPSLoser"))
Member = int(os.environ.get("Member"))
CharityRaffle = int(os.environ.get("CharityRaffle"))

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!!', intents=intents)

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

        channel = bot.get_channel(logChannel)

        roles = {
            'roleWin': interaction.guild.get_role(RPSWinner),
            'roleLose': interaction.guild.get_role(RPSLoser),
            'roleRaffler': interaction.guild.get_role(CharityRaffle), 
            'roleMember': interaction.guild.get_role(Member)
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
            'scissors': '✌️',
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
                document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Tie', timestamp=datetime.datetime.now(timezone))
                await do_insert_testCollection(document)
            elif botRPSDecision in gameRules[playerRPSDecision]:
                action = gameRules[playerRPSDecision][botRPSDecision]
                await interaction.followup.send(f"{playerRPSDecision.title()} {action} {botRPSDecision}! " + gameMessage['win'], ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Win \n Timestamp: {datetime.datetime.now(timezone)}")
                document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Win', timestamp=datetime.datetime.now(timezone))
                await do_insert_testCollection(document)
                await player.remove_roles(roles['roleLose'])
                await player.add_roles(roles['roleWin'])
            else:
                action = gameRules[botRPSDecision][playerRPSDecision]
                await interaction.followup.send(f"{botRPSDecision.title()} {action} {playerRPSDecision}! " + gameMessage['lose'], ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Lose \n Timestamp: {datetime.datetime.now(timezone)}")
                document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Lose', timestamp=datetime.datetime.now(timezone))
                await do_insert_testCollection(document)
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
    roleWin = ctx.guild.get_role(RPSWinner)
    if roleWin.members:
        for member in roleWin.members:
            await ctx.send(f"Removing <@{member.id}> from RPSWinner role...\n")
            await member.remove_roles(roleWin)
    else:
        await ctx.send(f"No one else has the winner role")

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def RPSResetAll(ctx):
    roleWin = ctx.guild.get_role(RPSWinner)
    if roleWin.members:
        for member in roleWin.members:
            await ctx.send(f"Removing <@{member.id}> from RPSWinner role...\n")
            await member.remove_roles(roleWin)
    else:
        await ctx.send(f"No one else has the winner role")

    roleLose = ctx.guild.get_role(RPSLoser)
    if roleLose.members:
        for member in roleLose.members:
            await ctx.send(f"Removing <@{member.id}> from RPSLoser role...\n")
            await member.remove_roles(roleLose)
    else:
        await ctx.send(f"No one else has the loser role")

bot.run(botToken)