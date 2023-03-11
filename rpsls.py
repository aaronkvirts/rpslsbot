import discord
from discord.ext import tasks, commands
from discord.utils import get
import random
import logging

logging.basicConfig(level=logging.INFO)

token = open("token", "r").read() 

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

botChoices = ['✊ Rock', '🖐️ Paper', '✌️ Scissors', '🤌 Lizard', '🖖 Spock']

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
                value="✊ Rock",
            ),
            discord.SelectOption(
                label="Paper",
                emoji="🖐️",
                value="🖐️ Paper",
            ),
            discord.SelectOption(
                label="Scissors",
                emoji="✌️",
                value="✌️ Scissors",
            ),
            discord.SelectOption(
                label="Lizard",
                emoji="🤌",
                value="🤌 Lizard",
            ),
            discord.SelectOption(
                label="Spock",
                emoji="🖖",
                value="🖖 Spock",
            )
        ]
    )

    async def select_callback(self, select, interaction):
        playerRPSDecision = select.values[0]
        player = interaction.user
        roleWin = interaction.guild.get_role(1083054156123738232)
        roleLose = interaction.guild.get_role(1083054190512832552)
        roleRaffler = interaction.guild.get_role(1083068650568814664)
        roleMember = interaction.guild.get_role(1083068673704599602)
        IHopeThisIsRNGEnough = random.SystemRandom()
        botRPSDecision = botChoices[IHopeThisIsRNGEnough.randint(0, 4)]

        if roleLose in player.roles:
            await interaction.response.send_message(f"Bruh you lost why you tryna cheat?", ephemeral=True)

        elif roleRaffler in player.roles:
            await interaction.response.send_message(f"I'm sorry but you're not eligible to join this.", ephemeral=True)

        elif roleWin or roleMember in player.roles:
            await interaction.response.send_message(f"You: {playerRPSDecision}!\nBot: {botRPSDecision}!", ephemeral=True)

            match playerRPSDecision:
                case '✊ Rock':
                    match botRPSDecision:
                        case '✊ Rock':
                            await interaction.followup.send(f"It's a tie!", ephemeral=True)
                        case '🖐️ Paper':
                            await interaction.followup.send(f"Paper covers rock! You lose.", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case '✌️ Scissors':
                            await interaction.followup.send(f"Rock smashes scissors! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin)  
                        case '🤌 Lizard':
                            await interaction.followup.send(f"Rock crushes lizard! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin) 
                        case '🖖 Spock':
                            await interaction.followup.send(f"Spock vaporizes rocks! You lose!", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case other:
                            pass
                case '🖐️ Paper':
                    match botRPSDecision:
                        case '✊ Rock':
                            await interaction.followup.send(f"Paper covers rock! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin)
                        case '🖐️ Paper':
                            await interaction.followup.send(f"It's a tie!", ephemeral=True)
                        case '✌️ Scissors':
                            await interaction.followup.send(f"Scissors cuts paper! You lose.", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case '🤌 Lizard':
                            await interaction.followup.send(f"Lizard eats paper! You lose!", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case '🖖 Spock':
                            await interaction.followup.send(f"Paper disproves spock! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin)
                        case other:
                            pass
                case '✌️ Scissors':
                    match botRPSDecision:
                        case '✊ Rock':
                            await interaction.followup.send(f"Rock smashes scissors! You lose.", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case '🖐️ Paper':
                            await interaction.followup.send(f"Scissors cuts paper! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin)
                        case '✌️ Scissors':
                            await interaction.followup.send(f"It's a tie!", ephemeral=True)
                        case '🤌 Lizard':
                            await interaction.followup.send(f"Scissors decapitates lizard! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin)
                        case '🖖 Spock':
                            await interaction.followup.send(f"Spock smashes scissors! You lose!", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case other:
                            pass
                case '🤌 Lizard':
                    match botRPSDecision:
                        case '✊ Rock':
                            await interaction.followup.send(f"Rock crushes lizard! You lose!", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case '🖐️ Paper':
                            await interaction.followup.send(f"Lizard eats paper! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin)
                        case '✌️ Scissors':
                            await interaction.followup.send(f"Scissors decapitates lizard! You lose!", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case '🤌 Lizard':
                            await interaction.followup.send(f"It's a tie!", ephemeral=True)
                        case '🖖 Spock':
                            await interaction.followup.send(f"Lizard poisons spock! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin)
                        case other:
                            pass
                case '🖖 Spock':
                    match botRPSDecision:
                        case '✊ Rock':
                            await interaction.followup.send(f"Spock vaporizes rocks! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin)
                        case '🖐️ Paper':
                            await interaction.followup.send(f"Paper disproves spock! You lose!", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case '✌️ Scissors':
                            await interaction.followup.send(f"Spock smashes scissors! You win!", ephemeral=True)
                            await player.remove_roles(roleLose)
                            await player.add_roles(roleWin)
                        case '🤌 Lizard':
                            await interaction.followup.send(f"Lizard poisons spock! You lose!", ephemeral=True)
                            await player.remove_roles(roleWin)
                            await player.add_roles(roleLose)
                        case '🖖 Spock':
                            await interaction.followup.send(f"It's a tie!", ephemeral=True)
                        case other:
                            pass
                case other:
                    pass
#            await player.add_roles(roleLose)
#            channel = bot.get_channel(1083002469593911327)
#            if channel:
#                await channel.send(f"<@{interaction.user.id}>:{playerRPSDecision}")

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