# -*- coding: utf-8 -*-
"""
КАРТОЧНЫЕ ИГРЫ - версия 1.1
- Масти рисуются графикой (без юникод-шрифтов)
- Поправлено позиционирование кнопок
- Поправлены пропорции карт в столбцах
"""

import os
import json
import random
import math

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import (Color, Rectangle, Line, RoundedRectangle, Ellipse,
                           Triangle, Mesh)
from kivy.graphics.tesselator import Tesselator
from kivy.core.window import Window
from kivy.clock import Clock


# ============================================================
# СОХРАНЕНИЕ РЕКОРДОВ
# ============================================================

def get_records_file():
    try:
        from android.storage import app_storage_path
        path = app_storage_path()
    except ImportError:
        path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(path, 'cards_records.json')


def load_record(game_key):
    try:
        path = get_records_file()
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get(game_key)
    except Exception:
        pass
    return None


def save_record(seconds, game_key):
    try:
        path = get_records_file()
        data = {}
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[game_key] = seconds
        with open(path, 'w') as f:
            json.dump(data, f)
        return True
    except Exception:
        return False


# ============================================================
# КАРТА
# ============================================================

SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
SUIT_COLORS = {
    'hearts': (0.85, 0.15, 0.15),
    'diamonds': (0.85, 0.15, 0.15),
    'clubs': (0.10, 0.10, 0.10),
    'spades': (0.10, 0.10, 0.10),
}
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.face_up = False

    @property
    def rank_value(self):
        return RANKS.index(self.rank) + 1

    @property
    def color(self):
        return 'red' if self.suit in ('hearts', 'diamonds') else 'black'


def make_deck():
    deck = []
    for suit in SUITS:
        for rank in RANKS:
            deck.append(Card(rank, suit))
    return deck


# ============================================================
# РИСОВАНИЕ МАСТЕЙ ПРИМИТИВАМИ
# ============================================================

def draw_heart(canvas, cx, cy, size, color):
    """Сердце ♥ с центром в (cx,cy) и шириной size."""
    r, g, b = color
    with canvas:
        Color(r, g, b, 1)
        # Два круга сверху
        radius = size * 0.28
        Ellipse(
            pos=(cx - size * 0.5, cy - size * 0.05),
            size=(size * 0.55, size * 0.55)
        )
        Ellipse(
            pos=(cx - size * 0.05, cy - size * 0.05),
            size=(size * 0.55, size * 0.55)
        )
        # Треугольник снизу
        Triangle(points=[
            cx - size * 0.5, cy + size * 0.18,
            cx + size * 0.5, cy + size * 0.18,
            cx, cy - size * 0.55
        ])


def draw_diamond(canvas, cx, cy, size, color):
    """Бубна ♦ - повёрнутый ромб."""
    r, g, b = color
    with canvas:
        Color(r, g, b, 1)
        # 4 треугольника складываются в ромб
        Triangle(points=[
            cx, cy + size * 0.55,         # верх
            cx - size * 0.4, cy,          # лево
            cx + size * 0.4, cy           # право
        ])
        Triangle(points=[
            cx, cy - size * 0.55,         # низ
            cx - size * 0.4, cy,          # лево
            cx + size * 0.4, cy           # право
        ])


def draw_club(canvas, cx, cy, size, color):
    """Трефа ♣ - три круга + ножка."""
    r, g, b = color
    with canvas:
        Color(r, g, b, 1)
        cr = size * 0.30
        # Верхний круг
        Ellipse(
            pos=(cx - cr, cy + size * 0.15),
            size=(cr * 2, cr * 2)
        )
        # Левый круг
        Ellipse(
            pos=(cx - size * 0.45, cy - size * 0.20),
            size=(cr * 2, cr * 2)
        )
        # Правый круг
        Ellipse(
            pos=(cx + size * 0.45 - cr * 2, cy - size * 0.20),
            size=(cr * 2, cr * 2)
        )
        # Ножка - треугольник снизу
        Triangle(points=[
            cx - size * 0.20, cy - size * 0.10,
            cx + size * 0.20, cy - size * 0.10,
            cx, cy - size * 0.55
        ])


def draw_spade(canvas, cx, cy, size, color):
    """Пика ♠ - перевёрнутое сердце + ножка."""
    r, g, b = color
    with canvas:
        Color(r, g, b, 1)
        # Два круга снизу (перевёрнутое сердце)
        Ellipse(
            pos=(cx - size * 0.5, cy - size * 0.45),
            size=(size * 0.55, size * 0.55)
        )
        Ellipse(
            pos=(cx - size * 0.05, cy - size * 0.45),
            size=(size * 0.55, size * 0.55)
        )
        # Треугольник сверху
        Triangle(points=[
            cx - size * 0.5, cy - size * 0.20,
            cx + size * 0.5, cy - size * 0.20,
            cx, cy + size * 0.55
        ])
        # Ножка снизу
        Triangle(points=[
            cx - size * 0.20, cy - size * 0.50,
            cx + size * 0.20, cy - size * 0.50,
            cx, cy - size * 0.70
        ])


def draw_suit(canvas, suit, cx, cy, size, color):
    """Универсальная функция - рисует масть."""
    if suit == 'hearts':
        draw_heart(canvas, cx, cy, size, color)
    elif suit == 'diamonds':
        draw_diamond(canvas, cx, cy, size, color)
    elif suit == 'clubs':
        draw_club(canvas, cx, cy, size, color)
    elif suit == 'spades':
        draw_spade(canvas, cx, cy, size, color)


# ============================================================
# РИСОВАНИЕ КАРТЫ
# ============================================================

def draw_card_canvas(canvas, card, x, y, w, h, selected=False):
    """Рисует фон карты + если открыта - масть в углу и в центре."""
    radius = w * 0.08

    with canvas:
        # Чёрная рамка
        Color(0.10, 0.10, 0.10, 1)
        RoundedRectangle(pos=(x, y), size=(w, h), radius=[radius])

        if not card.face_up:
            # === РУБАШКА ===
            Color(0.20, 0.35, 0.65, 1)
            RoundedRectangle(
                pos=(x + 2, y + 2),
                size=(w - 4, h - 4),
                radius=[radius]
            )
            # Узор - сетка крестиков
            Color(0.40, 0.55, 0.80, 1)
            margin_x = w * 0.12
            margin_y = h * 0.12
            for i in range(3):
                for j in range(5):
                    cx = x + margin_x + (w - 2 * margin_x) * (i + 0.5) / 3
                    cy = y + margin_y + (h - 2 * margin_y) * (j + 0.5) / 5
                    sz = w * 0.04
                    Rectangle(pos=(cx - sz, cy - sz * 0.2),
                              size=(sz * 2, sz * 0.4))
                    Rectangle(pos=(cx - sz * 0.2, cy - sz),
                              size=(sz * 0.4, sz * 2))
        else:
            # === ЛИЦО ===
            if selected:
                Color(1.0, 0.95, 0.6, 1)
            else:
                Color(0.99, 0.97, 0.92, 1)
            RoundedRectangle(
                pos=(x + 2, y + 2),
                size=(w - 4, h - 4),
                radius=[radius]
            )
            if selected:
                Color(1.0, 0.55, 0.0, 1)
                inset = max(3.0, w * 0.05)
                Line(rounded_rectangle=(
                    x + inset, y + inset,
                    w - 2 * inset, h - 2 * inset,
                    radius * 0.7
                ), width=max(2.5, w * 0.05))

    # Если открыта - рисуем масть в углу и в центре
    if card.face_up:
        suit_color = SUIT_COLORS[card.suit]
        # Маленькая масть в ПРАВОМ верхнем углу
        # (видна когда карта перекрыта другой картой в столбце,
        #  не наезжает на ранг даже у "10")
        small_size = w * 0.20
        small_cy = y + h * 0.83
        small_cx = x + w * 0.80   # правый верхний угол
        draw_suit(canvas, card.suit, small_cx, small_cy, small_size, suit_color)
        # Большая масть в центре карты
        big_size = w * 0.50
        big_cx = x + w * 0.5
        big_cy = y + h * 0.35
        draw_suit(canvas, card.suit, big_cx, big_cy, big_size, suit_color)


