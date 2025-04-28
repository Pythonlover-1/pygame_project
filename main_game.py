from os import path
import pygame
import random
import sqlite3
from datetime import datetime

from my_tools import load_image, snd_dir, size, width, height
from classes import Wolf, Egg, Chicken, Switch, Push
from classes import EGG, CATCH, NO_CATCH
from classes import FONT, DIFFICULT, LEVELS
from classes import points_chicken, points_push, points_egg, \
    points_switch, points_wolf, points_catch
from classes import all_sprites, control_sprites

DB_FILE = 'game_users.sqlite'
FPS = 50
# Цветовая схема
COLORS = {
    'bg': (240, 240, 245),
    'text': (50, 50, 70),
    'accent': (218, 165, 32),
    'button': (70, 130, 180),
    'button_text': (255, 255, 255),
    'success': (60, 160, 60),
    'warning': (190, 60, 60),
    'success_hover': (80, 180, 80),
    'warning_hover': (210, 80, 80),
    'error': (200, 50, 50),
    'hint': (120, 120, 140)
}


def init_db():
    """Инициализация базы данных SQLite"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  registration_date TEXT,
                  last_played TEXT,
                  highscore INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS game_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  play_date TEXT,
                  score INTEGER,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')

    conn.commit()
    conn.close()


def get_all_users():
    """Получение списка всех пользователей"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, highscore FROM users ORDER BY highscore DESC")
    users = c.fetchall()
    conn.close()
    return users


def register_user(username):
    """Регистрация нового пользователя"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        now = datetime.now().isoformat()
        c.execute("INSERT INTO users (username, registration_date, last_played) VALUES (?, ?, ?)",
                  (username, now, now))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_user_stats(username, score):
    """Обновление статистики пользователя"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        now = datetime.now().isoformat()

        c.execute('''UPDATE users 
                     SET last_played = ?,
                         highscore = MAX(highscore, ?)
                     WHERE username = ?''',
                  (now, score, username))

        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = c.fetchone()[0]

        c.execute("INSERT INTO game_sessions (user_id, play_date, score) VALUES (?, ?, ?)",
                  (user_id, now, score))

        conn.commit()
    finally:
        conn.close()


