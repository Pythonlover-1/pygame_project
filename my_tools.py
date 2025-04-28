import pygame
from os import path

# папки, хранящие файлы
snd_dir = path.join(path.dirname(__file__), 'data/wav')  # звука
img_dir = path.join(path.dirname(__file__), 'data')  # изображений

# основное окно программы
size = width, height = 1400, 800


def load_image(name, color_key=None):
    '''Вспомогательная функция загрузки изображений'''
    try:
        image = pygame.image.load(path.join(img_dir, name))
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image
