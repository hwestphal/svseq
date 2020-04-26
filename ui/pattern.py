from launchpad import Launchpad, BUTTON_SESSION, BUTTON_SCENE_1, BUTTON_USER_1, BUTTON_USER_2, BUTTON_UP, BUTTON_DOWN, BUTTON_RIGHT
from project import project
from engine import engine
from .padget import Padget
from .notes import PercussionPattern, MelodyPattern
from .controller import Controller


class Pattern(Padget):
    def __init__(self, pad: Launchpad, t: int, p: int):
        super().__init__(pad)
        self.__track = project.tracks[t]
        self.__pattern = self.__track.patterns[p]
        self.__tn = t
        self.__display = self.__create_notes()
        self.__scene = 0
        self.__pn = p

    def _buttonPressed(self, i: int) -> bool:
        if i >= BUTTON_SCENE_1 and i < BUTTON_SCENE_1 + 8:
            i -= BUTTON_SCENE_1
            if i != self.__scene and (i != 1 or i != 2):
                if i == 0:
                    self.__display = self.__create_notes()
                elif i == 3:
                    self.__display = Controller(self._pad, self.__pattern, 0, True)
                else:
                    self.__display = Controller(self._pad, self.__pattern, i-3, False)
                self.__scene = i
            return True
        if i == BUTTON_RIGHT:
            engine.startOrStopPattern(self.__tn, self.__pn)
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SESSION, 0x003)
        self._pad.set(BUTTON_UP, 0x000)
        self._pad.set(BUTTON_DOWN, 0x000)
        self._pad.set(BUTTON_USER_1, 0x000)
        self._pad.set(BUTTON_USER_2, 0x000)
        self._pad.set(BUTTON_SCENE_1, 0x030)
        self._pad.set(BUTTON_SCENE_1 + 1, 0x000)
        self._pad.set(BUTTON_SCENE_1 + 2, 0x000)
        for i in range(3, 8):
            self._pad.set(BUTTON_SCENE_1 + i, 0x030)

    def __create_notes(self) -> Padget:
        if self.__track.percussion:
            return PercussionPattern(self._pad, self.__pattern)
        return MelodyPattern(self._pad, self.__pattern, self.__track, self.__tn)
