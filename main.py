"""main of flappybird game with dynamic color restoration and victory sequence.
"""
import sys
import subprocess
from os.path import join

from constant import pygame, WINDOW, WINDOW_WIDTH, WINDOW_HEIGHT, ribbon_image
from constant import clock, GAME_TICK, MAINMENU_ACTIVE
from constant import toolkit, messages, buttons
from classes import Score, Pipe, Bird, Background, Floor, Ribbon, DynamicLighting, VictoryPlatform

MUSIC_END_EVENT = pygame.USEREVENT + 1


def gameover():
    """For when the player loses the game
    """
    pygame.mixer.music.stop()
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


def victory_screen():
    """Display victory screen when player completes the level
    """
    WINDOW.blit(messages['game_title'],
                (WINDOW_WIDTH / 2 - messages['game_title'].get_width() / 2,
                 100)
                )

    # Draw "VICTORY" or similar message
    victory_text = pygame.font.Font(None, 72).render("VICTORY!", True, (255, 215, 0))
    WINDOW.blit(victory_text,
                (WINDOW_WIDTH / 2 - victory_text.get_width() / 2,
                 200)
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


def lose_screen():
    """Display when the player runs out of time without reaching 25 points."""
    pygame.mixer.music.stop()
    font_big = pygame.font.Font(None, 52)
    font_mid = pygame.font.Font(None, 36)
    line1 = font_big.render("You loose,", True, (255, 80, 80))
    line2 = font_mid.render("not enough music to save the world!", True, (255, 130, 130))
    WINDOW.blit(line1, (WINDOW_WIDTH / 2 - line1.get_width() / 2, 240))
    WINDOW.blit(line2, (WINDOW_WIDTH / 2 - line2.get_width() / 2, 310))

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


def win_screen():
    """Display when the player reaches 25 points — then launch the cutscene."""
    pygame.mixer.music.stop()
    font_big = pygame.font.Font(None, 52)
    font_load = pygame.font.Font(None, 36)
    msg = font_big.render("Wow! The planet has finally been saved!", True, (255, 215, 0))
    WINDOW.blit(msg, (WINDOW_WIDTH / 2 - msg.get_width() / 2, 250))
    pygame.display.update()

    for frame in range(90):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        dots = '.' * ((frame // 15) % 4)
        load_surf = font_load.render(f'Loading cutscene{dots}', True, (200, 200, 255))
        pygame.draw.rect(WINDOW, (0, 0, 0),
                         (WINDOW_WIDTH // 2 - 200, 330, 400, 40))
        WINDOW.blit(load_surf, (WINDOW_WIDTH / 2 - load_surf.get_width() / 2, 335))
        pygame.display.update()
        clock.tick(30)

    subprocess.Popen([sys.executable, 'cutscene.py'])
    pygame.quit()
    sys.exit()


def mainmenu():
    """Main menu to start the game
    """
    pygame.mixer.music.stop()
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

    Features:
    - Color that returns as the bird progresses
    - Victory platform appears when music ends
    - Bird auto-celebrates on platform
    """
    game_start_time = pygame.time.get_ticks()
    GAME_DURATION_MS = 65000
    score = Score()
    background = Background()
    floor = Floor()

    # Initialize ribbon if image is available
    ribbon = None
    if ribbon_image:
        ribbon = Ribbon(ribbon_image, max_segments=12)

    # Initialize dynamic color restoration system
    lighting = DynamicLighting()

    bird = Bird(80, 350, ribbon=ribbon)

    # Initialize victory platform (initially inactive)
    victory_platform = None

    HEAD_START_PX = 300 
    pipes = []
    spawn_x = WINDOW_WIDTH + HEAD_START_PX
    while spawn_x < WINDOW_WIDTH + 400 + HEAD_START_PX:
        pipe = Pipe(spawn_x)
        pipes.append(pipe)
        spawn_x += pipe.width

    # Initialization for music tracking
    music_started = False
    music_elapsed_time = 0
    total_music_duration = 0  # Will be set when music starts
    level_completed = False
    celebration_started = False
    distance_traveled = 0
    hold_frames = 0
    hold_threshold = 5

    if not MAINMENU_ACTIVE:
        try:
            pygame.mixer.music.load(join('data', 'hip.mp3'))
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
            pygame.mixer.music.play()
            music_started = True
        except pygame.error as error:
            print(f"Warning: could not load data/hip.mp3: {error}")

    right_edge = max((pipe.x_pos + pipe.width for pipe in pipes), default=0)
    while right_edge < WINDOW_WIDTH + 400 + HEAD_START_PX:
        new_pipe = Pipe(right_edge)
        pipes.append(new_pipe)
        right_edge += new_pipe.width

    while True:
        clock.tick(GAME_TICK)

        # EVENT HANDLING
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # MUSIC TRACKING - Modify this section to work with your music system
            # This is a placeholder - integrate with your actual music/audio system
            if event.type == MUSIC_END_EVENT:
                level_completed = True
                # Create victory platform at current bird position
                victory_platform = VictoryPlatform(bird.x_pos + WINDOW_WIDTH)
                victory_platform.set_active()

        # INPUT HANDLING
        keys = pygame.key.get_pressed()
        is_holding_input = keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0] == 1
        if is_holding_input:
            hold_frames += 1
        else:
            hold_frames = 0

        if hold_frames >= hold_threshold:
            if not bird.is_celebrating:  # Can't jump while celebrating
                bird.jump()

        # TIMER CHECK
        if not MAINMENU_ACTIVE:
            elapsed = pygame.time.get_ticks() - game_start_time
            if elapsed >= GAME_DURATION_MS:
                if score.note_points >= Score.GOAL:
                    win_screen()
                else:
                    lose_screen()

        # GAME STATE CHECK
        if bird.crashed:
            # Display with current color restoration
            current_alpha = lighting.get_alpha()
            toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha)
            gameover()

        elif level_completed and celebration_started:
            # Victory sequence - bird celebrating
            current_alpha = 255  # Full color at victory
            bird.move()
            if victory_platform and victory_platform.is_active:
                victory_platform.move()
            toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha, victory_platform)

            # Check if celebration is complete
            if not bird.is_celebrating:
                # Celebration finished, show victory screen
                victory_screen()

        else:
            # Normal gameplay
            # Update dynamic color restoration based on bird position
            distance_traveled += Pipe.velocity
            lighting.update(distance_traveled)
            current_alpha = lighting.get_alpha()

            # Update game state
            score.update(Pipe.velocity)
            background.move()
            floor.move()
            bird.move()

            # Move victory platform if it exists
            if victory_platform and victory_platform.is_active:
                victory_platform.move()

            # Update pipes
            for pipe in pipes:
                pipe.move()
                collected_pts = pipe.check_note_collect(bird)
                if collected_pts:
                    score.add_note_points(collected_pts, bird.x_pos, bird.y_pos)
                if pipe.collide(bird):
                    # Collision with pipe - game over
                    toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha)
                    gameover()

            # Remove off-screen pipes
            pipes = [pipe for pipe in pipes if pipe.x_pos + pipe.width > 0]

            # Spawn new pipes (unless level is completed)
            if not level_completed:
                right_edge = max((pipe.x_pos + pipe.width for pipe in pipes), default=0)
                while right_edge < WINDOW_WIDTH + 400:
                    new_pipe = Pipe(right_edge)
                    pipes.append(new_pipe)
                    right_edge += new_pipe.width

            # Check if bird landed on victory platform
            if victory_platform and victory_platform.is_active and victory_platform.check_landing(bird):
                if not celebration_started:
                    celebration_started = True
                    bird.celebration_jump()  # Start auto-jumping celebration

            if MAINMENU_ACTIVE:
                toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha)
                mainmenu()

            # Render current frame
            toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha, victory_platform)


if __name__ == '__main__':
    run()
