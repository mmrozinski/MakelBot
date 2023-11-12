"""
Responsible for handling voice receiving related commands and functionalities

Classes:
    Listening

Functions:

"""
import discord
from discord.ext import commands


async def once_done(sink: discord.sinks, channel: discord.TextChannel,
                    *args):  # Our voice client already passes these in.
    recorded_users = [  # A list of recorded users
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    await sink.vc.disconnect()  # Disconnect from the voice channel.
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in
             sink.audio_data.items()]  # List down the files.
    await channel.send(f"finished recording audio for: {', '.join(recorded_users)}.",
                       files=files)  # Send a message with the accumulated files.


class Listening(commands.Cog):
    bot: commands.Bot = None
    connections = {}

    def __init__(self, bot):
        self.system = None
        self.context = None
        self.bot = bot
        self._last_member = None

    @commands.command()
    async def record(self, ctx: commands.Context):  # If you're using commands.Bot, this will also work.
        voice = ctx.author.voice

        if not voice:
            await ctx.message.reply("You aren't in a voice channel!")

        vc: discord.VoiceClient = await voice.channel.connect()  # Connect to the voice channel the author is in.
        self.connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

        vc.start_recording(
            discord.sinks.WaveSink(),  # The sink type to use.
            once_done,  # What to do once done.
            ctx.channel  # The channel to disconnect from.
        )
        await ctx.message.reply("Started recording!")

    @commands.command()
    async def stop_recording(self, ctx: commands.Context):
        if ctx.guild.id in self.connections:  # Check if the guild is in the cache.
            vc = self.connections[ctx.guild.id]
            vc.stop_recording()  # Stop recording, and call the callback (once_done).
            del self.connections[ctx.guild.id]  # Remove the guild from the cache.
            await ctx.message.delete()  # And delete.
        else:
            await ctx.message.reply("I am currently not recording here.")  # Respond with this if we aren't recording.


def setup(bot):
    """
    Called during bot's startup

    :param bot: bot object, passed by Discord's API
    """
    bot.add_cog(Listening(bot))
