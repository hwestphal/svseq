from launchpad import Launchpad, BUTTON_SCENE_1
from project import Pattern, Track
from engine import engine
from .padget import Padget

from typing import Optional


class ChordsAndTrigger(Padget):
    def __init__(self, pad: Launchpad, pattern: Pattern, track: Track, tn: int):
        super().__init__(pad)
        self.__pattern = pattern
        self.__track = track
        self.__tn = tn
        self.__pressed: Optional[int] = None

    def _buttonPressed(self, i: int) -> bool:
        if i < 32 and self.__pressed is None and self.__pattern.notes[i].tone > 0:
            self.__pressed = i
            return True
        if i >= 40 and i < 48 and not self.__track.percussion:
            if self.__pressed is not None:
                self.__pattern.notes[self.__pressed].chord = _chords[i - 40]
            elif not engine.playing:
                tone = 1 + self.__pattern.octave * 12
                chord = _chords[i - 40]
                engine.audioEngine.sendNotes(self.__tn, tone, tone + chord[0], tone + chord[1], (
                    tone + chord[2]) if chord[2] is not None else 128, 0, self.__track.instrument * 2 + 2)
            return True
        if i >= 48 and i < 50:
            if self.__pressed is not None:
                self.__pattern.notes[self.__pressed].trigger = i - 47
            return True
        if i >= 32 and i < 48 or i >= 50 and i < 64:
            if self.__pressed is not None:
                n = self.__pattern.notes[self.__pressed]
                if not self.__track.percussion:
                    n.chord = (None, None, None)
                n.trigger = 0
            return True
        return False

    def _buttonReleased(self, i: int) -> bool:
        if i == self.__pressed:
            self.__pressed = None
            return True
        if i >= 40 and i < 48 and not self.__track.percussion:
            if self.__pressed is None and not engine.playing:
                engine.audioEngine.sendNoteOff(
                    self.__tn, self.__track.instrument * 2 + 2)
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_SCENE_1 + 1, 0x033)
        notes = self.__pattern.notes
        for i in range(32):
            if notes[i].tone > 0:
                c = 0x001 if (self.__track.percussion or notes[i].chord == (
                    None, None, None)) and notes[i].trigger == 0 else 0x032
            else:
                c = 0x000
            if engine.uiState.playing and engine.uiState.phase * 4 == i:
                c |= 0x100
            self._pad.set(i, c)
        for i in range(32, 40):
            self._pad.set(i, 0x000)
        for i in range(40, 48):
            if self.__track.percussion:
                self._pad.set(i, 0x000)
            else:
                self._pad.set(
                    i, 0x130 if self.__pressed is not None and notes[self.__pressed].chord == _chords[i - 40] else 0x030)
        for i in range(48, 50):
            self._pad.set(
                i, 0x000 if self.__pressed is None else 0x133 if notes[self.__pressed].trigger == i - 47 else 0x033)
        for i in range(50, 64):
            self._pad.set(i, 0x000)


_chords = [
    (4, 7, None),  # major
    (3, 7, None),  # minor
    (3, 6, None),  # diminished
    (4, 8, None),  # augmented
    (4, 7, 10),    # dominant 7
    (3, 7, 10),    # minor 7
    (4, 7, 11),    # major 7
    (3, 6, 9)      # diminished 7
]
