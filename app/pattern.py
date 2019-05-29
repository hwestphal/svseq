from launchpad import Launchpad, BUTTON_SESSION, BUTTON_SCENE_1, BUTTON_USER_1, BUTTON_UP, BUTTON_DOWN
from padget import Padget
from .state import state, Pattern as PatternState


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
    def _buttonPressed(self, i: int) -> bool:
        if i == BUTTON_UP and self._pattern.octave > 0:
            self._pattern.octave -= 1
            return True
        if i == BUTTON_DOWN and self._pattern.octave < 7:
            self._pattern.octave += 1
            return True
        return False

    def _render(self) -> None:
        super()._render()
        self._pad.set(BUTTON_UP, 0x030 if self._pattern.octave > 0 else 0x000)
        self._pad.set(
            BUTTON_DOWN, 0x030 if self._pattern.octave < 7 else 0x000)
        for i in range(32, 48):
            self._pad.set(i, 0x000 if i in (32, 35, 39)
                          else _octave_color[self._pattern.octave])
        for i in range(48, 63):
            self._pad.set(i, 0x000 if i in (48, 51, 55)
                          else _octave_color[self._pattern.octave+1])
        self._pad.set(63, 0x003)


def createPattern(pad: Launchpad, t: int, p: int) -> Pattern:
    track = state.tracks[t]
    pattern = track.patterns[p]
    if track.percussion:
        return _PercussionPattern(pad, pattern)
    return _MelodyPattern(pad, pattern)


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
