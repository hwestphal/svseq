from launchpad import Launchpad, BUTTON_SCENE_1, BUTTON_USER_1, BUTTON_UP, BUTTON_DOWN
from project import Pattern, Track
from engine import engine
from .padget import Padget

from typing import Optional


class _Pattern(Padget):
    def __init__(self, pad: Launchpad, pattern: Pattern, track: Track, tn: int):
        super().__init__(pad)
        self._pattern = pattern
        self._track = track
        self._tn = tn

    def _render(self) -> None:
        self._pad.set(BUTTON_SCENE_1, 0x033)


class PercussionPattern(_Pattern):
    def __init__(self, pad: Launchpad, pattern: Pattern, track: Track, tn: int):
        super().__init__(pad, pattern, track, tn)
        self.__pressed: Optional[int] = None

    def _buttonPressed(self, i: int) -> bool:
        if i < 32 and self.__pressed is None:
            self.__pressed = i
            return True
        if i >= 40 and i < 47:
            o = i - 37
            if self.__pressed is not None:
                self._pattern.notes[self.__pressed].tone = 1 + 12 * o
            elif not self._track.muted and not engine.playing:
                engine.audioEngine.sendNotes(
                    self._tn, 1 + 12 * o, 128, 128, 128, round(self._track.volume * 128) + 1, self._track.instrument * 2 + 3)
            return True
        if i == 47:
            if self.__pressed is not None:
                self._pattern.notes[self.__pressed].tone = -1
            return True
        if i >= 32 and i < 64:
            if self.__pressed is not None:
                self._pattern.notes[self.__pressed].tone = 0
            return True
        return False

    def _buttonReleased(self, i: int) -> bool:
        if i == self.__pressed:
            self.__pressed = None
            return True
        if i >= 40 and i < 47 and not engine.playing:
            engine.audioEngine.sendNoteOff(
                self._tn, self._track.instrument * 2 + 3)
            return True
        return False

    def _render(self) -> None:
        super()._render()
        notes = self._pattern.notes
        for i in range(32):
            if i == self.__pressed:
                c = 0x033
            else:
                tone = notes[i].tone
                if tone == -1:
                    c = 0x003
                elif tone == 0:
                    c = 0x000
                else:
                    c = 0x030
                if engine.uiState.playing and engine.uiState.phase * 4 == i:
                    c |= 0x100
            self._pad.set(i, c)
        for i in range(32, 40):
            self._pad.set(i, 0x000)
        for i in range(40, 47):
            self._pad.set(i, 0x133 if self.__is_pressed(
                1 + (i - 37) * 12) else 0x033)
        self._pad.set(47, 0x103 if self.__is_pressed(-1) else 0x003)
        for i in range(48, 64):
            self._pad.set(i, 0x000)

    def __is_pressed(self, t: int) -> bool:
        return self.__pressed is not None and self._pattern.notes[self.__pressed].tone == t


class MelodyPattern(_Pattern):
    def __init__(self, pad: Launchpad, pattern: Pattern, track: Track, tn: int):
        super().__init__(pad, pattern, track, tn)
        self.__pressed: Optional[int] = None
        self.__transpose = False

    def _buttonPressed(self, i: int) -> bool:
        if i == BUTTON_USER_1:
            self.__transpose = True
            return True
        if self.__transpose:
            if i == BUTTON_UP:
                self.__transpose_pattern(1)
                return True
            if i == BUTTON_DOWN:
                self.__transpose_pattern(-1)
                return True
            return False
        if i == BUTTON_UP and self._pattern.octave > 0:
            self._pattern.octave -= 1
            return True
        if i == BUTTON_DOWN and self._pattern.octave < 8:
            self._pattern.octave += 1
            return True
        if i < 32 and self.__pressed is None:
            self.__pressed = i
            return True
        if i >= 32 and i < 64:
            tone = _to_tone(i-32, self._pattern.octave)
            if self.__pressed is not None:
                self._pattern.notes[self.__pressed].tone = tone
            elif tone > 0 and not self._track.muted:
                engine.audioEngine.sendNotes(
                    self._tn, tone, 128, 128, 128, round(self._track.volume * 128) + 1, self._track.instrument * 2 + 2)
            return True
        return False

    def _buttonReleased(self, i: int) -> bool:
        if i == BUTTON_USER_1:
            self.__transpose = False
            return True
        if i == self.__pressed:
            self.__pressed = None
            return True
        if i >= 32 and i < 64:
            if self.__pressed is None and _to_tone(i-32, self._pattern.octave) > 0:
                engine.audioEngine.sendNoteOff(
                    self._tn, self._track.instrument * 2 + 2)
            return True
        return False

    def _render(self) -> None:
        super()._render()
        notes = self._pattern.notes
        for i in range(32):
            tone = notes[i].tone
            if tone == -1:
                c = 0x003
            elif tone == 0:
                c = 0x000
            else:
                c = 0x030
            if engine.uiState.playing and engine.uiState.phase * 4 == i:
                c |= 0x100
            self._pad.set(i, c)
        self._pad.set(BUTTON_USER_1, 0x033 if self.__transpose else 0x030)
        self._pad.set(
            BUTTON_UP, 0x030 if self._pattern.octave > 0 or self.__transpose else 0x000)
        self._pad.set(
            BUTTON_DOWN, 0x030 if self._pattern.octave < 8 or self.__transpose else 0x000)
        for i in range(32):
            if i == self.__pressed:
                self._pad.set(i, 0x033)
        for i in range(32, 64):
            self._pad.set(i, self.__keyboard_color(i-32))

    def __keyboard_color(self, n: int) -> int:
        if n == 31:
            return 0x103 if self.__is_pressed(-1) else 0x003
        o = self._pattern.octave
        t = _to_tone(n, o)
        if not t:
            return 0x000
        o += n // 16
        n %= 16
        c = _octave_color[o]
        if self.__is_pressed(t):
            c |= 0x100
        return c

    def __is_pressed(self, t: int) -> bool:
        return self.__pressed is not None and self._pattern.notes[self.__pressed].tone == t

    def __transpose_pattern(self, i: int) -> None:
        for n in self._pattern.notes:
            t = n.tone
            if t > 0:
                n.tone = max(min(t+i, 120), 1)


def _to_tone(n: int, o: int) -> int:
    if n == 31:
        return -1
    o += n // 16
    n %= 16
    t = _tones[n]
    if t:
        return t + 12*o
    return 0


_octave_color = (
    0x010,
    0x020,
    0x030,
    0x031,
    0x032,
    0x033,
    0x023,
    0x013,
    0x002,
    0x001
)

_tones = {
    8: 1,    # C
    1: 2,    # C#
    9: 3,    # D
    2: 4,    # D#
    10: 5,   # E
    11: 6,   # F
    4: 7,    # F#
    12: 8,   # G
    5: 9,    # G#
    13: 10,  # A
    6: 11,   # A#
    14: 12,  # B
    15: 13,  # C
    0: 0,
    3: 0,
    7: 0
}
