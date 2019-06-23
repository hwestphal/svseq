from launchpad import Launchpad, BUTTON_SESSION, BUTTON_SCENE_1, BUTTON_USER_1, BUTTON_USER_2, BUTTON_UP, BUTTON_DOWN, BUTTON_RIGHT
from project import project
from engine import engine
from .padget import Padget
from .notes import PercussionPattern, MelodyPattern
from .controller import Controller


class Pattern(Padget):
    def __init__(self, pad: Launchpad, t: int, p: int):
        super().__init__(pad)
        track = project.tracks[t]
        self.__pattern = track.patterns[p]
        self.__percussion = track.percussion
        self.__display = self.__create_notes()
        self.__scene = 0
        self.__tn = t
        self.__pn = p

    def _buttonPressed(self, i: int) -> bool:
        if i >= BUTTON_SCENE_1 and i < BUTTON_SCENE_1 + 8:
            i -= BUTTON_SCENE_1
            if i != self.__scene and i != 1:
                if i == 0:
                    self.__display = self.__create_notes()
                else:
                    self.__display = Controller(self._pad, self.__pattern, i-2)
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
        for i in range(2, 8):
            self._pad.set(BUTTON_SCENE_1 + i, 0x030)

    def __create_notes(self) -> Padget:
        if self.__percussion:
            return PercussionPattern(self._pad, self.__pattern)
        return MelodyPattern(self._pad, self.__pattern)
