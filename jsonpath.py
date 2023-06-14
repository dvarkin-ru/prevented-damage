import json
with open("udsu_b3_L3_v1_190701.json") as file:
	j = json.load(file)

def get_el(el_id):
    ''' Находит элемент по Id '''
    for lvl in j['Level']:
        for e in lvl['BuildElement']:
            if e['Id'] == el_id:
                return e

def neighbours(start_room):
    ''' Находит соседние через DoorWayInt комнаты у данной комнаты, возвращает generator :) '''
    return (get_el(room_id) for door_id in start_room["Output"] if get_el(door_id)['Sign'] == 'DoorWayInt' for room_id in get_el(door_id)["Output"] if room_id != start_room["Id"])

def choose(room):
    ''' Пока что ходит по первым попавшимся непосещённым комнатам '''
    room["Visited"] = True
    print("Visited:", room["Id"], room["Name"])
    rooms = neighbours(room)
    for next_room in rooms:
        if not next_room.get("Visited"):
            choose(next_room)
            return

# Пока что входим в первый попавшийся DoorWayOut
for el in j['Level'][0]['BuildElement']:
    if el['Sign'] == "DoorWayOut":
        choose(get_el(el['Output'][0]))
        break
