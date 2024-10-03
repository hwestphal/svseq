import math
import sys
from typing import Generator, List, Optional, Tuple, cast

import pygame.draw
import pygame.event
import pygame.font
import pygame.midi
from pygame import locals
from pygame.surface import Surface

BUTTON_SCENE_1 = 64
BUTTON_UP = 72
BUTTON_DOWN = 73
BUTTON_LEFT = 74
BUTTON_RIGHT = 75
BUTTON_SESSION = 76
BUTTON_USER_1 = 77
BUTTON_USER_2 = 78
BUTTON_MIXER = 79

# fast mode seems to be broken
FAST_MODE = False
BLINK_PERIOD = 10
LABELS = ["U", "D", "L", "R", "S", "U1", "U2", "M"]


class NoopMidi:
    def poll(self):
        return False

    def read(self, num_events: int):
        raise

    def write_short(self, status: int, data1=0, data2=0):
        pass

    def close(self):
        pass


class Launchpad:
    def __init__(self, screen: Surface, id: bytes = b'Launchpad'):
        self.__screen = screen
        w = screen.get_width()
        h = screen.get_height()
        d = math.floor(min(w, h) / 10)
        di = d - math.floor(d / 10)
        x = math.floor((w - 10 * d) / 2)
        y = math.floor((h - 10 * d) / 2)
        self.__dims = x, y, d, di
        font = pygame.font.SysFont("", d // 2)
        self.__labels: List[Surface] = []
        for label in LABELS:
            self.__labels.append(font.render(label, True, (255, 255, 255)))
        for i in range(8):
            self.__labels.append(font.render(str(i+1), True, (255, 255, 255)))
        self.__frame = 0
        midiIn = midiOut = None
        for i in range(pygame.midi.get_count()):
            _, name, input, output, opened = pygame.midi.get_device_info(i)
            if id in name and not opened:
                if input and midiIn is None:
                    midiIn = i
                elif output and midiOut is None:
                    midiOut = i
        if midiIn is None or midiOut is None:
            print(f'Cannot connect to "{id.decode()}"', file=sys.stderr)
            self.__midiIn = self.__midiOut = NoopMidi()
        else:
            self.__midiIn = pygame.midi.Input(midiIn)
            self.__midiOut = pygame.midi.Output(midiOut)
        self.__midiOut.write_short(0xb0, 0x00, 0x00)
        self.__midiOut.write_short(0xb0, 0x00, 0x28)
        self.__current = [0x04] * 80
        self.__work = [0x04] * 80
        self.__pressed = [False] * 80
        self.__mouse: List[Optional[int]] = [None, None, None]

    def close(self) -> None:
        self.__midiOut.write_short(0xb0, 0x00, 0x00)
        self.__midiIn.close()
        self.__midiOut.close()

    def poll(self) -> Generator[Tuple[int, int], None, None]:
        while self.__midiIn.poll():
            c, i, v, _ = cast(List[int], self.__midiIn.read(1)[0][0])
            if c == 0x90:
                r = i // 16
                i = i % 16
                if i < 8:
                    self.__pressed[i + r * 8] = True if v else False
                    yield i + r * 8, v
                else:
                    self.__pressed[r + 64] = True if v else False
                    yield r + 64, v
            elif c == 0xb0:
                self.__pressed[i - 32] = True if v else False
                yield i - 32, v

        for event in pygame.event.get():
            if event.type == locals.MOUSEBUTTONDOWN and event.button in (1, 2, 3):
                x, y, d, _ = self.__dims
                i = (event.pos[0] - x) // d
                j = (event.pos[1] - y) // d - 1
                if 0 <= i < 9 and 0 <= j < 9 and (i != 8 or j != 0):
                    if i < 8 and j > 0:
                        k = (j - 1) * 8 + i
                    elif j == 0:
                        k = BUTTON_UP + i
                    else:
                        k = BUTTON_SCENE_1 + j - 1
                    self.__mouse[event.button - 1] = k
                    self.__pressed[k] = True
                    yield k, 127
            elif event.type == locals.MOUSEBUTTONUP and event.button in (1, 2, 3):
                i = self.__mouse[event.button - 1]
                if i is not None:
                    self.__mouse[event.button - 1] = None
                    self.__pressed[i] = False
                    yield i, 0

    def set(self, i: int, v: int) -> None:
        if i < 80:
            if v & 0x100 and v != 0x100:
                v = 0x08 | (v & 0x33)
            else:
                v = 0x04 | (v & 0x33)
            self.__work[i] = v

    def refresh(self) -> int:
        self.__draw_screen()
        changes = [(i, v) for i, v in enumerate(
            self.__work) if v != self.__current[i]]
        n = len(changes)
        if n == 0:
            return 0
        s = [(i, v) for i, v in enumerate(self.__work) if v != 0x04]
        ns = len(s)
        if not FAST_MODE or n < 40 or ns < 38:
            if n > ns + 2:
                changes = s
                n = ns + 2
                self.__midiOut.write_short(0xb0, 0x00, 0x00)
                self.__midiOut.write_short(0xb0, 0x00, 0x28)
            for i, v in changes:
                if i < 72:
                    if i < 64:
                        i = (i // 8) * 16 + (i % 8)
                    else:
                        i = (i - 64) * 16 + 8
                    self.__midiOut.write_short(0x90, i, v)
                else:
                    self.__midiOut.write_short(0xb0, i + 32, v)
        else:
            n = 40
            for i in range(0, 80, 2):
                self.__midiOut.write_short(
                    0x92, self.__work[i], self.__work[i + 1])
        self.__current = self.__work
        self.__work = self.__work.copy()
        return n

    def __draw_screen(self):
        screen = self.__screen
        x, y, d, di = self.__dims
        screen.fill((0, 0, 0))
        for i in range(64):
            v = self.__work[i]
            r = (x + d * (i % 8), y + d * ((i // 8) + 2), di, di)
            if v & 0x33 and (self.__frame < BLINK_PERIOD or (v & 0x08) == 0):
                c = ((v & 0x03) << 6, (v & 0x30) << 2, 0)
            else:
                c = (32, 32, 32)
            pygame.draw.rect(screen, c, r)
            if self.__pressed[i]:
                pygame.draw.rect(screen, (0, 0, 255), (r[0], r[1], di/3, di/3))
        for i in range(8):
            v = self.__work[i + 64]
            r = (x + d * 8 + di/2, y + d * (i+2) + di/2)
            if v & 0x33 and (self.__frame < BLINK_PERIOD or (v & 0x08) == 0):
                c = ((v & 0x03) << 6, (v & 0x30) << 2, 0)
            else:
                c = (32, 32, 32)
            pygame.draw.circle(screen, c, r, di/2)
            if self.__pressed[i + 64]:
                pygame.draw.rect(screen, (0, 0, 255),
                                 (r[0] - di/2, r[1] - di/2, di/3, di/3))
            screen.blit(self.__labels[i + 8], (r[0] + d - di/3, r[1] - di/4))
        for i in range(8):
            v = self.__work[i + 72]
            r = (x + d * i + di/2, y + di/2 + d)
            if v & 0x33 and (self.__frame < BLINK_PERIOD or (v & 0x08) == 0):
                c = ((v & 0x03) << 6, (v & 0x30) << 2, 0)
            else:
                c = (32, 32, 32)
            pygame.draw.circle(screen, c, r, di/2)
            if self.__pressed[i + 72]:
                pygame.draw.rect(screen, (0, 0, 255),
                                 (r[0] - di/2, r[1] - di/2, di/3, di/3))
            screen.blit(self.__labels[i], (r[0] - di/4, r[1] - d))
        self.__frame = (self.__frame + 1) % (BLINK_PERIOD * 2)
