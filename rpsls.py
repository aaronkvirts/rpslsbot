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
        if lastPlayedEntry['Times_Played'] == int(os.environ.get("maxPlays")):
            continueToPlay = False
            return continueToPlay
        else:
            pass
    else:
        continueToPlay = True
        return continueToPlay

async def do_insert_rpsCollection(document, userID, playerChoice, botChoice, playResult, matchType, points):
    entry = await client.rpsDatabase.rpsCollection.find_one({'Discord_ID': userID})
    match matchType:
        case 'leaderboard':
            if entry is None:
                await client.rpsDatabase.rpsCollection.insert_one(document)

            lastPlayedEntry = await client.rpsDatabase.rpsCollection.find_one({'Discord_ID': userID})
            finalPoint = lastPlayedEntry['Total_Points'] + points
            finalPlayed = lastPlayedEntry['Times_Played'] + 1
            timestamp = datetime.datetime.now(timezone)

            await client.rpsDatabase.rpsCollection.update_one({'Discord_ID': userID}, { '$set': {
                'Last_Player_Choice': playerChoice,
                'Last_Bot_Choice': botChoice,
                'Last_Result': playResult,
                'Last_Timestamp': timestamp,
                'Total_Points': finalPoint,
                'Times_Played': finalPlayed
            }})

        case 'battleroyale':

            if entry is None:
                await client.rpsDatabase.rpsCollection.insert_one(document)

            timestamp = datetime.datetime.now(timezone)

            result = await client.rpsDatabase.rpsCollection.update_one({'Discord_ID': userID}, { '$set': {
                'Last_Player_Choice': playerChoice,
                'Last_Bot_Choice': botChoice,
                'Last_Result': playResult,
                'Last_Timestamp': timestamp
            }})
        case other:
            pass

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
dc_logChannel = int(os.environ.get("logChannel"))
RPSWinner = int(os.environ.get("RPSWinner"))
RPSLoser = int(os.environ.get("RPSLoser"))
Member = int(os.environ.get("Member"))
CharityRaffle = int(os.environ.get("CharityRaffle"))
leaderboardChannel = int(os.environ.get("leaderboardChannel"))

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!!', intents=intents)

async def leaderboard_engine(interaction, playerRPSDecision):
    logChannel = bot.get_channel(dc_logChannel)

    botChoices = ['rock', 'paper', 'scissors', 'lizard', 'spock']

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
        await interaction.response.send_message(f"You've played the maximum of 10 times. No more :(", ephemeral=True)
    else:
        if playerRPSDecision == botRPSDecision:
            await interaction.response.send_message(f"Selection recorded", ephemeral=True, timeout=3.0)
            await logChannel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Tie \n Timestamp: {datetime.datetime.now(timezone)} \n Points Won: 1 \n")
            document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Tie', timestamp=datetime.datetime.now(timezone))
            await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Tie', matchType='leaderboard', points=1)
        elif botRPSDecision in gameRules[playerRPSDecision]:
            await interaction.response.send_message(f"Selection recorded", ephemeral=True, timeout=3.0)
            await logChannel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Win \n Timestamp: {datetime.datetime.now(timezone)} \n Points Won: 2 \n")
            document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Win', timestamp=datetime.datetime.now(timezone))
            await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Win', matchType='leaderboard', points=2)
        else:
            await interaction.response.send_message(f"Selection recorded", ephemeral=True, timeout=3.0)
            await logChannel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Lose \n Timestamp: {datetime.datetime.now(timezone)} \n Points Lost: 1 \n")
            document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Lose', timestamp=datetime.datetime.now(timezone))
            await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Lose', matchType='leaderboard', points=-1)

async def battleroyale_engine(interaction, playerRPSDecision):
    logChannel = bot.get_channel(dc_logChannel)

    player = interaction.user
    botChoices = ['rock', 'paper', 'scissors', 'lizard', 'spock']

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

        if playerRPSDecision == botRPSDecision:
            await interaction.response.send_message(f"Selection recorded", ephemeral=True, timeout=3.0)
            await logChannel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Tie \n Timestamp: {datetime.datetime.now(timezone)} \n")
            document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Tie', timestamp=datetime.datetime.now(timezone))
            await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Win', matchType='battleroyale', points=0)
        elif botRPSDecision in gameRules[playerRPSDecision]:
            await interaction.response.send_message(f"Selection recorded", ephemeral=True, timeout=3.0)
            await logChannel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Win \n Timestamp: {datetime.datetime.now(timezone)} \n")
            document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Win', timestamp=datetime.datetime.now(timezone))
            await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Win', matchType='battleroyale', points=0)
            await player.remove_roles(roles['roleLose'])
            await player.add_roles(roles['roleWin'])
        else:
            await interaction.response.send_message(f"Selection recorded", ephemeral=True, timeout=3.0)
            await logChannel.send(f"<@{interaction.user.id}> \n Played: {playerRPSDecision} \n Bot: {botRPSDecision} \n Result: Lose \n Timestamp: {datetime.datetime.now(timezone)} \n")
            document = await generate_document(interaction.user.id, playerRPSDecision, botRPSDecision, result='Lose', timestamp=datetime.datetime.now(timezone))
            await do_insert_rpsCollection(document, interaction.user.id, playerRPSDecision, botRPSDecision, playResult='Win', matchType='battleroyale', points=0)
            await player.remove_roles(roles['roleWin'])
            await player.add_roles(roles['roleLose'])

