import json

from tcg import tcg_functions


def add_user_to_db(author_id):
    auth_id = str(author_id)
    with open('database.json', 'r') as f:
        data = json.load(f)
        if data.get(auth_id) is None:
            data[auth_id] = {
                "points": 0,
                "elo": 0,
                "team": [],
                "inventory": [],
            }
        else:
            return
    with open('database.json', 'w') as f:
        try:
            json.dump(data, f, indent=4)
        except Exception as e:
            print(e)


def add_points(author_id, point_amount):
    add_user_to_db(author_id)
    auth_id = str(author_id)
    data = {}
    with open('database.json', 'r') as f:
        data = json.load(f)

    data[auth_id]["points"] += point_amount

    with open('database.json', 'w') as f:
        try:
            json.dump(data, f, indent=4)
        except Exception as e:
            print(e)


def get_points(discord_id):
    add_user_to_db(discord_id)
    auth_id = str(discord_id)
    points = 0
    try:
        with open('database.json', 'r') as f:
            json_data = json.load(f)
            if json_data.get(auth_id) is None:
                return 0
            points = json_data[auth_id]['points']
    except Exception as e:
        print(e)

    return points


def get_team(discord_id):
    add_user_to_db(discord_id)
    auth_id = str(discord_id)
    try:
        with open('database.json', 'r') as f:
            json_data = json.load(f)
            return json_data[auth_id]['team']
    except Exception as e:
        print(e)

    return None


def get_inventory(discord_id):
    add_user_to_db(discord_id)
    auth_id = str(discord_id)
    try:
        with open('database.json', 'r') as f:
            json_data = json.load(f)
            return json_data[auth_id]['inventory']
    except Exception as e:
        print(e)

    return None


def add_character_to_team(discord_id, character):
    add_user_to_db(discord_id)
    auth_id = str(discord_id)
    json_data = {}
    try:
        with open('database.json', 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        print(e)

    json_data[auth_id]['team'].append(character)

    with open('database.json', 'w') as f:
        try:
            json.dump(json_data, f, indent=4)
        except Exception as e:
            print(e)

    return True


def add_character_to_inventory(discord_id, character):
    add_user_to_db(discord_id)
    auth_id = str(discord_id)
    json_data = {}

    try:
        with open('database.json', 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        print(e)

    json_data[auth_id]['inventory'].append(character)

    with open('database.json', 'w') as f:
        try:
            json.dump(json_data, f, indent=4)
        except Exception as e:
            print(e)

    return True


def get_elo(discord_id):
    add_user_to_db(discord_id)
    auth_id = str(discord_id)
    try:
        with open('database.json', 'r') as f:
            json_data = json.load(f)
            return json_data[auth_id]['elo']
    except Exception as e:
        print(e)

    return None


def add_elo(discord_id, elo_amount):
    add_user_to_db(discord_id)
    auth_id = str(discord_id)
    data = {}
    with open('database.json', 'r') as f:
        data = json.load(f)

    data[auth_id]["elo"] += elo_amount

    with open('database.json', 'w') as f:
        try:
            json.dump(data, f, indent=4)
        except Exception as e:
            print(e)


def remove_character_from_inventory(discord_id, character_name):
    add_user_to_db(discord_id)
    auth_id = str(discord_id)
    json_data = {}

    res = None

    try:
        with open('database.json', 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        print(e)

    for character in json_data[auth_id]['inventory']:
        if ' '.join(character['name']).lower() == character_name.lower():
            json_data[auth_id]['inventory'].remove(character)
            res = character
        elif ' '.join(reversed(character['name'])).lower() == character_name.lower():
            json_data[auth_id]['inventory'].remove(character)
            res = character

    with open('database.json', 'w') as f:
        try:
            json.dump(json_data, f, indent=4)
        except Exception as e:
            print(e)

    return res


def remove_character_from_team(discord_id, character_name):
    add_user_to_db(discord_id)
    auth_id = str(discord_id)
    json_data = {}

    try:
        with open('database.json', 'r') as f:
            json_data = json.load(f)
    except Exception as e:
        print(e)

    res = None

    for character in json_data[auth_id]['team']:
        if ' '.join(character['name']).lower() == character_name.lower():
            json_data[auth_id]['team'].remove(character)
            res = character
        elif ' '.join(reversed(character['name'])).lower() == character_name.lower():
            json_data[auth_id]['team'].remove(character)
            res = character

    with open('database.json', 'w') as f:
        try:
            json.dump(json_data, f, indent=4)
        except Exception as e:
            print(e)

    return res
