#Сложность здания
from pprint import pprint
import networkx as nx
import json 
from collections import Counter
import math

#class Model:
#    def __init__(self, speed, time, length):
#        self.speed = speed
#        self.time = time
#        self.length = length


pathJson = [
    #'jsonUdsu/udsu_b1_L4_v1_190701 (1).json',
    #'jsonUdsu/udsu_b2_L4_v1_190701.json',
    #'jsonUdsu/udsu_b3_L3_v1_190701 (1).json',
    #'jsonUdsu/udsu_b4_L5_v1_190701.json',
    #'jsonUdsu/udsu_b5_L4_v1_200102.json',
    #'jsonUdsu/udsu_b7_L8_v1_190701.json'
    'test.json'
]

#Скорость нарушителя
V = 1

roomsData = []

def getObjectCount():
    
    roomsCount = 0
    doorsCount = 0
    widthCount = 0
    depthCount = 0
    P = []
    H = []
    S0 = []
    H1 = []
    S1 = []
    U = []
    for i, jsonBuild in enumerate(pathJson):
        with open(jsonBuild, 'r', encoding='utf-8') as f:
            jsonsrc = json.load(f)

        
        doors = []
        rooms = []

        roomsOutput = {}
        doorsOutput = {}

        

        doorsToStreet = []

        bimLevels = jsonsrc['Level']
        for level in bimLevels:
            for bimEl in level['BuildElement']:
                if (bimEl['Sign'] ==  'Room' or bimEl['Sign'] == 'Staircase'):
                    X = []
                    Y = []
                    #for idx in range(len(bimEl['XY'][0])):
                    #    X.append(bimEl['XY'][0][idx][0])
                    #    Y.append(bimEl['XY'][0][idx][1])
                    #Square = abs(X[2] - X[0]) * abs(Y[1] - Y[0])
                    #bimEl['Square'] = Square
                    rooms.append(bimEl)
                    roomsOutput[bimEl['Id']] = bimEl['Output']
                    roomsData.append(bimEl)
                    
                if (bimEl['Sign'] == 'DoorWayOut' or bimEl['Sign'] == 'DoorWayInt' or bimEl['Sign'] == 'DoorWay'):
                    if len(bimEl['Output']) < 2: 
                        doorsToStreet.append(bimEl['Id'])
                        bimEl['Output'].append('0000')
                        roomsOutput['0000'] = doorsToStreet
                    doorsOutput[bimEl['Id']] = bimEl['Output']
                    doors.append(bimEl)
        roomsCount = roomsCount + len(rooms)
        doorsCount = doorsCount + len(doors)
        
        #pprint(f'roomsOutput {len(roomsOutput)}')
        inc = bondGraph(roomsOutput, doorsOutput)
        visited = set()  # Посещена ли вершина?
        Q = []  # Очередь
        BFS = []
        level = {el: 0 for el in inc}
        start = '0000'
        #pprint(inc)
        #pprint(f'inc {len(inc)}')
        bfs(start, inc, visited, Q, BFS, level)
        deph = []
        width = []
        for j in level: deph.append(level[j])
        widthCount = widthCount + max(Counter(deph).values())
        depthCount = depthCount + max(deph)
        #pprint(f'level {max(deph)}')
        #pprint(f'width {max(Counter(deph).values())}')4
        H.append([len(rooms), len(doors), max(Counter(deph).values()), max(deph)])
        if i == len(pathJson) - 1: P = [roomsCount/len(pathJson), doorsCount/len(pathJson), widthCount/len(pathJson), depthCount/len(pathJson)]
        ##print(f' doorCount {len(doors)}')
        ##print(f' roomCount {len(rooms)}')
        #print(dfs(start, inc))
        tk = []
        sumLenhth = []
        Square = []
        path = []
        #dfs(start, inc, tk, sumLenhth, Square,  visited = None)
        intruder(start, inc, path, visited=None)
        pprint(f'path {path}')
        print(sum(tk))
        print(f'summLength {sum(sumLenhth)}')
        print(f'Square {sum(Square)}')
    pprint(H)
    for i,elemI in enumerate(H):
        H1.append([])
        for j, elemJ in enumerate(elemI):
            H1[i].append(H[i][j]/P[j])

    #ВЫчисление S0
    for i, elemI in enumerate(H1):
        S0.append(0.5 * (H1[i][0] * H1[i][1] + H1[i][1] * H1[i][2] + H1[i][2] * H1[i][3] + H1[i][3] * H1[i][0]))

    #S1
    for i, elemI in enumerate(H):
        S1.append(0.5 * (H[i][0] * H[i][1] + H[i][1] * H[i][2] + H[i][2] * H[i][3] + H[i][3] * H[i][0]))

    #Сложность 
    for i, elemI in enumerate(S0):
        U.append(S0[i]*0.5)

    pprint(H1)
    pprint(P)
    pprint(S0)
    pprint(U)
    

