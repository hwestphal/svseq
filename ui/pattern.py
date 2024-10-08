from engine import engine
from launchpad import (BUTTON_DOWN, BUTTON_RIGHT, BUTTON_SCENE_1,
                       BUTTON_SESSION, BUTTON_UP, BUTTON_USER_1, BUTTON_USER_2,
                       Launchpad)
from project import project

from .chords import ChordsAndTrigger
from .controller import Controller
from .notes import MelodyPattern, PercussionPattern
from .padget import Padget


class Pattern(Padget):
    def __init__(self, pad: Launchpad, t: int, p: int):
        super().__init__(pad)
        self.__track = project.tracks[t]
        self.__pattern = self.__track.patterns[p]
        self.__tn = t
        self.__pn = p
        self.__display = self.__create_notes()
        self.__scene = 0
        self.__record = False

    def _buttonPressed(self, i: int) -> bool:
        if BUTTON_SCENE_1 <= i < BUTTON_SCENE_1 + 8:
            i -= BUTTON_SCENE_1
            if i != self.__scene and i != 2:
                if i == 0:
                    self.__display = self.__create_notes()
                elif i == 1:
                    self.__display = ChordsAndTrigger(
                        self._pad, self.__pattern, self.__track, self.__tn)
                else:
                    self.__display = Controller(
                        self._pad, self.__pattern, i - 3)
                self.__scene = i
            return True
        if i == BUTTON_RIGHT:
            engine.startOrStopPattern(self.__tn, self.__pn, self.__record)
            return True
        if i == BUTTON_USER_2 and not engine.playing:
            self.__record = True
            return True
        return False

    def _buttonReleased(self, i: int) -> bool:
        if i == BUTTON_USER_2 and self.__record:
            self.__record = False
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SESSION, 0x003)
        self._pad.set(BUTTON_UP, 0x000)
        self._pad.set(BUTTON_DOWN, 0x000)
        self._pad.set(BUTTON_USER_1, 0x000)
        self._pad.set(BUTTON_USER_2, 0x103 if engine.recording == (self.__tn, self.__pn)
                      else 0x000 if engine.playing else 0x033 if self.__record else 0x030)
        self._pad.set(BUTTON_SCENE_1, 0x030)
        self._pad.set(BUTTON_SCENE_1 + 1, 0x030)
        self._pad.set(BUTTON_SCENE_1 + 2, 0x000)
        for i in range(3, 8):
            self._pad.set(BUTTON_SCENE_1 + i, 0x030)

    def __create_notes(self) -> Padget:
        if self.__track.percussion:
            return PercussionPattern(self._pad, self.__pattern, self.__track, self.__tn, self.__pn)
        return MelodyPattern(self._pad, self.__pattern, self.__track, self.__tn, self.__pn)
