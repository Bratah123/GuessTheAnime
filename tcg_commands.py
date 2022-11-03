import asyncio
import random

import discord
from discord import Embed
from discord.ext import commands, menus

import database_functions
from tcg import tcg_functions


class TeamMenu(menus.Menu):
    def __init__(self):
        super().__init__(timeout=60.0)
        self.embeds = []
        self.embed_index = 0

    async def send_initial_message(self, ctx, channel):
        e: Embed = self.embeds[self.embed_index]
        e.title = f"Team Member ({self.embed_index + 1}/{len(self.embeds)})"
        return await channel.send(embed=self.embeds[self.embed_index])

    @menus.button('⬅')
    async def on_left_arrow(self, payload):
        self.embed_index -= 1
        if self.embed_index <= 0:
            self.embed_index = 0
        e: Embed = self.embeds[self.embed_index]
        e.title = f"Team Member ({self.embed_index + 1}/{len(self.embeds)})"
        await self.message.edit(embed=self.embeds[self.embed_index])

    @menus.button('➡')
    async def on_right_arrow(self, payload):
        self.embed_index += 1
        if self.embed_index >= len(self.embeds):
            self.embed_index = len(self.embeds) - 1
        e: Embed = self.embeds[self.embed_index]
        e.title = f"Team Member ({self.embed_index + 1}/{len(self.embeds)})"
        await self.message.edit(embed=self.embeds[self.embed_index])

    @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f')
    async def on_stop(self, payload):
        self.stop()


