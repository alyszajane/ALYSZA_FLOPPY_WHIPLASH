"""game classes, for:
make, calculate and show pipe, bird, score, background and floor
"""
from random import randrange
from os.path import join
from constant import pygame, BEST_SCORE
from constant import WINDOW_HEIGHT, WINDOW_WIDTH, FLOOR_HEIGHT, PIPE_GAP
from constant import world, bird_images, numbers_img, scoreboard_img


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


def make_powerless_surface(surface):
    """Create a dark monochrome copy once instead of filtering every frame."""
    powerless = pygame.transform.grayscale(surface).convert_alpha()
    powerless.fill((78, 78, 78, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return powerless


def blit_color_restored(window, color_surface, powerless_surface, position, color_amount):
    """Draw monochrome first, then fade the original color back in."""
    window.blit(powerless_surface, position)
    if color_amount <= 0:
        return

    color_surface.set_alpha(color_amount)
    window.blit(color_surface, position)
    color_surface.set_alpha(None)


def restore_color(color, color_amount):
    color_mix = max(0, min(255, color_amount)) / 255
    luminance = int((color[0] * 0.299 + color[1] * 0.587 + color[2] * 0.114) * 0.78)
    return tuple(int(luminance * (1 - color_mix) + channel * color_mix) for channel in color)


class Ribbon:
    """Ribbon trail class for
    storing bird position history and drawing a fading ribbon behind it
    """

    def __init__(self, ribbon_image, max_segments=30):
        """Initialize the ribbon trail

        Args:
            ribbon_image (pygame surface): the ribbon sprite image
            max_segments (int): how many trail segments to keep (higher = longer trail)
        """
        self.ribbon_img = ribbon_image
        self.max_segments = max_segments
        self.segments = []
        self.alpha_decay = 255 / max_segments
        self.velocity = 6
        self.base_width = max(10, ribbon_image.get_height() * 0.3)
        self.tail_width = max(5, ribbon_image.get_height() * 0.3)

    def update(self, bird_x, bird_y, bird_width, bird_height, ribbon_x=None, ribbon_y=None):
        """Update ribbon trail.

        If ribbon_x/ribbon_y are provided, they are used as the attachment point.
        Otherwise, the attachment point is computed from bird_x/bird_y and size.
        """
        for segment in self.segments:
            segment['x'] -= self.velocity

        if ribbon_x is None or ribbon_y is None:
            ribbon_x = bird_x + (bird_width * 0.25)
            ribbon_y = bird_y + (bird_height / 2)

        new_segment = {
            'x': ribbon_x,
            'y': ribbon_y,
            'alpha': 255
        }
        self.segments.insert(0, new_segment)

        if len(self.segments) > self.max_segments:
            self.segments.pop()

        for i, segment in enumerate(self.segments):
            segment['alpha'] = max(0, 255 - (i * self.alpha_decay))

    def draw(self, window, color_amount=255):
        """Draw the ribbon as a continuous fading strip."""
        if len(self.segments) < 2:
            return

        ribbon_surface = pygame.Surface(window.get_size(), pygame.SRCALPHA)
        top_edge = []
        bottom_edge = []
        ribbon_path = self._smooth_path(self.segments)
        total = max(1, len(ribbon_path) - 1)

        for index, segment in enumerate(ribbon_path):
            prev_segment = ribbon_path[max(0, index - 1)]
            next_segment = ribbon_path[min(len(ribbon_path) - 1, index + 1)]
            dx = next_segment['x'] - prev_segment['x']
            dy = next_segment['y'] - prev_segment['y']
            length = max(1, (dx * dx + dy * dy) ** 0.5)
            normal_x = -dy / length
            normal_y = dx / length

            taper = 1 - (index / total)
            half_width = (self.tail_width + (self.base_width - self.tail_width) * taper) / 2
            x_pos = segment['x']
            y_pos = segment['y']
            top_edge.append((x_pos + normal_x * half_width, y_pos + normal_y * half_width))
            bottom_edge.append((x_pos - normal_x * half_width, y_pos - normal_y * half_width))

        for index in range(len(ribbon_path) - 1):
            fade = 1 - (index / total)
            body_alpha = int(35 + 125 * fade)
            edge_alpha = int(25 + 105 * fade)
            quad = [top_edge[index], top_edge[index + 1], bottom_edge[index + 1], bottom_edge[index]]
            pygame.draw.polygon(
                ribbon_surface,
                (*restore_color((105, 230, 95), color_amount), body_alpha),
                quad
            )
            pygame.draw.line(
                ribbon_surface,
                (*restore_color((230, 255, 225), color_amount), edge_alpha),
                top_edge[index],
                top_edge[index + 1],
                3
            )
            pygame.draw.line(
                ribbon_surface,
                (*restore_color((230, 255, 225), color_amount), edge_alpha),
                bottom_edge[index],
                bottom_edge[index + 1],
                3
            )

        pygame.draw.circle(
            ribbon_surface,
            (*restore_color((105, 230, 95), color_amount), 120),
            (round(ribbon_path[0]['x']), round(ribbon_path[0]['y'])),
            max(3, round(self.base_width / 2))
        )
        window.blit(ribbon_surface, (0, 0))

    def _smooth_path(self, points):
        """Round off sharp corners with a light Chaikin pass."""
        smoothed = points[:]
        for _ in range(2):
            if len(smoothed) < 3:
                break

            next_points = [smoothed[0]]
            for first, second in zip(smoothed, smoothed[1:]):
                next_points.append({
                    'x': first['x'] * 0.75 + second['x'] * 0.25,
                    'y': first['y'] * 0.75 + second['y'] * 0.25,
                    'alpha': first['alpha'],
                })
                next_points.append({
                    'x': first['x'] * 0.25 + second['x'] * 0.75,
                    'y': first['y'] * 0.25 + second['y'] * 0.75,
                    'alpha': second['alpha'],
                })
            next_points.append(smoothed[-1])
            smoothed = next_points
        return smoothed

    def reset(self):
        """Clear all segments"""
        self.segments = []


class FloatingText:
    """A small floating '+N' label that pops up when a note is collected."""
    _font = None

    def __init__(self, text, x, y):
        if FloatingText._font is None:
            FloatingText._font = _load_font(16)
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.vy = -2.0
        self.life = 55
        self.alpha = 255

    def update(self):
        self.y += self.vy
        self.life -= 1
        self.alpha = max(0, int(255 * self.life / 55))

    @property
    def dead(self):
        return self.life <= 0

    def draw(self, window):
        text = self._font.render(self.text, True, (255, 245, 255))
        text.set_alpha(self.alpha)
        shadow = self._font.render(self.text, True, (160, 70, 180))
        shadow.set_alpha(self.alpha)
        window.blit(shadow, (int(self.x) + 2, int(self.y) + 2))
        window.blit(text, (int(self.x), int(self.y)))


class Score:
    """Score class - music note points meter with distance tracker.

    Goal: collect 25 points worth of notes (each note is worth 3, 4, or 5).
    """
    GOAL = 25
    numbers = numbers_img
    scoreboard = scoreboard_img
    _fill_img = None
    _frame_img = None
    _font_med = None
    _font_sm = None
    _settings_img = None

    SPRITE_W = 380
    SPRITE_H = 105
    HUD_W = SPRITE_W
    HUD_H = 300
    BAR_X_OFF = 102
    BAR_Y_OFF = 36
    BAR_W = 250
    BAR_H = 35

    # Score text font size (used for the X/GOAL label)
    SCORE_FONT_SIZE = 20

    # Distance label position inside the HUD surface
    DIST_TEXT_X = 35
    DIST_TEXT_Y = SPRITE_H + 2

    # Distance label font size
    DIST_FONT_SIZE = 30

    SETTINGS_ICON_SIZE = 52

    def __init__(self):
        self.note_points = 0
        self.distance = 0
        self.floating_texts = []
        self.settings_rect = pygame.Rect(0, 0, 0, 0)
        if Score._fill_img is None:
            fill = pygame.image.load(join('data', 'fill.png')).convert_alpha()
            fill = crop_to_opaque(fill)
            Score._fill_img = pygame.transform.scale(fill, (Score.BAR_W, Score.BAR_H))
        if Score._frame_img is None:
            frame = pygame.image.load(join('data', 'frame.png')).convert_alpha()
            Score._frame_img = pygame.transform.scale(frame, (Score.SPRITE_W, Score.SPRITE_H))
        if Score._font_med is None:
            Score._font_med = _load_font(self.SCORE_FONT_SIZE)
        if Score._font_sm is None:
            Score._font_sm = _load_font(self.DIST_FONT_SIZE)
        if Score._settings_img is None:
            try:
                raw_s = pygame.image.load(join('data', 'settings.png')).convert_alpha()
                Score._settings_img = pygame.transform.scale(
                    raw_s, (self.SETTINGS_ICON_SIZE, self.SETTINGS_ICON_SIZE))
            except (FileNotFoundError, pygame.error):
                surf = pygame.Surface((self.SETTINGS_ICON_SIZE, self.SETTINGS_ICON_SIZE), pygame.SRCALPHA)
                pygame.draw.circle(surf, (200, 200, 200, 220),
                                   (self.SETTINGS_ICON_SIZE // 2, self.SETTINGS_ICON_SIZE // 2),
                                   self.SETTINGS_ICON_SIZE // 2 - 2)
                pygame.draw.circle(surf, (80, 80, 80, 220),
                                   (self.SETTINGS_ICON_SIZE // 2, self.SETTINGS_ICON_SIZE // 2), 6)
                Score._settings_img = surf

    def add_score(self):
        """Legacy method - kept for compatibility."""
        pass

    def add_note_points(self, value, bird_x=0, bird_y=0):
        """Add note points and spawn a floating '+N' label."""
        self.note_points = min(self.note_points + value, self.GOAL)
        self.floating_texts.append(FloatingText(f'+{value}', bird_x + 40, bird_y))

    def update(self, distance_delta=0):
        """Advance the distance counter and tick floating texts."""
        self.distance += distance_delta
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if not ft.dead]

    def draw(self, window):
        """Draw the meter from the original fill and frame sprites."""
        hud_x = 24
        hud_y = 18

        hud = pygame.Surface((self.HUD_W, self.HUD_H), pygame.SRCALPHA)
        fill_x = self.BAR_X_OFF
        fill_y = self.BAR_Y_OFF

        hud.blit(self._frame_img, (0, 0))

        fill_ratio = min(1.0, self.note_points / self.GOAL)
        fill_w = max(0, int(self.BAR_W * fill_ratio))
        if self.note_points > 0:
            fill_w = max(fill_w, self.BAR_H // 2)
        if fill_w > 0:
            fill_surf = pygame.Surface((fill_w, self.BAR_H), pygame.SRCALPHA)
            fill_surf.blit(self._fill_img, (0, 0))
            hud.blit(fill_surf, (fill_x, fill_y))

        pts_text = f'{self.note_points}/{self.GOAL}'
        tw, th = self._font_med.size(pts_text)
        cx = fill_x + self.BAR_W // 2 - tw // 2
        cy = fill_y + self.BAR_H // 2 - th // 2
        pts_shad = self._font_med.render(pts_text, True, (50, 50, 50))
        pts_surf = self._font_med.render(pts_text, True, (255, 255, 255))
        hud.blit(pts_shad, (cx + 1, cy + 1))
        hud.blit(pts_surf, (cx, cy))

        dist_m = self.distance // 60
        dist_text = f'Distance: {dist_m}m'
        dist_surf = self._font_sm.render(dist_text, True, (255, 255, 255))
        hud.blit(dist_surf, (self.DIST_TEXT_X, self.DIST_TEXT_Y))

        settings_hud_x = self.DIST_TEXT_X
        settings_hud_y = self.DIST_TEXT_Y + dist_surf.get_height() + 8
        hud.blit(self._settings_img, (settings_hud_x, settings_hud_y))

        window.blit(hud, (hud_x, hud_y))

        self.settings_rect = pygame.Rect(
            hud_x + settings_hud_x,
            hud_y + settings_hud_y,
            self.SETTINGS_ICON_SIZE,
            self.SETTINGS_ICON_SIZE
        )

        for ft in self.floating_texts:
            ft.draw(window)


def crop_to_opaque(surf):
    """Return a copy with transparent border pixels removed."""
    bounds = surf.get_bounding_rect()
    if bounds.width <= 0 or bounds.height <= 0:
        return surf

    cropped = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
    cropped.blit(surf, (0, 0), bounds)
    return cropped


class MusicNote:
    """A collectible musical note that lives inside a pipe gap."""

    NOTE_SIZE = 38
    _sprites = None  # List of (img, powerless_img, mask) — one per sprite in the sheet

    @classmethod
    def _load_sprites(cls):
        """Slice the 3x3 note sprite sheet into 9 individual sprites.
        Each cell is cropped to its opaque bounding box so the note
        fills the full NOTE_SIZE area instead of appearing as a tiny speck.
        """
        raw = pygame.image.load(join('data', 'note.png')).convert_alpha()
        sheet_w, sheet_h = raw.get_size()
        cols, rows = 3, 3
        cell_w = sheet_w // cols
        cell_h = sheet_h // rows
        cls._sprites = []
        for row in range(rows):
            for col in range(cols):
                cell = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                cell.blit(raw, (0, 0), (col * cell_w, row * cell_h, cell_w, cell_h))
                bounds = cell.get_bounding_rect()
                if bounds.width > 0 and bounds.height > 0:
                    cropped = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
                    cropped.blit(cell, (0, 0), bounds)
                    scaled = pygame.transform.smoothscale(cropped, (cls.NOTE_SIZE, cls.NOTE_SIZE))
                else:
                    scaled = pygame.transform.smoothscale(cell, (cls.NOTE_SIZE, cls.NOTE_SIZE))
                powerless = make_powerless_surface(scaled)
                mask = pygame.mask.from_surface(scaled)
                cls._sprites.append((scaled, powerless, mask))

    def __init__(self, x_pos, y_pos):
        if MusicNote._sprites is None:
            MusicNote._load_sprites()

        chosen = MusicNote._sprites[randrange(len(MusicNote._sprites))]
        self.img, self.powerless_img, self._mask = chosen
        self.x_pos = float(x_pos)
        self.y_pos = float(y_pos)
        self.collected = False
        self.point_value = randrange(3, 6)
        self.velocity = Pipe.velocity

        self.rect = self.img.get_rect(topleft=(int(self.x_pos), int(self.y_pos)))

    def move(self):
        self.x_pos -= self.velocity
        self.rect.x = int(self.x_pos)

    @property
    def off_screen(self):
        return self.x_pos + self.NOTE_SIZE < 0

    def check_collect(self, bird):
        if self.collected:
            return False

        bird_rect = bird.img.get_rect(topleft=(int(bird.x_pos), round(bird.y_pos)))
        if not self.rect.colliderect(bird_rect):
            return False

        bird_mask = pygame.mask.from_surface(bird.img)
        offset = (self.rect.x - bird_rect.x, self.rect.y - bird_rect.y)
        if bird_mask.overlap(self._mask, offset):
            self.collected = True
            return self.point_value
        return False

    def draw(self, window, color_amount=255):
        if not self.collected:
            blit_color_restored(
                window,
                self.img,
                self.powerless_img,
                (int(self.x_pos), int(self.y_pos)),
                color_amount
            )


class DynamicLighting:
    """Manage the level's color returning as notes are collected."""

    def __init__(self):
        self.progress = 0.0
        self.start_color = 0
        self.full_color = 255

    def update(self, note_points, goal):
        if goal <= 0:
            self.progress = 1.0
            return

        self.progress = max(0.0, min(1.0, note_points / goal))

    def get_alpha(self):
        eased_progress = self.progress * self.progress * (3 - 2 * self.progress)
        color_range = self.full_color - self.start_color
        return int(self.start_color + (color_range * eased_progress))


class VictoryPlatform:
    """Landing platform that appears at the end of the level."""

    velocity = 6

    def __init__(self, x_pos):
        self.x_pos = x_pos
        self.width = 300
        self.height = 60
        self.y_pos = WINDOW_HEIGHT - FLOOR_HEIGHT - self.height
        self.color = (100, 200, 100)
        self.edge_color = (255, 215, 0)
        self.is_active = False
        self.rect = pygame.Rect(self.x_pos, self.y_pos, self.width, self.height)

    def set_active(self):
        self.is_active = True

    def move(self):
        if not self.is_active:
            return
        self.x_pos -= self.velocity
        self.rect.x = round(self.x_pos)

    def check_landing(self, bird):
        if not self.is_active:
            return False

        bird_rect = pygame.Rect(
            bird.x_pos,
            round(bird.y_pos),
            bird.img.get_width(),
            bird.img.get_height()
        )
        bird_bottom = bird_rect.bottom
        platform_top = self.rect.top
        is_above_platform = bird_bottom <= platform_top + 18
        is_falling = bird.last_displacement >= 0

        return bird_rect.colliderect(self.rect) and is_above_platform and is_falling

    def draw(self, window, color_amount=255):
        if not self.is_active:
            return

        pygame.draw.rect(window, restore_color(self.color, color_amount), self.rect, border_radius=8)
        pygame.draw.rect(
            window,
            restore_color(self.edge_color, color_amount),
            self.rect,
            width=4,
            border_radius=8
        )


class Pipe:
    """Pipe class for
    set pipes height,
    move and draw pipes
    and check collide the bird to pipes
    """
    TOP_BUILDING_IMG = world['building_top']
    TOP_BUILDING_POWERLESS_IMG = world['building_top_powerless']
    BOTTOM_BUILDING_IMG = world['building_bottom']
    BOTTOM_BUILDING_POWERLESS_IMG = world['building_bottom_powerless']
    velocity = 6
    SEGMENT_WIDTH = 1564

    def __init__(self, x_pos):
        self.x_pos = x_pos
        self.passed = False
        self.set_height()
        self._spawn_note()

    def _make_building(self, image, target_width, target_height, flip_vertical=False):
        """Scale the building and crop transparent padding like the old version."""
        surf = pygame.transform.smoothscale(
            image,
            (target_width, target_height)
        )
        if flip_vertical:
            surf = pygame.transform.flip(surf, False, True)
        surf = crop_to_opaque(surf)
        return surf, make_powerless_surface(surf)

    def set_height(self):
        """Initialize one skyline segment with top and bottom buildings."""
        min_building_height = int(WINDOW_HEIGHT * 0.30)
        max_building_height = int(WINDOW_HEIGHT * 0.60)
        gap_size = PIPE_GAP + randrange(-35, 36)
        available_height = WINDOW_HEIGHT - gap_size

        bottom_min = max(min_building_height, available_height - max_building_height)
        bottom_max = min(max_building_height, available_height - min_building_height)
        if bottom_min > bottom_max:
            bottom_height = max(min_building_height, available_height // 2)
        else:
            bottom_height = randrange(bottom_min, bottom_max + 1)
        top_height = max(min_building_height, available_height - bottom_height)

        target_width = self.SEGMENT_WIDTH

        self.bottom_building, self.bottom_building_powerless = self._make_building(
            self.BOTTOM_BUILDING_IMG, target_width, bottom_height)
        self.width = target_width
        self.height = self.bottom_building.get_height()
        self.bottom_y = WINDOW_HEIGHT - self.height

        self.top_building, self.top_building_powerless = self._make_building(
            self.TOP_BUILDING_IMG, target_width, top_height, flip_vertical=True)
        self.bottom_mask = pygame.mask.from_surface(self.bottom_building)
        self.top_mask = pygame.mask.from_surface(self.top_building)
        self.top_height = self.top_building.get_height()
        self.top_draw_y = 0
        self.gap_top = self.top_height
        self.gap_bottom = self.bottom_y

        # Bottom collision rect based on non-transparent pixels
        bottom_bounds = self.bottom_building.get_bounding_rect()
        self.bottom_rect = pygame.Rect(
            self.x_pos + bottom_bounds.x,
            self.bottom_y + bottom_bounds.y,
            bottom_bounds.width,
            bottom_bounds.height
        )

        # Top collision rect based on non-transparent pixels
        top_bounds = self.top_building.get_bounding_rect()
        self.top_rect = pygame.Rect(
            self.x_pos + top_bounds.x,
            self.top_draw_y + top_bounds.y,
            top_bounds.width,
            top_bounds.height
        )

    def _spawn_note(self):
        note_size = MusicNote.NOTE_SIZE
        margin = 30
        gap_top = self.gap_top + margin
        gap_bottom = self.gap_bottom - margin - note_size

        if gap_bottom <= gap_top:
            self.note = None
            return

        note_y = randrange(gap_top, gap_bottom + 1)
        note_x = self.x_pos + (self.width // 2) - (note_size // 2)
        self.note = MusicNote(note_x, note_y)

    def move(self):
        self.x_pos -= self.velocity
        self.top_rect.x -= self.velocity
        self.bottom_rect.x -= self.velocity
        if self.note:
            self.note.move()

    def draw(self, window, color_amount=255, note_color_amount=255):
        """draw skyline buildings in screen

        Args:
            window (pygame surface): display of the game
        """
        blit_color_restored(
            window,
            self.top_building,
            self.top_building_powerless,
            (self.x_pos, self.top_draw_y),
            color_amount
        )
        blit_color_restored(
            window,
            self.bottom_building,
            self.bottom_building_powerless,
            (self.x_pos, self.bottom_y),
            color_amount
        )
        if self.note:
            self.note.draw(window, note_color_amount)

    def check_note_collect(self, bird) -> bool:
        if self.note:
            return self.note.check_collect(bird)
        return False

    def collide(self, bird: object) -> bool:
        """check collide the bird to pipes

        Args:
            bird (object): bird class

        Returns:
            bool: True for collide and false for not collide
        """
        bird_rect = pygame.Rect(bird.x_pos, round(bird.y_pos), bird.img.get_width(), bird.img.get_height())
        bird_mask = pygame.mask.from_surface(bird.img)

        if self.top_rect.colliderect(bird_rect):
            top_offset = (
                round(bird.x_pos - self.x_pos),
                round(bird.y_pos - self.top_draw_y)
            )
            if self.top_mask.overlap(bird_mask, top_offset):
                return True

        if self.bottom_rect.colliderect(bird_rect):
            bottom_offset = (
                round(bird.x_pos - self.x_pos),
                round(bird.y_pos - self.bottom_y)
            )
            if self.bottom_mask.overlap(bird_mask, bottom_offset):
                return True

        return False


class Bird:
    """Bird class for
    bird jump,
    change tilt
    check crashed,
    move the bird(change bird position),
    set state of bird image(idle, ascend, descend)
    draw the bird in screen
    and get mask(for collide in Pipe model)
    """
    img = bird_images['idle']
    crashed = False
    FLAPS_ANIMATION_TIME = 5
    ROTATE_VEL = 10
    MAX_TILT_UP = 25
    MAX_TILT_DOWN = -45
    JUMP_STRENGTH = -9.6
    ASCENT_GRAVITY = 2
    DESCENT_GRAVITY = 1.25
    MAX_FALL_SPEED = 16

    def __init__(self, x_pos, y_pos, ribbon=None):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.tilt = 0
        self.tick = 0
        self.frame_index = 0
        self.velacity = 0
        self.height = self.y_pos
        self.ribbon = ribbon
        self.is_celebrating = False
        self.celebration_tick = 0
        self.last_displacement = 0

    def jump(self):
        """jump the bird in screen
        """
        self.velacity = self.JUMP_STRENGTH
        self.tick = 0
        self.height = self.y_pos

    def celebration_jump(self):
        """Start the automatic victory celebration."""
        self.is_celebrating = True
        self.celebration_tick = 0
        self.velacity = -12
        self.tick = 0

    def tilt_bird(self, displacement):
        """Tilt upward while rising, tilt downward while falling."""
        if displacement < 0:
            # Rising: quickly tilt up to a cap
            self.tilt = min(self.MAX_TILT_UP, self.tilt + self.ROTATE_VEL)
        else:
            # Falling: gradually tilt down to a cap
            self.tilt = max(self.MAX_TILT_DOWN, self.tilt - self.ROTATE_VEL)

    def check_crashed(self):
        """check for crashed bird, if it falls or goes up a lot
        """
        if self.y_pos >= WINDOW_HEIGHT:
            self.crashed = True

        if self.y_pos < - self.img.get_height() / 4:
            self.crashed = True

    def move(self):
        """move bird in screen with displacement value
        """
        if self.is_celebrating:
            self.celebration_tick += 1
            if self.celebration_tick % 30 == 0:
                self.jump()
            if self.celebration_tick >= 120:
                self.is_celebrating = False

        self.tick += 1
        ascent_displacement = self.velacity * self.tick + self.ASCENT_GRAVITY * self.tick ** 2
        gravity = self.ASCENT_GRAVITY if ascent_displacement < 0 else self.DESCENT_GRAVITY
        displacement = self.velacity * self.tick + gravity * self.tick ** 2
        if displacement >= self.MAX_FALL_SPEED:
            displacement = (displacement/abs(displacement)) * self.MAX_FALL_SPEED

        self.last_displacement = displacement
        self.y_pos += displacement

        self.tilt_bird(displacement)
        self.check_crashed()

        # Update ribbon trail if it exists
        if self.ribbon:
            width = self.img.get_width()
            height = self.img.get_height()
            center = pygame.math.Vector2(self.x_pos + width / 2, self.y_pos + height / 2)
            tail_base = pygame.math.Vector2(self.x_pos + (width * 0.25), self.y_pos + (height / 2))
            rotated_tail = center + (tail_base - center).rotate(-self.tilt)
            self.ribbon.update(
                self.x_pos,
                self.y_pos,
                width,
                height,
                ribbon_x=rotated_tail.x,
                ribbon_y=rotated_tail.y,
            )

    def set_state(self):
        """Single-sprite character: no animation frames."""
        self.img = bird_images['idle']
        self.powerless_img = bird_images['idle_powerless']

    def draw(self, window, color_amount=255):
        """Draw the bird with tilt animation (rotate on ascent/descent)."""
        self.set_state()

        # Build the final colored sprite (powerless base + color fade-in), then rotate it.
        rendered = self.powerless_img.copy()
        if color_amount > 0:
            color_layer = self.img.copy()
            color_layer.set_alpha(color_amount)
            rendered.blit(color_layer, (0, 0))

        rotated = pygame.transform.rotate(rendered, self.tilt)
        rect = rotated.get_rect(center=(self.x_pos + self.img.get_width() / 2,
                                        self.y_pos + self.img.get_height() / 2))
        window.blit(rotated, rect.topleft)


class Background:
    """Background class for,
    move and draw backgrounds (3 parallax layers: backBG, midBG, frontBG)
    """
    img_back = world['backBG']
    img_back_powerless = world['backBG_powerless']
    img_mid = world['midBG']
    img_mid_powerless = world['midBG_powerless']
    img_front = world['frontBG']
    img_front_powerless = world['frontBG_powerless']
    width = img_back.get_width()
    velocity = 1

    def __init__(self):
        self.back_x1 = 0
        self.back_x2 = self.width
        self.mid_x1 = 0
        self.mid_x2 = self.width
        self.front_x1 = 0
        self.front_x2 = self.width

    def move(self):
        """move backgrounds with velocity
        """
        self.back_x1 -= self.velocity
        self.back_x2 -= self.velocity
        self.mid_x1 -= self.velocity
        self.mid_x2 -= self.velocity
        self.front_x1 -= self.velocity
        self.front_x2 -= self.velocity

        if self.back_x1 + self.width < 0:
            self.back_x1 = self.back_x2 + self.width
        if self.back_x2 + self.width < 0:
            self.back_x2 = self.back_x1 + self.width
        if self.mid_x1 + self.width < 0:
            self.mid_x1 = self.mid_x2 + self.width
        if self.mid_x2 + self.width < 0:
            self.mid_x2 = self.mid_x1 + self.width
        if self.front_x1 + self.width < 0:
            self.front_x1 = self.front_x2 + self.width
        if self.front_x2 + self.width < 0:
            self.front_x2 = self.front_x1 + self.width

    def draw(self, window, color_amount=255):
        """draw backgrounds in screen

        Args:
            window (pygame surface): game display
        """
        blit_color_restored(
            window,
            self.img_back,
            self.img_back_powerless,
            (self.back_x1, 0),
            color_amount
        )
        blit_color_restored(
            window,
            self.img_back,
            self.img_back_powerless,
            (self.back_x2, 0),
            color_amount
        )

        # Draw midBG at the bottom of screen
        mid_y = WINDOW_HEIGHT - self.img_mid.get_height()
        blit_color_restored(
            window,
            self.img_mid,
            self.img_mid_powerless,
            (self.mid_x1, mid_y),
            color_amount
        )
        blit_color_restored(
            window,
            self.img_mid,
            self.img_mid_powerless,
            (self.mid_x2, mid_y),
            color_amount
        )

        # Draw frontBG a little higher than midBG
        front_y = WINDOW_HEIGHT - self.img_mid.get_height() - self.img_front.get_height()
        blit_color_restored(
            window,
            self.img_front,
            self.img_front_powerless,
            (self.front_x1, front_y),
            color_amount
        )
        blit_color_restored(
            window,
            self.img_front,
            self.img_front_powerless,
            (self.front_x2, front_y),
            color_amount
        )


class Floor:
    """Floor class for,
    move and draw floors
    """
    img = world['floor']
    width = img.get_width()
    height = img.get_height()
    velocity = 6

    def __init__(self):
        self.floor_x1 = 0
        self.floor_x2 = self.width

    def move(self):
        """move floor in screen with velocity
        """
        self.floor_x1 -= self.velocity
        self.floor_x2 -= self.velocity

        if self.floor_x1 + self.width < 0:
            self.floor_x1 = self.floor_x2 + self.width
        if self.floor_x2 + self.width < 0:
            self.floor_x2 = self.floor_x1 + self.width

    def draw(self, window, color_amount=255):
        """Draw floor to screen

        Args:
            window (pygame surface): game display
        """
        # Floor sprite hidden; keep the object for movement/game-loop compatibility.
        return
