import numpy

class MainObject():
    def __init__(self, position=[0, 0]):
        self.position=position
        self.radius=4

    def move(sel, x, y):
        self.position[0]+=x
        self.position[1]+=y
    def getPosition(self):
        return self.position

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
                return num1 == 0 and num == 0

            r=num1 / denominator
            s=num2 / denominator

            return (r >= 0 and r <= 1) and (s >= 0 and s <= 1)

class Node():
    def __init__(self, position, tx_power):
        self.position=position
        self.tx_power=tx_power

    def createRay(self, vector):
        return Ray(self.position, self.tx_power, vector)

    def createRayTrace(self, vector):
        return RayTrace(self.position, self.tx_power, vector, self) #test of self reference


class Ray():
    def __init__(self,position, power, vector):
        self.power=power
        self.vector=vector
        self.reflection_count=0
        self.position=position

    def applyLoss(self, loss):
        self.power-=loss

    def distanceLoss(self,distance):
        loss=4*numpy.pi*distance*frequency/300000000
        applyLoss(loss)
        if self.power <= power_threshold:
            return False
        return True

    def reflect(self, new_pos, new_vec, loss):
        applyLoss(loss)
        if self.power <= power_threshold or self.reflection_count == 2:
            return False
        self.position = new_pos
        self.vector = new_vec
        return True

class RayTrace(Ray):
    def __init__(self, position, power, vector, start_node):
        super().__init__(position, power, vector)
        self.position_list=[self.position]
        self.start_node=start_node
        self.end_node=None

    def setEndNode(self,end_node):
        self.end_node=end_node

class Map():
    def __init__(self,height,width):
        self.height = height
        self.width = width
        self.objectList=[]

    def addObject(self, obj):
        self.objectList.append(obj)





def readmapfromfile(filename):
    f = open(filename, "r")
    try:
            map = Map(int(f.readline().strip()), int(f.readline().strip()))
            line=f.readline()
            while line!="":
                if line[0] == '#':
                    line=f.readline()
                    continue
                if line == "wall":
                    map.addObject(Wall([int(f.readline().strip()), int(f.readline().strip())],[int(f.readline().strip()), int(f.readline().strip())]))
                    continue
    except any:
        print("Error during map setup")
        exit(-1)