class TCGCommands(commands.Cog, name="tcg_commands"):
    def __init__(self, bot):
        self.bot = bot
        self.in_game = {}

    @commands.command(name="card", pass_context=True)
    async def card(self, ctx):
        args = ctx.message.content.split(" ")
        if len(args) < 2:
            await ctx.send("Syntax Error: !card <name of character>")
            return
        card_name = " ".join(args[1:])
        character = tcg_functions.return_character_from_name(card_name)
        if character is None:
            await ctx.send("ERROR: Character not found.")
            return
        e = discord.Embed(title="Character Stats")
        e.set_image(url=character['img'])

        attack, health, speed = tcg_functions.get_char_stats(character)

        # Name
        e.add_field(name="Name", value=" ".join(character['name']), inline=False)

        # Attack Power
        e.add_field(name="Attack Power ⚔", value=f"{attack:,}", inline=True)

        # Health
        e.add_field(name="Health Points 🔴", value=f"{health:,}", inline=True)

        # Speed
        e.add_field(name="Speed ⏩", value=f"{speed:,}", inline=True)

        # Anime From
        e.add_field(name="Anime 📺", value=character["anime"], inline=False)

        await ctx.send(embed=e)

    @commands.command(name="duel", aliases=['d'], pass_context=True)
    async def duel(self, ctx):
        args = ctx.message.content.split(" ")
        if len(args) < 2:
            await ctx.send("Syntax Error: !duel <@user>")
            return
        target_id = args[1].replace("<", "").replace(">", "").replace("@", "").replace("!", "")
        player_team = database_functions.get_team(ctx.message.author.id)
        target_team = database_functions.get_team(target_id)

        if len(player_team) < 1 or len(target_team) < 1:
            await ctx.send("You or your opponent does not have a team.")
            return

        def wait_for_approval(m):
            return (m.content.lower() == "accept" and str(m.author.id) == target_id) \
                   or (m.content.lower() == "decline" and str(m.author.id) == target_id)

        await ctx.send(
            f"{ctx.message.author.mention} has challenged {args[1]} to a duel! Type `accept` to start or `decline` to "
            f"run away!")

        user_msg = None

        try:
            user_msg = await self.bot.wait_for('message', check=wait_for_approval, timeout=10.0)
            user_ans = user_msg.content.lower()
            if user_ans == "decline":
                await ctx.send(f"Duel declined by {user_msg.author.name}.")
                return
            else:
                await ctx.send(f"Duel accepted by {user_msg.author.name}.\nPrepare for DEATH!!")
        except asyncio.TimeoutError:
            await ctx.send(f"Your opponent did not accept the duel in time, {ctx.author.name}.")
            return

        # Duel mechanics here
        player_deck = []
        target_deck = []

        # Add all characters into card objects for easier use
        for char in player_team:
            attack, health, speed = tcg_functions.get_char_stats(char)
            player_deck.append(
                Card(char, attack, health, speed, char['anime'], char['animes_from'], char['mangas_from']))
        for char in target_team:
            attack, health, speed = tcg_functions.get_char_stats(char)
            # character, dmg, health, speed, anime, animes_from, mangas_from
            target_deck.append(
                Card(char, attack, health, speed, char['anime'], char['animes_from'], char['mangas_from']))
        # Calculate any stat boosts, decreases etc.
        player_deck = calculate_team_power(player_deck)
        target_deck = calculate_team_power(target_deck)
        e = Embed(title="KomiTCG Duel", description=f"{ctx.message.author.name} vs {user_msg.author.name}")
        e.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/746519006961336370/942326792293851157/komi_scared.jpg")
        e.add_field(name=f"{ctx.message.author.name}'s deck",
                    value="--------------------------------------------------", inline=False)
        for card in player_deck:
            character_name = " ".join(card.character['name'])
            attack = card.dmg
            health = card.health
            speed = card.speed
            display_stats = f"Attack Power ⚔: {attack}\nHealth 🔴: {health}\nSpeed ⏩: {speed}\nAnime 📺: {card.anime}"
            e.add_field(name=character_name, value=display_stats, inline=True)
        e.add_field(name="-------------------------------------------------",
                    value="-------------------------------------------------", inline=False)
        e.add_field(name=f"{user_msg.author.name}'s deck",
                    value="-------------------------------------------------", inline=False)
        for card in target_deck:
            character_name = " ".join(card.character['name'])
            attack = card.dmg
            health = card.health
            speed = card.speed
            display_stats = f"Attack Power ⚔: {attack}\nHealth 🔴: {health}\nSpeed ⏩: {speed}\nAnime 📺: {card.anime}"
            e.add_field(name=character_name, value=display_stats, inline=True)

        await ctx.send("Here are the stats:", embed=e)

        # Start Combat where each card is facing each other one after another.
        # The card with the highest speed goes first, then the other card.
        # If they are the same speed there is a 50/50 chance
        # If the card is dead it is removed from the deck
        # Check the first card of both decks and see who attacks first
        # If the card is dead, remove it from the deck
        player_top_card = player_deck[0]
        player_dead_cards = []

        target_top_card = target_deck[0]
        target_dead_cards = []

        while len(player_deck) > 0 and len(target_deck) > 0:
            seed = -1
            if player_top_card.speed == target_top_card.speed:
                seed = random.randint(0, 1)
            if player_top_card.speed > target_top_card.speed or seed == 0:
                player_top_card.attack(target_top_card)
                if target_top_card.is_dead:
                    target_dead_cards.append(target_deck.pop(0))
                if len(target_deck) == 0:
                    break
                target_top_card.attack(player_top_card)
                if player_top_card.is_dead:
                    player_dead_cards.append(player_deck.pop(0))
                if len(player_deck) == 0:
                    break
            elif player_top_card.speed < target_top_card.speed or seed == 1:
                if target_top_card.speed > player_top_card.speed:
                    target_top_card.attack(player_top_card)
                    if player_top_card.is_dead:
                        player_dead_cards.append(player_deck.pop(0))
                    if len(player_deck) == 0:
                        break
                    player_top_card.attack(target_top_card)
                    if target_top_card.is_dead:
                        target_dead_cards.append(target_deck.pop(0))
                    if len(target_deck) == 0:
                        break

        # winner of the fight is the one with the most cards left
        if len(player_deck) > len(target_deck):
            winner = ctx.message.author
            database_functions.add_elo(winner.id, len(player_deck))
            database_functions.add_elo(user_msg.author.id, -len(target_dead_cards))
        else:
            winner = user_msg.author
            database_functions.add_elo(winner.id, len(target_deck))
            database_functions.add_elo(ctx.message.author.id, -len(player_dead_cards))

        for card in player_dead_cards:
            database_functions.remove_character_from_team(ctx.author.id, " ".join(card.character['name']))
        for card in target_dead_cards:
            database_functions.remove_character_from_team(user_msg.author.id, " ".join(card.character['name']))
        e = Embed(title="KomiTCG Duel Results", description=f"Winner: {winner.name}")
        e.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/746519006961336370/942326792293851157/komi_scared.jpg")
        player_names_of_dead_cards = []
        target_names_of_dead_cards = []
        for card in player_dead_cards:
            player_names_of_dead_cards.append(" ".join(card.character['name']))
        for card in target_dead_cards:
            target_names_of_dead_cards.append(" ".join(card.character['name']))

        player_casualty_display = "\n".join(player_names_of_dead_cards) if len(
            player_names_of_dead_cards) > 0 else "No Casulties!"
        target_casualty_display = "\n".join(target_names_of_dead_cards) if len(
            target_names_of_dead_cards) > 0 else "No Casulties!"
        e.add_field(name=f"Casualties for {ctx.message.author.name}",
                    value=player_casualty_display,
                    inline=True)
        e.add_field(name=f"Casualties for {user_msg.author.name}",
                    value=target_casualty_display,
                    inline=True)
        await ctx.send(embed=e)

    @commands.command(name="team", aliases=['deck'], pass_context=True)
    async def team(self, ctx):
        auth_id = ctx.author.id
        team = database_functions.get_team(auth_id)
        if len(team) == 0:
            e = discord.Embed(title=f"{ctx.author.name}'s Team")
            e.add_field(name="Team", value="No characters in team.")
            await ctx.send(embed=e)
            return
        list_of_embeds = []
        deck = []
        for character in team:
            attack, health, speed = tcg_functions.get_char_stats(character)
            deck.append(Card(character, attack, health, speed, character['anime'], character['animes_from'],
                             character['mangas_from']))
        deck = calculate_team_power(deck)
        for card in deck:
            e = discord.Embed(title="Team Member")
            e.set_image(url=card.character['img'])

            # Name
            e.add_field(name="Name", value=" ".join(card.character['name']), inline=False)

            # Attack Power
            e.add_field(name="Attack Power ⚔", value=f"{card.dmg:,}", inline=True)

            # Health
            e.add_field(name="Health Points 🔴", value=f"{card.health:,}", inline=True)

            # Speed
            e.add_field(name="Speed ⏩", value=f"{card.speed:,}", inline=True)

            # Anime From
            e.add_field(name="Anime 📺", value=card.character["anime"], inline=False)
            list_of_embeds.append(e)
        menu = TeamMenu()
        menu.embeds = list_of_embeds
        await menu.start(ctx)

    @commands.command(name="inventory", aliases=['inv'], pass_context=True)
    async def inventory(self, ctx):
        auth_id = ctx.author.id
        inv = database_functions.get_inventory(auth_id)
        if len(inv) == 0:
            e = discord.Embed(title=f"{ctx.author.name}'s Inventory")
            e.add_field(name="Inventory", value="No characters in the inventory.")
            await ctx.send(embed=e)
            return
        names = []
        for character in inv:
            names.append(" ".join(character['name']))
        # write to file
        with open("inventory.txt", "w") as file:
            file.write('\n'.join(names))

        # send file to Discord in message
        with open("inventory.txt", "rb") as file:
            await ctx.send("Your **inventory**:", file=discord.File(file, "team.txt"))

    @commands.command(name="move_to_team", pass_context=True)
    async def move_to_team(self, ctx):
        args = ctx.message.content.split(" ")
        if len(args) < 2:
            await ctx.send("Syntax Error: !move_to_team <name of character>")
            return
        card_name = " ".join(args[1:])
        if len(database_functions.get_team(ctx.author.id)) >= 4:
            await ctx.send("You cannot have more than 4 people on your team!")
            return
        character = database_functions.remove_character_from_inventory(ctx.author.id, card_name)
        if character is None:
            await ctx.send("ERROR: Character not found.")
            return
        database_functions.add_character_to_team(ctx.author.id, character)
        await ctx.send("Character moved to team successfully.")

    @commands.command(name="clear_team", pass_context=True)
    async def clear_team(self, ctx):
        team = database_functions.get_team(ctx.author.id)
        for character in team:
            char = database_functions.remove_character_from_team(ctx.author.id, ' '.join(character['name']))
            database_functions.add_character_to_inventory(ctx.author.id, char)
        await ctx.send("Cleared your team successfully!")

    @commands.command(name="deck_info", pass_context=True)
    async def deck_info(self, ctx):
        """
        Command explains the different type of buffs and how dueling works
        """
        rules = """```
Your team's stats may change depending on how you build it.
Every card has a base stat that is calculated by popularity, animes and mangas they are in.
Do !card <name of character> to see their base stats.

There are a couple of ways to buff your deck's stats and here are the rules:
There are no buffs/benefits of using a team less than 4 cards.

Note: These set effects stack!
1. If you have 4 cards from the same anime, you get a significant buff to all stats.
2. If you have all 4 cards from different animes, the strongest member gets nerfed while the weakest member gets buffed.
3. If you have mixmatched animes, the strongest member gets a significant nerf it it's stats.
    
4. If all of the card's in your deck's damage are within 2k range of each other then every card gets a significant buff.
5. If all of the card's in your deck's damage are within 5k range of each other then every card gets a slight.
6. If all of the card's in your deck's damage are within 20k range of each other then every card gets a slight nerf.
    
7. If all of the card's in your deck has 6 speed every card gets a significant damage buff.
8. If all of the card's in your deck has 2 or less speed every card gets a significant health buff.
9. If all of the card's in your deck has less than 1k damage every card gets 25k+ stats.
10. If all of the card's in your deck has the same first name OR last name, every card gains 50L stats
    
11. If the total favorite score of the deck is less than 50k buff every card
12. If the total favorite score of the deck is more than 200k debuff every card
13. If their manga or animes they are from match they are buffed
```
        """

        dueling_sequence = "```DUELING SEQUENCING:\n" \
                           "1. The first card in your deck goes against the first card in your opponent's deck.\n" \
                           "2. Whichever card is faster attacks first (if they have the same speed, it is a 50/50 " \
                           "chance of who attacks first).\n " \
                           "3. When a card is knocked out, the next card in the deck will begin to attack the card " \
                           "that won last.\n" \
                           "4. This continues til someone is out of cards.\n\n" \
                           "PSA: When a card dies, you will lose it from your team and inventory.```"

        await ctx.send(rules)
        await ctx.send(dueling_sequence)


