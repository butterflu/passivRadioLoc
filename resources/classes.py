import numpy , time, random
from shapely import geometry
import matplotlib.pyplot as pyplot
from descartes import PolygonPatch
# from .globalconfig import *

#global variables
frequency=7000000000 #7GHz
power_threshold=0 #dbm
wall_loss=20
ray_list = []
angle_err = 2
random.seed(time.time())


class MainObject():
    def __init__(self, position=[0, 0]):
        self.position=position
        self.radius=4

    def move(self, x, y):
        self.position[0]+=x
        self.position[1]+=y
    def getPosition(self):
        return self.position

    def getShape(self):
        return geometry.Point(self.position[:]).buffer(self.radius)

    def plot(self, ax):
        patch = PolygonPatch(self.getShape())
        ax.add_patch(patch)

class Wall():
    def __init__(self, position, size):
        self.position=position
        self.size=size
        self.corner_ul = [position[0]-size[0]/2, position[1]+size[1]/2]
        self.corner_ur = [position[0]+size[0]/2, position[1]+size[1]/2]
        self.corner_ll = [position[0]-size[0]/2, position[1]-size[1]/2]
        self.corner_lr = [position[0]+size[0]/2, position[1]-size[1]/2]
        self.corners=[self.corner_ul,self.corner_ur,self.corner_lr,self.corner_ll]


    def check_line_collision(self, point1, point2):
        for point3 in self.corners:
            point4 = self.corners[self.corners.index(point3)-1]
            denominator=((point2[0]-point1[0])*(point4[1]-point3[1])) - ((point2[1]-point1[1])*point4[0]-point3[0])
            num1=((point1[1]-point3[1])*(point4[0]-point3[0])) - ((point1[0]-point3[0])*(point4[1]-point3[1]))
            num2=((point1[1]-point3[1])*(point2[0]-point1[0])) - ((point1[0]-point3[0])*(point2[1]-point1[1]))

            if (denominator == 0):
                return num1 == 0 and num2 == 0

            r=num1 / denominator
            s=num2 / denominator

            return (r >= 0 and r <= 1) and (s >= 0 and s <= 1)
    
    def getLineStringonPoint(self, point: geometry.Point):
        points = list(self.getShape().coords)
        for x in range(len(points)):
            if geometry.LineString([points[x-1],points[x]]).contains(point):
                return geometry.LineString([points[x-1],points[x]])
        print("error point not on line")


    def getShape(self):
        return geometry.LinearRing(self.corners[:])

    def plot(self, ax):
        x,y = self.getShape().xy
        ax.plot(x,y)

class Node():
    def __init__(self, position, tx_power):
        self.position=position
        self.tx_power=tx_power
        self.ray_list=[]

    def createRayTrace(self, angle):
        return RayTrace(self.position, self.tx_power, angle, self) #test of self reference

    def getShape(self):
        return geometry.Point(self.position[:]).buffer(5)

    def plot(self, ax):
        patch = PolygonPatch(self.getShape())
        ax.add_patch(patch)
    
    def reciveRay(self, rayT):
        vector = [rayT.position_list[-1][x]-rayT.position_list[-2][x] for x in range(2)]
        angle = (numpy.arctan2(vector[0],vector[1])*180/numpy.pi)+90
        print(rayT.start_node, rayT.end_node)
        self.ray_list.append(RecivedRay(self.position, rayT.power, -angle , rayT.end_node, rayT.start_node))

    def retraceAllRecievedRays(self):
        self.retraced_rays = [ray.traceBack() for ray in self.ray_list]

    def plotRecivedRays(self, ax):
        for ray in self.retraced_rays:
            ray.plot(ax)

    def traceBack(self, angle_list, end_node):
        for angle in angle_list:
            rayT = RayTrace(self.position, self.tx_power, angle, self)
            traceToEnd(rayT, map, MO)
            print(rayT.end_node, end_node)
                # if end_node == rayT.end_node:
            return rayT
    
    def sendRays(self, angle_list=[0,360]):
        for angle in [x for x in range(angle_list[0],angle_list[1]*1)]:
            rayT = RayTrace(self.position, self.tx_power, angle, self)
            if traceToEnd(rayT, map, MO):      #mainObj
                ray_list.append(rayT)

