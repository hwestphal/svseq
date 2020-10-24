from project import project, Note
import audio_engine

from mopyx import model, action, render
import os
from math import floor
from datetime import timedelta
from itertools import zip_longest
from typing import List, Tuple, Optional, Generator


class Engine:
    def __init__(self) -> None:
        self.uiState = UiState()
        self.playing = False
        self.recording: Optional[Tuple[int, int]] = None
        self.session = False
        self.tick = 0
        self.pattern: List[Optional[int]] = [None] * 8
        self.audioEngine = audio_engine.Engine(
            project.tempo, project.quantum, timedelta(milliseconds=project.latency * 7))
        self.defaultCtls = self.audioEngine.getCtls()
        self.__tempo_changed()
        self.__latency_changed()
        self.__quantum_changed()

    def startOrStopPattern(self, track: int, pattern: int, record: bool) -> None:
        if not self.playing:
            self.tick = 0
            for i in range(8):
                self.pattern[i] = pattern if i == track else None
            self.__update_events()
            self.session = False
            self.playing = True
            if record:
                self.recording = (track, pattern)
            self.audioEngine.start(record)
        else:
            self.recording = None
            self.playing = False
            self.audioEngine.stop()
            self.__reset_ctls()

    def startOrStopSession(self) -> None:
        if not self.playing:
            self.tick = 0
            for i in range(8):
                s = project.tracks[i].sequence
                self.pattern[i] = s[0] if s else None
            self.__update_events()
            self.session = True
            self.playing = True
            self.audioEngine.start(False)
        else:
            self.playing = False
            self.audioEngine.stop()
            self.__reset_ctls()

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
                if tick % (project.quantum * 4) == 0 and self.session:
                    for i in range(8):
                        s = project.tracks[i].sequence
                        self.pattern[i] = s[(tick // (project.quantum * 4)) %
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
            phase = floor(beat) % project.quantum
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
            tick = self.tick % (project.quantum * 4)
            note: Optional[Note]
            if p is not None and not track.muted:
                note = track.patterns[p].notes[tick]
            elif p is None and not track.muted and tick == 0:
                note = Note()
            else:
                note = None

            if note:
                instrument = track.instrument * 2 + \
                    (3 if track.percussion else 2)
                ctls = []
                for j in range(4):
                    c = note.control[j + 1]
                    ctls.append(round(c * 0x8000)
                                if c is not None else self.defaultCtls[instrument - 2][j] if tick == 0 else None)
                tone = note.tone

                if tone > 0:
                    tones = [tone]
                    for c in note.chord:
                        tones.append((tone + c) if c is not None else 128)
                    ctl0 = note.control[0]
                    vel = round(track.volume *
                                (ctl0 if ctl0 is not None else 1) * 128) + 1
                    for j in range(4):
                        ctl = ctls[j]
                        events.append(
                            (i * 4 + j, tones[j] + note.trigger * 256, vel, instrument, ((j + 6) << 8) if ctl is not None else 0, ctl if ctl is not None else 0))

                else:
                    ctl0 = note.control[0]
                    vel = round(track.volume * ctl0 * 128) + \
                        1 if ctl0 is not None else 0
                    for j in range(4):
                        ctl = ctls[j]
                        if tone or ctl is not None or vel:
                            events.append(
                                (i * 4 + j, 128 if tone or tick == 0 else 0, vel, instrument, ((j + 6) << 8) if ctl is not None else 0, ctl if ctl is not None else 0))

        self.audioEngine.setEvents(events)

    @render
    def __tempo_changed(self) -> None:
        self.audioEngine.setTempo(project.tempo)
        self.engineTempo = project.tempo

    @render
    def __latency_changed(self) -> None:
        self.audioEngine.setLatency(
            timedelta(milliseconds=project.latency * 7))

    @render
    def __quantum_changed(self) -> None:
        self.audioEngine.setQuantum(project.quantum)

    def __reset_ctls(self) -> None:
        for track in project.tracks:
            module = track.instrument * 2 + (3 if track.percussion else 2)
            self.audioEngine.setCtls(module, self.defaultCtls[module - 2])


@model
class UiState:
    def __init__(self) -> None:
        # -1 | 0 | 1
        self.playing = 0
        # 0 - 7
        self.phase = 0
        # None | 0 - 7 per track
        self.pattern: List[Optional[int]] = [None] * 8


def modules(subfolder: str) -> Generator[str, None, None]:
    for entry in sorted(os.scandir(os.path.join('./instruments', subfolder)), key=lambda e: e.name):
        if entry.name.endswith('.sunsynth'):
            yield os.path.abspath(entry.path)


instruments = []
for ms in zip_longest(modules('melody'), modules('percussion')):
    for m in ms:
        instruments.append(m or '')

audio_engine.init_sunvox(instruments)

engine = Engine()
