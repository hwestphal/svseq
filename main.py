import pygame.time
from launchpad import Launchpad, BUTTON_MIXER
from app import App


clock = pygame.time.Clock()
pad = Launchpad()

try:
    pad.set(BUTTON_MIXER, 0x130)
    pad.refresh()
    pygame.time.wait(500)
    pad.set(BUTTON_MIXER, 0x000)
    pad.refresh()

    app = App(pad)
    app.renderUi()
    pressedForExit = None
    while True:
        for i, v in pad.poll():
            if v:
                app.buttonPressed(i)
                if i == BUTTON_MIXER:
                    pressedForExit = pygame.time.get_ticks()
            else:
                app.buttonReleased(i)
                if i == BUTTON_MIXER:
                    pressedForExit = None

        if pressedForExit and pygame.time.get_ticks() - pressedForExit > 2000:
            break

        pad.refresh()
        clock.tick(60)

finally:
    pad.close()
