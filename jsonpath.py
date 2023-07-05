import json
import tkinter
import math
import time
from operator import itemgetter, truediv
import sys
sys.setrecursionlimit(4000)

# Имя файла, название теста, число людей в помещении, время эвакуации, номер входной двери
tests = (("udsu_b1_L4_v1_190701 (1).json", "1.1", 617, 226, 1),
         ("udsu_b2_L4_v1_190701.json", "2.1", 749, 233, 9),
         ("udsu_b3_L3_v1_190701 (1).json", "3.1", 180, 167, 1),
         ("udsu_b4_L5_v1_190701.json", "4.1", 1135, 335, 2),
         ("udsu_b5_L4_v1_200102.json", "5.1", 159, 247, 4),
         ("udsu_b7_L8_v1_190701.json", "7.2", 335, 265, 1))
test_num = 2

scale = 20 # Масштаб здания в tkinter
choosen_door = tests[test_num][4] # Дверь, в которую входит нарушитель
intruder_type = 1 # Тип нарушителя
vision_lvl = 6 # дальность видимости для нарушителей 2 и 3
i = 1000000 # Кол-во допустимых входов в рекурсивную функцию
num_people = tests[test_num][2]
te = tests[test_num][3]

old_i = i

with open(tests[test_num][0]) as file:
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

def room_area(xy):
    return math.fabs(0.5*sum((x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(xy, xy[1:]+xy[:1]))))

def get_total_area(j):
    total_area = 0.0
    for lvl in j['Level']:
        for e in lvl['BuildElement']:
            if e['Sign'] in ("Room", "Staircase"):
                total_area += room_area(e["XY"][0])
    return total_area

def bfs(v, Q, visits, density):
    ''' Проходимся по графу по ширине '''
    if not (visits.get(v["Id"]) is None):
        return
    visits[v['Id']] = 0
    # BFS.append(out)  # Запоминаем порядок обхода
    # print("v = ", v)
    for i in neighbours(v):  # Все смежные с v вершины
        if visits.get(i['Id']) is None:
            Q.append(i)
            i["GLevel"] = v["GLevel"]+1
            #x1, y1, x2, y2 = *i["XY"][0][0], *i["XY"][0][2]
            #if i["Type"] == 8: # имитируем людей в крайних кабинетах
                #i["NumPeople"] = int(abs(x2-x1) * abs(y2-y1)) # количество людей = примерная площадь
            i["NumPeople"] = room_area(i["XY"][0]) * density
    while Q:
        bfs(Q.pop(0), Q, visits, density)


def cntr_real(coords):
    ''' Центр в координатах здания '''
    xy = coords["XY"][0][:-1]
    return sum((x for x, y in xy))/len(xy), sum((y for x, y in xy))/len(xy)

def add_door(j, id1, id2):
    el1, el2 = get_el(id1), get_el(id2)
    door_id = "{0}"
    el1["Output"].append(door_id)
    el2["Output"].append(door_id)
    lvl = None
    for lvl_j in j['Level']:
        if is_el_on_lvl(el1, lvl_j):
            lvl = lvl_j
    if not lvl:
        print("Wrong id!")
        return
    xy1, xy3 = cntr_real(el1), cntr_real(el2)
    xy2, xy4 = (xy1[0], xy3[1]), (xy3[0], xy1[1])
    lvl['BuildElement'].append({"Id": door_id, "Sign": "DoorWay", "XY": [(xy1, xy2, xy3, xy4, xy1),], "Output": [id1, id2]})

# add_door(j, "{deb2ccb8-43ea-465e-a3ee-e54affced3a9}", "{58f01831-e806-4437-894c-a2cdcd3f239e}")

def vision(room, vis, curr_path, lvl = 0):
    if len(curr_path) == 2: # в пути только 2 помещения, не можем взять 2 двери
        ob1 = top_room
    elif len(curr_path) >= 3:
        ob1 = get_door(curr_path[-2], curr_path[-3])
    else:
        print("ERROR! Intruder outside?")
        sys.exit()
    ob2 = get_door(curr_path[-1], curr_path[-2])
    curr_room_dist = math.dist(cntr_real(ob1), cntr_real(ob2))
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

def step_variants(room, vis, curr_path, disabled_rooms):
    if intruder_type == 1:
        return [n for n in neighbours(room) if n["GLevel"] == room["GLevel"]+1 and n not in disabled_rooms]
    elif intruder_type in (2, 3):
        # Варианты перехода во все непосещённые помещения
        v = [n for n in neighbours(room) if vis[n["Id"]] == 0 and n not in disabled_rooms]
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

