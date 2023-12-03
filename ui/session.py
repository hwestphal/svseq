from launchpad import Launchpad, BUTTON_SESSION, BUTTON_SCENE_1, BUTTON_USER_1, BUTTON_USER_2, BUTTON_UP, BUTTON_DOWN
from project import project
from engine import engine
from .padget import Padget
from .pattern import Pattern

from mopyx import computed
from typing import Optional, List


class Session(Padget):

    def __init__(self, pad: Launchpad):
        super().__init__(pad)
        self.__tracks: List[Track] = []
        self.__initTracks()
        self.__preset: Optional[Preset] = None
        self.__select = False
        self.__copy = False
        self.__copy_from: Optional[int] = None
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
            self.__copy = False
            return True
        if i == BUTTON_USER_2 and not self.__copy:
            self.__copy = True
            self.__copy_from = None
            self.__select = False
            return True
        if i < 64:
            if self.__select:
                self.__tracks.clear()
                self.__pattern = Pattern(self._pad, i // 8, i % 8)
                return True
            if self.__copy:
                self.__handleCopy(i)
                return True
        return False

    def __handleCopy(self, i: int) -> None:
        t = project.tracks[i // 8]
        p = t.patterns[i % 8]
        if self.__copy_from is None:
            if not p.empty:
                self.__copy_from = i
            return
        if i == self.__copy_from:
            # clear
            for n in p.notes:
                n.tone = 0
                n.chord = (None, None, None)
                for c in range(len(n.control)):
                    n.control[c] = None
                n.trigger = 0
            self.__copy = False
            return
        st = project.tracks[self.__copy_from // 8]
        if t.percussion != st.percussion:
            return
        # copy
        sp = st.patterns[self.__copy_from % 8]
        for m in range(len(sp.notes)):
            p.notes[m].tone = sp.notes[m].tone
            p.notes[m].chord = sp.notes[m].chord
            p.notes[m].control = sp.notes[m].control.copy()
            p.notes[m].trigger = sp.notes[m].trigger
        self.__copy = False

    def _buttonReleased(self, i: int) -> bool:
        if i == BUTTON_USER_1 and self.__select:
            self.__select = False
            return True
        if i == BUTTON_USER_2 and self.__copy:
            self.__copy = False
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SESSION, 0x033)
        self._pad.set(BUTTON_USER_1, 0x033 if self.__select else 0x030)
        self._pad.set(
            BUTTON_USER_2, (0x033 if self.__copy_from is None else 0x003) if self.__copy else 0x030)
        self._pad.set(BUTTON_UP, 0x000)
        self._pad.set(BUTTON_DOWN, 0x000)

    def __initTracks(self) -> None:
        for i in range(8):
            self.__tracks.append(Track(self._pad, i))

    @computed
    def session_mode(self) -> bool:
        return self.__pattern is None


class Track(Padget):

    def __init__(self, pad: Launchpad, i: int):
        super().__init__(pad)
        self.__track = project.tracks[i]
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
            if engine.uiState.playing and engine.uiState.pattern[self.__i] == i:
                c |= 0x100
            self._pad.set(i + self.__i * 8, c)


class Preset(Padget):
    def __init__(self, pad: Launchpad, i: int):
        super().__init__(pad)
        self.__track = project.tracks[i]
        self.__i = i

    def _buttonPressed(self, i: int) -> bool:
        if i < 64 and not self.__in_use(i):
            engine.audioEngine.setVolume(self.__track.instrument * 2 + (3 if self.__track.percussion else 2), 0)
            self.__track.instrument = i
            if self.__track.muted:
                engine.audioEngine.setVolume(self.__track.instrument * 2 + (3 if self.__track.percussion else 2), 0)
            else:
                engine.audioEngine.setVolume(self.__track.instrument * 2 + (3 if self.__track.percussion else 2), round(self.__track.volume * 0x4000))
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SESSION, 0x003)
        self._pad.set(BUTTON_USER_1, 0x000)
        self._pad.set(BUTTON_USER_2, 0x000)
        for i in range(8):
            self._pad.set(BUTTON_SCENE_1 + i, 0x033 if i ==
                          self.__i else 0x000)
        for i in range(64):
            self._pad.set(i, 0x003 if i == self.__track.instrument else (
                0x000 if self.__in_use(i) else 0x030))

    def __in_use(self, i: int) -> bool:
        for t in project.tracks:
            if t.percussion == self.__track.percussion and t.instrument == i:
                return True
        return False
