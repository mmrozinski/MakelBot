"""
A simple Discord bot's main file

Functions:
    on_ready()

Miscellaneous variables:
    intents
    cogs
    client
"""

import discord
from discord.ext import commands

import settings
import Local.Keys.botToken as botToken

intents = discord.Intents.all()

cogs: list = ['Functions.Info.Info', 'Functions.Message.Message', 'Functions.Misc.Misc', 'Functions.Users.Users',
              'Functions.Sound.Sound', 'Functions.Message.Conversation', 'Functions.Economy.Economy',
              'Functions.Sound.Listening']

client = commands.Bot(command_prefix=settings.Prefix, help_command=None, intents=intents)


@client.event
async def on_ready():
    """
    Function called when bot starts up
    """
    print('Bot is ready!')
    await client.change_presence(status=discord.Status.online, activity=discord.Game(settings.BotStatus))
    for cog in cogs:
        try:
            print(f'Loading cog {cog}')
            client.load_extension(cog)
            print(f'Loaded cog {cog}')
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load cog {}\n{}'.format(cog, exc))


client.run(botToken.TOKEN)
