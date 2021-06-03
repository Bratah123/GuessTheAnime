import json
import random

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

OWNER_CLIENT_ID = "207371595113562124"


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
        with open('songs.json') as f:
            data = json.load(f)
            self.song_data = data

    @commands.command(name="playgame", pass_context=True)
    async def play_song(self, ctx):
        """
        Entry point for the game
        :return: void
        """
        voice_channel = ctx.author.voice.channel
        try:
            await voice_channel.connect()
            await ctx.send("Playing a song in a few seconds, hold tight!")
        except Exception as e:
            print(e)
            await ctx.send("Sorry, but I'm already in a voice channel!")
        await asyncio.sleep(3)

        rand_idx = random.randint(0, len(self.song_data) - 1)
        music_to_guess = self.song_data[rand_idx][0]
        music_url = self.song_data[rand_idx][1]

        player = await YTDLSource.from_url(music_url, loop=self.bot.loop,
                                           stream=True)
        ctx.voice_client.play(player, after=lambda x: print('Player error: %s' % x) if x else None)
        await ctx.send("Try guessing the anime by typing in this channel (anyone can try)! You got 3 minutes.")

        def check_anime_song(m):
            anime_name = m.content.lower()
            return anime_name == music_to_guess.lower() and m.channel == ctx.channel

        try:
            user_msg = await self.bot.wait_for('message', check=check_anime_song, timeout=180.0)
            await ctx.send("Nice, you guessed the correct anime ({})!".format(music_to_guess.title()))
            ctx.voice_client.stop()
        except Exception as e:
            print(e)
            await ctx.send("Sorry, you took to long to guess.")
            ctx.voice_client.stop()

    @commands.command(name="leavevc", pass_context=True)
    async def leave_vc(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send("Goodbye!")

    @commands.command(name="hello", pass_context=True)
    async def handle_hello(self, ctx):
        await ctx.send("Shut up scum.")

    @commands.command(name="suggest_song", pass_context=True)
    async def suggest_song(self, ctx):
        args = ctx.message.content.split(" ")
        if len(args) < 3:
            await ctx.send("Format: !!suggest_song <youtube_link> <anime name>")
            return

        youtube_link = args[1]
        anime_name = " ".join(args[2:])

        if str(ctx.author.id) == OWNER_CLIENT_ID:
            self.song_data.append([anime_name, youtube_link])
            with open('songs.json', 'w') as json_file:
                json_string = json.dumps(self.song_data, indent=4)
                json_file.write(json_string)
            print(anime_name)
            print(youtube_link)
            await ctx.message.delete()
            await ctx.send("Successfully added anime song to song database.")
            return
        else:
            await ctx.send("Considering the song suggestion, please wait until Brandon's approval.")
            if anime_name.startswith("http"):
                await ctx.send("The correct format is: !!suggest_song <ANIME NAME> <YOUTUBE LINK>")
                return

            def wait_for_approval(m):
                return m.content.lower() == "lgtm" and str(m.author.id) == OWNER_CLIENT_ID

            try:
                user_msg = await self.bot.wait_for('message', check=wait_for_approval, timeout=180.0)
                self.song_data.append([anime_name, youtube_link])
                with open('songs.json', 'w') as json_file:
                    json_string = json.dumps(self.song_data, indent=4)
                    json_file.write(json_string)
                await ctx.send("Successfully added anime song to song database.")
            except Exception as e:
                print(e)
                await ctx.send("Ran out of time for approval")


def setup(bot):
    bot.add_cog(Commands(bot))