class RayTrace():
    def __init__(self, position, power, angle: float, start_node):
        self.power=power
        self.setVector(angle, position)
        self.position_list=[position]
        self.start_node=start_node
        self.end_node=None
        self.reflection_count=0

    def setEndNode(self,end_node: Node):
        self.end_node=end_node
        self.vector = None
        self.position_list.append(end_node.position)
        self.end_node.reciveRay(self)

    def setVector(self,angle,position):
        self.vector=[numpy.cos(angle/180*numpy.pi)*100000+position[0], numpy.sin(angle/180*numpy.pi)*100000+position[1]]      #relative endpoint
        # print(self.vector)
    
    def getShape(self):
        if self.end_node==None:
            return geometry.LineString([*self.position_list,self.vector])
        return geometry.LineString(self.position_list)
    
    def getCurrPoint(self):
        return geometry.Point(*self.position_list[-1])

    def plot(self, ax):
        x,y = self.getShape().xy
        ax.plot(x,y)

    def applyLoss(self, loss):
        self.power-=loss

    def distanceLoss(self,distance):
        loss=4*numpy.pi*distance/100*frequency/300000000
        self.applyLoss(loss)
        if self.power <= power_threshold:
            return False
        return True

    def reflect(self, new_pos, new_angle, loss):
        self.applyLoss(loss)
        if self.power <= power_threshold or self.reflection_count > 2:
            return False
        self.position_list.append(list(*new_pos.coords))
        self.setVector(new_angle, list(*new_pos.coords))
        self.reflection_count+=1
        return True

class RecivedRay(RayTrace):
    def __init__(self, position, power, angle, start_node, end_node):
        self.end_node=end_node
        self.angle=angle
        super().__init__(position, power, angle, start_node)

    def traceBack(self):
        # print(self.angle)
        return self.start_node.traceBack([x*0.1 for x in numpy.arange(self.angle-angle_err,self.angle+angle_err)], self.end_node)
            

class Map():
    def __init__(self,width,height):
        self.height = height
        self.width = width
        self.objectList=[self]
        self.node_list=[]

    def addObject(self, obj):
        self.objectList.append(obj)
    
    def addNode(self, obj):
        self.objectList.append(obj)
        self.node_list.append(obj)

    def getShape(self):
        return geometry.LinearRing([[0,0],[0, self.height],[self.width, self.height],[self.width, 0]])

    def getObjectsShape(self):  #not used currently
        shapes = [self.getShape()]
        for obj in self.objectList:
            shapes.append(obj.getShape)
        return shapes

    def plot(self, ax):
        x,y = self.getShape().xy
        ax.plot(x,y)
        for object in self.objectList[1:]:
            object.plot(ax)

    def getLineStringonPoint(self, point: geometry.Point):
        points = list(self.getShape().coords)
        for x in range(len(points)):
            if geometry.LineString([points[x-1],points[x]]).contains(point):
                return geometry.LineString([points[x-1],points[x]])
        print("error point not on line")

    

#functions
def readmapfromfile(filename):
    f = open(filename, "r")
    try:
            map = Map(int(f.readline().strip()), int(f.readline().strip()))
            line=f.readline()
            while line!="":
                if line[0] == '#':
                    line=f.readline()
                    continue
                if line.strip() == "wall":
                    map.addObject(Wall([int(f.readline().strip()), int(f.readline().strip())],[int(f.readline().strip()), int(f.readline().strip())]))
                    line=f.readline()
                    continue
                if line.strip() == "node":
                    map.addNode(Node([int(f.readline().strip()), int(f.readline().strip())],700))      #txpower

                    line=f.readline()
                    continue
    except FileNotFoundError:
        print("Error during map setup")
        exit(-1)

    return map

