from mopyx import action, render, model
from launchpad import Launchpad
from typing import Callable, Any


@model
class Padget:

    def __init__(self, pad: Launchpad):
        self._pad = pad

    @render
    def renderUi(self) -> None:
        self._render()
        for name in self.__dict__:
            value = getattr(self, name)
            if not isinstance(value, list):
                value = [value]
            for child in value:
                if isinstance(child, Padget):
                    child.renderUi()

    @action
    def buttonPressed(self, i: int) -> bool:
        if self._buttonPressed(i):
            return True
        return self.__forChildren(lambda c: c.buttonPressed(i))

    @action
    def buttonReleased(self, i: int) -> bool:
        if self._buttonReleased(i):
            return True
        return self.__forChildren(lambda c: c.buttonReleased(i))

    def _render(self) -> None:
        pass

    def _buttonPressed(self, i: int) -> bool:
        return False

    def _buttonReleased(self, i: int) -> bool:
        return False

    def __forChildren(self, f: Callable[['Padget'], Any]) -> bool:
        for value in self.__dict__.values():
            if not isinstance(value, list):
                value = [value]
            for child in value:
                if isinstance(child, Padget) and f(child):
                    return True
        return False
