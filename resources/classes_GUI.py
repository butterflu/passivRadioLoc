import enum
from re import M
from typing import List
import numpy, time, random
from shapely import geometry
import matplotlib.pyplot as pyplot
from descartes import PolygonPatch
import csv
import os

# global variables
frequency = 7000000000  # 7GHz
power_threshold = 0  # dbm
wall_loss = 20
ray_list = []
angle_err = 2
random.seed(time.time())


class MainObject():
    def __init__(self, position=[0, 0]):
        self.position = position
        self.radius = 4

    def move(self, x, y):
        self.position[0] += x
        self.position[1] += y

    def getPosition(self):
        return self.position

    def getShape(self):
        return geometry.Point(self.position).buffer(self.radius)

    def plot(self, ax):
        patch = PolygonPatch(self.getShape())
        ax.add_patch(patch)


class Wall():
    def __init__(self, position, size):
        self.position = position
        self.size = size
        self.corner_ul = [position[0] - size[0] / 2, position[1] + size[1] / 2]
        self.corner_ur = [position[0] + size[0] / 2, position[1] + size[1] / 2]
        self.corner_ll = [position[0] - size[0] / 2, position[1] - size[1] / 2]
        self.corner_lr = [position[0] + size[0] / 2, position[1] - size[1] / 2]
        self.corners = [self.corner_ul, self.corner_ur, self.corner_lr, self.corner_ll]

    def check_line_collision(self, point1, point2):
        for point3 in self.corners:
            point4 = self.corners[self.corners.index(point3) - 1]
            denominator = ((point2[0] - point1[0]) * (point4[1] - point3[1])) - (
                        (point2[1] - point1[1]) * point4[0] - point3[0])
            num1 = ((point1[1] - point3[1]) * (point4[0] - point3[0])) - (
                        (point1[0] - point3[0]) * (point4[1] - point3[1]))
            num2 = ((point1[1] - point3[1]) * (point2[0] - point1[0])) - (
                        (point1[0] - point3[0]) * (point2[1] - point1[1]))

            if (denominator == 0):
                return num1 == 0 and num2 == 0

            r = num1 / denominator
            s = num2 / denominator

            return (r >= 0 and r <= 1) and (s >= 0 and s <= 1)

    def getLineStringonPoint(self, point: geometry.Point):
        points = list(self.getShape().coords)
        for x in range(len(points)):
            if geometry.LineString([points[x - 1], points[x]]).contains(point):
                return geometry.LineString([points[x - 1], points[x]])
        print("error point not on line")

    def getShape(self):
        return geometry.LinearRing(self.corners[:])

    def plot(self, ax):
        x, y = self.getShape().xy
        ax.plot(x, y)


