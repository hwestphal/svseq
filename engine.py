from project import project
from audio.audio_engine import Engine as AudioEngine

from mopyx import model, action, render
from math import floor
from datetime import timedelta
from typing import List, Optional


class Engine:
    def __init__(self) -> None:
        self.uiState = UiState()
        self.playing = False
        self.pattern: List[Optional[int]] = [None] * 8
        self.audioEngine = AudioEngine(
            project.tempo, 8, timedelta(milliseconds=project.latency * 5))
        self.__tempo_changed()
        self.__latency_changed()

    def startOrStopPattern(self, track: int, pattern: int) -> None:
        if not self.playing:
            for i in range(8):
                self.pattern[i] = pattern if i == track else None
            self.playing = True
            self.audioEngine.start()
        else:
            self.playing = False
            self.audioEngine.stop()

    def startOrStopSession(self) -> None:
        if not self.playing:
            for i in range(8):
                s = project.tracks[i].sequence
                self.pattern[i] = s[0] if s else None
            self.playing = True
            self.audioEngine.start()
        else:
            self.playing = False
            self.audioEngine.stop()

    @action
    def updateUiState(self) -> None:
        if not self.playing and self.uiState.playing:
            self.uiState.playing = 0

        tempo, phase = self.audioEngine.getState()
        if tempo != self.engineTempo:
            project.tempo = max(min(round(tempo), 240), 40)

        if self.playing:
            for i, p in enumerate(self.pattern):
                if p != self.uiState.pattern[i]:
                    self.uiState.pattern[i] = p
            beat = floor(phase)
            if beat < 0:
                beat += 8
                if self.uiState.playing >= 0:
                    self.uiState.playing = -1
            elif self.uiState.playing <= 0:
                self.uiState.playing = 1
            if beat != self.uiState.beat:
                self.uiState.beat = beat

    @render
    def __tempo_changed(self) -> None:
        self.audioEngine.setTempo(project.tempo)
        self.engineTempo = project.tempo

    @render
    def __latency_changed(self) -> None:
        self.audioEngine.setLatency(
            timedelta(milliseconds=project.latency * 5))


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
