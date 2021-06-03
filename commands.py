import discord
import youtube_dl as youtube_dl
from discord.ext import commands
import asyncio

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


# Referenced from the Author of discord.py Rapptz
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Commands(commands.Cog, name="commands"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="playgame", pass_context=True)
    async def play_song(self, ctx):
        """
        Entry point for the game
        :return: void
        """
        # TODO: Play a song, and wait until someone gets the anime correct, once they do play a different song
        # and continue
        voice_channel = ctx.author.voice.channel
        try:
            await voice_channel.connect()
            await ctx.send("Playing a song in a few seconds, hold tight!")
        except Exception as e:
            print(e)
            await ctx.send("Sorry, but I'm already in a voice channel!")
        await asyncio.sleep(3)

        love_decoration_url = "https://www.youtube.com/watch?v=M1PurvnqTjc"

        player = await YTDLSource.from_url(love_decoration_url, loop=self.bot.loop,
                                           stream=True)
        ctx.voice_client.play(player, after=lambda x: print('Player error: %s' % x) if x else None)
        await ctx.send('Now playing: {}'.format(player.title))

        def check_anime_song(m):
            anime_name = m.content.lower()
            return anime_name == "bunny girl senpai" and m.channel == ctx.channel
        try:
            user_msg = await self.bot.wait_for('message', check=check_anime_song, timeout=180.0)
            await ctx.send("Nice, you guessed the correct anime!")
            ctx.voice_client.stop()
        except Exception as e:
            print(e)
            ctx.voice_client.stop()
        # timeout for 20 seconds for now, TODO: Check the length of the song

    @commands.command(name="leavevc", pass_context=True)
    async def leave_vc(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send("Goodbye!")

    @commands.command(name="hello", pass_context=True)
    async def handle_hello(self, ctx):
        await ctx.send("Shut up scum.")


def setup(bot):
    bot.add_cog(Commands(bot))