class Node():
    def __init__(self, position, tx_power):
        self.position = position
        self.tx_power = tx_power
        self.ray_list = []
        self.retraced_rays = []
        self.reference_rays = []
        self.ref_ray_list = []
        self.missing_rays = []

    def createRayTrace(self, angle):
        return RayTrace(self.position, self.tx_power, angle, self)  # test of self reference

    def getShape(self):
        return geometry.Point(self.position[:]).buffer(5)

    def plot(self, ax):
        patch = PolygonPatch(self.getShape())
        ax.add_patch(patch)

    def addReferenceRay(self, rayT):
        self.reference_rays.append(rayT)

    def recieveRays(self):
        self.ray_list = []
        for rayT in self.reference_rays:
            applyObjectLoss(MO, rayT)
            if rayT.power == 0:
                continue
            angle = (rayT.getAngle() + random.normalvariate(0, 1)) % 360
            self.ray_list.append(
                RecivedRay(self.position, rayT.power + random.normalvariate(0, 1), angle, rayT.end_node,
                           rayT.start_node))

    def recieveRefRays(self):  # do once
        for rayT in self.reference_rays:
            angle = (rayT.getAngle() + random.normalvariate(0, 1)) % 360  # losowa pomyłka
            self.ref_ray_list.append(
                RecivedRay(self.position, rayT.power + random.normalvariate(0, 1), angle, rayT.end_node,
                           rayT.start_node))

    def findMissingRays(self):
        missing_ref_rays = []
        for refRay in self.ref_ray_list:
            if checkifrayinlist(refRay, self.ray_list):
                continue
            missing_ref_rays.append(refRay)
        if len(missing_ref_rays) > 0:
            missing_rays = []
            for rayT in missing_ref_rays:
                angle = (rayT.getAngle() + random.normalvariate(0, 1)) % 360
                missing_rays.append(
                    RecivedRay(self.position, rayT.power + random.normalvariate(0, 1), angle, rayT.end_node,
                               rayT.start_node))
            for ray in missing_rays:
                rayt = ray.traceBack()
                if rayt is not None:
                    self.missing_rays.append(rayt)

    def retraceAllRecievedRays(self):
        for ray in self.ray_list:
            rayt = ray.traceBack()
            if rayt is not None:
                self.retraced_rays.append(rayt)

    def plotRecivedRays(self, ax):
        if not hasattr(self, 'retraced_rays'):
            return
        for ray in self.retraced_rays:
            ray.plot(ax)

    def traceBack(self, angle_list, end_node):
        global map, MO
        for angle in angle_list:
            rayT = RayTrace(self.position, self.tx_power, angle, self)
            if traceToEnd(rayT, map):
                if end_node is rayT.end_node:
                    return rayT

    def sendRays(self, angle_list=[0, 360]):
        for angle in [x for x in numpy.arange(angle_list[0], angle_list[1], 1)]:  # dokładność wysyłania prmieni
            rayT = RayTrace(self.position, self.tx_power, angle, self)
            if traceToEnd(rayT, map):  # mainObj
                ray_list.append(rayT)
                rayT.end_node.addReferenceRay(rayT)

    def once(self):
        self.recieveRefRays()

    def repeat(self):
        self.recieveRays()
        self.findMissingRays()
        self.retraceAllRecievedRays()


class RayTrace():
    def __init__(self, position, power, angle: float, start_node):
        self.power = power
        self.setVector(angle, position)
        self.position_list = [position]
        self.start_node = start_node
        self.end_node = None
        self.reflection_count = 0

    def setEndNode(self, end_node: Node):
        self.end_node = end_node
        self.vector = None
        self.position_list.append(end_node.position)

    def getAngle(self):
        if len(self.position_list) >= 2:
            line = geometry.LineString([self.position_list[-2], self.position_list[-1]])
        else:
            line = geometry.LineString([self.position_list[0], self.vector])
        uvector = [list(line.coords)[1][x] - list(line.coords)[0][x] for x in range(2)]
        return ((numpy.arctan2(uvector[1], uvector[0]) * 180 / numpy.pi) + 360) % 180

    def setVector(self, angle, position):
        self.vector = [numpy.cos(angle / 180 * numpy.pi) * 100000 + position[0],
                       numpy.sin(angle / 180 * numpy.pi) * 100000 + position[1]]  # relative endpoint

    def getShape(self):
        if self.end_node == None:
            return geometry.LineString([*self.position_list, self.vector])
        return geometry.LineString(self.position_list)

    def getCurrPoint(self):
        return geometry.Point(*self.position_list[-1])

    def plot(self, ax):
        x, y = self.getShape().xy
        ax.plot(x, y)

    def applyLoss(self, loss):
        self.power -= loss

    def distanceLoss(self, distance):
        loss = 4 * numpy.pi * distance / 100 * frequency / 300000000
        self.applyLoss(loss)
        if self.power <= power_threshold:
            return False
        return True

    def reflect(self, new_pos, new_angle, loss):
        self.applyLoss(loss)
        if self.power <= power_threshold or self.reflection_count > 1:
            return False
        self.position_list.append(list(*new_pos.coords))
        self.setVector(new_angle, list(*new_pos.coords))
        self.reflection_count += 1
        return True


class RecivedRay(RayTrace):
    def __init__(self, position, power, angle, start_node, end_node):
        super().__init__(position, power, angle, start_node)
        self.end_node = end_node
        self.angle = angle

    def traceBack(self):
        return self.start_node.traceBack(numpy.arange(self.angle - angle_err, self.angle + angle_err, 0.05),
                                         self.end_node)  # accuracy