def show_user_selection_screen(screen):
    """Отображение экрана выбора пользователя"""
    users = get_all_users()
    selected_index = 0 if users else -1
    font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 48)
    button_font = pygame.font.Font(None, 32)
    clock = pygame.time.Clock()
    monitor_rect = draw_monitor_surface(screen)
    offset_x, offset_y = monitor_rect.x, monitor_rect.y
    inner_width, inner_height = monitor_rect.width, monitor_rect.height
    new_user_rect = pygame.Rect(offset_x + inner_width // 2 - 150,
                                offset_y + inner_height - 150, 300, 50)
    start_rect = pygame.Rect(offset_x + inner_width // 2 - 150,
                             offset_y + inner_height - 80, 300, 50)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if new_user_rect.collidepoint(mouse_pos):
                    username = show_registration_screen(screen)
                    if username:
                        return username
                    users = get_all_users()
                    selected_index = 0 if users else -1
                    draw_monitor_surface(screen)

                elif start_rect.collidepoint(mouse_pos) and selected_index >= 0:
                    return users[selected_index][0]

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and selected_index > 0:
                    selected_index -= 1
                elif event.key == pygame.K_DOWN and selected_index < len(users) - 1:
                    selected_index += 1
                elif event.key == pygame.K_RETURN and selected_index >= 0:
                    return users[selected_index][0]
        draw_monitor_surface(screen)
        title = title_font.render("Выберите игрока", True, COLORS['text'])
        screen.blit(title, (offset_x + inner_width // 2 - title.get_width() // 2,
                            offset_y + 50))
        if not users:
            no_users = font.render("Нет зарегистрированных пользователей", True, COLORS['text'])
            screen.blit(no_users, (offset_x + inner_width // 2 - no_users.get_width() // 2,
                                   offset_y + inner_height // 3))
        else:
            for i, (user, highscore) in enumerate(users):
                color = COLORS['accent'] if i == selected_index else COLORS['text']
                user_text = font.render(f"{user} (рекорд: {highscore})", True, color)
                screen.blit(user_text, (offset_x + inner_width // 2 - user_text.get_width() // 2,
                                        offset_y + 150 + i * 40))
        pygame.draw.rect(screen, COLORS['button'], new_user_rect)
        new_user_text = button_font.render("Новый игрок", True, COLORS['button_text'])
        screen.blit(new_user_text, (new_user_rect.x + new_user_rect.w // 2 - new_user_text.get_width() // 2,
                                    new_user_rect.y + new_user_rect.h // 2 - new_user_text.get_height() // 2))

        if selected_index >= 0:
            pygame.draw.rect(screen, COLORS['success'], start_rect)
            start_text = button_font.render("Начать игру", True, COLORS['button_text'])
            screen.blit(start_text, (start_rect.x + start_rect.w // 2 - start_text.get_width() // 2,
                                     start_rect.y + start_rect.h // 2 - start_text.get_height() // 2))

        pygame.display.flip()
        clock.tick(30)


def show_registration_screen(screen):
    """Отображение экрана регистрации"""
    input_active = True
    username = ""
    font = pygame.font.Font(None, 36)
    title_font = pygame.font.Font(None, 48)
    clock = pygame.time.Clock()
    error_message = ""
    monitor_rect = draw_monitor_surface(screen)
    offset_x, offset_y = monitor_rect.x, monitor_rect.y
    inner_width, inner_height = monitor_rect.width, monitor_rect.height
    input_box = pygame.Rect(offset_x + inner_width // 2 - 150,
                            offset_y + inner_height // 2, 300, 40)
    color_inactive = pygame.Color(*COLORS['button']).lerp((255, 255, 255), 0.7)
    color_active = pygame.Color(*COLORS['button'])
    color = color_inactive
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    input_active = True
                else:
                    input_active = False
                color = color_active if input_active else color_inactive
            if event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        if username.strip():
                            if register_user(username):
                                return username
                            else:
                                error_message = "Пользователь уже существует"
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                        error_message = ""
                    else:
                        username += event.unicode
                        error_message = ""

        draw_monitor_surface(screen)
        title = title_font.render("Регистрация нового игрока", True, COLORS['text'])
        screen.blit(title, (offset_x + inner_width // 2 - title.get_width() // 2,
                            offset_y + inner_height // 3))
        txt_surface = font.render("Введите имя:", True, COLORS['text'])
        screen.blit(txt_surface, (offset_x + inner_width // 2 - 150,
                                  offset_y + inner_height // 2 - 40))

        pygame.draw.rect(screen, color, input_box, 2)
        txt_surface = font.render(username, True, COLORS['text'])
        screen.blit(txt_surface, (input_box.x + 10, input_box.y + 10))
        input_box.w = max(300, txt_surface.get_width() + 20)

        if error_message:
            error_text = font.render(error_message, True, COLORS['error'])
            screen.blit(error_text, (offset_x + inner_width // 2 - error_text.get_width() // 2,
                                     offset_y + inner_height // 2 + 50))

        hint = font.render("Нажмите Enter для подтверждения", True, COLORS['hint'])
        screen.blit(hint, (offset_x + inner_width // 2 - hint.get_width() // 2,
                           offset_y + inner_height - 100))

        pygame.display.flip()
        clock.tick(30)


def show_results_screen(screen, username, score):
    """Отображение экрана с результатами игры с кликабельными кнопками"""
    font_large = pygame.font.Font(None, 72)
    font_medium = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 36)

    # Получаем рекорд пользователя
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT highscore FROM users WHERE username = ?", (username,))
    highscore = c.fetchone()[0]
    conn.close()
    monitor_rect = draw_monitor_surface(screen)
    offset_x, offset_y = monitor_rect.x, monitor_rect.y
    inner_width, inner_height = monitor_rect.width, monitor_rect.height
    new_game_rect = pygame.Rect(offset_x + inner_width // 2 - 150,
                                offset_y + inner_height - 150, 300, 50)
    menu_rect = pygame.Rect(offset_x + inner_width // 2 - 150,
                            offset_y + inner_height - 80, 300, 50)

    clock = pygame.time.Clock()
    while True:
        mouse_pos = pygame.mouse.get_pos()
        new_game_hover = new_game_rect.collidepoint(mouse_pos)
        menu_hover = menu_rect.collidepoint(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if new_game_rect.collidepoint(event.pos):
                    return "restart"
                elif menu_rect.collidepoint(event.pos):
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "restart"
                elif event.key in (pygame.K_q, 1081):
                    return "menu"
        draw_monitor_surface(screen)

        # Результаты игры
        result_text = font_large.render(f"Игрок: {username}", True, COLORS['text'])
        screen.blit(result_text, (offset_x + inner_width // 2 - result_text.get_width() // 2,
                                  offset_y + inner_height // 3 - 50))

        score_text = font_medium.render(f"Ваш результат: {score}", True, COLORS['text'])
        screen.blit(score_text, (offset_x + inner_width // 2 - score_text.get_width() // 2,
                                 offset_y + inner_height // 3 + 50))

        highscore_text = font_medium.render(f"Ваш рекорд: {highscore}", True, COLORS['accent'])
        screen.blit(highscore_text, (offset_x + inner_width // 2 - highscore_text.get_width() // 2,
                                     offset_y + inner_height // 3 + 120))
        pygame.draw.rect(screen,
                         COLORS['success_hover'] if new_game_hover else COLORS['success'],
                         new_game_rect)
        pygame.draw.rect(screen,
                         COLORS['warning_hover'] if menu_hover else COLORS['warning'],
                         menu_rect)
        new_game_text = font_small.render("Новая игра (Enter)", True, COLORS['button_text'])
        screen.blit(new_game_text, (new_game_rect.x + new_game_rect.w // 2 - new_game_text.get_width() // 2,
                                    new_game_rect.y + new_game_rect.h // 2 - new_game_text.get_height() // 2))
        menu_text = font_small.render("В меню (Q)", True, COLORS['button_text'])
        screen.blit(menu_text, (menu_rect.x + menu_rect.w // 2 - menu_text.get_width() // 2,
                                menu_rect.y + menu_rect.h // 2 - menu_text.get_height() // 2))

        pygame.display.flip()
        clock.tick(30)


def draw_monitor_surface(screen, bg_color=(240, 240, 245)):
    """Отрисовывает поверхность монитора с рамкой и заданным цветом фона"""
    monitor_bg = pygame.Surface((width - width // 5, height - height // 5), pygame.SRCALPHA)
    monitor_bg.fill(bg_color)
    x_pos = width // 10
    y_pos = height // 10
    screen.blit(monitor_bg, (x_pos, y_pos))
    monitor_frame = load_image('screen__.png', -1)
    monitor_frame = pygame.transform.scale(monitor_frame, size)
    screen.blit(monitor_frame, (0, 0))

    return pygame.Rect(x_pos, y_pos, width - width // 5, height - height // 5)


def run_game(screen, username):
    """Основной игровой цикл"""
    global switch_on, push_on, pause_state

    # Задаём начальное состояние
    switch_on = False
    push_on = [False, False]
    pause_state = False
    show_help = False
    all_sprites.empty()
    control_sprites.empty()
    delta_level = 0
    egg_frequency = old_frequency = 2200
    level_music = 0.4
    wolf = Wolf(random.randint(0, 3), points_wolf)
    chickens = [Chicken(points_chicken[count]) for count in range(3)]

    switch_sound = Switch(0, switch_on, points_switch)
    push_turn = Push(0, push_on[0], points_push[0])  # Кнопка включения
    push_enable = Push(2, push_on[1], points_push[1])  # Кнопка паузы
    push_info = Push(4, False, points_push[2])  # Кнопка настроек

    surface_bg = pygame.Surface((width - width // 4, height - height // 6))
    surface_bg.fill((255, 255, 255))

    levels_images = [pygame.transform.scale(
        load_image(LEVELS[count + 1], -1), (width - width // 5, height - height // 7)) for count in range(3)]
    level = levels_images[0]

    monitor = load_image('screen__.png', -1)
    monitor = pygame.transform.scale(monitor, size)

    trays = load_image('lots__.png', -1)
    trays = pygame.transform.scale(trays, (width + 2, height + 1))

    # Инициализация звуков
    switch_sound_ = pygame.mixer.Sound(path.join(snd_dir, 'switch.wav'))
    push_sound = pygame.mixer.Sound(path.join(snd_dir, 'push.wav'))
    denied_sound = pygame.mixer.Sound(path.join(snd_dir, 'denied.mp3'))

    clock = pygame.time.Clock()
    pygame.time.set_timer(EGG, egg_frequency)
    space = True
    total = 0
    current_level = 0
    life = 3

    running = True

    pygame.mixer.music.load(path.join(snd_dir, 'wolf_catches_eggs1.mp3'))
    pygame.mixer.music.play(loops=-1)
    pygame.mixer.music.set_volume(0)

    try:
        while running:
            clock.tick(FPS + delta_level)
            if not pause_state:
                if current_level < len(DIFFICULT):
                    if total == DIFFICULT[current_level]:
                        level = pygame.transform.scale(levels_images[current_level + 1],
                                                       (width - width // 4, height - height // 6))
                        current_level += 1
                        delta_level += 5
                        egg_frequency -= 700
                else:
                    delta_level = 20
                    egg_frequency = 700
            if total == 200:
                delta_level = 30
                egg_frequency = 600
            elif total == 250:
                delta_level += 30
                egg_frequency = 200
            if egg_frequency != old_frequency:
                pygame.time.set_timer(EGG, egg_frequency)
                old_frequency = egg_frequency

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.time.set_timer(EGG, 0)
                    return False, None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if switch_sound.rect.collidepoint(pygame.mouse.get_pos()):
                        switch_on = not switch_on
                        switch_sound.change_switch(int(switch_on))
                        pygame.mixer.music.set_volume(level_music if switch_on else 0)
                        switch_sound_.play()

                    if push_turn.push_collidepoint(pygame.mouse.get_pos()):
                        if not show_help:
                            if push_on[0]:
                                pygame.time.set_timer(EGG, 0)
                                return False, None
                            push_on[0] = not push_on[0]
                            push_turn.change_push(int(push_on[0]))
                            push_sound.play()
                        else:
                            denied_sound.play()
                    if push_enable.push_collidepoint(pygame.mouse.get_pos()):
                        if push_on[0] and not show_help:
                            pause_state = not pause_state
                            push_enable.change_push(2 + int(pause_state))
                            push_sound.play()
                        else:
                            denied_sound.play()
                    if push_info.push_collidepoint(pygame.mouse.get_pos()):
                        push_sound.play()
                        show_help = not show_help
                if pause_state:
                    continue
                if event.type == EGG and push_on[0]:
                    Egg(points_egg[random.randint(0, 3)])
                if event.type == CATCH:
                    total += 1
                if event.type == NO_CATCH:
                    life -= 1
                    if chickens:
                        chickens.pop(0).kill()
                    if life == 0:
                        pygame.time.set_timer(EGG, 0)
                        running = False
                if event.type == pygame.KEYDOWN:
                    if event.key in (1073741919, pygame.K_END):
                        wolf.move(0, points_wolf, points_catch[0])
                    elif event.key in (1073741921, pygame.K_HOME):
                        wolf.move(1, points_wolf, points_catch[1])
                    elif event.key in (1073741915, pygame.K_UP):
                        wolf.move(3, points_wolf, points_catch[3])
                    elif event.key in (1073741913, pygame.K_DOWN):
                        wolf.move(2, points_wolf, points_catch[2])
                    elif event.key == pygame.K_SPACE:
                        space = not space
                        pygame.time.set_timer(EGG, 0 if space else egg_frequency)

            surface_bg.blit(level, (0, 0))
            screen.blit(surface_bg, (160, 60))
            counter = FONT.render(f'{total}', True, (255, 0, 0))
            box = counter.get_rect(midtop=(width - width // 4, height // 8))
            screen.blit(counter, box)
            screen.blit(trays, (-1, 0))
            all_sprites.draw(screen)
            if not pause_state:
                all_sprites.update(wolf.point)
            else:
                pause_text = FONT.render("ПАУЗА", True, (255, 0, 0))
                screen.blit(pause_text, (width // 2 - pause_text.get_width() // 2, height // 2))
            screen.blit(monitor, (0, 0))
            if show_help:
                if not pause_state and push_on[0]:
                    pause_state = not pause_state
                    push_enable.change_push(2 + int(pause_state))
                help_surface = pygame.Surface((width, height), pygame.SRCALPHA)
                help_surface.fill((0, 0, 0, 180))
                screen.blit(help_surface, (0, 0))

                # Создаем текст подсказки
                font = pygame.font.Font(None, 36)
                lines = [
                    "Управление в игре:",
                    "",
                    "Клавиши END/HOME - движение волка влево/вправо",
                    "Клавиши UP/DOWN - движение волка вверх/вниз",
                    "Клавиша SPACE - пауза",
                    "Кнопка звука - включение/выключение звука",
                    "Кнопка паузы - поставить игру на паузу",
                    "",
                    "Нажмите кнопку информации еще раз, чтобы закрыть"
                ]
                for i, line in enumerate(lines):
                    text = font.render(line, True, (255, 255, 255))
                    screen.blit(text, (width // 2 - text.get_width() // 2,
                                       height // 2 - 100 + i * 40))

            control_sprites.draw(screen)

            pygame.display.flip()
    finally:
        pygame.mixer.music.stop()
        pygame.time.set_timer(EGG, 0)
        update_user_stats(username, total)
        return True, total


def _show_screen_template(screen, title_text, title_color=(255, 179, 173)):
    """Шаблон для показа экранов (заставка и прощание)"""
    image = load_image('old_gadget.jpg')
    k = 1.5
    new_width = int(image.get_rect().width * k)
    new_height = int(image.get_rect().height * k)
    image = pygame.transform.scale(image, (new_width, new_height))

    text = FONT.render(title_text, True, title_color)
    titul = text.get_rect(midtop=(width // 2, 100))

    pygame.mixer.music.load(path.join(snd_dir, 'old_gadget_game.mp3'))
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(loops=-1)

    clock = pygame.time.Clock()
    waiting = True

    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                return False
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

        screen.fill((0, 0, 0))
        screen.blit(text, titul)
        screen.blit(image, (width // 6, height // 4))

        font = pygame.font.Font(None, 36)
        hint = font.render("Нажмите любую клавишу или кнопку мыши", True, (200, 200, 200))
        screen.blit(hint, (width // 2 - hint.get_width() // 2, height - 100))

        pygame.display.flip()

    pygame.mixer.music.stop()
    return True


def show_splash_screen(screen):
    """Отображение заставки игры"""
    return _show_screen_template(screen, "Старая, добрая игра...")


def show_goodbye_screen(screen):
    """Отображение прощального экрана при выходе из игры"""
    _show_screen_template(screen, "До новых встреч!")


def main():
    """Главная функция программы"""
    pygame.init()
    pygame.display.set_caption("Ну Погоди!")
    pygame.mixer.init()
    screen = pygame.display.set_mode(size)

    # Показываем заставку
    if not show_splash_screen(screen):
        pygame.quit()
        return

    # Основной игровой цикл
    current_user = None
    while True:
        # Выбор пользователя (если current_user не установлен)
        if current_user is None:
            current_user = show_user_selection_screen(screen)
            if not current_user:  # Если пользователь не выбран (нажали отмену)
                break
        play_again, total = run_game(screen, current_user)

        # Показываем результаты
        action = show_results_screen(screen, current_user, total)
        if action == "menu":
            current_user = None
            continue
        elif action == "restart":
            continue
        else:
            break

    # Показываем прощальный экран
    show_goodbye_screen(screen)
    pygame.mixer.quit()
    pygame.quit()


if __name__ == "__main__":
    init_db()
    main()
