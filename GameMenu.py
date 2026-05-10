import pygame
import sys
import os
import math
import importlib.util

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#initialize
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

#screen
WIDTH, HEIGHT = 1280, 768
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("WHIPLASH: Rhythm of the Cosmos")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
YELLOW = (255, 255, 0)

TITLE_FONT_SIZE = 58
BUTTON_FONT_SIZE = 29
MENU_TITLE_FONT_SIZE = 46
PLANET_NAME_FONT_SIZE = 37
PLANET_SUBTITLE_FONT_SIZE = 26
ICON_SIZE = 288
BUTTON_WIDTH = 352
BUTTON_HEIGHT = 100
BUTTON_SPACING = 6
CARD_WIDTH = 416
CARD_HEIGHT = 435
CARD_ICON_OFFSET = 64
ARROW_ICON_SIZE = 64
PAGE_DOT_RADIUS = 6
SETTINGS_ICON_SIZE = 90
SLIDER_WIDTH = 160
SLIDER_HEIGHT = 20

#GIF loader
def load_gif_frames(path, size=None):
    if not PIL_AVAILABLE or not os.path.exists(path):
        return None, None
    try:
        gif = Image.open(path)
        frames = []
        durations = []
        for frame_idx in range(gif.n_frames):
            gif.seek(frame_idx)
            frame = gif.convert("RGBA")
            if size:
                frame = frame.resize(size, Image.LANCZOS)
            frame_surface = pygame.image.frombytes(frame.tobytes(), frame.size, frame.mode)
            frames.append(frame_surface)
            duration = gif.info.get('duration', 100)
            durations.append(duration)
        return frames, durations
    except Exception as e:
        print(f"Error loading GIF {path}: {e}")
        return None, None

try:
    titleFont = pygame.font.Font("PressStart2P.ttf", TITLE_FONT_SIZE)
    buttonFont = pygame.font.Font("PressStart2P.ttf", BUTTON_FONT_SIZE)
    menuTitleFont = pygame.font.Font("PressStart2P.ttf", MENU_TITLE_FONT_SIZE)
    planetNameFont = pygame.font.Font("PressStart2P.ttf", PLANET_NAME_FONT_SIZE)
    planetSubtitleFont = pygame.font.Font("PressStart2P.ttf", PLANET_SUBTITLE_FONT_SIZE)
except:
    titleFont = pygame.font.SysFont("Courier", TITLE_FONT_SIZE, bold=True)
    buttonFont = pygame.font.SysFont("Courier", BUTTON_FONT_SIZE, bold=True)
    menuTitleFont = pygame.font.SysFont("Courier", MENU_TITLE_FONT_SIZE, bold=True)
    planetNameFont = pygame.font.SysFont("Courier", PLANET_NAME_FONT_SIZE, bold=True)
    planetSubtitleFont = pygame.font.SysFont("Courier", PLANET_SUBTITLE_FONT_SIZE, bold=True)

#buttons rectangles size
start_button = pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, HEIGHT//2 - BUTTON_HEIGHT - BUTTON_SPACING,
                           BUTTON_WIDTH, BUTTON_HEIGHT)
instructions_button = pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, HEIGHT//2,
                                  BUTTON_WIDTH, BUTTON_HEIGHT)
exit_button = pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, HEIGHT//2 + BUTTON_HEIGHT + BUTTON_SPACING,
                          BUTTON_WIDTH, BUTTON_HEIGHT)
back_button = pygame.Rect(20, 20, 100, 75)
skip_button = pygame.Rect(WIDTH - 140, HEIGHT - 60, 120, 40)
settings_button = pygame.Rect(WIDTH - SETTINGS_ICON_SIZE - 20, 20, SETTINGS_ICON_SIZE, SETTINGS_ICON_SIZE)

#planet selection
planet_options = [
    {
        "name": "Eburonia",
        "subtitle": "Hip",
        "preview": "MENU/Assets/hip.mp3",
        "icon": "data/planet1.gif",
        "color": (255, 170, 120),
    },
    {
        "name": "Coruscant",
        "subtitle": "jellyous - ILLIT",
        "preview": "MENU/Assets/jellyous.mp3",
        "icon": "data/planet2.gif",
        "color": (170, 255, 140),
    },
    {
        "name": "Cybertron",
        "subtitle": "Whiplash - aespa",
        "preview": "MENU/Assets/whiplash.mp3",
        "icon": "data/planet3.gif",
        "color": (220, 130, 255),
    },
]

#planet icon
planet_menu_bg = None
planet_menu_bg_frames = None
planet_menu_bg_durations = None
planet_menu_bg_frame_idx = 0
planet_menu_bg_elapsed = 0
planet_icon_assets = {}
planet_icon_animations = {}

