import pygame
import pygame.midi
from mopyx import action

from engine import engine
from launchpad import BUTTON_MIXER, Launchpad
from project import project
from ui import App

PROJECT_FILE = 'project.json'

pygame.init()
pygame.midi.init()

clock = pygame.time.Clock()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pad = Launchpad(screen)

try:
    project.load(PROJECT_FILE)
    engine.initVolume()
    clock.tick(1)
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

        engine.update()

        if pressedForExit and pygame.time.get_ticks() - pressedForExit > 2000:
            return False

        return True

    while process():
        pad.refresh()
        pygame.display.flip()
        clock.tick(60)

finally:
    pad.close()
    project.dump(PROJECT_FILE)
    pygame.quit()
