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
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ.get("MONGO_URL"), serverSelectionTimeoutMS=5000)

async def continue_to_play(userID):
    lastPlayedEntry = await client.rpsDatabase.rpsCollection.find_one({'Discord_ID': userID})
    if lastPlayedEntry is not None:
        if lastPlayedEntry['Times_Played'] == 10:
            continueToPlay = False
            return continueToPlay
        else:
            pass
    else:
        continueToPlay = True
        return continueToPlay

async def do_insert_rpsCollection(document, userID, playerChoice, botChoice, playResult, matchType, points):
    match matchType:
        case 'leaderboard':
            lastPlayedEntry = await client.rpsDatabase.rpsCollection.find_one({'Discord_ID': userID})

            if lastPlayedEntry is None:
                await client.rpsDatabase.rpsCollection.insert_one(document)

            finalPoint = lastPlayedEntry['Total_Points'] + points
            finalPlayed = lastPlayedEntry['Times_Played'] + 1
            timestamp=datetime.datetime.now(timezone)

            result = await client.rpsDatabase.rpsCollection.update_one({'Discord_ID': userID}, { '$set': {
                'Last_Player_Choice': playerChoice,
                'Last_Bot_Choice': botChoice,
                'Last_Result': playResult,
                'Last_Timestamp': timestamp,
                'Total_Points': finalPoint,
                'Times_Played': finalPlayed
            }})

        case 'battleroyale':
            lastPlayedEntry = await client.rpsDatabase.rpsCollection.find_one({'Discord_ID': userID})

            if lastPlayedEntry is None:
                await client.rpsDatabase.rpsCollection.insert_one(document)

            timestamp=datetime.datetime.now(timezone)

            result = await client.rpsDatabase.rpsCollection.update_one({'Discord_ID': userID}, { '$set': {
                'Last_Player_Choice': playerChoice,
                'Last_Bot_Choice': botChoice,
                'Last_Result': playResult,
                'Last_Timestamp': timestamp
            }})
            result = await client.rpsDatabase.rpsCollection.insert_one(document)
        case other:
            pass
    print('result %s' % repr(result.inserted_id))

