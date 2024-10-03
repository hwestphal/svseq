from typing import List, Optional, cast

from engine import engine
from launchpad import (BUTTON_DOWN, BUTTON_SCENE_1, BUTTON_UP, BUTTON_USER_1,
                       Launchpad)
from project import Pattern, Track

from .padget import Padget


class _Pattern(Padget):
    def __init__(self, pad: Launchpad, pattern: Pattern, track: Track, tn: int, pn: int):
        super().__init__(pad)
        self._pattern = pattern
        self._track = track
        self._tn = tn
        self._pn = pn

    def _render(self) -> None:
        self._pad.set(BUTTON_SCENE_1, 0x033)


class PercussionPattern(_Pattern):
    def __init__(self, pad: Launchpad, pattern: Pattern, track: Track, tn: int, pn: int):
        super().__init__(pad, pattern, track, tn, pn)
        self.__pressed: Optional[int] = None

    def _buttonPressed(self, i: int) -> bool:
        if i < 32 and self.__pressed is None:
            self.__pressed = i
            return True
        if 40 <= i < 47:
            o = i - 37
            if self.__pressed is not None:
                self.__record(o, self.__pressed, True)
            else:
                if engine.recording == (self._tn, self._pn):
                    self.__record(o, engine.tick % 32, False)
                engine.audioEngine.sendNotes(
                    self._tn, 1 + 12 * o, 128, 128, 128, 0, self._track.instrument * 2 + 3)
            return True
        if i == 47:
            if self.__pressed is not None:
                n = self._pattern.notes[self.__pressed]
                n.tone = 0 if n.tone == -1 else -1
                n.chord = (None, None, None)
            return True
        return False

    def __record(self, o: int, t: int, remove: bool) -> None:
        pt = 1 + 12 * o
        n = self._pattern.notes[t]
        ts = []
        if n.tone > 0:
            ts.append(n.tone)
            for j in range(3):
                if n.chord[j] is not None:
                    ts.append(n.tone + cast(int, n.chord[j]))
        if pt in ts:
            if remove:
                ts.remove(pt)
        elif len(ts) < 4:
            ts.append(pt)
        if ts:
            n.tone = ts[0]
        else:
            n.tone = 0
        cs: List[Optional[int]] = [None, None, None]
        for i in range(1, len(ts)):
            cs[i - 1] = ts[i] - ts[0]
        n.chord = (cs[0], cs[1], cs[2])

    def _buttonReleased(self, i: int) -> bool:
        if i == self.__pressed:
            self.__pressed = None
            return True
        if 40 <= i < 47 and not engine.playing:
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
        if self.__pressed is not None:
            pt = self._pattern.notes[self.__pressed].tone
            c = self._pattern.notes[self.__pressed].chord
            return t in (pt, pt + (c[0] or 0), pt + (c[1] or 0), pt + (c[2] or 0))
        return False


class MelodyPattern(_Pattern):
    def __init__(self, pad: Launchpad, pattern: Pattern, track: Track, tn: int, pn: int):
        super().__init__(pad, pattern, track, tn, pn)
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
        if 32 <= i < 64:
            tone = _to_tone(i-32, self._pattern.octave)
            if self.__pressed is not None:
                self._pattern.notes[self.__pressed].tone = tone
            elif tone > 0:
                if engine.recording == (self._tn, self._pn):
                    n = self._pattern.notes[engine.tick % 32]
                    n.tone = tone
                    n.chord = (None, None, None)
                engine.audioEngine.sendNotes(
                    self._tn, tone, 128, 128, 128, 0, self._track.instrument * 2 + 2)
            return True
        return False

    def _buttonReleased(self, i: int) -> bool:
        if i == BUTTON_USER_1:
            self.__transpose = False
            return True
        if i == self.__pressed:
            self.__pressed = None
            return True
        if 32 <= i < 64:
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
