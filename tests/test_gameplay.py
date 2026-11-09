"""Проверки правил игры и отрисовки в дополнение к тестам задания."""

import pygame
import pytest


@pytest.mark.parametrize('position, direction, expected', [
    ((620, 100), (1, 0), (0, 100)),
    ((0, 100), (-1, 0), (620, 100)),
    ((100, 460), (0, 1), (100, 0)),
    ((100, 0), (0, -1), (100, 460)),
])
def test_wraparound(snake, position, direction, expected):
    """Все четыре края переносят голову на противоположную сторону."""
    snake.positions = [position]
    snake.direction = direction
    snake.move()
    assert snake.positions == [expected]
    assert snake.last == position


def test_growth_preserves_tail(snake):
    """Увеличенная длина сохраняет хвост при следующем шаге."""
    original_head = snake.get_head_position()
    snake.length += 1
    snake.move()
    assert len(snake.positions) == snake.length == 2
    assert snake.positions[-1] == original_head
    assert snake.last is None


@pytest.mark.parametrize('direction', [(0, -1), (0, 1), (-1, 0), (1, 0)])
def test_reverse_is_rejected(snake, direction):
    """Противоположное направление не применяется."""
    snake.direction = direction
    snake.next_direction = (-direction[0], -direction[1])
    snake.update_direction()
    assert snake.direction == direction
    assert snake.next_direction is None


def test_arrow_events(snake, _the_snake, monkeypatch):
    """Последовательность событий не разрешает разворот за один шаг."""
    events = [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP),
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT),
    ]
    monkeypatch.setattr(pygame.event, 'get', lambda: events)
    _the_snake.handle_keys(snake)
    snake.update_direction()
    assert snake.direction == _the_snake.UP


def test_apple_uses_only_free_cell(apple, _the_snake):
    """Яблоко выбирает единственную свободную клетку, даже у края."""
    occupied = [
        (x, y) for x in range(0, 640, 20) for y in range(0, 480, 20)
        if (x, y) != (620, 460)
    ]
    apple.randomize_position(occupied)
    assert apple.position == (620, 460)
    with pytest.raises(ValueError):
        apple.randomize_position(occupied + [apple.position])


def test_tail_cell_can_be_entered(snake, _the_snake):
    """Освобождённая клетка хвоста остаётся видимой при входе головы."""
    snake.positions = [(20, 20), (20, 40), (0, 40), (0, 20)]
    snake.length = 4
    snake.direction = _the_snake.LEFT
    snake.move()
    snake.draw()
    assert snake.get_head_position() not in snake.positions[1:]
    assert _the_snake.screen.get_at((10, 30))[:3] == snake.body_color


def run_one_frame(game, snake, apple, monkeypatch):
    """Выполнить одну итерацию настоящего игрового цикла."""
    class EndFrame(Exception):
        """Остановить бесконечный цикл перед второй итерацией."""

    class FrameClock:
        """Пропустить только первый вызов ограничения скорости."""

        def __init__(self):
            """Начать подсчёт итераций с нуля."""
            self.calls = 0

        def tick(self, speed):
            """Проверить скорость и остановиться после первого кадра."""
            assert speed == game.SPEED
            self.calls += 1
            if self.calls > 1:
                raise EndFrame

    monkeypatch.setattr(game, 'Snake', lambda: snake)
    monkeypatch.setattr(game, 'Apple', lambda: apple)
    monkeypatch.setattr(game, 'clock', FrameClock())
    monkeypatch.setattr(pygame.event, 'get', lambda: [])
    monkeypatch.setattr(apple, 'randomize_position', lambda occupied=(): None)
    with pytest.raises(EndFrame):
        game.main()


def test_eating_grows_immediately(snake, apple, _the_snake, monkeypatch):
    """Поедание яблока сохраняет хвост уже в текущем кадре."""
    apple.position = (340, 240)
    run_one_frame(_the_snake, snake, apple, monkeypatch)
    assert snake.length == len(snake.positions) == 2
    assert snake.positions == [(340, 240), (320, 240)]
    assert snake.last is None


def test_collision_resets_and_clears(snake, apple, _the_snake, monkeypatch):
    """Удар о тело возвращает змейку в центр и стирает старое тело."""
    snake.positions = [(20, 20), (40, 20), (40, 40), (20, 40)]
    snake.length = 4
    snake.direction = _the_snake.RIGHT
    apple.position = (100, 100)
    run_one_frame(_the_snake, snake, apple, monkeypatch)
    assert snake.positions == [(320, 240)]
    assert snake.length == 1
    assert snake.direction == _the_snake.RIGHT
    assert _the_snake.screen.get_at((50, 30))[:3] == (0, 0, 0)


def test_full_board_starts_new_game(snake, apple, _the_snake, monkeypatch):
    """Последнее яблоко перезапускает игру без поиска свободной клетки."""
    snake.positions = [(0, 0)] + [
        (x, y) for x in range(0, 640, 20) for y in range(0, 480, 20)
        if (x, y) not in ((0, 0), (20, 0))
    ]
    snake.length = len(snake.positions)
    apple.position = (20, 0)
    run_one_frame(_the_snake, snake, apple, monkeypatch)
    assert snake.length == 1
    assert snake.positions == [(320, 240)]


def test_close_window(snake, _the_snake, monkeypatch):
    """Закрытие окна завершает игру и вызывает освобождение Pygame."""
    closed = []
    monkeypatch.setattr(pygame, 'quit', lambda: closed.append(True))
    monkeypatch.setattr(pygame.event, 'get', lambda: [
        pygame.event.Event(pygame.QUIT),
    ])
    with pytest.raises(SystemExit):
        _the_snake.handle_keys(snake)
    assert closed == [True]
