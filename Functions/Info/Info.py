"""
Responsible for handling information providing commands

Classes:
    Info

Functions:
    setup
"""

import discord
from discord.ext import commands

import settings


class Info(commands.Cog):
    """
    Contains information providing commands

    Methods
    -------
        info(self, ctx)
        avatar(self, ctx)
        help(self, ctx)
    """

    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def info(self, ctx):
        """
        Provides basic information about the bot

        :param ctx: context object
        """
        info_board = discord.Embed(
            title=settings.BotName,
            description="Podstawy kodu tego bota mogły, ale nie musiały, zostać bezczelnie ukradzione z GitHuba",
            colour=discord.Colour.dark_purple()
        )
        info_board.set_footer(text=settings.BotOwner)
        info_board.add_field(name="Komendy", value="Wpisz " + settings.Prefix + "help aby pokazać listę komend.",
                             inline=True)
        await ctx.send(embed=info_board)

    @commands.command()
    async def avatar(self, ctx):
        """
        Sends a message with author's avatar

        :param ctx: context object
        """
        await ctx.send(ctx.author.avatar_url)


    @commands.command()
    async def help(self, ctx):
        """
        Sends a message with information on available commands

        :param ctx: context object
        """
        info_board = discord.Embed(
            title=settings.BotName,
            colour=discord.Colour.dark_purple()
        )
        info_board.set_footer(text=settings.BotOwner)
        info_board.add_field(name=settings.Prefix + "avatar", value="Wyświetla twój awatar", inline=False)
        info_board.add_field(name=settings.Prefix + "info", value="Informacje o bocie", inline=False)
        info_board.add_field(name=settings.Prefix + "roll (X)", value="Rzut kością DX (domyślnie D6)", inline=False)
        await ctx.send(embed=info_board)


def setup(bot):
    """
    Called during bot's startup

    :param bot: bot object, passed by Discord's API
    """
    bot.add_cog(Info(bot))
