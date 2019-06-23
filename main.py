from launchpad import Launchpad, BUTTON_MIXER
from ui import App
from project import project
from engine import engine

import pygame.time
from mopyx import action


PROJECT_FILE = 'project.json'

clock = pygame.time.Clock()
pad = Launchpad()

try:
    project.load(PROJECT_FILE)
    app = App(pad)
    app.renderUi()
    pressedForExit = None

    @action
    def process() -> bool:
        global pressedForExit
        for i, v in pad.poll():
            if v:
                app.buttonPressed(i)
                if i == BUTTON_MIXER:
                    pressedForExit = pygame.time.get_ticks()
            else:
                app.buttonReleased(i)
                if i == BUTTON_MIXER:
                    pressedForExit = None

        engine.updateUiState()

        if pressedForExit and pygame.time.get_ticks() - pressedForExit > 2000:
            return False

        return True

    while process():
        pad.refresh()
        clock.tick(60)

finally:
    pad.close()
    project.dump(PROJECT_FILE)
