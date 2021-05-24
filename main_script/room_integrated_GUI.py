import pygame
from resources import classes_GUI
import sys

# Initialing Color
black = (0, 0, 0)
white = (255, 255, 255)
gray = (96, 96, 96)
green = (0, 128, 0)
blue = (0, 0, 205)
gold = (255, 215, 0)
red = (255, 0, 0)
scale = 2

class GUI:
    def __init__(self, map):
        self.can_move = True
        self.map = map
        pygame.init()
        # Initializing surface
        self.surface_size = (scale*self.map.width, scale*self.map.height)
        self.surface = pygame.display.set_mode(self.surface_size)
        pygame.display.set_caption("Trace room")
        self.surface.fill(white)
        self.clock = pygame.time.Clock()
        self.fps = 20
        self.prevPos = (scale*200, scale*200)
        self.currentPos = (200, 200)
        self.forbid_move = False

        # draw map on surface based on mapSettings.txt
        self.wall_list = []
        self.node_list = []
        for object in self.map.objectList:
            # print(type(object))
            # if isinstance(object, classes_GUI.Wall):
            if type(object).__name__ == "Wall":
                self.wall = pygame.draw.rect(self.surface, gray, pygame.Rect(int(scale * object.position[0]),
                                                                   int(self.surface_size[1] - scale * object.position[1]),
                                                                   int(scale * object.size[0]),
                                                                   int(scale * (-object.size[1]))))
                self.wall_list.append(self.wall)
            #if isinstance(object, classes_GUI.Node):
            if type(object).__name__ == "Node":
                self.node = pygame.draw.rect(self.surface, gold, pygame.Rect(int(scale * object.position[0]),
                                                                   int(self.surface_size[1] - scale * object.position[1]),
                                                                   scale * 10, scale * 10))
                self.node_list.append(self.node)

    def main_loop(self):
        self.can_move = True
        while self.can_move:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.terminate()
                if event.type == pygame.KEYDOWN and pygame.K_n:
                    self.can_move = False
            if self.prevPos:
                pygame.draw.rect(self.surface, white, pygame.Rect(self.prevPos[0], self.prevPos[1], scale*10, scale*10))

            circle = pygame.Rect(self.getPos()[0], self.getPos()[1], scale*10, scale*10)
            self.checkCollisions(circle, self.wall_list)
            self.checkCollisions(circle, self.node_list)

            if not self.forbid_move:
                circle = pygame.draw.rect(self.surface, blue, pygame.Rect(self.getPos()[0], self.getPos()[1], scale*10, scale*10))
                self.prevPos = (self.getPos()[0], self.getPos()[1])
            else:
                circle = pygame.draw.rect(self.surface, blue, pygame.Rect(self.prevPos[0], self.prevPos[1], scale*10, scale*10))

            self.currentPos = (self.prevPos[0]/scale, (self.surface_size[1] - self.prevPos[1]) / scale)
            print(self.currentPos)
            self.forbid_move = False
            pygame.display.flip()
            pygame.image.save(self.surface, '../results/surface.png')    # wstępnie można będie heatMapę na tej podstawie zrobić

            self.clock.tick(self.fps)

    def terminate(self):
        pygame.quit()
        sys.exit()

    def getPos(self):
        pos = pygame.mouse.get_pos()
        return pos

    def checkCollisions(self, human_pos, walls):
        for wall in walls:
            if pygame.Rect.colliderect(wall, human_pos):
                self.forbid_move = True
                break
        for node in self.node_list:
            if pygame.Rect.colliderect(node, human_pos):
                self.forbid_move = True
                break

    def getCurrentPos(self):
        return self.currentPos

    # def drawRays(ray_list):
    #     for ray in ray_list:
    #         try:
    #             line = pygame.draw.line(surface, red, (scale*ray.position_list[0][0], surface_size[1]-scale*ray.position_list[0][1]), (scale*ray.position_list[2][0], surface_size[1]-scale*ray.position_list[2][1]), 5)
    #         except:
    #             pass

# Initialise GUI
# map = classes.readmapfromfile("../resources/mapSettings.txt")
# room = GUI(map)
# room.main_loop()