import pygame
from my_tools import load_image, width, height
from math import sqrt
import random

pygame.init()

# события в игре:
EGG = pygame.USEREVENT + 1  # появление яйца в лотке
CATCH = pygame.USEREVENT + 2  # яйцо поймано
NO_CATCH = pygame.USEREVENT + 3  # яйцо не поймано

pause_state = False
# коэффициент для изображений волка
ratio = 1.1
# шрифт (по умолчанию) для отображения счета
FONT = pygame.font.Font(None, 60)
# информация об уровнях перехода на следующий уровень
DIFFICULT = (50, 100)
# шкала для уменьшения изображения волка
SCALES = (380, 406, 416, 429)
# информация о файлах, хранящих изображения
LEVELS = {1: 'level_1.png', 2: 'level_2.png', 3: 'level_3.png'}  # фоны, соответствующие уровню сложности
PLACES = {0: 'wolf_lt.png', 1: 'wolf_rt.png', 2: 'wolf_lb.png', 3: 'wolf_rb.png', }  # фигуры волка в разных положениях
SWITCH = {0: 'sound_off.png', 1: 'sound_on.png'}  # переключатель on/off
# картинки, кнопкам управления (on/off)
PUSH = {'game': ('off.png', 'on.png'),
        'pause': ('pause_off.png', 'pause_on.png'),
        'setting': ('setting.png', '')}

all_sprites = pygame.sprite.Group()
control_sprites = pygame.sprite.Group()

