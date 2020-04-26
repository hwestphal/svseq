from project import project
from audio import audio_engine
from audio.audio_engine import Engine as AudioEngine

from mopyx import model, action, render
from math import floor
from datetime import timedelta
from typing import List, Tuple, Optional


audio_engine.init_sunvox('svseq.sunvox')


class Engine:
    def __init__(self) -> None:
        self.uiState = UiState()
        self.playing = False
        self.session = False
        self.tick = 0
        self.pattern: List[Optional[int]] = [None] * 8
        self.audioEngine = AudioEngine(
            project.tempo, 8, timedelta(milliseconds=project.latency * 5))
        self.__tempo_changed()
        self.__latency_changed()

    def startOrStopPattern(self, track: int, pattern: int) -> None:
        if not self.playing:
            self.tick = 0
            for i in range(8):
                self.pattern[i] = pattern if i == track else None
            self.__update_events()
            self.session = False
            self.playing = True
            self.audioEngine.start()
        else:
            self.playing = False
            self.audioEngine.stop()

    def startOrStopSession(self) -> None:
        if not self.playing:
            self.tick = 0
            for i in range(8):
                s = project.tracks[i].sequence
                self.pattern[i] = s[0] if s else None
            self.__update_events()
            self.session = True
            self.playing = True
            self.audioEngine.start()
        else:
            self.playing = False
            self.audioEngine.stop()

    @action
    def update(self) -> None:
        if not self.playing and self.uiState.playing:
            self.uiState.playing = 0

        tempo, beat = self.audioEngine.getState()
        if tempo != self.engineTempo:
            project.tempo = max(min(round(tempo), 240), 40)

        if self.playing:
            tick = (floor(beat * 4) + 1) if beat >= 0 else 0
            if self.tick == 0 and tick == 1 or self.tick > 0 and tick > self.tick:
                self.tick = tick
                if tick % 32 == 0 and self.session:
                    for i in range(8):
                        s = project.tracks[i].sequence
                        self.pattern[i] = s[(tick // 32) %
                                            len(s)] if s else None
                self.__update_events()

            for i, p in enumerate(self.pattern):
                if p != self.uiState.pattern[i]:
                    self.uiState.pattern[i] = p
            if beat < 0:
                if self.uiState.playing >= 0:
                    self.uiState.playing = -1
            elif self.uiState.playing <= 0:
                self.uiState.playing = 1
            phase = floor(beat) % 8
            if phase != self.uiState.phase:
                self.uiState.phase = phase

    def __update_events(self) -> None:
        """
        track_num - track number within the pattern;
        note: 0 - nothing; 1..127 - note num; 128 - note off; 129, 130... - see NOTECMD_xxx defines;
        vel: velocity 1..129; 0 - default;
        module: 0 (empty) or module number + 1 (1..65535);
        ctl: 0xCCEE. CC - number of a controller (1..255). EE - effect;
        ctl_val: value of controller or effect.
        """
        events: List[Tuple[int, int, int, int, int, int]] = []
        for i in range(8):
            track = project.tracks[i]
            p = self.pattern[i]
            if p is not None and not track.muted:
                instrument = track.instrument * 2 + \
                    (3 if track.percussion else 2)
                note = track.patterns[p].notes[self.tick % 32]
                ctl1 = note.control[1]
                ctl1_value = round(ctl1 * 0x8000) if ctl1 is not None else 0
                if note.tone > 0:
                    ctl0 = note.control[0]
                    vel = round(track.volume *
                                (ctl0 if ctl0 is not None else 1) * 128) + 1
                    events.append(
                        (i * 4, note.tone, vel, instrument, 0x600 if ctl1 is not None else 0, ctl1_value))
                elif note.tone or ctl1 is not None:
                    events.append(
                        (i * 4, 128 if note.tone == -1 else 0, 0, instrument, 0x600 if ctl1 is not None else 0, ctl1_value))
                for j in range(2, 5):
                    ctl = note.control[j]
                    if ctl is not None:
                        events.append(
                            (i * 4 + (j - 1), 0, 0, instrument, (j + 5) << 8, round(ctl * 0x8000)))
        self.audioEngine.setEvents(events)

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
        self.phase = 0
        # None | 0 - 7 per track
        self.pattern: List[Optional[int]] = [None] * 8


engine = Engine()
