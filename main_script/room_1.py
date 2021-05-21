import pygame
from resources import classes
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
map = classes.readmapfromfile("../resources/mapSettings.txt")
forbid_move = False

def terminate():
    pygame.quit()
    sys.exit()

def getPos():
    pos = pygame.mouse.get_pos()
    return pos


def checkCollisions(human_pos, walls):
    global forbid_move, prevPos
    for wall in walls:
        if pygame.Rect.colliderect(wall, human_pos):
            forbid_move = True
            break
    for node in node_list:
        if pygame.Rect.colliderect(node, human_pos):
            forbid_move = True
            break


def drawRays(ray_list):
    for ray in ray_list:
        try:
            line = pygame.draw.line(surface, red, (scale*ray.position_list[0][0], surface_size[1]-scale*ray.position_list[0][1]), (scale*ray.position_list[2][0], surface_size[1]-scale*ray.position_list[2][1]), 5)
        except:
            pass


pygame.init()
# Initializing surface
surface_size = (scale*map.width, scale*map.height)
surface = pygame.display.set_mode(surface_size)
pygame.display.set_caption("Trace room")
surface.fill(white)
clock = pygame.time.Clock()
fps=20
prevPos = (scale*200, scale*200)

#draw map on surface based on mapSettings.txt
wall_list = []
node_list = []
for object in map.objectList:
    if isinstance(object, classes.Wall):
        wall = pygame.draw.rect(surface, gray, pygame.Rect(int(scale*object.position[0]), int(surface_size[1] - scale*object.position[1]),
                                                            int(scale*object.size[0]), int(scale*(-object.size[1]))))
        wall_list.append(wall)
    if isinstance(object, classes.Node):
        node = pygame.draw.rect(surface, gold, pygame.Rect(int(scale*object.position[0]), int(surface_size[1] - scale*object.position[1]),
                                                            scale*10, scale*10))
        node_list.append(node)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
    if prevPos:
        pygame.draw.rect(surface, white, pygame.Rect(prevPos[0], prevPos[1], scale*10, scale*10))

    circle = pygame.Rect(getPos()[0], getPos()[1], scale*10, scale*10)
    checkCollisions(circle, wall_list)
    checkCollisions(circle, node_list)

    if not forbid_move:
        circle = pygame.draw.rect(surface, blue, pygame.Rect(getPos()[0], getPos()[1], scale*10, scale*10))
        prevPos = (getPos()[0], getPos()[1])
    else:
        circle = pygame.draw.rect(surface, blue, pygame.Rect(prevPos[0], prevPos[1], scale*10, scale*10))

    currentPos = (prevPos[0]/scale, (surface_size[1]-prevPos[1])/scale)
    print(currentPos)
    forbid_move = False
    pygame.display.flip()
    pygame.image.save(surface, '../results/surface.png')    # wstępnie można będie heatMapę na tej podstawie zrobić
    #drawRays(rayLista)

    clock.tick(fps)