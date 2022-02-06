import json
import random

import discord
import youtube_dl as youtube_dl
from discord.ext import commands
import asyncio

from database_functions import add_points, get_points

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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ffmpeg_options = {
    'options': '-vn -fflags +discardcorrupt -ignore_unknown -dn -sn -ab 32000',
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
        random.shuffle(self.song_data)
        self.song_index = 0
        with open('anime_characters.json') as f:
            data = json.load(f)
            self.anime_char_data = data
        self.in_game = {}

    @commands.command(name="playgame", aliases=['pg'], pass_context=True)
    async def play_game(self, ctx):
        """
        Entry point for the game
        :return: void
        """
        play_amount = 0
        args = ctx.message.content.split(" ")
        if len(args) > 2:
            play_amount += int(args[1])
        voice_channel = ctx.author.voice.channel
        try:
            await voice_channel.connect()
            await ctx.send("Playing a song in a few seconds, hold tight!")
        except Exception as e:
            print(e)
            await ctx.send("Starting up another game!")
        await asyncio.sleep(1)

        if self.song_index == len(self.song_data) - 1:
            self.song_index = 0
            random.shuffle(self.song_data)
            await ctx.send("All unique songs have been played, shuffling the list now")

        def check_anime_song(m):
            anime_name = m.content.lower()
            return anime_name == music_to_guess.lower() and m.channel == ctx.channel

        while True:
            try:
                music_to_guess = self.song_data[self.song_index][0]
                music_url = self.song_data[self.song_index][1]

                player = await YTDLSource.from_url(music_url, loop=self.bot.loop,
                                                   stream=True)
                try:
                    ctx.voice_client.play(player, after=lambda x: print('Player error: %s' % x) if x else None)
                except Exception as e:
                    print("error playing song:", e)
                    self.song_index += 1
                    continue
                await ctx.send(
                    "Try guessing this anime by typing in this channel (anyone can try)! You got 25 seconds.")

                user_msg = await self.bot.wait_for('message', check=check_anime_song, timeout=25.0)
                add_points(str(user_msg.author.id), 1)
                await ctx.send("Nice, you guessed the correct anime ({})!".format(
                    music_to_guess.title()))

                self.song_index += 1

                if self.song_index == len(self.song_data) - 1:
                    self.song_index = 0
                    random.shuffle(self.song_data)
                    await ctx.send("All unique songs have been played, shuffling the list now")

                music_to_guess = self.song_data[self.song_index][0]
                music_url = self.song_data[self.song_index][1]

                ctx.voice_client.stop()
                await asyncio.sleep(1)
            except Exception as e:
                print(e)
                await ctx.send(
                    "Sorry, you took to long to guess do !playgame to start again, the song was from {}.".format(
                        music_to_guess.title()))
                self.song_index += 1
                ctx.voice_client.stop()

    @commands.command(name="playsong", pass_context=True)
    async def play_song(self, ctx):
        voice_channel = ctx.author.voice.channel
        try:
            await voice_channel.connect()
            await ctx.send("Playing a random anime song in my database, hold tight!")
        except Exception as e:
            print(e)
            ctx.voice_client.stop()
            await ctx.send("Starting up another random anime song!")
        await asyncio.sleep(1)

        rand_idx = random.randint(0, len(self.song_data) - 1)
        music_url = self.song_data[rand_idx][1]

        player = await YTDLSource.from_url(music_url, loop=self.bot.loop,
                                           stream=True)
        ctx.voice_client.play(player, after=lambda x: print('Player error: %s' % x) if x else None)

    @commands.command(name="leavegame", pass_context=True)
    async def leave_vc(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send("Goodbye!")

    @commands.command(name="hello", pass_context=True)
    async def handle_hello(self, ctx):
        await ctx.send("Shut up scum.")

    @commands.command(name="stats", pass_context=True)
    async def handle_stats(self, ctx):
        e = discord.Embed(title=ctx.author.name + "'s Stats",
                          description=f"Song Points: {get_points(str(ctx.author.id))}")
        await ctx.send(embed=e)

    @commands.command(name="query_song", aliases=['qs'], pass_context=True)
    async def query_song(self, ctx):
        args = ctx.message.content.split(" ")
        if len(args) < 2:
            await ctx.send("Format: !query_song <anime name>")
            return
        links = ""
        queried_name = " ".join(args[1:]).lower()
        total_songs = 0
        for data in self.song_data:
            anime_name = data[0].lower()
            if queried_name in anime_name:
                # youtube_vid = await YTDLSource.from_url(data[1], stream=True)
                links += anime_name.title() + f": " + data[1] + "\n\n"  # Links
                total_songs += 1

        await ctx.send(
            f"All Song Links from the queried {queried_name.title()}:\n```Total Songs Found: {total_songs}\n\n{links}```")

    @commands.command(name="character", aliases=['char', 'c', 'C'], pass_context=True)
    async def rand_char(self, ctx):
        if self.in_game.get(ctx.author.id):
            await ctx.send("You are already in a game, please finish that one first.")
            return
        if self.in_game.get(ctx.author.id) is None:
            self.in_game[ctx.author.id] = True
        if not self.in_game.get(ctx.author.id):
            self.in_game[ctx.author.id] = True
        character = random.choice(self.anime_char_data)
        e = discord.Embed(title="Guess the Character")
        e.set_image(url=character['img'])

        def check(m):
            char_name = m.content.lower()
            if m.channel == ctx.channel:
                for n in character['name']:
                    if char_name == n.lower():
                        return True
            return char_name == " ".join(character['name']).lower()

        await ctx.send(embed=e)

        try:
            user_msg = await self.bot.wait_for('message', check=check, timeout=12.0)
            add_points(str(user_msg.author.id), 1)
            await ctx.send(
                "Nice, {} got the correct answer, you gain a point! ({})".format(user_msg.author.name, " ".join(
                    character['name'])))
        except asyncio.TimeoutError:
            await ctx.send(f"You could not answer correctly in the time given {ctx.author.name}.")
        finally:
            self.in_game[ctx.author.id] = False

    @commands.command(aliases=['sg'], pass_context=True)
    async def suggest_song(self, ctx):
        args = ctx.message.content.split(" ")
        if len(args) < 3:
            await ctx.send("Format: !suggest_song or !sg <youtube_link> <anime name>")
            return

        youtube_link = args[1]
        anime_name = " ".join(args[2:])

        if str(ctx.author.id) == OWNER_CLIENT_ID:
            self.song_data.append([anime_name, youtube_link])
            with open('songs.json', 'w') as json_file:
                json_string = json.dumps(self.song_data, indent=4)
                json_file.write(json_string)
            await ctx.send("Successfully added anime song to song database.")
            return
        else:
            await ctx.send("Considering the song suggestion, please wait until Brandon's approval.")
            if anime_name.startswith("http"):
                await ctx.send("The correct format is: !!suggest_song <YOUTUBE LINK> <ANIME NAME>")
                return

            def wait_for_approval(m):
                return (m.content.lower() == "lgtm" and str(m.author.id) == OWNER_CLIENT_ID) \
                       or (m.content.lower() == "no" and str(m.author.id) == OWNER_CLIENT_ID)

        try:
            user_msg = await self.bot.wait_for('message', check=wait_for_approval, timeout=180.0)
            if user_msg.content.lower() == "no":
                await ctx.send("Unapproved by Brandon.")
                return
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
