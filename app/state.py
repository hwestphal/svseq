from mopyx import model, computed
from typing import List


@model
class State:
    def __init__(self) -> None:
        self.tracks: List[Track] = []
        for i in range(8):
            self.tracks.append(Track(True if i % 2 else False))


@model
class Track:
    def __init__(self, percussion: bool):
        self.muted = False
        self.volume = 1.0
        self.percussion = percussion
        self.instrument = 0
        self.sequence: List[int] = []
        self.patterns: List[Pattern] = []
        for i in range(8):
            self.patterns.append(Pattern())


@model
class Pattern:
    def __init__(self) -> None:
        self.notes: List[Note] = []
        for i in range(32):
            self.notes.append(Note())
        # 0-8
        self.octave = 3

    @computed
    def empty(self) -> bool:
        for n in self.notes:
            if n.tone:
                return False
        return True


@model
class Note:
    def __init__(self) -> None:
        # -1: note off
        # 0: silence
        # 1 - 108: C1 - B9
        self.tone = 0


state = State()
