from launchpad import Launchpad, BUTTON_SESSION, BUTTON_SCENE_1, BUTTON_USER_1, BUTTON_UP, BUTTON_DOWN
from padget import Padget
from typing import Optional, List
from .state import state
from .pattern import createPattern, Pattern


class Session(Padget):

    def __init__(self, pad: Launchpad):
        super().__init__(pad)
        self.__tracks: List[Track] = []
        self.__initTracks()
        self.__preset: Optional[Preset] = None
        self.__select = False
        self.__pattern: Optional[Pattern] = None

    def _buttonPressed(self, i: int) -> bool:
        if self.__preset:
            if i == BUTTON_SESSION:
                self.__initTracks()
                self.__preset = None
                return True
            return False
        if self.__pattern:
            if i == BUTTON_SESSION:
                self.__initTracks()
                self.__pattern = None
                return True
            return False
        if i >= BUTTON_SCENE_1 and i < BUTTON_SCENE_1 + 8:
            self.__tracks.clear()
            self.__preset = Preset(self._pad, i - BUTTON_SCENE_1)
            return True
        if i == BUTTON_USER_1 and not self.__select:
            self.__select = True
            return True
        if i < 64 and self.__select:
            self.__tracks.clear()
            self.__pattern = createPattern(self._pad, i // 8, i % 8)
            return True
        return False

    def _buttonReleased(self, i: int) -> bool:
        if i == BUTTON_USER_1 and self.__select:
            self.__select = False
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SESSION, 0x033)
        self._pad.set(BUTTON_USER_1, 0x033 if self.__select else 0x030)
        self._pad.set(BUTTON_UP, 0x000)
        self._pad.set(BUTTON_DOWN, 0x000)

    def __initTracks(self) -> None:
        for i in range(8):
            self.__tracks.append(Track(self._pad, i))


class Track(Padget):

    def __init__(self, pad: Launchpad, i: int):
        super().__init__(pad)
        self.__track = state.tracks[i]
        self.__i = i

    def _buttonPressed(self, i: int) -> bool:
        if i >= self.__i * 8 and i < (self.__i + 1) * 8:
            i -= self.__i * 8
            if i in self.__track.sequence:
                self.__track.sequence.remove(i)
            else:
                self.__track.sequence.append(i)
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SCENE_1 + self.__i, 0x030)
        for i in range(8):
            empty = self.__track.patterns[i].empty
            if i in self.__track.sequence:
                c = 0x001 if empty else 0x003
            else:
                c = 0x000 if empty else 0x030
            self._pad.set(i + self.__i * 8, c)


class Preset(Padget):
    def __init__(self, pad: Launchpad, i: int):
        super().__init__(pad)
        self.__track = state.tracks[i]
        self.__i = i

    def _buttonPressed(self, i: int) -> bool:
        if i < 64:
            self.__track.instrument = i
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SESSION, 0x003)
        self._pad.set(BUTTON_USER_1, 0x000)
        for i in range(8):
            self._pad.set(BUTTON_SCENE_1 + i, 0x033 if i ==
                          self.__i else 0x000)
        for i in range(64):
            self._pad.set(i, 0x003 if i == self.__track.instrument else 0x030)