class Map():
    def __init__(self, width, height):
        self.height = height
        self.width = width
        self.objectList = [self]
        self.node_list = []

    def addObject(self, obj):
        self.objectList.append(obj)

    def addNode(self, obj):
        self.objectList.append(obj)
        self.node_list.append(obj)

    def getShape(self):
        return geometry.LinearRing([[0, 0], [0, self.height], [self.width, self.height], [self.width, 0]])

    def getObjectsShape(self):  # not used currently
        shapes = [self.getShape()]
        for obj in self.objectList:
            shapes.append(obj.getShape)
        return shapes

    def plot(self, ax):
        x, y = self.getShape().xy
        ax.plot(x, y)
        for object in self.objectList[1:]:
            object.plot(ax)

    def getLineStringonPoint(self, point: geometry.Point):
        points = list(self.getShape().coords)
        for x in range(len(points)):
            if geometry.LineString([points[x - 1], points[x]]).contains(point):
                return geometry.LineString([points[x - 1], points[x]])
            elif geometry.LineString([points[x - 1], points[x]]).intersects(point):
                return None
        print("error point not on line")

    def getAllMissingRays(self):
        missing_ray_list = []
        for node in self.node_list:
            if len(node.missing_rays) > 0:
                missing_ray_list.extend(node.missing_rays)
        return missing_ray_list

    def plotMissingRays(self, ax):
        if len(self.getAllMissingRays()) == 0:
            return
        for ray in self.getAllMissingRays():
            ray.plot(ax)

    def retraceAllNodes(self):
        for node in self.node_list:
            node.recieveRays()
            node.retraceAllRecievedRays()

    def sendAllRays(self):
        for node in self.node_list:
            node.sendRays()

    def plotRetracedRays(self, ax):
        for node in self.node_list:
            node.plotRecivedRays(ax)

    def once(self):
        self.sendAllRays()
        for node in self.node_list:
            node.once()

    def repeat(self):
        for node in self.node_list:
            node.repeat()


# functions
def checkifrayinlist(ray: RayTrace, list: List):
    for refRay in list:
        ref_angle = refRay.getAngle()
        angle = ray.getAngle()
        if refRay.power > ray.power - 4 and refRay.power < ray.power + 4 and ref_angle > angle - 4 and ref_angle < angle + 4:
            return True
    return False


def readmapfromfile(filename):
    f = open(filename, "r")
    try:
        map = Map(int(f.readline().strip()), int(f.readline().strip()))
        line = f.readline()
        while line != "":
            if line[0] == '#':
                line = f.readline()
                continue
            if line.strip() == "wall":
                map.addObject(Wall([int(f.readline().strip()), int(f.readline().strip())],
                                   [int(f.readline().strip()), int(f.readline().strip())]))
                line = f.readline()
                continue
            if line.strip() == "node":
                map.addNode(Node([int(f.readline().strip()), int(f.readline().strip())], 700))  # txpower

                line = f.readline()
                continue
    except FileNotFoundError:
        print("Error during map setup")
        exit(-1)

    return map


def getClosestPoint(point1, point_list):
    if type(point_list) == geometry.Point:
        return point_list
    else:
        dist = [[x, x.distance(point1)] for x in point_list if x.distance(point1) > 0.01]
        dist.sort(key=lambda x: x[1])
        return dist[0][0]


def getReflectionAngle(line1: geometry.LineString, line2: geometry.LineString):
    line2_uvector = [list(line2.coords)[1][x] - list(line2.coords)[0][x] for x in range(2)]
    angle2 = ((numpy.arctan2(line2_uvector[1], line2_uvector[0]) * 180 / numpy.pi) + 360) % 180
    line1_uvector = [list(line1.coords)[1][x] - list(line1.coords)[0][x] for x in range(2)]

    if angle2 == 0:
        vector = [line1_uvector[0] - list(line2.coords)[0][0], line1_uvector[1] - list(line2.coords)[0][1]]
        vector[1] = -vector[1]
        return ((numpy.arctan2(vector[1], vector[0]) * 180 / numpy.pi) + 360) % 360
    elif angle2 == 90:
        vector = [line1_uvector[0] - list(line2.coords)[0][0], line1_uvector[1] - list(line2.coords)[0][1]]
        vector[0] = -vector[0]
        return ((numpy.arctan2(vector[1], vector[0]) * 180 / numpy.pi) + 360) % 360


