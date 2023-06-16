import json
import tkinter
import math
import time

with open("udsu_b3_L3_v1_190701.json") as file:
	j = json.load(file)
j_clear = j.copy()

def get_el(el_id):
    ''' Находит элемент по Id '''
    for lvl in j['Level']:
        for e in lvl['BuildElement']:
            if e['Id'] == el_id:
                return e

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
                i["NumPeople"] = (abs(x2-x1) * abs(y2-y1)) # количество людей = примерная площадь
            max_lvl = max(max_lvl, i["GLevel"])
    while Q:
        bfs(Q.pop(0), Q)

i = 100000
K = 0.9


def step(out, vis):
    ''' Рекурсивная функция '''
    global i
    i -= 1
    vis[out["Id"]] += 1
    eff = out.get('NumPeople')*(K**vis[out["Id"]]) if out.get('NumPeople') else 0
    # Условия прекращения рекурсии
    if vis[out["Id"]] >= 3 or out.get('GLevel') == max_lvl or out['Sign'] == 'DoorWayOut' or i < 1:
        return [out,], eff
    variants = [step(next_out, vis.copy()) for next_out in neighbours(out)]
    path, max_eff= variants[0]
    # Выбираем самый эффективный вариант
    for var in variants:
        if var[1] > max_eff:
            path, max_eff = var
    return path+[out,], max_eff + eff


# ищем входные двери
out_doors = []
for el in j['Level'][0]['BuildElement']:
    if el['Sign'] == "DoorWayOut":
        out_doors.append(el)

# заходим в одну, делаем помещение за ней верхушкой
top_room = get_el(out_doors[0]['Output'][0])
top_room["GLevel"] = 0

bfs(top_room, [])
print("Max level:", max_lvl)
for lvl in j['Level']:
    for e in lvl['BuildElement']:
        visits[e['Id']] = 0

# находим лучшие путь и эффективность пути
t1 = time.time()
best_path, best_eff = step(top_room, visits)
print("t1", t1, " t2", time.time(), "delta", time.time()-t1)
if i < 1:
    print("Interrupted")

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

# Масштаб
scale = 20

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
            c.create_text(cntr(el['XY']), text=el.get('GLevel'))

    for i in range(len(best_path)-1):
        if is_el_on_lvl(best_path[i], lvl) or is_el_on_lvl(best_path[i+1], lvl):
            c.create_line(cntr(best_path[i]['XY']), cntr(best_path[i+1]['XY']), arrow=tkinter.LAST)


top.mainloop()
        