def getClosestPoint(point1, point_list):
    if type(point_list) == geometry.Point:
        return point_list
    else:
        dist = [[x, x.distance(point1)] for x in point_list if x.distance(point1)>0.01]
        dist.sort(key=lambda x: x[1])
        return dist[0][0]


def getReflectionAngle(line1: geometry.LineString, line2: geometry.LineString):
    line2_uvector = [list(line2.coords)[1][x]-list(line2.coords)[0][x] for x in range(2)]
    angle2 = ((numpy.arctan2(line2_uvector[1],line2_uvector[0])*180/numpy.pi)+360)%180
    # print("angle2:",angle2)
    line1_uvector = [list(line1.coords)[1][x]-list(line1.coords)[0][x] for x in range(2)]
    angle1 = ((numpy.arctan2(line1_uvector[1],line1_uvector[0])*180/numpy.pi)+360)%360
    # print("angle1:",angle1)
    a=(angle1-angle2+360)%360
    return (2*angle2-angle1)%360
    if a>=angle2 and a<angle2+90:
        return (2*angle2-angle1)%360
    elif a>=angle2+90 and a<angle2+180:
        return (angle2-angle1)%360
    elif a>=angle2+180 and a<angle2+270:
        return (3*angle2+180-angle1)%360
    elif (a>=(angle2+270)%360 and a<angle2%360) or (a>=angle2+270 and a<angle2):
        return (3*angle2 - angle1)%360
    else:
        print("angle_error", a, angle2)


def rayTracing(rayT: RayTrace, map: Map, Mob: MainObject):
    rayShape = rayT.getShape()
    distance = 0
    for obj in [ob for ob in map.objectList if ob is not rayT.start_node]:
        objShape = obj.getShape()
        if rayShape.crosses(objShape):
            inter = rayShape.intersection(objShape)
            dist2 = rayT.getCurrPoint().distance(inter)
            if distance == 0 or dist2 < distance:
                distance=dist2
                reflectionObject = obj
                reflectionPoint=inter
    
    if rayT.distanceLoss(distance):
        if type(reflectionObject)==Node:        #check if node and if startnode
            if not rayT.start_node == reflectionObject:
                rayT.setEndNode(reflectionObject)
                return "end"
            else:
                return "loss"
        else:
            new_point = getClosestPoint(geometry.Point(rayT.position_list[-1]),reflectionPoint)
            new_angle = getReflectionAngle(geometry.LineString([rayT.position_list[-1],new_point]), reflectionObject.getLineStringonPoint(new_point))
            # print(new_angle, new_point)
            if rayT.reflect(new_point,new_angle,wall_loss):     #loss from material
                return "ref"
            else:
                return "ref_count"
    else:
        return "loss"

def traceToEnd(rayT: RayTrace, map: Map, Mob: MainObject):
    while True:
        state = rayTracing(rayT, map, MainObject)
        if state == "ref":
            continue
        elif state == "end":
            return True
        else:
            return False
    





# def generateHeatmap(map: Map):
#     heatmap=[[0 for col in range(map.width)] for row in range(map.height)]
    
    #for each point on map draw mainObcject and check if it intersects with all the rays + exclude impossible locations


if __name__ == '__main__':
    fig , (ax , ax2) = pyplot.subplots(1, 2)
    pyplot.xlim([-1,300])
    pyplot.ylim([-1,301])
    MO = MainObject([200,200])
    map=readmapfromfile("C:\\Users\\benia\\Desktop\\programy\\programowanie\\RadioLoc\passivRadioLoc\\resources\\mapSettings.txt")
    map.plot(ax)
    map.objectList[2].sendRays()
    
    for el in ray_list:
        el.plot(ax)

    map.plot(ax2)
    map.node_list[1].retraceAllRecievedRays()
    # print( map.node_list[1].ray_list[:].end_node)
    map.node_list[1].plotRecivedRays(ax2)
    
    pyplot.show()

    