import json
import tkinter
import math
import time
from operator import itemgetter, truediv
import sys
sys.setrecursionlimit(4000)


scale = 20 # Масштаб здания в tkinter
choosen_door = 1 # Дверь, в которую входит нарушитель
intruder_type = 3 # Тип нарушителя
i = 1000000 # Кол-во допустимых входов в рекурсивную функцию

old_i = i

with open("udsu_b3_L3_v1_190701.json") as file:
	j = json.load(file)

def get_el(el_id):
    ''' Находит элемент по Id '''
    for lvl in j['Level']:
        for e in lvl['BuildElement']:
            if e['Id'] == el_id:
                return e

def get_door(room1, room2):
    if room1 == room2:
        #raise ValueError("Get_door: same room as arguments! "+room1["Name"])
        return
    for door1 in room1["Output"]:
        for door2 in room2["Output"]:
            if door1==door2:
                return get_el(door1)

def is_el_on_lvl(el, lvl):
    ''' Принадлежит ли элемент этажу '''
    el_id = el["Id"]
    for e in lvl['BuildElement']:
        if e['Id'] == el_id:
            return True
    return False

def neighbours(start_room):
    ''' Находит соседние через DoorWayInt комнаты у данной комнаты, возвращает generator :) '''
    return (get_el(room_id) for door_id in start_room["Output"] if get_el(door_id)['Sign'] in ('DoorWayInt', 'DoorWay') for room_id in get_el(door_id)["Output"] if room_id != start_room["Id"])

max_lvl = 0
visits = {}

def bfs(v, Q):
    ''' Проходимся по графу по ширине '''
    global max_lvl
    global visits
    if not (visits.get(v["Id"]) is None):
        return
    visits[v['Id']] = 0
    # BFS.append(out)  # Запоминаем порядок обхода
    # print("v = ", v)
    for i in neighbours(v):  # Все смежные с v вершины
        if visits.get(i['Id']) is None:
            Q.append(i)
            i["GLevel"] = v["GLevel"]+1
            x1, y1, x2, y2 = *i["XY"][0][0], *i["XY"][0][2]
            if i["Type"] == 8: # имитируем людей в крайних кабинетах
                i["NumPeople"] = int(abs(x2-x1) * abs(y2-y1)) # количество людей = примерная площадь
            max_lvl = max(max_lvl, i["GLevel"])
    while Q:
        bfs(Q.pop(0), Q)


def cntr_real(coords):
    ''' Центр в координатах здания '''
    xy = coords["XY"][0][:-1]
    return sum((x for x, y in xy))/len(xy), sum((y for x, y in xy))/len(xy)

def distance(ob1, ob2):
    if not ob1:
        print("NO OB1, program will crashed NOW")
    if not ob2:
        print("NO OB2, program will crashed NOW")
    (x1, y1), (x2, y2) = cntr_real(ob1), cntr_real(ob2)
    return math.sqrt((x2-x1)**2+(y2-y1)**2)

vision_lvl = 6

def vision(room, vis, curr_path, lvl = 0):
    if len(curr_path) == 2: # в пути только 2 помещения, не можем взять 2 двери
        ob1 = top_room
    elif len(curr_path) >= 3:
        ob1 = get_door(curr_path[-2], curr_path[-3])
    else:
        print("ERROR! Intruder outside?")
        sys.exit()
    ob2 = get_door(curr_path[-1], curr_path[-2])
    curr_room_dist = distance(ob1, ob2)
    if lvl >= vision_lvl:
        return room["NumPeople"], curr_room_dist
    vis[room["Id"]] += 1
    v = [vision(n, vis.copy(), curr_path+[n], lvl+1) for n in neighbours(room) if vis[n["Id"]] == 0]
    pep, dist = sum((p for p, d in v)), sum((d for p, d in v))
    return pep+room["NumPeople"], dist+curr_room_dist

def dict_peak(d, key, reverse):
    ''' Возвращает крайние элементы словаря d по ключу key,
    это минимальные элементы если reverse == False, иначе максимальные '''
    d = sorted(d, key=itemgetter(key), reverse=reverse)
    return [i for i in d if i[key] == d[0][key]]

def step_variants(room, vis, curr_path):
    if intruder_type == 1:
        return [n for n in neighbours(room) if n["GLevel"] == room["GLevel"]+1]
    elif intruder_type in (2, 3):
        # Варианты перехода во все непосещённые помещения
        v = [n for n in neighbours(room) if vis[n["Id"]] == 0]
        if intruder_type == 3:
            # Нарушитель типа 3 предпочтёт путь с наибольшим уроном за время
            visible = [(truediv(*vision(n, vis.copy(), curr_path+[n])), n) for n in v]
        else:
            # Нарушитель типа 2 предпочтёт путь с наибольшим уроном в принципе
            visible = [(vision(n, vis.copy(), curr_path+[n])[0], n) for n in v]
        if visible: # если такие находятся
            max_eff = max(visible, key=itemgetter(0))
            if max_eff[0] > 0: # если хотя бы на одном из них есть люди
                return [max_eff[1]]
            else:
                # выбираем высокоуровневые варианты
                hi_lev = dict_peak(v, "GLevel", True) #[max(v, key=itemgetter("GLevel"))]
                # из них можно выбрать вариант с наиболее быстро преодолеваемыми дверными проёмами
                # а пока выберем вариант с наибольшим возможным расстоянием (наименьшее кол-во дверей за расстояние)
                return [max(((vision(n, vis.copy(), curr_path+[n])[1], n) for n in hi_lev), key=itemgetter(0))[1]]
            
        # если непосещённых нет, идём назад, но не назад в назад
        for back in reversed(curr_path):
            door = get_door(room, back)
            if door and vis[door["Id"]] <= 1:
                return [back]
        return [] # ???