class Card:

    def __init__(self, character, dmg, health, speed, anime, animes_from, mangas_from):
        self.character = character
        self.dmg = dmg
        self.health = health
        self.speed = speed
        self.anime = anime
        self.animes_from = animes_from
        self.mangas_from = mangas_from

        self.is_dead = False

    def attack(self, target):
        target.take_damage(self.dmg)

    def take_damage(self, dmg):
        self.health -= dmg
        if self.health <= 0:
            self.is_dead = True

    def multiply_dmg(self, multiplier):
        self.dmg *= multiplier
        self.dmg = round(self.dmg)

    def multiply_health(self, multiplier):
        self.health *= multiplier
        self.health = round(self.health)

    def add_dmg(self, multiplier):
        self.dmg += multiplier
        self.dmg = round(self.dmg)

    def add_health(self, multiplier):
        self.health += multiplier
        self.health = round(self.health)

    def divide_dmg(self, multiplier):
        self.dmg /= multiplier
        self.dmg = round(self.dmg)

    def divide_health(self, multiplier):
        self.health /= multiplier
        self.health = round(self.health)


def calculate_team_power(player_deck):
    animes_in_team = set()

    # All special additives require a full team.
    if len(player_deck) < 4:
        return player_deck

    for card in player_deck:
        animes_in_team.add(card.anime)

    if len(animes_in_team) == 1:
        for card in player_deck:
            card.multiply_dmg(5.5)
            card.multiply_health(3.5)
    # If the deck isn't completely all unique we debuff their strongest member
    elif len(player_deck) != len(set(player_deck)):
        strongest_card = max(player_deck, key=lambda x: x.dmg)
        strongest_card.dmg /= 2.2
        strongest_card.health /= 2.2
    # If the deck is completely unique we buff their weakest member and debuff their strongest member
    else:
        strongest_card = max(player_deck, key=lambda x: x.dmg)
        strongest_card.dmg /= 1.8
        strongest_card.health /= 1.8
        weakest_card = min(player_deck, key=lambda x: x.dmg)
        weakest_card.dmg *= 2.6
        weakest_card.health *= 2.6

    # We will buff all cards if their damage are within 2k range of each other
    if max(player_deck, key=lambda x: x.dmg).dmg - min(player_deck, key=lambda x: x.dmg).dmg <= 2000:
        for card in player_deck:
            card.multiply_dmg(2)
            card.multiply_health(2)
    # We will slightly buff all cards if their damage are within 5k range of each other
    elif max(player_deck, key=lambda x: x.dmg).dmg - min(player_deck, key=lambda x: x.dmg).dmg <= 5000:
        for card in player_deck:
            card.multiply_dmg(1.5)
            card.multiply_health(1.5)
    # We will debuff all cards if their damage are within 20k range of each other
    elif max(player_deck, key=lambda x: x.dmg).dmg - min(player_deck, key=lambda x: x.dmg).dmg <= 20000:
        for card in player_deck:
            card.divide_dmg(1.5)
            card.divide_health(1.5)

    # We will buff dmg of all cards if every card has 6 speed or more
    if all(card.speed >= 6 for card in player_deck):
        for card in player_deck:
            card.multiply_dmg(3.3)
    # We will buff health of all cards if every card has 2 or less speed
    elif all(card.speed <= 2 for card in player_deck):
        for card in player_deck:
            card.multiply_health(5.5)

    # We will add 25k damage to every card if all cards are less than 1k damage
    if all(card.dmg <= 1000 for card in player_deck):
        for card in player_deck:
            card.add_dmg(25000)
            card.add_health(25000)

    # We will add 50k damage and health to every card if all cards have the same last name
    if len(set(card.character['name'][0] for card in player_deck)) == 1:
        for card in player_deck:
            card.add_dmg(50000)
            card.add_health(50000)
    # For first names
    if len(set(card.character['name'][1] for card in player_deck)) == 1:
        for card in player_deck:
            card.add_dmg(50000)
            card.add_health(50000)

    # if the total favorite score of the deck is less than 50k buff every card
    if sum(card.character['favorites'] for card in player_deck) < 50000:
        for card in player_deck:
            card.multiply_dmg(3.2)
            card.multiply_health(3.2)
    # if the total favorite score of the deck is more than 200k debuff every card
    elif sum(card.character['favorites'] for card in player_deck) > 200000:
        for card in player_deck:
            card.divide_dmg(1.5)
            card.divide_health(1.5)

    # If their manga or animes they are from match they are buffed
    if len(set(card.animes_from for card in player_deck)) == 1:
        for card in player_deck:
            card.multiply_dmg(2.5)
    if len(set(card.mangas_from for card in player_deck)) == 1:
        for card in player_deck:
            card.multiply_health(3.2)

    return player_deck


async def setup(bot):
    await bot.add_cog(TCGCommands(bot))
