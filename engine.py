from project import project

from mopyx import model, action
from typing import List, Optional


class Engine:
    def __init__(self) -> None:
        self.uiState = UiState()
        self.playing = False
        self.pattern: List[Optional[int]] = [None] * 8

    def startOrStopPattern(self, track: int, pattern: int) -> None:
        if not self.playing:
            for i in range(8):
                self.pattern[i] = pattern if i == track else None
            self.playing = True
        else:
            self.playing = False

    def startOrStopSession(self) -> None:
        if not self.playing:
            for i in range(8):
                s = project.tracks[i].sequence
                self.pattern[i] = s[0] if s else None
            self.playing = True
        else:
            self.playing = False

    @action
    def updateUiState(self) -> None:
        if self.playing and not self.uiState.playing or not self.playing and self.uiState.playing:
            self.uiState.playing = 1 if self.playing else 0
        if self.playing:
            for i, p in enumerate(self.pattern):
                if p != self.uiState.pattern[i]:
                    self.uiState.pattern[i] = p


@model
class UiState:
    def __init__(self) -> None:
        # -1 | 0 | 1
        self.playing = 0
        # 0 - 7
        self.beat = 0
        # None | 0 - 7 per track
        self.pattern: List[Optional[int]] = [None] * 8


engine = Engine()
