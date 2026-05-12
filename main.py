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
    """Load PressStart2P font with fallback."""
    try:
        return pygame.font.Font(join('data', 'PressStart2P.ttf'), size)
    except Exception as e:
        print(f"Warning: could not load PressStart2P.ttf: {e}")
        return pygame.font.Font(None, size)


def _draw_shadow_text(surface, font, text, color, x, y,
                      shadow_color=(95, 95, 95), offset=3):
    """Render text with a soft natural grey shadow."""

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


def result_screen(won, note_points, distance, best_score):
    """Scroll-based end screen shown after the timer runs out.
    Displays scroll.png centered on black, with win/lose text and stats.
    Auto-advances after 6 seconds or when the player clicks NEXT.
    Win → launch cutscene.py.  Lose → loop via run().
    """
    pygame.mixer.music.stop()

    font_big = _load_font(28)
    font_med = _load_font(18)
    font_sm  = _load_font(14)

    try:
        scroll_raw = pygame.image.load(join('data', 'scroll.png')).convert_alpha()
        scroll_h = int(WINDOW_HEIGHT * 0.82)
        scale_f  = scroll_h / scroll_raw.get_height()
        scroll_w = int(scroll_raw.get_width() * scale_f)
        scroll_img = pygame.transform.smoothscale(scroll_raw, (scroll_w, scroll_h))
    except Exception as e:
        print(f"Warning: could not load scroll.png: {e}")
        scroll_img = None
        scroll_w, scroll_h = 0, 0

    scroll_x = WINDOW_WIDTH  // 2 - scroll_w // 2
    scroll_y = WINDOW_HEIGHT // 2 - scroll_h // 2

    # Inner parchment content area (approx proportions of the scroll image)
    content_top = scroll_y + int(scroll_h * 0.23)
    content_bot = scroll_y + int(scroll_h * 0.82)
    cx = WINDOW_WIDTH // 2

    if won:
        headline    = ["WOW! The planet has", "finally been saved!"]
        head_color  = (90, 35, 5)
    else:
        headline    = ["Fails to score enough music!", "But this is NOT the end yet!"]
        head_color  = (90, 35, 5)

    dist_m = distance // 60
    stats = [
        f"DISTANCE: {dist_m}m",
        f"POINTS:   {note_points}/25",
        f"BEST:     {best_score}",
    ]

    btn_w, btn_h = 200, 44
    next_rect = pygame.Rect(cx - btn_w // 2, content_bot + 18, btn_w, btn_h)

    start_ms = pygame.time.get_ticks()
    AUTO_MS  = 6000
    advance  = False

    while not advance:
        WINDOW.fill((0, 0, 0))
        if scroll_img:
            WINDOW.blit(scroll_img, (scroll_x, scroll_y))

        # Headline (big text on parchment)
        y = content_top + 16
        for line in headline:
            lw = font_big.size(line)[0]
            _draw_shadow_text(WINDOW, font_big, line, head_color,
                              cx - lw // 2, y, shadow_color=(180, 130, 60))
            y += font_big.get_linesize() + 8

        y += 14
        for stat in stats:
            sw = font_med.size(stat)[0]
            _draw_shadow_text(WINDOW, font_med, stat, (75, 35, 8),
                              cx - sw // 2, y, shadow_color=(160, 110, 50))
            y += font_med.get_linesize() + 8

        # NEXT button below the scroll
        mouse     = pygame.mouse.get_pos()
        btn_col   = (110, 75, 20) if next_rect.collidepoint(mouse) else (75, 48, 10)
        pygame.draw.rect(WINDOW, btn_col, next_rect, border_radius=10)
        pygame.draw.rect(WINDOW, (210, 165, 60), next_rect, width=2, border_radius=10)
        nw, nh = font_sm.size("NEXT >")
        _draw_shadow_text(WINDOW, font_sm, "NEXT >", (255, 220, 100),
                          next_rect.x + btn_w // 2 - nw // 2,
                          next_rect.y + btn_h // 2 - nh // 2,
                          shadow_color=(120, 80, 0))

        pygame.display.update()
        clock.tick(30)

        if pygame.time.get_ticks() - start_ms >= AUTO_MS:
            advance = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if next_rect.collidepoint(event.pos):
                    advance = True

    if won:
        subprocess.Popen([sys.executable, 'cutscene.py'])
        pygame.quit()
        sys.exit()
    else:
        run()


def pause_menu(score, background, pipes, floor, bird, ribbon, lighting):
    """Pause overlay opened with S key or the settings icon.
    Shows volume control (click/drag the bar) and a go-back-to-main-menu button.
    """
    pygame.mixer.music.pause()

    # Snapshot current frame once — prevents dark re-render glitch
    screen_snapshot = WINDOW.copy()

    font_title = _load_font(24)
    font_label = _load_font(12)
    font_btn   = _load_font(14)
    volume = pygame.mixer.music.get_volume()

    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))

    cx = WINDOW_WIDTH // 2
    cy = WINDOW_HEIGHT // 2

    btn_w, btn_h = 320, 52
    resume_rect = pygame.Rect(cx - btn_w // 2, cy + 40,  btn_w, btn_h)
    menu_rect   = pygame.Rect(cx - btn_w // 2, cy + 110, btn_w, btn_h)

    vol_bar_w, vol_bar_h = 280, 20
    vol_bar_x = cx - vol_bar_w // 2
    vol_bar_y = cy - 28
    vol_hit_rect = pygame.Rect(vol_bar_x, vol_bar_y - 6, vol_bar_w, vol_bar_h + 12)

    dragging_vol = False

    def _draw_btn(rect, text, base=(50, 50, 80), hover=(80, 80, 120)):
        mouse = pygame.mouse.get_pos()
        color = hover if rect.collidepoint(mouse) else base
        pygame.draw.rect(WINDOW, color, rect, border_radius=10)
        pygame.draw.rect(WINDOW, (180, 180, 255), rect, width=2, border_radius=10)
        tw, th = font_btn.size(text)
        _draw_shadow_text(WINDOW, font_btn, text, (255, 255, 255),
                          rect.x + rect.w // 2 - tw // 2,
                          rect.y + rect.h // 2 - th // 2)

    while True:
        WINDOW.blit(screen_snapshot, (0, 0))
        WINDOW.blit(overlay, (0, 0))

        title_w = font_title.size("PAUSED")[0]
        _draw_shadow_text(WINDOW, font_title, "PAUSED", (255, 255, 255),
                          cx - title_w // 2, cy - 120)

        # Volume label
        lbl = "VOLUME"
        lbl_w = font_label.size(lbl)[0]
        _draw_shadow_text(WINDOW, font_label, lbl, (180, 200, 255),
                          cx - lbl_w // 2, vol_bar_y - 26)

        # Volume bar track
        pygame.draw.rect(WINDOW, (30, 30, 55), (vol_bar_x, vol_bar_y, vol_bar_w, vol_bar_h), border_radius=10)
        fill_w = max(0, int(vol_bar_w * volume))
        if fill_w > 0:
            pygame.draw.rect(WINDOW, (100, 130, 255), (vol_bar_x, vol_bar_y, fill_w, vol_bar_h), border_radius=10)
        pygame.draw.rect(WINDOW, (160, 160, 255), (vol_bar_x, vol_bar_y, vol_bar_w, vol_bar_h), width=2, border_radius=10)

        # Draggable knob
        knob_x = vol_bar_x + fill_w
        knob_x = max(vol_bar_x + vol_bar_h // 2, min(knob_x, vol_bar_x + vol_bar_w - vol_bar_h // 2))
        pygame.draw.circle(WINDOW, (220, 230, 255), (knob_x, vol_bar_y + vol_bar_h // 2), vol_bar_h // 2 + 4)

        # Percentage below bar
        pct_text = f"{int(volume * 100)}%"
        pct_w = font_label.size(pct_text)[0]
        _draw_shadow_text(WINDOW, font_label, pct_text, (200, 220, 255),
                          cx - pct_w // 2, vol_bar_y + vol_bar_h + 8)

        _draw_btn(resume_rect, "RESUME",    base=(35, 90, 55),  hover=(45, 120, 70))
        _draw_btn(menu_rect,   "MAIN MENU", base=(90, 35, 35),  hover=(120, 45, 45))

        pygame.display.update()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_s, pygame.K_ESCAPE):
                    pygame.mixer.music.unpause()
                    return
                if event.key == pygame.K_UP:
                    volume = min(1.0, round(volume + 0.05, 2))
                    pygame.mixer.music.set_volume(volume)
                if event.key == pygame.K_DOWN:
                    volume = max(0.0, round(volume - 0.05, 2))
                    pygame.mixer.music.set_volume(volume)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if vol_hit_rect.collidepoint(event.pos):
                    dragging_vol = True
                    volume = max(0.0, min(1.0, (event.pos[0] - vol_bar_x) / vol_bar_w))
                    pygame.mixer.music.set_volume(volume)
                elif resume_rect.collidepoint(event.pos):
                    pygame.mixer.music.unpause()
                    return
                elif menu_rect.collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    mainmenu()
                    return
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging_vol = False
            if event.type == pygame.MOUSEMOTION and dragging_vol:
                volume = max(0.0, min(1.0, (event.pos[0] - vol_bar_x) / vol_bar_w))
                pygame.mixer.music.set_volume(volume)


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
    hold_frames = 0
    hold_threshold = 5

    # GET READY sprite: crop (49, 75, 185, 15) from text.png, scaled up for visibility
    has_jumped = False
    get_ready_img = None
    try:
        _text_sheet = pygame.image.load(join('data', 'text.png')).convert_alpha()
        _gr_cell = pygame.Surface((185, 15), pygame.SRCALPHA)
        _gr_cell.blit(_text_sheet, (0, 0), (49, 75, 185, 15))
        get_ready_img = pygame.transform.scale(_gr_cell, (185 * 5, 15 * 5))
    except Exception as _e:
        print(f"Warning: could not load GET READY sprite: {_e}")

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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
                if not MAINMENU_ACTIVE:
                    pause_menu(score, background, pipes, floor, bird, ribbon, lighting)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not MAINMENU_ACTIVE and score.settings_rect.collidepoint(event.pos):
                    pause_menu(score, background, pipes, floor, bird, ribbon, lighting)

        # INPUT HANDLING
        keys = pygame.key.get_pressed()
        is_holding_input = keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0] == 1
        if is_holding_input:
            hold_frames += 1
        else:
            hold_frames = 0

        if hold_frames >= hold_threshold:
            bird.jump()
            has_jumped = True

        # TIMER CHECK
        if not MAINMENU_ACTIVE:
            elapsed = pygame.time.get_ticks() - game_start_time
            if elapsed >= GAME_DURATION_MS:
                best = max(score.note_points, Score.GOAL if score.note_points >= Score.GOAL else 0)
                won  = score.note_points >= Score.GOAL
                result_screen(won, score.note_points, score.distance, score.note_points)
                return

        # GAME STATE CHECK
        if bird.crashed:
            current_alpha = lighting.get_alpha()
            toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha)
            gameover()

        else:
            # Normal gameplay
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
                    lighting.update(score.note_points, Score.GOAL)
                    current_alpha = lighting.get_alpha()
                    toolkit.update_display_with_lighting(background, pipes, floor, bird, score, ribbon, current_alpha)
                    gameover()

            lighting.update(score.note_points, Score.GOAL)
            current_alpha = lighting.get_alpha()

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

            # GET READY overlay — shown before the player's first jump
            if not has_jumped and get_ready_img:
                WINDOW.blit(get_ready_img,
                            (WINDOW_WIDTH // 2 - get_ready_img.get_width() // 2,
                             WINDOW_HEIGHT // 3 - get_ready_img.get_height() // 2))
                pygame.display.update()


if __name__ == '__main__':
    run()
