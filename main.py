"""main of flappybird game with dynamic color restoration and victory sequence.
"""
import sys
import subprocess
from os.path import join

from constant import pygame, WINDOW, WINDOW_WIDTH, WINDOW_HEIGHT, ribbon_image
from constant import clock, GAME_TICK, MAINMENU_ACTIVE
from constant import toolkit, messages, buttons
from classes import Score, Pipe, Bird, Background, Floor, Ribbon, DynamicLighting

MUSIC_END_EVENT = pygame.USEREVENT + 1


def _load_font(size):
    """Load PressStart2P font with fallback to pygame default."""
    path = pygame.font.match_font('pressstart2p')
    if path:
        return pygame.font.Font(path, size)
    try:
        return pygame.font.Font(join('data', 'PressStart2P.ttf'), size)
    except Exception:
        return pygame.font.Font(None, size)


def _draw_shadow_text(surface, font, text, color, x, y, shadow_color=(70, 70, 70), offset=2):
    """Render text with a subtle grey shadow underneath."""
    shadow = font.render(text, True, shadow_color)
    surface.blit(shadow, (x + offset, y + offset))
    label = font.render(text, True, color)
    surface.blit(label, (x, y))


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
    font_big = _load_font(32)
    WINDOW.blit(messages['game_title'],
                (WINDOW_WIDTH / 2 - messages['game_title'].get_width() / 2,
                 100)
                )
    victory_surf = font_big.render("VICTORY!", True, (255, 215, 0))
    _draw_shadow_text(WINDOW, font_big, "VICTORY!", (255, 215, 0),
                      WINDOW_WIDTH // 2 - victory_surf.get_width() // 2, 200)

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
    font_big = _load_font(32)
    font_mid = _load_font(18)
    line1 = "You lose!"
    line2 = "Not enough music"
    line3 = "to save the world!"
    w1 = font_big.render(line1, True, (0, 0, 0)).get_width()
    w2 = font_mid.render(line2, True, (0, 0, 0)).get_width()
    w3 = font_mid.render(line3, True, (0, 0, 0)).get_width()
    _draw_shadow_text(WINDOW, font_big, line1, (255, 80, 80),
                      WINDOW_WIDTH // 2 - w1 // 2, WINDOW_HEIGHT // 2 - 80)
    _draw_shadow_text(WINDOW, font_mid, line2, (255, 140, 140),
                      WINDOW_WIDTH // 2 - w2 // 2, WINDOW_HEIGHT // 2 + 10)
    _draw_shadow_text(WINDOW, font_mid, line3, (255, 140, 140),
                      WINDOW_WIDTH // 2 - w3 // 2, WINDOW_HEIGHT // 2 + 50)

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
    font_big = _load_font(26)
    font_load = _load_font(16)
    line = "Wow! The planet has"
    line2 = "finally been saved!"
    w = font_big.render(line, True, (0, 0, 0)).get_width()
    w2 = font_big.render(line2, True, (0, 0, 0)).get_width()
    _draw_shadow_text(WINDOW, font_big, line, (255, 215, 0),
                      WINDOW_WIDTH // 2 - w // 2, WINDOW_HEIGHT // 2 - 60)
    _draw_shadow_text(WINDOW, font_big, line2, (255, 215, 0),
                      WINDOW_WIDTH // 2 - w2 // 2, WINDOW_HEIGHT // 2 - 10)
    pygame.display.update()

    for frame in range(90):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        dots = '.' * ((frame // 15) % 4)
        load_text = f'Loading cutscene{dots}'
        lw = font_load.render(load_text, True, (0, 0, 0)).get_width()
        pygame.draw.rect(WINDOW, (0, 0, 0),
                         (WINDOW_WIDTH // 2 - 250, 330, 500, 50))
        _draw_shadow_text(WINDOW, font_load, load_text, (200, 200, 255),
                          WINDOW_WIDTH // 2 - lw // 2, 340)
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

    HEAD_START_PX = 300
    pipes = []
    spawn_x = WINDOW_WIDTH + HEAD_START_PX
    while spawn_x < WINDOW_WIDTH + 400 + HEAD_START_PX:
        pipe = Pipe(spawn_x)
        pipes.append(pipe)
        spawn_x += pipe.width

    # Initialization for music tracking
    level_completed = False
    distance_traveled = 0
    hold_frames = 0
    hold_threshold = 5

    if not MAINMENU_ACTIVE:
        try:
            pygame.mixer.music.load(join('data', 'hip.mp3'))
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
            pygame.mixer.music.play()
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

        # INPUT HANDLING
        keys = pygame.key.get_pressed()
        is_holding_input = keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0] == 1
        if is_holding_input:
            hold_frames += 1
        else:
            hold_frames = 0

        if hold_frames >= hold_threshold:
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
            current_alpha = lighting.get_alpha()
            toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha)
            gameover()

        else:
            # Normal gameplay
            distance_traveled += Pipe.velocity
            lighting.update(distance_traveled)
            current_alpha = lighting.get_alpha()

            score.update(Pipe.velocity)
            background.move()
            floor.move()
            bird.move()

            # Update pipes
            for pipe in pipes:
                pipe.move()
                collected_pts = pipe.check_note_collect(bird)
                if collected_pts:
                    score.add_note_points(collected_pts, bird.x_pos, bird.y_pos)
                if pipe.collide(bird):
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

            if MAINMENU_ACTIVE:
                toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha)
                mainmenu()

            # Render current frame
            toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha)


if __name__ == '__main__':
    run()
