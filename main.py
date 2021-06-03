"""
A Discord that lets you play "guess the anime song"
@Author Brandon
Created 6/02/2021 MM/DD/YYYY
"""
from discord.ext import commands
import json

with open('config.json') as f:
    json_data = json.load(f)
    PREFIX = json_data['PREFIX']
    TOKEN = json_data['TOKEN']

bot = commands.Bot(command_prefix=PREFIX)

# Load commands cog
print("Loading all commands..")
bot.load_extension("commands")


@bot.event
async def on_ready():
    print("Bot is now online.")


if __name__ == '__main__':
    print("Loading Bot..")
    bot.run(TOKEN)
