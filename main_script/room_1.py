import pygame
import sys

def terminate():
    pygame.quit()
    sys.exit()

pygame.init()
# Initializing surface

surface = pygame.display.set_mode((400, 300))
# Initialing Color
color = (255, 0, 0)
clock = pygame.time.Clock()
fps=30

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            terminate()
    pygame.draw.rect(surface, color, pygame.Rect(30, 30, 60, 60))
    pygame.display.flip()
    clock.tick(fps)


# To do:
# 1. narysować pokój z krawędziami do kolizji
# 2. umieszczenie kwadratu symbolizującego osobę
# 3. przemieszczanie osoby strzałkami
# 4. implementacja nadajników/odbiorników
# 5. połączenie z częścia radiową
# 6. stworzenie obrazu, który by pokazywał gdzie znajduje się osoba w pomieszczeniu