def step(from_room, to_room, vis, curr_path, disabled_rooms, max_lvl):
    ''' Рекурсивная функция '''
    global i
    i -= 1
    door = from_room if from_room["Sign"] == 'DoorWayOut' else get_door(from_room, to_room) # для входа
    vis[door["Id"]] += 1
    vis[to_room["Id"]] += 1
    eff = to_room['NumPeople']
    variants = [step(to_room, next_to_room, vis.copy(), curr_path+[to_room], disabled_rooms, max_lvl) for next_to_room in step_variants(to_room, vis.copy(), curr_path+[to_room], disabled_rooms)]
    # Условия прекращения рекурсии
    if not variants or vis[door["Id"]] >= 3 or to_room["GLevel"] == max_lvl or i < 1:
        return curr_path+[to_room], eff
    # Выбираем самый эффективный вариант
    path, max_eff = max(variants, key = itemgetter(1))
    return path, max_eff + eff

def get_out_doors(j):
    ''' Ищем входные двери'''
    return [el for lvl in j['Level'] for el in lvl['BuildElement'] if el['Sign'] == "DoorWayOut"]

def intruder(j, top_door, top_room, disabled_rooms = []):
    # находим лучшие путь и эффективность пути
    max_lvl = max((e["GLevel"] for lvl in j['Level'] for e in lvl['BuildElement'] if e.get("GLevel")))
    # print("Max level:", max_lvl)
    t1 = time.time()
    visits = {e['Id']: 0 for lvl in j['Level'] for e in lvl['BuildElement']}
    best_path, best_eff = step(get_el(top_door["Id"]), top_room, visits, [], disabled_rooms, max_lvl)
    t2 = time.time()
    if i < 1:
        print("[Interrupted]")
    # print("Time:", t2-t1, " i:", old_i-i)
    # print(int((old_i-i)/(t2-t1)), "steps per second")
    return best_path

def gen_3_paths(choosen_door):
    total_area = get_total_area(j)
    density = num_people/total_area
    # заходим в одну, делаем помещение за ней верхушкой
    top_door = get_out_doors(j)[choosen_door]
    top_room = get_el(top_door['Output'][0])
    top_room["GLevel"] = 0

    bfs(top_room, [], {}, density)
    paths = []
    for path_num in range(3):
        end_paths = [p[-1] for p in paths]
        p = intruder(j, top_door, top_room, end_paths)

        # print(*[str(v["Id"])+'\n' for v in best_path])
        time = []
        len_path = math.dist(cntr_real(top_door), cntr_real(get_door(p[0], p[1]))) if len(p)>0 else 0
        num_victims = 0
        for i in range(len(p)-2):
            door1, door2 = get_door(p[i], p[i+1]), get_door(p[i+1], p[i+2])
            if door1 == door2:
                # зашёл в комнату и вышел из неё
                # door_len_path += 1 # метр, например
                pass
            else:
                # расстояние между средними точками дверей
                len_path += math.dist(cntr_real(door1), cntr_real(door2))
        path_area = 0
        for room in p:
            num_victims += room["NumPeople"]
            path_area += room_area(room['XY'][0])
        
        paths += [p]
        print("Информация, ПУТЬ", tests[test_num][1], path_num+1)
        print("Длина пути по дверям:", len_path)
        t_intruder = 100/60*len_path
        print("Время нарушителя:", t_intruder)
        print("Отношение к Te:", t_intruder/te)
        print("Площадь:", path_area)
        print("Плотность:", density)
        print("Количество жертв:", num_victims)
        print()
    return paths

paths = gen_3_paths(choosen_door)
best_path = paths[-1]

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
path_colors = ("red", "green", "blue")
for lvl, c in cs:
    for el in lvl['BuildElement']:
        for xy in el['XY']:
            p = c.create_polygon([crd(x,y) for x, y in xy[:-1]], fill=colors[el['Sign']], outline='black')
            c.tag_bind(p, "<Button-1>", lambda e, el_id=el['Id']: print(el_id))
        if el["Sign"] == "Room":
            c.create_text(cntr(el['XY']), text=str(el.get('GLevel'))+"("+str(int(el.get('NumPeople')))+")")
    for i, path in enumerate(paths): 
        for path_from, path_to in zip(path, path[1:]):
            if is_el_on_lvl(path_from, lvl) or is_el_on_lvl(path_to, lvl):
                c.create_line(cntr(path_from['XY']), cntr(path_to['XY']), arrow=tkinter.LAST, fill=path_colors[i])
        if is_el_on_lvl(path[-1], lvl):
            c.create_text([i+12 for i in cntr(path[-1]['XY'])], text="BREAK") # окончание пути, смещённое на 12 точек


top.mainloop()
        