for planet in planet_options:
    icon_path = planet.get("icon")

    if icon_path and os.path.exists(icon_path):
        try:
            if icon_path.lower().endswith('.gif') and PIL_AVAILABLE:
                frames, durations = load_gif_frames(icon_path, (ICON_SIZE, ICON_SIZE))
                if frames:
                    planet_icon_animations[planet["name"]] = {
                        'frames': frames,
                        'durations': durations,
                        'frame_idx': 0,
                        'elapsed': 0
                    }
                    planet_icon_assets[planet["name"]] = frames[0]
                    print(f"Loaded animated GIF for {planet['name']}: {len(frames)} frames")
                else:
                    planet_icon_assets[planet["name"]] = None
                    print(f"Failed to load GIF for {planet['name']}")
            else:
                img = pygame.image.load(icon_path).convert_alpha()
                img = pygame.transform.smoothscale(img, (ICON_SIZE, ICON_SIZE))
                planet_icon_assets[planet["name"]] = img
                print(f"Loaded static image for {planet['name']}")
        except Exception as e:
            print(f"Error loading icon for {planet['name']}: {e}")
            planet_icon_assets[planet["name"]] = None
    else:
        print(f"No icon found for {planet['name']}")
        planet_icon_assets[planet["name"]] = None

if os.path.exists("data/ChoosePlanet.gif"):
    try:
        if PIL_AVAILABLE:
            frames, durations = load_gif_frames("data/ChoosePlanet.gif", (WIDTH, HEIGHT))
            if frames:
                planet_menu_bg_frames = frames
                planet_menu_bg_durations = durations
                planet_menu_bg = frames[0]
                print(f"Loaded animated background ChoosePlanet.gif: {len(frames)} frames")
            else:
                planet_menu_bg = pygame.Surface((WIDTH, HEIGHT))
                planet_menu_bg.fill((8, 12, 22))
                print("Failed to load ChoosePlanet.gif, using fallback")
        else:
            planet_menu_bg = pygame.Surface((WIDTH, HEIGHT))
            planet_menu_bg.fill((8, 12, 22))
            print("PIL not available, using fallback background")
    except Exception as e:
        print(f"Error loading planet menu background: {e}")
        planet_menu_bg = pygame.Surface((WIDTH, HEIGHT))
        planet_menu_bg.fill((8, 12, 22))
else:
    planet_menu_bg = pygame.Surface((WIDTH, HEIGHT))
    planet_menu_bg.fill((8, 12, 22))
    print("ChoosePlanet.gif not found, using fallback background")

preview_sounds = []
for planet in planet_options:
    if os.path.exists(planet["preview"]):
        try:
            sound = pygame.mixer.Sound(planet["preview"])
            sound.set_volume(0.5)
            preview_sounds.append(sound)
        except Exception as e:
            print(f"Error loading preview sound {planet['preview']}: {e}")
            preview_sounds.append(None)
    else:
        print(f"Preview sound '{planet['preview']}' not found")
        preview_sounds.append(None)

preview_channel = pygame.mixer.Channel(6)

#animation update
def update_animations(delta_time):
    global planet_menu_bg_frame_idx, planet_menu_bg_elapsed

    if planet_menu_bg_frames:
        planet_menu_bg_elapsed += delta_time
        if planet_menu_bg_elapsed >= planet_menu_bg_durations[planet_menu_bg_frame_idx]:
            planet_menu_bg_elapsed = 0
            planet_menu_bg_frame_idx = (planet_menu_bg_frame_idx + 1) % len(planet_menu_bg_frames)

    for planet_name, anim in planet_icon_animations.items():
        anim['elapsed'] += delta_time
        if anim['elapsed'] >= anim['durations'][anim['frame_idx']]:
            anim['elapsed'] = 0
            old_frame = anim['frame_idx']
            anim['frame_idx'] = (anim['frame_idx'] + 1) % len(anim['frames'])
            planet_icon_assets[planet_name] = anim['frames'][anim['frame_idx']]

#cutscene audio
type_sound = None
for _tw_path in ("data/typewriter.wav", "typewriter.wav"):
    if os.path.exists(_tw_path):
        try:
            type_sound = pygame.mixer.Sound(_tw_path)
            type_sound.set_volume(0.6)
            print(f"Loaded typewriter sound: {_tw_path}")
        except Exception as e:
            print(f"Error loading typewriter sound {_tw_path}: {e}")
        break
if not type_sound:
    print(f"Typewriter sound not found in data/ or working dir")

#bgm
bgm_file = "data/nj.mp3"
bgm_loaded = False
if os.path.exists(bgm_file):
    try:
        pygame.mixer.music.load(bgm_file)
        pygame.mixer.music.set_volume(0.35)
        bgm_loaded = True
    except Exception as e:
        print(f"Error loading BGM: {e}")
else:
    print(f"BGM file '{bgm_file}' not found in {os.getcwd()}")

#settings icon
settings_icon = None
for _s_path in ("data/settings.png", "MENU/Assets/settings.png", "settings.png"):
    if os.path.exists(_s_path):
        try:
            settings_icon = pygame.image.load(_s_path).convert_alpha()
            settings_icon = pygame.transform.scale(settings_icon, (SETTINGS_ICON_SIZE, SETTINGS_ICON_SIZE))
            print(f"Loaded settings icon: {_s_path}")
        except Exception as e:
            print(f"Error loading settings icon {_s_path}: {e}")
        break

