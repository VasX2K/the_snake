"""Игра «Змейка» с переходом через границы игрового поля."""

from random import choice

import pygame


SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

BOARD_BACKGROUND_COLOR = (0, 0, 0)
BORDER_COLOR = (93, 216, 228)
APPLE_COLOR = (255, 0, 0)
SNAKE_COLOR = (0, 255, 0)
SPEED = 20

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
pygame.display.set_caption('Змейка')
clock = pygame.time.Clock()


class GameObject:
    """Базовый объект с позицией и цветом на игровом поле."""

    def __init__(self):
        """Разместить объект в центре поля без заданного цвета."""
        self.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.body_color = None

    def draw(self):
        """Определить интерфейс отрисовки для дочерних классов."""
        pass


class Apple(GameObject):
    """Яблоко, которое появляется в случайной свободной клетке."""

    def __init__(self):
        """Задать красный цвет и случайную начальную позицию."""
        super().__init__()
        self.body_color = APPLE_COLOR
        self.randomize_position()

    def randomize_position(self, occupied_positions=()):
        """Выбрать случайную клетку вне переданных занятых позиций."""
        occupied = set(occupied_positions)
        free_positions = [
            (column * GRID_SIZE, row * GRID_SIZE)
            for column in range(GRID_WIDTH)
            for row in range(GRID_HEIGHT)
            if (column * GRID_SIZE, row * GRID_SIZE) not in occupied
        ]
        if not free_positions:
            raise ValueError('На игровом поле нет свободных клеток.')
        self.position = choice(free_positions)

    def draw(self):
        """Нарисовать яблоко с границей размером в одну клетку."""
        rect = pygame.Rect(self.position, (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, self.body_color, rect)
        pygame.draw.rect(screen, BORDER_COLOR, rect, 1)


class Snake(GameObject):
    """Змейка, состоящая из списка координат её сегментов."""

    def __init__(self):
        """Создать зелёную змейку длиной в один сегмент."""
        super().__init__()
        self.body_color = SNAKE_COLOR
        self.reset()

    def update_direction(self):
        """Применить выбранный поворот, запретив разворот назад."""
        if self.next_direction:
            opposite = (-self.direction[0], -self.direction[1])
            if self.next_direction != opposite:
                self.direction = self.next_direction
            self.next_direction = None

    def move(self):
        """Сдвинуть змейку на клетку с переходом через края поля."""
        head_x, head_y = self.get_head_position()
        direction_x, direction_y = self.direction
        new_head = (
            (head_x + direction_x * GRID_SIZE) % SCREEN_WIDTH,
            (head_y + direction_y * GRID_SIZE) % SCREEN_HEIGHT,
        )
        self.positions.insert(0, new_head)
        self.last = None
        if len(self.positions) > self.length:
            self.last = self.positions.pop()

    def draw(self):
        """Стереть прежний хвост и нарисовать все сегменты змейки."""
        if self.last is not None:
            last_rect = pygame.Rect(self.last, (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, last_rect)

        for position in self.positions:
            rect = pygame.Rect(position, (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, self.body_color, rect)
            pygame.draw.rect(screen, BORDER_COLOR, rect, 1)

    def get_head_position(self):
        """Вернуть координаты первого сегмента змейки."""
        return self.positions[0]

    def reset(self):
        """Вернуть змейку в центр и начать движение вправо."""
        self.position = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.length = 1
        self.positions = [self.position]
        self.direction = RIGHT
        self.next_direction = None
        self.last = None


def handle_keys(game_object):
    """Обработать закрытие окна и повороты стрелками клавиатуры."""
    directions = {
        pygame.K_UP: UP,
        pygame.K_DOWN: DOWN,
        pygame.K_LEFT: LEFT,
        pygame.K_RIGHT: RIGHT,
    }
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        if event.type == pygame.KEYDOWN and event.key in directions:
            direction = directions[event.key]
            opposite = (-game_object.direction[0], -game_object.direction[1])
            if direction != opposite:
                game_object.next_direction = direction


def main():
    """Запустить игру и обновлять её состояние до закрытия окна."""
    pygame.init()
    snake = Snake()
    apple = Apple()
    apple.randomize_position(snake.positions)
    screen.fill(BOARD_BACKGROUND_COLOR)

    while True:
        clock.tick(SPEED)
        handle_keys(snake)
        snake.update_direction()
        snake.move()

        if snake.get_head_position() in snake.positions[1:]:
            snake.reset()
            screen.fill(BOARD_BACKGROUND_COLOR)
            apple.randomize_position(snake.positions)
        elif snake.get_head_position() == apple.position:
            snake.length += 1
            # Сохранить хвост, чтобы вырасти в момент поедания яблока.
            snake.positions.append(snake.last)
            snake.last = None
            if snake.length == GRID_WIDTH * GRID_HEIGHT:
                snake.reset()
                screen.fill(BOARD_BACKGROUND_COLOR)
            apple.randomize_position(snake.positions)

        snake.draw()
        apple.draw()
        pygame.display.update()


if __name__ == '__main__':
    main()