def step(from_room, to_room, vis, curr_path):
    ''' Рекурсивная функция '''
    global i
    i -= 1
    door = from_room if from_room["Sign"] == 'DoorWayOut' else get_door(from_room, to_room) # для входа
    vis[door["Id"]] += 1
    vis[to_room["Id"]] += 1
    eff = to_room['NumPeople']
    # Условия прекращения рекурсии
    if (vis[door["Id"]] >= 3) or (to_room["GLevel"] == max_lvl) or (i < 1):
        print(i, end = '   \r') # чтобы не так часто
        return curr_path+[to_room], eff
    variants = [step(to_room, next_to_room, vis.copy(), curr_path+[to_room]) for next_to_room in step_variants(to_room, vis.copy(), curr_path+[to_room])]
    # Выбираем самый эффективный вариант
    path, max_eff = max(variants, key = itemgetter(1)) if variants else (curr_path, 0)
    return path, max_eff + eff


# ищем входные двери
out_doors = []
for el in j['Level'][0]['BuildElement']:
    if el['Sign'] == "DoorWayOut":
        out_doors.append(el)

# заходим в одну, делаем помещение за ней верхушкой
top_door = out_doors[choosen_door]
top_room = get_el(top_door['Output'][0])
top_room["GLevel"] = 0

bfs(top_room, [])
print("Max level:", max_lvl)
for lvl in j['Level']:
    for e in lvl['BuildElement']:
        visits[e['Id']] = 0

# находим лучшие путь и эффективность пути
t1 = time.time()
best_path, best_eff = step(get_el(top_door["Id"]), top_room, visits, [])
t2 = time.time()
if i < 1:
    print("[Interrupted]")
print("Time:", t2-t1, " i:", old_i-i)
print(int((old_i-i)/(t2-t1)), "steps per second")

# print(*[str(v["Id"])+'\n' for v in best_path])

# находим offset для canvas
min_x, min_y, max_x, max_y = 0, 0, 0, 0
for lvl in j['Level']:
    for el in lvl['BuildElement']:
        for xy in el['XY']:
            for x, y in xy:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
offset_x, offset_y = -min_x, -min_y

def crd(x, y):
    ''' Перевод из координат здания в координаты canvas '''
    return (x+offset_x)*scale, (y+offset_y)*scale

def cntr(coords):
    ''' Центр для canvas по координатам здания '''
    xy = [crd(x, y) for xy in coords for x, y in xy[:-1]]
    return sum((x for x, y in xy))/len(xy), sum((y for x, y in xy))/len(xy)


# Tkinter окно для каждого этажа
cs = []
for lvl in j["Level"]:
    top = tkinter.Tk()
    top.title(lvl['NameLevel'])
    frame=tkinter.Frame(top)
    frame.pack(expand=True, fill=tkinter.BOTH)
    c = tkinter.Canvas(frame, scrollregion=(*crd(min_x, min_y), *crd(max_x, max_y)))
    v = tkinter.Scrollbar(frame, orient = 'vertical')
    v.pack(side=tkinter.RIGHT, fill = tkinter.Y)
    v.config(command=c.yview)
    h = tkinter.Scrollbar(frame, orient = 'horizontal')
    h.pack(side=tkinter.BOTTOM, fill = tkinter.X)
    h.config(command=c.xview)
    c.config(xscrollcommand=h.set, yscrollcommand=v.set)
    c.pack(side=tkinter.LEFT,expand=True,fill=tkinter.BOTH)
    cs.append((lvl, c))

# Рисуем
colors = {"Room": "", "DoorWayInt": "yellow", "DoorWayOut": "brown", "DoorWay": "", "Staircase": "green"}
for lvl, c in cs:
    for el in lvl['BuildElement']:
        for xy in el['XY']:
            c.create_polygon([crd(x,y) for x, y in xy[:-1]], fill=colors[el['Sign']], outline='black')
        if el["Sign"] == "Room":
            c.create_text(cntr(el['XY']), text=str(int(el.get('GLevel')))+"("+str(int(el.get('NumPeople')))+")")

    for i in range(len(best_path)-1):
        if is_el_on_lvl(best_path[i], lvl) or is_el_on_lvl(best_path[i+1], lvl):
            c.create_line(cntr(best_path[i]['XY']), cntr(best_path[i+1]['XY']), arrow=tkinter.LAST)
    if is_el_on_lvl(best_path[-1], lvl):
        c.create_text([i+12 for i in cntr(best_path[-1]['XY'])], text="BREAK") # окончание пути, смещённое на 12 точек


top.mainloop()
        