def make_card_rank_label(card, x, y, w, h):
    """Лейбл с рангом (числом или буквой) в верхней части карты.
    Масти рисуются графикой - не нужны лейблы для них."""
    if not card.face_up:
        return None
    r, g, b = SUIT_COLORS[card.suit]
    # Ранг - вверху по левому краю карты, поверх масти
    rank_font = max(16, int(h * 0.22))
    rank_lbl = Label(
        text=card.rank,
        font_size=rank_font,
        bold=True,
        color=(r, g, b, 1),
        size_hint=(None, None),
        size=(w * 0.35, h * 0.20),
        pos=(x + w * 0.03, y + h * 0.78)
    )
    return rank_lbl


# ============================================================
# СТОПКА
# ============================================================

class Pile:
    def __init__(self, name):
        self.name = name
        self.cards = []

    def push(self, card):
        self.cards.append(card)

    def pop(self):
        return self.cards.pop() if self.cards else None

    def top(self):
        return self.cards[-1] if self.cards else None

    def is_empty(self):
        return len(self.cards) == 0

    def __len__(self):
        return len(self.cards)


# ============================================================
# КОСЫНКА - игровая логика
# ============================================================

class KlondikeGame:
    def __init__(self):
        self.tableau = [Pile('t' + str(i)) for i in range(7)]
        self.foundations = [Pile('f' + str(i)) for i in range(4)]
        self.stock = Pile('stock')
        self.waste = Pile('waste')
        self.history = []
        self.elapsed_seconds = 0
        self.timer_running = True
        self.game_over = False
        self.deal()

    def deal(self):
        deck = make_deck()
        random.shuffle(deck)
        idx = 0
        for i in range(7):
            for j in range(i + 1):
                card = deck[idx]
                idx += 1
                if j == i:
                    card.face_up = True
                self.tableau[i].push(card)
        for i in range(idx, len(deck)):
            deck[i].face_up = False
            self.stock.push(deck[i])

    def can_place_on_tableau(self, card, pile):
        if pile.is_empty():
            return card.rank == 'K'
        top = pile.top()
        if not top.face_up:
            return False
        if card.color == top.color:
            return False
        return card.rank_value == top.rank_value - 1

    def can_place_on_foundation(self, card, pile):
        if pile.is_empty():
            return card.rank == 'A'
        top = pile.top()
        if card.suit != top.suit:
            return False
        return card.rank_value == top.rank_value + 1

    def draw_from_stock(self):
        if not self.stock.is_empty():
            card = self.stock.pop()
            card.face_up = True
            self.waste.push(card)
            self.history.append(('draw', card))
        else:
            moved = []
            while not self.waste.is_empty():
                c = self.waste.pop()
                c.face_up = False
                self.stock.push(c)
                moved.append(c)
            if moved:
                self.history.append(('recycle', moved))

    def find_movable_sequence(self, pile, card):
        if not card.face_up:
            return -1
        try:
            idx = pile.cards.index(card)
        except ValueError:
            return -1
        for i in range(idx, len(pile.cards) - 1):
            cur = pile.cards[i]
            nxt = pile.cards[i + 1]
            if not cur.face_up or not nxt.face_up:
                return -1
            if cur.color == nxt.color:
                return -1
            if cur.rank_value != nxt.rank_value + 1:
                return -1
        return idx

    def move_card(self, src_pile, src_idx, dst_pile):
        if src_idx < 0 or src_idx >= len(src_pile.cards):
            return False
        moving = src_pile.cards[src_idx:]
        first = moving[0]
        if dst_pile.name.startswith('f'):
            if len(moving) != 1:
                return False
            if not self.can_place_on_foundation(first, dst_pile):
                return False
        else:
            if not self.can_place_on_tableau(first, dst_pile):
                return False
        flipped = False
        src_pile.cards = src_pile.cards[:src_idx]
        for c in moving:
            dst_pile.push(c)
        if src_pile.name.startswith('t') and not src_pile.is_empty():
            top = src_pile.top()
            if not top.face_up:
                top.face_up = True
                flipped = True
        self.history.append(('move', src_pile, dst_pile, len(moving), flipped))
        return True

    def auto_to_foundation(self, src_pile):
        if src_pile.is_empty():
            return False
        card = src_pile.top()
        if not card.face_up:
            return False
        for f in self.foundations:
            if self.can_place_on_foundation(card, f):
                src_idx = len(src_pile.cards) - 1
                return self.move_card(src_pile, src_idx, f)
        return False

    def undo(self):
        if not self.history:
            return False
        action = self.history.pop()
        kind = action[0]
        if kind == 'draw':
            card = action[1]
            self.waste.pop()
            card.face_up = False
            self.stock.push(card)
        elif kind == 'recycle':
            moved = action[1]
            for _ in moved:
                c = self.stock.pop()
                c.face_up = True
                self.waste.push(c)
        elif kind == 'move':
            _, src_pile, dst_pile, count, flipped = action
            if flipped and src_pile.cards:
                src_pile.top().face_up = False
            moving = dst_pile.cards[-count:]
            dst_pile.cards = dst_pile.cards[:-count]
            for c in moving:
                src_pile.push(c)
        return True

    def is_won(self):
        return all(len(f) == 13 for f in self.foundations)


# ============================================================
# АНИМАЦИЯ ПОБЕДЫ - "прыгающие карты" в стиле классики Windows
# ============================================================