#button background image
button_bg = None
for _btn_path in ("data/button.png", "button.png"):
    if os.path.exists(_btn_path):
        try:
            button_bg = pygame.image.load(_btn_path).convert_alpha()
            print(f"Loaded button background: {_btn_path}")
        except Exception as e:
            print(f"Error loading button background {_btn_path}: {e}")
        break

#main menu background
menu_bg = None
for _menu_bg_path in ("data/Menu.jpeg", "data/Menu.jpg", "MENU/Assets/Menu.jpeg", "Menu.jpeg"):
    if os.path.exists(_menu_bg_path):
        try:
            _img = pygame.image.load(_menu_bg_path).convert()
            menu_bg = pygame.transform.scale(_img, (WIDTH, HEIGHT))
            print(f"Loaded main menu background: {_menu_bg_path}")
        except Exception as e:
            print(f"Error loading menu background {_menu_bg_path}: {e}")
        break

#semi-transparent dark overlay drawn on top of menu_bg
menu_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
menu_overlay.fill((0, 0, 0, 130))

#easter egg sprites: normal/monster icon pairs loaded from sprite sheet
#sheet layout: 2 columns (col 0=normal, col 1=monster), 5 rows
#cell size is calculated from the actual image dimensions, not hardcoded
_DISPLAY_SIZE = 80
_SPRITE_NAMES = ["Book", "File", "Note", "Cone", "Cmd"]
#scattered positions (top-left x,y) — spread across the full screen, clear of buttons/title/settings
_SPRITE_POSITIONS = [
    ( 80, 175),   # Book  - upper-left
    ( 38, 430),   # File  - far-left middle
    ( 95, 600),   # Note  - lower-left corner
    (1060, 195),  # Cone  - upper-right (clear of settings icon)
    (1095, 590),  # Cmd   - lower-right corner
]
menu_sprites_normal  = []
menu_sprites_monster = []
_sheet = None
for _sp in ("data/scary.png", "data/sprites.png", "data/Sprites.png", "data/sprite_sheet.png", "data/monsters.png"):
    if os.path.exists(_sp):
        try:
            _sheet = pygame.image.load(_sp).convert_alpha()
            print(f"Loaded sprite sheet: {_sp} size={_sheet.get_size()}")
        except Exception as e:
            print(f"Error loading sprite sheet {_sp}: {e}")
        break
if _sheet:
    _cell_w = _sheet.get_width() // 2
    _col1_w = _sheet.get_width() - _cell_w
    _sh = _sheet.get_height()
    _row_y = [0, int(_sh * 0.254), int(_sh * 0.424), int(_sh * 0.594), int(_sh * 0.780)]
    print(f"Sprite cell width: {_cell_w}, row boundaries: {_row_y}")
    for _row in range(5):
        _cy = _row_y[_row]
        _rh = (_row_y[_row + 1] - _cy) if _row < 4 else (_sh - _cy)
        _norm  = _sheet.subsurface(pygame.Rect(0,       _cy, _cell_w, _rh))
        _monst = _sheet.subsurface(pygame.Rect(_cell_w, _cy, _col1_w, _rh))
        menu_sprites_normal.append(pygame.transform.smoothscale(_norm,  (_DISPLAY_SIZE, _DISPLAY_SIZE)))
        menu_sprites_monster.append(pygame.transform.smoothscale(_monst, (_DISPLAY_SIZE, _DISPLAY_SIZE)))
else:
    print("Sprite sheet not found — easter egg sprites disabled. Place scary.png in data/")

#animation state: timestamp when each sprite's scare animation started (0 = idle)
_SCARE_DURATION = 520   # total ms for the whole animation
_sprite_anim_start = [0] * 5
#current positions (mutable — sprites jump away after being scared)
import random as _random
_sprite_pos_current = [list(p) for p in _SPRITE_POSITIONS]

def _pick_new_sprite_pos(idx):
    """Return a new [x,y] for sprite idx that avoids buttons and current positions."""
    _btn_zone = pygame.Rect(440, 280, 400, 280)   # rough button area
    _set_zone = pygame.Rect(1150, 10, 110, 110)   # settings icon
    for _ in range(80):
        # pick from left strip or right strip
        if _random.random() < 0.5:
            nx = _random.randint(30, 380)
        else:
            nx = _random.randint(870, 1160)
        ny = _random.randint(150, 680)
        candidate = pygame.Rect(nx, ny, _DISPLAY_SIZE, _DISPLAY_SIZE)
        if candidate.colliderect(_btn_zone) or candidate.colliderect(_set_zone):
            continue
        # avoid being too close to current sibling sprites
        too_close = False
        for j, op in enumerate(_sprite_pos_current):
            if j != idx and abs(nx - op[0]) < 80 and abs(ny - op[1]) < 80:
                too_close = True
                break
        if not too_close:
            return [nx, ny]
    return _sprite_pos_current[idx]   # fallback: stay put

