from launchpad import Launchpad, BUTTON_LEFT, BUTTON_SCENE_1, BUTTON_UP, BUTTON_DOWN
from padget import Padget
from typing import List
from .project import project


class Tempo(Padget):

    def __init__(self, pad: Launchpad):
        super().__init__(pad)

    def _buttonPressed(self, i: int) -> bool:
        if i == BUTTON_UP and project.tempo < 240:
            project.tempo += 1
            return True
        if i == BUTTON_DOWN and project.tempo > 40:
            project.tempo -= 1
            return True
        if i == BUTTON_SCENE_1 and project.tempo <= 230:
            project.tempo += 10
            return True
        if i == BUTTON_SCENE_1+1 and project.tempo >= 50:
            project.tempo -= 10
            return True
        return False

    def _render(self) -> None:
        self._pad.set(BUTTON_LEFT, 0x033)
        self._pad.set(BUTTON_SCENE_1, 0x030 if project.tempo <= 230 else 0x000)
        self._pad.set(BUTTON_SCENE_1 + 1,
                      0x030 if project.tempo >= 50 else 0x000)
        for i in range(2, 8):
            self._pad.set(BUTTON_SCENE_1 + i, 0x000)
        self._pad.set(BUTTON_UP, 0x030 if project.tempo < 240 else 0x000)
        self._pad.set(BUTTON_DOWN, 0x030 if project.tempo > 40 else 0x000)
        for i in range(8):
            self._pad.set(i, 0x000)

        d = _DIGITS_2[project.tempo // 100]
        for i in range(5):
            for j in range(2):
                self._pad.set(8 + i * 8 + j, 0x033 if d[i][j] else 0x000)

        d = _DIGITS_3[(project.tempo // 10) % 10]
        for i in range(5):
            for j in range(3):
                self._pad.set(8 + i * 8 + j + 2, 0x030 if d[i][j] else 0x000)

        d = _DIGITS_3[project.tempo % 10]
        for i in range(5):
            for j in range(3):
                self._pad.set(8 + i * 8 + j + 5, 0x003 if d[i][j] else 0x000)

        for i in range(48, 64):
            self._pad.set(i, 0x000)


def _to_data(data: str, width: int, height: int = 5) -> List[List[List[int]]]:
    lines = data.splitlines()[1:]
    assert len(lines) % (height + 1) == height
    chars = []
    while lines:
        rows = []
        for i in range(height):
            line = (lines[i] + ' ' * width)[:width]
            row = []
            for c in line:
                row.append(1 if c == '*' else 0)
            rows.append(row)
        chars.append(rows)
        lines = lines[height+1:]
    return chars


_DIGITS_2 = _to_data("""






*
*
*
*
*

**
 *
**
*
**
""", 2)

_DIGITS_3 = _to_data("""
***
* *
* *
* *
***

 *
 *
 *
 *
 *

***
  *
***
*
***

***
  *
***
  *
***

* *
* *
***
  *
  *

***
*
***
  *
***

***
*
***
* *
***

***
  *
  *
  *
  *

***
* *
***
* *
***

***
* *
***
  *
***
""", 3)