@bot.event
async def on_ready():
    bot.add_view(RPSLS_leaderboard())
    bot.add_view(RPSLS_battleroyale())

class RPSLS_leaderboard(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Rock", custom_id='button_leaderboard_rock', style=discord.ButtonStyle.primary, emoji="✊")
    async def first_button_callback(self, button, interaction):
        await leaderboard_engine(interaction, playerRPSDecision='rock')
    @discord.ui.button(label="Paper", custom_id='button_leaderboard_paper', style=discord.ButtonStyle.primary, emoji="🖐️")
    async def second_button_callback(self, button, interaction):
        await leaderboard_engine(interaction, playerRPSDecision='paper')
    @discord.ui.button(label="Scissors", custom_id='button_leaderboard_scissors', style=discord.ButtonStyle.primary, emoji="✌️")
    async def third_button_callback(self, button, interaction):
        await leaderboard_engine(interaction, playerRPSDecision='scissors')
    @discord.ui.button(label="Lizard", custom_id='button_leaderboard_lizards', style=discord.ButtonStyle.primary, emoji="🤌")
    async def fourth_button_callback(self, button, interaction):
        await leaderboard_engine(interaction, playerRPSDecision='lizard')
    @discord.ui.button(label="Spock", custom_id='button_leaderboard_spock', style=discord.ButtonStyle.primary, emoji="🖖")
    async def fifth_button_callback(self, button, interaction):
        await leaderboard_engine(interaction, playerRPSDecision='spock')

class RPSLS_battleroyale(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Rock", custom_id='button_battleroyale_rock', style=discord.ButtonStyle.primary, emoji="✊")
    async def first_button_callback(self, button, interaction):
        await battleroyale_engine(interaction, playerRPSDecision='rock')
    @discord.ui.button(label="Paper", custom_id='button_battleroyale_paper', style=discord.ButtonStyle.primary, emoji="🖐️")
    async def second_button_callback(self, button, interaction):
        await battleroyale_engine(interaction, playerRPSDecision='paper')
    @discord.ui.button(label="Scissors", custom_id='button_battleroyale_scissors', style=discord.ButtonStyle.primary, emoji="✌️")
    async def third_button_callback(self, button, interaction):
        await battleroyale_engine(interaction, playerRPSDecision='scissors')
    @discord.ui.button(label="Lizard", custom_id='button_battleroyale_lizard', style=discord.ButtonStyle.primary, emoji="🤌")
    async def fourth_button_callback(self, button, interaction):
        await battleroyale_engine(interaction, playerRPSDecision='lizard')
    @discord.ui.button(label="Spock", custom_id='button_battleroyale_spock', style=discord.ButtonStyle.primary, emoji="🖖")
    async def fifth_button_callback(self, button, interaction):
        await battleroyale_engine(interaction, playerRPSDecision='spock')

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
    leaderboardMessage = await bot.get_channel(leaderboardChannel).send(f"‎ ")
    bot.loop.create_task(rpsls_showLeaderboardLoop(leaderboardMessage))
    
async def rpsls_showLeaderboardLoop(leaderboardMessage):
    while True:
        channel = bot.get_channel(leaderboardChannel)
        position = 0
        embedPosition = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Nineth', 'Tenth']
        top10Scorer = client.rpsDatabase.rpsCollection.find().sort('Total_Points', -1).limit(10)

        leaderboardEmbed = discord.Embed(
            title = "RPSLS Leaderboards",
            description = "A top 10 leaderboard for RPSLS league, refreshed every 30 minutes",
            color = discord.Color.greyple()
        )

        if top10Scorer is None:
            leaderboardEmbed.add_field(name=f"**Leaderboard**", value=f"> Still empty now...", inline=False)
            message = await channel.fetch_message(leaderboardMessage.id)
            await message.edit(embed=leaderboardEmbed)
            print(f"Scoreboard updated: {datetime.datetime.now(timezone)}")
        else:
            async for entries in top10Scorer:
                leaderboardEmbed.add_field(name=f"**{embedPosition[position]}**", 
                                        value=f"> Username <@{entries['Discord_ID']}> \n > Total Points {entries['Total_Points']} \n > Times Played {entries['Times_Played']} \n ", 
                                        inline=False)
                position += 1
            message = await channel.fetch_message(leaderboardMessage.id)
            await message.edit(embed=leaderboardEmbed)
            print(f"Scoreboard updated: {datetime.datetime.now(timezone)}")
        await asyncio.sleep(int(os.environ.get("leaderboardRefreshSeconds")))

bot.run(botToken)
