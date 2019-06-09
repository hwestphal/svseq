from launchpad import Launchpad, BUTTON_SESSION, BUTTON_SCENE_1, BUTTON_USER_1, BUTTON_UP, BUTTON_DOWN
from padget import Padget
from .state import state, Pattern as PatternState
from typing import Optional


class Pattern(Padget):
    def __init__(self, pad: Launchpad, pattern: PatternState):
        super().__init__(pad)
        self._pattern = pattern

    def _render(self) -> None:
        self._pad.set(BUTTON_SESSION, 0x003)
        self._pad.set(BUTTON_USER_1, 0x000)
        for i in range(8):
            self._pad.set(BUTTON_SCENE_1 + i, 0x000)
        notes = self._pattern.notes
        for i in range(32):
            tone = notes[i].tone
            if tone == -1:
                c = 0x003
            elif tone == 0:
                c = 0x000
            else:
                c = 0x030
            self._pad.set(i, c)


class _PercussionPattern(Pattern):
    def _buttonPressed(self, i: int) -> bool:
        if i < 32:
            tone = self._pattern.notes[i].tone
            if tone:
                self._pattern.notes[i].tone = 0
            else:
                self._pattern.notes[i].tone = 61  # C5
            return True
        return False

    def _render(self) -> None:
        super()._render()
        for i in range(32, 64):
            self._pad.set(i, 0x000)


class _MelodyPattern(Pattern):
    def __init__(self, pad: Launchpad, pattern: PatternState):
        super().__init__(pad, pattern)
        self.__pressed: Optional[int] = None

    def _buttonPressed(self, i: int) -> bool:
        if i == BUTTON_UP and self._pattern.octave > 0:
            self._pattern.octave -= 1
            return True
        if i == BUTTON_DOWN and self._pattern.octave < 7:
            self._pattern.octave += 1
            return True
        if i < 32 and self.__pressed is None:
            self.__pressed = i
            return True
        if i >= 32 and i < 64:
            if self.__pressed is not None:
                self._pattern.notes[self.__pressed].tone = _to_tone(
                    i-32, self._pattern.octave)
            return True
        return False

    def _buttonReleased(self, i: int) -> bool:
        if i == self.__pressed:
            self.__pressed = None
            return True
        return False

    def _render(self) -> None:
        super()._render()
        self._pad.set(BUTTON_UP, 0x030 if self._pattern.octave > 0 else 0x000)
        self._pad.set(
            BUTTON_DOWN, 0x030 if self._pattern.octave < 7 else 0x000)
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


def createPattern(pad: Launchpad, t: int, p: int) -> Pattern:
    track = state.tracks[t]
    pattern = track.patterns[p]
    if track.percussion:
        return _PercussionPattern(pad, pattern)
    return _MelodyPattern(pad, pattern)


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
