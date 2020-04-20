from launchpad import Launchpad, BUTTON_SCENE_1
from project import Pattern
from engine import engine
from .padget import Padget

from typing import Optional, Tuple


class Controller(Padget):
    def __init__(self, pad: Launchpad, pattern: Pattern, cn: int):
        super().__init__(pad)
        self.__pattern = pattern
        self.__cn = cn
        self.__pressed: Optional[int] = None

    def _buttonPressed(self, i: int) -> bool:
        if i < 32 and self.__pressed is None:
            self.__pressed = i
            return True
        if i >= 32 and i < 64:
            if self.__pressed is not None:
                control = self.__pattern.notes[self.__pressed].control
                if i == 32:
                    control[self.__cn] = None
                else:
                    i -= 33
                    c, v = _to_column_and_value(control[self.__cn])
                    if i != c:
                        control[self.__cn] = _from_column_and_value(i, 3)
                    else:
                        control[self.__cn] = _from_column_and_value(
                            i, (v-1) % 4)
            return True
        return False

    def _buttonReleased(self, i: int) -> bool:
        if i == self.__pressed:
            self.__pressed = None
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SCENE_1 + 3 + self.__cn, 0x033)
        notes = self.__pattern.notes
        for i in range(32):
            tone = notes[i].tone
            control = notes[i].control[self.__cn]
            if control is None and tone > 0:
                c = 0x001
            elif control is not None and tone > 0:
                c = 0x032
            elif control is not None:
                c = 0x030
            else:
                c = 0x000
            if engine.uiState.playing and engine.uiState.beat % 8 * 4 == i:
                c |= 0x100
            self._pad.set(i, c)
        if self.__pressed is not None:
            cv = self.__pattern.notes[self.__pressed].control[self.__cn]
            self._pad.set(32, 0x103 if cv is None else 0x003)
            c, v = _to_column_and_value(cv)
            for i in range(c):
                self._pad.set(i + 33, 0x033)
            self._pad.set(c + 33, 0x011 * v)
            for i in range(c+1, 31):
                self._pad.set(i + 33, 0x000)
        else:
            for i in range(32, 64):
                self._pad.set(i, 0x000)


def _to_column_and_value(w: Optional[float]) -> Tuple[int, int]:
    if w is None:
        return 0, 0
    v = round(max(min(1, w), 0) * 3 * 31)
    if v == 0:
        return 0, 0
    v -= 1
    return v // 3, (v % 3) + 1


def _from_column_and_value(c: int, v: int) -> float:
    return (c * 3 + v) / (3 * 31)