class WinAnimation(Widget):
    """Поверх поля. Карты по очереди вылетают из 4 фундаментов,
    падают вниз с гравитацией, отскакивают от нижнего края, оставляя след.
    Холст не чистится между кадрами - след копится сам собой.
    """

    # Сколько карт всего пускаем
    TOTAL_CARDS = 24
    # Интервал запуска новой карты в секундах
    LAUNCH_INTERVAL = 0.20
    # Интервал отрисовки кадра
    FRAME_INTERVAL = 1 / 30.0
    # Гравитация (пикс/сек^2) и затухание при отскоке
    GRAVITY = 1400.0
    BOUNCE_DAMP = 0.65
    # Минимальная скорость отскока - ниже этого карта улетает за пределы
    MIN_BOUNCE_VY = 120.0

    def __init__(self, foundations_xy, card_w, card_h, on_finished, **kwargs):
        super().__init__(**kwargs)
        # Стартовые позиции - 4 фундамента (x, y) в координатах родителя
        self._foundations_xy = list(foundations_xy)
        self._card_w = card_w
        self._card_h = card_h
        self._on_finished = on_finished

        # Очередь карт для запуска - перемешанная колода
        self._queue = []
        for suit in SUITS:
            for rank in RANKS:
                c = Card(rank, suit)
                c.face_up = True
                self._queue.append(c)
        random.shuffle(self._queue)
        self._queue = self._queue[:self.TOTAL_CARDS]

        # Активные летящие карты: список dict с x, y, vx, vy, card
        self._flying = []
        # Какой фундамент использовать для следующего запуска
        self._next_foundation = 0
        # Накопленное время до следующего запуска
        self._launch_acc = 0.0
        # Флаг что анимация запущена
        self._running = False
        self._launch_event = None
        self._frame_event = None
        # Сколько ударов о пол сделала каждая карта (после N - удаляем)
        self._max_bounces = 2

    def start(self):
        if self._running:
            return
        self._running = True
        # Очищаем холст один раз в начале
        self.canvas.clear()
        self._frame_event = Clock.schedule_interval(self._tick, self.FRAME_INTERVAL)
        # Аварийная страховка - через 25 сек попап появится сам
        Clock.schedule_once(self._safety_finish, 25.0)
        # Подсказка "Тапни" чтоб мама знала что делать
        hint = Label(
            text='[ нажми на экран ]',
            font_size=28,
            bold=True,
            color=(1, 1, 0.7, 1),
            size_hint=(None, None),
            size=(self.width, 50),
            pos=(self.x, self.y + self.height - 80)
        )
        self.add_widget(hint)

    def _safety_finish(self, dt):
        # Аварийная страховка - если за 25 сек попап не появился, показать сам
        if self._on_finished:
            cb = self._on_finished
            self._on_finished = None
            self.stop()
            cb()

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._frame_event:
            self._frame_event.cancel()
            self._frame_event = None
        self._flying = []

    def _launch_one(self):
        """Запустить одну карту из очередного фундамента."""
        if not self._queue:
            return
        card = self._queue.pop(0)
        fx, fy = self._foundations_xy[self._next_foundation % 4]
        self._next_foundation += 1
        # Случайный начальный импульс - влево или вправо
        direction = random.choice([-1, 1])
        vx = direction * random.uniform(120, 320)
        vy = random.uniform(-50, 50)  # лёгкий толчок вверх/вниз
        self._flying.append({
            'x': float(fx),
            'y': float(fy),
            'vx': vx,
            'vy': vy,
            'card': card,
            'bounces': 0,
        })

    def _tick(self, dt):
        if not self._running:
            return
        # Запуск новых карт
        self._launch_acc += dt
        while self._launch_acc >= self.LAUNCH_INTERVAL and self._queue:
            self._launch_acc -= self.LAUNCH_INTERVAL
            self._launch_one()

        # Обновляем физику и рисуем СЛЕД (canvas НЕ чистим)
        floor_y = self.y
        left_x = self.x
        right_x = self.x + self.width

        still_flying = []
        for f in self._flying:
            # Физика
            f['vy'] -= self.GRAVITY * dt  # гравитация тянет вниз (y уменьшается)
            f['x'] += f['vx'] * dt
            f['y'] += f['vy'] * dt

            # Отскок от пола
            if f['y'] <= floor_y:
                f['y'] = floor_y
                if abs(f['vy']) < self.MIN_BOUNCE_VY:
                    # энергия кончилась - последний раз нарисуем и удалим
                    f['bounces'] = self._max_bounces
                else:
                    f['vy'] = -f['vy'] * self.BOUNCE_DAMP
                    f['vx'] *= 0.92
                    f['bounces'] += 1

            # Рисуем карту в текущей позиции (НЕ очищая прошлые!)
            draw_card_canvas(self.canvas, f['card'],
                             f['x'], f['y'],
                             self._card_w, self._card_h)
            # Лейбл с рангом не добавляем (Label-виджеты накапливать дорого);
            # масти и так нарисованы графикой в draw_card_canvas, а ранг
            # будет виден частично - для эффекта "следа" этого достаточно.

            # Если карта улетела далеко за края или сделала достаточно прыжков -
            # снимаем её с симуляции (но след остаётся на холсте)
            if (f['bounces'] < self._max_bounces and
                    f['x'] > left_x - self._card_w * 2 and
                    f['x'] < right_x + self._card_w):
                still_flying.append(f)

        self._flying = still_flying

        # Условие окончания: очередь пуста и все карты отлетали
        if not self._queue and not self._flying:
            # анимация завершилась сама собой - но не закрываем,
            # ждём тап пользователя
            if self._frame_event:
                self._frame_event.cancel()
                self._frame_event = None

    def on_touch_down(self, touch):
        # Любой тап в любом состоянии - сразу показываем попап
        self.stop()
        if self._on_finished:
            cb = self._on_finished
            self._on_finished = None
            cb()
        return True


# ============================================================
# ПОЛЕ КОСЫНКИ
# ============================================================