# позиционирование переключателя (on/off) звука
points_switch = (55, 190)
switch_on = False  # информация о начальном состоянии переключателя
# позиционирование кнопок управления
points_push = ((1240, 105), (1240, 290), (45, 35))
push_on = [False] * 3  # информация о состоянии кнопок управления
# точки коллизий яйцо-корзинка
points_catch = ((550, 451), (912, 443), (490, 615), (912, 607))
#  точки появления выкатывающихся яиц
points_egg = ((195, 193), (195, 385), (1155, 193), (1155, 385))
# позиционирование цыплят (отображение "жизней"-попыток)
points_chicken = tuple([(width // 2 - width // 12 + 80 * count, height // 4) for count in range(3)])
# позиционирование волка
top, bottom = 490, 340
points_wolf = (top, bottom)
# позиционирование разбившихся яиц
points_egg_break = ([450, 610], [840, 610])


class Game:
    def __init__(self, size_):
        self.size = size_
        self.width, self.height = self.size
        self.points = {
            'switch': (55, 190), 'push': ((1240, 105), (1240, 290), (45, 35)),
            'egg_catch': ((550, 451), (912, 443), (490, 615), (912, 607)),
            'egg_break': ([450, 610], [840, 610]),
            'egg': ((195, 193), (195, 385), (1155, 193), (1155, 385)),
            'wolf': (490, 340),
            'chicken': tuple(
                [(self.width // 2 - self.width // 12 + 80 * count, self.height // 4) for count in range(3)])
        }
        self.pieces_sprites = pygame.sprite.Group()
        self.control_sprites = pygame.sprite.Group()


class Switch(pygame.sprite.Sprite):
    images = [pygame.transform.scale(load_image(SWITCH[count], -1), (100, 70)) for count in range(2)]

    def __init__(self, figure, state, point):
        super().__init__(control_sprites)
        self.image = Switch.images[figure]
        self.switch = state
        self.rect = self.image.get_rect()
        self.rect.x = point[0]
        self.rect.y = point[1]

    def change_switch(self, figure):
        self.image = Switch.images[figure]


class Push(pygame.sprite.Sprite):
    images = list()
    for key in PUSH:
        for count in range(2):
            if PUSH[key][count]:
                images.append(pygame.transform.scale(load_image(PUSH[key][count], -1), (115, 115)))

    def __init__(self, figure, state, point_push):
        super().__init__(control_sprites)
        self.image = Push.images[figure]
        self.push = state
        self.figure = figure
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.radius = 45
        self.rect.x = point_push[0]
        self.rect.y = point_push[1]

    def change_push(self, figure):
        self.image = Push.images[figure]
        self.figure = figure

    def push_collidepoint(self, point):
        return (sqrt(
            (self.rect.center[0] - point[0]) ** 2 + (self.rect.center[1] - point[1]) ** 2)) <= float(self.radius)


class Wolf(pygame.sprite.Sprite):
    images = [pygame.transform.scale(
        load_image(PLACES[count], -1), (int(SCALES[count] * ratio), int(330 * ratio))) for count in range(4)]

    def __init__(self, figure, point):
        super().__init__(all_sprites)
        delta = 0 if figure != 3 else 40
        self.image = Wolf.images[figure]
        self.point = points_catch[figure]
        self.rect = self.image.get_rect()
        self.rect.x = point[0] - delta
        self.rect.y = point[1]

    def move(self, figure, point, point_catch):
        delta = 0 if figure != 3 else 40
        self.image = Wolf.images[figure]
        self.point = point_catch
        self.rect = self.image.get_rect()
        self.rect.x = point[0] - delta
        self.rect.y = point[1]


class Chicken(pygame.sprite.Sprite):
    image = load_image('chicken.png', -1)
    image = pygame.transform.scale(image, (70, 85))

    def __init__(self, pos):
        super().__init__(all_sprites)
        self.image = Chicken.image
        self.rect = self.image.get_rect()
        self.last_update = pygame.time.get_ticks()
        self.rect.x = pos[0]
        self.rect.y = pos[1]


class EggBreak(pygame.sprite.Sprite):
    image = load_image('break_egg.png', -1)
    image = pygame.transform.scale(image, (100, 100))

    def __init__(self, pos, delta):
        super().__init__(all_sprites)
        self.image = EggBreak.image
        self.rect = self.image.get_rect()
        self.last_update = pygame.time.get_ticks()
        self.rect.x = pos[0]
        self.rect.y = pos[1] + delta

    def erase_break_egg(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > 1000:
            self.kill()

    def update(self, none):
        self.erase_break_egg()


class Egg(pygame.sprite.Sprite):
    image = load_image('egg_0.png', -1)
    image = pygame.transform.scale(image, (40, 50))

    def __init__(self, pos):
        super().__init__(all_sprites)
        self.image = Egg.image
        self.rect = self.image.get_rect()
        self.up = True if pos[1] < height // 3 else False  # верхний/нижний лоток
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.last_update = pygame.time.get_ticks()
        self.speed_y = 1.99
        self.speed_x = 2.5
        self.rot = 0
        if self.rect.x == 195:
            self.direct = -1
        else:
            self.direct = 1
        self.rot_speed = self.direct * 7

    def rotate(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > 10:
            self.last_update = now
            self.rot = (self.rot + self.rot_speed) % 360
            new_image = pygame.transform.rotate(Egg.image, self.rot)
            old_center = self.rect.center
            self.image = new_image
            self.rect = self.image.get_rect()
            self.rect.center = old_center

    def update(self, point):
        self.rotate()
        if not self.rect.collidepoint(point):
            if self.direct < 0:
                # левая сторона
                if self.rect.x <= 490:
                    #  яйцо скатывается
                    self.rect = self.rect.move(
                        -self.direct * self.speed_x, self.speed_y) if self.up else self.rect.move(
                        -self.direct * self.speed_x, self.speed_y - 0.39)
                else:
                    #  яйцо падает отвесно
                    self.rect = self.rect.move(0, self.speed_y * 2)
            else:
                # правая сторона
                if 1155 >= self.rect.x > 860:
                    #  яйцо скатывается
                    self.rect = self.rect.move(
                        -self.direct * self.speed_x, self.speed_y) if self.up else self.rect.move(
                        -self.direct * self.speed_x, self.speed_y - 0.39)
                else:
                    #  яйцо падает отвесно
                    self.rect = self.rect.move(0, self.speed_y * 2)
            if self.rect.y > 609:
                if self.rect.x < width // 2:
                    #  разбитое яйцо слева
                    EggBreak(points_egg_break[0], random.randint(0, 30))
                else:
                    #  разбитое яйцо справа
                    EggBreak(points_egg_break[1], random.randint(0, 30))
                self.kill()
                pygame.event.post(pygame.event.Event(NO_CATCH))
        else:
            pygame.event.post(pygame.event.Event(CATCH))
            self.kill()