async def generate_document(discordID, playerChoice, botChoice, result, timestamp):
    document = {
        'Discord_ID': discordID,
        'Last_Player_Choice': playerChoice,
        'Last_Bot_Choice': botChoice,
        'Last_Result': result,
        'Last_Timestamp': timestamp,
        'Total_Points': 0,
        'Times_Played': 0
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
    bot.add_view(RPSLS_leaderboard())
    bot.add_view(RPSLS_battleroyale())

class RPSLS_leaderboard(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select( 
        placeholder = "Rock, Paper, Scissors, Lizards or Spock?!", 
        min_values = 1, 
        max_values = 1, 
        custom_id = "RockPaperScissorGame_Leaderboard",
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
        if select.custom_id == "RockPaperScissorGame_Leaderboard":
            await interaction.response.send_message(f"You're now playing Leaderboard Mode", ephemeral=True)

        playerRPSDecision = select.values[0]
        botChoices = ['rock', 'paper', 'scissors', 'lizard', 'spock']

        channel = bot.get_channel(logChannel)

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

        if await continue_to_play(interaction.user.id) == False:
            await interaction.followup.send(f"You've played the maximum of 10 times. No more :(", ephemeral=True)
        else:
            await interaction.followup.send(f"You: {selectionEmoji[playerRPSDecision]} {playerRPSDecision}!\nBot: {selectionEmoji[botRPSDecision]} {botRPSDecision}!", ephemeral=True)
            if playerRPSDecision == botRPSDecision:
                await interaction.followup.send(f"" + gameMessage['tie'] + "\n You won 1 point!", ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Tie \n Timestamp: {datetime.datetime.now(timezone)}")
                document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Tie', timestamp=datetime.datetime.now(timezone))
                await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Tie', matchType='leaderboard', points=1)
            elif botRPSDecision in gameRules[playerRPSDecision]:
                action = gameRules[playerRPSDecision][botRPSDecision]
                await interaction.followup.send(f"{playerRPSDecision.title()} {action} {botRPSDecision}! " + gameMessage['win'] + "\n You won 2 points!", ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Win \n Timestamp: {datetime.datetime.now(timezone)}")
                document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Win', timestamp=datetime.datetime.now(timezone))
                await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Win', matchType='leaderboard', points=2)
            else:
                action = gameRules[botRPSDecision][playerRPSDecision]
                await interaction.followup.send(f"{botRPSDecision.title()} {action} {playerRPSDecision}! " + gameMessage['lose'] + "\n You lost 1 point!", ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Lose \n Timestamp: {datetime.datetime.now(timezone)}")
                document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Lose', timestamp=datetime.datetime.now(timezone))
                await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Lose', matchType='leaderboard', points=-1)

class RPSLS_battleroyale(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select( 
        placeholder = "Rock, Paper, Scissors, Lizards or Spock?!", 
        min_values = 1, 
        max_values = 1, 
        custom_id = "RockPaperScissorGame_BattleRoyale",
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
        if select.custom_id == "RockPaperScissorGame_BattleRoyale":
            await interaction.response.send_message(f"You're now playing Battle Royale Mode", ephemeral=True)
            
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
            await interaction.followup.send(f"Bruh you lost why you tryna cheat?", ephemeral=True)

        elif roles["roleRaffler"] in player.roles:
            await interaction.followup.send(f"I'm sorry but you're not eligible to join this.", ephemeral=True)

        elif roles["roleWin"] or roles["roleMember"] in player.roles:
            await interaction.followup.send(f"You: {selectionEmoji[playerRPSDecision]} {playerRPSDecision}!\nBot: {selectionEmoji[botRPSDecision]} {botRPSDecision}!", ephemeral=True)

            if playerRPSDecision == botRPSDecision:
                await interaction.followup.send(f"" + gameMessage['tie'], ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Tie \n Timestamp: {datetime.datetime.now(timezone)}")
                document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Tie', timestamp=datetime.datetime.now(timezone))
                await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Win', matchType='battleroyale', points=0)
            elif botRPSDecision in gameRules[playerRPSDecision]:
                action = gameRules[playerRPSDecision][botRPSDecision]
                await interaction.followup.send(f"{playerRPSDecision.title()} {action} {botRPSDecision}! " + gameMessage['win'], ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Win \n Timestamp: {datetime.datetime.now(timezone)}")
                document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Win', timestamp=datetime.datetime.now(timezone))
                await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Win', matchType='battleroyale', points=0)
                await player.remove_roles(roles['roleLose'])
                await player.add_roles(roles['roleWin'])
            else:
                action = gameRules[botRPSDecision][playerRPSDecision]
                await interaction.followup.send(f"{botRPSDecision.title()} {action} {playerRPSDecision}! " + gameMessage['lose'], ephemeral=True)
                await channel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Lose \n Timestamp: {datetime.datetime.now(timezone)}")
                document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Lose', timestamp=datetime.datetime.now(timezone))
                await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Win', matchType='battleroyale', points=0)
                await player.remove_roles(roles['roleWin'])
                await player.add_roles(roles['roleLose'])

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def rpsls_leaderboard(ctx):
    await ctx.send(f"Leaderboard Mode")
    await ctx.send(view=RPSLS_leaderboard())

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def rpsls_battleroyale(ctx):
    await ctx.send(f"Battle Royale Mode")
    await ctx.send(view=RPSLS_battleroyale())

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

@bot.command(pass_context=True)
async def rpsls_showScore(ctx):
    userID = ctx.author.id
    lastPlayedEntry = await client.rpsDatabase.rpsCollection.find_one({'Discord_ID': userID})

    if lastPlayedEntry:
        await ctx.send(f"<@{userID}>, you now have {lastPlayedEntry['Total_Points']} points.\n")
    else:
        await ctx.send(f"<@{userID}>, you have not played at all.\n")
    
@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def rpsls_showLeaderboard(ctx):
    userID = ctx.author.id
    top10Scorer = await client.rpsDatabase.rpsCollection.find().sort('Total_Points', -1).limit(10)
    
    for x in top10Scorer:
        await ctx.send(f"{x}")

bot.run(botToken)