import json
from typing import Any, Dict, List, Optional, Tuple, cast

from mopyx import action, computed

from model import model


@model
class Project:
    def __init__(self) -> None:
        # 40 - 240
        self.tempo = 125
        # 0 - 24
        self.latency = 0
        # 1 - 8
        self.quantum = 8
        # 0 - 24
        self.swing = 0
        self.tracks: List[Track] = []
        for i in range(5):
            self.tracks.append(Track(False, i))
        for i in range(3):
            self.tracks.append(Track(True, i))

    @computed
    def dict(self) -> Dict[str, Any]:
        return {
            'tempo': self.tempo,
            'latency': self.latency,
            'quantum': self.quantum,
            'swing': self.swing,
            'tracks': [t.dict for t in self.tracks]
        }

    @action
    def from_dict(self, d: Dict[str, Any]) -> None:
        self.tempo = d['tempo']
        self.latency = d['latency']
        self.quantum = d['quantum']
        self.swing = d['swing']
        for i in range(len(self.tracks)):
            self.tracks[i].from_dict(d['tracks'][i])

    def dump(self, name: str) -> None:
        with open(name, 'w') as f:
            json.dump(self.dict, f)

    def load(self, name: str) -> None:
        try:
            with open(name, 'r') as f:
                d = json.load(f)
                self.from_dict(d)
        except IOError:
            pass


@model
class Track:
    def __init__(self, percussion: bool, instrument: int):
        self.muted = False
        self.volume = 1.0
        self.percussion = percussion
        self.instrument = instrument
        self.sequence: List[int] = []
        self.patterns: List[Pattern] = []
        for i in range(8):
            self.patterns.append(Pattern())

    @computed
    def dict(self) -> Dict[str, Any]:
        return {
            'muted': self.muted,
            'volume': self.volume,
            'percussion': self.percussion,
            'instrument': self.instrument,
            'sequence': self.sequence,
            'patterns': [p.dict for p in self.patterns]
        }

    @action
    def from_dict(self, d: Dict[str, Any]) -> None:
        self.muted = d['muted']
        self.volume = d['volume']
        self.percussion = d['percussion']
        self.instrument = d['instrument']
        self.sequence = d['sequence']
        for i in range(len(self.patterns)):
            self.patterns[i].from_dict(d['patterns'][i])


@model
class Pattern:
    def __init__(self) -> None:
        self.notes: List[Note] = []
        for i in range(32):
            self.notes.append(Note())
        # 0 - 8
        self.octave = 4

    @computed
    def empty(self) -> bool:
        for n in self.notes:
            if not n.empty:
                return False
        return True

    @computed
    def dict(self) -> Dict[str, Any]:
        return {
            'octave': self.octave,
            'notes': [n.dict for n in self.notes]
        }

    @action
    def from_dict(self, d: Dict[str, Any]) -> None:
        self.octave = d['octave']
        for i in range(len(self.notes)):
            self.notes[i].from_dict(d['notes'][i])


@model
class Note:
    def __init__(self) -> None:
        # -1: note off
        # 0: silence
        # 1 - 120: C0 - B9
        self.tone = 0
        self.chord: Tuple[Optional[int], Optional[int],
                          Optional[int]] = (None, None, None)
        # None | 0.0 - 1.0
        self.control: List[Optional[float]] = [None] * 5
        # 0: once
        # 1: twice (1/32)
        # 2: 3 times (1/24, 2/24)
        self.trigger = 0

    @computed
    def empty(self) -> bool:
        if self.tone or self.chord != (None, None, None) or self.trigger:
            return False
        for c in self.control:
            if c is not None:
                return False
        return True

    @computed
    def dict(self) -> Dict[str, Any]:
        return {
            'tone': self.tone,
            'chord': self.chord,
            'control': self.control,
            'trigger': self.trigger
        }

    @action
    def from_dict(self, d: Dict[str, Any]) -> None:
        self.tone = d['tone']
        self.chord = cast(Tuple[Optional[int], Optional[int],
                                Optional[int]], tuple(d['chord']))
        self.control = d['control']
        self.trigger = d['trigger']


project = Project()
