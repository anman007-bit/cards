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

    # Если открыта - рисуем масть в углах и в центре
    if card.face_up:
        suit_color = SUIT_COLORS[card.suit]
        # Маленькая масть СПРАВА ОТ РАНГА в верхней полоске
        # (видна даже когда карта перекрыта другой картой в столбце)
        small_size = w * 0.22
        small_cy = y + h * 0.88
        small_cx_left = x + w * 0.42   # справа от ранга
        draw_suit(canvas, card.suit, small_cx_left, small_cy, small_size, suit_color)
        # Маленькая масть в правом верхнем углу
        small_cx_right = x + w * 0.80
        draw_suit(canvas, card.suit, small_cx_right, small_cy, small_size, suit_color)
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
        self.bind(size=self._redraw, pos=self._redraw)
        self.restart()
        Clock.schedule_interval(self._tick_timer, 1)

    def restart(self):
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
            self._show_win_popup()

    def _show_win_popup(self):
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
        self.height = 220
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
                rec_text = 'Рекорд: ' + str(m).zfill(2) + ':' + str(s).zfill(2)
            else:
                rec_text = 'Рекорд: --:--'
        else:
            rec_text = 'Скоро...'
        record_label = Label(
            text=rec_text,
            font_size=30,
            color=(0.9, 0.9, 0.7, 1) if available else (0.6, 0.6, 0.6, 1),
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
            'Паук', 'spider', False, self._select_game))
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

        self.sm = sm
        return sm

    def _start_game(self, key):
        if key == 'klondike':
            self.klondike_screen.board.restart()
            self.sm.transition.direction = 'left'
            self.sm.current = 'klondike'


if __name__ == '__main__':
    CardGamesApp().run()
