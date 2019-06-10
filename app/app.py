from launchpad import Launchpad, BUTTON_MIXER, BUTTON_SESSION, BUTTON_USER_1, BUTTON_USER_2, BUTTON_UP, BUTTON_DOWN
from padget import Padget
from .mixer import Mixer
from .session import Session
from typing import Optional


class App(Padget):

    def __init__(self, pad: Launchpad):
        super().__init__(pad)
        self.__mixer: Optional[Mixer] = None
        self.__session: Optional[Session] = Session(pad)

    def _buttonPressed(self, i: int) -> bool:
        if i == BUTTON_MIXER and not self.__mixer:
            self.__mixer = Mixer(self._pad)
            self.__session = None
            return True
        if i == BUTTON_SESSION and not self.__session:
            self.__mixer = None
            self.__session = Session(self._pad)
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_MIXER, 0x030)
        self._pad.set(BUTTON_SESSION, 0x030)
        self._pad.set(BUTTON_USER_1, 0x000)
        self._pad.set(BUTTON_USER_2, 0x000)
        self._pad.set(BUTTON_UP, 0x000)
        self._pad.set(BUTTON_DOWN, 0x000)
