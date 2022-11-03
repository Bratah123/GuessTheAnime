import json
from typing import Tuple


def get_char_stats(character) -> Tuple[int, int, int]:  # Returns the stats of the given character dictionary
    # Calculate Attack Power
    attack_power = character['favorites']
    if character['animes_from'] == 0:  # If this character isn't even from an anime we make it worth more points
        attack_power *= 2.6
    elif character['animes_from'] == 1:
        attack_power *= 2.2
    else:
        attack_power /= character['animes_from']

    # Calculate Health Points
    health_points = character['favorites']
    if character['mangas_from'] == 0:  # If this character isn't even from an anime we make it worth more points
        health_points *= 2.6
    elif character['mangas_from'] == 1:
        health_points *= 1.5
    else:
        health_points /= character['mangas_from']

    if character['animes_from'] == 3 and character['mangas_from'] == 3:
        attack_power /= 1.4
        health_points /= 1.4

    if character['animes_from'] == 1 and character['mangas_from'] == 1:
        attack_power *= 2.3
        health_points *= 2.3

    if character['animes_from'] == 3 and character['mangas_from'] == 1:
        attack_power *= 1.6
        health_points *= 1.3

    speed = (character['animes_from'] + character['mangas_from'])

    if speed == 1:
        health_points *= 2.8

    return round(attack_power), round(health_points), speed


def return_character_from_name(name: str):  # returns the dictionary of the character
    with open('anime_characters.json', 'r') as f:
        json_data = json.load(f)
        for character in json_data:
            char_name = ' '.join(character['name']).lower()
            if char_name == name.lower():
                return character
            if ' '.join(reversed(character['name'])).lower() == name.lower():
                return character
    return None
