"""main of flappybird game.
"""
import sys
from random import randrange

from constant import pygame, WINDOW, WINDOW_WIDTH
from constant import clock, GAME_TICK, MAINMENU_ACTIVE
from constant import toolkit, messages, buttons
from classes import Score, Pipe, Bird, Background


def gameover():
    """For when the player loses the game
    """
    WINDOW.blit(messages['game_title'],
                (WINDOW_WIDTH / 2 - messages['game_title'].get_width() / 2,
                 100)
                )
    WINDOW.blit(messages['gameover'],
                (WINDOW_WIDTH / 2 - messages['gameover'].get_width() / 2,
                 180)
                )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        toolkit.button(buttons['play'],
                       WINDOW_WIDTH / 2 - buttons['play'].get_width() / 2,
                       550,
                       run)

        pygame.display.update()
        clock.tick(30)


def mainmenu():
    """Main menu to start the game
    """
    WINDOW.blit(messages['game_title'],
                (WINDOW_WIDTH / 2 - messages['game_title'].get_width() / 2,
                 200)
                )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        toolkit.button(buttons['play'],
                       WINDOW_WIDTH / 2 - buttons['play'].get_width() / 2,
                       600,
                       close_mainmenu)

        pygame.display.update()
        clock.tick(30)


def close_mainmenu():
    """Close main menu and start the game
    """
    global MAINMENU_ACTIVE
    MAINMENU_ACTIVE = False
    run()


def run():
    """This is the base function of the game,
    where all processes are controlled
    """
    score = Score()
    background = Background()
    bird = Bird(80, 200)
    pipes = [
        Pipe(WINDOW_WIDTH + 100),
        Pipe(WINDOW_WIDTH + 400),
        Pipe(WINDOW_WIDTH + 700)
    ]

    while True:
        clock.tick(GAME_TICK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0] == 1:
            bird.jump()

        add_pipe = False
        if bird.crashed:
            toolkit.update_display(background, pipes, bird, score)
            gameover()
        else:
            background.move()
            bird.move()
            for pipe in pipes:
                pipe.move()
                if pipe.collide(bird):
                    toolkit.update_display(background, pipes, bird, score)
                    gameover()
                if not pipe.passed and pipe.x_pos < bird.x_pos:
                    pipe.passed = True
                    add_pipe = True

            pipes = [pipe for pipe in pipes if pipe.x_pos + pipe.BUILDINGS[pipe.building].get_width() > 0]

        if add_pipe:
            score.add_score()
            spawn_x = WINDOW_WIDTH + randrange(80, 120)
            pipes.append(Pipe(spawn_x))

        if MAINMENU_ACTIVE:
            toolkit.update_display(background)
            mainmenu()

        toolkit.update_display(background, pipes, bird, score)


if __name__ == '__main__':
    run()