#shadow surface shared for all sprites
_shadow_surf = pygame.Surface((_DISPLAY_SIZE + 10, 14), pygame.SRCALPHA)
pygame.draw.ellipse(_shadow_surf, (0, 0, 0, 90),
                    pygame.Rect(0, 0, _DISPLAY_SIZE + 10, 14))

#planet menu arrow
left_arrow_icon = None
right_arrow_icon = None
left_arrow_path = "MENU/Assets/left_arrow.png"
right_arrow_path = "MENU/Assets/right_arrow.png"
for path, icon_var in ((left_arrow_path, "left_arrow_icon"), (right_arrow_path, "right_arrow_icon")):
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (ARROW_ICON_SIZE, ARROW_ICON_SIZE))
            if path == left_arrow_path:
                left_arrow_icon = img
            else:
                right_arrow_icon = img
        except Exception as e:
            print(f"Error loading arrow icon '{path}': {e}")
    else:
        print(f"Arrow icon '{path}' not found")

#ui
def draw_button(rect, text, is_hovered):
    draw_rect = rect.inflate(10, 10) if is_hovered else rect
    # button fill
    if button_bg:
        scaled_btn = pygame.transform.smoothscale(button_bg, (draw_rect.width, draw_rect.height))
        screen.blit(scaled_btn, (draw_rect.x, draw_rect.y))
        if is_hovered:
            hover_tint = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            hover_tint.fill((255, 255, 0, 60))
            screen.blit(hover_tint, (draw_rect.x, draw_rect.y))
    else:
        color = YELLOW if is_hovered else GRAY
        pygame.draw.rect(screen, color, draw_rect)
    # text shadow
    shadow_label = buttonFont.render(text, True, (110, 110, 110))
    screen.blit(shadow_label, (draw_rect.centerx - shadow_label.get_width()//2 + 2,
                               draw_rect.centery - shadow_label.get_height()//2 + 2))
    # text
    label = buttonFont.render(text, True, BLACK)
    screen.blit(label, (draw_rect.centerx - label.get_width()//2,
                        draw_rect.centery - label.get_height()//2))

def draw_settings_icon(is_hovered):
    if settings_icon:
        if is_hovered:
            hover_size = SETTINGS_ICON_SIZE + 8
            hover_icon = pygame.transform.smoothscale(settings_icon, (hover_size, hover_size))
            blit_x = settings_button.centerx - hover_size // 2
            blit_y = settings_button.centery - hover_size // 2
            glow = pygame.Surface((hover_size + 10, hover_size + 10), pygame.SRCALPHA)
            glow.fill((255, 255, 180, 60))
            screen.blit(glow, (blit_x - 5, blit_y - 5))
            screen.blit(hover_icon, (blit_x, blit_y))
        else:
            screen.blit(settings_icon, (settings_button.x, settings_button.y))
    else:
        pygame.draw.rect(screen, GRAY, settings_button)
        label = buttonFont.render("⚙", True, BLACK)
        screen.blit(label, (settings_button.centerx - label.get_width()//2,
                            settings_button.centery - label.get_height()//2))

def show_exit_confirm():
    pygame.mixer.music.pause()
    _confirm_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    _confirm_overlay.fill((0, 0, 0, 180))
    _leave_btn  = pygame.Rect(WIDTH//2 - BUTTON_WIDTH - 16, HEIGHT//2 + 10, BUTTON_WIDTH, BUTTON_HEIGHT)
    _stay_btn   = pygame.Rect(WIDTH//2 + 16,                HEIGHT//2 + 10, BUTTON_WIDTH, BUTTON_HEIGHT)
    _prompt_col = (120, 255, 190)
    while True:
        screen.blit(_confirm_overlay, (0, 0))
        _q = menuTitleFont.render("ARE YOU SURE?", True, _prompt_col)
        _qs = menuTitleFont.render("ARE YOU SURE?", True, (0, 55, 35))
        screen.blit(_qs, (WIDTH//2 - _q.get_width()//2 + 2, HEIGHT//2 - 80 + 2))
        screen.blit(_q,  (WIDTH//2 - _q.get_width()//2,     HEIGHT//2 - 80))
        _mp = pygame.mouse.get_pos()
        draw_button(_leave_btn, "LEAVE", _leave_btn.collidepoint(_mp))
        draw_button(_stay_btn,  "STAY",  _stay_btn.collidepoint(_mp))
        pygame.display.flip()
        for _ev in pygame.event.get():
            if _ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if _ev.type == pygame.MOUSEBUTTONDOWN:
                if _leave_btn.collidepoint(_ev.pos):
                    pygame.quit(); sys.exit()
                elif _stay_btn.collidepoint(_ev.pos):
                    pygame.mixer.music.unpause()
                    return

#cutscene typewrite
def typewriter_text(line, show_skip=False):
    displayed = ""
    char_index = 0
    type_channel = pygame.mixer.Channel(7)
    clock = pygame.time.Clock()

    if type_sound:
        audio_ms = type_sound.get_length() * 200
        ms_per_char = audio_ms / len(line) if len(line) > 0 else 60
        type_channel.play(type_sound)
    else:
        ms_per_char = 60

    start_time = pygame.time.get_ticks()

    while char_index < len(line):
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        char_index = int(elapsed / ms_per_char)
        displayed = line[:char_index + 1]

        screen.fill(BLACK)

        # ---- CENTERED MULTI-LINE TEXT ----
        lines = displayed.split("\n")

        total_height = len(lines) * buttonFont.get_height()
        start_y = HEIGHT // 2 - total_height // 2

        for i, line_part in enumerate(lines):
            text_surface = buttonFont.render(line_part, True, WHITE)

            x = WIDTH // 2 - text_surface.get_width() // 2
            y = start_y + i * buttonFont.get_height()

            screen.blit(text_surface, (x, y))
        # -----------------------------------

        if show_skip:
            mouse_pos = pygame.mouse.get_pos()
            draw_button(skip_button, "SKIP", skip_button.collidepoint(mouse_pos))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if show_skip:
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
                   (event.type == pygame.MOUSEBUTTONDOWN and skip_button.collidepoint(event.pos)):
                    type_channel.stop()
                    return True

    return False

#cutscenes
def play_cutscenes():
    cutscenes = [
        "Once, every planet in the galaxy\nthrived through the power of music.",
        "But one day, the melodies vanished,\nand the universe lost its color, light, and life.",
        "Oceans fell silent, stars dimmed,\nand entire worlds were left frozen in darkness.",
        "Now, you are the last soul who can still\n hear the beat hidden among the stars.",
        "Travel across dying planets,\nrecover the lost notes, and bring color back to the\n universe before The Silence consumes everything."
    ]

    for idx, line in enumerate(cutscenes, start=1):
        if typewriter_text(line, show_skip=(idx >= 2)):
            break

        pause_start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - pause_start < 6000:
            pygame.event.pump()
            pygame.time.Clock().tick(60)

#Screen functions
def show_settings():
    global current_volume
    _TC = (120, 255, 190)
    while True:
        if menu_bg:
            screen.blit(menu_bg, (0, 0))
            screen.blit(menu_overlay, (0, 0))
        else:
            screen.fill(BLACK)
        _tsh = titleFont.render("SETTINGS", True, (0, 55, 35))
        screen.blit(_tsh, (WIDTH//2 - _tsh.get_width()//2 + 2, 102))
        titleText = titleFont.render("SETTINGS", True, _TC)
        screen.blit(titleText, (WIDTH//2 - titleText.get_width()//2, 100))

        # Display current volume percentage
        vol_text = buttonFont.render(f"Volume: {int(current_volume*100)}%", True, WHITE)
        screen.blit(vol_text, (WIDTH//2 - vol_text.get_width()//2, HEIGHT//2 - 40))

        # Slider bar
        slider_x = WIDTH//2 - SLIDER_WIDTH//2
        slider_y = HEIGHT//2
        slider_width = SLIDER_WIDTH
        slider_height = SLIDER_HEIGHT

        # Slider background
        pygame.draw.rect(screen, GRAY, (slider_x, slider_y, slider_width, slider_height))
        # Slider fill based on current volume
        fill_width = int(slider_width * current_volume)
        pygame.draw.rect(screen, YELLOW, (slider_x, slider_y, fill_width, slider_height))

        # Back button
        mouse_pos = pygame.mouse.get_pos()
        draw_button(back_button, "BACK", back_button.collidepoint(mouse_pos))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # Adjust volume with arrow keys
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and current_volume < 1.0:
                    current_volume = round(current_volume + 0.1, 1)
                elif event.key == pygame.K_DOWN and current_volume > 0.0:
                    current_volume = round(current_volume - 0.1, 1)
                pygame.mixer.music.set_volume(current_volume)
                if type_sound: type_sound.set_volume(current_volume)
                preview_channel.set_volume(current_volume)

            # Adjust volume by clicking on slider
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return
                # If clicked inside slider, set volume based on click position
                if slider_x <= event.pos[0] <= slider_x + slider_width and slider_y <= event.pos[1] <= slider_y + slider_height:
                    click_pos = event.pos[0] - slider_x
                    current_volume = round(click_pos / slider_width, 2)
                    pygame.mixer.music.set_volume(current_volume)
                    if type_sound: type_sound.set_volume(current_volume)
                    preview_channel.set_volume(current_volume)


def stop_planet_preview():
    if preview_channel.get_busy():
        preview_channel.fadeout(300)


def play_planet_preview(index):
    if 0 <= index < len(preview_sounds):
        stop_planet_preview()
        sound = preview_sounds[index]
        if sound:
            preview_channel.play(sound, loops=-1)


def draw_planet_card(planet, center_x, center_y, is_selected):
    rect = pygame.Rect(center_x - CARD_WIDTH//2, center_y - CARD_HEIGHT//2, CARD_WIDTH, CARD_HEIGHT)
    pygame.draw.rect(screen, (20, 20, 30), rect, border_radius=20)
    outline_color = YELLOW if is_selected else GRAY
    pygame.draw.rect(screen, outline_color, rect, 4, border_radius=20)

    card_top = center_y - CARD_HEIGHT // 2
    icon_center_y = card_top + 30 + ICON_SIZE // 2
    text_y = card_top + 30 + ICON_SIZE + 15
    subtitle_y = text_y + 45

    icon = planet_icon_assets.get(planet["name"])
    if icon:
        icon_rect = icon.get_rect(center=(center_x, icon_center_y))
        screen.blit(icon, icon_rect)
    else:
        pygame.draw.circle(screen, planet["color"], (center_x, icon_center_y), ICON_SIZE//2)
        pygame.draw.circle(screen, WHITE, (center_x, icon_center_y), ICON_SIZE//2, 4)

    name_text = planetNameFont.render(planet["name"], True, WHITE)
    screen.blit(name_text, (center_x - name_text.get_width()//2, text_y))

    subtitle_text = planetSubtitleFont.render(planet["subtitle"], True, GRAY)
    screen.blit(subtitle_text, (center_x - subtitle_text.get_width()//2, subtitle_y))


def launch_level(selected_planet):
    level_dirs = {
        0: os.path.join(BASE_DIR, "..", "WHIPLASH LEVELS", "level 1 hip"),
        1: os.path.join(BASE_DIR, "..", "WHIPLASH LEVELS", "level 2 jellyous"),
        2: os.path.join(BASE_DIR, "..", "WHIPLASH LEVELS", "level 3 whiplash"),
    }
    level_dir = level_dirs.get(selected_planet)
    if not level_dir or not os.path.isdir(level_dir):
        print(f"Level directory not found for selection {selected_planet}: {level_dir}")
        return

    level_path = os.path.join(level_dir, "GAME.py")
    if not os.path.exists(level_path):
        print(f"Level file not found for selection {selected_planet}: {level_path}")
        return

    try:
        pygame.mixer.music.stop()

        sys.path.insert(0, level_dir)
        try:
            spec = importlib.util.spec_from_file_location(f"level_module_{selected_planet}", level_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            run_fn = getattr(module, "run_level", None) or getattr(module, "main", None)
            if not callable(run_fn):
                print(f"No runnable entry point found in {level_path}")
                return

            run_fn(screen)
        finally:
            if sys.path and sys.path[0] == level_dir:
                sys.path.pop(0)
    except Exception as e:
        print(f"Error launching level: {e}")


def show_planet_menu():
    selected_planet = 0
    camera_x = 0.0
    target_camera_x = 0.0
    left_arrow = pygame.Rect(WIDTH//2 - CARD_WIDTH//2 - 60, HEIGHT//2 - 24, 50, 48)
    right_arrow = pygame.Rect(WIDTH//2 + CARD_WIDTH//2 + 10, HEIGHT//2 - 24, 50, 48)
    confirm_button = pygame.Rect(WIDTH//2 - BUTTON_WIDTH//2, HEIGHT - BUTTON_HEIGHT - 5, BUTTON_WIDTH, BUTTON_HEIGHT)

    if planet_menu_bg:
        bg = planet_menu_bg
    else:
        bg = None

    play_planet_preview(selected_planet)

    clock = pygame.time.Clock()

    while True:
        delta_time = clock.tick(60)
        update_animations(delta_time)

        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_a) and selected_planet > 0:
                    selected_planet -= 1
                    target_camera_x = selected_planet * WIDTH
                    play_planet_preview(selected_planet)
                elif event.key in (pygame.K_RIGHT, pygame.K_d) and selected_planet < len(planet_options) - 1:
                    selected_planet += 1
                    target_camera_x = selected_planet * WIDTH
                    play_planet_preview(selected_planet)
                elif event.key == pygame.K_RETURN:
                    stop_planet_preview()
                    return selected_planet
                elif event.key == pygame.K_ESCAPE:
                    stop_planet_preview()
                    pygame.mixer.music.unpause()
                    return None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    stop_planet_preview()
                    pygame.mixer.music.unpause()
                    return None
                if left_arrow.collidepoint(event.pos) and selected_planet > 0:
                    selected_planet -= 1
                    target_camera_x = selected_planet * WIDTH
                    play_planet_preview(selected_planet)
                if right_arrow.collidepoint(event.pos) and selected_planet < len(planet_options) - 1:
                    selected_planet += 1
                    target_camera_x = selected_planet * WIDTH
                    play_planet_preview(selected_planet)
                if confirm_button.collidepoint(event.pos):
                    stop_planet_preview()
                    return selected_planet

        camera_x += (target_camera_x - camera_x) * 0.12

        if planet_menu_bg_frames:
            screen.blit(planet_menu_bg_frames[planet_menu_bg_frame_idx], (0, 0))
        elif bg:
            screen.blit(bg, (0, 0))
        else:
            screen.fill((8, 12, 22))
            for star_x in range(0, WIDTH, 120):
                for star_y in range(0, HEIGHT, 120):
                    if (star_x + star_y) % 240 == 0:
                        pygame.draw.circle(screen, (50, 80, 140), (star_x + 30, star_y + 20), 2)
                        pygame.draw.circle(screen, (144, 209, 255), (star_x + 70, star_y + 100), 2)

        titleText = menuTitleFont.render("SELECT YOUR PLANET", True, WHITE)
        screen.blit(titleText, (WIDTH//2 - titleText.get_width()//2, 40))
        subtitle = planetSubtitleFont.render("Move left/right or tap arrows", True, GRAY)
        screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 82))

        # draw planets centered 
        for idx, planet in enumerate(planet_options):
            center_x = WIDTH//2 + (idx * WIDTH - camera_x)
            center_y = HEIGHT//2 - 20
            is_selected = idx == selected_planet
            draw_planet_card(planet, center_x, center_y, is_selected)

        #dots
        for idx in range(len(planet_options)):
            dot_color = YELLOW if idx == selected_planet else GRAY
            total_dots_width = (len(planet_options) - 1) * 40
            dot_x = WIDTH//2 - total_dots_width//2 + idx * 40
            pygame.draw.circle(screen, dot_color, (dot_x, HEIGHT - 110), PAGE_DOT_RADIUS)

        #arrows and buttons
        if left_arrow_icon:
            icon_rect = left_arrow_icon.get_rect(center=left_arrow.center)
            screen.blit(left_arrow_icon, icon_rect)
        else:
            pygame.draw.polygon(screen, WHITE if left_arrow.collidepoint(mouse_pos) else GRAY,
                                [(left_arrow.right, left_arrow.top), (left_arrow.right, left_arrow.bottom), (left_arrow.left, left_arrow.centery)])

        if right_arrow_icon:
            icon_rect = right_arrow_icon.get_rect(center=right_arrow.center)
            screen.blit(right_arrow_icon, icon_rect)
        else:
            pygame.draw.polygon(screen, WHITE if right_arrow.collidepoint(mouse_pos) else GRAY,
                                [(right_arrow.left, right_arrow.top), (right_arrow.left, right_arrow.bottom), (right_arrow.right, right_arrow.centery)])

        draw_button(confirm_button, "CONFIRM", confirm_button.collidepoint(mouse_pos))
        draw_button(back_button, "BACK", back_button.collidepoint(mouse_pos))

        pygame.display.flip()


def show_game_screen(selected_planet=None):
    if selected_planet is None:
        return

    planet_name = planet_options[selected_planet]["name"]
    screen.fill(BLACK)
    titleText = titleFont.render("GAME STARTING...", True, WHITE)
    screen.blit(titleText, (WIDTH//2 - titleText.get_width()//2, HEIGHT//2 - 40))
    subtitle = buttonFont.render(f"Planet: {planet_name}", True, GRAY)
    screen.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, HEIGHT//2 + 30))
    pygame.display.flip()
    pygame.time.wait(300)
    launch_level(selected_planet)

def show_instructions():
    _TC  = (120, 255, 190)
    _WH  = (220, 220, 220)
    try:
        _cf = pygame.font.Font("PressStart2P.ttf", 15)
    except:
        _cf = pygame.font.SysFont("Courier", 15, bold=True)
    # (is_header, text)
    _lines = [
        (True,  ""),
        (True,  ""),
        (True,  "SPACEBAR / LEFT CLICK"),
        (False, "- Makes the player fly continuously"),
        (True,  ""),
        (True,  ""),
        (True,  "FULLSCREEN TOGGLE"),
        (False, "- Press F11 or a button"),
        (False, "- Switch between windowed and fullscreen"),
        (True,  ""),
        (True,  ""),
        (True,  "GAMEPLAY:"),
        (False, "- The player automatically moves forward"),
        (False, "- Buildings and obstacles approach continuously"),
        (False, "- Gravity pulls the player downward"),
        (False, "- Time your jumps carefully to avoid crashing"),
        (False, "- Pass through gaps between obstacles to gain points"),
    ]
    _lx = 120
    _ly_start = 80
    _h_gap = 34
    _b_gap = 26
    while True:
        if menu_bg:
            screen.blit(menu_bg, (0, 0))
            screen.blit(menu_overlay, (0, 0))
        else:
            screen.fill(BLACK)
        _y = _ly_start
        for _is_hdr, _txt in _lines:
            if _txt == "":
                _y += 10
                continue
            if _is_hdr:
                _surf = buttonFont.render(_txt, True, _TC)
                screen.blit(_surf, (_lx, _y))
                _y += _h_gap
            else:
                _surf = _cf.render(_txt, True, _WH)
                screen.blit(_surf, (_lx + 20, _y))
                _y += _b_gap
        mouse_pos = pygame.mouse.get_pos()
        draw_button(back_button, "BACK", back_button.collidepoint(mouse_pos))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and back_button.collidepoint(event.pos):
                return

def menu_loop():
    global current_volume
    current_volume = 0.5  # default volume

    while True:
        if menu_bg:
            screen.blit(menu_bg, (0, 0))
            screen.blit(menu_overlay, (0, 0))
        else:
            screen.fill(BLACK)
        TITLE_COLOR = (120, 255, 190)
        title_shadow = titleFont.render("WHIPLASH: Rhythm of the Cosmos", True, (0, 55, 35))
        screen.blit(title_shadow, (WIDTH//2 - title_shadow.get_width()//2 + 2, 102))
        titleText = titleFont.render("WHIPLASH: Rhythm of the Cosmos", True, TITLE_COLOR)
        screen.blit(titleText, (WIDTH//2 - titleText.get_width()//2, 100))

        mouse_pos = pygame.mouse.get_pos()

        #draw easter egg sprites (normal → monster on hover, scare+jump on click)
        _now = pygame.time.get_ticks()
        for _i, (_norm_spr, _mon_spr) in enumerate(
                zip(menu_sprites_normal, menu_sprites_monster)):
            _px, _py = _sprite_pos_current[_i]
            _base_rect = pygame.Rect(_px, _py, _DISPLAY_SIZE, _DISPLAY_SIZE)
            _elapsed = _now - _sprite_anim_start[_i]
            _animating = _sprite_anim_start[_i] > 0 and _elapsed < _SCARE_DURATION
            # when animation finishes, jump to new position
            if _sprite_anim_start[_i] > 0 and _elapsed >= _SCARE_DURATION:
                _sprite_pos_current[_i] = _pick_new_sprite_pos(_i)
                _sprite_anim_start[_i] = 0
            if _animating:
                _t = _elapsed / _SCARE_DURATION
                if _t < 0.3:
                    _scale = 1.0 + 0.45 * (_t / 0.3)
                elif _t < 0.7:
                    _scale = 1.45
                else:
                    _scale = 1.45 - 0.45 * ((_t - 0.7) / 0.3)
                _jiggle_t = max(0.0, min(1.0, (_t - 0.25) / 0.5))
                _jiggle_fade = math.sin(_jiggle_t * math.pi)
                _jx = int(math.sin(_elapsed * 0.08) * 10 * _jiggle_fade)
                _jy = int(math.cos(_elapsed * 0.11) * 6  * _jiggle_fade)
                _sz = int(_DISPLAY_SIZE * _scale)
                _spr = pygame.transform.smoothscale(_mon_spr, (_sz, _sz))
                _dx = _base_rect.centerx - _sz // 2 + _jx
                _dy = _base_rect.centery - _sz // 2 + _jy
                # shadow scales too
                _sh = pygame.transform.smoothscale(_shadow_surf, (_sz + 10, 14))
                screen.blit(_sh, (_dx - 5, _dy + _sz - 4))
                screen.blit(_spr, (_dx, _dy))
            elif _base_rect.collidepoint(mouse_pos):
                screen.blit(_shadow_surf, (_base_rect.x - 5, _base_rect.bottom - 6))
                screen.blit(_mon_spr, _base_rect.topleft)
            else:
                screen.blit(_shadow_surf, (_base_rect.x - 5, _base_rect.bottom - 6))
                screen.blit(_norm_spr, _base_rect.topleft)

        draw_button(start_button, "START", start_button.collidepoint(mouse_pos))
        draw_button(instructions_button, "CONTROLS", instructions_button.collidepoint(mouse_pos))
        draw_button(exit_button, "EXIT", exit_button.collidepoint(mouse_pos))
        draw_settings_icon(settings_button.collidepoint(mouse_pos))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                #check sprite clicks first (easter eggs — use current positions)
                _clicked_sprite = False
                for _si in range(len(_sprite_pos_current)):
                    _sp2 = _sprite_pos_current[_si]
                    _sr = pygame.Rect(_sp2[0], _sp2[1], _DISPLAY_SIZE, _DISPLAY_SIZE)
                    if _sr.collidepoint(event.pos) and menu_sprites_monster:
                        _sprite_anim_start[_si] = pygame.time.get_ticks()
                        _clicked_sprite = True
                        break
                if not _clicked_sprite:
                    if start_button.collidepoint(event.pos):
                        selected = show_planet_menu()
                        if selected is not None:
                            show_game_screen(selected)
                        pygame.mixer.music.unpause()
                    elif instructions_button.collidepoint(event.pos):
                        show_instructions()
                    elif exit_button.collidepoint(event.pos):
                        show_exit_confirm()
                    elif settings_button.collidepoint(event.pos):
                        show_settings()

if __name__ == "__main__":
    play_cutscenes()
    #start background music loop for menu
    if bgm_loaded:
        pygame.mixer.music.play(-1)  #loop indefinitely

    menu_loop()
