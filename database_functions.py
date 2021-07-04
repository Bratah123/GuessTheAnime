import json


def add_points(author_id, point_amount):
    db = open('database.json', 'r')
    json_data = json.load(db)
    db.close()
    db = open('database.json', 'w')
    if json_data.get(str(author_id)) is None:
        json_data[str(author_id)] = point_amount
    json_data[str(author_id)] += point_amount
    try:
        json.dump(json_data, db, indent=4)
    except Exception as e:
        print(e)
    db.close()


def get_points(discord_id):
    points = 0
    try:
        with open('database.json', 'r') as f:
            json_data = json.load(f)
            if json_data.get(discord_id) is None:
                return 0
            points = json_data[discord_id]
    except Exception as e:
        print(e)

    return points
