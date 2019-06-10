from launchpad import Launchpad, BUTTON_MIXER, BUTTON_SCENE_1
from padget import Padget
from typing import List, Tuple
from .project import project
from math import modf


class Mixer(Padget):

    def __init__(self, pad: Launchpad):
        super().__init__(pad)
        self.__tracks: List[Track] = []
        for i in range(8):
            self.__tracks.append(Track(pad, i))

    def _render(self) -> None:
        self._pad.set(BUTTON_MIXER, 0x033)


class Track(Padget):

    def __init__(self, pad: Launchpad, i: int):
        super().__init__(pad)
        self.__track = project.tracks[i]
        self.__i = i

    def _buttonPressed(self, i: int) -> bool:
        if i == BUTTON_SCENE_1 + self.__i:
            self.__track.muted = not self.__track.muted
            return True
        if i >= self.__i * 8 and i < (self.__i + 1) * 8:
            i -= self.__i * 8
            c, v = _to_column_and_value(self.__track.volume)
            if i != c:
                self.__track.volume = _from_column_and_value(i, 3)
            else:
                self.__track.volume = _from_column_and_value(i, (v-1) % 4)
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SCENE_1 + self.__i,
                      0x003 if self.__track.muted else 0x030)
        c, v = _to_column_and_value(self.__track.volume)
        for i in range(c):
            self._pad.set(i + self.__i * 8, 0x033)
        self._pad.set(c + self.__i * 8, 0x011 * v)
        for i in range(c+1, 8):
            self._pad.set(i + self.__i * 8, 0x000)


def _to_column_and_value(w: float) -> Tuple[int, int]:
    v = round(max(min(1, w), 0) * 24)
    if v == 0:
        return 0, 0
    v -= 1
    return v // 3, (v % 3) + 1


def _from_column_and_value(c: int, v: int) -> float:
    return (c * 3 + v) / 24