# Поиск в ширину - ПВШ (Breadth First Search - BFS)
#поиск уровня вершины
def bfs(v, inc, visited, Q, BFS, level):
    if v in visited:  # Если вершина уже посещена, выходим
        return
    visited.add(v)  # Посетили вершину v
    BFS.append(v)  # Запоминаем порядок обхода
    # print("v = %d" % v)
    for i in inc[v]:  # Все смежные с v вершины
        if not i in visited:
            Q.append(i)
            level[i] = level[v] + 1
    
    while Q:
        bfs(Q.pop(0), inc, visited, Q, BFS, level)

def intruder(v, inc, path, visited=None, stack = None, zoneBack = None):
    if visited is None:
        visited = set()
    if stack is None:
        stack = []
    if zoneBack is None:
        zoneBack = 0
    if v in visited:  # Если вершина уже посещена, выходим
        return
    if v in stack:
        return

    neighbour = []

    #neighbourCounter = Counter(path)
    #for el in neighbourCounter:
    #    if neighbourCounter[el] >= 3:
    #        return

    visited.add(v)
    path.append(v)
    stack.append(v)
    for vertex in inc[v]:
        if (vertex in stack):
            neighbour.append(vertex)

    if (len(neighbour) == len(inc[v])):
        #visited.remove(path[-1])
        zoneBack = zoneBack + 1
        stack.pop(-zoneBack)
        print('ss')
        intruder(path[-zoneBack], inc, path, visited, stack, zoneBack)
    
    #if (len(inc[v]) <= 1):
    #    visited.remove(path[-2])
    #    intruder(stack.pop(), inc, path, visited, stack, zoneBack = 0)
    
    
    numPeople = []
    for i in inc[v]:
        if not i in stack:
            intruder(i, inc, path, visited, stack)
    


#поик в глубину
# Поиск в глубину - ПВГ (Depth First Search - DFS)
# Путь нарушителя
def dfs(v, inc, tk, sumLenhth, Square, visited=None):

    if visited is None:
        visited = set()
    if v in visited:  # Если вершина уже посещена, выходим
        return
    #print(visited)
    visited.add(v)  # Посетили вершину v
    numPeople = []
    for i in inc[v]:  # Все смежные с v вершины

        for room in roomsData:
            if room['Id'] == v:
                numPeople.append(room['NumPeople'])

        
        if not i in visited:
            for room in roomsData:
                if room['Id'] == v:
                    tk.append(math.sqrt(room['Square'])/100 + 0.3)
                    sumLenhth.append(math.sqrt(room['Square']))
                    Square.append(room['Square'])
            dfs(i, inc, tk, sumLenhth, Square, visited)
            


#start = 1
#dfs(start)  # start - начальная вершина обхода



#Свзяывает помещения между собой
def bondGraph(roomsOutput, doorsOutput):
    bondRooms = {}
    for room in roomsOutput:
        bondRooms[room] = []
        for idDoor in roomsOutput[room]:
            if room in doorsOutput[idDoor]:
                bondRooms[room].append(doorsOutput[idDoor][doorsOutput[idDoor].index(room) - 1])
                #G.add_edge(room,doorsOutput[idDoor][doorsOutput[idDoor].index(room) - 1])

    #print(bondRooms)
    return bondRooms




#def unionObj(rooms, doors):
#    for room in rooms:
#        for door in doors:




getObjectCount()
