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