def rayTracing(rayT: RayTrace, map: Map):
    rayShape = rayT.getShape()
    distance = 0
    for obj in [ob for ob in map.objectList if ob is not rayT.start_node]:
        objShape = obj.getShape()
        if rayShape.crosses(objShape):
            inter = rayShape.intersection(objShape)
            dist2 = rayT.getCurrPoint().distance(inter)
            if distance == 0 or dist2 < distance:
                distance = dist2
                reflectionObject = obj
                reflectionPoint = inter
    if rayT.distanceLoss(distance):
        if type(reflectionObject) == Node:  # check if node and if startnode
            if not rayT.start_node == reflectionObject:
                rayT.setEndNode(reflectionObject)
                return "end"
            else:
                return "loss"
        else:
            new_point = getClosestPoint(geometry.Point(rayT.position_list[-1]), reflectionPoint)
            try:
                new_angle = getReflectionAngle(geometry.LineString([rayT.position_list[-1], rayT.vector]),
                                               reflectionObject.getLineStringonPoint(new_point))
            except:
                return "corner"
            if rayT.reflect(new_point, new_angle, wall_loss):  # loss from material
                return "ref"
            else:
                return "ref_count"
    else:
        return "loss"


def traceToEnd(rayT: RayTrace, map: Map):
    while True:
        state = rayTracing(rayT, map)
        if state == "ref":
            continue
        elif state == "end":
            return True
        else:
            return False


def applyObjectLoss(main_obj: MainObject, ray: RayTrace):
    if ray.getShape().intersects(main_obj.getShape()):
        ray.power = 0


def checkIfObjectIntersects(main_obj: geometry.Point, list: List):
    mo_shape = main_obj.buffer(MO.radius)
    for element in list:
        if mo_shape.intersects(element.getShape()):
            return True
    return False


def generateHeatmap(map: Map):
    heatmap = numpy.zeros((int(map.width / 5), int(map.height / 5)))

    for row in range(map.width):
        for cell in range(map.height):
            object = geometry.Point([row, cell])
            if checkIfObjectIntersects(object, map.getAllMissingRays()) and not checkIfObjectIntersects(object,
                                                                                                        map.objectList):
                heatmap[int((row - row % 5) / 5)][int((cell - cell % 5) / 5)] += 1

    return heatmap


def displayHeatMap(heatMap, estimatedPos, i):
    # dorzucić jakby okręgi przewidywania od tego miejsca i cacy
    heatMap[estimatedPos[0], estimatedPos[1]] += 50
    heatMap = numpy.rot90(heatMap, k=1)
    pyplot.figure(2)
    pyplot.axis('off')
    pyplot.title("Room heatmap")
    pyplot.imshow(heatMap, cmap='viridis')
    pyplot.colorbar()
    pyplot.show()
    string = 'heatmap' + str(i) + '.png'
    pyplot.imsave(string, heatMap)


def room_update():
    pass


def log(file, data):
    with open(file, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data)


if __name__ == '__main__':
    import main_script.room_1

    fig, (ax, ax2) = pyplot.subplots(1, 2)
    ax.set_xlim([-1, 300])
    ax.set_ylim([-1, 301])
    ax2.set_xlim([-1, 300])
    ax2.set_ylim([-1, 301])
    MO = MainObject([130, 256])
    map = readmapfromfile("C:\\Users\\marcin\\Desktop\\ES\\passivRadioLoc\\resources\\mapSettings.txt")
    map.plot(ax)
    map.once()
    for el in ray_list:
        el.plot(ax)
    # Main loop
    i = 1
    while True:
        # draw MO
        MO.plot(ax)
        MO.plot(ax2)
        map.plot(ax2)
        map.repeat()  # Tracing - obliczenia
        map.plotRetracedRays(ax2)
        map.plotMissingRays(ax2)
        heatmap = generateHeatmap(map)
        x, y = numpy.where(heatmap == numpy.max(heatmap))
        print("Estymacja")
        print("x= " + str(numpy.mean(x) * 5))
        print("y= " + str(numpy.mean(y) * 5))
        print("Rzeczywista pozycja")
        print(MO.getPosition())
        estimatedPos = [round(numpy.mean(x)), round(numpy.mean(y))]
        displayHeatMap(heatmap, estimatedPos, i)
        log('estymacja.csv', [numpy.mean(x), numpy.mean(y)])
        log('real.csv', MO.getPosition())
        pyplot.show()
        fig.canvas.draw()
        MO.move(-50, -50)
        i += 1
        if i == 4:
            break