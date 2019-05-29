import pygame.midi
from typing import Generator, Tuple

pygame.midi.init()


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


class Launchpad:
    def __init__(self, id: bytes = b'Launchpad'):
        midiIn = midiOut = None
        for i in range(pygame.midi.get_count()):
            _, name, input, output, opened = pygame.midi.get_device_info(i)
            if name == id and not opened:
                if input and midiIn is None:
                    midiIn = i
                elif output and midiOut is None:
                    midiOut = i
        if midiIn is None or midiOut is None:
            raise RuntimeError(f'Cannot connect to "{id.decode()}"')
        self.__midiIn = pygame.midi.Input(midiIn)
        self.__midiOut = pygame.midi.Output(midiOut)
        self.__midiOut.write_short(0xb0, 0x00, 0x00)
        self.__midiOut.write_short(0xb0, 0x00, 0x28)
        self.__current = [0x04] * 80
        self.__work = [0x04] * 80

    def close(self) -> None:
        self.__midiOut.write_short(0xb0, 0x00, 0x00)
        self.__midiIn.close()
        self.__midiOut.close()

    def poll(self) -> Generator[Tuple[int, int], None, None]:
        while self.__midiIn.poll():
            c, i, v, _ = self.__midiIn.read(1)[0][0]
            if c == 0x90:
                r = i // 16
                i = i % 16
                if i < 8:
                    yield i + r * 8, v
                else:
                    yield r + 64, v
            elif c == 0xb0:
                yield i - 32, v

    def set(self, i: int, v: int) -> None:
        if i < 80:
            if v & 0x100 and v != 0x100:
                v = 0x08 | (v & 0x33)
            else:
                v = 0x04 | (v & 0x33)
            self.__work[i] = v

    def refresh(self) -> int:
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
