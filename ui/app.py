from launchpad import Launchpad, BUTTON_MIXER, BUTTON_SESSION, BUTTON_LEFT, BUTTON_RIGHT, BUTTON_USER_1, BUTTON_USER_2, BUTTON_UP, BUTTON_DOWN
from engine import engine
from .padget import Padget
from .mixer import Mixer
from .session import Session
from .tempo import Tempo

from typing import Optional


class App(Padget):

    def __init__(self, pad: Launchpad):
        super().__init__(pad)
        self.__session: Optional[Session] = Session(pad)
        self.__mixer: Optional[Mixer] = None
        self.__tempo: Optional[Tempo] = None

    def _buttonPressed(self, i: int) -> bool:
        if i == BUTTON_MIXER and not self.__mixer:
            self.__mixer = Mixer(self._pad)
            self.__session = None
            self.__tempo = None
            return True
        if i == BUTTON_SESSION and not self.__session:
            self.__session = Session(self._pad)
            self.__mixer = None
            self.__tempo = None
            return True
        if i == BUTTON_LEFT and not self.__tempo:
            self.__tempo = Tempo(self._pad)
            self.__mixer = None
            self.__session = None
            return True
        if i == BUTTON_RIGHT and (not self.__session or self.__session.session_mode):
            engine.startOrStopSession()
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_MIXER, 0x030)
        self._pad.set(BUTTON_SESSION, 0x030)
        self._pad.set(BUTTON_LEFT, 0x030)
        self._pad.set(BUTTON_RIGHT, 0x103 if engine.uiState.playing >
                      0 else 0x133 if engine.uiState.playing < 0 else 0x030)
        self._pad.set(BUTTON_USER_1, 0x000)
        self._pad.set(BUTTON_USER_2, 0x000)
        self._pad.set(BUTTON_UP, 0x000)
        self._pad.set(BUTTON_DOWN, 0x000)