class KlondikeBoard(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.selected_pile = None
        self.selected_idx = None
        self.last_tap_time = 0
        self.last_tap_target = None
        self._labels = []
        self._win_anim = None  # активная анимация победы (если есть)
        self.bind(size=self._redraw, pos=self._redraw)
        self.restart()
        Clock.schedule_interval(self._tick_timer, 1)

    def restart(self):
        # Если осталась анимация от прошлой партии - убираем
        if self._win_anim is not None:
            try:
                self._win_anim.stop()
                if self._win_anim.parent:
                    self._win_anim.parent.remove_widget(self._win_anim)
            except Exception:
                pass
            self._win_anim = None
        self.game = KlondikeGame()
        self.selected_pile = None
        self.selected_idx = None
        self._redraw()

    def _tick_timer(self, dt):
        if self.game and self.game.timer_running and not self.game.game_over:
            self.game.elapsed_seconds += 1

    def _layout(self):
        # Топбар сверху - 8% высоты
        topbar_h = self.height * 0.08
        # Боковые отступы побольше чтоб карты были не такие широкие
        margin = self.width * 0.015
        gap = self.width * 0.008
        card_w = (self.width - 2 * margin - 6 * gap) / 7
        # Высота карт - 1.45 от ширины (стандартная карточная пропорция)
        card_h = card_w * 1.45

        # Зазор между топбаром и верхним рядом карт
        gap_top = self.height * 0.015
        # Верхний ряд (foundations + stock + waste)
        top_y = self.y + self.height - topbar_h - gap_top - card_h

        layout = {
            'card_w': card_w,
            'card_h': card_h,
            'gap': gap,
            'foundations': [],
            'stock': None,
            'waste': None,
            'tableau': [],
        }
        # 4 фундамента слева
        for i in range(4):
            fx = self.x + margin + i * (card_w + gap)
            layout['foundations'].append((fx, top_y))
        # Stock и waste справа
        stock_x = self.x + self.width - margin - card_w
        waste_x = stock_x - card_w - gap
        layout['waste'] = (waste_x, top_y)
        layout['stock'] = (stock_x, top_y)

        # 7 столбцов с большим зазором от верхнего ряда (чтоб не перекрывали)
        tableau_top = top_y - card_h * 1.15
        for i in range(7):
            tx = self.x + margin + i * (card_w + gap)
            layout['tableau'].append((tx, tableau_top))

        return layout

    def _calc_steps(self, pile, ty, ch, face_down_step, face_up_step):
        """Высчитать шаги между картами в столбце с учётом доступной высоты."""
        if len(pile.cards) <= 1:
            return []
        steps = []
        for c in pile.cards[:-1]:
            steps.append(face_down_step if not c.face_up else face_up_step)
        total_h = sum(steps) + ch
        available = ty - self.y - ch * 0.1
        if total_h > available and available > ch:
            scale = (available - ch) / (total_h - ch) if total_h > ch else 1.0
            scale = max(0.3, scale)
            steps = [s * scale for s in steps]
        return steps

    def _redraw(self, *args):
        if not self.game:
            return
        self.canvas.clear()
        for lbl in self._labels:
            self.remove_widget(lbl)
        self._labels = []

        layout = self._layout()
        cw, ch = layout['card_w'], layout['card_h']

        with self.canvas:
            Color(0.08, 0.25, 0.15, 1)
            for fx, fy in layout['foundations']:
                Line(rounded_rectangle=(fx, fy, cw, ch, cw * 0.08), width=1.5)
            sx, sy = layout['stock']
            Line(rounded_rectangle=(sx, sy, cw, ch, cw * 0.08), width=1.5)
            wx, wy = layout['waste']
            Line(rounded_rectangle=(wx, wy, cw, ch, cw * 0.08), width=1.5)
            for tx, ty in layout['tableau']:
                Line(rounded_rectangle=(tx, ty, cw, ch, cw * 0.08), width=1.5)

        # Фундаменты
        for i, (fx, fy) in enumerate(layout['foundations']):
            f = self.game.foundations[i]
            if not f.is_empty():
                top = f.top()
                draw_card_canvas(self.canvas, top, fx, fy, cw, ch)
                lbl = make_card_rank_label(top, fx, fy, cw, ch)
                if lbl:
                    self._labels.append(lbl)
            else:
                # Иконка масти-плейсхолдера? Пока просто пусто
                pass

        # Stock
        sx, sy = layout['stock']
        if not self.game.stock.is_empty():
            fake = Card('A', 'spades')
            fake.face_up = False
            draw_card_canvas(self.canvas, fake, sx, sy, cw, ch)
            cnt_lbl = Label(
                text=str(len(self.game.stock)),
                font_size=max(20, int(ch * 0.30)),
                bold=True,
                color=(1, 1, 1, 1),
                size_hint=(None, None),
                size=(cw, ch * 0.4),
                pos=(sx, sy + ch * 0.30)
            )
            self._labels.append(cnt_lbl)
        else:
            recycle_lbl = Label(
                text='RE',
                font_size=max(28, int(ch * 0.50)),
                bold=True,
                color=(0.7, 0.7, 0.7, 1),
                size_hint=(None, None),
                size=(cw, ch),
                pos=(sx, sy)
            )
            self._labels.append(recycle_lbl)

        # Waste
        wx, wy = layout['waste']
        if not self.game.waste.is_empty():
            top = self.game.waste.top()
            sel = (self.selected_pile is self.game.waste)
            draw_card_canvas(self.canvas, top, wx, wy, cw, ch, selected=sel)
            lbl = make_card_rank_label(top, wx, wy, cw, ch)
            if lbl:
                self._labels.append(lbl)

        # Tableau
        face_down_step = ch * 0.10
        face_up_step = ch * 0.24
        for i, (tx, ty) in enumerate(layout['tableau']):
            pile = self.game.tableau[i]
            if pile.is_empty():
                continue
            steps = self._calc_steps(pile, ty, ch, face_down_step, face_up_step)
            cy = ty
            for j, card in enumerate(pile.cards):
                sel = (self.selected_pile is pile and self.selected_idx is not None
                       and j >= self.selected_idx)
                draw_card_canvas(self.canvas, card, tx, cy, cw, ch, selected=sel)
                if card.face_up:
                    lbl = make_card_rank_label(card, tx, cy, cw, ch)
                    if lbl:
                        self._labels.append(lbl)
                if j < len(pile.cards) - 1:
                    cy -= steps[j]

        for lbl in self._labels:
            self.add_widget(lbl)

    def _hit_test(self, pos):
        layout = self._layout()
        cw, ch = layout['card_w'], layout['card_h']
        x, y = pos

        sx, sy = layout['stock']
        if sx <= x <= sx + cw and sy <= y <= sy + ch:
            return (self.game.stock, -1)

        wx, wy = layout['waste']
        if wx <= x <= wx + cw and wy <= y <= wy + ch:
            if not self.game.waste.is_empty():
                return (self.game.waste, len(self.game.waste.cards) - 1)
            return (self.game.waste, -2)

        for i, (fx, fy) in enumerate(layout['foundations']):
            if fx <= x <= fx + cw and fy <= y <= fy + ch:
                f = self.game.foundations[i]
                if f.is_empty():
                    return (f, -2)
                return (f, len(f.cards) - 1)

        face_down_step = ch * 0.10
        face_up_step = ch * 0.24
        for i, (tx, ty) in enumerate(layout['tableau']):
            pile = self.game.tableau[i]
            if not (tx <= x <= tx + cw):
                continue
            if pile.is_empty():
                if ty <= y <= ty + ch:
                    return (pile, -2)
                continue
            steps = self._calc_steps(pile, ty, ch, face_down_step, face_up_step)
            # Считаем позицию каждой карты, потом ищем самую нижнюю под пальцем
            card_positions = []
            cy = ty
            for j, card in enumerate(pile.cards):
                card_positions.append(cy)
                if j < len(pile.cards) - 1:
                    cy -= steps[j]
            # Идём с КОНЦА (нижняя карта стека = последняя в списке = верхняя по факту)
            # Картa j занимает прямоугольник (tx, card_positions[j], cw, ch)
            # Но видна только верхняя полоска кроме последней которая видна вся
            hit_idx = -1
            for j in range(len(pile.cards) - 1, -1, -1):
                cy = card_positions[j]
                if cy <= y <= cy + ch:
                    hit_idx = j
                    break
            if hit_idx >= 0:
                return (pile, hit_idx)
        return (None, None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self.game.game_over:
            return True

        import time
        now = time.time()
        is_double = (now - self.last_tap_time < 0.4)
        self.last_tap_time = now

        pile, idx = self._hit_test(touch.pos)
        if pile is None:
            self.selected_pile = None
            self.selected_idx = None
            self._redraw()
            return True

        if pile is self.game.stock:
            self.game.draw_from_stock()
            self.selected_pile = None
            self.selected_idx = None
            self._redraw()
            self._check_win()
            return True

        if is_double and self.last_tap_target == (pile, idx):
            if pile is not self.game.stock and (pile.name.startswith('t')
                                                or pile.name == 'waste'):
                if self.game.auto_to_foundation(pile):
                    self.selected_pile = None
                    self.selected_idx = None
                    self._redraw()
                    self._check_win()
                    self.last_tap_target = None
                    return True
        self.last_tap_target = (pile, idx)

        if self.selected_pile is None:
            if idx == -2 or idx == -1:
                return True
            card = pile.cards[idx]
            if not card.face_up:
                return True
            if pile.name.startswith('t'):
                seq_idx = self.game.find_movable_sequence(pile, card)
                if seq_idx < 0:
                    return True
                self.selected_pile = pile
                self.selected_idx = seq_idx
            else:
                if idx != len(pile.cards) - 1:
                    return True
                self.selected_pile = pile
                self.selected_idx = idx
            self._redraw()
        else:
            if pile is self.selected_pile:
                self.selected_pile = None
                self.selected_idx = None
                self._redraw()
                return True
            ok = self.game.move_card(self.selected_pile, self.selected_idx, pile)
            self.selected_pile = None
            self.selected_idx = None
            self._redraw()
            if ok:
                self._check_win()
        return True

    def _check_win(self):
        if self.game.is_won():
            self.game.game_over = True
            self.game.timer_running = False
            current_record = load_record('klondike')
            if current_record is None or self.game.elapsed_seconds < current_record:
                save_record(self.game.elapsed_seconds, 'klondike')
            # Сначала запускаем анимацию "прыгающих карт",
            # попап покажется когда пользователь тапнет по экрану
            self._start_win_animation()

    def _start_win_animation(self):
        """Запустить анимацию победы поверх поля."""
        layout = self._layout()
        # Координаты 4 фундаментов - там стартуют карты
        foundations_xy = list(layout['foundations'])
        cw = layout['card_w']
        ch = layout['card_h']

        # Создаём виджет анимации поверх board, на весь board
        anim = WinAnimation(
            foundations_xy=foundations_xy,
            card_w=cw,
            card_h=ch,
            on_finished=self._show_win_popup,
            size=self.size,
            pos=self.pos,
        )
        # Убираем подсветку выделения чтоб не отвлекало
        self.selected_pile = None
        self.selected_idx = None
        # Прячем рекордную панельку и выделение - просто перерисуем поле
        self._redraw()
        # Добавляем анимацию поверх board
        self.add_widget(anim)
        self._win_anim = anim
        anim.start()

    def _show_win_popup(self):
        # Убираем виджет анимации (с накопленным следом) с экрана
        if self._win_anim is not None:
            try:
                self._win_anim.stop()
                if self._win_anim.parent:
                    self._win_anim.parent.remove_widget(self._win_anim)
            except Exception:
                pass
            self._win_anim = None
        m = self.game.elapsed_seconds // 60
        s = self.game.elapsed_seconds % 60
        content = BoxLayout(orientation='vertical', spacing=20, padding=20)
        content.add_widget(Label(
            text='ПОБЕДА!\nВремя: ' + str(m).zfill(2) + ':' + str(s).zfill(2),
            font_size=40,
            bold=True,
            halign='center'
        ))
        btn = Button(
            text='Новая партия',
            font_size=32,
            size_hint=(1, 0.4),
            background_color=(0.3, 0.7, 0.4, 1)
        )
        content.add_widget(btn)
        popup = Popup(
            title='',
            content=content,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        btn.bind(on_release=lambda *a: (popup.dismiss(), self.restart()))
        popup.open()


# ============================================================
# ПРЕВЬЮ ИГРЫ В МЕНЮ
# ============================================================

class CardGamePreview(Widget):
    def __init__(self, game_key, **kwargs):
        super().__init__(**kwargs)
        self.game_key = game_key
        self.bind(size=self._redraw, pos=self._redraw)

    def _redraw(self, *a):
        self.canvas.clear()
        for child in list(self.children):
            self.remove_widget(child)
        if self.width <= 0 or self.height <= 0:
            return
        ch = self.height * 0.7
        cw = ch / 1.4
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2 - ch / 2
        if self.game_key == 'spider':
            # Паук - все пики
            sample_cards = [
                Card('A', 'spades'),
                Card('K', 'spades'),
                Card('Q', 'spades'),
            ]
        else:
            sample_cards = [
                Card('A', 'spades'),
                Card('K', 'hearts'),
                Card('Q', 'clubs'),
            ]
        for c in sample_cards:
            c.face_up = True
        offsets = [-cw * 0.55, 0, cw * 0.55]
        for i, c in enumerate(sample_cards):
            x = cx + offsets[i] - cw / 2
            y = cy - i * 3
            draw_card_canvas(self.canvas, c, x, y, cw, ch)
            lbl = make_card_rank_label(c, x, y, cw, ch)
            if lbl:
                self.add_widget(lbl)


# ============================================================
# ПУНКТ МЕНЮ
# ============================================================

class CardGameMenuItem(BoxLayout):
    def __init__(self, name, key, available, on_select, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.name = name
        self.key = key
        self.available = available
        self.on_select = on_select
        self.size_hint_y = None
        self.height = 240
        self.padding = 20
        self.spacing = 20
        self._last_tap = 0

        with self.canvas.before:
            if available:
                self._bg_color = Color(0.20, 0.45, 0.30, 0.7)
            else:
                self._bg_color = Color(0.30, 0.30, 0.30, 0.5)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(size=self._update_bg, pos=self._update_bg)

        self.preview = CardGamePreview(key, size_hint_x=0.4)
        self.add_widget(self.preview)

        text_box = BoxLayout(orientation='vertical', size_hint_x=0.6)
        name_label = Label(
            text=name,
            font_size=44,
            bold=True,
            color=(1, 1, 1, 1) if available else (0.7, 0.7, 0.7, 1),
            halign='left',
            valign='middle'
        )
        name_label.bind(size=lambda l, s: setattr(l, 'text_size', s))
        text_box.add_widget(name_label)

        if available:
            record = load_record(key)
            if record is not None:
                m = record // 60
                s = record % 60
                rec_text = 'РЕКОРД  ' + str(m).zfill(2) + ':' + str(s).zfill(2)
            else:
                rec_text = 'РЕКОРД  --:--'
        else:
            rec_text = 'Скоро...'
        record_label = Label(
            text=rec_text,
            font_size=42,
            bold=True,
            color=(1.0, 0.95, 0.4, 1) if available else (0.6, 0.6, 0.6, 1),
            halign='left',
            valign='middle'
        )
        record_label.bind(size=lambda l, s: setattr(l, 'text_size', s))
        text_box.add_widget(record_label)

        self.add_widget(text_box)

    def _update_bg(self, *a):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if not self.available:
            return True
        import time
        now = time.time()
        if now - self._last_tap < 0.5:
            self.on_select(self.key)
            self._last_tap = 0
        else:
            self._last_tap = now
        return True


# ============================================================
# ПАУК - игровая логика (1 масть)
# ============================================================

class SpiderGame:
    """Состояние партии Паука с одной мастью.
    104 карты = 8 комплектов по 13 карт (все пики).
    10 столбцов внизу, 5 раздач из колоды по 10 карт.
    Цель - собрать 8 комплектов от Короля до Туза.
    """

    NUM_COLUMNS = 10
    NUM_DEALS = 5  # сколько раз можно раздать из колоды
    NUM_SETS = 8   # сколько комплектов нужно собрать

    def __init__(self):
        # 10 столбцов
        self.tableau = [Pile('t' + str(i)) for i in range(self.NUM_COLUMNS)]
        # Колода (откуда раздаём)
        self.stock = Pile('stock')
        # Копилка - сколько комплектов собрано (просто счётчик)
        self.completed = 0
        # История ходов для отмены
        self.history = []
        # Время и состояние
        self.elapsed_seconds = 0
        self.timer_running = True
        self.game_over = False
        self.deal()

    def deal(self):
        """Раздаёт новую партию."""
        # 8 комплектов по 13 карт = 104 карты, все пики
        deck = []
        for _ in range(8):
            for rank in RANKS:
                deck.append(Card(rank, 'spades'))
        random.shuffle(deck)

        # Сначала 54 карты в столбцы:
        # первые 4 столбца получают по 6 карт, остальные 6 - по 5
        for i in range(self.NUM_COLUMNS):
            count = 6 if i < 4 else 5
            for j in range(count):
                card = deck.pop()
                # Последняя карта в столбце - открыта, остальные - закрыты
                card.face_up = (j == count - 1)
                self.tableau[i].push(card)

        # Остальные 50 карт - в колоду
        for card in deck:
            card.face_up = False
            self.stock.push(card)

    def can_place_on_tableau(self, card, pile):
        """В Пауке на столбец можно класть любую карту по убыванию,
        а на пустой - вообще что угодно. Масть для размещения не важна."""
        if pile.is_empty():
            return True
        top = pile.top()
        if not top.face_up:
            return False
        return card.rank_value == top.rank_value - 1

    def is_valid_sequence(self, cards):
        """Проверить что список карт - валидная последовательность по убыванию,
        одной масти (для перетаскивания всей пачкой).
        В нашем случае масть всегда одна - пики, проверяем только убывание."""
        if len(cards) <= 1:
            return True
        for i in range(len(cards) - 1):
            if not cards[i].face_up:
                return False
            if cards[i].rank_value != cards[i + 1].rank_value + 1:
                return False
            if cards[i].suit != cards[i + 1].suit:
                return False
        if not cards[-1].face_up:
            return False
        return True

    def find_movable_sequence(self, pile, card):
        """От указанной карты вниз - вернуть индекс начала, если эту пачку
        можно перетаскивать (она формирует валидную последовательность)."""
        if not card.face_up:
            return -1
        idx = pile.cards.index(card)
        seq = pile.cards[idx:]
        if self.is_valid_sequence(seq):
            return idx
        return -1

    def move_sequence(self, src_pile, src_idx, dst_pile):
        """Переложить пачку карт из src_pile (с индекса src_idx) на dst_pile."""
        if src_pile is dst_pile:
            return False
        seq = src_pile.cards[src_idx:]
        if not self.is_valid_sequence(seq):
            return False
        first = seq[0]
        if not self.can_place_on_tableau(first, dst_pile):
            return False

        # Сохраняем для undo
        snapshot = self._snapshot()

        # Перемещаем
        moved = src_pile.cards[src_idx:]
        src_pile.cards = src_pile.cards[:src_idx]
        for c in moved:
            dst_pile.push(c)

        # Открываем верхнюю в источнике
        flipped = False
        if src_pile.cards and not src_pile.top().face_up:
            src_pile.top().face_up = True
            flipped = True

        self.history.append(snapshot)

        # Пробуем авто-сбор комплекта
        self._auto_collect(dst_pile)
        return True

    def _auto_collect(self, pile):
        """Если в столбце сверху лежит полный комплект К-Д-...-A одной масти
        подряд, отправить его в копилку."""
        if len(pile.cards) < 13:
            return
        last_13 = pile.cards[-13:]
        if not self.is_valid_sequence(last_13):
            return
        # Должно начинаться с K и заканчиваться A
        if last_13[0].rank != 'K' or last_13[-1].rank != 'A':
            return
        # Все одной масти (для одной масти всегда так, но всё же)
        suits = set(c.suit for c in last_13)
        if len(suits) != 1:
            return
        # Снимаем 13 карт с верха столбца
        del pile.cards[-13:]
        self.completed += 1
        # Открываем верхнюю
        if pile.cards and not pile.top().face_up:
            pile.top().face_up = True

    def deal_from_stock(self):
        """Раздать по одной карте в каждый из 10 столбцов.
        Запрещено если хоть один столбец пуст."""
        if self.stock.is_empty():
            return False
        # Проверяем что нет пустых столбцов
        for col in self.tableau:
            if col.is_empty():
                return False
        # Карт в колоде должно быть >= 10
        if len(self.stock) < self.NUM_COLUMNS:
            return False

        snapshot = self._snapshot()
        for i in range(self.NUM_COLUMNS):
            card = self.stock.pop()
            card.face_up = True
            self.tableau[i].push(card)
        self.history.append(snapshot)

        # После раздачи может в каком-то столбце оказаться комплект
        for col in self.tableau:
            self._auto_collect(col)
        return True

    def _snapshot(self):
        """Сохранить состояние для undo."""
        snap = {
            'tableau': [
                [(c.rank, c.suit, c.face_up) for c in col.cards]
                for col in self.tableau
            ],
            'stock': [(c.rank, c.suit, c.face_up) for c in self.stock.cards],
            'completed': self.completed,
        }
        return snap

    def undo(self):
        """Откатить последний ход."""
        if not self.history:
            return False
        snap = self.history.pop()
        for i, col_data in enumerate(snap['tableau']):
            self.tableau[i].cards = []
            for rank, suit, face_up in col_data:
                c = Card(rank, suit)
                c.face_up = face_up
                self.tableau[i].push(c)
        self.stock.cards = []
        for rank, suit, face_up in snap['stock']:
            c = Card(rank, suit)
            c.face_up = face_up
            self.stock.push(c)
        self.completed = snap['completed']
        return True

    def find_hint(self):
        """Подсказка: ищем самый полезный ход.
        Приоритет:
        1. Ход, который освобождает столбец
        2. Ход, который открывает закрытую карту
        3. Любой ход, удлиняющий последовательность одной масти
        4. Любой валидный ход
        Возвращает (src_pile, src_idx, dst_pile) или None.
        """
        candidates = []  # (приоритет, src, idx, dst)

        for src in self.tableau:
            if src.is_empty():
                continue
            # Перебираем все возможные начальные индексы валидной пачки
            for idx in range(len(src.cards)):
                if not src.cards[idx].face_up:
                    continue
                seq = src.cards[idx:]
                if not self.is_valid_sequence(seq):
                    continue
                first = seq[0]

                for dst in self.tableau:
                    if dst is src:
                        continue
                    if not self.can_place_on_tableau(first, dst):
                        continue
                    # Не предлагаем перекладывать на пустой столбец одну
                    # последовательность из того же столбца если он
                    # после этого станет пустым - бессмысленный ход
                    if dst.is_empty() and idx == 0:
                        # столбец-источник станет пустым - двигаем впустую
                        continue

                    # Считаем приоритет
                    priority = 0
                    # Освобождение столбца
                    if idx == 0:
                        priority += 100
                    # Открытие закрытой карты
                    if idx > 0 and not src.cards[idx - 1].face_up:
                        priority += 80
                    # Удлинение последовательности одной масти на dst
                    if not dst.is_empty():
                        top = dst.top()
                        if top.suit == first.suit:
                            priority += 30
                    # Базовый ход
                    priority += 1
                    candidates.append((priority, src, idx, dst))

        if not candidates:
            return None
        # Берём ход с максимальным приоритетом
        candidates.sort(key=lambda x: -x[0])
        _, src, idx, dst = candidates[0]
        return (src, idx, dst)

    def is_won(self):
        return self.completed >= self.NUM_SETS


# ============================================================
# ПОЛЕ ПАУКА
# ============================================================

class SpiderBoard(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.selected_pile = None
        self.selected_idx = None
        self.last_tap_time = 0
        self.last_tap_target = None
        self._labels = []
        self._win_anim = None
        self._hint_highlight = None  # (src_pile, src_idx, dst_pile)
        self._hint_clear_event = None
        self.bind(size=self._redraw, pos=self._redraw)
        self.restart()
        Clock.schedule_interval(self._tick_timer, 1)

    def restart(self):
        if self._win_anim is not None:
            try:
                self._win_anim.stop()
                if self._win_anim.parent:
                    self._win_anim.parent.remove_widget(self._win_anim)
            except Exception:
                pass
            self._win_anim = None
        self.game = SpiderGame()
        self.selected_pile = None
        self.selected_idx = None
        self._hint_highlight = None
        self._redraw()

    def _tick_timer(self, dt):
        if self.game and self.game.timer_running and not self.game.game_over:
            self.game.elapsed_seconds += 1

    def _layout(self):
        # Топбар сверху - 8% высоты
        topbar_h = self.height * 0.08
        margin = self.width * 0.010
        gap = self.width * 0.006
        # 10 столбцов
        ncols = SpiderGame.NUM_COLUMNS
        card_w = (self.width - 2 * margin - (ncols - 1) * gap) / ncols
        card_h = card_w * 1.45

        # Зазор между топбаром и верхним рядом карт
        gap_top = self.height * 0.015
        # Верхний ряд: счётчик собранных + колода
        top_y = self.y + self.height - topbar_h - gap_top - card_h

        layout = {
            'card_w': card_w,
            'card_h': card_h,
            'gap': gap,
            'stock': None,
            'completed': None,
            'tableau': [],
        }
        # Stock справа
        stock_x = self.x + self.width - margin - card_w
        layout['stock'] = (stock_x, top_y)
        # Слева - индикатор собранных
        layout['completed'] = (self.x + margin, top_y)

        # 10 столбцов с большим зазором сверху
        tableau_top = top_y - card_h * 1.15
        for i in range(ncols):
            tx = self.x + margin + i * (card_w + gap)
            layout['tableau'].append((tx, tableau_top))

        return layout

    def _calc_steps(self, pile, ty, ch, face_down_step, face_up_step):
        """Шаги между картами в столбце с учётом доступной высоты."""
        if len(pile.cards) <= 1:
            return []
        steps = []
        for c in pile.cards[:-1]:
            steps.append(face_down_step if not c.face_up else face_up_step)
        total_h = sum(steps) + ch
        available = ty - self.y - ch * 0.1
        if total_h > available and available > ch:
            scale = (available - ch) / (total_h - ch) if total_h > ch else 1.0
            scale = max(0.25, scale)
            steps = [s * scale for s in steps]
        return steps

    def _redraw(self, *args):
        if not self.game:
            return
        self.canvas.clear()
        for lbl in self._labels:
            self.remove_widget(lbl)
        self._labels = []

        layout = self._layout()
        cw = layout['card_w']
        ch = layout['card_h']

        # Шаги между картами
        face_down_step = ch * 0.18
        face_up_step = ch * 0.30

        # === ВЕРХНИЙ РЯД ===
        # Колода - стопка рубашек справа
        sx, sy = layout['stock']
        if not self.game.stock.is_empty():
            # Рисуем как стопочку (несколько слоёв) - сразу видно сколько раздач осталось
            deals_left = len(self.game.stock) // SpiderGame.NUM_COLUMNS
            for i in range(min(deals_left, 5)):
                offset = i * 3
                fake = Card('A', 'spades')
                fake.face_up = False
                draw_card_canvas(self.canvas, fake, sx - offset, sy + offset, cw, ch)
        else:
            # Пусто - рамочка
            with self.canvas:
                Color(0.05, 0.20, 0.10, 1)
                from kivy.graphics import Line as _Line
                _Line(rounded_rectangle=(sx, sy, cw, ch, cw * 0.08), width=2)

        # Индикатор собранных комплектов слева
        cx, cy = layout['completed']
        if self.game.completed > 0:
            # Рисуем последний собранный комплект как одну карту
            fake = Card('K', 'spades')
            fake.face_up = True
            draw_card_canvas(self.canvas, fake, cx, cy, cw, ch)
            lbl = make_card_rank_label(fake, cx, cy, cw, ch)
            if lbl:
                self._labels.append(lbl)
                self.add_widget(lbl)
        # Счётчик "X/8"
        cnt_lbl = Label(
            text=str(self.game.completed) + '/8',
            font_size=max(20, int(ch * 0.30)),
            bold=True,
            color=(1, 1, 0.7, 1),
            size_hint=(None, None),
            size=(cw, ch * 0.4),
            pos=(cx + cw + 10, cy + ch * 0.3)
        )
        self._labels.append(cnt_lbl)
        self.add_widget(cnt_lbl)

        # === СТОЛБЦЫ ===
        # Подсветка подсказки
        hint_src_idx = None
        hint_dst_pile = None
        if self._hint_highlight:
            hsrc, hidx, hdst = self._hint_highlight
            hint_src_idx = (hsrc, hidx)
            hint_dst_pile = hdst

        for i, (tx, ty) in enumerate(layout['tableau']):
            pile = self.game.tableau[i]
            if pile.is_empty():
                # Рамочка пустого столбца
                with self.canvas:
                    Color(0.05, 0.20, 0.10, 1)
                    from kivy.graphics import Line as _Line
                    _Line(rounded_rectangle=(tx, ty, cw, ch, cw * 0.08), width=2)
                # Если это dst подсказки - подсветить ярче
                if hint_dst_pile is pile:
                    with self.canvas:
                        Color(1.0, 0.8, 0.2, 1)
                        _Line(rounded_rectangle=(tx, ty, cw, ch, cw * 0.08), width=4)
                continue

            steps = self._calc_steps(pile, ty, ch, face_down_step, face_up_step)
            cy = ty
            for j, card in enumerate(pile.cards):
                # Координата текущей карты
                if j == 0:
                    pass
                else:
                    cy -= steps[j - 1]

                # Выделена ли эта карта (выбор пользователя)
                sel = False
                if (self.selected_pile is pile and
                        self.selected_idx is not None and
                        j >= self.selected_idx):
                    sel = True

                # Подсветка подсказки
                if hint_src_idx and hint_src_idx[0] is pile and j >= hint_src_idx[1]:
                    sel = True

                draw_card_canvas(self.canvas, card, tx, cy, cw, ch, selected=sel)
                lbl = make_card_rank_label(card, tx, cy, cw, ch)
                if lbl:
                    self._labels.append(lbl)
                    self.add_widget(lbl)

            # Подсветка dst-столбца (рамка вокруг верхней карты)
            if hint_dst_pile is pile:
                top_y_pos = ty
                if len(pile.cards) > 1:
                    top_y_pos = ty - sum(steps)
                with self.canvas:
                    Color(1.0, 0.8, 0.2, 1)
                    from kivy.graphics import Line as _Line
                    _Line(rounded_rectangle=(tx, top_y_pos, cw, ch, cw * 0.08), width=4)

    def _hit_test(self, pos):
        """Определить во что попал палец. Возвращает (pile, idx)."""
        layout = self._layout()
        cw = layout['card_w']
        ch = layout['card_h']
        face_down_step = ch * 0.18
        face_up_step = ch * 0.30

        x, y = pos
        # Колода
        sx, sy = layout['stock']
        if sx <= x <= sx + cw and sy <= y <= sy + ch:
            return (self.game.stock, -1)

        # Столбцы
        for i, (tx, ty) in enumerate(layout['tableau']):
            if not (tx <= x <= tx + cw):
                continue
            pile = self.game.tableau[i]
            if pile.is_empty():
                # Тап по пустому слоту
                if ty <= y <= ty + ch:
                    return (pile, -2)
                continue
            steps = self._calc_steps(pile, ty, ch, face_down_step, face_up_step)
            # Перебираем карты сверху вниз (последняя - самая нижняя визуально)
            cy = ty
            positions = [cy]
            for s in steps:
                cy -= s
                positions.append(cy)
            # Хит-тест: проверяем сверху вниз стека (последняя самая верхняя в z-order)
            hit_idx = -1
            for j in range(len(pile.cards) - 1, -1, -1):
                cy_j = positions[j]
                # У всех карт кроме последней видна только верхняя полоска
                if j == len(pile.cards) - 1:
                    # Целая карта
                    if cy_j <= y <= cy_j + ch:
                        hit_idx = j
                        break
                else:
                    # Видна только верхняя часть высотой shape_step
                    s = steps[j]
                    if cy_j + ch - s <= y <= cy_j + ch:
                        hit_idx = j
                        break
            if hit_idx >= 0:
                return (pile, hit_idx)
        return (None, None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self.game.game_over:
            return True

        # Сбрасываем подсказку при любом тапе
        if self._hint_highlight:
            self._hint_highlight = None
            self._redraw()

        import time
        now = time.time()
        is_double = (now - self.last_tap_time < 0.4)
        self.last_tap_time = now

        pile, idx = self._hit_test(touch.pos)
        if pile is None:
            self.selected_pile = None
            self.selected_idx = None
            self._redraw()
            return True

        # Тап по колоде - раздать
        if pile is self.game.stock:
            self.game.deal_from_stock()
            self.selected_pile = None
            self.selected_idx = None
            self._redraw()
            self._check_win()
            return True

        self.last_tap_target = (pile, idx)

        if self.selected_pile is None:
            if idx < 0:
                return True
            card = pile.cards[idx]
            if not card.face_up:
                return True
            seq_idx = self.game.find_movable_sequence(pile, card)
            if seq_idx < 0:
                return True
            self.selected_pile = pile
            self.selected_idx = seq_idx
            self._redraw()
        else:
            if pile is self.selected_pile:
                self.selected_pile = None
                self.selected_idx = None
                self._redraw()
                return True
            ok = self.game.move_sequence(self.selected_pile, self.selected_idx, pile)
            self.selected_pile = None
            self.selected_idx = None
            self._redraw()
            if ok:
                self._check_win()
        return True

    def show_hint(self):
        """Показать подсказку - подсветить рекомендуемый ход на 3 секунды."""
        if self.game.game_over:
            return
        h = self.game.find_hint()
        if h is None:
            # Нет ходов - сообщение
            popup = Popup(
                title='',
                content=Label(
                    text='Нет ходов.\nРаздай колоду или начни заново.',
                    font_size=32,
                    halign='center'
                ),
                size_hint=(0.7, 0.3)
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 2.0)
            return
        src, idx, dst = h
        self._hint_highlight = (src, idx, dst)
        self._redraw()
        # Через 3 секунды убираем подсветку
        if self._hint_clear_event:
            self._hint_clear_event.cancel()
        self._hint_clear_event = Clock.schedule_once(self._clear_hint, 3.0)

    def _clear_hint(self, dt):
        if self._hint_highlight:
            self._hint_highlight = None
            self._redraw()
        self._hint_clear_event = None

    def _check_win(self):
        if self.game.is_won():
            self.game.game_over = True
            self.game.timer_running = False
            current_record = load_record('spider')
            if current_record is None or self.game.elapsed_seconds < current_record:
                save_record(self.game.elapsed_seconds, 'spider')
            self._start_win_animation()

    def _start_win_animation(self):
        layout = self._layout()
        # Стартовые позиции - 4 точки сверху (берём 4 равноудалённых столбца)
        tab = layout['tableau']
        starts = [tab[1], tab[3], tab[5], tab[7]]
        # Сдвигаем по y вверх к верхнему ряду
        sy = layout['stock'][1]
        starts = [(x, sy) for (x, _) in starts]

        cw = layout['card_w']
        ch = layout['card_h']
        anim = WinAnimation(
            foundations_xy=starts,
            card_w=cw,
            card_h=ch,
            on_finished=self._show_win_popup,
            size=self.size,
            pos=self.pos,
        )
        self.selected_pile = None
        self.selected_idx = None
        self._redraw()
        self.add_widget(anim)
        self._win_anim = anim
        anim.start()

    def _show_win_popup(self):
        if self._win_anim is not None:
            try:
                self._win_anim.stop()
                if self._win_anim.parent:
                    self._win_anim.parent.remove_widget(self._win_anim)
            except Exception:
                pass
            self._win_anim = None
        m = self.game.elapsed_seconds // 60
        s = self.game.elapsed_seconds % 60
        content = BoxLayout(orientation='vertical', spacing=20, padding=20)
        content.add_widget(Label(
            text='ПОБЕДА!\nВремя: ' + str(m).zfill(2) + ':' + str(s).zfill(2),
            font_size=40,
            bold=True,
            halign='center'
        ))
        btn = Button(
            text='Новая партия',
            font_size=32,
            size_hint=(1, 0.4),
            background_color=(0.3, 0.7, 0.4, 1)
        )
        content.add_widget(btn)
        popup = Popup(
            title='',
            content=content,
            size_hint=(0.7, 0.4),
            auto_dismiss=False
        )
        btn.bind(on_release=lambda *a: (popup.dismiss(), self.restart()))
        popup.open()


# ============================================================
# ЭКРАН ПАУКА
# ============================================================

class SpiderScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        outer = FloatLayout()

        with outer.canvas.before:
            Color(0.10, 0.35, 0.20, 1)
            self._bg = Rectangle(pos=outer.pos, size=outer.size)
        outer.bind(size=self._upd_bg, pos=self._upd_bg)

        self.board = SpiderBoard(
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        outer.add_widget(self.board)

        # Топбар - назад
        self.btn_home = Button(
            text='<',
            font_size=44,
            bold=True,
            size_hint=(0.12, 0.07),
            pos_hint={'x': 0.01, 'top': 0.99},
            background_color=(0.4, 0.5, 0.7, 0.95)
        )
        self.btn_home.bind(on_release=self._go_home)
        outer.add_widget(self.btn_home)

        # Таймер
        self.timer_label = Label(
            text='00:00',
            font_size=40,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(0.22, 0.07),
            pos_hint={'center_x': 0.4, 'top': 0.99}
        )
        outer.add_widget(self.timer_label)

        # Подсказка
        self.btn_hint = Button(
            text='?',
            font_size=44,
            bold=True,
            size_hint=(0.10, 0.07),
            pos_hint={'right': 0.74, 'top': 0.99},
            background_color=(0.4, 0.6, 0.4, 0.95)
        )
        self.btn_hint.bind(on_release=self._hint)
        outer.add_widget(self.btn_hint)

        # Отмена
        self.btn_undo = Button(
            text='Отмена',
            font_size=22,
            bold=True,
            size_hint=(0.16, 0.07),
            pos_hint={'right': 0.86, 'top': 0.99},
            background_color=(0.5, 0.4, 0.7, 0.95)
        )
        self.btn_undo.bind(on_release=self._undo)
        outer.add_widget(self.btn_undo)

        # Новая
        self.btn_new = Button(
            text='+',
            font_size=44,
            bold=True,
            size_hint=(0.12, 0.07),
            pos_hint={'right': 0.99, 'top': 0.99},
            background_color=(0.5, 0.3, 0.3, 0.95)
        )
        self.btn_new.bind(on_release=self._new_game)
        outer.add_widget(self.btn_new)

        self.add_widget(outer)
        Clock.schedule_interval(self._update_timer, 0.5)

    def _upd_bg(self, inst, val):
        self._bg.pos = inst.pos
        self._bg.size = inst.size

    def _go_home(self, *a):
        self.manager.transition.direction = 'right'
        self.manager.current = 'menu'

    def _undo(self, *a):
        if self.board.game:
            self.board.game.undo()
            self.board.selected_pile = None
            self.board.selected_idx = None
            self.board._redraw()

    def _hint(self, *a):
        self.board.show_hint()

    def _new_game(self, *a):
        self.board.restart()

    def _update_timer(self, dt):
        if self.board.game:
            sec = self.board.game.elapsed_seconds
            m = sec // 60
            s = sec % 60
            self.timer_label.text = str(m).zfill(2) + ':' + str(s).zfill(2)


# ============================================================
# ЭКРАН МЕНЮ
# ============================================================

class MenuScreen(Screen):
    def __init__(self, on_game_selected, **kwargs):
        super().__init__(**kwargs)
        self.on_game_selected = on_game_selected
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        with layout.canvas.before:
            Color(0.10, 0.35, 0.20, 1)
            self._bg = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(size=self._upd_bg, pos=self._upd_bg)

        title = Label(
            text='Карточные игры',
            font_size=52,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=110
        )
        layout.add_widget(title)

        layout.add_widget(CardGameMenuItem(
            'Косынка', 'klondike', True, self._select_game))
        layout.add_widget(CardGameMenuItem(
            'Паук', 'spider', True, self._select_game))
        layout.add_widget(CardGameMenuItem(
            'Свободная ячейка', 'freecell', False, self._select_game))

        layout.add_widget(Widget())

        hint = Label(
            text='Двойной тап — старт',
            font_size=40,
            bold=True,
            color=(0.9, 0.9, 0.7, 1),
            size_hint_y=None,
            height=70
        )
        layout.add_widget(hint)

        self.add_widget(layout)

    def _upd_bg(self, inst, val):
        self._bg.pos = inst.pos
        self._bg.size = inst.size

    def _select_game(self, key):
        self.on_game_selected(key)


# ============================================================
# ЭКРАН КОСЫНКИ
# ============================================================

class KlondikeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        outer = FloatLayout()

        with outer.canvas.before:
            Color(0.10, 0.35, 0.20, 1)
            self._bg = Rectangle(pos=outer.pos, size=outer.size)
        outer.bind(size=self._upd_bg, pos=self._upd_bg)

        # Игровое поле занимает 90% высоты снизу
        self.board = KlondikeBoard(
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        outer.add_widget(self.board)

        # Топбар - кнопки и таймер - в самом верху
        # Слева: кнопка "назад"
        self.btn_home = Button(
            text='<',
            font_size=44,
            bold=True,
            size_hint=(0.12, 0.07),
            pos_hint={'x': 0.01, 'top': 0.99},
            background_color=(0.4, 0.5, 0.7, 0.95)
        )
        self.btn_home.bind(on_release=self._go_home)
        outer.add_widget(self.btn_home)

        # Центр: таймер
        self.timer_label = Label(
            text='00:00',
            font_size=44,
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(0.3, 0.07),
            pos_hint={'center_x': 0.5, 'top': 0.99}
        )
        outer.add_widget(self.timer_label)

        # Справа: Undo и New (рядом, чтоб не налезали на колоду)
        self.btn_undo = Button(
            text='Отмена',
            font_size=24,
            bold=True,
            size_hint=(0.16, 0.07),
            pos_hint={'right': 0.83, 'top': 0.99},
            background_color=(0.5, 0.4, 0.7, 0.95)
        )
        self.btn_undo.bind(on_release=self._undo)
        outer.add_widget(self.btn_undo)

        self.btn_new = Button(
            text='+',
            font_size=44,
            bold=True,
            size_hint=(0.12, 0.07),
            pos_hint={'right': 0.99, 'top': 0.99},
            background_color=(0.5, 0.3, 0.3, 0.95)
        )
        self.btn_new.bind(on_release=self._new_game)
        outer.add_widget(self.btn_new)

        self.add_widget(outer)
        Clock.schedule_interval(self._update_timer, 0.5)

    def _upd_bg(self, inst, val):
        self._bg.pos = inst.pos
        self._bg.size = inst.size

    def _go_home(self, *a):
        self.manager.transition.direction = 'right'
        self.manager.current = 'menu'

    def _undo(self, *a):
        if self.board.game:
            self.board.game.undo()
            self.board.selected_pile = None
            self.board.selected_idx = None
            self.board._redraw()

    def _new_game(self, *a):
        self.board.restart()

    def _update_timer(self, dt):
        if self.board.game:
            sec = self.board.game.elapsed_seconds
            m = sec // 60
            s = sec % 60
            self.timer_label.text = str(m).zfill(2) + ':' + str(s).zfill(2)


# ============================================================
# ПРИЛОЖЕНИЕ
# ============================================================

class CardGamesApp(App):
    def build(self):
        Window.clearcolor = (0.10, 0.35, 0.20, 1)
        sm = ScreenManager(transition=SlideTransition(duration=0.25))

        menu = MenuScreen(on_game_selected=self._start_game, name='menu')
        self.menu_screen = menu
        sm.add_widget(menu)

        self.klondike_screen = KlondikeScreen(name='klondike')
        sm.add_widget(self.klondike_screen)

        self.spider_screen = SpiderScreen(name='spider')
        sm.add_widget(self.spider_screen)

        self.sm = sm
        return sm

    def _start_game(self, key):
        if key == 'klondike':
            self.klondike_screen.board.restart()
            self.sm.transition.direction = 'left'
            self.sm.current = 'klondike'
        elif key == 'spider':
            self.spider_screen.board.restart()
            self.sm.transition.direction = 'left'
            self.sm.current = 'spider'


if __name__ == '__main__':
    CardGamesApp().run()
